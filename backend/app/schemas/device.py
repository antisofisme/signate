"""
Device schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class DeviceBase(BaseModel):
    """Base device schema"""
    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(..., pattern="^(tv|monitor)$")


class TVRegisterRequest(BaseModel):
    """Request schema for registering a TV device"""
    device_name: str = Field(..., min_length=1, max_length=100)
    ip_address: str = Field(..., pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    passphrase: str = Field(..., min_length=6, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "device_name": "Lobby TV 1",
                "ip_address": "192.168.1.100",
                "passphrase": "123456"
            }
        }


class MonitorGenerateRequest(BaseModel):
    """Request schema for generating monitor activation code"""
    device_name: str = Field(..., min_length=1, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "device_name": "Reception Monitor 1"
            }
        }


class MonitorSelfRegisterRequest(BaseModel):
    """Request schema for monitor self-registration (no auth required)"""
    activation_code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")
    device_name: str = Field(..., min_length=1, max_length=100)
    device_uuid: Optional[str] = Field(None, min_length=36, max_length=36)
    platform: Optional[str] = Field(None, max_length=20)
    model_name: Optional[str] = Field(None, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "activation_code": "123456",
                "device_name": "Monitor-123456",
                "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "platform": "webOS",
                "model_name": "LG OLED55C1PUB"
            }
        }


class MonitorActivateRequest(BaseModel):
    """Request schema for activating a monitor"""
    unique_code: str = Field(..., min_length=6, max_length=20)

    class Config:
        json_schema_extra = {
            "example": {
                "unique_code": "ABC123"
            }
        }


class DeviceUpdateRequest(BaseModel):
    """Request schema for updating device"""
    device_name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, pattern="^(pending|active|inactive)$")
    # Display settings
    rotation: Optional[int] = Field(None, ge=0, le=270)
    volume_enabled: Optional[bool] = None

    @validator('rotation')
    def validate_rotation(cls, v):
        if v is not None and v not in [0, 90, 180, 270]:
            raise ValueError('rotation must be 0, 90, 180, or 270')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "device_name": "Updated Device Name",
                "status": "active",
                "rotation": 0,
                "volume_enabled": True
            }
        }


class HeartbeatRequest(BaseModel):
    """Request schema for device heartbeat"""
    device_id: int
    ip_address: Optional[str] = None
    # Permanent device identifier
    device_uuid: Optional[str] = None
    # Platform information
    platform: Optional[str] = None
    model_name: Optional[str] = None
    firmware_version: Optional[str] = None
    # Device information
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    device_pixel_ratio: Optional[float] = None
    user_agent: Optional[str] = None
    connection_type: Optional[str] = None
    connection_speed: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "ip_address": "192.168.1.100",
                "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "platform": "webOS",
                "model_name": "LG OLED55C1PUB",
                "firmware_version": "6.0.0",
                "screen_width": 1920,
                "screen_height": 1080,
                "viewport_width": 1299,
                "viewport_height": 902,
                "device_pixel_ratio": 1.0,
                "user_agent": "Mozilla/5.0...",
                "connection_type": "4g",
                "connection_speed": 5.3
            }
        }


class DeviceResponse(BaseModel):
    """Response schema for device"""
    id: int
    device_type: str
    device_name: str
    ip_address: Optional[str] = None
    unique_code: Optional[str] = None
    code_expires_at: Optional[datetime] = None
    device_uuid: Optional[str] = None
    platform: Optional[str] = None
    model_name: Optional[str] = None
    firmware_version: Optional[str] = None
    status: str
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Device information
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    device_pixel_ratio: Optional[float] = None
    user_agent: Optional[str] = None
    connection_type: Optional[str] = None
    connection_speed: Optional[float] = None
    # Display settings
    rotation: int = 0
    volume_enabled: bool = True

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_type": "tv",
                "device_name": "Lobby TV 1",
                "ip_address": "192.168.1.100",
                "unique_code": None,
                "code_expires_at": None,
                "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "platform": "webOS",
                "model_name": "LG OLED55C1PUB",
                "firmware_version": "6.0.0",
                "status": "active",
                "last_seen": "2025-10-21T12:00:00",
                "created_at": "2025-10-21T10:00:00",
                "updated_at": "2025-10-21T10:00:00",
                "screen_width": 1920,
                "screen_height": 1080,
                "viewport_width": 1299,
                "viewport_height": 902,
                "device_pixel_ratio": 1.0,
                "user_agent": "Mozilla/5.0...",
                "connection_type": "4g",
                "connection_speed": 5.3,
                "rotation": 0,
                "volume_enabled": True
            }
        }


class MonitorCodeResponse(BaseModel):
    """Response schema for monitor code generation"""
    device_id: int
    device_name: str
    unique_code: str
    code_expires_at: datetime
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 2,
                "device_name": "Reception Monitor 1",
                "unique_code": "ABC123",
                "code_expires_at": "2025-10-21T10:10:00",
                "status": "pending"
            }
        }


class DeviceListResponse(BaseModel):
    """Response schema for device list"""
    total: int
    devices: List[DeviceResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "devices": [
                    {
                        "id": 1,
                        "device_type": "tv",
                        "device_name": "Lobby TV 1",
                        "status": "active"
                    }
                ]
            }
        }


class HeartbeatResponse(BaseModel):
    """Response schema for heartbeat"""
    device_id: int
    status: str
    last_seen: datetime
    message: str
    # Display settings (for auto-update)
    rotation: int = 0
    volume_enabled: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "status": "active",
                "last_seen": "2025-10-21T12:00:00",
                "message": "Heartbeat recorded",
                "rotation": 0,
                "volume_enabled": True
            }
        }
