"""
HLS Transcoding Schemas
Request/response schemas for video transcoding to HLS format
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Literal
from datetime import datetime
from enum import Enum


class TranscodingStatus(str, Enum):
    """Transcoding job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityLevel(str, Enum):
    """Available quality levels for HLS variants"""
    ULTRA_HD = "1080p"  # 1920x1080 @ 5Mbps
    HD = "720p"         # 1280x720 @ 3Mbps
    SD = "480p"         # 854x480 @ 1.5Mbps
    LOW = "360p"        # 640x360 @ 800Kbps


class QualityPreset(BaseModel):
    """
    Quality preset configuration for HLS variant

    Attributes:
        width: Video width in pixels
        height: Video height in pixels
        bitrate: Target bitrate (e.g., "5M", "800k")
        max_bitrate: Maximum bitrate for buffer (e.g., "5.5M", "880k")
        buffer_size: Buffer size for rate control
    """
    width: int = Field(..., gt=0, description="Video width in pixels")
    height: int = Field(..., gt=0, description="Video height in pixels")
    bitrate: str = Field(..., description="Target bitrate (e.g., '5M', '800k')")
    max_bitrate: str = Field(..., description="Maximum bitrate for buffer")
    buffer_size: str = Field(..., description="Buffer size for rate control")

    class Config:
        json_schema_extra = {
            "example": {
                "width": 1920,
                "height": 1080,
                "bitrate": "5M",
                "max_bitrate": "5.5M",
                "buffer_size": "7.5M"
            }
        }


# Predefined quality presets for HLS transcoding
QUALITY_PRESETS: Dict[str, QualityPreset] = {
    "1080p": QualityPreset(
        width=1920,
        height=1080,
        bitrate="5M",
        max_bitrate="5.5M",
        buffer_size="7.5M"
    ),
    "720p": QualityPreset(
        width=1280,
        height=720,
        bitrate="3M",
        max_bitrate="3.3M",
        buffer_size="4.5M"
    ),
    "480p": QualityPreset(
        width=854,
        height=480,
        bitrate="1.5M",
        max_bitrate="1.65M",
        buffer_size="2.25M"
    ),
    "360p": QualityPreset(
        width=640,
        height=360,
        bitrate="800k",
        max_bitrate="880k",
        buffer_size="1.2M"
    ),
}


class TranscodingJobRequest(BaseModel):
    """
    Request schema for creating a transcoding job

    Attributes:
        content_id: ID of content to transcode
        source_path: Absolute path to source video file
        output_dir: Directory for HLS output files
        quality_levels: List of quality levels to generate (default: all)
        segment_duration: HLS segment duration in seconds (default: 6)
        overwrite: Whether to overwrite existing HLS files (default: False)
        priority: Job priority (0-100, higher = more urgent, default: 50)
    """
    content_id: int = Field(..., gt=0, description="ID of content to transcode")
    source_path: str = Field(..., min_length=1, description="Absolute path to source video")
    output_dir: str = Field(..., min_length=1, description="Directory for HLS output")
    quality_levels: Optional[List[QualityLevel]] = Field(
        default=None,
        description="Quality levels to generate (default: all available)"
    )
    segment_duration: int = Field(
        default=6,
        ge=2,
        le=10,
        description="HLS segment duration in seconds"
    )
    overwrite: bool = Field(
        default=False,
        description="Overwrite existing HLS files"
    )
    priority: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Job priority (0-100, higher = more urgent)"
    )

    @field_validator('quality_levels')
    @classmethod
    def validate_quality_levels(cls, v):
        """Ensure at least one quality level if specified"""
        if v is not None and len(v) == 0:
            raise ValueError("At least one quality level must be specified")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "content_id": 1,
                "source_path": "/data/uploads/video123.mp4",
                "output_dir": "/data/hls/1",
                "quality_levels": ["1080p", "720p", "480p", "360p"],
                "segment_duration": 6,
                "overwrite": False,
                "priority": 50
            }
        }


class TranscodingProgress(BaseModel):
    """
    Schema for transcoding progress updates

    Attributes:
        job_id: Unique job identifier
        content_id: ID of content being transcoded
        status: Current transcoding status
        progress: Progress percentage (0-100)
        current_variant: Currently processing quality variant
        completed_variants: List of completed quality variants
        estimated_time_remaining: Estimated seconds until completion
        error_message: Error message if status is FAILED
    """
    job_id: str = Field(..., description="Unique job identifier")
    content_id: int = Field(..., description="Content ID")
    status: TranscodingStatus = Field(..., description="Current status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    current_variant: Optional[str] = Field(None, description="Currently processing variant")
    completed_variants: List[str] = Field(default_factory=list, description="Completed variants")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated seconds remaining")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "transcode_1_20251028_123456",
                "content_id": 1,
                "status": "processing",
                "progress": 45,
                "current_variant": "720p",
                "completed_variants": ["1080p"],
                "estimated_time_remaining": 120,
                "error_message": None,
                "started_at": "2025-10-28T12:34:56",
                "completed_at": None
            }
        }


class HLSVariantInfo(BaseModel):
    """
    Information about a single HLS variant

    Attributes:
        quality: Quality level identifier (e.g., "1080p")
        resolution: Resolution string (e.g., "1920x1080")
        bitrate: Bitrate in kbps
        bandwidth: Bandwidth in bits per second (for master playlist)
        playlist_path: Relative path to variant playlist (.m3u8)
        size_bytes: Total size of variant files in bytes
        segment_count: Number of segments in variant
    """
    quality: str = Field(..., description="Quality level identifier")
    resolution: str = Field(..., description="Resolution (e.g., '1920x1080')")
    bitrate: int = Field(..., description="Bitrate in kbps")
    bandwidth: int = Field(..., description="Bandwidth in bits per second")
    playlist_path: str = Field(..., description="Relative path to variant playlist")
    size_bytes: Optional[int] = Field(None, description="Total size in bytes")
    segment_count: Optional[int] = Field(None, description="Number of segments")

    class Config:
        json_schema_extra = {
            "example": {
                "quality": "1080p",
                "resolution": "1920x1080",
                "bitrate": 5000,
                "bandwidth": 5000000,
                "playlist_path": "1080p.m3u8",
                "size_bytes": 52428800,
                "segment_count": 120
            }
        }


class TranscodingJobResponse(BaseModel):
    """
    Response schema for transcoding job

    Attributes:
        job_id: Unique job identifier
        content_id: ID of content
        status: Current transcoding status
        progress: Progress percentage (0-100)
        master_playlist_path: Absolute path to master playlist
        master_playlist_url: Public URL to master playlist
        variants: List of available HLS variants
        total_size_bytes: Total size of all HLS files
        transcoding_time_seconds: Time taken for transcoding
        error_message: Error message if failed
        created_at: Job creation timestamp
        updated_at: Last update timestamp
    """
    job_id: str = Field(..., description="Unique job identifier")
    content_id: int = Field(..., description="Content ID")
    status: TranscodingStatus = Field(..., description="Current status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    master_playlist_path: Optional[str] = Field(None, description="Absolute path to master.m3u8")
    master_playlist_url: Optional[str] = Field(None, description="Public URL to master.m3u8")
    variants: List[HLSVariantInfo] = Field(default_factory=list, description="Available variants")
    total_size_bytes: Optional[int] = Field(None, description="Total size of HLS files")
    transcoding_time_seconds: Optional[float] = Field(None, description="Transcoding duration")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Job creation time")
    updated_at: datetime = Field(..., description="Last update time")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "transcode_1_20251028_123456",
                "content_id": 1,
                "status": "completed",
                "progress": 100,
                "master_playlist_path": "/data/hls/1/master.m3u8",
                "master_playlist_url": "http://192.168.5.12:8001/hls/1/master.m3u8",
                "variants": [
                    {
                        "quality": "1080p",
                        "resolution": "1920x1080",
                        "bitrate": 5000,
                        "bandwidth": 5000000,
                        "playlist_path": "1080p.m3u8",
                        "size_bytes": 52428800,
                        "segment_count": 120
                    }
                ],
                "total_size_bytes": 157286400,
                "transcoding_time_seconds": 245.7,
                "error_message": None,
                "created_at": "2025-10-28T12:34:56",
                "updated_at": "2025-10-28T12:38:42"
            }
        }


class TranscodingJobListResponse(BaseModel):
    """Response schema for listing transcoding jobs"""
    total: int = Field(..., description="Total number of jobs")
    items: List[TranscodingJobResponse] = Field(..., description="List of jobs")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {
                        "job_id": "transcode_1_20251028_123456",
                        "content_id": 1,
                        "status": "completed",
                        "progress": 100
                    }
                ]
            }
        }


class TranscodingStartRequest(BaseModel):
    """
    Request schema for starting transcoding

    Attributes:
        quality_levels: Optional list of quality levels
        overwrite: Whether to overwrite existing transcoding
        priority: Task priority (0-10)
    """
    quality_levels: Optional[List[str]] = Field(
        None,
        description="Quality levels to generate (1080p, 720p, 480p, 360p)"
    )
    overwrite: bool = Field(
        default=False,
        description="Overwrite existing transcoding"
    )
    priority: int = Field(
        default=5,
        ge=0,
        le=10,
        description="Task priority (0-10, higher = more important)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "quality_levels": ["1080p", "720p", "480p"],
                "overwrite": False,
                "priority": 5
            }
        }


class BatchTranscodingRequest(BaseModel):
    """
    Request schema for batch transcoding

    Attributes:
        content_ids: List of content IDs to transcode
        quality_levels: Optional list of quality levels
        priority: Task priority
    """
    content_ids: List[int] = Field(
        ...,
        description="List of content IDs to transcode",
        min_length=1
    )
    quality_levels: Optional[List[str]] = Field(
        None,
        description="Quality levels to generate"
    )
    priority: int = Field(
        default=5,
        ge=0,
        le=10,
        description="Task priority"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content_ids": [1, 2, 3],
                "quality_levels": ["1080p", "720p"],
                "priority": 7
            }
        }


class TranscodingQueueStatus(BaseModel):
    """
    Queue status response schema

    Attributes:
        queues: Statistics per queue
        total_active: Total active tasks across all queues
        total_reserved: Total reserved tasks
        total_scheduled: Total scheduled tasks
    """
    queues: Dict[str, Dict[str, int]] = Field(
        ...,
        description="Statistics per queue"
    )
    total_active: int = Field(..., description="Total active tasks")
    total_reserved: int = Field(..., description="Total reserved tasks")
    total_scheduled: int = Field(..., description="Total scheduled tasks")

    class Config:
        json_schema_extra = {
            "example": {
                "queues": {
                    "default": {"active": 0, "reserved": 0, "scheduled": 0},
                    "transcoding": {"active": 2, "reserved": 1, "scheduled": 0},
                    "anthias": {"active": 0, "reserved": 0, "scheduled": 0}
                },
                "total_active": 2,
                "total_reserved": 1,
                "total_scheduled": 0
            }
        }
