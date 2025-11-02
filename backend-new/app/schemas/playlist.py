"""
Playlist Schemas
================

Pydantic schemas for playlist API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, time
from pydantic import BaseModel, Field, field_validator


# ==================== Request Schemas ====================

class PlaylistCreate(BaseModel):
    """Schema for creating a new playlist."""

    name: str = Field(..., min_length=1, max_length=100, description="Playlist name")
    description: Optional[str] = Field(None, max_length=1000, description="Playlist description")
    is_active: bool = Field(True, description="Whether playlist is active")
    priority: int = Field(1, ge=1, le=10, description="Priority level (1-10, higher = more important)")

    # Scheduling fields
    schedule_mode: Optional[str] = Field("inclusive", description="'inclusive' or 'exclusive'")
    schedule_start: Optional[str] = Field(None, description="Start time (HH:MM:SS)")
    schedule_end: Optional[str] = Field(None, description="End time (HH:MM:SS)")
    schedule_days: Optional[str] = Field(None, description='JSON array of days ["mon","tue","wed"]')
    schedule_timezone: Optional[str] = Field("Asia/Jakarta", description="Timezone for schedule")

    @field_validator("schedule_mode")
    @classmethod
    def validate_schedule_mode(cls, v: Optional[str]) -> Optional[str]:
        """Validate schedule mode is 'inclusive' or 'exclusive'."""
        if v:
            if v.lower() not in ["inclusive", "exclusive"]:
                raise ValueError("schedule_mode must be 'inclusive' or 'exclusive'")
            return v.lower()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Morning Promotions",
                "description": "Promotional content for morning hours",
                "is_active": True,
                "priority": 5,
                "schedule_mode": "inclusive",
                "schedule_start": "06:00:00",
                "schedule_end": "12:00:00",
                "schedule_days": '["mon","tue","wed","thu","fri"]',
                "schedule_timezone": "Asia/Jakarta"
            }
        }


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    schedule_mode: Optional[str] = None
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None
    schedule_days: Optional[str] = None
    schedule_timezone: Optional[str] = None

    @field_validator("schedule_mode")
    @classmethod
    def validate_schedule_mode(cls, v: Optional[str]) -> Optional[str]:
        """Validate schedule mode if provided."""
        if v:
            if v.lower() not in ["inclusive", "exclusive"]:
                raise ValueError("schedule_mode must be 'inclusive' or 'exclusive'")
            return v.lower()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Playlist Name",
                "is_active": True,
                "priority": 7
            }
        }


class PlaylistContentAdd(BaseModel):
    """Schema for adding content to playlist."""

    content_id: int = Field(..., description="Content ID to add")
    order_index: Optional[int] = Field(None, ge=0, description="Order in playlist (auto if not provided)")
    duration: Optional[int] = Field(None, ge=1, description="Duration in seconds (uses content default if not provided)")

    class Config:
        json_schema_extra = {
            "example": {
                "content_id": 42,
                "order_index": 5,
                "duration": 15
            }
        }


class PlaylistContentReorder(BaseModel):
    """Schema for reordering content in playlist."""

    content_orders: List[Dict[str, int]] = Field(
        ...,
        description='List of {"content_id": X, "order_index": Y}'
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content_orders": [
                    {"content_id": 5, "order_index": 1},
                    {"content_id": 3, "order_index": 2},
                    {"content_id": 7, "order_index": 3}
                ]
            }
        }


class PlaylistAssignDevice(BaseModel):
    """Schema for assigning playlist to device."""

    device_id: int = Field(..., description="Device ID to assign")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 123
            }
        }


class PlaylistDuplicate(BaseModel):
    """Schema for duplicating a playlist."""

    new_name: str = Field(..., min_length=1, max_length=100, description="Name for the new playlist")
    copy_assignments: bool = Field(False, description="Whether to copy device assignments")

    class Config:
        json_schema_extra = {
            "example": {
                "new_name": "Morning Promotions (Copy)",
                "copy_assignments": True
            }
        }


# ==================== Response Schemas ====================

class PlaylistContentItem(BaseModel):
    """Content item within a playlist with metadata."""

    content_id: int
    content_title: str
    content_type: str
    order_index: int
    duration: Optional[int] = None
    file_url: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "content_id": 42,
                "content_title": "Summer Sale Video",
                "content_type": "video",
                "order_index": 1,
                "duration": 15,
                "file_url": "http://192.168.5.12:8000/api/v1/assets/123/file.mp4"
            }
        }


class PlaylistBase(BaseModel):
    """Base playlist response schema."""

    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    priority: int
    schedule_mode: Optional[str] = None
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None
    schedule_days: Optional[str] = None
    schedule_timezone: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Morning Promotions",
                "description": "Promotional content for morning hours",
                "is_active": True,
                "priority": 5,
                "schedule_mode": "inclusive",
                "schedule_start": "06:00:00",
                "schedule_end": "12:00:00",
                "schedule_days": '["mon","tue","wed","thu","fri"]',
                "schedule_timezone": "Asia/Jakarta",
                "created_at": "2025-10-30T10:00:00Z",
                "updated_at": "2025-10-30T14:30:00Z"
            }
        }


class PlaylistResponse(PlaylistBase):
    """Standard playlist response."""

    content_count: Optional[int] = Field(None, description="Number of content items")
    total_duration: Optional[int] = Field(None, description="Total duration in seconds")
    device_count: Optional[int] = Field(None, description="Number of assigned devices")


class PlaylistDetailResponse(PlaylistBase):
    """Detailed playlist response with content items."""

    contents: List[PlaylistContentItem] = Field(default_factory=list)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Morning Promotions",
                "description": "Promotional content for morning hours",
                "is_active": True,
                "priority": 5,
                "created_at": "2025-10-30T10:00:00Z",
                "contents": [
                    {
                        "content_id": 42,
                        "content_title": "Summer Sale Video",
                        "content_type": "video",
                        "order_index": 1,
                        "duration": 15
                    }
                ]
            }
        }


class PlaylistListResponse(BaseModel):
    """Response for list playlists endpoint."""

    playlists: List[PlaylistResponse]
    total: int
    skip: int
    limit: int

    class Config:
        json_schema_extra = {
            "example": {
                "playlists": [
                    {
                        "id": 1,
                        "name": "Morning Promotions",
                        "is_active": True,
                        "priority": 5,
                        "content_count": 10,
                        "device_count": 5,
                        "created_at": "2025-10-30T10:00:00Z"
                    }
                ],
                "total": 25,
                "skip": 0,
                "limit": 20
            }
        }


class PlaylistStatsResponse(BaseModel):
    """Playlist statistics response."""

    total_contents: int
    total_duration: int
    device_count: int
    content_types: Dict[str, int] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "total_contents": 10,
                "total_duration": 300,
                "device_count": 5,
                "content_types": {
                    "video": 5,
                    "image": 3,
                    "web": 2
                }
            }
        }


class PlaylistContentAddResponse(BaseModel):
    """Response for adding content to playlist."""

    message: str = "Content added to playlist"
    playlist_id: int
    content_id: int
    order_index: int
    duration: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Content added to playlist",
                "playlist_id": 1,
                "content_id": 42,
                "order_index": 5,
                "duration": 15
            }
        }


class PlaylistAssignmentResponse(BaseModel):
    """Response for playlist assignment operations."""

    message: str
    playlist_id: int
    device_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Playlist assigned to device",
                "playlist_id": 1,
                "device_id": 123
            }
        }


class DevicePlaylistResponse(BaseModel):
    """Response for device's assigned playlists."""

    device_id: int
    playlists: List[PlaylistResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 123,
                "playlists": [
                    {
                        "id": 1,
                        "name": "Morning Promotions",
                        "priority": 5,
                        "is_active": True
                    }
                ],
                "total": 3
            }
        }
