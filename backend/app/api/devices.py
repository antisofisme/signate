"""
Device Management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_active_user
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
    current_user: User = Depends(get_current_active_user)
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
    """
    # Build query
    query = db.query(Device)

    # Apply filters
    if device_type:
        query = query.filter(Device.device_type == device_type)
    if status:
        query = query.filter(Device.status == status)

    # Get total count
    total = query.count()

    # Get devices with pagination
    devices = query.offset(skip).limit(limit).all()

    return DeviceListResponse(
        total=total,
        devices=devices
    )


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    db: Session = Depends(get_db)
):
    """
    Self-registration endpoint for monitor devices (NO AUTH REQUIRED)

    This allows monitor clients to register themselves with a self-generated
    activation code. The monitor generates a 6-digit code, displays it to the user,
    and the admin activates it via Web Admin.

    Args:
        device_data: Monitor registration data (activation_code, device_name)
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

    # Create monitor device with self-generated code
    device = Device(
        device_type="monitor",
        device_name=device_data.device_name,
        unique_code=device_data.activation_code,
        code_expires_at=get_code_expiry(),  # 10 minutes expiry
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
    current_user: User = Depends(get_current_active_user)
):
    """
    Update device information

    Args:
        device_id: Device ID
        device_data: Update data
        db: Database session
        current_user: Authenticated user

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

    db.commit()
    db.refresh(device)

    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete device

    Args:
        device_id: Device ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If device not found

    Notes:
        - This will also delete related content assignments (CASCADE)
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    db.delete(device)
    db.commit()

    return None


@router.post("/heartbeat", response_model=HeartbeatResponse)
def device_heartbeat(
    heartbeat_data: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    """
    Device heartbeat endpoint

    Args:
        heartbeat_data: Device ID and optional IP
        db: Database session

    Returns:
        HeartbeatResponse: Heartbeat confirmation

    Raises:
        HTTPException: If device not found

    Notes:
        - This endpoint does NOT require authentication (for device clients)
        - Devices call this every 30-60 seconds to stay "online"
        - Updates last_seen timestamp
    """
    device = db.query(Device).filter(Device.id == heartbeat_data.device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {heartbeat_data.device_id} not found"
        )

    # Update last_seen
    device.last_seen = datetime.utcnow()

    # Update IP if provided (for dynamic IPs)
    if heartbeat_data.ip_address:
        device.ip_address = heartbeat_data.ip_address

    db.commit()
    db.refresh(device)

    return HeartbeatResponse(
        device_id=device.id,
        status=device.status,
        last_seen=device.last_seen,
        message="Heartbeat recorded successfully"
    )
