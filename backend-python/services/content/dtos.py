"""
Content DTOs (Data Transfer Objects)
Request/Response models for API
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ContentUploadRequest(BaseModel):
    """Upload content request (from form data)"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    duration: int = Field(10, ge=1, le=86400)
    is_active: bool = True


class ContentUpdateRequest(BaseModel):
    """Update content metadata request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    duration: Optional[int] = Field(None, ge=1, le=86400)
    is_active: Optional[bool] = None


class BulkDeleteRequest(BaseModel):
    """Bulk delete content request"""
    content_ids: List[int] = Field(..., min_items=1, max_items=100)


class BulkUpdateRequest(BaseModel):
    """Bulk update content request"""
    content_ids: List[int] = Field(..., min_items=1, max_items=100)
    updates: ContentUpdateRequest


class ContentResponse(BaseModel):
    """Content response"""
    id: int
    title: str
    description: Optional[str]
    content_type: str

    # URLs
    file_url: str
    thumbnail_url: Optional[str]
    hls_master_playlist_url: Optional[str]

    # Settings
    duration: int
    is_active: bool

    # File metadata
    file_size: int
    mime_type: str
    original_filename: str
    resolution: Optional[str]

    # Transcoding status
    transcoding_status: str
    transcoding_progress: int
    upload_status: str

    # Multi-tenant
    organization_id: int
    uploaded_by: Optional[int]

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

    @staticmethod
    def from_entity(content) -> "ContentResponse":
        """Convert domain entity to response DTO"""
        return ContentResponse(
            id=content.id,
            title=content.title,
            description=content.description,
            content_type=content.content_type,
            file_url=content.file_url,
            thumbnail_url=content.thumbnail_url,
            hls_master_playlist_url=content.hls_master_playlist_url,
            duration=content.duration,
            is_active=content.is_active,
            file_size=content.file_size,
            mime_type=content.mime_type,
            original_filename=content.original_filename,
            resolution=content.resolution,
            transcoding_status=content.transcoding_status,
            transcoding_progress=content.transcoding_progress,
            upload_status=content.upload_status,
            organization_id=content.organization_id,
            uploaded_by_id=content.uploaded_by_id,
            created_at=content.created_at,
            updated_at=content.updated_at
        )


class ContentStatsResponse(BaseModel):
    """Storage statistics response"""
    total_files: int
    total_size_bytes: int
    total_size_readable: str
    by_type: Dict[str, Dict[str, Any]]


class PaginatedContentResponse(BaseModel):
    """Paginated content list response"""
    data: list[ContentResponse]
    total: int
    skip: int
    limit: int
