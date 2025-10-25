"""
Playlist Models
Playlists for organizing and scheduling content playback
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, JSON, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Playlist(Base):
    """
    Playlist model for content organization and scheduling

    Playlists allow grouping content for scheduled playback with priorities.

    Attributes:
        id: Primary key
        name: Name of the playlist
        description: Description of playlist purpose
        is_active: Whether this playlist is currently active
        priority: Priority level (1-10, higher = higher priority)
        schedule: JSON field containing schedule configuration
        created_at: Timestamp when playlist was created
        updated_at: Timestamp when playlist was last updated
    """

    __tablename__ = "playlists"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Playlist Info
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=1, nullable=False)

    # Schedule as JSON
    # Structure: {
    #   "start_time": "07:00",
    #   "end_time": "23:00",
    #   "days": ["monday", "tuesday", ...],
    #   "start_date": "2025-01-01",  # optional
    #   "end_date": "2025-12-31"      # optional
    # }
    schedule = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    content_items = relationship("PlaylistContent", back_populates="playlist", cascade="all, delete-orphan", order_by="PlaylistContent.order_index")
    assignments = relationship("PlaylistAssignment", back_populates="playlist", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Playlist(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "priority": self.priority,
            "schedule": self.schedule,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PlaylistContent(Base):
    """
    Many-to-many relationship between playlists and content

    Manages content items within a playlist with ordering and duration.

    Attributes:
        id: Primary key
        playlist_id: Foreign key to playlists table
        content_id: Foreign key to content table
        order_index: Display order within playlist (0-based)
        duration: Duration in seconds for this item (overrides content default)
        created_at: Timestamp when content was added to playlist
    """

    __tablename__ = "playlist_content"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ordering and Settings
    order_index = Column(Integer, default=0, nullable=False)
    duration = Column(Integer, nullable=True)  # Duration in seconds, nullable to use content default

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    playlist = relationship("Playlist", back_populates="content_items")
    content = relationship("Content")

    def __repr__(self):
        return f"<PlaylistContent(playlist_id={self.playlist_id}, content_id={self.content_id}, order={self.order_index})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "playlist_id": self.playlist_id,
            "content_id": self.content_id,
            "order_index": self.order_index,
            "duration": self.duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PlaylistAssignment(Base):
    """
    Assignment of playlists to devices or tags

    Manages which playlists are assigned to which devices/tags.

    Attributes:
        id: Primary key
        playlist_id: Foreign key to playlists table
        device_id: Foreign key to devices table (nullable, mutually exclusive with tag_id)
        tag_id: Foreign key to tags table (nullable, mutually exclusive with device_id)
        created_at: Timestamp when playlist was assigned

    Constraints:
        - Either device_id OR tag_id must be set, but not both
    """

    __tablename__ = "playlist_assignments"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    playlist = relationship("Playlist", back_populates="assignments")
    device = relationship("Device")
    tag = relationship("Tag")

    def __repr__(self):
        return f"<PlaylistAssignment(playlist_id={self.playlist_id}, device_id={self.device_id}, tag_id={self.tag_id})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "playlist_id": self.playlist_id,
            "device_id": self.device_id,
            "tag_id": self.tag_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
