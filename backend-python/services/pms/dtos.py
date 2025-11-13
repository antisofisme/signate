"""
PMS Integration DTOs
Request/Response data transfer objects
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Guest DTOs
# ============================================================================


class GuestSyncRequest(BaseModel):
    """Single guest data from Firebird Bridge Agent"""

    organization_id: int
    guest_name: str
    room_number: str
    checkin_date: str  # ISO format
    checkout_date: str  # ISO format
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    reservation_no: Optional[str] = None


class BulkGuestSyncRequest(BaseModel):
    """Bulk guest sync from Bridge Agent"""

    guests: List[GuestSyncRequest]


class GuestResponse(BaseModel):
    """Guest data response"""

    id: int
    organization_id: int
    guest_name: str
    room_number: str
    checkin_date: str
    checkout_date: str
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    reservation_no: Optional[str] = None
    synced_at: str
    updated_at: str


class GuestListResponse(BaseModel):
    """List of guests"""

    items: List[GuestResponse]
    total: int


# ============================================================================
# Room DTOs
# ============================================================================


class RoomSyncRequest(BaseModel):
    """Single room status from Firebird Bridge Agent"""

    organization_id: int
    room_number: str
    room_type: Optional[str] = None
    status: str  # available, occupied, cleaning, maintenance
    floor: Optional[str] = None
    bed_type: Optional[str] = None
    max_occupancy: Optional[int] = None


class BulkRoomSyncRequest(BaseModel):
    """Bulk room sync from Bridge Agent"""

    rooms: List[RoomSyncRequest]


class RoomResponse(BaseModel):
    """Room status response"""

    id: int
    organization_id: int
    room_number: str
    room_type: Optional[str] = None
    status: str
    floor: Optional[str] = None
    bed_type: Optional[str] = None
    max_occupancy: Optional[int] = None
    synced_at: str
    updated_at: str


class RoomListResponse(BaseModel):
    """List of rooms"""

    items: List[RoomResponse]
    total: int


# ============================================================================
# Configuration DTOs
# ============================================================================


class CreatePMSConfigRequest(BaseModel):
    """Create PMS configuration"""

    sync_interval_minutes: int = Field(default=5, ge=1, le=60)


class UpdatePMSConfigRequest(BaseModel):
    """Update PMS configuration"""

    is_active: Optional[bool] = None
    sync_interval_minutes: Optional[int] = Field(default=None, ge=1, le=60)


class PMSConfigResponse(BaseModel):
    """PMS configuration response"""

    id: int
    organization_id: int
    api_key: str
    is_active: bool
    last_synced_at: Optional[str] = None
    sync_interval_minutes: int
    created_by: Optional[int] = None
    created_at: str
    updated_at: str


# ============================================================================
# Stats DTOs
# ============================================================================


class PMSStatsResponse(BaseModel):
    """PMS integration statistics"""

    total_guests: int
    checkins_today: int
    checkouts_today: int
    current_occupancy: int
    total_rooms: int
    available_rooms: int
    occupied_rooms: int
    last_synced_at: Optional[str] = None
