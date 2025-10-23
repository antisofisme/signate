"""
Content schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ContentBase(BaseModel):
    """Base content schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class ContentUploadResponse(BaseModel):
    """Response schema for content upload"""
    id: int
    title: str
    description: Optional[str]
    content_type: str
    anthias_url: str
    anthias_asset_id: str
    duration: int
    is_active: bool
    file_size: Optional[int]
    mime_type: Optional[str]
    resolution: Optional[str]
    width: Optional[int]
    height: Optional[int]
    codec: Optional[str]
    fps: Optional[float]
    bitrate: Optional[int]
    video_duration: Optional[float]
    audio_codec: Optional[str]
    audio_bitrate: Optional[int]
    audio_sample_rate: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Banner Promo",
                "description": "Promo banner for lobby",
                "content_type": "image",
                "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc123.jpg",
                "anthias_asset_id": "abc123",
                "duration": 10,
                "is_active": True,
                "file_size": 1024000,
                "mime_type": "image/jpeg",
                "resolution": "1920x1080",
                "width": 1920,
                "height": 1080,
                "codec": "jpeg",
                "fps": None,
                "bitrate": None,
                "video_duration": None,
                "audio_codec": None,
                "audio_bitrate": None,
                "audio_sample_rate": None,
                "created_at": "2025-10-21T12:00:00"
            }
        }


class ContentResponse(BaseModel):
    """Response schema for content"""
    id: int
    title: str
    description: Optional[str]
    content_type: str
    anthias_url: str
    anthias_asset_id: Optional[str]
    duration: int
    is_active: bool
    file_size: Optional[int]
    mime_type: Optional[str]
    resolution: Optional[str]
    width: Optional[int]
    height: Optional[int]
    codec: Optional[str]
    fps: Optional[float]
    bitrate: Optional[int]
    video_duration: Optional[float]
    audio_codec: Optional[str]
    audio_bitrate: Optional[int]
    audio_sample_rate: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Banner Promo",
                "description": "Promo banner for lobby",
                "content_type": "image",
                "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc123.jpg",
                "anthias_asset_id": "abc123",
                "duration": 10,
                "is_active": True,
                "file_size": 1024000,
                "mime_type": "image/jpeg",
                "resolution": "1920x1080",
                "width": 1920,
                "height": 1080,
                "codec": "jpeg",
                "fps": None,
                "bitrate": None,
                "video_duration": None,
                "audio_codec": None,
                "audio_bitrate": None,
                "audio_sample_rate": None,
                "created_at": "2025-10-21T12:00:00",
                "updated_at": "2025-10-21T12:00:00"
            }
        }


class ContentListResponse(BaseModel):
    """Response schema for content list"""
    total: int
    items: List[ContentResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {
                        "id": 1,
                        "title": "Banner Promo",
                        "content_type": "image",
                        "duration": 10
                    }
                ]
            }
        }


class ContentUpdateRequest(BaseModel):
    """Request schema for updating content"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    duration: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Banner",
                "description": "Updated description",
                "duration": 15,
                "is_active": True
            }
        }


class ContentAssignRequest(BaseModel):
    """Request schema for assigning content to device/tag"""
    device_id: Optional[int] = None
    tag_id: Optional[int] = None
    priority: int = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "tag_id": None,
                "priority": 10
            }
        }


class ContentAssignmentResponse(BaseModel):
    """Response schema for content assignment"""
    id: int
    content_id: int
    device_id: Optional[int]
    tag_id: Optional[int]
    priority: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "content_id": 1,
                "device_id": 1,
                "tag_id": None,
                "priority": 10,
                "created_at": "2025-10-21T12:00:00"
            }
        }
