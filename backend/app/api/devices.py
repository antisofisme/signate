"""
Device Management API endpoints
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, lazyload, joinedload
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException, ValidationException
from app.schemas.common import success_response, paginated_response, APIResponse, PaginatedAPIResponse
from app.middleware.request_id import get_request_id
from app.models.user import User
from app.models.device import Device
from app.models.device_command import DeviceCommand
from app.models.tag import Tag, DeviceTag
from app.models.playlist import Playlist, PlaylistAssignment
from app.models.assignment import ContentAssignment
from app.models.content import Content
from app.schemas.device import (
    TVRegisterRequest,
    MonitorGenerateRequest,
    MonitorSelfRegisterRequest,
    MonitorActivateRequest,
    DeviceUpdateRequest,
    HeartbeatRequest,
    DeviceResponse,
    MonitorCodeResponse,
    DeviceListResponse,
    HeartbeatResponse
)
from app.schemas.device_command import (
    DeviceCommandBase,
    DeviceCommandResponse,
    DeviceCommandListResponse
)
from app.schemas.preview import (
    DevicePreviewResponse
)
from app.schemas.content import (
    ContentAssignmentResponse,
    ContentAssignRequest
)
from app.services.preview_service import PreviewService
from app.utils.device_utils import (
    generate_activation_code,
    generate_numeric_code,
    get_code_expiry,
    is_code_expired
)

# Create structured logger
logger = StructuredLogger(__name__)

router = APIRouter()


def device_to_response(device: Device, db: Session) -> DeviceResponse:
    """
    Transform Device model to DeviceResponse with populated tags & playlists

    Args:
        device: Device model instance
        db: Database session for querying relationships

    Returns:
        DeviceResponse with populated tags & playlists
    """
    # Extract tags from device.tags relationship (DeviceTag -> Tag)
    device_tags = []
    for device_tag in device.tags:
        tag = db.query(Tag).filter(Tag.id == device_tag.tag_id).first()
        if tag:
            device_tags.append({
                "id": tag.id,
                "tag_name": tag.tag_name,
                "color": tag.color
            })

    # Extract playlists from device.playlist_assignments relationship
    device_playlists = []
    for assignment in device.playlist_assignments:
        playlist = db.query(Playlist).filter(Playlist.id == assignment.playlist_id).first()
        if playlist:
            device_playlists.append({
                "id": playlist.id,
                "name": playlist.name,
                "description": playlist.description,
                "is_active": playlist.is_active,
                "priority": playlist.priority
            })

    # Build DeviceResponse dict from device attributes
    device_dict = {
        "id": device.id,
        "device_type": device.device_type,
        "device_name": device.device_name,
        "ip_address": device.ip_address,
        "unique_code": device.unique_code,
        "code_expires_at": device.code_expires_at,
        "platform": device.platform,
        "model_name": device.model_name,
        "firmware_version": device.firmware_version,
        "status": device.status,
        "last_seen": device.last_seen,
        "created_at": device.created_at,
        "updated_at": device.updated_at,
        "screen_width": device.screen_width,
        "screen_height": device.screen_height,
        "viewport_width": device.viewport_width,
        "viewport_height": device.viewport_height,
        "device_pixel_ratio": device.device_pixel_ratio,
        "user_agent": device.user_agent,
        "connection_type": device.connection_type,
        "connection_speed": device.connection_speed,
        "rotation": device.rotation,
        "volume_enabled": device.volume_enabled,
        "tags": device_tags,
        "playlists": device_playlists
    }

    return DeviceResponse(**device_dict)


@router.get("/")
def list_devices(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    device_type: str = None,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    List all devices with optional filters

    Args:
        request: FastAPI request object (for request_id)
        skip: Number of records to skip (pagination)
        limit: Max number of records to return
        device_type: Filter by device type (tv/monitor)
        status_filter: Filter by status (pending/active/inactive)
        db: Database session
        current_user: Authenticated user

    Returns:
        PaginatedAPIResponse: List of devices with pagination metadata

    Notes:
        - Pending devices with expired activation codes are automatically filtered out
        - This prevents closed monitor viewers from cluttering the device list
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing devices",
        request_id=request_id,
        skip=skip,
        limit=limit,
        device_type=device_type,
        status_filter=status_filter
    )

    # Build query with eager loading for tags & playlists
    query = db.query(Device).options(
        joinedload(Device.tags),
        joinedload(Device.playlist_assignments)
    )

    # Apply filters
    if device_type:
        query = query.filter(Device.device_type == device_type)
    if status_filter:
        query = query.filter(Device.status == status_filter)

    # Get total count before pagination
    total = query.count()

    # Get devices with pagination
    devices = query.offset(skip).limit(limit).all()

    # NO FILTERING - show all devices regardless of status
    # Let viewer handle expired codes via check-activation endpoint
    # Admin can manually delete pending devices that are no longer needed
    # This allows admin to approve pending devices at any time, even if code expired

    # Transform devices to response with tags & playlists
    device_responses = [device_to_response(device, db) for device in devices]

    logger.info(
        "Devices listed successfully",
        request_id=request_id,
        total=total,
        returned=len(device_responses)
    )

    # Calculate page number (1-indexed)
    page = (skip // limit) + 1 if limit > 0 else 1

    return paginated_response(
        data=[d.model_dump() if hasattr(d, 'model_dump') else d.dict() for d in device_responses],
        total=total,
        page=page,
        page_size=limit,
        request_id=request_id
    )


@router.get("/{device_id}")
def get_device(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get device by ID

    Args:
        device_id: Device ID
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Device details wrapped in standardized response

    Raises:
        NotFoundException: If device not found
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching device",
        request_id=request_id,
        device_id=device_id
    )

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        logger.warning(
            "Device not found",
            request_id=request_id,
            device_id=device_id
        )
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
        )

    # Transform to response with populated tags & playlists
    device_response = device_to_response(device, db)

    logger.info(
        "Device fetched successfully",
        request_id=request_id,
        device_id=device_id,
        device_name=device.device_name
    )

    return success_response(
        data=device_response.model_dump() if hasattr(device_response, 'model_dump') else device_response.dict(),
        request_id=request_id
    )


@router.get("/{device_id}/preview", response_model=DevicePreviewResponse)
async def get_device_preview(
    device_id: int,
    preview_time: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get content preview for a device with resolution breakdown

    This endpoint shows what content will be displayed on a device at a specific time,
    including the resolution algorithm breakdown (direct, playlist, tag sources).

    Args:
        device_id: Device ID
        preview_time: ISO 8601 datetime string for preview (defaults to current time)
        include_inactive: Include inactive content sources in preview
        db: Database session
        current_user: Authenticated user

    Returns:
        DevicePreviewResponse: Complete preview with content sources and final playlist

    Raises:
        HTTPException: If device not found or preview generation fails

    Notes:
        - Resolution algorithm applies SEQUENTIAL PRIORITY (Direct > Playlist > Tag)
        - EXCLUSIVE playlists override all other content sources
        - INCLUSIVE mode merges all content by priority
        - Time-based scheduling is evaluated at preview_time
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Parse preview_time if provided
    preview_datetime = None
    if preview_time:
        try:
            preview_datetime = datetime.fromisoformat(preview_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid preview_time format. Use ISO 8601 format (e.g., 2025-10-26T14:00:00)"
            )

    # Initialize preview service
    preview_service = PreviewService(db)

    # Generate preview
    try:
        preview_data = await preview_service.get_device_preview(
            device_id=device_id,
            preview_time=preview_datetime,
            include_inactive=include_inactive
        )
        return DevicePreviewResponse(**preview_data)
    except Exception as e:
        logger.error(f"Preview generation failed for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.post("/tv", status_code=status.HTTP_201_CREATED)
def register_tv(
    device_data: TVRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Register a new TV device

    Args:
        device_data: TV registration data (name, IP, passphrase)
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Created device wrapped in standardized response

    Raises:
        ConflictException: If IP already registered
    """
    request_id = get_request_id(request)

    logger.info(
        "Registering TV device",
        request_id=request_id,
        device_name=device_data.device_name,
        ip_address=device_data.ip_address
    )

    # Check if IP already registered
    existing_device = db.query(Device).filter(
        Device.ip_address == device_data.ip_address
    ).first()

    if existing_device:
        logger.warning(
            "TV registration failed - IP already registered",
            request_id=request_id,
            ip_address=device_data.ip_address,
            existing_device_id=existing_device.id
        )
        raise ConflictException(
            message=f"Device with IP {device_data.ip_address} already registered",
            field="ip_address",
            details={"ip_address": device_data.ip_address, "existing_device_id": existing_device.id}
        )

    # Create TV device
    device = Device(
        device_type="tv",
        device_name=device_data.device_name,
        ip_address=device_data.ip_address,
        passphrase=device_data.passphrase,
        status="pending"  # Pending until TV connects
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    logger.info(
        "TV device registered successfully",
        request_id=request_id,
        device_id=device.id,
        device_name=device.device_name
    )

    # Transform to response
    device_response = device_to_response(device, db)

    return success_response(
        data=device_response.model_dump() if hasattr(device_response, 'model_dump') else device_response.dict(),
        request_id=request_id
    )


@router.post("/monitor", response_model=MonitorCodeResponse, status_code=status.HTTP_201_CREATED)
def generate_monitor_code(
    device_data: MonitorGenerateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Generate activation code for monitor device

    Args:
        device_data: Monitor registration data (name)
        db: Database session
        current_user: Authenticated user

    Returns:
        MonitorCodeResponse: Device with activation code

    Notes:
        - Code expires in 10 minutes
        - Monitor must activate using this code before expiry
    """
    # Generate unique activation code
    unique_code = generate_activation_code()

    # Ensure code is unique
    while db.query(Device).filter(Device.unique_code == unique_code).first():
        unique_code = generate_activation_code()

    # Create monitor device
    device = Device(
        device_type="monitor",
        device_name=device_data.device_name,
        unique_code=unique_code,
        code_expires_at=get_code_expiry(),
        status="pending"  # Pending until monitor activates
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return MonitorCodeResponse(
        device_id=device.id,
        device_name=device.device_name,
        unique_code=device.unique_code,
        code_expires_at=device.code_expires_at,
        status=device.status
    )


@router.post("/monitor/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def register_monitor_self(
    device_data: MonitorSelfRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Self-registration endpoint for monitor devices (NO AUTH REQUIRED)

    This allows monitor clients to register themselves with a self-generated
    activation code. The monitor generates a 6-digit code, displays it to the user,
    and the admin activates it via Web Admin.

    Args:
        device_data: Monitor registration data (activation_code, device_name)
        request: FastAPI request object (for IP auto-detection and request_id)
        db: Database session

    Returns:
        APIResponse: Created device wrapped in standardized response

    Raises:
        ConflictException: If activation code already exists

    Notes:
        - This endpoint does NOT require authentication (for monitor clients)
        - Monitor generates its own 6-digit activation code
        - Device starts with status "pending"
        - Admin activates via Web Admin PUT /devices/{id} endpoint
        - Auto-detects client IP from request
    """
    request_id = get_request_id(request)

    logger.info(
        "Monitor self-registration initiated",
        request_id=request_id,
        activation_code=device_data.activation_code,
        device_name=device_data.device_name,
        platform=device_data.platform
    )

    # Check if activation code already exists
    existing_device = db.query(Device).filter(
        Device.unique_code == device_data.activation_code
    ).first()

    if existing_device:
        logger.warning(
            "Monitor registration failed - activation code already exists",
            request_id=request_id,
            activation_code=device_data.activation_code,
            existing_device_id=existing_device.id
        )
        raise ConflictException(
            message=f"Activation code {device_data.activation_code} already exists",
            field="activation_code",
            details={"activation_code": device_data.activation_code, "existing_device_id": existing_device.id}
        )

    # Auto-detect IP address from request
    client_ip = None

    # Check X-Forwarded-For header first (for proxy/nginx)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host

    # AUTO-CLEANUP DISABLED
    # Multiple devices can have the same IP (e.g., Chrome + WebOS Simulator on same PC)
    # Let pending devices expire naturally via code_expires_at (10 minutes)
    # Or admin can manually delete old pending devices from Web Admin

    # Determine device_type based on platform
    # TV platforms: webOS, Tizen, Android TV
    # Monitor/Browser platforms: Chrome, Firefox, Safari, Edge, etc.
    device_type = "monitor"  # Default
    if device_data.platform and device_data.platform in ['webOS', 'Tizen', 'Android TV']:
        device_type = "tv"

    # Create device with self-generated code
    device = Device(
        device_type=device_type,
        device_name=device_data.device_name,
        unique_code=device_data.activation_code,
        code_expires_at=get_code_expiry(),  # 10 minutes expiry
        platform=device_data.platform if device_data.platform else None,  # Optional
        model_name=device_data.model_name if device_data.model_name else None,  # Optional
        ip_address=client_ip,  # Auto-detected IP
        status="pending"
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    logger.info(
        "Monitor self-registration successful",
        request_id=request_id,
        device_id=device.id,
        device_name=device.device_name,
        device_type=device_type,
        activation_code=device_data.activation_code,
        ip_address=client_ip
    )

    # Transform to response
    device_response = device_to_response(device, db)

    return success_response(
        data=device_response.model_dump() if hasattr(device_response, 'model_dump') else device_response.dict(),
        request_id=request_id
    )


@router.post("/monitor/activate", response_model=DeviceResponse)
def activate_monitor(
    activation_data: MonitorActivateRequest,
    db: Session = Depends(get_db)
):
    """
    Activate monitor using activation code

    Args:
        activation_data: Activation code
        db: Database session

    Returns:
        DeviceResponse: Activated device

    Raises:
        HTTPException: If code invalid, expired, or already used

    Notes:
        - This endpoint does NOT require authentication (for monitor client)
        - Monitor client calls this to activate itself
    """
    # Find device by activation code
    device = db.query(Device).filter(
        Device.unique_code == activation_data.unique_code,
        Device.device_type == "monitor"
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid activation code"
        )

    # Check if already activated
    if device.status == "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device already activated"
        )

    # Check if code expired
    if is_code_expired(device.code_expires_at):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Activation code expired. Please generate a new code."
        )

    # Activate device
    device.status = "active"
    device.last_seen = datetime.utcnow()

    db.commit()
    db.refresh(device)

    return device


@router.put("/{device_id}")
def update_device(
    device_id: int,
    device_data: DeviceUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update device information

    Args:
        device_id: Device ID
        device_data: Update data
        request: FastAPI request object (for request_id)
        db: Database session

    Returns:
        APIResponse: Updated device wrapped in standardized response

    Raises:
        NotFoundException: If device not found
    """
    request_id = get_request_id(request)

    logger.info(
        "Updating device",
        request_id=request_id,
        device_id=device_id
    )

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        logger.warning(
            "Device update failed - device not found",
            request_id=request_id,
            device_id=device_id
        )
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
        )

    # Track what was updated
    updates = {}

    # Update fields if provided
    if device_data.device_name is not None:
        device.device_name = device_data.device_name
        updates['device_name'] = device_data.device_name
    if device_data.status is not None:
        device.status = device_data.status
        updates['status'] = device_data.status
    # Update display settings if provided
    if device_data.rotation is not None:
        device.rotation = device_data.rotation
        updates['rotation'] = device_data.rotation
    if device_data.volume_enabled is not None:
        device.volume_enabled = device_data.volume_enabled
        updates['volume_enabled'] = device_data.volume_enabled

    db.commit()
    db.refresh(device)

    logger.info(
        "Device updated successfully",
        request_id=request_id,
        device_id=device_id,
        updates=updates
    )

    # Transform to response
    device_response = device_to_response(device, db)

    return success_response(
        data=device_response.model_dump() if hasattr(device_response, 'model_dump') else device_response.dict(),
        request_id=request_id
    )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete device

    This will:
    1. Queue a reset command for the device (if online, device might catch it)
    2. Delete the device record (CASCADE will delete assignments, logs, commands)

    Args:
        device_id: Device ID
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Success message wrapped in standardized response

    Raises:
        NotFoundException: If device not found

    Notes:
        - This will also delete related content assignments (CASCADE)
        - A reset command is queued before deletion (in case device is online)
        - Command will be CASCADE deleted along with device
    """
    request_id = get_request_id(request)

    logger.info(
        "Deleting device",
        request_id=request_id,
        device_id=device_id
    )

    # Check if device exists (without loading relationships to avoid DeviceTag id issue)
    device_exists = db.query(Device.id).filter(Device.id == device_id).first()

    if not device_exists:
        logger.warning(
            "Device deletion failed - device not found",
            request_id=request_id,
            device_id=device_id
        )
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
        )

    # Queue reset command BEFORE deletion
    # If device is online and polling, it might catch this command before CASCADE deletion
    try:
        reset_command = DeviceCommand(
            device_id=device_id,
            command_type="reset",
            reason="deleted_by_admin",
            status="pending",
            expires_at=datetime.now() + timedelta(days=7)
        )
        db.add(reset_command)
        db.commit()  # Commit command first

        logger.info(
            "Reset command queued before device deletion",
            request_id=request_id,
            device_id=device_id
        )

        # Brief window for device to poll before deletion
        import time
        time.sleep(0.5)  # 500ms window for online devices to poll

    except Exception as e:
        # If command creation fails, continue with deletion anyway
        db.rollback()
        logger.warning(
            "Failed to queue reset command for device deletion",
            request_id=request_id,
            device_id=device_id,
            error=str(e)
        )

    # Delete device directly - CASCADE will handle related records (including the command we just created)
    db.query(Device).filter(Device.id == device_id).delete()
    db.commit()

    logger.info(
        "Device deleted successfully",
        request_id=request_id,
        device_id=device_id
    )

    return success_response(
        data={"message": f"Device {device_id} deleted successfully"},
        request_id=request_id
    )


@router.post("/{device_id}/release", response_model=DeviceResponse)
def release_device(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Release device (reset but keep record)

    This will:
    1. Queue a reset command for the device
    2. Change device status to "inactive"
    3. Clear activation code
    4. Keep all content assignments and settings

    Unlike DELETE, this keeps the device record in database.
    When device executes the reset command, it will show activation screen with new code.

    Args:
        device_id: Device ID
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Updated device wrapped in standardized response

    Raises:
        NotFoundException: If device not found
        BadRequestException: If reset command queueing fails
    """
    request_id = get_request_id(request)

    logger.info(
        "Releasing device",
        request_id=request_id,
        device_id=device_id
    )

    # Get device
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        logger.warning(
            "Device release failed - device not found",
            request_id=request_id,
            device_id=device_id
        )
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
        )

    # Queue reset command (will persist since device is not deleted)
    try:
        reset_command = DeviceCommand(
            device_id=device_id,
            command_type="reset",
            reason="released_by_admin",
            status="pending",
            expires_at=datetime.now() + timedelta(days=7)
        )
        db.add(reset_command)
        db.commit()

        logger.info(
            "Reset command queued for device release",
            request_id=request_id,
            device_id=device_id
        )

    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to queue reset command for device release",
            request_id=request_id,
            device_id=device_id,
            error=str(e)
        )
        raise BadRequestException(
            message=f"Failed to queue reset command: {str(e)}",
            details={"device_id": device_id, "error": str(e)}
        )

    # Release device: Set inactive, mark released timestamp, clear code
    # Viewer will reset and self-register as NEW pending device
    device.status = "inactive"
    device.released_at = datetime.now()
    device.unique_code = None  # Clear activation code
    device.code_expires_at = None  # Clear expiry
    device.last_seen = None  # Clear last_seen to show as offline

    # Device record stays for history (assignments, logs remain)
    # Can be reused later by assigning new code if needed
    # Viewer will create a NEW device record with new code after reset

    db.commit()
    db.refresh(device)

    logger.info(
        "Device released successfully",
        request_id=request_id,
        device_id=device_id,
        device_name=device.device_name
    )

    # Transform to response
    device_response = device_to_response(device, db)

    return success_response(
        data=device_response.model_dump() if hasattr(device_response, 'model_dump') else device_response.dict(),
        request_id=request_id
    )


@router.post("/{device_id}/replace-with-pending/{pending_device_id}", response_model=DeviceResponse)
def replace_device_with_pending(
    device_id: int,
    pending_device_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Replace target device's code with a pending device

    This is used when a device loses connection (e.g., cache cleared) and needs to reconnect
    with a new activation code. The pending device's code will replace the target device's code,
    and the pending device will be deleted.

    Args:
        device_id: Target device ID to replace
        pending_device_id: Pending device ID to take code from
        db: Database session
        current_user: Optional authenticated user

    Returns:
        Updated device with new code

    Raises:
        HTTPException: If either device not found or pending device is not actually pending
    """
    # Get target device
    target_device = db.query(Device).filter(Device.id == device_id).first()
    if not target_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target device with ID {device_id} not found"
        )

    # Get pending device
    pending_device = db.query(Device).filter(Device.id == pending_device_id).first()
    if not pending_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending device with ID {pending_device_id} not found"
        )

    # Validate pending device is actually pending
    if pending_device.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device {pending_device_id} is not pending (status: {pending_device.status})"
        )

    logger.info(f"Replacing device {device_id} (code: {target_device.unique_code}) with pending device {pending_device_id} (code: {pending_device.unique_code})")

    # Save pending device data before deleting
    pending_code = pending_device.unique_code
    pending_ip = pending_device.ip_address
    pending_expires = pending_device.code_expires_at
    pending_platform = pending_device.platform
    pending_screen_w = pending_device.screen_width
    pending_screen_h = pending_device.screen_height
    pending_viewport_w = pending_device.viewport_width
    pending_viewport_h = pending_device.viewport_height
    pending_dpr = pending_device.device_pixel_ratio
    pending_ua = pending_device.user_agent
    pending_conn_type = pending_device.connection_type
    pending_conn_speed = pending_device.connection_speed
    pending_last_seen = pending_device.last_seen

    # Delete pending device FIRST to free up unique_code constraint
    db.delete(pending_device)
    db.flush()  # Flush to apply delete before update

    # Now replace target device with pending device data
    target_device.unique_code = pending_code
    target_device.ip_address = pending_ip
    target_device.code_expires_at = pending_expires
    target_device.platform = pending_platform
    target_device.screen_width = pending_screen_w
    target_device.screen_height = pending_screen_h
    target_device.viewport_width = pending_viewport_w
    target_device.viewport_height = pending_viewport_h
    target_device.device_pixel_ratio = pending_dpr
    target_device.user_agent = pending_ua
    target_device.connection_type = pending_conn_type
    target_device.connection_speed = pending_conn_speed
    target_device.last_seen = pending_last_seen

    # If target device is inactive (released), reactivate it
    if target_device.status == "inactive":
        logger.info(f"Reactivating inactive device {device_id}")
        target_device.status = "active"
        target_device.released_at = None  # Clear release timestamp

    # Commit changes
    db.commit()
    db.refresh(target_device)

    # Queue reload command for the target device so viewer updates with new code
    try:
        reload_command = DeviceCommand(
            device_id=device_id,
            command_type="reload",
            reason="device_replaced_with_pending",
            status="pending",
            expires_at=datetime.now() + timedelta(days=7)
        )
        db.add(reload_command)
        db.commit()
        logger.info(f"Queued reload command for device {device_id} after replacement")
    except Exception as e:
        logger.error(f"Failed to queue reload command: {str(e)}")
        # Don't fail the whole operation if command queueing fails
        db.rollback()

    logger.info(f"Successfully replaced device {device_id} with code {target_device.unique_code}")

    return target_device


@router.get("/check-activation/{activation_code}")
def check_activation_status(
    activation_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Check if an activation code has been activated

    This is used by pending viewers to detect when their code
    has been activated (e.g., by replacing with inactive device)

    Args:
        activation_code: The activation code to check
        request: FastAPI request object (for request_id)
        db: Database session

    Returns:
        APIResponse: Activation status wrapped in standardized response
            - activated: boolean
            - device_id: int (if activated)
            - device_name: str (if activated)

    Notes:
        - This endpoint does NOT require authentication (for device clients)
        - Called periodically by pending devices to poll activation status
    """
    request_id = get_request_id(request)

    logger.info(
        "Checking activation status",
        request_id=request_id,
        activation_code=activation_code
    )

    # Find device with this code
    device = db.query(Device).filter(Device.unique_code == activation_code).first()

    if not device:
        logger.info(
            "Activation check - code not found or expired",
            request_id=request_id,
            activation_code=activation_code
        )
        return success_response(
            data={
                "activated": False,
                "expired": True,  # Code not found = expired/deleted
                "device_id": None,
                "device_name": None,
                "message": "Code not found or expired"
            },
            request_id=request_id
        )

    # Check if code expired (for pending devices)
    if device.status == "pending" and device.code_expires_at:
        if is_code_expired(device.code_expires_at):
            logger.info(
                "Activation check - code expired",
                request_id=request_id,
                activation_code=activation_code,
                device_id=device.id,
                code_expires_at=device.code_expires_at
            )
            return success_response(
                data={
                    "activated": False,
                    "expired": True,
                    "device_id": device.id,
                    "device_name": device.device_name,
                    "message": "Activation code has expired"
                },
                request_id=request_id
            )

    # Check if activated
    if device.status == "active":
        logger.info(
            "Activation check - code activated",
            request_id=request_id,
            activation_code=activation_code,
            device_id=device.id,
            device_name=device.device_name
        )
        return success_response(
            data={
                "activated": True,
                "expired": False,
                "device_id": device.id,
                "device_name": device.device_name,
                "message": "Code activated successfully"
            },
            request_id=request_id
        )
    else:
        # Still pending (not expired, not activated)
        logger.info(
            "Activation check - code still pending",
            request_id=request_id,
            activation_code=activation_code,
            device_id=device.id,
            device_status=device.status
        )
        return success_response(
            data={
                "activated": False,
                "expired": False,
                "device_id": device.id,
                "device_name": device.device_name,
                "status": device.status,
                "message": f"Code found but status is {device.status}"
            },
            request_id=request_id
        )


@router.post("/heartbeat", response_model=HeartbeatResponse)
def device_heartbeat(
    heartbeat_data: HeartbeatRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Device heartbeat endpoint

    Args:
        heartbeat_data: Device ID and optional IP
        request: FastAPI request object (for IP auto-detection and request_id)
        db: Database session

    Returns:
        APIResponse: Heartbeat confirmation wrapped in standardized response

    Raises:
        NotFoundException: If device not found

    Notes:
        - This endpoint does NOT require authentication (for device clients)
        - Devices call this every 30-60 seconds to stay "online"
        - Updates last_seen timestamp
        - Auto-detects client IP from request
    """
    request_id = get_request_id(request)

    logger.info(
        "Device heartbeat received",
        request_id=request_id,
        device_id=heartbeat_data.device_id
    )

    device = db.query(Device).filter(Device.id == heartbeat_data.device_id).first()

    if not device:
        logger.warning(
            "Heartbeat failed - device not found",
            request_id=request_id,
            device_id=heartbeat_data.device_id
        )
        raise NotFoundException(
            message=f"Device with ID {heartbeat_data.device_id} not found",
            resource_type="Device",
            resource_id=heartbeat_data.device_id
        )

    # Update last_seen
    device.last_seen = datetime.utcnow()

    # Auto-detect IP address from request
    client_ip = None

    # Check X-Forwarded-For header first (for proxy/nginx)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can be comma-separated list, take first IP
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client:
        # Fallback to direct client IP
        client_ip = request.client.host

    # Update IP (priority: provided > auto-detected > existing)
    if heartbeat_data.ip_address:
        device.ip_address = heartbeat_data.ip_address
    elif client_ip:
        device.ip_address = client_ip

    # Update platform information if provided
    if heartbeat_data.platform is not None:
        device.platform = heartbeat_data.platform
    if heartbeat_data.model_name is not None:
        device.model_name = heartbeat_data.model_name
    if heartbeat_data.firmware_version is not None:
        device.firmware_version = heartbeat_data.firmware_version

    # Update device information if provided
    if heartbeat_data.screen_width is not None:
        device.screen_width = heartbeat_data.screen_width
    if heartbeat_data.screen_height is not None:
        device.screen_height = heartbeat_data.screen_height
    if heartbeat_data.viewport_width is not None:
        device.viewport_width = heartbeat_data.viewport_width
    if heartbeat_data.viewport_height is not None:
        device.viewport_height = heartbeat_data.viewport_height
    if heartbeat_data.device_pixel_ratio is not None:
        device.device_pixel_ratio = heartbeat_data.device_pixel_ratio
    if heartbeat_data.user_agent is not None:
        device.user_agent = heartbeat_data.user_agent
    if heartbeat_data.connection_type is not None:
        device.connection_type = heartbeat_data.connection_type
    if heartbeat_data.connection_speed is not None:
        device.connection_speed = heartbeat_data.connection_speed

    db.commit()
    db.refresh(device)

    logger.info(
        "Device heartbeat processed successfully",
        request_id=request_id,
        device_id=device.id,
        device_name=device.device_name,
        ip_address=device.ip_address
    )

    heartbeat_response = HeartbeatResponse(
        device_id=device.id,
        status=device.status,
        last_seen=device.last_seen,
        message="Heartbeat recorded successfully",
        rotation=device.rotation,
        volume_enabled=device.volume_enabled
    )

    return success_response(
        data=heartbeat_response.model_dump() if hasattr(heartbeat_response, 'model_dump') else heartbeat_response.dict(),
        request_id=request_id
    )


# =============================================================================
# DEVICE COMMAND ENDPOINTS (Remote command queue system)
# =============================================================================

@router.post("/{device_id}/commands", response_model=DeviceCommandResponse)
def queue_command(
    device_id: int,
    command: DeviceCommandBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Queue a command for device (generic endpoint for all command types)

    Accepts any command type: reset, refresh, reload, run_speed_test, etc.
    Command is queued and will be executed when device polls for commands.

    Args:
        device_id: Device ID
        command: Command details (command_type, reason)

    Returns:
        DeviceCommandResponse with command details

    Raises:
        404: Device not found
    """
    # Check if device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )

    # Create command
    device_command = DeviceCommand(
        device_id=device_id,
        command_type=command.command_type,
        reason=command.reason or f"manual_{command.command_type}",
        status="pending",
        expires_at=datetime.now() + timedelta(days=7)  # Expire after 7 days
    )

    db.add(device_command)
    db.commit()
    db.refresh(device_command)

    logger.info(f"Queued {command.command_type} command for device {device_id} by user {current_user.username}")

    return DeviceCommandResponse(
        id=device_command.id,
        device_id=device_command.device_id,
        command_type=device_command.command_type,
        reason=device_command.reason,
        status=device_command.status,
        created_at=device_command.created_at,
        executed_at=device_command.executed_at,
        expires_at=device_command.expires_at
    )


@router.post("/{device_id}/commands/reset", response_model=DeviceCommandResponse)
def queue_reset_command(
    device_id: int,
    reason: str = "manual_reset",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Queue a reset command for device (admin only)

    Admin can trigger device reset remotely. Command is queued and will be
    executed when device next polls for commands (via heartbeat).

    Reset command will:
    - Clear localStorage (device_id, device_status, etc.)
    - Delete IndexedDB cache
    - Reload page → Generate new activation code

    Args:
        device_id: Device ID to reset
        reason: Reason for reset (e.g., "deleted_by_admin", "released_by_admin", "manual_reset")

    Returns:
        DeviceCommandResponse with command details

    Raises:
        404: Device not found
    """
    # Check if device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )

    # Create reset command
    command = DeviceCommand(
        device_id=device_id,
        command_type="reset",
        reason=reason,
        status="pending",
        expires_at=datetime.now() + timedelta(days=7)  # Expire after 7 days
    )

    db.add(command)
    db.commit()
    db.refresh(command)

    return DeviceCommandResponse(
        id=command.id,
        device_id=command.device_id,
        command_type=command.command_type,
        reason=command.reason,
        status=command.status,
        created_at=command.created_at,
        executed_at=command.executed_at,
        expires_at=command.expires_at
    )


@router.get("/{device_id}/commands/pending", response_model=DeviceCommandListResponse)
def get_pending_commands(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get pending commands for device (called by viewer)

    Viewer polls this endpoint via heartbeat to check for pending commands.
    No authentication required (viewer doesn't have auth token).

    Returns only non-expired pending commands.

    Args:
        device_id: Device ID

    Returns:
        DeviceCommandListResponse with list of pending commands

    Raises:
        404: Device not found
    """
    # Check if device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )

    # Get pending commands (not expired)
    commands = db.query(DeviceCommand).filter(
        DeviceCommand.device_id == device_id,
        DeviceCommand.status == "pending",
        DeviceCommand.expires_at > datetime.now()
    ).order_by(DeviceCommand.created_at.asc()).all()

    command_responses = [
        DeviceCommandResponse(
            id=cmd.id,
            device_id=cmd.device_id,
            command_type=cmd.command_type,
            reason=cmd.reason,
            status=cmd.status,
            created_at=cmd.created_at,
            executed_at=cmd.executed_at,
            expires_at=cmd.expires_at
        )
        for cmd in commands
    ]

    return DeviceCommandListResponse(
        commands=command_responses,
        total=len(command_responses)
    )


@router.post("/{device_id}/commands/{command_id}/execute")
def execute_command(
    device_id: int,
    command_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark command as executed (called by viewer after execution)

    Viewer calls this endpoint after successfully executing a command.
    No authentication required (viewer doesn't have auth token).

    Args:
        device_id: Device ID
        command_id: Command ID to mark as executed

    Returns:
        Success message

    Raises:
        404: Device or command not found
        400: Command already executed or expired
    """
    # Check if device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )

    # Get command
    command = db.query(DeviceCommand).filter(
        DeviceCommand.id == command_id,
        DeviceCommand.device_id == device_id
    ).first()

    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command with id {command_id} not found for device {device_id}"
        )

    # Check if already executed
    if command.status == "executed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command already executed"
        )

    # Check if expired
    if command.status == "expired" or (command.expires_at and command.expires_at < datetime.now()):
        command.status = "expired"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command has expired"
        )

    # Mark as executed
    command.status = "executed"
    command.executed_at = datetime.now()
    db.commit()

    return {
        "message": "Command executed successfully",
        "command_id": command_id,
        "device_id": device_id,
        "executed_at": command.executed_at
    }


# ==================== CONTENT ASSIGNMENT ENDPOINTS ====================

@router.get("/{device_id}/content", response_model=List[ContentAssignmentResponse])
def get_device_content(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all content directly assigned to a device

    Returns list of ContentAssignment objects for content directly assigned
    to this device (not including tag-based assignments).

    Args:
        device_id: Device ID
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        List[ContentAssignmentResponse]: List of content assignments

    Raises:
        404: Device not found
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Get direct assignments (device_id matches, tag_id is NULL) with content relationship
    assignments = db.query(ContentAssignment).options(
        joinedload(ContentAssignment.content)
    ).filter(
        ContentAssignment.device_id == device_id,
        ContentAssignment.tag_id == None
    ).order_by(ContentAssignment.priority.desc()).all()

    return assignments


@router.post("/{device_id}/content", response_model=ContentAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_content_to_device(
    device_id: int,
    assignment_data: ContentAssignRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Assign content directly to a device

    Creates a new direct assignment (device-to-content).

    Args:
        device_id: Device ID
        assignment_data: Assignment data (must include content_id)
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        ContentAssignmentResponse: Created assignment

    Raises:
        404: Device or content not found
        409: Assignment already exists
        400: Invalid request
    """
    # Verify device exists and is active
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    if device.status != 'active':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign content to device with status '{device.status}'. Device must be active."
        )

    # Verify content exists
    if not assignment_data.content_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content_id is required"
        )

    content = db.query(Content).filter(Content.id == assignment_data.content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {assignment_data.content_id} not found"
        )

    # Check if assignment already exists
    existing = db.query(ContentAssignment).filter(
        ContentAssignment.content_id == assignment_data.content_id,
        ContentAssignment.device_id == device_id,
        ContentAssignment.tag_id == None
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Content already assigned to this device"
        )

    # Create assignment
    assignment = ContentAssignment(
        content_id=assignment_data.content_id,
        device_id=device_id,
        tag_id=None,
        priority=assignment_data.priority if hasattr(assignment_data, 'priority') else 0,
        display_order=assignment_data.display_order if hasattr(assignment_data, 'display_order') else 0,
        is_active=assignment_data.is_active if hasattr(assignment_data, 'is_active') else True
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    logger.info(f"Content {assignment_data.content_id} assigned to device {device_id}")

    return assignment


@router.delete("/{device_id}/content/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_content_from_device(
    device_id: int,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove content assignment from a device

    Deletes the direct assignment between device and content.

    Args:
        device_id: Device ID
        content_id: Content ID to unassign
        db: Database session
        current_user: Authenticated user (optional)

    Raises:
        404: Device, content, or assignment not found
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Find assignment
    assignment = db.query(ContentAssignment).filter(
        ContentAssignment.content_id == content_id,
        ContentAssignment.device_id == device_id,
        ContentAssignment.tag_id == None
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content {content_id} is not assigned to device {device_id}"
        )

    # Delete assignment
    db.delete(assignment)
    db.commit()

    logger.info(f"Content {content_id} unassigned from device {device_id}")

    return None
