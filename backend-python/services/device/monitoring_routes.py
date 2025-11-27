"""
Device Monitoring Routes

Consolidated routes for device monitoring, health, logs, and remote control.
Merged from: extended_routes, health_routes, log_routes, command_routes,
             console_control_routes, console_routes, connection_log_routes

Created: 2025-11-27
Purpose: Single unified router for all device monitoring operations
"""

from fastapi import APIRouter, Depends, Query, HTTPException, WebSocket, WebSocketDisconnect, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.database import get_db
from shared.api_routes import DeviceRoutes
from shared.auth import get_current_user, CurrentUser
from shared.middleware import require_permission
from shared.errors import handle_errors, NotFoundError
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from shared import websocket_manager as ws_manager_module
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import json
import random
import string
import logging
import asyncio

# DTOs
from pydantic import BaseModel, Field
from services.device.dtos import (
    DeviceHealthMetricsCreate,
    DeviceHealthResponse,
    HealthAlertResponse,
    DeviceHealthWithAlertsResponse,
    HealthHistoryResponse,
    OrganizationHealthSummaryResponse,
    BatchDeviceLogsRequest,
    SaveDeviceLogsResponse,
    ConnectionLogEntryDTO,
    SaveConnectionLogsDTO
)

# Repositories
from services.device.repositories.device_health_repo import DeviceHealthRepository
from services.device.repositories.device_repo import DeviceRepository

# Use Cases
from services.device.use_cases.record_health_metrics import RecordHealthMetricsUseCase
from services.device.use_cases.get_device_health import (
    GetDeviceHealthUseCase,
    GetDeviceHealthWithAlertsUseCase,
    GetDeviceHealthHistoryUseCase,
    GetOrganizationHealthSummaryUseCase
)

monitoring_router = APIRouter(prefix="/api/v1/devices", tags=["Device Monitoring"])

# Initialize loggers
request_logger = RequestLogger()
audit_logger = AuditLogger()
logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS & UTILITIES
# ============================================================================

def generate_activation_code() -> str:
    """Generate 6-digit activation code"""
    # Use alphanumeric excluding confusing chars (0, O, 1, I)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(6))


def calculate_speed_quality(download: float, upload: float) -> str:
    """Calculate speed test quality"""
    if download >= 25 and upload >= 10:
        return 'good'
    elif download >= 10 and upload >= 5:
        return 'fair'
    else:
        return 'poor'


def get_ws_manager():
    """Get WebSocket manager instance (access at runtime, not import time)"""
    manager = ws_manager_module.websocket_manager
    if manager is None:
        raise RuntimeError("WebSocket manager not initialized. This should not happen in production.")
    return manager


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_health_repository(db: Session = Depends(get_db)) -> DeviceHealthRepository:
    """Get device health repository instance"""
    return DeviceHealthRepository(db)


def get_device_repository(db: Session = Depends(get_db)) -> DeviceRepository:
    """Get device repository instance"""
    return DeviceRepository(db)


# ============================================================================
# DTOs - Additional Models (not in shared dtos.py)
# ============================================================================

class TVRegisterRequest(BaseModel):
    """TV device registration"""
    device_name: str
    organization_id: int
    device_uuid: Optional[str] = None
    platform: Optional[str] = "webOS"
    model_name: Optional[str] = None
    firmware_version: Optional[str] = None


class MonitorRegisterRequest(BaseModel):
    """Monitor device registration"""
    organization_id: Optional[int] = None  # Optional - for re-registration
    activation_code: str
    device_name: Optional[str] = None
    platform: Optional[str] = "browser"
    device_type: str = "monitor"


class SpeedTestRequest(BaseModel):
    """Request to run speed test"""
    device_id: int
    download_speed: float
    upload_speed: float
    latency: int
    jitter: Optional[int] = None
    packet_loss: Optional[float] = None
    dns_server: Optional[str] = None
    server_endpoint: Optional[str] = None
    test_duration_ms: Optional[int] = None


class SpeedTestResponse(BaseModel):
    """Speed test result"""
    id: int
    device_id: int
    download_speed: float
    upload_speed: float
    latency: int
    jitter: Optional[int]
    packet_loss: Optional[float]
    dns_server: Optional[str]
    server_endpoint: Optional[str]
    quality: str
    test_duration_ms: Optional[int]
    tested_at: datetime


class ContentItem(BaseModel):
    """Content item in resolution result"""
    id: int
    name: str
    type: str
    uri: str
    duration: int
    priority: int
    source: str  # 'direct', 'tag', or 'playlist'


class CreateLogRequest(BaseModel):
    """Request to create device log (called by player)"""
    device_id: int
    log_level: str = Field(..., description="Log level: log, info, warn, error, debug")
    message: str = Field(..., description="Log message")
    source: Optional[str] = Field(None, description="Source file/function")
    stack_trace: Optional[str] = Field(None, description="Error stack trace")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    url: Optional[str] = Field(None, description="Current page URL")


class LogResponse(BaseModel):
    """Single log entry response"""
    id: int
    device_id: int
    log_level: str
    message: str
    source: Optional[str]
    stack_trace: Optional[str]
    user_agent: Optional[str]
    url: Optional[str]
    recorded_at: datetime


class LogListResponse(BaseModel):
    """List of logs response"""
    total: int
    items: List[LogResponse]


class SendCommandRequest(BaseModel):
    """Request to send command to device"""
    command_type: str = Field(..., description="Type of command: reset, refresh, reload, reboot, screenshot, volume, brightness, speed_test")
    parameters: Optional[dict] = Field(None, description="Command parameters (e.g., {'level': 75} for volume)")
    reason: Optional[str] = Field(None, description="Why this command was issued")


class CommandResponse(BaseModel):
    """Single command response"""
    id: int
    device_id: int
    command_type: str
    parameters: Optional[dict]
    reason: Optional[str]
    status: str
    sent_at: Optional[datetime]
    executed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]


class CommandListResponse(BaseModel):
    """List of commands response"""
    total: int
    items: List[CommandResponse]


class ConnectionLogResponse(BaseModel):
    """Single connection log response"""
    id: int
    device_id: int
    logged_at: datetime
    event_type: str
    status: str
    latency_ms: Optional[int]
    error_message: Optional[str]
    download_speed_mbps: Optional[float]
    upload_speed_mbps: Optional[float]
    connection_type: Optional[str]
    effective_type: Optional[str]
    rtt_ms: Optional[int]
    endpoint: Optional[str]
    http_status: Optional[int]
    test_trigger: Optional[str]
    test_duration_ms: Optional[int]
    metadata: Optional[dict]
    created_at: datetime


class ConnectionLogListResponse(BaseModel):
    """List of connection logs response"""
    total: int
    items: List[ConnectionLogResponse]


# ============================================================================
# EXTENDED OPERATIONS (TV/Monitor Registration, Content Resolution)
# ============================================================================

@monitoring_router.post(DeviceRoutes.TV_REGISTER, status_code=status.HTTP_201_CREATED)
def register_tv_device(
    request: TVRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register TV device (WebOS/native)

    TV devices activate immediately as 'active' (no code needed).
    """
    query = text("""
        INSERT INTO devices (
            device_type, device_name, device_uuid, platform, model_name,
            firmware_version, organization_id, status, created_at
        )
        VALUES (
            'tv', :device_name, :device_uuid, :platform, :model_name,
            :firmware_version, :organization_id, 'active', NOW()
        )
        RETURNING id, device_name, device_uuid, status, created_at
    """)

    result = db.execute(query, {
        "device_name": request.device_name,
        "device_uuid": request.device_uuid,
        "platform": request.platform,
        "model_name": request.model_name,
        "firmware_version": request.firmware_version,
        "organization_id": request.organization_id
    }).fetchone()

    db.commit()

    return {
        "success": True,
        "data": {
            "id": result.id,
            "device_name": result.device_name,
            "device_uuid": result.device_uuid,
            "status": result.status,
            "created_at": result.created_at
        },
        "message": "TV device registered successfully"
    }


@monitoring_router.post(DeviceRoutes.MONITOR_REGISTER, status_code=status.HTTP_201_CREATED)
def register_monitor_device(
    request: MonitorRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register monitor device (browser-based)

    Uses activation code provided by player (6-digit).
    Device status is 'pending' until admin activates.
    """
    # Use code from player, or generate if not provided
    code = request.activation_code or generate_activation_code()
    code_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    device_name = request.device_name or f"Monitor-{code}"

    query = text("""
        INSERT INTO devices (
            device_type, device_name, unique_code, code_expires_at,
            platform, organization_id, status, created_at
        )
        VALUES (
            'monitor', :device_name, :unique_code, :code_expires_at,
            :platform, :organization_id, 'pending', NOW()
        )
        RETURNING id, device_name, unique_code, code_expires_at, status, created_at, organization_id
    """)

    result = db.execute(query, {
        "device_name": device_name,
        "unique_code": code,
        "code_expires_at": code_expires,
        "platform": request.platform,
        "organization_id": request.organization_id
    }).fetchone()

    db.commit()

    return {
        "success": True,
        "data": {
            "id": result.id,
            "device_name": result.device_name,
            "unique_code": result.unique_code,
            "code_expires_at": result.code_expires_at,
            "organization_id": result.organization_id,
            "status": result.status,
            "created_at": result.created_at
        },
        "message": "Monitor device registered. Use the code to activate."
    }


@monitoring_router.post(DeviceRoutes.RELEASE, status_code=status.HTTP_200_OK)
def release_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Release device without deletion

    Sets status to 'inactive', clears code, records release timestamp.
    Sends RESET command to device to clear storage.
    """
    # Check device exists
    device_check = db.execute(
        text("SELECT id, organization_id, device_name FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Update device to inactive
    update_query = text("""
        UPDATE devices
        SET status = 'inactive',
            unique_code = NULL,
            code_expires_at = NULL,
            released_at = NOW()
        WHERE id = :device_id
        RETURNING id, device_name, status, released_at
    """)

    result = db.execute(update_query, {"device_id": device_id}).fetchone()

    # Queue RESET command
    command_query = text("""
        INSERT INTO device_commands (
            device_id, organization_id, command_type, reason,
            status, expires_at, created_at
        )
        VALUES (
            :device_id, :organization_id, 'reset', 'device_released',
            'pending', :expires_at, NOW()
        )
    """)

    db.execute(command_query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
    })

    db.commit()

    return {
        "success": True,
        "data": {
            "id": result.id,
            "device_name": result.device_name,
            "status": result.status,
            "released_at": result.released_at
        },
        "message": f"Device '{result.device_name}' released successfully"
    }


@monitoring_router.get(DeviceRoutes.CONTENT_RESOLVED)
def get_resolved_content(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get content for device using 3-tier priority system

    🔒 SECURITY:
    - Public endpoint (called by player devices)
    - Validates device exists and extracts organization_id
    - ALL content queries filtered by organization_id to prevent cross-org leakage

    Priority Order:
    1. Direct assignments (highest priority)
    2. Tag-based assignments
    3. Playlist assignments (lowest priority)

    Returns merged content list sorted by priority.
    """
    # 🔒 SECURITY FIX: Verify device exists and get organization_id
    device_check = db.execute(
        text("SELECT id, organization_id, device_name FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # 🔒 SECURITY: Extract organization_id for multi-tenant filtering
    organization_id = device_check.organization_id

    if organization_id is None:
        # Device not activated yet - no content should be returned
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "total": 0,
                "items": [],
                "breakdown": {
                    "direct": 0,
                    "tag": 0,
                    "playlist": 0
                }
            }
        }

    # Wrap in try-except to handle missing tables gracefully
    try:
        # Priority 1: Direct content assignments
        # 🔒 SECURITY FIX: Added organization_id filter to contents table
        direct_query = text("""
            SELECT c.id, c.title as name, c.content_type as type, c.file_url as uri, c.duration,
                   ca.priority, 'direct' as source
            FROM content_assignments ca
            JOIN contents c ON c.id = ca.content_id
            WHERE ca.device_id = :device_id
              AND c.organization_id = :organization_id
              AND (ca.expires_at IS NULL OR ca.expires_at > NOW())
            ORDER BY ca.priority DESC
        """)

        direct_results = db.execute(direct_query, {
            "device_id": device_id,
            "organization_id": organization_id
        }).fetchall()

        # Priority 2: Tag-based content
        # 🔒 SECURITY FIX: Added organization_id filter to contents table
        tag_query = text("""
            SELECT DISTINCT c.id, c.title as name, c.content_type as type, c.file_url as uri, c.duration,
                   0 as priority, 'tag' as source
            FROM device_tags dt
            JOIN content_tags ct ON ct.tag_id = dt.tag_id
            JOIN contents c ON c.id = ct.content_id
            WHERE dt.device_id = :device_id
              AND c.organization_id = :organization_id
        """)

        tag_results = db.execute(tag_query, {
            "device_id": device_id,
            "organization_id": organization_id
        }).fetchall()

        # Priority 3: Playlist content
        # 🔒 SECURITY FIX: Added organization_id filters to playlists and contents
        playlist_query = text("""
            SELECT c.id, c.title as name, c.content_type as type, c.file_url as uri, c.duration,
                   0 as priority, 'playlist' as source
            FROM playlist_assignments pa
            JOIN playlists p ON p.id = pa.playlist_id
            JOIN playlist_contents pc ON pc.playlist_id = pa.playlist_id
            JOIN contents c ON c.id = pc.content_id
            WHERE pa.device_id = :device_id
              AND p.organization_id = :organization_id
              AND c.organization_id = :organization_id
            ORDER BY pc.order_index ASC
        """)

        playlist_results = db.execute(playlist_query, {
            "device_id": device_id,
            "organization_id": organization_id
        }).fetchall()

        # Merge all results
        content_items = []

        for row in direct_results:
            content_items.append({
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "uri": row.uri,
                "duration": row.duration,
                "priority": row.priority,
                "source": row.source
            })

        for row in tag_results:
            # Avoid duplicates from direct assignments
            if not any(item['id'] == row.id for item in content_items):
                content_items.append({
                    "id": row.id,
                    "name": row.name,
                    "type": row.type,
                    "uri": row.uri,
                    "duration": row.duration,
                    "priority": row.priority,
                    "source": row.source
                })

        for row in playlist_results:
            # Avoid duplicates
            if not any(item['id'] == row.id for item in content_items):
                content_items.append({
                    "id": row.id,
                    "name": row.name,
                    "type": row.type,
                    "uri": row.uri,
                    "duration": row.duration,
                    "priority": row.priority,
                    "source": row.source
                })

        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "total": len(content_items),
                "items": content_items,
                "breakdown": {
                    "direct": len(direct_results),
                    "tag": len(tag_results),
                    "playlist": len(playlist_results)
                }
            }
        }
    except Exception as e:
        # Tables don't exist yet (Phase 5+ feature)
        # Return empty content - player will show "No content assigned"
        print(f"[Content Resolution] Tables not ready: {e}")
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "total": 0,
                "items": [],
                "breakdown": {
                    "direct": 0,
                    "tag": 0,
                    "playlist": 0
                }
            }
        }


@monitoring_router.post(DeviceRoutes.SPEED_TEST, response_model=SpeedTestResponse, status_code=status.HTTP_201_CREATED)
def record_speed_test(
    device_id: int,
    request: SpeedTestRequest,
    db: Session = Depends(get_db)
):
    """
    Record speed test result (called by player)

    Stores network speed test results for monitoring.
    Calculates quality based on download/upload speeds.
    """
    # Check device exists
    device_check = db.execute(
        text("SELECT id, organization_id FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Calculate quality
    quality = calculate_speed_quality(request.download_speed, request.upload_speed)

    # Insert speed test
    query = text("""
        INSERT INTO device_speed_tests (
            device_id, organization_id, download_speed, upload_speed,
            latency, jitter, packet_loss, dns_server, server_endpoint,
            quality, test_duration_ms, tested_at
        )
        VALUES (
            :device_id, :organization_id, :download_speed, :upload_speed,
            :latency, :jitter, :packet_loss, :dns_server, :server_endpoint,
            :quality, :test_duration_ms, NOW()
        )
        RETURNING id, device_id, download_speed, upload_speed, latency,
                  jitter, packet_loss, dns_server, server_endpoint,
                  quality, test_duration_ms, tested_at
    """)

    result = db.execute(query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "download_speed": request.download_speed,
        "upload_speed": request.upload_speed,
        "latency": request.latency,
        "jitter": request.jitter,
        "packet_loss": request.packet_loss,
        "dns_server": request.dns_server,
        "server_endpoint": request.server_endpoint,
        "quality": quality,
        "test_duration_ms": request.test_duration_ms
    }).fetchone()

    db.commit()

    return SpeedTestResponse(
        id=result.id,
        device_id=result.device_id,
        download_speed=result.download_speed,
        upload_speed=result.upload_speed,
        latency=result.latency,
        jitter=result.jitter,
        packet_loss=result.packet_loss,
        dns_server=result.dns_server,
        server_endpoint=result.server_endpoint,
        quality=result.quality,
        test_duration_ms=result.test_duration_ms,
        tested_at=result.tested_at
    )


@monitoring_router.get(DeviceRoutes.SPEED_TESTS)
def get_speed_test_history(
    device_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get speed test history for device

    Returns recent speed test results, newest first.
    """
    query = text("""
        SELECT id, device_id, download_speed, upload_speed, latency,
               jitter, packet_loss, dns_server, server_endpoint,
               quality, test_duration_ms, tested_at
        FROM device_speed_tests
        WHERE device_id = :device_id
        ORDER BY tested_at DESC
        LIMIT :limit
    """)

    results = db.execute(query, {"device_id": device_id, "limit": limit}).fetchall()

    tests = []
    for row in results:
        tests.append({
            "id": row.id,
            "device_id": row.device_id,
            "download_speed": float(row.download_speed),
            "upload_speed": float(row.upload_speed),
            "latency": row.latency,
            "jitter": row.jitter,
            "packet_loss": float(row.packet_loss) if row.packet_loss else None,
            "dns_server": row.dns_server,
            "server_endpoint": row.server_endpoint,
            "quality": row.quality,
            "test_duration_ms": row.test_duration_ms,
            "tested_at": row.tested_at
        })

    return {
        "success": True,
        "data": {
            "total": len(tests),
            "items": tests
        }
    }


# ============================================================================
# HEALTH MONITORING
# ============================================================================

@monitoring_router.post("/{device_id}/health", response_model=DeviceHealthResponse, status_code=status.HTTP_201_CREATED)
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


@monitoring_router.get("/{device_id}/health", response_model=DeviceHealthWithAlertsResponse)
def get_device_health(
    device_id: int,
    current_user: dict = Depends(require_permission("devices", "read")),
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get latest health metrics with alerts (called by CMS)

    Returns latest health metrics and any active alerts for the device.

    Requires: devices.read permission
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


@monitoring_router.get("/{device_id}/health/history", response_model=HealthHistoryResponse)
def get_device_health_history(
    device_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve (max 7 days)"),
    current_user: dict = Depends(require_permission("devices", "read")),
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get health history for device (called by CMS)

    Returns historical health metrics for charting and analysis.

    Requires: devices.read permission
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


@monitoring_router.get("/organizations/{organization_id}/health/summary", response_model=OrganizationHealthSummaryResponse)
def get_organization_health_summary(
    organization_id: int,
    current_user: dict = Depends(require_permission("devices", "read")),
    health_repo: DeviceHealthRepository = Depends(get_health_repository)
):
    """
    Get organization-wide health summary (called by CMS)

    Returns aggregated health statistics for all devices in organization.
    Useful for dashboard overview.

    Requires: devices.read permission
    """
    # Verify user belongs to organization
    if current_user["organization_id"] != organization_id:
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


@monitoring_router.get("/{device_id}/health/latest", response_model=Optional[DeviceHealthResponse])
def get_latest_device_health(
    device_id: int,
    current_user: dict = Depends(require_permission("devices", "read")),
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get only latest health metrics (called by CMS)

    Returns latest health metrics without alerts.
    Lighter endpoint for simple health checks.

    Requires: devices.read permission
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


@monitoring_router.get("/{device_id}/health/alerts", response_model=List[HealthAlertResponse])
def get_device_health_alerts(
    device_id: int,
    current_user: dict = Depends(require_permission("devices", "read")),
    health_repo: DeviceHealthRepository = Depends(get_health_repository),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get health alerts for device (called by CMS)

    Returns only active health alerts without full metrics.

    Requires: devices.read permission
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


# ============================================================================
# DEVICE LOGS
# ============================================================================

@monitoring_router.post("/{device_id}/logs", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
def create_device_log(
    device_id: int,
    request: CreateLogRequest,
    db: Session = Depends(get_db)
):
    """
    Create device log entry (called by player)

    Devices send console logs to backend for remote debugging.
    No authentication required (device sends with device_id).
    """
    # Validate log level
    valid_levels = ['log', 'info', 'warn', 'error', 'debug']
    if request.log_level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log_level. Must be one of: {', '.join(valid_levels)}"
        )

    # Check device exists and get organization_id
    device_check = db.execute(
        text("SELECT id, organization_id FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Insert log
    query = text("""
        INSERT INTO device_logs (
            device_id, organization_id, log_level, message, source,
            stack_trace, user_agent, url, recorded_at
        )
        VALUES (
            :device_id, :organization_id, :log_level, :message, :source,
            :stack_trace, :user_agent, :url, NOW()
        )
        RETURNING id, device_id, log_level, message, source,
                  stack_trace, user_agent, url, recorded_at
    """)

    result = db.execute(query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "log_level": request.log_level,
        "message": request.message,
        "source": request.source,
        "stack_trace": request.stack_trace,
        "user_agent": request.user_agent,
        "url": request.url
    }).fetchone()

    db.commit()

    return LogResponse(
        id=result.id,
        device_id=result.device_id,
        log_level=result.log_level,
        message=result.message,
        source=result.source,
        stack_trace=result.stack_trace,
        user_agent=result.user_agent,
        url=result.url,
        recorded_at=result.recorded_at)


@monitoring_router.get("/{device_id}/logs", response_model=LogListResponse)
def get_device_logs(
    device_id: int,
    log_level: Optional[str] = Query(None, description="Filter by log level: log, info, warn, error, debug"),
    limit: int = Query(100, ge=1, le=500, description="Number of logs to return"),
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    db: Session = Depends(get_db)
):
    """
    Get device logs (called by CMS)

    Returns paginated list of device logs with optional level filter.
    Sorted by timestamp DESC (newest first).
    """
    # Build query
    where_clause = "WHERE device_id = :device_id"
    params = {"device_id": device_id, "limit": limit, "skip": skip}

    if log_level:
        where_clause += " AND log_level = :log_level"
        params["log_level"] = log_level

    # Get total count
    count_query = text(f"SELECT COUNT(*) as total FROM device_logs {where_clause}")
    total = db.execute(count_query, params).fetchone().total

    # Get logs
    query = text(f"""
        SELECT id, device_id, log_level, message, source,
               stack_trace, user_agent, url, recorded_at
        FROM device_logs
        {where_clause}
        ORDER BY recorded_at DESC
        LIMIT :limit OFFSET :skip
    """)

    results = db.execute(query, params).fetchall()

    logs = []
    for row in results:
        logs.append(LogResponse(
            id=row.id,
            device_id=row.device_id,
            log_level=row.log_level,
            message=row.message,
            source=row.source,
            stack_trace=row.stack_trace,
            user_agent=row.user_agent,
            url=row.url,
            recorded_at=row.recorded_at))

    return LogListResponse(total=total, items=logs)


@monitoring_router.delete("/{device_id}/logs", status_code=status.HTTP_204_NO_CONTENT)
def clear_device_logs(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Clear all logs for device (called by CMS)

    Permanently deletes all log entries for the specified device.
    """
    query = text("""
        DELETE FROM device_logs
        WHERE device_id = :device_id
    """)

    db.execute(query, {"device_id": device_id})
    db.commit()

    return None


@monitoring_router.get("/{device_id}/logs/latest", response_model=LogListResponse)
def get_latest_device_logs(
    device_id: int,
    count: int = Query(20, ge=1, le=100, description="Number of latest logs to return"),
    db: Session = Depends(get_db)
):
    """
    Get latest N logs for device (called by CMS)

    Convenience endpoint to quickly get recent logs.
    """
    query = text("""
        SELECT id, device_id, log_level, message, source,
               stack_trace, user_agent, url, recorded_at
        FROM device_logs
        WHERE device_id = :device_id
        ORDER BY recorded_at DESC
        LIMIT :count
    """)

    results = db.execute(query, {"device_id": device_id, "count": count}).fetchall()

    logs = []
    for row in results:
        logs.append(LogResponse(
            id=row.id,
            device_id=row.device_id,
            log_level=row.log_level,
            message=row.message,
            source=row.source,
            stack_trace=row.stack_trace,
            user_agent=row.user_agent,
            url=row.url,
            recorded_at=row.recorded_at))

    return LogListResponse(total=len(logs), items=logs)


@monitoring_router.get("/{device_id}/test-endpoint")
def test_endpoint(device_id: int):
    """Simple test endpoint to verify routing works"""
    return {"message": f"Test endpoint works for device {device_id}", "success": True}


@monitoring_router.post("/{device_id}/logs/batch", response_model=SaveDeviceLogsResponse, status_code=status.HTTP_201_CREATED)
def save_console_logs_batch(
    device_id: int,
    request: BatchDeviceLogsRequest,
    db: Session = Depends(get_db)
):
    """
    Save batch of console logs from player browser (Console Interceptor)

    This endpoint receives batched console.log(), console.error(), etc. from player.
    Player sends logs in batches every 5-60 seconds to minimize network overhead.

    Features:
    - Bulk insert optimization (single SQL statement)
    - Multi-tenancy support (organization_id)
    - XSS sanitization (backend validation)
    - Rate limiting (20 batches/min per device)

    No JWT auth required - device_id verification is sufficient.
    """
    from services.device.use_cases.save_device_logs_batch import SaveDeviceLogsBatch

    try:
        use_case = SaveDeviceLogsBatch(db)
        result = use_case.execute(device_id=device_id, dto=request)

        return SaveDeviceLogsResponse(
            success=True,
            logs_saved=result['logs_saved'],
            message=result['message']
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# REMOTE COMMANDS
# ============================================================================

@monitoring_router.post("/{device_id}/commands", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
def send_command_to_device(
    device_id: int,
    request: SendCommandRequest,
    db: Session = Depends(get_db)
):
    """
    Send command to device

    Admin queues a command that device will execute during next heartbeat.
    Command expires after 7 days if not executed.
    """
    # Validate command type
    valid_commands = ['reset', 'refresh', 'reload', 'reboot', 'screenshot', 'volume', 'brightness', 'speed_test', 'update_content']
    if request.command_type not in valid_commands:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid command_type. Must be one of: {', '.join(valid_commands)}"
        )

    # Check device exists
    device_check = db.execute(
        text("SELECT id, organization_id, status FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Create command
    query = text("""
        INSERT INTO device_commands (
            device_id, organization_id, command_type, parameters, reason,
            status, expires_at, created_at
        )
        VALUES (
            :device_id, :organization_id, :command_type, :parameters, :reason,
            'pending', :expires_at, NOW()
        )
        RETURNING id, device_id, organization_id, command_type, parameters, reason,
                  status, sent_at, executed_at, error_message, created_at, expires_at
    """)

    params_json = json.dumps(request.parameters) if request.parameters else None
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    result = db.execute(query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "command_type": request.command_type,
        "parameters": params_json,
        "reason": request.reason,
        "expires_at": expires_at
    }).fetchone()

    db.commit()

    # Convert to response
    return CommandResponse(
        id=result.id,
        device_id=result.device_id,
        command_type=result.command_type,
        parameters=json.loads(result.parameters) if result.parameters else None,
        reason=result.reason,
        status=result.status,
        sent_at=result.sent_at,
        executed_at=result.executed_at,
        error_message=result.error_message,
        created_at=result.created_at,
        expires_at=result.expires_at
    )


@monitoring_router.get("/{device_id}/commands/pending", response_model=CommandListResponse)
def get_pending_commands(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get pending commands for device (called by player)

    Device polls this endpoint during heartbeat to check for commands to execute.
    Returns only non-expired pending commands.
    """
    query = text("""
        SELECT id, device_id, command_type, parameters, reason,
               status, sent_at, executed_at, error_message, created_at, expires_at
        FROM device_commands
        WHERE device_id = :device_id
          AND status = 'pending'
          AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY created_at ASC
    """)

    results = db.execute(query, {"device_id": device_id}).fetchall()

    commands = []
    for row in results:
        commands.append(CommandResponse(
            id=row.id,
            device_id=row.device_id,
            command_type=row.command_type,
            parameters=json.loads(row.parameters) if row.parameters else None,
            reason=row.reason,
            status=row.status,
            sent_at=row.sent_at,
            executed_at=row.executed_at,
            error_message=row.error_message,
            created_at=row.created_at,
            expires_at=row.expires_at
        ))

    return CommandListResponse(total=len(commands), items=commands)


@monitoring_router.post("/{device_id}/commands/{command_id}/execute", status_code=status.HTTP_200_OK)
def execute_command(
    device_id: int,
    command_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark command as executed (called by player after execution)

    Device calls this after successfully executing a command.
    Updates command status to 'executed' and records execution timestamp.
    """
    # Update command status
    query = text("""
        UPDATE device_commands
        SET status = 'executed',
            executed_at = NOW(),
            sent_at = COALESCE(sent_at, NOW())
        WHERE id = :command_id
          AND device_id = :device_id
          AND status = 'pending'
        RETURNING id, command_type, executed_at
    """)

    result = db.execute(query, {
        "command_id": command_id,
        "device_id": device_id
    }).fetchone()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command {command_id} not found or already executed"
        )

    db.commit()

    return {
        "success": True,
        "message": f"Command '{result.command_type}' marked as executed",
        "command_id": result.id,
        "executed_at": result.executed_at
    }


@monitoring_router.get("/{device_id}/commands", response_model=CommandListResponse)
def get_device_commands(
    device_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, executed, failed, expired"),
    limit: int = Query(50, ge=1, le=200, description="Number of commands to return"),
    skip: int = Query(0, ge=0, description="Number of commands to skip"),
    db: Session = Depends(get_db)
):
    """
    Get command history for device (called by CMS)

    Returns paginated list of commands with optional status filter.
    """
    # Build query
    where_clause = "WHERE device_id = :device_id"
    params = {"device_id": device_id, "limit": limit, "skip": skip}

    if status_filter:
        where_clause += " AND status = :status"
        params["status"] = status_filter

    # Get total count
    count_query = text(f"SELECT COUNT(*) as total FROM device_commands {where_clause}")
    total = db.execute(count_query, params).fetchone().total

    # Get commands
    query = text(f"""
        SELECT id, device_id, command_type, parameters, reason,
               status, sent_at, executed_at, error_message, created_at, expires_at
        FROM device_commands
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)

    results = db.execute(query, params).fetchall()

    commands = []
    for row in results:
        commands.append(CommandResponse(
            id=row.id,
            device_id=row.device_id,
            command_type=row.command_type,
            parameters=json.loads(row.parameters) if row.parameters else None,
            reason=row.reason,
            status=row.status,
            sent_at=row.sent_at,
            executed_at=row.executed_at,
            error_message=row.error_message,
            created_at=row.created_at,
            expires_at=row.expires_at
        ))

    return CommandListResponse(total=total, items=commands)


@monitoring_router.post("/{device_id}/commands/reset", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
def send_reset_command(
    device_id: int,
    reason: Optional[str] = Query("manual_reset", description="Reason for reset"),
    db: Session = Depends(get_db)
):
    """
    Quick endpoint to send reset command

    Convenience endpoint for sending reset command (clear storage + reload).
    """
    request = SendCommandRequest(
        command_type="reset",
        reason=reason
    )

    return send_command_to_device(device_id, request, db)


# ============================================================================
# CONSOLE CONTROL (WebSocket) - Player Control Connection
# ============================================================================

@monitoring_router.websocket("/{device_id}/console/control")
async def console_control_websocket(
    websocket: WebSocket,
    device_id: int
):
    """
    Player control WebSocket endpoint - Bidirectional communication

    Architecture: Hybrid Console Streaming

    Responsibilities:
    1. Accept WebSocket connection from player
    2. Validate device_id exists in database
    3. Register player with WebSocket Manager
    4. Listen for incoming logs from player (Player → Backend)
    5. Listen for commands from Redis (Backend → Player)
    6. Broadcast logs to subscribed admins
    7. Handle graceful disconnect

    Message Protocol:

    INCOMING (Player → Backend):
    {
        "type": "console_logs",
        "logs": [
            {
                "level": "log" | "info" | "warn" | "error",
                "message": "Console message",
                "timestamp": "2025-01-13T10:30:00.000Z",
                "stack": "Error stack trace (optional)"
            }
        ],
        "logType": "historical" | "realtime"
    }

    OUTGOING (Backend → Player via Redis):
    {
        "command": "start_streaming" | "stop_streaming",
        "data": {},
        "timestamp": "2025-01-13T10:30:00.000Z"
    }
    """
    db_session = None
    organization_id = None
    ws_manager = get_ws_manager()

    try:
        # 1. Accept WebSocket connection
        await websocket.accept()
        logger.info(f"[PlayerControl] Device {device_id} attempting to connect control WebSocket")

        # 2. Validate device_id and get organization_id (multi-tenant security)
        db_session = next(get_db())
        device_repo = DeviceRepository(db_session)

        # Don't filter by org - player self-identifies by device_id
        device = device_repo.find_by_id(device_id, organization_id=None)

        if not device or not device.organization_id:
            logger.warning(f"[PlayerControl] ❌ Device {device_id} not found or not activated")
            await websocket.send_json({
                "error": "Device not found or not activated",
                "code": "DEVICE_NOT_FOUND"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        organization_id = device.organization_id
        logger.info(f"[PlayerControl] ✅ Device {device_id} validated (org: {organization_id})")

        # 3. Register player control WebSocket
        await ws_manager.register_player_control(device_id, websocket)
        logger.info(f"[PlayerControl] Player {device_id} registered for control commands")

        # Send connection confirmation
        await websocket.send_json({
            "event": "control.connected",
            "data": {
                "device_id": device_id,
                "organization_id": organization_id,
                "message": "Control WebSocket connected successfully"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # 4. Start concurrent listeners (run both simultaneously)
        await asyncio.gather(
            _listen_player_messages(websocket, device_id, organization_id, ws_manager),
            _listen_redis_commands(websocket, device_id, ws_manager),
            return_exceptions=True
        )

    except WebSocketDisconnect:
        logger.info(f"[PlayerControl] Device {device_id} disconnected control WebSocket")
    except Exception as e:
        logger.error(f"[PlayerControl] Error in control WebSocket for device {device_id}: {e}")
    finally:
        # 5. Cleanup: Unregister player control WebSocket
        if organization_id:
            await ws_manager.unregister_player_control(device_id)
            logger.info(f"[PlayerControl] Device {device_id} unregistered from control WebSocket")

        # Close database session
        if db_session:
            db_session.close()

        # Close WebSocket connection
        try:
            await websocket.close()
        except:
            pass


async def _listen_player_messages(
    websocket: WebSocket,
    device_id: int,
    organization_id: int,
    ws_manager
):
    """
    Listen for incoming messages from player

    Handles:
    - console_logs: Batch of console logs from player
    - ping: Heartbeat messages
    """
    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")

            logger.debug(f"[PlayerControl] Received message from device {device_id}: {message_type}")

            if message_type == "console_logs":
                logs = message.get("logs", [])
                log_type = message.get("logType", "realtime")

                if not logs:
                    logger.warning(f"[PlayerControl] Device {device_id} sent empty logs array")
                    continue

                logger.info(
                    f"[PlayerControl] Device {device_id} sent {len(logs)} {log_type} console logs "
                    f"(org: {organization_id})"
                )

                # Validate log structure
                valid_logs = []
                for log in logs:
                    if _validate_log_entry(log):
                        valid_logs.append(log)
                    else:
                        logger.warning(f"[PlayerControl] Invalid log entry from device {device_id}: {log}")

                if not valid_logs:
                    logger.warning(f"[PlayerControl] No valid logs from device {device_id}")
                    continue

                # Add logType metadata
                enriched_logs = []
                for log in valid_logs:
                    enriched_log = log.copy()
                    enriched_log["logType"] = log_type
                    enriched_logs.append(enriched_log)

                # Broadcast to subscribed admins
                logger.info(
                    f"[PlayerControl] Broadcasting {len(enriched_logs)} {log_type} logs "
                    f"from device {device_id} to subscribed admins"
                )

                await ws_manager.broadcast_console_log(
                    device_id=device_id,
                    organization_id=organization_id,
                    logs=enriched_logs
                )

                logger.info(f"[PlayerControl] ✅ Broadcast complete for device {device_id}")

            elif message_type == "ping":
                await websocket.send_json({
                    "event": "control.pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            else:
                logger.warning(f"[PlayerControl] Unknown message type from device {device_id}: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"[PlayerControl] Player {device_id} disconnected during message listening")
        raise
    except Exception as e:
        logger.error(f"[PlayerControl] Error listening to player {device_id} messages: {e}")
        raise


async def _listen_redis_commands(
    websocket: WebSocket,
    device_id: int,
    ws_manager
):
    """
    Listen for commands from Redis and forward to player

    Commands:
    - start_streaming: Send buffered + real-time logs
    - stop_streaming: Stop sending logs, keep buffering
    """
    try:
        # Check if Redis is enabled
        if not ws_manager._use_redis or not ws_manager._command_pubsub:
            logger.info(f"[PlayerControl] Redis disabled - relying on WebSocket Manager command listener")
            while True:
                await asyncio.sleep(30)
            return

        # Subscribe to device-specific command channel
        channel = f"command:{device_id}"
        pubsub = ws_manager._redis_client.pubsub()
        await pubsub.subscribe(channel)

        logger.info(f"[PlayerControl] Listening for commands on Redis channel: {channel}")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    command = data.get("command")
                    command_data = data.get("data", {})
                    timestamp = data.get("timestamp")

                    logger.info(f"[PlayerControl] Received command '{command}' from Redis for device {device_id}")

                    # Forward command to player via WebSocket
                    await websocket.send_json({
                        "command": command,
                        "data": command_data,
                        "timestamp": timestamp
                    })

                    logger.info(f"[PlayerControl] ✅ Forwarded command '{command}' to player {device_id}")

                except json.JSONDecodeError as e:
                    logger.error(f"[PlayerControl] Failed to parse command message: {e}")
                except Exception as e:
                    logger.error(f"[PlayerControl] Error forwarding command to player {device_id}: {e}")

    except WebSocketDisconnect:
        logger.info(f"[PlayerControl] Player {device_id} disconnected during command listening")
        raise
    except Exception as e:
        logger.error(f"[PlayerControl] Error listening to Redis commands for device {device_id}: {e}")
        raise


def _validate_log_entry(log: Dict[str, Any]) -> bool:
    """
    Validate console log entry structure

    Required fields:
    - level: string (log, info, warn, error, debug)
    - message: string
    - timestamp: string (ISO 8601)
    """
    required_fields = ["level", "message", "timestamp"]

    # Check required fields exist
    for field in required_fields:
        if field not in log:
            logger.warning(f"Log entry missing required field: {field}")
            return False

    # Validate level
    valid_levels = ["log", "info", "warn", "error", "debug"]
    if log["level"] not in valid_levels:
        logger.warning(f"Invalid log level: {log['level']}")
        return False

    # Validate message is string
    if not isinstance(log["message"], str):
        logger.warning(f"Log message is not a string: {type(log['message'])}")
        return False

    # Validate timestamp is string
    if not isinstance(log["timestamp"], str):
        logger.warning(f"Log timestamp is not a string: {type(log['timestamp'])}")
        return False

    return True


# ============================================================================
# CONSOLE STREAMING (WebSocket) - Admin Subscription
# ============================================================================

@monitoring_router.websocket("/{device_id}/console/stream")
async def stream_console_logs(
    websocket: WebSocket,
    device_id: int
):
    """
    Admin WebSocket endpoint to subscribe to device console logs

    Flow:
    1. Admin opens modal → establishes WebSocket connection
    2. Subscribe to device console logs (with organization_id)
    3. Backend signals player to start streaming (if first subscriber)
    4. Receive real-time console logs from device
    5. Unsubscribe when modal closed
    6. Backend signals player to stop streaming (if last subscriber)

    No authentication needed here - handled by main WebSocket connection
    """
    await websocket.accept()

    organization_id = None
    db_session = None

    try:
        # Get user_id from query params
        user_id = int(websocket.query_params.get("user_id", 0))
        if not user_id:
            print(f"[Console] ❌ No user_id in query params")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get device to retrieve organization_id
        db_session = next(get_db())
        device_repo = DeviceRepository(db_session)
        device = device_repo.find_by_id(device_id, organization_id=None)

        if not device:
            print(f"[Console] ❌ Device {device_id} not found")
            logger.error(f"Device {device_id} not found for console subscription")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if not device.organization_id:
            print(f"[Console] ❌ Device {device_id} has no organization_id")
            logger.error(f"Device {device_id} has no organization_id")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        organization_id = device.organization_id

        # Subscribe to console logs
        print(f"[Console] Subscribing admin {user_id} to device {device_id} console stream (org: {organization_id})")
        success = await get_ws_manager().subscribe_to_console(
            device_id=device_id,
            admin_user_id=user_id,
            organization_id=organization_id,
            websocket=websocket
        )
        if not success:
            print(f"[Console] ❌ Failed to subscribe admin {user_id}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        print(f"[Console] ✅ Admin {user_id} subscribed to device {device_id} console stream (org: {organization_id})")
        logger.info(f"Admin {user_id} subscribed to device {device_id} console stream (org: {organization_id})")

        # Send initial confirmation
        await websocket.send_json({
            "event": "console.subscribed",
            "data": {
                "device_id": device_id,
                "organization_id": organization_id,
                "message": "Successfully subscribed to console logs"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep connection alive - one-way connection (server -> client)
        try:
            while True:
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            logger.info(f"Admin {user_id} disconnected from device {device_id} console stream (org: {organization_id})")

    except Exception as e:
        logger.error(f"Error in console stream: {e}")
    finally:
        # Unsubscribe on disconnect
        try:
            if organization_id:
                await get_ws_manager().unsubscribe_from_console(
                    device_id=device_id,
                    admin_user_id=user_id,
                    organization_id=organization_id
                )
                logger.info(f"Admin {user_id} unsubscribed from device {device_id} console (org: {organization_id})")
        except:
            pass

        # Close database session
        if db_session:
            db_session.close()

        try:
            await websocket.close()
        except:
            pass


# ============================================================================
# CONNECTION LOGS
# ============================================================================

@monitoring_router.get("/{device_id}/connection-logs", response_model=ConnectionLogListResponse)
def get_device_connection_logs(
    device_id: int,
    event_type: Optional[str] = Query(None, description="Filter by event type: network, server, speed_test"),
    limit: int = Query(50, ge=1, le=500, description="Number of logs to return"),
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    db: Session = Depends(get_db)
):
    """
    Get device connection logs (called by CMS)

    Returns paginated list of connection logs with optional event_type filter.
    Sorted by logged_at DESC (newest first).
    """
    # Build query
    where_clause = "WHERE device_id = :device_id"
    params = {"device_id": device_id, "limit": limit, "skip": skip}

    if event_type:
        where_clause += " AND event_type = :event_type"
        params["event_type"] = event_type

    # Get total count
    count_query = text(f"SELECT COUNT(*) as total FROM device_connection_logs {where_clause}")
    total = db.execute(count_query, params).fetchone().total

    # Get logs
    query = text(f"""
        SELECT id, device_id, logged_at, event_type, status, latency_ms,
               error_message, download_speed_mbps, upload_speed_mbps,
               connection_type, effective_type, rtt_ms, endpoint, http_status,
               test_trigger, test_duration_ms, metadata, created_at
        FROM device_connection_logs
        {where_clause}
        ORDER BY logged_at DESC
        LIMIT :limit OFFSET :skip
    """)

    results = db.execute(query, params).fetchall()

    logs = []
    for row in results:
        logs.append(ConnectionLogResponse(
            id=row.id,
            device_id=row.device_id,
            logged_at=row.logged_at,
            event_type=row.event_type,
            status=row.status,
            latency_ms=row.latency_ms,
            error_message=row.error_message,
            download_speed_mbps=row.download_speed_mbps,
            upload_speed_mbps=row.upload_speed_mbps,
            connection_type=row.connection_type,
            effective_type=row.effective_type,
            rtt_ms=row.rtt_ms,
            endpoint=row.endpoint,
            http_status=row.http_status,
            test_trigger=row.test_trigger,
            test_duration_ms=row.test_duration_ms,
            metadata=row.metadata if row.metadata else {},
            created_at=row.created_at
        ))

    return ConnectionLogListResponse(total=total, items=logs)


@monitoring_router.post("/{device_id}/connection-logs", status_code=status.HTTP_201_CREATED)
def save_connection_logs(
    device_id: int,
    dto: SaveConnectionLogsDTO,
    db: Session = Depends(get_db)
):
    """
    Save batch of connection logs from player device

    Player automatically sends logs every 5 minutes containing:
    - Network status changes (online/offline)
    - Server connectivity (connected/disconnected)
    - Speed test results (hourly)

    No JWT auth required - device_id verification is sufficient.
    """
    from services.device.use_cases.save_connection_logs import SaveConnectionLogs

    try:
        use_case = SaveConnectionLogs(db)
        result = use_case.execute(device_id=device_id, dto=dto)

        return success_response(
            data=result,
            message=f"Successfully saved {result['count']} connection logs"
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
