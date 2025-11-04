"""
Device API Routes
HTTP endpoints for device management

Updated to use centralized utilities:
- shared.errors for error handling
- shared.responses for standardized responses
- shared.logging for request logging
"""

from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.api_routes import DeviceRoutes
from shared.errors import handle_errors, NotFoundError, ValidationError
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from typing import Optional
import time

from .dtos import (
    RequestActivationCodeRequest,
    ActivateDeviceRequest,
    HeartbeatRequest,
    UpdateDeviceRequest,
    ActivationCodeResponse,
    DeviceResponse,
    DeviceListResponse,
    HeartbeatResponse,
    ActivationStatusResponse
)
from .use_cases.request_activation_code import RequestActivationCodeUseCase
from .use_cases.activate_device import ActivateDeviceUseCase
from .use_cases.heartbeat import DeviceHeartbeatUseCase
from .use_cases.list_devices import ListDevicesUseCase
from .use_cases.update_device import UpdateDeviceUseCase
from .repositories.device_repo import DeviceRepository
from .domain.device import DeviceHeartbeat


router = APIRouter()

# Initialize loggers
request_logger = RequestLogger()
audit_logger = AuditLogger()


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
# PLAYER ENDPOINTS (PUBLIC - NO AUTH)
# =============================================================================

@router.post("/devices/request-code", response_model=ActivationCodeResponse, status_code=status.HTTP_201_CREATED)
def request_activation_code(
    request: RequestActivationCodeRequest,
    use_case: RequestActivationCodeUseCase = Depends(get_request_activation_code_use_case)
):
    """
    Request activation code (called by player)

    Generates 6-digit code that expires in 10 minutes
    """
    try:
        result = use_case.execute(
            organization_id=request.organization_id,
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


@router.post("/devices/heartbeat", response_model=HeartbeatResponse)
def device_heartbeat(
    request: HeartbeatRequest,
    use_case: DeviceHeartbeatUseCase = Depends(get_heartbeat_use_case)
):
    """
    Device heartbeat (called by player every 30 seconds)

    Updates last_seen timestamp and device metadata
    """
    try:
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
            connection_speed=request.connection_speed
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


@router.get("/devices/check-activation/{unique_code}", response_model=ActivationStatusResponse)
def check_activation_status(
    unique_code: str,
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Check activation status (called by player to poll activation)

    Returns activation status and device info if activated
    """
    try:
        device = device_repo.find_by_code(unique_code)

        if not device:
            return ActivationStatusResponse(
                is_activated=False,
                message="Device not found"
            )

        if device.is_active():
            return ActivationStatusResponse(
                is_activated=True,
                device_id=device.id,
                device_name=device.device_name,
                message="Device is activated"
            )
        else:
            return ActivationStatusResponse(
                is_activated=False,
                message=f"Device status: {device.status}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# CMS ENDPOINTS (PROTECTED - REQUIRES AUTH)
# TODO: Add authentication middleware
# =============================================================================

@router.post(DeviceRoutes.ACTIVATE)
@handle_errors
def activate_device(
    request_body: ActivateDeviceRequest,
    http_request: Request,
    use_case: ActivateDeviceUseCase = Depends(get_activate_device_use_case)
):
    """
    Activate device with code (called by CMS admin)

    Admin enters the 6-digit code shown on screen to activate device
    Uses centralized error handling and logging
    """
    start_time = time.time()

    # Execute activation use case (will raise ValidationError if fails)
    device = use_case.execute(
        unique_code=request_body.unique_code,
        device_name=request_body.device_name,
        room_number=request_body.room_number,
        location_type=request_body.location_type
    )

    # Convert to response with is_online computed field
    response = DeviceResponse.model_validate(device)
    response.is_online = device.is_online()

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful activation
    request_logger.log_request(
        method="POST",
        path=DeviceRoutes.ACTIVATE,
        status_code=200,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=None,  # TODO: Get from JWT token when auth is implemented
        action="device.activate",
        resource_type="device",
        resource_id=device.id,
        details={
            "unique_code": request_body.unique_code,
            "device_name": request_body.device_name,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    # Return standardized success response
    return success_response(
        data=response,
        message=f"Device '{device.device_name}' berhasil diaktivasi"
    )


@router.get(DeviceRoutes.LIST, response_model=DeviceListResponse)
def list_devices(
    organization_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status: active, pending, inactive"),
    online_only: bool = Query(False, description="Show only online devices"),
    use_case: ListDevicesUseCase = Depends(get_list_devices_use_case)
):
    """
    List all devices (called by CMS)

    Returns all devices with online/offline status
    """
    try:
        devices = use_case.execute(
            organization_id=organization_id,
            status_filter=status_filter,
            online_only=online_only
        )

        # Convert to response models with is_online computed field
        device_responses = []
        for device in devices:
            response = DeviceResponse.model_validate(device)
            response.is_online = device.is_online()
            device_responses.append(response)

        # Get counts
        total = use_case.count_devices(organization_id)
        online = use_case.count_online_devices(organization_id)

        return DeviceListResponse(
            devices=device_responses,
            total=total,
            online=online
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(DeviceRoutes.GET, response_model=DeviceResponse)
def get_device(
    device_id: int,
    device_repo: DeviceRepository = Depends(get_device_repository)
):
    """
    Get device details (called by CMS)
    """
    try:
        device = device_repo.find_by_id(device_id)

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )

        # Convert to response with is_online computed field
        response = DeviceResponse.model_validate(device)
        response.is_online = device.is_online()

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
    use_case: UpdateDeviceUseCase = Depends(get_update_device_use_case)
):
    """
    Update device settings (called by CMS)
    Uses centralized error handling and logging
    """
    start_time = time.time()

    # Execute update use case (will raise ValidationError/NotFoundError if fails)
    device = use_case.execute(
        device_id=device_id,
        device_name=request_body.device_name,
        room_number=request_body.room_number,
        location_type=request_body.location_type,
        rotation=request_body.rotation,
        volume_enabled=request_body.volume_enabled,
        supports_personalization=request_body.supports_personalization,
        privacy_mode=request_body.privacy_mode
    )

    # Convert to response with is_online computed field
    response = DeviceResponse.model_validate(device)
    response.is_online = device.is_online()

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful update
    request_logger.log_request(
        method="PUT",
        path=DeviceRoutes.UPDATE.replace("{device_id}", str(device_id)),
        status_code=200,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=None,  # TODO: Get from JWT token
        action="device.update",
        resource_type="device",
        resource_id=device_id,
        details={
            "device_name": request_body.device_name,
            "ip_address": http_request.client.host if http_request.client else None
        }
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
    use_case: UpdateDeviceUseCase = Depends(get_update_device_use_case)
):
    """
    Delete device (called by CMS)
    Uses centralized error handling and logging
    """
    start_time = time.time()

    # Execute delete use case (will raise NotFoundError if device not found)
    success = use_case.delete_device(device_id)

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
        user_id=None,  # TODO: Get from JWT token
        action="device.delete",
        resource_type="device",
        resource_id=device_id,
        details={
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return None
