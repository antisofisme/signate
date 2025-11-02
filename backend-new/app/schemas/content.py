"""
Content Schemas
===============

Pydantic schemas for content API requests and responses.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ==================== Request Schemas ====================

class ContentUploadMetadata(BaseModel):
    """Metadata for content upload."""

    title: Optional[str] = Field(None, max_length=200, description="Content title")
    description: Optional[str] = Field(None, max_length=1000, description="Content description")
    content_type: str = Field(..., description="Content type: video, image, or web")
    tags: Optional[List[str]] = Field(None, max_items=10, description="Tags for content")
    check_quota: bool = Field(True, description="Check storage quota before upload")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type."""
        allowed_types = ["video", "image", "web"]
        if v.lower() not in allowed_types:
            raise ValueError(f"content_type must be one of: {', '.join(allowed_types)}")
        return v.lower()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags."""
        if v is not None:
            # Remove empty tags and trim
            v = [tag.strip() for tag in v if tag.strip()]
            # Check for duplicates
            if len(v) != len(set(v)):
                raise ValueError("Tags must be unique")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Product Showcase Video",
                "description": "New product line showcase for Q1 2025",
                "content_type": "video",
                "tags": ["product", "showcase", "2025"],
                "check_quota": True
            }
        }


class ContentUpdate(BaseModel):
    """Schema for updating content."""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_items=10)
    is_active: Optional[bool] = None
    display_duration: Optional[int] = Field(None, ge=1, le=3600, description="Duration in seconds")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags."""
        if v is not None:
            v = [tag.strip() for tag in v if tag.strip()]
            if len(v) != len(set(v)):
                raise ValueError("Tags must be unique")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Title",
                "description": "Updated description",
                "tags": ["updated", "2025"],
                "display_duration": 15
            }
        }


# ==================== Response Schemas ====================

class ContentBase(BaseModel):
    """Base content response schema."""

    id: int
    organization_id: int
    title: str
    description: Optional[str] = None
    content_type: str
    mime_type: str
    file_size: int
    file_size_mb: float
    anthias_asset_id: Optional[str] = None
    anthias_url: Optional[str] = None
    display_duration: int
    tags: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    @property
    def file_url(self) -> Optional[str]:
        """Get file URL."""
        return self.anthias_url

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "title": "Product Showcase Video",
                "description": "New product line showcase for Q1 2025",
                "content_type": "video",
                "mime_type": "video/mp4",
                "file_size": 52428800,
                "file_size_mb": 50.0,
                "anthias_asset_id": "asset-uuid-here",
                "anthias_url": "http://192.168.5.12:8000/api/storage/serve/asset-uuid-here",
                "display_duration": 15,
                "tags": ["product", "showcase", "2025"],
                "is_active": True,
                "created_at": "2025-10-30T10:00:00Z",
                "updated_at": "2025-10-30T14:30:00Z"
            }
        }


class ContentResponse(ContentBase):
    """Standard content response."""
    pass


class ContentUploadResponse(ContentBase):
    """Response for successful upload."""

    upload_info: dict = Field(default_factory=dict, description="Additional upload information")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "title": "Product Showcase Video",
                "content_type": "video",
                "mime_type": "video/mp4",
                "file_size": 52428800,
                "file_size_mb": 50.0,
                "anthias_asset_id": "asset-uuid-here",
                "anthias_url": "http://192.168.5.12:8000/api/storage/serve/asset-uuid-here",
                "display_duration": 15,
                "is_active": True,
                "created_at": "2025-10-30T10:00:00Z",
                "upload_info": {
                    "storage_service": "anthias",
                    "md5": "abc123def456",
                    "processing_status": "completed"
                }
            }
        }


class ContentListResponse(BaseModel):
    """Response for list contents endpoint."""

    contents: List[ContentResponse]
    total: int
    skip: int
    limit: int
    filters: dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "contents": [
                    {
                        "id": 1,
                        "organization_id": 1,
                        "title": "Product Video",
                        "content_type": "video",
                        "mime_type": "video/mp4",
                        "file_size": 52428800,
                        "file_size_mb": 50.0,
                        "is_active": True,
                        "created_at": "2025-10-30T10:00:00Z"
                    }
                ],
                "total": 150,
                "skip": 0,
                "limit": 20,
                "filters": {"content_type": "video"}
            }
        }


class ContentStatsResponse(BaseModel):
    """Content statistics by type."""

    organization_id: int
    total_content: int
    total_size_bytes: int
    total_size_gb: float
    by_type: dict = Field(default_factory=dict, description="Count by content type")
    by_mime_type: dict = Field(default_factory=dict, description="Count by MIME type")
    active_count: int
    inactive_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "total_content": 150,
                "total_size_bytes": 75000000000,
                "total_size_gb": 69.85,
                "by_type": {
                    "video": 80,
                    "image": 60,
                    "web": 10
                },
                "by_mime_type": {
                    "video/mp4": 70,
                    "video/webm": 10,
                    "image/jpeg": 40,
                    "image/png": 20
                },
                "active_count": 145,
                "inactive_count": 5
            }
        }


class StorageUsageResponse(BaseModel):
    """Storage usage statistics."""

    organization_id: int
    total_size_bytes: int
    total_size_gb: float
    max_storage_gb: int
    available_gb: float
    usage_percentage: float
    content_count: int
    largest_files: Optional[List[dict]] = Field(None, description="Top 5 largest files")

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "total_size_bytes": 75000000000,
                "total_size_gb": 69.85,
                "max_storage_gb": 100,
                "available_gb": 30.15,
                "usage_percentage": 69.85,
                "content_count": 150,
                "largest_files": [
                    {
                        "id": 1,
                        "title": "Product Video",
                        "file_size_mb": 450.5,
                        "content_type": "video"
                    }
                ]
            }
        }


class ContentFileServeResponse(BaseModel):
    """Response for file serve endpoint (redirect)."""

    url: str = Field(..., description="Direct URL to file")
    expires_at: Optional[datetime] = Field(None, description="URL expiration time")
    content_type: str
    file_size: int

    class Config:
        json_schema_extra = {
            "example": {
                "url": "http://192.168.5.12:8000/api/storage/serve/asset-uuid-here",
                "expires_at": None,
                "content_type": "video/mp4",
                "file_size": 52428800
            }
        }
