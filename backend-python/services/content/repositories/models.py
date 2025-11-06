"""
SQLAlchemy Models for Content
Database representation
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, BigInteger, ForeignKey, JSON, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base


class ContentModel(Base):
    """Content database model"""
    __tablename__ = "contents"

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String(20), nullable=False)  # 'image', 'video', 'audio'

    # File Storage (Custom System)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    storage_key = Column(String(255), nullable=False, unique=True, index=True)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA256

    # Display Settings
    duration = Column(Integer, default=10, nullable=False)  # seconds
    is_active = Column(Boolean, default=True, nullable=False)

    # File Metadata
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_extension = Column(String(20), nullable=False)

    # Media Properties
    resolution = Column(String(50), nullable=True)  # "1920x1080"
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    codec = Column(String(50), nullable=True)
    fps = Column(Float, nullable=True)
    bitrate = Column(Integer, nullable=True)  # kbps

    # Video/Audio Specific
    media_duration = Column(Float, nullable=True)  # actual media length
    video_start_time = Column(Float, default=0.0, nullable=False)
    video_end_time = Column(Float, nullable=True)
    audio_codec = Column(String(50), nullable=True)
    audio_bitrate = Column(Integer, nullable=True)
    audio_sample_rate = Column(Integer, nullable=True)
    audio_channels = Column(Integer, default=2, nullable=False)

    # Transcoding (HLS for video)
    transcoding_status = Column(String(50), default="pending", nullable=False)  # pending/processing/completed/failed
    transcoding_job_id = Column(String(200), nullable=True)
    transcoding_progress = Column(Integer, default=0, nullable=False)  # 0-100%
    transcoding_error = Column(Text, nullable=True)
    hls_master_playlist_path = Column(String(500), nullable=True)
    hls_master_playlist_url = Column(String(500), nullable=True)
    hls_variants = Column(JSON, nullable=True)

    # Thumbnail
    thumbnail_path = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    thumbnail_generated_at = Column(DateTime(timezone=True), nullable=True)

    # Upload Status
    upload_status = Column(String(20), default="pending", nullable=False)  # pending/processing/completed/failed

    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    # organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    # user = relationship("UserModel", foreign_keys=[uploaded_by])

    # Composite indexes
    __table_args__ = (
        Index('idx_content_org_active', 'organization_id', 'is_active'),
        Index('idx_content_org_type', 'organization_id', 'content_type'),
        Index('idx_content_org_created', 'organization_id', 'created_at'),
        Index('idx_content_hash_org', 'file_hash', 'organization_id'),  # for deduplication
    )
