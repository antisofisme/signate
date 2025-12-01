"""
Tag DTOs (Data Transfer Objects)
Request/Response models for API layer
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# =============================================================================
# REQUEST DTOs
# =============================================================================

class CreateTagRequest(BaseModel):
    """Create tag request"""
    tag_name: str = Field(..., min_length=1, max_length=100, description="Tag name (unique within organization)")
    description: Optional[str] = Field(None, max_length=500, description="Optional tag description")
    color: str = Field(default="#3B82F6", pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", description="Hex color code")


class UpdateTagRequest(BaseModel):
    """Update tag request - all fields optional"""
    tag_name: Optional[str] = Field(None, min_length=1, max_length=100, description="New tag name")
    description: Optional[str] = Field(None, max_length=500, description="New description")
    color: Optional[str] = Field(None, pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", description="New color")


class ListTagsQuery(BaseModel):
    """Query parameters for listing tags"""
    sort_by: str = Field(default="newest", description="Sort order: newest, oldest, name_asc, name_desc")

    class Config:
        use_enum_values = True


class AssignTagRequest(BaseModel):
    """Assign tag to single content request"""
    content_id: int = Field(..., description="Content ID to assign tag to")


class AssignTagToContentsRequest(BaseModel):
    """Bulk assign tag to multiple contents request"""
    content_ids: List[int] = Field(..., min_length=1, description="List of content IDs to assign tag to")


class UnassignTagRequest(BaseModel):
    """Unassign tag from single content request"""
    content_id: int = Field(..., description="Content ID to unassign tag from")


class UnassignTagFromContentsRequest(BaseModel):
    """Bulk unassign tag from multiple contents request"""
    content_ids: List[int] = Field(..., min_length=1, description="List of content IDs to unassign tag from")


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class TagResponse(BaseModel):
    """Tag response"""
    id: int
    tag_name: str
    description: Optional[str]
    color: str
    organization_id: int
    created_at: datetime
    # Usage counts (computed)
    device_count: int = Field(default=0, description="Number of devices using this tag")
    content_count: int = Field(default=0, description="Number of content items using this tag")

    class Config:
        from_attributes = True


class TagUsageResponse(BaseModel):
    """Tag usage statistics"""
    device_count: int = Field(default=0, description="Number of devices using this tag")
    content_count: int = Field(default=0, description="Number of content items using this tag")


class TagWithUsageResponse(BaseModel):
    """Tag with usage statistics"""
    tag: TagResponse
    usage: TagUsageResponse


class TagListResponse(BaseModel):
    """List of tags response"""
    success: bool = True
    data: List[TagResponse]
    total: int


class TagDetailResponse(BaseModel):
    """Single tag response"""
    success: bool = True
    data: TagResponse


class TagWithUsageDetailResponse(BaseModel):
    """Single tag with usage response"""
    success: bool = True
    data: TagWithUsageResponse


class TagDeleteResponse(BaseModel):
    """Tag deletion response"""
    success: bool = True
    message: str


class TagAssignmentResponse(BaseModel):
    """Tag assignment response"""
    success: bool
    message: str


class BulkTagAssignmentResponse(BaseModel):
    """Bulk tag assignment response"""
    success: bool = True
    assigned: int
    skipped: int
    failed: int
    message: str


class BulkTagUnassignmentResponse(BaseModel):
    """Bulk tag unassignment response"""
    success: bool = True
    unassigned: int
    not_found: int
    message: str


class ContentTagsResponse(BaseModel):
    """Content tags list response"""
    success: bool = True
    data: List[TagResponse]
    total: int


# =============================================================================
# DEVICE-TAG DTOs
# =============================================================================

class DeviceTagResponse(BaseModel):
    """Device info for tag context"""
    id: int
    device_name: str
    device_type: str
    status: str
    assigned_at: datetime

    class Config:
        from_attributes = True


class DeviceTagsListResponse(BaseModel):
    """List of devices assigned to a tag"""
    success: bool = True
    data: List[DeviceTagResponse]
    total: int


class AssignTagToDevicesRequest(BaseModel):
    """Bulk assign tag to multiple devices request"""
    device_ids: List[int] = Field(..., min_length=1, description="List of device IDs to assign tag to")


class UnassignTagFromDevicesRequest(BaseModel):
    """Bulk unassign tag from multiple devices request"""
    device_ids: List[int] = Field(..., min_length=1, description="List of device IDs to unassign tag from")


class BulkDeviceTagAssignmentResponse(BaseModel):
    """Bulk device-tag assignment response"""
    success: bool = True
    assigned: int
    skipped: int
    failed: int
    message: str


class BulkDeviceTagUnassignmentResponse(BaseModel):
    """Bulk device-tag unassignment response"""
    success: bool = True
    unassigned: int
    not_found: int
    message: str
