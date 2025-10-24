"""
Device Management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, lazyload
from datetime import datetime
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.models.user import User
from app.models.device import Device
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
from app.utils.device_utils import (
    generate_activation_code,
    get_code_expiry,
    is_code_expired
)

router = APIRouter()


@router.get("/", response_model=DeviceListResponse)
def list_devices(
    skip: int = 0,
    limit: int = 100,
    device_type: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    List all devices with optional filters

    Args:
        skip: Number of records to skip (pagination)
        limit: Max number of records to return
        device_type: Filter by device type (tv/monitor)
        status: Filter by status (pending/active/inactive)
        db: Database session
        current_user: Authenticated user

    Returns:
        DeviceListResponse: List of devices with total count

    Notes:
        - Pending devices with expired activation codes are automatically filtered out
        - This prevents closed monitor viewers from cluttering the device list
    """
    # Build query
    query = db.query(Device)

    # Apply filters
    if device_type:
        query = query.filter(Device.device_type == device_type)
    if status:
        query = query.filter(Device.status == status)

    # Get devices with pagination
    devices = query.offset(skip).limit(limit).all()

    # Filter out inactive pending devices (based on heartbeat, not expiry time)
    # Pending devices only shown if actively sending heartbeat (last_seen within 60 seconds)
    # Active/inactive devices always shown (for tracking)
    filtered_devices = []
    now = datetime.utcnow()
    HEARTBEAT_TIMEOUT = 60  # 60 seconds (monitor sends heartbeat every 30s)

    for device in devices:
        # Keep all non-pending devices (active/inactive)
        if device.status != 'pending':
            filtered_devices.append(device)
        # For pending devices, only keep if still sending heartbeat
        elif device.last_seen:
            seconds_since_last_seen = (now - device.last_seen).total_seconds()
            if seconds_since_last_seen <= HEARTBEAT_TIMEOUT:
                filtered_devices.append(device)
            # If last_seen > 60 seconds ago, hide (viewer closed/disconnected)
        # Pending devices without last_seen (just registered, not yet sent heartbeat)
        # Keep them for a short grace period
        elif device.created_at:
            seconds_since_creation = (now - device.created_at).total_seconds()
            if seconds_since_creation <= 30:  # 30 second grace period after registration
                filtered_devices.append(device)

    # Get total count (excluding offline pending devices)
    total = len(filtered_devices)

    return DeviceListResponse(
        total=total,
        devices=filtered_devices
    )


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get device by ID

    Args:
        device_id: Device ID
        db: Database session
        current_user: Authenticated user

    Returns:
        DeviceResponse: Device details

    Raises:
        HTTPException: If device not found
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    return device


@router.post("/tv", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def register_tv(
    device_data: TVRegisterRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Register a new TV device

    Args:
        device_data: TV registration data (name, IP, passphrase)
        db: Database session
        current_user: Authenticated user

    Returns:
        DeviceResponse: Created device

    Raises:
        HTTPException: If IP already registered
    """
    # Check if IP already registered
    existing_device = db.query(Device).filter(
        Device.ip_address == device_data.ip_address
    ).first()

    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with IP {device_data.ip_address} already registered"
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

    return device


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
        request: FastAPI request object (for IP auto-detection)
        db: Database session

    Returns:
        DeviceResponse: Created device with pending status

    Raises:
        HTTPException: If activation code already exists

    Notes:
        - This endpoint does NOT require authentication (for monitor clients)
        - Monitor generates its own 6-digit activation code
        - Device starts with status "pending"
        - Admin activates via Web Admin PUT /devices/{id} endpoint
        - Auto-detects client IP from request
    """
    # Check if activation code already exists
    existing_device = db.query(Device).filter(
        Device.unique_code == device_data.activation_code
    ).first()

    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Activation code {device_data.activation_code} already exists"
        )

    # Auto-detect IP address from request
    client_ip = None

    # Check X-Forwarded-For header first (for proxy/nginx)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host

    # Create monitor device with self-generated code
    device = Device(
        device_type="monitor",
        device_name=device_data.device_name,
        unique_code=device_data.activation_code,
        code_expires_at=get_code_expiry(),  # 10 minutes expiry
        device_uuid=device_data.device_uuid,  # Permanent UUID
        platform=device_data.platform,  # WebOS or browser
        model_name=device_data.model_name,  # TV model name
        ip_address=client_ip,  # Auto-detected IP
        status="pending"
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


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


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    device_data: DeviceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update device information

    Args:
        device_id: Device ID
        device_data: Update data
        db: Database session

    Returns:
        DeviceResponse: Updated device

    Raises:
        HTTPException: If device not found
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Update fields if provided
    if device_data.device_name is not None:
        device.device_name = device_data.device_name
    if device_data.status is not None:
        device.status = device_data.status
    # Update display settings if provided
    if device_data.rotation is not None:
        device.rotation = device_data.rotation
    if device_data.volume_enabled is not None:
        device.volume_enabled = device_data.volume_enabled

    db.commit()
    db.refresh(device)

    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete device

    Args:
        device_id: Device ID
        db: Database session

    Raises:
        HTTPException: If device not found

    Notes:
        - This will also delete related content assignments (CASCADE)
    """
    # Check if device exists (without loading relationships to avoid DeviceTag id issue)
    device_exists = db.query(Device.id).filter(Device.id == device_id).first()

    if not device_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Delete device directly - CASCADE will handle related records
    db.query(Device).filter(Device.id == device_id).delete()
    db.commit()

    return None


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
        request: FastAPI request object (for IP auto-detection)
        db: Database session

    Returns:
        HeartbeatResponse: Heartbeat confirmation

    Raises:
        HTTPException: If device not found

    Notes:
        - This endpoint does NOT require authentication (for device clients)
        - Devices call this every 30-60 seconds to stay "online"
        - Updates last_seen timestamp
        - Auto-detects client IP from request
    """
    device = db.query(Device).filter(Device.id == heartbeat_data.device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {heartbeat_data.device_id} not found"
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

    # Update UUID and platform information if provided
    if heartbeat_data.device_uuid is not None:
        device.device_uuid = heartbeat_data.device_uuid
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

    return HeartbeatResponse(
        device_id=device.id,
        status=device.status,
        last_seen=device.last_seen,
        message="Heartbeat recorded successfully",
        rotation=device.rotation,
        volume_enabled=device.volume_enabled
    )
