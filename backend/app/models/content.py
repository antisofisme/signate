"""
Content Model
Media content (images, videos) served to devices
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, Boolean, Float
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
        is_active: Whether content is active
        created_at: Timestamp when content was uploaded
        updated_at: Timestamp when content was last updated
    """

    __tablename__ = "content"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Content Info
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_type = Column(String(20), nullable=False)

    # Anthias Integration
    anthias_url = Column(String(500), nullable=False)
    anthias_asset_id = Column(String(100), index=True)

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

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    assignments = relationship("ContentAssignment", back_populates="content", cascade="all, delete-orphan")

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
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
