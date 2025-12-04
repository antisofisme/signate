"""
SQLAlchemy Models for Content
Database representation
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, BigInteger, ForeignKey, Text, Index, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
from shared.database import Base

# Note: Relationships to OrganizationModel and UserModel are commented out
# to avoid circular import issues. If needed, use lazy loading or back_populates.


class ContentModel(Base):
    """Content database model"""
    __tablename__ = "contents"

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String(20), nullable=False)  # 'image', 'video', 'audio'

    # File Storage (Custom System)
    file_path = Column(String(1000), nullable=False)
    file_url = Column(String(1000), nullable=False)
    storage_key = Column(String(255), nullable=False, unique=True, index=True)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA256

    # Display Settings
    duration = Column(Integer, default=10, nullable=False)  # seconds
    is_active = Column(Boolean, default=True, nullable=False)

    # File Metadata
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(200), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_extension = Column(String(20), nullable=False)

    # Media Properties
    resolution = Column(String(50), nullable=True)  # "1920x1080"
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    codec = Column(String(50), nullable=True)
    fps = Column(Numeric(5, 3), nullable=True)  # Exact precision for frame rates like 23.976
    bitrate = Column(Integer, nullable=True)  # kbps

    # Video/Audio Specific - Using Float which maps to DOUBLE PRECISION in PostgreSQL
    media_duration = Column(Float, nullable=True)  # Actual media length in seconds
    video_start_time = Column(Float, default=0.0, nullable=False)  # Start trim point
    video_end_time = Column(Float, nullable=True)  # End trim point
    audio_codec = Column(String(50), nullable=True)
    audio_bitrate = Column(Integer, nullable=True)
    audio_sample_rate = Column(Integer, nullable=True)
    audio_channels = Column(Integer, default=2, nullable=False)

    # Transcoding (HLS for video)
    transcoding_status = Column(String(50), default="pending", nullable=False)  # pending/processing/completed/failed
    transcoding_job_id = Column(String(200), nullable=True)
    transcoding_progress = Column(Integer, default=0, nullable=False)  # 0-100%
    transcoding_error = Column(Text, nullable=True)
    hls_master_playlist_path = Column(String(1000), nullable=True)
    hls_master_playlist_url = Column(String(1000), nullable=True)
    hls_variants = Column(JSONB, nullable=True)  # JSONB for better query performance

    # Thumbnail
    thumbnail_path = Column(String(1000), nullable=True)
    thumbnail_url = Column(String(1000), nullable=True)
    thumbnail_generated_at = Column(DateTime(timezone=True), nullable=True)

    # Upload Status
    upload_status = Column(String(20), default="pending", nullable=False)  # pending/processing/completed/failed

    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Audit trail
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships - Commented out to avoid circular import issues
    # These can be added back if needed with proper lazy loading configuration
    # organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    # uploader = relationship("UserModel", foreign_keys=[uploaded_by_id])
    # updater = relationship("UserModel", foreign_keys=[updated_by_id])
    # deleter = relationship("UserModel", foreign_keys=[deleted_by_id])

    # Composite indexes
    __table_args__ = (
        Index('idx_content_org_active', 'organization_id', 'is_active'),
        Index('idx_content_org_type', 'organization_id', 'content_type'),
        Index('idx_content_org_created', 'organization_id', 'created_at'),
        Index('idx_content_hash_org', 'file_hash', 'organization_id'),  # for deduplication
    )


class ContentAssignmentModel(Base):
    """
    Content Assignment database model

    For DIRECT device-to-content assignments only.
    Tag-based assignments use content_tags table instead.
    """
    __tablename__ = "content_assignments"

    # Identity
    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant (REQUIRED for all assignments)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Direct device assignment
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Content reference
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Assignment properties
    priority = Column(Integer, default=1, nullable=False)
    schedule = Column(JSONB, nullable=True)  # Optional schedule configuration (JSONB)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_muted = Column(Boolean, default=False, nullable=False)  # Per-content mute control

    # Audit trail
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Composite indexes
    __table_args__ = (
        # Unique constraint: one device can only have one assignment per content per org
        Index('unique_org_device_content', 'organization_id', 'device_id', 'content_id', unique=True, postgresql_where=text('device_id IS NOT NULL')),
        # Performance indexes
        Index('idx_content_assignments_org_device', 'organization_id', 'device_id'),
        Index('idx_content_assignments_org_content', 'organization_id', 'content_id'),
    )
