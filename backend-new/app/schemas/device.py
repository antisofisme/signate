"""
Device Schemas
==============

Pydantic schemas for device API requests and responses.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ==================== Request Schemas ====================

class DeviceRegister(BaseModel):
    """Schema for device registration with PIN."""

    organization_pin: str = Field(..., min_length=8, max_length=8, description="8-digit organization PIN")
    device_name: str = Field(..., min_length=1, max_length=100, description="Device name/identifier")
    device_type: Optional[str] = Field("screen", description="Device type: screen, tv, monitor")
    location: Optional[str] = Field(None, max_length=200, description="Device location")
    hardware_id: Optional[str] = Field(None, max_length=100, description="Hardware identifier (MAC, UUID, etc)")
    screen_resolution: Optional[str] = Field(None, max_length=20, description="Screen resolution (e.g., 1920x1080)")

    @field_validator("organization_pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        """Validate PIN is exactly 8 digits."""
        if not v.isdigit():
            raise ValueError("PIN must contain only digits")
        if len(v) != 8:
            raise ValueError("PIN must be exactly 8 digits")
        return v

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, v: Optional[str]) -> str:
        """Validate device type."""
        if v:
            allowed_types = ["screen", "tv", "monitor", "kiosk", "tablet"]
            if v.lower() not in allowed_types:
                raise ValueError(f"device_type must be one of: {', '.join(allowed_types)}")
            return v.lower()
        return "screen"

    class Config:
        json_schema_extra = {
            "example": {
                "organization_pin": "12345678",
                "device_name": "Lobby Screen 1",
                "device_type": "screen",
                "location": "Main Lobby",
                "hardware_id": "AA:BB:CC:DD:EE:FF",
                "screen_resolution": "1920x1080"
            }
        }


class DeviceUpdate(BaseModel):
    """Schema for updating device."""

    device_name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_type: Optional[str] = Field(None)
    location: Optional[str] = Field(None, max_length=200)
    screen_resolution: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate device type if provided."""
        if v:
            allowed_types = ["screen", "tv", "monitor", "kiosk", "tablet"]
            if v.lower() not in allowed_types:
                raise ValueError(f"device_type must be one of: {', '.join(allowed_types)}")
            return v.lower()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "device_name": "Lobby Screen 1 - Updated",
                "location": "Main Lobby - Floor 1",
                "is_active": True
            }
        }


class DeviceHeartbeat(BaseModel):
    """Schema for device heartbeat."""

    activation_code: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit activation code")
    status: Optional[str] = Field("online", description="Device status")
    current_content_id: Optional[int] = Field(None, description="Currently playing content ID")

    @field_validator("activation_code")
    @classmethod
    def validate_activation_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate activation code format."""
        if v:
            if not v.isdigit():
                raise ValueError("Activation code must contain only digits")
            if len(v) != 6:
                raise ValueError("Activation code must be exactly 6 digits")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "activation_code": "123456",
                "status": "online",
                "current_content_id": 42
            }
        }


# ==================== Response Schemas ====================

class DeviceBase(BaseModel):
    """Base device response schema."""

    id: int
    organization_id: int
    device_name: str
    device_type: str
    activation_code: str
    location: Optional[str] = None
    hardware_id: Optional[str] = None
    screen_resolution: Optional[str] = None
    is_active: bool
    is_approved: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @property
    def is_online(self) -> bool:
        """Check if device is online (last_seen within 5 minutes)."""
        if not self.last_seen:
            return False
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.last_seen < timedelta(minutes=5)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "device_name": "Lobby Screen 1",
                "device_type": "screen",
                "activation_code": "123456",
                "location": "Main Lobby",
                "hardware_id": "AA:BB:CC:DD:EE:FF",
                "screen_resolution": "1920x1080",
                "is_active": True,
                "is_approved": True,
                "last_seen": "2025-10-30T14:30:00Z",
                "created_at": "2025-10-30T10:00:00Z",
                "updated_at": "2025-10-30T14:30:00Z"
            }
        }


class DeviceResponse(DeviceBase):
    """Standard device response."""

    is_online: Optional[bool] = Field(None, description="Derived from last_seen")


class DeviceRegisterResponse(DeviceBase):
    """Response for successful device registration."""

    organization_name: str = Field(..., description="Organization name for confirmation")
    registration_message: str = Field(default="Device registered successfully")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "organization_name": "Acme Corporation",
                "device_name": "Lobby Screen 1",
                "device_type": "screen",
                "activation_code": "123456",
                "location": "Main Lobby",
                "is_active": True,
                "is_approved": True,
                "created_at": "2025-10-30T10:00:00Z",
                "registration_message": "Device registered successfully"
            }
        }


class DeviceListResponse(BaseModel):
    """Response for list devices endpoint."""

    devices: List[DeviceResponse]
    total: int
    skip: int
    limit: int
    filters: dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "devices": [
                    {
                        "id": 1,
                        "organization_id": 1,
                        "device_name": "Lobby Screen 1",
                        "device_type": "screen",
                        "activation_code": "123456",
                        "is_active": True,
                        "is_approved": True,
                        "is_online": True,
                        "last_seen": "2025-10-30T14:30:00Z",
                        "created_at": "2025-10-30T10:00:00Z"
                    }
                ],
                "total": 45,
                "skip": 0,
                "limit": 20,
                "filters": {"is_approved": True}
            }
        }


class DeviceStatsResponse(BaseModel):
    """Device statistics."""

    organization_id: int
    total_devices: int
    active_devices: int
    inactive_devices: int
    approved_devices: int
    pending_approval: int
    online_devices: int
    offline_devices: int
    by_type: dict = Field(default_factory=dict, description="Count by device type")

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "total_devices": 45,
                "active_devices": 42,
                "inactive_devices": 3,
                "approved_devices": 40,
                "pending_approval": 5,
                "online_devices": 38,
                "offline_devices": 7,
                "by_type": {
                    "screen": 30,
                    "tv": 10,
                    "monitor": 5
                }
            }
        }


class DeviceHeartbeatResponse(BaseModel):
    """Response for heartbeat endpoint."""

    device_id: int
    status: str = "ok"
    last_seen: datetime
    is_online: bool
    message: str = "Heartbeat received"

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "status": "ok",
                "last_seen": "2025-10-30T14:30:00Z",
                "is_online": True,
                "message": "Heartbeat received"
            }
        }
