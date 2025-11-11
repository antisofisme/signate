"""
Device Health API Routes
HTTP endpoints for device health monitoring
"""

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, CurrentUser
from shared.errors import handle_errors, NotFoundError
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from typing import List, Optional

from .dtos import (
    DeviceHealthMetricsCreate,
    DeviceHealthResponse,
    HealthAlertResponse,
    DeviceHealthWithAlertsResponse,
    HealthHistoryResponse,
    OrganizationHealthSummaryResponse
)
from .repositories.device_health_repo import DeviceHealthRepository
from .repositories.device_repo import DeviceRepository
from .use_cases.record_health_metrics import RecordHealthMetricsUseCase
from .use_cases.get_device_health import (
    GetDeviceHealthUseCase,
    GetDeviceHealthWithAlertsUseCase,
    GetDeviceHealthHistoryUseCase,
    GetOrganizationHealthSummaryUseCase
)


router = APIRouter()

# Initialize loggers
request_logger = RequestLogger()
audit_logger = AuditLogger()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_health_repository(db: Session = Depends(get_db)) -> DeviceHealthRepository:
    """Get device health repository instance"""
    return DeviceHealthRepository(db)


def get_device_repository(db: Session = Depends(get_db)) -> DeviceRepository:
    """Get device repository instance"""
    return DeviceRepository(db)


# =============================================================================
# PLAYER ENDPOINTS (PUBLIC - NO AUTH, but requires device validation)
# =============================================================================

@router.post("/api/v1/devices/{device_id}/health", response_model=DeviceHealthResponse, status_code=status.HTTP_201_CREATED)
def record_device_health(
    device_id: int,
    request: DeviceHealthMetricsCreate,
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Record health metrics from device (called by player)

    Player sends health metrics periodically (e.g., every 5 minutes).
    Metrics include CPU, memory, disk, network, and player status.
    """
    use_case = RecordHealthMetricsUseCase(health_repo, device_repo)

    try:
        health_metric = use_case.execute(
            device_id=device_id,
            cpu_usage=request.cpu_usage,
            memory_usage=request.memory_usage,
            memory_total_mb=request.memory_total_mb,
            memory_used_mb=request.memory_used_mb,
            disk_usage=request.disk_usage,
            disk_total_gb=request.disk_total_gb,
            disk_used_gb=request.disk_used_gb,
            network_latency_ms=request.network_latency_ms,
            network_download_mbps=request.network_download_mbps,
            network_upload_mbps=request.network_upload_mbps,
            display_resolution=request.display_resolution,
            display_refresh_rate=request.display_refresh_rate,
            gpu_usage=request.gpu_usage,
            player_version=request.player_version,
            player_uptime_hours=request.player_uptime_hours,
            content_errors_count=request.content_errors_count,
            last_error_message=request.last_error_message,
            metadata=request.metadata
        )

        return DeviceHealthResponse.model_validate(health_metric)

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )


# =============================================================================
# CMS ENDPOINTS (PROTECTED - REQUIRES AUTH)
# =============================================================================

@router.get("/api/v1/devices/{device_id}/health", response_model=DeviceHealthWithAlertsResponse)
def get_device_health(
    device_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get latest health metrics with alerts (called by CMS)

    Returns latest health metrics and any active alerts for the device.
    """
    use_case = GetDeviceHealthWithAlertsUseCase(health_repo, device_repo)

    try:
        health_metric, alerts = use_case.execute(device_id)

        return DeviceHealthWithAlertsResponse(
            health=DeviceHealthResponse.model_validate(health_metric) if health_metric else None,
            alerts=[HealthAlertResponse.model_validate(alert) for alert in alerts]
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )


@router.get("/api/v1/devices/{device_id}/health/history", response_model=HealthHistoryResponse)
def get_device_health_history(
    device_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve (max 7 days)"),
    current_user: CurrentUser = Depends(get_current_user),
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get health history for device (called by CMS)

    Returns historical health metrics for charting and analysis.
    """
    use_case = GetDeviceHealthHistoryUseCase(health_repo, device_repo)

    try:
        history = use_case.execute(device_id, hours)

        return HealthHistoryResponse(
            history=[DeviceHealthResponse.model_validate(metric) for metric in history],
            count=len(history)
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )


@router.get("/api/v1/organizations/{organization_id}/health/summary", response_model=OrganizationHealthSummaryResponse)
def get_organization_health_summary(
    organization_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    health_repo: DeviceHealthRepository = Depends(get_health_repository)
):
    """
    Get organization-wide health summary (called by CMS)

    Returns aggregated health statistics for all devices in organization.
    Useful for dashboard overview.
    """
    # Verify user belongs to organization
    if current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )

    use_case = GetOrganizationHealthSummaryUseCase(health_repo)

    summary = use_case.execute(organization_id)

    if not summary:
        # Return empty summary if no data
        return OrganizationHealthSummaryResponse(
            total_devices=0,
            healthy_devices=0,
            warning_devices=0,
            critical_devices=0,
            offline_devices=0,
            avg_cpu_usage=None,
            avg_memory_usage=None,
            avg_disk_usage=None,
            devices_with_errors=0
        )

    return OrganizationHealthSummaryResponse.model_validate(summary)


@router.get("/api/v1/devices/{device_id}/health/latest", response_model=Optional[DeviceHealthResponse])
def get_latest_device_health(
    device_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get only latest health metrics (called by CMS)

    Returns latest health metrics without alerts.
    Lighter endpoint for simple health checks.
    """
    use_case = GetDeviceHealthUseCase(health_repo, device_repo)

    try:
        health_metric = use_case.execute(device_id)

        if health_metric:
            return DeviceHealthResponse.model_validate(health_metric)
        else:
            return None

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )


@router.get("/api/v1/devices/{device_id}/health/alerts", response_model=List[HealthAlertResponse])
def get_device_health_alerts(
    device_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get health alerts for device (called by CMS)

    Returns only active health alerts without full metrics.
    """
    # Verify device exists
    device = device_repo.find_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Get alerts
    alerts = health_repo.get_alerts(device_id)

    return [HealthAlertResponse.model_validate(alert) for alert in alerts]
