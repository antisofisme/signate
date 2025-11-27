"""
Content Domain Entity
Business logic for content management
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class Content:
    """Content domain entity - Pure business logic"""

    # REQUIRED FIELDS (no defaults - must come first in dataclass)
    id: Optional[int]
    title: str
    content_type: str  # 'image', 'video', 'audio'

    # Storage fields (custom system)
    file_path: str
    file_url: str
    storage_key: str
    file_hash: str
    file_size: int

    # Display settings
    duration: int
    is_active: bool

    # File metadata
    mime_type: str
    original_filename: str
    file_extension: str

    # Multi-tenant (must be before optional fields!)
    organization_id: int
    uploaded_by_id: int  # 🐛 FIX: Match database column name

    # OPTIONAL FIELDS WITH DEFAULTS (must come after required fields)
    description: Optional[str] = None

    # Media properties
    resolution: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    codec: Optional[str] = None
    fps: Optional[float] = None
    bitrate: Optional[int] = None

    # Video/Audio specific
    media_duration: Optional[float] = None
    video_start_time: float = 0.0
    video_end_time: Optional[float] = None
    audio_codec: Optional[str] = None
    audio_bitrate: Optional[int] = None
    audio_sample_rate: Optional[int] = None
    audio_channels: int = 2

    # Transcoding (HLS for video)
    transcoding_status: str = "pending"  # pending/processing/completed/failed
    transcoding_job_id: Optional[str] = None
    transcoding_progress: int = 0
    transcoding_error: Optional[str] = None
    hls_master_playlist_path: Optional[str] = None
    hls_master_playlist_url: Optional[str] = None
    hls_variants: Optional[Dict[str, Any]] = None

    # Thumbnail
    thumbnail_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    thumbnail_generated_at: Optional[datetime] = None

    # Upload status
    upload_status: str = "pending"  # pending/processing/completed/failed

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Audit trail fields
    updated_by_id: Optional[int] = None
    deleted_by_id: Optional[int] = None

    # Valid types
    VALID_TYPES = ['image', 'video', 'audio']

    def __post_init__(self):
        """Validate business rules"""
        # Title validation
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Title is required")

        if len(self.title) > 200:
            raise ValueError("Title must be <= 200 characters")

        # Content type validation
        if self.content_type not in self.VALID_TYPES:
            raise ValueError(
                f"Content type must be one of: {', '.join(self.VALID_TYPES)}"
            )

        # Duration validation
        if self.duration < 1:
            raise ValueError("Duration must be at least 1 second")

        if self.duration > 86400:  # 24 hours
            raise ValueError("Duration must be <= 24 hours")

        # File size validation
        if self.file_size < 0:
            raise ValueError("File size cannot be negative")

        # Description length
        if self.description and len(self.description) > 1000:
            raise ValueError("Description must be <= 1000 characters")

    def is_image(self) -> bool:
        """Check if content is an image"""
        return self.content_type == 'image'

    def is_video(self) -> bool:
        """Check if content is a video"""
        return self.content_type == 'video'

    def is_audio(self) -> bool:
        """Check if content is audio"""
        return self.content_type == 'audio'

    def is_deleted(self) -> bool:
        """Check if content is soft-deleted"""
        return self.deleted_at is not None

    def is_transcoding_needed(self) -> bool:
        """Check if transcoding is needed (video content)"""
        return self.is_video() and self.transcoding_status in ['pending', 'failed']

    def is_transcoding_complete(self) -> bool:
        """Check if transcoding is complete"""
        return self.transcoding_status == 'completed'

    def has_thumbnail(self) -> bool:
        """Check if thumbnail is available"""
        return self.thumbnail_url is not None

    def get_display_url(self) -> str:
        """Get URL for display (HLS for video, original for others)"""
        if self.is_video() and self.is_transcoding_complete() and self.hls_master_playlist_url:
            return self.hls_master_playlist_url
        return self.file_url

    def get_file_size_readable(self) -> str:
        """Get human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def mark_upload_completed(self):
        """Mark upload as completed"""
        self.upload_status = 'completed'

    def mark_transcoding_started(self, job_id: str):
        """Mark transcoding as started"""
        self.transcoding_status = 'processing'
        self.transcoding_job_id = job_id
        self.transcoding_progress = 0

    def update_transcoding_progress(self, progress: int):
        """Update transcoding progress"""
        if 0 <= progress <= 100:
            self.transcoding_progress = progress

    def mark_transcoding_completed(self, hls_path: str, hls_url: str, variants: Dict[str, Any]):
        """Mark transcoding as completed"""
        self.transcoding_status = 'completed'
        self.transcoding_progress = 100
        self.hls_master_playlist_path = hls_path
        self.hls_master_playlist_url = hls_url
        self.hls_variants = variants

    def mark_transcoding_failed(self, error: str):
        """Mark transcoding as failed"""
        self.transcoding_status = 'failed'
        self.transcoding_error = error

    def set_thumbnail(self, thumbnail_path: str, thumbnail_url: str):
        """Set thumbnail information"""
        self.thumbnail_path = thumbnail_path
        self.thumbnail_url = thumbnail_url
        self.thumbnail_generated_at = datetime.now(timezone.utc)

    def soft_delete(self, deleted_by_id: Optional[int] = None):
        """Mark content as soft-deleted with audit trail"""
        self.deleted_at = datetime.now(timezone.utc)
        self.is_active = False
        if deleted_by_id is not None:
            self.deleted_by_id = deleted_by_id
