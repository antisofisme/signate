"""
Schedule Models
SQLAlchemy models for advanced scheduling system
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Date, Time, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.database import Base
from services.auth.repositories.models import UserModel


class ScheduleDeviceTargeting(Base):
    """
    Junction table for schedule-to-device targeting.
    Replaces JSONB device_ids array for better referential integrity.
    """
    __tablename__ = "schedule_device_targeting"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    schedule = relationship("Schedule", back_populates="device_targets")
    device = relationship("DeviceModel", foreign_keys=[device_id])

    def __repr__(self):
        return f"<ScheduleDeviceTargeting schedule={self.schedule_id} device={self.device_id}>"


class ScheduleTagTargeting(Base):
    """
    Junction table for schedule-to-tag targeting.
    Replaces JSONB tag_ids array for better referential integrity.
    """
    __tablename__ = "schedule_tag_targeting"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    schedule = relationship("Schedule", back_populates="tag_targets")
    tag = relationship("TagModel", foreign_keys=[tag_id])

    def __repr__(self):
        return f"<ScheduleTagTargeting schedule={self.schedule_id} tag={self.tag_id}>"


class Schedule(Base):
    """
    Advanced Schedule Model with Recurrence Patterns

    Supports:
    - Once: Single occurrence
    - Daily: Every N days
    - Weekly: Specific days of week
    - Monthly: Specific days of month
    - Yearly: Specific date each year

    Color-coded for calendar display
    """
    __tablename__ = "schedules"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Schedule Info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), index=True)

    # Time Range
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    # Recurrence Pattern
    recurrence_type = Column(String(20), nullable=True)  # 'once', 'daily', 'weekly', 'monthly', 'yearly'
    recurrence_pattern = Column(JSONB, nullable=True)    # {"days": [1,3,5], "interval": 2}
    exceptions = Column(JSONB, nullable=True)            # ["2025-01-15", "2025-02-20"]

    # Color & Status
    color = Column(String(7), default='#3B82F6', nullable=False)  # Hex color for calendar display
    mode = Column(String(20), default='rotate', index=True)  # 'override' or 'rotate'
    is_active = Column(Boolean, default=True, index=True)
    
    # Targeting (LEGACY - will be removed after migration 080)
    # Use schedule_device_targeting and schedule_tag_targeting junction tables instead
    device_ids = Column(JSONB, nullable=True)           # DEPRECATED: Use device_targets relationship
    tag_ids = Column(JSONB, nullable=True)              # DEPRECATED: Use tag_targets relationship
    applies_to_all = Column(Boolean, default=False)     # Apply to all org devices

    # Metadata
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(TIMESTAMP, nullable=True)

    # Audit trail fields (Migration 046/052)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    playlist = relationship("PlaylistModel", foreign_keys=[playlist_id])
    created_by = relationship("UserModel", foreign_keys=[created_by_id])
    updated_by = relationship("UserModel", foreign_keys=[updated_by_id])
    deleted_by = relationship("UserModel", foreign_keys=[deleted_by_id])
    # organization = relationship("OrganizationModel", foreign_keys=[organization_id])

    # Junction table relationships (new - replaces JSONB arrays)
    device_targets = relationship("ScheduleDeviceTargeting", back_populates="schedule", cascade="all, delete-orphan")
    tag_targets = relationship("ScheduleTagTargeting", back_populates="schedule", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Schedule {self.id}: {self.name} ({self.recurrence_type})>"
