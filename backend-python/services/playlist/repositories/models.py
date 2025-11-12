"""
Playlist SQLAlchemy Models
Maps to playlist tables in database
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from shared.database import Base


class PlaylistModel(Base):
    """Playlist SQLAlchemy model"""
    __tablename__ = "playlists"
    __table_args__ = {'extend_existing': True}

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    schedule = Column(JSON, nullable=True)  # JSONB in PostgreSQL
    is_default = Column(Boolean, default=False, nullable=False)
    is_pms_template = Column(Boolean, default=False, nullable=False)

    # Multi-tenancy & User tracking
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    contents = relationship("PlaylistContentModel", back_populates="playlist", cascade="all, delete-orphan")
    assignments = relationship("PlaylistAssignmentModel", back_populates="playlist", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PlaylistModel(id={self.id}, name='{self.name}', org={self.organization_id})>"


class PlaylistContentModel(Base):
    """Playlist content junction model"""
    __tablename__ = "playlist_contents"
    __table_args__ = {'extend_existing': True}

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Order and duration
    order_index = Column(Integer, default=0, nullable=False)
    duration = Column(Integer, nullable=True)  # Override content duration

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    playlist = relationship("PlaylistModel", back_populates="contents")

    def __repr__(self):
        return f"<PlaylistContentModel(id={self.id}, playlist={self.playlist_id}, content={self.content_id})>"


class PlaylistAssignmentModel(Base):
    """Playlist assignment model (polymorphic: device OR tag)"""
    __tablename__ = "playlist_assignments"
    __table_args__ = {'extend_existing': True}

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)

    # Polymorphic assignment (device OR tag)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=True, index=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    playlist = relationship("PlaylistModel", back_populates="assignments")

    def __repr__(self):
        target = f"device={self.device_id}" if self.device_id else f"tag={self.tag_id}"
        return f"<PlaylistAssignmentModel(id={self.id}, playlist={self.playlist_id}, {target})>"
