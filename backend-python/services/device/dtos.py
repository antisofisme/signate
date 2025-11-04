"""
Device DTOs (Data Transfer Objects)
Request/Response models for Device API layer
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# =============================================================================
# REQUEST DTOs
# =============================================================================

class RequestActivationCodeRequest(BaseModel):
    """Request activation code - called by player"""
    organization_id: int = Field(..., gt=0)
    device_type: str = Field(default='monitor', pattern='^(tv|monitor)$')
    device_name: str = Field(default='New Device', max_length=200)
    device_uuid: Optional[str] = Field(None, max_length=100)
    platform: str = Field(default='browser', max_length=50)


class ActivateDeviceRequest(BaseModel):
    """Activate device - called by CMS admin"""
    unique_code: str = Field(..., min_length=6, max_length=6)
    device_name: Optional[str] = Field(None, max_length=200)
    room_number: Optional[str] = Field(None, max_length=50)
    location_type: Optional[str] = Field(None, pattern='^(guest_room|lobby|conference_room|restaurant|other)$')


class HeartbeatRequest(BaseModel):
    """Heartbeat from player - sent every 30 seconds"""
    unique_code: str = Field(..., min_length=6, max_length=6)
    device_uuid: Optional[str] = None
    screen_width: Optional[int] = Field(None, gt=0)
    screen_height: Optional[int] = Field(None, gt=0)
    viewport_width: Optional[int] = Field(None, gt=0)
    viewport_height: Optional[int] = Field(None, gt=0)
    device_pixel_ratio: Optional[float] = Field(None, gt=0)
    user_agent: Optional[str] = Field(None, max_length=500)
    connection_type: Optional[str] = Field(None, max_length=50)
    connection_speed: Optional[float] = Field(None, ge=0)


class UpdateDeviceRequest(BaseModel):
    """Update device settings - called by CMS admin"""
    device_name: Optional[str] = Field(None, max_length=200)
    room_number: Optional[str] = Field(None, max_length=50)
    location_type: Optional[str] = Field(None, pattern='^(guest_room|lobby|conference_room|restaurant|other)$')
    rotation: Optional[int] = Field(None, pattern='^(0|90|180|270)$')
    volume_enabled: Optional[bool] = None
    supports_personalization: Optional[bool] = None
    privacy_mode: Optional[str] = Field(None, pattern='^(none|limited|full)$')


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class ActivationCodeResponse(BaseModel):
    """Activation code response - for player"""
    unique_code: str
    expires_at: str  # ISO format
    device_id: int

    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    """Device response - for CMS"""
    id: int
    device_type: str
    device_name: str
    organization_id: int

    # Activation info
    unique_code: Optional[str]
    code_expires_at: Optional[datetime]
    device_uuid: Optional[str]

    # Network info
    ip_address: Optional[str]
    platform: Optional[str]

    # Device metadata
    screen_width: Optional[int]
    screen_height: Optional[int]
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    device_pixel_ratio: Optional[float]
    user_agent: Optional[str]
    connection_type: Optional[str]
    connection_speed: Optional[float]

    # WebOS specific
    model_name: Optional[str]
    firmware_version: Optional[str]

    # Status
    status: str
    last_seen: Optional[datetime]
    is_online: bool  # Computed field

    # Display settings
    rotation: int
    volume_enabled: bool

    # Hotel-specific
    room_number: Optional[str]
    location_type: str
    supports_personalization: bool
    privacy_mode: str

    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]
    released_at: Optional[datetime]

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """List of devices - for CMS dashboard"""
    devices: list[DeviceResponse]
    total: int
    online: int

    class Config:
        from_attributes = True


class HeartbeatResponse(BaseModel):
    """Heartbeat response - minimal response to player"""
    success: bool = True
    message: str = "Heartbeat received"

    class Config:
        from_attributes = True


class ActivationStatusResponse(BaseModel):
    """Check activation status - for player polling"""
    is_activated: bool
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    message: str

    class Config:
        from_attributes = True
