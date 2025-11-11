"""
Tag schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TagCreate(BaseModel):
    """Schema for creating a tag"""
    tag_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")

    class Config:
        json_schema_extra = {
            "example": {
                "tag_name": "Lobby TVs",
                "description": "All TVs in lobby area",
                "color": "#3B82F6"
            }
        }


class TagUpdate(BaseModel):
    """Schema for updating a tag"""
    tag_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    """Schema for tag response"""
    id: int
    tag_name: str
    description: Optional[str]
    color: str
    created_at: datetime
    device_count: int = 0  # Number of devices with this tag

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "tag_name": "Lobby TVs",
                "description": "All TVs in lobby area",
                "color": "#3B82F6",
                "created_at": "2025-10-21T10:00:00",
                "device_count": 5
            }
        }


class TagListResponse(BaseModel):
    """Schema for list of tags"""
    total: int
    items: list[TagResponse]


class DeviceTagAssign(BaseModel):
    """Schema for assigning tag to device"""
    tag_id: int
    device_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "tag_id": 1,
                "device_id": 1
            }
        }
