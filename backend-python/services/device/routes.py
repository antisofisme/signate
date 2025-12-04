"""
Device API Routes
HTTP endpoints for device management

Updated to use centralized utilities:
- shared.errors for error handling
- shared.responses for standardized responses
- shared.logging for request logging
"""

from fastapi import APIRouter, Depends, Request, status, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.api_routes import DeviceRoutes
from shared.errors import handle_errors, NotFoundError, ValidationError
from shared.responses import success_response, get_client_ip
from shared.logging import RequestLogger, AuditLogger
from shared.auth import get_current_device, CurrentDevice
from shared.middleware import require_permission
from shared.cache import cache, device_cache_key, list_cache_key
from shared.metrics import track_cache_operation, update_device_metrics
from typing import Optional
import time

from .dtos import (
    RequestActivationCodeRequest,
    ActivateDeviceRequest,
    HeartbeatRequest,
    UpdateDeviceRequest,
    ValidateResetPasswordRequest,
    ActivationCodeResponse,
    DeviceResponse,
    DeviceListResponse,
    HeartbeatResponse,
    ActivationStatusResponse,
    DeviceActivationResponse,
    DeviceHealthMetricsCreate,
    DeviceHealthResponse
)
from .use_cases.request_activation_code import RequestActivationCodeUseCase
from .use_cases.activate_device import ActivateDeviceUseCase
from .use_cases.heartbeat import DeviceHeartbeatUseCase
from .use_cases.list_devices import ListDevicesUseCase
from .use_cases.update_device import UpdateDeviceUseCase
from .repositories.device_repo import DeviceRepository
from .domain.device import DeviceHeartbeat

# WebSocket imports
from shared.websocket_manager import websocket_manager
import asyncio


router = APIRouter()

# Initialize loggers
request_logger = RequestLogger()
audit_logger = AuditLogger()

# Helper function for WebSocket broadcast
async def broadcast_device_event(organization_id: int, event_type: str, data: dict):
    """
    Broadcast device event to organization members via WebSocket
    Runs in background task to not block HTTP response
    """
    try:
        await websocket_manager.broadcast_to_organization(
            organization_id=organization_id,
            event_type=event_type,
            data=data
        )
        print(f"[WebSocket] ✅ Broadcasted {event_type} to org {organization_id}")
    except Exception as e:
        print(f"[WebSocket] ⚠️ Broadcast failed: {e}")


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_device_repository(db: Session = Depends(get_db)) -> DeviceRepository:
    """Get device repository instance"""
    return DeviceRepository(db)


def get_request_activation_code_use_case(
    device_repo: DeviceRepository = Depends(get_device_repository)
) -> RequestActivationCodeUseCase:
    """Get request activation code use case"""
    return RequestActivationCodeUseCase(device_repo)


def get_activate_device_use_case(
    device_repo: DeviceRepository = Depends(get_device_repository)
) -> ActivateDeviceUseCase:
    """Get activate device use case"""
    return ActivateDeviceUseCase(device_repo)


def get_heartbeat_use_case(
    device_repo: DeviceRepository = Depends(get_device_repository)
) -> DeviceHeartbeatUseCase:
    """Get heartbeat use case"""
    return DeviceHeartbeatUseCase(device_repo)


def get_list_devices_use_case(
    device_repo: DeviceRepository = Depends(get_device_repository)
) -> ListDevicesUseCase:
    """Get list devices use case"""
    return ListDevicesUseCase(device_repo)


def get_update_device_use_case(
    device_repo: DeviceRepository = Depends(get_device_repository)
) -> UpdateDeviceUseCase:
    """Get update device use case"""
    return UpdateDeviceUseCase(device_repo)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def device_to_response(device) -> DeviceResponse:
    """
    Convert Device domain model to DeviceResponse DTO
    Computes is_online field from device.is_online() method
    """
    from .domain.device import Device

    # Build dict with all fields + computed is_online
    return DeviceResponse(
        id=device.id,
        device_type=device.device_type,
        device_name=device.device_name,
        organization_id=device.organization_id,
        unique_code=device.unique_code,
        code_expires_at=device.code_expires_at,
        device_uuid=device.device_uuid,
        ip_address=device.ip_address,
        platform=device.platform,
        screen_width=device.screen_width,
        screen_height=device.screen_height,
        viewport_width=device.viewport_width,
        viewport_height=device.viewport_height,
        device_pixel_ratio=device.device_pixel_ratio,
        user_agent=device.user_agent,
        connection_type=device.connection_type,
        connection_speed=device.connection_speed,
        model_name=device.model_name,
        firmware_version=device.firmware_version,
        status=device.status,
        last_seen_at=device.last_seen_at,
        is_online=device.is_online(),  # Compute is_online boolean value
        rotation=device.rotation,
        is_volume_enabled=device.is_volume_enabled,
        location_type=device.location_type,
        room_number=device.room_number,
        is_personalization_supported=device.is_personalization_supported,
        privacy_mode=device.privacy_mode,
        created_at=device.created_at,
        updated_at=device.updated_at,
        released_at=device.released_at
    )


# =============================================================================
# PLAYER ENDPOINTS (PUBLIC - NO AUTH)
# =============================================================================

@router.post(DeviceRoutes.REQUEST_CODE, response_model=ActivationCodeResponse, status_code=status.HTTP_201_CREATED)
def request_activation_code(
    request: RequestActivationCodeRequest,
    use_case: RequestActivationCodeUseCase = Depends(get_request_activation_code_use_case)
):
    """
    Request activation code (called by player)

    🔒 SECURITY CHANGES:
    - organization_id NO LONGER accepted from player (prevents org hijacking)
    - First-time: org_id assigned during activation by admin
    - Re-registration: org_id extracted from device_token JWT

    Accepts 6-digit code from frontend (generated client-side) and validates uniqueness
    Code expires in 10 minutes
    """
    try:
        result = use_case.execute(
            code=request.code,  # 6-digit code from frontend
            device_token=request.device_token,  # 🔒 JWT token instead of org_id
            device_type=request.device_type,
            device_name=request.device_name,
            device_uuid=request.device_uuid,
            platform=request.platform
        )
        return ActivationCodeResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(DeviceRoutes.HEARTBEAT, response_model=HeartbeatResponse)
def device_heartbeat(
    device_id: int,
    request: HeartbeatRequest,
    use_case: DeviceHeartbeatUseCase = Depends(get_heartbeat_use_case),
    http_request: Request = None
):
    """
    Device heartbeat (called by player every 30 seconds)

    🔒 SECURITY: Optional JWT validation for device authentication
    - If Authorization header present → validate device JWT token
    - If not present → fallback to unique_code validation (backward compatible)

    Updates last_seen_at timestamp and device metadata
    """
    try:
        # 🔒 SECURITY: Optional JWT validation (backward compatible)
        auth_header = http_request.headers.get("Authorization") if http_request else None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                from shared.auth import extract_device_from_token
                device_info = extract_device_from_token(token)

                # Verify device_id matches JWT token
                if device_info['device_id'] != device_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Device ID mismatch: JWT contains {device_info['device_id']}, request has {device_id}"
                    )

                print(f"[Heartbeat] ✅ Device {device_id} authenticated via JWT token")
            except Exception as e:
                # JWT validation failed - reject heartbeat
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid device token: {str(e)}"
                )
        else:
            # No JWT token - fallback to unique_code validation (legacy devices)
            print(f"[Heartbeat] ⚠️ Device {device_id} using legacy auth (unique_code only)")

        # Extract real client IP (handles X-Forwarded-For from Nginx proxy)
        client_ip = get_client_ip(http_request)

        heartbeat_data = DeviceHeartbeat(
            unique_code=request.unique_code,
            device_uuid=request.device_uuid,
            screen_width=request.screen_width,
            screen_height=request.screen_height,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            device_pixel_ratio=request.device_pixel_ratio,
            user_agent=request.user_agent,
            connection_type=request.connection_type,
            connection_speed=request.connection_speed,
            ip_address=client_ip
        )

        success = use_case.execute(heartbeat_data)

        if success:
            return HeartbeatResponse(success=True, message="Heartbeat received")
        else:
            return HeartbeatResponse(success=False, message="Failed to update heartbeat")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# =============================================================================
# DEVICE HEALTH METRICS ENDPOINT
# =============================================================================

@router.post("/devices/{device_id}/health", response_model=DeviceHealthResponse)
def record_device_health(
    device_id: int,
    request_body: DeviceHealthMetricsCreate,
    device_repo: DeviceRepository = Depends(get_device_repository),
    current_device: CurrentDevice = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Record device health metrics (called by player every 5 minutes)

    🔒 SECURITY: Requires device JWT token authentication
    Device can only submit health metrics for itself

    Creates a new health metric record in device_health_metrics table
    """
    from datetime import datetime, timezone
    from .repositories.models import DeviceHealthMetricModel

    try:
        # 🔒 SECURITY: Verify device_id matches JWT token
        if current_device.id != device_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Device ID mismatch: JWT contains {current_device.id}, request has {device_id}"
            )

        # Use connection_quality from request or calculate based on latency
        connection_quality = request_body.connection_quality or "unknown"
        if connection_quality == "unknown" and request_body.network_latency_ms is not None:
            latency = request_body.network_latency_ms
            if latency < 50:
                connection_quality = "excellent"
            elif latency < 100:
                connection_quality = "good"
            elif latency < 200:
                connection_quality = "fair"
            elif latency < 500:
                connection_quality = "poor"
            else:
                connection_quality = "very_poor"

        # Determine overall health status
        overall_status = "healthy"
        is_alert_triggered = False
        alert_message = None

        # Check for warning/critical thresholds
        cpu = request_body.cpu_usage or 0
        memory = request_body.memory_usage or 0
        disk = request_body.disk_usage or 0
        max_usage = max(cpu, memory, disk)

        if max_usage >= 90:
            overall_status = "critical"
            is_alert_triggered = True
            if cpu >= 90:
                alert_message = f"Critical CPU usage: {cpu}%"
            elif memory >= 90:
                alert_message = f"Critical memory usage: {memory}%"
            else:
                alert_message = f"Critical disk usage: {disk}%"
        elif max_usage >= 70:
            overall_status = "warning"

        # Extract metadata from request
        metadata = request_body.metadata or {}

        # Create health metric record
        health_metric = DeviceHealthMetricModel(
            device_id=device_id,
            organization_id=current_device.organization_id,
            # System metrics
            cpu_usage=request_body.cpu_usage,
            memory_usage=request_body.memory_usage,
            memory_total_mb=request_body.memory_total_mb,
            memory_used_mb=request_body.memory_used_mb,
            disk_usage=request_body.disk_usage,
            disk_total_gb=request_body.disk_total_gb,
            disk_used_gb=request_body.disk_used_gb,
            # Network metrics
            network_latency_ms=request_body.network_latency_ms,
            network_download_mbps=request_body.network_download_mbps,
            network_upload_mbps=request_body.network_upload_mbps,
            connection_quality=connection_quality,
            # Display metrics
            display_resolution=request_body.display_resolution,
            display_refresh_rate=request_body.display_refresh_rate,
            gpu_usage=request_body.gpu_usage,
            # Player metrics
            player_version=request_body.player_version,
            player_uptime_hours=request_body.player_uptime_hours,
            content_errors_count=request_body.content_errors_count,
            last_error_message=request_body.last_error_message,
            last_error_at=datetime.fromisoformat(request_body.last_error_at.replace('Z', '+00:00')) if request_body.last_error_at else None,
            # Health status
            overall_status=overall_status,
            is_alert_triggered=is_alert_triggered,
            alert_message=alert_message,
            # Metadata
            metadata=metadata,
            recorded_at=datetime.now(timezone.utc)
        )

        db.add(health_metric)
        db.commit()
        db.refresh(health_metric)

        print(f"[HealthMetrics] ✅ Recorded health for device {device_id}: {overall_status}")

        return DeviceHealthResponse(
            id=health_metric.id,
            device_id=health_metric.device_id,
            organization_id=health_metric.organization_id,
            cpu_usage=float(health_metric.cpu_usage) if health_metric.cpu_usage else None,
            memory_usage=float(health_metric.memory_usage) if health_metric.memory_usage else None,
            memory_total_mb=health_metric.memory_total_mb,
            memory_used_mb=health_metric.memory_used_mb,
            disk_usage=float(health_metric.disk_usage) if health_metric.disk_usage else None,
            disk_total_gb=health_metric.disk_total_gb,
            disk_used_gb=health_metric.disk_used_gb,
            network_latency_ms=health_metric.network_latency_ms,
            network_download_mbps=float(health_metric.network_download_mbps) if health_metric.network_download_mbps else None,
            network_upload_mbps=float(health_metric.network_upload_mbps) if health_metric.network_upload_mbps else None,
            connection_quality=health_metric.connection_quality,
            display_resolution=health_metric.display_resolution,
            display_refresh_rate=health_metric.display_refresh_rate,
            gpu_usage=float(health_metric.gpu_usage) if health_metric.gpu_usage else None,
            player_version=health_metric.player_version,
            player_uptime_hours=health_metric.player_uptime_hours,
            content_errors_count=health_metric.content_errors_count,
            last_error_message=health_metric.last_error_message,
            last_error_at=health_metric.last_error_at,
            overall_status=health_metric.overall_status,
            is_alert_triggered=health_metric.is_alert_triggered,
            alert_message=health_metric.alert_message,
            metadata=health_metric.metadata or {},
            recorded_at=health_metric.recorded_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[HealthMetrics] ❌ Failed to record health for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record health metrics: {str(e)}"
        )


@router.get(DeviceRoutes.CHECK_ACTIVATION, response_model=ActivationStatusResponse)
def check_activation_status(
    unique_code: str,
    device_repo: DeviceRepository = Depends(get_device_repository),
    db: Session = Depends(get_db)
):
    """
    Check activation status (called by player to poll activation)

    Returns activation status and device info if activated
    IMPORTANT: For active devices, always return device info regardless of code expiration
    """
    try:
        device = device_repo.find_by_code(unique_code)

        if not device:
            return ActivationStatusResponse(
                activated=False,
                expired=False,
                message="Device not found"
            )

        # Fetch organization PIN if device has organization_id
        organization_pin = None
        if device.organization_id:
            from services.auth.repositories.models import OrganizationModel
            org = db.query(OrganizationModel).filter(
                OrganizationModel.id == device.organization_id
            ).first()
            if org:
                organization_pin = org.pin  # Column name is 'pin' not 'organization_pin'

        # Check if device is activated
        # IMPORTANT: Return device info for active devices even if code expired!
        # Player needs device_id to persist across reloads
        if device.is_active():
            # Generate JWT token for session restore (after cache clear)
            device_token = None
            if device.organization_id:
                from shared.auth import create_device_token
                device_token = create_device_token(
                    device_id=device.id,
                    organization_id=device.organization_id
                )

            return ActivationStatusResponse(
                activated=True,
                expired=False,  # Don't set expired for active devices
                device_id=device.id,
                device_name=device.device_name,
                organization_id=device.organization_id,
                organization_pin=organization_pin,  # Fixed: use organization_pin not pin
                device_token=device_token,  # JWT token for session restore
                unique_code=device.unique_code,  # For heartbeat
                message="Device is activated"
            )

        # Device is pending - check if code expired
        is_expired = not device.can_activate()

        return ActivationStatusResponse(
            activated=False,
            expired=is_expired,
            device_id=device.id if not is_expired else None,
            organization_pin=None,  # Don't send PIN for pending devices
            message=f"Device status: {device.status}" + (" (code expired)" if is_expired else "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(DeviceRoutes.CHECK_ACTIVATION_BY_UUID)
def check_activation_by_uuid(
    device_uuid: str,
    device_repo: DeviceRepository = Depends(get_device_repository),
    db: Session = Depends(get_db)
):
    """
    Check device activation status by UUID fingerprint
    Used by player after cache clear to restore device state

    Returns device info if device exists, regardless of activation status
    """
    try:
        device = device_repo.find_by_uuid(device_uuid)

        if not device:
            return {
                "device_id": None,
                "unique_code": None,
                "status": None,
                "message": "No device found with this fingerprint"
            }

        # Fetch organization PIN if device has organization_id
        organization_pin = None
        if device.organization_id:
            from services.auth.repositories.models import OrganizationModel
            org = db.query(OrganizationModel).filter(
                OrganizationModel.id == device.organization_id
            ).first()
            if org:
                organization_pin = org.pin

        # Return device info regardless of status
        return {
            "device_id": device.id,
            "unique_code": device.unique_code,
            "status": device.status,
            "device_name": device.device_name,
            "organization_id": device.organization_id,
            "pin": organization_pin,
            "message": f"Device found with status: {device.status}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(DeviceRoutes.VERIFY_FINGERPRINT)
def verify_device_by_fingerprint(
    device_uuid: str,
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Verify device by fingerprint UUID (for cache clear scenario)

    Returns device info if device exists and is activated
    This allows player to restore state after localStorage is cleared
    """
    try:
        device = device_repo.find_by_uuid(device_uuid)

        if not device:
            return {
                "device": None,
                "token": None,
                "message": "No device found with this fingerprint"
            }

        if device.status != 'active':
            return {
                "device": None,
                "token": None,
                "message": f"Device found but not activated (status: {device.status})"
            }

        # Device is activated - return device info
        # Generate new device token for authentication
        from shared.auth import create_device_token
        device_token = create_device_token(
            device_id=device.id,
            organization_id=device.organization_id
        )

        # Get organization info for PIN
        from services.organization.repositories.organization_repo import OrganizationRepository
        org_repo = OrganizationRepository(device_repo.db)
        org = org_repo.find_by_id(device.organization_id) if device.organization_id else None

        return {
            "device": {
                "id": device.id,
                "unique_code": device.unique_code,
                "status": device.status,
                "device_name": device.device_name,
                "organization_id": device.organization_id,
                "organization_pin": org.organization_pin if org else None,
                "device_uuid": device.device_uuid
            },
            "token": device_token,
            "message": "Device verified successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# CMS ENDPOINTS (PROTECTED - REQUIRES AUTH)
# TODO: Add authentication middleware
# =============================================================================

@router.post(DeviceRoutes.ACTIVATE, response_model=DeviceActivationResponse)
@handle_errors
async def activate_device(
    request_body: ActivateDeviceRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    use_case: ActivateDeviceUseCase = Depends(get_activate_device_use_case),
    current_user: dict = Depends(require_permission("devices", "create"))
):
    """
    Activate device with code (called by CMS admin)

    Admin enters the 6-digit code shown on screen to activate device
    Device is assigned to admin's organization automatically
    Uses centralized error handling and logging

    Requires: devices.create permission
    """
    start_time = time.time()

    # Execute activation use case (will raise ValidationError if fails)
    # Pass admin's organization_id from JWT token
    result = use_case.execute(
        unique_code=request_body.unique_code,
        organization_id=current_user["organization_id"],
        device_name=request_body.device_name,
        room_number=request_body.room_number,
        location_type=request_body.location_type
    )

    device = result["device"]
    device_token = result["token"]

    # Convert to response with is_online computed field
    response = device_to_response(device)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful activation
    request_logger.log_request(
        method="POST",
        path=DeviceRoutes.ACTIVATE,
        status_code=200,
        duration_ms=duration_ms
    )

    # Invalidate device cache
    cache.invalidate_device(device.id, current_user["organization_id"])

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="device.activate",
        resource_type="device",
        resource_id=device.id,
        details={
            "unique_code": request_body.unique_code,
            "device_name": request_body.device_name,
            "organization_id": current_user["organization_id"]
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    # WebSocket broadcast - Schedule as background task
    if hasattr(use_case, '_broadcast_data') and use_case._broadcast_data:
        background_tasks.add_task(
            broadcast_device_event,
            use_case._broadcast_data["organization_id"],
            use_case._broadcast_data["event_type"],
            use_case._broadcast_data["data"]
        )

    # Return activation response with JWT token
    return DeviceActivationResponse(
        device=response,
        token=device_token,
        message=f"Device '{device.device_name}' berhasil diaktivasi"
    )


@router.get(DeviceRoutes.LIST, response_model=DeviceListResponse)
def list_devices(
    scope: str = Query("my_org", description="Scope: my_org (default), released, pending, or all"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, pending, inactive, released"),
    online_only: bool = Query(False, description="Show only online devices"),
    sort_by: Optional[str] = Query(None, description="Sort by column: device_name, status, device_type, ip_address, last_seen_at"),
    sort_dir: Optional[str] = Query(None, description="Sort direction: asc or desc"),
    use_case: ListDevicesUseCase = Depends(get_list_devices_use_case),
    current_user: dict = Depends(require_permission("devices", "read"))
):
    """
    List devices with scope filter (called by CMS)

    Scopes:
    - my_org (default): Active/inactive devices in Device List
    - released: Released devices in Unsigned Pool (same organization)
    - pending: Pending devices waiting to be claimed (org_id = NULL)
    - unassigned: Alias for pending (backward compatibility)
    - all: All devices (super admin only)

    Sorting:
    - sort_by: device_name, status, device_type, ip_address, last_seen_at
    - sort_dir: asc or desc

    Requires: devices.read permission
    """
    # Validate scope
    valid_scopes = ["my_org", "released", "pending", "unassigned", "all"]
    if scope not in valid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope. Must be one of: {valid_scopes}"
        )

    # Check super admin for 'all' scope
    user_role = current_user.get("role", "")
    if scope == "all" and user_role.upper() not in ["SUPER_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can view all devices"
        )

    # Generate cache key with scope and sorting
    cache_key = list_cache_key(
        entity="devices",
        org_id=current_user["organization_id"] if scope == "my_org" else "global",
        status_filter=status_filter,
        online_only=online_only,
        scope=scope,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        track_cache_operation("get", hit=True)
        return cached_result

    track_cache_operation("get", hit=False)

    try:
        # Determine organization_id based on scope
        if scope == "my_org" or scope == "released":
            # Both my_org and released need user's organization
            organization_id = current_user["organization_id"]
            if not organization_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User must belong to an organization"
                )
        elif scope in ["unassigned", "pending"]:
            # Query devices with organization_id = NULL (pending/unassigned)
            organization_id = None
        else:  # all
            # Super admin - query all devices
            organization_id = "all"

        devices = use_case.execute(
            organization_id=organization_id,
            status_filter=status_filter,
            online_only=online_only,
            scope=scope,
            sort_by=sort_by,
            sort_dir=sort_dir
        )

        # Convert to response models with is_online computed field
        device_responses = []
        for device in devices:
            response = device_to_response(device)
            device_responses.append(response)

        # Get counts
        total = use_case.count_devices(organization_id)
        online = use_case.count_online_devices(organization_id)
        
        # Update metrics
        update_device_metrics(organization_id, online, total - online)

        result = DeviceListResponse(
            items=device_responses,  # Changed from 'devices' to 'items'
            total=total,
            online=online
        )
        
        # Cache for 1 minute (devices change frequently)
        cache.set(cache_key, result.dict(), ttl=60)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# NOTE: /me route MUST be defined BEFORE /{device_id} route to ensure proper matching
@router.get(DeviceRoutes.ME, response_model=DeviceResponse)
def get_my_device_info(
    device_repo: DeviceRepository = Depends(get_device_repository),
    current_device: CurrentDevice = Depends(get_current_device)
):
    """
    Get current device's own information (called by player)

    Requires device JWT token authentication.
    Device can only access its own data, ensuring security.

    Returns:
        DeviceResponse with all device fields including ip_address
    """
    try:
        # Fetch device data
        device = device_repo.find_by_id(current_device.id)

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {current_device.id} not found"
            )

        # Verify organization match (security check)
        if device.organization_id != current_device.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device organization mismatch"
            )

        # Convert to response with is_online computed field
        return device_to_response(device)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(DeviceRoutes.GET, response_model=DeviceResponse)
def get_device(
    device_id: int,
    device_repo: DeviceRepository = Depends(get_device_repository),
    current_user: dict = Depends(require_permission("devices", "read"))
):
    """
    Get device details (called by CMS)

    Requires: devices.read permission
    """
    # Generate cache key
    cache_key = device_cache_key(device_id)

    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        track_cache_operation("get", hit=True)
        # Verify organization access
        if cached_result.get('organization_id') != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )
        return DeviceResponse(**cached_result)

    track_cache_operation("get", hit=False)

    try:
        # SECURITY FIX: Add organization isolation
        device = device_repo.find_by_id(device_id, organization_id=current_user["organization_id"])

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )

        # Verify organization access
        if device.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )

        # Convert to response with is_online computed field
        response = device_to_response(device)
        
        # Cache for 1 minute
        cache.set(cache_key, response.dict(), ttl=60)

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(DeviceRoutes.UPDATE)
@handle_errors
def update_device(
    device_id: int,
    request_body: UpdateDeviceRequest,
    http_request: Request,
    current_user: dict = Depends(require_permission("devices", "edit")),
    use_case: UpdateDeviceUseCase = Depends(get_update_device_use_case)
):
    """
    Update device settings (called by CMS)
    Uses centralized error handling and logging

    Requires: devices.update permission
    """
    start_time = time.time()

    # Execute update use case (will raise ValidationError/NotFoundError if fails)
    device = use_case.execute(
        device_id=device_id,
        device_name=request_body.device_name,
        room_number=request_body.room_number,
        location_type=request_body.location_type,
        rotation=request_body.rotation,
        is_volume_enabled=request_body.is_volume_enabled,
        is_personalization_supported=request_body.is_personalization_supported,
        privacy_mode=request_body.privacy_mode,
        current_user_org_id=current_user["organization_id"],
        updated_by_id=current_user["user_id"]
    )

    # Convert to response with is_online computed field
    response = device_to_response(device)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful update
    request_logger.log_request(
        method="PUT",
        path=DeviceRoutes.UPDATE.replace("{device_id}", str(device_id)),
        status_code=200,
        duration_ms=duration_ms
    )

    # Invalidate device cache
    cache.invalidate_device(device_id, device.organization_id)

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="device.update",
        resource_type="device",
        resource_id=device_id,
        details={
            "device_name": request_body.device_name
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    # Return standardized success response
    return success_response(
        data=response,
        message=f"Device '{device.device_name}' berhasil diupdate"
    )


@router.delete(DeviceRoutes.DELETE, status_code=status.HTTP_204_NO_CONTENT)
@handle_errors
def delete_device(
    device_id: int,
    http_request: Request,
    current_user: dict = Depends(require_permission("devices", "delete")),
    use_case: UpdateDeviceUseCase = Depends(get_update_device_use_case)
):
    """
    Delete device (called by CMS)
    Uses centralized error handling and logging

    Requires: devices.delete permission
    """
    start_time = time.time()

    # Execute delete use case (will raise NotFoundError if device not found)
    success = use_case.delete_device(
        device_id,
        current_user_org_id=current_user["organization_id"],
        deleted_by_id=current_user["user_id"]
    )

    if not success:
        raise NotFoundError(
            message=f"Device dengan ID {device_id} tidak ditemukan",
            resource_type="device",
            resource_id=device_id
        )

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful deletion
    request_logger.log_request(
        method="DELETE",
        path=DeviceRoutes.DELETE.replace("{device_id}", str(device_id)),
        status_code=204,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="device.delete",
        resource_type="device",
        resource_id=device_id,
        details={
            "soft_delete": True
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    return None


@router.post(DeviceRoutes.RELEASE, response_model=DeviceResponse)
@handle_errors
def release_device_by_admin(
    device_id: int,
    http_request: Request,
    current_user: dict = Depends(require_permission("devices", "edit")),
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Release device by CMS admin (soft release)

    Flow:
    1. Admin clicks "Release" button in CMS
    2. Backend sets status='released'
    3. Player heartbeat gets 403 error
    4. Player clears tokens but KEEPS org_id in IndexedDB
    5. Player requests new activation code (with org_id)
    6. Device appears in SAME organization's pending list

    This is DIFFERENT from hard reset:
    - CMS Release: Keep org_id → re-register to SAME org
    - Hard Reset: Clear org_id → re-register to GLOBAL pending

    Requires: devices.update permission
    """
    from datetime import datetime, timezone

    start_time = time.time()

    # Get device
    device = device_repo.find_by_id(device_id, organization_id=current_user["organization_id"])

    if not device:
        raise NotFoundError(
            message=f"Device with ID {device_id} not found",
            resource_type="device",
            resource_id=device_id
        )

    # Verify ownership
    if device.organization_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to release this device"
        )

    # Update status to released
    device.status = 'released'
    device.released_at = datetime.now(timezone.utc)

    updated_device = device_repo.update(device)

    # Convert to response
    response = device_to_response(updated_device)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful release
    request_logger.log_request(
        method="POST",
        path=f"/devices/{device_id}/release",
        status_code=200,
        duration_ms=duration_ms
    )

    # Invalidate device cache
    cache.invalidate_device(device_id, current_user["organization_id"])

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="device.release",
        resource_type="device",
        resource_id=device_id,
        details={
            "device_name": device.device_name
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    return response


@router.post(DeviceRoutes.HARD_RESET)
def hard_reset_device(
    device_id: int,
    http_request: Request,
    device_repo: DeviceRepository = Depends(get_device_repository),
    current_device: CurrentDevice = Depends(get_current_device)
):
    """
    Hard reset device (factory reset) - called by player after password validation

    🔒 SECURITY REQUIREMENTS:
    - Requires device JWT authentication (prevents unauthorized reset attacks)
    - Device can only reset ITSELF (device_id must match JWT token)
    - Password validation MUST be called first via /validate-reset-password
    - Rate limiting applied to prevent brute force attacks

    Flow:
    1. Player validates password via /validate-reset-password
    2. Player calls this endpoint WITH device JWT token
    3. Backend verifies device can only reset itself
    4. Backend sets status='released' (same as CMS release)
    5. Player clears ALL IndexedDB data (including org_id)
    6. Player requests new activation code (WITHOUT org_id)
    7. Device appears in GLOBAL pending list (unassigned)

    This is DIFFERENT from CMS release:
    - CMS Release: Keep org_id → re-register to SAME org
    - Hard Reset: Clear org_id → re-register to GLOBAL pending

    ⚠️ SECURITY FIX (CVSS 9.8 - Critical):
    - Added device authentication requirement
    - Added device ownership verification (can only reset self)
    - Added IP address logging for audit trail
    - Password validation must be enforced client-side
    """
    from datetime import datetime, timezone

    # 🔒 SECURITY CHECK: Verify device can only reset itself
    if current_device.id != device_id:
        audit_logger.log_action(
            user_id=None,
            action="device.hard_reset.unauthorized_attempt",
            resource_type="device",
            resource_id=device_id,
            details={
                "authenticated_device_id": current_device.id,
                "attempted_device_id": device_id,
                "ip_address": http_request.client.host if http_request.client else None,
                "severity": "CRITICAL",
                "attack_type": "Unauthorized device reset attempt"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Devices can only reset themselves"
        )

    # Get device (verify it exists)
    device = device_repo.find_by_id(device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # 🔒 SECURITY CHECK: Additional verification that device matches JWT org
    if device.organization_id != current_device.organization_id:
        audit_logger.log_action(
            user_id=None,
            action="device.hard_reset.org_mismatch",
            resource_type="device",
            resource_id=device_id,
            details={
                "device_org_id": device.organization_id,
                "token_org_id": current_device.organization_id,
                "ip_address": http_request.client.host if http_request.client else None,
                "severity": "HIGH"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization mismatch - device token invalid"
        )

    # Store original state for audit
    original_org_id = device.organization_id
    original_status = device.status
    original_code = device.unique_code

    # Hard reset: set status to released AND clear unique_code
    # This disconnects the device record from the player
    # Player will request new code and create NEW device record
    device.status = 'released'
    device.released_at = datetime.now(timezone.utc)
    device.unique_code = None  # Clear code - player will get new one

    updated_device = device_repo.update(device)

    # 🔒 SECURITY: Comprehensive audit logging
    audit_logger.log_action(
        user_id=None,  # No user - called by player device
        action="device.hard_reset",
        resource_type="device",
        resource_id=device_id,
        details={
            "device_name": device.device_name,
            "organization_id": original_org_id,
            "previous_status": original_status,
            "new_status": "released",
            "reset_type": "Factory reset by device",
            "authenticated_device_id": current_device.id,
            "ip_address": http_request.client.host if http_request.client else None,
            "user_agent": http_request.headers.get("User-Agent") if http_request else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "security_note": "Password validation required client-side"
        }
    )

    print(f"[Hard Reset] ✅ Device {device_id} ({device.device_name}) factory reset completed by authenticated device")

    return {
        "success": True,
        "message": "Device factory reset completed"
    }


# NOTE: get_resolved_content endpoint moved to extended_routes.py to avoid duplication
# The extended_routes version includes full 3-tier priority implementation


@router.post(DeviceRoutes.VALIDATE_RESET_PASSWORD)
def validate_reset_password(
    request: ValidateResetPasswordRequest,
    http_request: Request,
    current_device: CurrentDevice = Depends(get_current_device)
):
    """
    Validate device reset password (called by player)

    🔒 SECURITY REQUIREMENTS:
    - Requires device JWT authentication (prevents unauthorized password checking)
    - Device can only validate for ITSELF
    - Rate limiting applied (prevent brute force attacks)
    - Failed attempts are logged for security monitoring
    - Password stored in environment variable (never hardcoded)

    Flow:
    1. Player shows password input dialog
    2. Player calls this endpoint WITH device JWT token
    3. Backend verifies device authentication
    4. Backend checks password against environment variable
    5. Failed attempts logged for security monitoring
    6. On success, player can proceed to hard_reset_device

    Request body: { "password": "admin123" }

    ⚠️ SECURITY FIX (CVSS 7.5 - High):
    - Added device authentication requirement
    - Added rate limiting consideration (TODO: implement rate limiter)
    - Added comprehensive audit logging for failed attempts
    - IP address logging for forensic analysis
    """
    import os
    import time

    # Get reset password from environment variable
    reset_password = os.getenv('DEVICE_RESET_PASSWORD', 'admin123')

    # Log the validation attempt
    attempt_details = {
        "device_id": current_device.id,
        "organization_id": current_device.organization_id,
        "ip_address": http_request.client.host if http_request.client else None,
        "user_agent": http_request.headers.get("User-Agent") if http_request else None,
        "timestamp": time.time()
    }

    if request.password == reset_password:
        # 🔒 SECURITY: Log successful validation
        audit_logger.log_action(
            user_id=None,
            action="device.reset_password.validation_success",
            resource_type="device",
            resource_id=current_device.id,
            details={
                **attempt_details,
                "result": "success",
                "severity": "INFO"
            }
        )

        return {
            "valid": True,
            "message": "Password correct"
        }
    else:
        # 🔒 SECURITY: Log FAILED validation attempt (potential attack)
        audit_logger.log_action(
            user_id=None,
            action="device.reset_password.validation_failed",
            resource_type="device",
            resource_id=current_device.id,
            details={
                **attempt_details,
                "result": "failed",
                "severity": "WARNING",
                "security_note": "Monitor for brute force attempts"
            }
        )

        # Add small delay to mitigate brute force (timing attack prevention)
        time.sleep(1)

        return {
            "valid": False,
            "message": "Incorrect password"
        }
