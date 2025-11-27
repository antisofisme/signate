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


class Schedule(Base):
    """
    Advanced Schedule Model with Recurrence Patterns

    Supports:
    - Once: Single occurrence
    - Daily: Every N days
    - Weekly: Specific days of week
    - Monthly: Specific days of month
    - Yearly: Specific date each year

    Priority-based scheduling: Higher priority wins when schedules overlap
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

    # Priority & Status
    priority = Column(Integer, default=0, index=True)    # Higher = more important
    is_active = Column(Boolean, default=True, index=True)
    
    # Targeting
    device_ids = Column(JSONB, nullable=True)           # [1, 2, 3] - specific devices
    tag_ids = Column(JSONB, nullable=True)              # [1, 2] - devices with these tags
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

    def __repr__(self):
        return f"<Schedule {self.id}: {self.name} ({self.recurrence_type})>"
