"""
PMS Sync Routes
API endpoints for Firebird Bridge Agent to sync data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser

from services.pms.dtos import (
    BulkGuestSyncRequest,
    BulkRoomSyncRequest,
    GuestListResponse,
    GuestResponse,
    RoomListResponse,
    RoomResponse,
    PMSStatsResponse,
    PMSConfigResponse,
    CreatePMSConfigRequest,
    UpdatePMSConfigRequest,
)

from services.pms.use_cases.sync_guests import SyncGuestsUseCase
from services.pms.use_cases.sync_rooms import SyncRoomsUseCase
from services.pms.use_cases.get_pms_stats import GetPMSStatsUseCase
from services.pms.repositories.pms_repo import PMSRepository

import secrets
from datetime import datetime

router = APIRouter(prefix="/pms", tags=["PMS Integration"])


# ============================================================================
# Authentication Dependency for Bridge Agent
# ============================================================================


def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db)
) -> int:
    """
    Verify API key from Firebird Bridge Agent

    Returns:
        organization_id if valid
    """
    if not x_api_key or not x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key or X-Organization-ID header"
        )

    repo = PMSRepository(db)
    config = repo.get_config_by_api_key(x_api_key)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    if config.organization_id != x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization ID mismatch"
        )

    if not config.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PMS integration is disabled"
        )

    return x_organization_id


# ============================================================================
# SYNC ENDPOINTS (for Bridge Agent)
# ============================================================================


@router.post("/sync/guests", status_code=status.HTTP_201_CREATED)
def sync_guests(
    request: BulkGuestSyncRequest,
    organization_id: int = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Sync guest check-in data from Firebird Bridge Agent

    Requires:
    - X-API-Key header
    - X-Organization-ID header
    """
    try:
        use_case = SyncGuestsUseCase(db)
        guests_data = [guest.dict() for guest in request.guests]
        result = use_case.execute(guests_data, organization_id)

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync guests: {str(e)}"
        )


@router.post("/sync/rooms", status_code=status.HTTP_201_CREATED)
def sync_rooms(
    request: BulkRoomSyncRequest,
    organization_id: int = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Sync room status from Firebird Bridge Agent

    Requires:
    - X-API-Key header
    - X-Organization-ID header
    """
    try:
        use_case = SyncRoomsUseCase(db)
        rooms_data = [room.dict() for room in request.rooms]
        result = use_case.execute(rooms_data, organization_id)

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync rooms: {str(e)}"
        )


# ============================================================================
# DATA ENDPOINTS (for Web Admin)
# ============================================================================


@router.get("/guests", response_model=GuestListResponse)
def get_guests(
    limit: int = 100,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get guest data for organization"""
    try:
        repo = PMSRepository(db)
        guests = repo.get_guests_by_organization(
            current_user.organization_id, limit, offset
        )

        guest_responses = [GuestResponse(**g.to_dict()) for g in guests]

        return GuestListResponse(items=guest_responses, total=len(guest_responses))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get guests: {str(e)}"
        )


@router.get("/guests/current", response_model=GuestListResponse)
def get_current_guests(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get currently checked-in guests"""
    try:
        repo = PMSRepository(db)
        guests = repo.get_current_guests(current_user.organization_id)

        guest_responses = [GuestResponse(**g.to_dict()) for g in guests]

        return GuestListResponse(items=guest_responses, total=len(guest_responses))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current guests: {str(e)}"
        )


@router.get("/rooms", response_model=RoomListResponse)
def get_rooms(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get room status for organization"""
    try:
        repo = PMSRepository(db)
        rooms = repo.get_rooms_by_organization(current_user.organization_id)

        room_responses = [RoomResponse(**r.to_dict()) for r in rooms]

        return RoomListResponse(items=room_responses, total=len(room_responses))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rooms: {str(e)}"
        )


@router.get("/device/{device_id}/current-guest")
def get_device_current_guest(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current guest data for a specific device (by room association)
    
    This endpoint is used by the player to fetch PMS data for template processing
    """
    try:
        # Get device info
        from services.device.repositories.device_repo import DeviceRepository
        device_repo = DeviceRepository(db)
        device = device_repo.get_by_device_id(device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Extract room number from device location or metadata
        room_number = None
        if device.location:
            # Assume location contains room number (e.g., "Room 301" -> "301")
            import re
            match = re.search(r'(\d+)', device.location)
            if match:
                room_number = match.group(1)
        
        if not room_number and device.metadata:
            # Check metadata for room_number field
            room_number = device.metadata.get('room_number')
        
        if not room_number:
            # No room association
            return {
                "guest_name": None,
                "room_number": None,
                "message": "Device not associated with a room"
            }
        
        # Get PMS repo and find guest by room
        pms_repo = PMSRepository(db)
        
        # Get room info
        room = pms_repo.get_room_by_number(room_number, device.organization_id)
        if not room or room.status != 'occupied':
            return {
                "guest_name": None,
                "room_number": room_number,
                "room_status": room.status if room else "not_found",
                "message": "Room not occupied"
            }
        
        # Get current guest in this room
        guests = pms_repo.get_guests_by_room(room_number, device.organization_id)
        current_guest = None
        
        for guest in guests:
            if guest.checkout_date is None or guest.checkout_date >= datetime.now().date():
                current_guest = guest
                break
        
        if not current_guest:
            return {
                "guest_name": None,
                "room_number": room_number,
                "room_status": "occupied",
                "message": "No active guest found"
            }
        
        # Return guest data for template processing
        return {
            "guest_name": current_guest.guest_name,
            "guest_title": current_guest.title,
            "room_number": room_number,
            "check_in_date": current_guest.checkin_date.isoformat() if current_guest.checkin_date else None,
            "check_out_date": current_guest.checkout_date.isoformat() if current_guest.checkout_date else None,
            "balance": float(current_guest.balance) if current_guest.balance else 0,
            "loyalty_level": current_guest.loyalty_level,
            "language": current_guest.language,
            "country": current_guest.country,
            "special_requests": current_guest.special_requests,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get guest data: {str(e)}"
        )


@router.get("/stats", response_model=PMSStatsResponse)
def get_pms_stats(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get PMS integration statistics"""
    try:
        use_case = GetPMSStatsUseCase(db)
        stats = use_case.execute(current_user.organization_id)

        return PMSStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================


@router.post("/config", response_model=PMSConfigResponse, status_code=status.HTTP_201_CREATED)
def create_pms_config(
    request: CreatePMSConfigRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create PMS configuration and generate API key

    Returns API key for Firebird Bridge Agent
    """
    try:
        repo = PMSRepository(db)

        # Check if config already exists
        existing = repo.get_config_by_organization(current_user.organization_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PMS configuration already exists"
            )

        # Generate API key
        api_key = secrets.token_urlsafe(32)

        config_data = {
            "organization_id": current_user.organization_id,
            "api_key": api_key,
            "sync_interval_minutes": request.sync_interval_minutes,
            "is_active": True,
            "created_by": current_user.id,
        }

        config = repo.create_config(config_data)

        return PMSConfigResponse(**config.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create config: {str(e)}"
        )


@router.get("/config", response_model=PMSConfigResponse)
def get_pms_config(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get PMS configuration"""
    try:
        repo = PMSRepository(db)
        config = repo.get_config_by_organization(current_user.organization_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PMS configuration not found"
            )

        return PMSConfigResponse(**config.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}"
        )


@router.put("/config", response_model=PMSConfigResponse)
def update_pms_config(
    request: UpdatePMSConfigRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update PMS configuration"""
    try:
        repo = PMSRepository(db)
        config = repo.get_config_by_organization(current_user.organization_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PMS configuration not found"
            )

        updates = request.dict(exclude_unset=True)
        updated_config = repo.update_config(config.id, updates)

        return PMSConfigResponse(**updated_config.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config: {str(e)}"
        )
