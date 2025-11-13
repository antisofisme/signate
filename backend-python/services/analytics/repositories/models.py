"""
Analytics SQLAlchemy Models
Maps to content_playback_logs table and analytical views
Phase 2 Day 2 - Analytics Service
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, text, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.database import Base


class ContentPlaybackLog(Base):
    """Content playback log model for analytics tracking"""
    __tablename__ = "content_playback_logs"

    id = Column(Integer, primary_key=True, index=True)

    # References
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Playback details
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    ended_at = Column(TIMESTAMP(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Actual playback duration
    expected_duration = Column(Integer, nullable=True)  # Expected duration from content
    is_completed = Column(Boolean, nullable=False, default=False)  # Watched to completion

    # Metadata
    device_info = Column(JSONB)  # Device details at playback time
    playback_quality = Column(String(20))  # SD, HD, FHD, etc.
    error_count = Column(Integer, nullable=False, default=0)
    error_details = Column(JSONB)  # Error logs if any

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    def __repr__(self):
        return f"<ContentPlaybackLog(id={self.id}, content_id={self.content_id}, device_id={self.device_id})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content_id": self.content_id,
            "device_id": self.device_id,
            "playlist_id": self.playlist_id,
            "organization_id": self.organization_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "expected_duration": self.expected_duration,
            "is_completed": self.is_completed,
            "device_info": self.device_info,
            "playback_quality": self.playback_quality,
            "error_count": self.error_count,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
