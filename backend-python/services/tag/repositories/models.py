"""
SQLAlchemy Models for Tag Service
Maps to existing 'tags' table in database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base


class TagModel(Base):
    """
    Tag SQLAlchemy Model
    Maps to 'tags' table in database (already created by init.sql)
    """
    __tablename__ = "tags"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Tag info
    tag_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#3B82F6", nullable=False)

    # Priority for tag-based playlist resolution
    priority = Column(Integer, default=50, nullable=False)

    # Assigned playlist (for tag-based routing)
    assigned_playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="SET NULL"), nullable=True)

    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships (using string references to avoid circular imports)
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    assigned_playlist = relationship("PlaylistModel", foreign_keys=[assigned_playlist_id])
    devices = relationship("DeviceModel", secondary="device_tags", back_populates="tags")

    def __repr__(self):
        return f"<TagModel(id={self.id}, name='{self.tag_name}', org={self.organization_id})>"


class ContentTag(Base):
    """
    Content-Tag junction table (many-to-many)
    Maps to 'content_tags' table in database
    """
    __tablename__ = "content_tags"

    # Identity
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ContentTag(id={self.id}, content_id={self.content_id}, tag_id={self.tag_id})>"
