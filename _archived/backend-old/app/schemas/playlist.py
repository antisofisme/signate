"""
Playlist schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class PlaylistSchedule(BaseModel):
    """Schema for playlist schedule configuration"""
    start_time: str = Field(default="00:00", pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: str = Field(default="23:59", pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    days: List[str] = Field(default=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
    start_date: Optional[str] = None  # Format: YYYY-MM-DD
    end_date: Optional[str] = None    # Format: YYYY-MM-DD

    class Config:
        json_schema_extra = {
            "example": {
                "start_time": "07:00",
                "end_time": "23:00",
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            }
        }


class PlaylistCreate(BaseModel):
    """Schema for creating a playlist"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    priority: int = Field(default=1, ge=1, le=10)
    schedule: Optional[PlaylistSchedule] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Morning Show",
                "description": "Content for morning hours",
                "is_active": True,
                "priority": 5,
                "schedule": {
                    "start_time": "07:00",
                    "end_time": "12:00",
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                }
            }
        }


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    schedule: Optional[Any] = None  # Can be dict or PlaylistSchedule


class PlaylistContentItem(BaseModel):
    """Schema for content item in playlist"""
    id: int
    content_id: int
    content_name: str
    content_type: str
    order_index: int
    duration: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class PlaylistResponse(BaseModel):
    """Schema for playlist response"""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    priority: int
    schedule: Optional[Any]
    content_count: int = 0
    total_duration: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Morning Show",
                "description": "Content for morning hours",
                "is_active": True,
                "priority": 5,
                "schedule": {
                    "start_time": "07:00",
                    "end_time": "12:00",
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "content_count": 5,
                "total_duration": 180,
                "created_at": "2025-10-26T07:00:00",
                "updated_at": "2025-10-26T08:00:00"
            }
        }


class PlaylistListResponse(BaseModel):
    """Schema for list of playlists"""
    total: int
    items: List[PlaylistResponse]


class PlaylistContentResponse(BaseModel):
    """Schema for playlist content response"""
    total: int
    items: List[PlaylistContentItem]


class PlaylistContentAdd(BaseModel):
    """Schema for adding content to playlist"""
    content_ids: List[int] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "content_ids": [1, 2, 3]
            }
        }


class PlaylistContentReorder(BaseModel):
    """Schema for reordering playlist content"""
    content_items: List[dict] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "content_items": [
                    {"id": 1, "order_index": 0, "duration": 10},
                    {"id": 2, "order_index": 1, "duration": 15}
                ]
            }
        }


class PlaylistDeviceAssign(BaseModel):
    """Schema for assigning playlist to devices"""
    device_ids: List[int] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "device_ids": [1, 2, 3]
            }
        }


class PlaylistTagAssign(BaseModel):
    """Schema for assigning playlist to tags"""
    tag_ids: List[int] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "tag_ids": [1, 2]
            }
        }


class PlaylistAssignmentResponse(BaseModel):
    """Schema for playlist assignment response"""
    devices: List[dict]
    tags: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "devices": [
                    {"id": 1, "name": "Lobby TV 1", "device_type": "tv"}
                ],
                "tags": [
                    {"id": 1, "tag_name": "Lobby", "color": "#3B82F6"}
                ]
            }
        }
