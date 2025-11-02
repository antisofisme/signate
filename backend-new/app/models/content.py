"""
Content Model
Media content (images, videos) served to devices
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ContentType(str, enum.Enum):
    """Content type enumeration"""
    IMAGE = "image"
    VIDEO = "video"


class Content(Base):
    """
    Content model for media files

    Attributes:
        id: Primary key
        title: Display title of content
        description: Description of content
        content_type: Type of content (image or video)
        anthias_url: URL to content in Anthias system
        anthias_asset_id: Asset ID in Anthias
        anthias_file_uri: Cached file URI from Anthias (e.g., "/data/screenly_assets/abc123.jpg")
        duration: Display duration in seconds
        file_size: File size in bytes
        mime_type: MIME type of file
        resolution: Media resolution (e.g., "1920x1080")
        width: Media width in pixels
        height: Media height in pixels
        codec: Video/image codec name
        fps: Frame rate (video only)
        bitrate: Video bitrate in kbps
        video_duration: Actual video duration in seconds (from metadata)
        video_start_time: Start time for video playback in seconds (video only)
        video_end_time: End time for video playback in seconds (video only, NULL = play to end)
        audio_codec: Audio codec name (video only)
        audio_bitrate: Audio bitrate in kbps (video only)
        audio_sample_rate: Audio sample rate in Hz (video only)
        transcoding_status: Status of transcoding job (pending/processing/completed/failed/cancelled)
        transcoding_job_id: Celery task ID for transcoding job
        transcoding_progress: Transcoding progress percentage (0-100)
        transcoding_error: Error message if transcoding failed
        hls_master_playlist_path: Path to HLS master playlist (master.m3u8)
        hls_variants: JSON array of HLS variant information
        is_active: Whether content is active
        is_template: Whether this content uses template variables
        template_variables: JSON array of variable names used in template
        language_code: ISO language code (en, zh, ja, etc.)
        content_group_id: Groups translations together
        fallback_content_id: Fallback content if template fails
        created_at: Timestamp when content was uploaded
        updated_at: Timestamp when content was last updated
    """

    __tablename__ = "contents"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Content Info
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_type = Column(String(20), nullable=False)

    # Anthias Integration
    anthias_url = Column(String(500), nullable=False)
    anthias_asset_id = Column(String(100), index=True)
    anthias_file_uri = Column(String(500), nullable=True, index=True)  # Cached URI from Anthias (e.g., "/data/screenly_assets/abc123.jpg")

    # Display Settings
    duration = Column(Integer, default=10, nullable=False)  # seconds

    # File Info
    file_size = Column(Integer)  # bytes (bigint in DB)
    mime_type = Column(String(100))

    # Media Metadata (extracted via FFprobe)
    resolution = Column(String(50))  # e.g., "1920x1080"
    width = Column(Integer)  # pixels
    height = Column(Integer)  # pixels
    codec = Column(String(50))  # video/image codec
    fps = Column(Float)  # frame rate (video only)
    bitrate = Column(Integer)  # kbps (video only)
    video_duration = Column(Float)  # seconds (video only, from metadata)
    video_start_time = Column(Float, default=0)  # start time in seconds (video only)
    video_end_time = Column(Float, nullable=True)  # end time in seconds (video only, NULL = play to end)
    audio_codec = Column(String(50))  # audio codec (video only)
    audio_bitrate = Column(Integer)  # kbps (video only)
    audio_sample_rate = Column(Integer)  # Hz (video only)

    # Transcoding Fields (for HLS streaming)
    transcoding_status = Column(String(50), default=None, nullable=True)  # pending/processing/completed/failed/cancelled
    transcoding_job_id = Column(String(200), nullable=True)  # Celery task ID
    transcoding_progress = Column(Integer, default=0, nullable=True)  # 0-100%
    transcoding_error = Column(Text, nullable=True)  # Error message
    hls_master_playlist_path = Column(String(500), nullable=True)  # Path to master.m3u8
    hls_variants = Column(JSON, nullable=True)  # Array of variant info

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Tags (for content categorization and search)
    tags = Column(JSON, nullable=True)  # JSON array of tag strings, e.g., ["product", "2025", "showcase"]

    # Template & Multi-language fields (Phase 0 enhancement)
    is_template = Column(Boolean, default=False, nullable=True)  # Whether content uses templates
    template_variables = Column(JSON, nullable=True)  # JSON array of variable names
    language_code = Column(String(10), nullable=True)  # ISO language code (en, zh, ja, etc.)
    content_group_id = Column(Integer, nullable=True)  # Groups translations together
    fallback_content_id = Column(Integer, ForeignKey("contents.id", ondelete="SET NULL"), nullable=True)  # Fallback content

    # Multi-tenancy fields
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    assignments = relationship("ContentAssignment", back_populates="content", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="content")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title}', type='{self.content_type}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content_type": self.content_type,
            "anthias_url": self.anthias_url,
            "anthias_asset_id": self.anthias_asset_id,
            "anthias_file_uri": self.anthias_file_uri,
            "duration": self.duration,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "resolution": self.resolution,
            "width": self.width,
            "height": self.height,
            "codec": self.codec,
            "fps": self.fps,
            "bitrate": self.bitrate,
            "video_duration": self.video_duration,
            "video_start_time": self.video_start_time,
            "video_end_time": self.video_end_time,
            "audio_codec": self.audio_codec,
            "audio_bitrate": self.audio_bitrate,
            "audio_sample_rate": self.audio_sample_rate,
            # Transcoding fields
            "transcoding_status": self.transcoding_status,
            "transcoding_job_id": self.transcoding_job_id,
            "transcoding_progress": self.transcoding_progress,
            "transcoding_error": self.transcoding_error,
            "hls_master_playlist_path": self.hls_master_playlist_path,
            "hls_variants": self.hls_variants,
            "is_active": self.is_active,
            # Tags
            "tags": self.tags,
            # Template & Multi-language fields
            "is_template": self.is_template,
            "template_variables": self.template_variables,
            "language_code": self.language_code,
            "content_group_id": self.content_group_id,
            "fallback_content_id": self.fallback_content_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
