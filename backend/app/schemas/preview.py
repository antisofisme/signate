"""
Preview schemas for device content resolution preview
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContentItemPreview(BaseModel):
    """Schema for individual content item in preview"""
    content_id: int
    title: str
    content_type: str
    anthias_url: str
    duration: int
    priority: int
    display_order: int
    source: str  # 'direct', 'playlist', 'tag'
    source_id: Optional[int] = None  # playlist_id or tag_id
    source_name: Optional[str] = None  # playlist name or tag name
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    # Content metadata
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    resolution: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "content_id": 1,
                "title": "Welcome Banner",
                "content_type": "image",
                "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc123.jpg",
                "duration": 10,
                "priority": 999,
                "display_order": 0,
                "source": "direct",
                "source_id": None,
                "source_name": None,
                "is_active": True,
                "start_date": None,
                "end_date": None,
                "file_size": 1024000,
                "mime_type": "image/jpeg",
                "resolution": "1920x1080"
            }
        }


class ContentSourceBreakdown(BaseModel):
    """Schema for content source breakdown in preview"""
    source_type: str  # 'direct', 'playlist', 'tag'
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    priority: int
    content_count: int
    is_active: bool
    is_scheduled: bool = False
    schedule_info: Optional[Dict[str, Any]] = None
    content_items: List[ContentItemPreview]

    class Config:
        json_schema_extra = {
            "example": {
                "source_type": "playlist",
                "source_id": 1,
                "source_name": "Morning Playlist",
                "priority": 50,
                "content_count": 3,
                "is_active": True,
                "is_scheduled": True,
                "schedule_info": {
                    "mode": "inclusive",
                    "start_time": "06:00:00",
                    "end_time": "12:00:00",
                    "days": ["mon", "tue", "wed", "thu", "fri"],
                    "timezone": "Asia/Jakarta"
                },
                "content_items": []
            }
        }


class ResolutionSummary(BaseModel):
    """Schema for content resolution summary"""
    resolution_mode: str  # 'inclusive' or 'exclusive'
    total_sources: int
    active_sources: int
    total_content_items: int
    final_playlist_size: int
    has_exclusive_playlist: bool
    exclusive_playlist_name: Optional[str] = None
    priority_breakdown: Dict[str, int]  # {source_type: count}

    class Config:
        json_schema_extra = {
            "example": {
                "resolution_mode": "inclusive",
                "total_sources": 3,
                "active_sources": 3,
                "total_content_items": 8,
                "final_playlist_size": 8,
                "has_exclusive_playlist": False,
                "exclusive_playlist_name": None,
                "priority_breakdown": {
                    "direct": 2,
                    "playlist": 4,
                    "tag": 2
                }
            }
        }


class DevicePreviewResponse(BaseModel):
    """Response schema for device content preview"""
    device_id: int
    device_name: str
    device_type: str
    preview_time: datetime
    device_info: Dict[str, Any]
    content_sources: List[ContentSourceBreakdown]
    final_playlist: List[ContentItemPreview]
    resolution_summary: ResolutionSummary

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "device_name": "Lobby TV 1",
                "device_type": "tv",
                "preview_time": "2025-10-26T10:00:00",
                "device_info": {
                    "status": "active",
                    "last_seen": "2025-10-26T09:55:00",
                    "tags": ["lobby", "premium"],
                    "playlists": ["Morning Playlist"],
                    "room_number": "101",
                    "location_type": "guest_room"
                },
                "content_sources": [],
                "final_playlist": [],
                "resolution_summary": {
                    "resolution_mode": "inclusive",
                    "total_sources": 3,
                    "active_sources": 3,
                    "total_content_items": 8,
                    "final_playlist_size": 8,
                    "has_exclusive_playlist": False,
                    "exclusive_playlist_name": None,
                    "priority_breakdown": {
                        "direct": 2,
                        "playlist": 4,
                        "tag": 2
                    }
                }
            }
        }


class PreviewQueryParams(BaseModel):
    """Query parameters for preview request"""
    preview_time: Optional[datetime] = Field(
        None,
        description="Time to preview content for (ISO 8601 format). Defaults to current time."
    )
    include_inactive: bool = Field(
        False,
        description="Include inactive content sources in preview"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "preview_time": "2025-10-26T14:00:00",
                "include_inactive": False
            }
        }
