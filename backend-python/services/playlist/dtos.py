"""
Playlist DTOs (Data Transfer Objects)
Pydantic models for Request/Response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ========== Request DTOs ==========

class PlaylistCreateRequest(BaseModel):
    """Create playlist request"""
    name: str = Field(..., min_length=1, max_length=255, description="Playlist name")
    description: Optional[str] = Field(None, description="Playlist description")
    is_active: bool = Field(True, description="Active status")
    priority: int = Field(0, ge=0, description="Priority (0=lowest)")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Schedule configuration (JSON)")


class PlaylistUpdateRequest(BaseModel):
    """Update playlist request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    schedule: Optional[Dict[str, Any]] = None


class AddContentRequest(BaseModel):
    """Add content to playlist request"""
    content_ids: List[int] = Field(..., min_items=1, description="List of content IDs to add")


class ReorderContentRequest(BaseModel):
    """Reorder playlist content request"""
    content_items: List[Dict[str, Any]] = Field(
        ...,
        min_items=1,
        description="List of {id, order_index, duration?}"
    )


class AssignDevicesRequest(BaseModel):
    """Assign playlist to devices request"""
    device_ids: List[int] = Field(..., min_items=1, description="List of device IDs")


# NOTE: AssignTagsRequest has been removed
# Tags are NOT assigned to Playlists (architecture decision)


class DuplicatePlaylistRequest(BaseModel):
    """Duplicate playlist request"""
    new_name: Optional[str] = Field(None, max_length=255, description="Optional custom name for duplicated playlist")


# ========== Response DTOs ==========

class PlaylistResponse(BaseModel):
    """Playlist response"""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    priority: int
    schedule: Optional[Dict[str, Any]]
    organization_id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    # Computed fields
    content_count: int = 0
    total_duration: int = 0  # in seconds

    class Config:
        from_attributes = True


class PlaylistListResponse(BaseModel):
    """Playlist list response"""
    total: int
    items: List[PlaylistResponse]


class PlaylistContentItemResponse(BaseModel):
    """Playlist content item response"""
    id: int
    playlist_id: int
    content_id: int
    order_index: int
    duration: Optional[int]  # Override duration
    created_at: datetime

    # Optional: enriched with content details
    content_name: Optional[str] = None
    content_type: Optional[str] = None

    class Config:
        from_attributes = True


class PlaylistContentListResponse(BaseModel):
    """Playlist content list response"""
    total: int
    items: List[PlaylistContentItemResponse]


class BulkOperationResponse(BaseModel):
    """Bulk operation response (add/assign)"""
    success: bool = True
    message: str
    added: Optional[int] = None
    assigned: Optional[int] = None
    skipped_missing: Optional[List[int]] = None
    skipped_duplicate: Optional[List[int]] = None


class RemoveOperationResponse(BaseModel):
    """Remove operation response"""
    success: bool = True
    message: str
    removed: Optional[int] = None


class DeviceInfoResponse(BaseModel):
    """Device info response"""
    id: int
    device_name: str
    location: Optional[str]


class PlaylistAssignmentsResponse(BaseModel):
    """Playlist assignments response (devices only)

    NOTE: Tags have been removed from playlist assignments.
    Tags are assigned to Devices and Content only, NOT to Playlists.
    """
    devices: List[DeviceInfoResponse]
