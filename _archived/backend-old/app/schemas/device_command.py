"""
Device Command schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DeviceCommandBase(BaseModel):
    """Base device command schema"""
    command_type: str = Field(..., pattern="^(reset|refresh|reload|run_speed_test)$")
    reason: Optional[str] = Field(None, max_length=100)


class DeviceCommandCreate(DeviceCommandBase):
    """Schema for creating a new device command"""
    device_id: int = Field(..., gt=0)
    expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "command_type": "reset",
                "reason": "deleted_by_admin"
            }
        }


class DeviceCommandResponse(DeviceCommandBase):
    """Schema for device command response"""
    id: int
    device_id: int
    status: str
    created_at: datetime
    executed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_id": 1,
                "command_type": "reset",
                "reason": "deleted_by_admin",
                "status": "pending",
                "created_at": "2025-10-24T10:00:00",
                "executed_at": None,
                "expires_at": "2025-10-31T10:00:00"
            }
        }


class DeviceCommandListResponse(BaseModel):
    """Schema for list of device commands"""
    commands: List[DeviceCommandResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "commands": [
                    {
                        "id": 1,
                        "device_id": 1,
                        "command_type": "reset",
                        "reason": "deleted_by_admin",
                        "status": "pending",
                        "created_at": "2025-10-24T10:00:00",
                        "executed_at": None,
                        "expires_at": "2025-10-31T10:00:00"
                    }
                ],
                "total": 1
            }
        }


class DeviceCommandExecuteRequest(BaseModel):
    """Schema for executing a device command (viewer side)"""
    command_id: int = Field(..., gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "command_id": 1
            }
        }
