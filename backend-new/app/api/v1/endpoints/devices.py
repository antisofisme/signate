"""
Devices API Endpoints
=====================

Device registration dengan PIN, heartbeat monitoring, dan device management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.deps import get_db
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.repositories import DeviceRepository, OrganizationRepository
from app.services import OrganizationService
from app.schemas.device import (
    DeviceRegister,
    DeviceUpdate,
    DeviceHeartbeat,
    DeviceResponse,
    DeviceRegisterResponse,
    DeviceListResponse,
    DeviceStatsResponse,
    DeviceHeartbeatResponse
)

router = APIRouter()


@router.post(
    "/register",
    response_model=DeviceRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Device with PIN",
    description="Register new device menggunakan 8-digit organization PIN (CRITICAL)"
)
async def register_device(
    device_data: DeviceRegister,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Register device dengan organization PIN.

    **Flow**:
    1. Verify organization PIN via OrganizationService
    2. Check device quota (jika enforce_quota=True)
    3. Generate unique 6-digit activation code
    4. Create device record (is_approved=True by default)
    5. Return device details + organization name

    **Device Registration pada Viewer**:
    ```javascript
    // User masukkan PIN di viewer
    const pin = "12345678";
    const response = await fetch("/api/v1/devices/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            organization_pin: pin,
            device_name: "Lobby Screen 1",
            device_type: "screen",
            location: "Main Lobby",
            hardware_id: getMacAddress(),
            screen_resolution: "1920x1080"
        })
    });

    const device = await response.json();
    // Save device_id dan activation_code untuk heartbeat
    localStorage.setItem("device_id", device.id);
    localStorage.setItem("activation_code", device.activation_code);
    ```
    """
    org_service = OrganizationService(db)

    # Verify PIN
    org_data = org_service.verify_pin(device_data.organization_pin)
    if not org_data:
        raise NotFoundException(
            message="Invalid organization PIN",
            details={"pin": "PIN not found or organization inactive"}
        )

    organization_id = org_data["id"]

    # Check device quota
    quota = org_service.check_device_quota(organization_id)
    if not quota["can_add"]:
        raise ForbiddenException(
            message="Device quota exceeded",
            details={
                "max_devices": quota["max_devices"],
                "current_devices": quota["current_devices"],
                "message": f"Organization has reached maximum device limit ({quota['max_devices']})"
            }
        )

    device_repo = DeviceRepository(db)

    # Generate unique activation code
    import random
    def generate_activation_code():
        while True:
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            existing = db.query(device_repo.model).filter(
                device_repo.model.activation_code == code
            ).first()
            if not existing:
                return code

    activation_code = generate_activation_code()

    # Create device
    device = device_repo.create({
        "organization_id": organization_id,
        "device_name": device_data.device_name,
        "device_type": device_data.device_type or "screen",
        "activation_code": activation_code,
        "location": device_data.location,
        "hardware_id": device_data.hardware_id,
        "screen_resolution": device_data.screen_resolution,
        "is_active": True,
        "is_approved": True,  # Auto-approve by default
        "last_seen": datetime.utcnow()
    })

    return {
        **device.to_dict(),
        "organization_name": org_data["name"],
        "registration_message": f"Device registered successfully to {org_data['name']}"
    }


@router.post(
    "/{device_id}/heartbeat",
    response_model=DeviceHeartbeatResponse,
    summary="Device Heartbeat",
    description="Update device last_seen timestamp (kirim setiap 30 detik)"
)
async def device_heartbeat(
    device_id: int,
    heartbeat_data: DeviceHeartbeat,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Device heartbeat untuk monitoring online/offline status.

    **Viewer Implementation**:
    ```javascript
    // Send heartbeat setiap 30 detik
    setInterval(async () => {
        const deviceId = localStorage.getItem("device_id");
        const activationCode = localStorage.getItem("activation_code");

        await fetch(`/api/v1/devices/${deviceId}/heartbeat`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                activation_code: activationCode,
                status: "online",
                current_content_id: currentlyPlayingContentId
            })
        });
    }, 30000);
    ```

    **Online/Offline Logic**:
    - Device is_online = True jika last_seen < 5 minutes
    - Dashboard shows device online/offline based on this
    """
    device_repo = DeviceRepository(db)
    device = device_repo.get(device_id)

    if not device:
        raise NotFoundException(
            message=f"Device {device_id} not found"
        )

    # Verify activation code if provided
    if heartbeat_data.activation_code:
        if device.activation_code != heartbeat_data.activation_code:
            raise ForbiddenException(
                message="Invalid activation code",
                details={"activation_code": "Activation code does not match"}
            )

    # Update last_seen
    updated_device = device_repo.update(device_id, {
        "last_seen": datetime.utcnow()
    })

    # Check if online
    is_online = datetime.utcnow() - updated_device.last_seen < timedelta(minutes=5)

    return {
        "device_id": device_id,
        "status": "ok",
        "last_seen": updated_device.last_seen,
        "is_online": is_online,
        "message": "Heartbeat received"
    }


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Get Device Details",
    description="Get device information by ID"
)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get device details."""
    device_repo = DeviceRepository(db)
    device = device_repo.get(device_id)

    if not device:
        raise NotFoundException(
            message=f"Device {device_id} not found"
        )

    device_dict = device.to_dict()

    # Add is_online status
    if device.last_seen:
        device_dict["is_online"] = datetime.utcnow() - device.last_seen < timedelta(minutes=5)
    else:
        device_dict["is_online"] = False

    return device_dict


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update Device",
    description="Update device information"
)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update device metadata.

    **Updatable Fields**:
    - device_name
    - device_type
    - location
    - screen_resolution
    - is_active
    - is_approved
    """
    device_repo = DeviceRepository(db)
    device = device_repo.get(device_id)

    if not device:
        raise NotFoundException(
            message=f"Device {device_id} not found"
        )

    # Build update dict
    update_data = device_update.model_dump(exclude_none=True)

    # Update device
    updated_device = device_repo.update(device_id, update_data)

    device_dict = updated_device.to_dict()

    # Add is_online status
    if updated_device.last_seen:
        device_dict["is_online"] = datetime.utcnow() - updated_device.last_seen < timedelta(minutes=5)
    else:
        device_dict["is_online"] = False

    return device_dict


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Device",
    description="Soft delete device (sets is_active=False)"
)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete device.

    **Note**: Sets is_active=False instead of hard delete.
    Device can be reactivated later via PUT endpoint.
    """
    device_repo = DeviceRepository(db)
    device = device_repo.get(device_id)

    if not device:
        raise NotFoundException(
            message=f"Device {device_id} not found"
        )

    # Soft delete
    device_repo.update(device_id, {"is_active": False})

    return None


@router.post(
    "/{device_id}/approve",
    response_model=DeviceResponse,
    summary="Approve Device",
    description="Approve pending device (manual approval workflow)"
)
async def approve_device(
    device_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Approve pending device.

    **Use Case**: Manual approval workflow
    - Device registers with is_approved=False
    - Admin reviews device in dashboard
    - Admin calls this endpoint to approve
    - Device becomes active
    """
    device_repo = DeviceRepository(db)
    device = device_repo.get(device_id)

    if not device:
        raise NotFoundException(
            message=f"Device {device_id} not found"
        )

    if device.is_approved:
        raise BadRequestException(
            message="Device already approved"
        )

    # Approve device
    updated_device = device_repo.update(device_id, {
        "is_approved": True,
        "is_active": True
    })

    device_dict = updated_device.to_dict()
    if updated_device.last_seen:
        device_dict["is_online"] = datetime.utcnow() - updated_device.last_seen < timedelta(minutes=5)
    else:
        device_dict["is_online"] = False

    return device_dict


@router.get(
    "/",
    response_model=DeviceListResponse,
    summary="List Devices",
    description="List organization devices with pagination and filtering"
)
async def list_devices(
    organization_id: int = Query(..., description="Organization ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    is_approved: Optional[bool] = Query(None, description="Filter by approval status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    is_online: Optional[bool] = Query(None, description="Filter by online status"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List organization devices.

    **Filters**:
    - is_approved: Filter by approval status
    - is_active: Filter by active status
    - device_type: Filter by type (screen, tv, monitor, etc)
    - is_online: Filter by online status (last_seen < 5 min)

    **Sorting**: By created_at DESC (newest first)
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    device_repo = DeviceRepository(db)

    # Build filters
    filters = {"organization_id": organization_id}
    if is_approved is not None:
        filters["is_approved"] = is_approved
    if is_active is not None:
        filters["is_active"] = is_active
    if device_type:
        filters["device_type"] = device_type

    # Get devices
    devices = device_repo.get_by_organization(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        filters=filters
    )

    # Filter by online status if requested
    if is_online is not None:
        online_cutoff = datetime.utcnow() - timedelta(minutes=5)
        devices = [
            d for d in devices
            if (d.last_seen and d.last_seen > online_cutoff) == is_online
        ]

    # Get total count
    total = device_repo.count_by_organization(
        organization_id=organization_id,
        filters=filters
    )

    # Format response
    devices_list = []
    for device in devices:
        device_dict = device.to_dict()
        # Add is_online status
        if device.last_seen:
            device_dict["is_online"] = datetime.utcnow() - device.last_seen < timedelta(minutes=5)
        else:
            device_dict["is_online"] = False
        devices_list.append(device_dict)

    return {
        "devices": devices_list,
        "total": total,
        "skip": skip,
        "limit": limit,
        "filters": filters
    }


@router.get(
    "/stats/{organization_id}",
    response_model=DeviceStatsResponse,
    summary="Get Device Statistics",
    description="Get device statistics for organization"
)
async def get_device_stats(
    organization_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get device statistics.

    **Returns**:
    - Total devices
    - Active/inactive count
    - Approved/pending count
    - Online/offline count (based on last_seen < 5 min)
    - Count by device type
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    device_repo = DeviceRepository(db)

    # Get device stats
    stats = device_repo.get_device_stats(organization_id)

    # Calculate online/offline
    online_cutoff = datetime.utcnow() - timedelta(minutes=5)
    all_devices = device_repo.get_by_organization(
        organization_id=organization_id,
        skip=0,
        limit=1000,
        filters={}
    )

    online_count = sum(
        1 for d in all_devices
        if d.last_seen and d.last_seen > online_cutoff
    )
    offline_count = len(all_devices) - online_count

    return {
        "organization_id": organization_id,
        "total_devices": stats["total"],
        "active_devices": stats["active"],
        "inactive_devices": stats["inactive"],
        "approved_devices": stats["approved"],
        "pending_approval": stats["pending"],
        "online_devices": online_count,
        "offline_devices": offline_count,
        "by_type": stats["by_type"]
    }
