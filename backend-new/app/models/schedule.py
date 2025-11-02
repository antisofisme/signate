"""
Schedule Model
Time-based scheduling for content display
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Time, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Schedule(Base):
    """
    Schedule model for time-based content display

    Allows setting specific times and days for content to be displayed.

    Attributes:
        id: Primary key
        schedule_name: Name of the schedule
        device_id: Foreign key to devices table (optional, can be tag-based)
        content_id: Foreign key to content table
        day_of_week: Days of week (0=Monday, 6=Sunday, comma-separated)
        start_time: Time to start showing content
        end_time: Time to stop showing content
        start_date: Date to start this schedule
        end_date: Date to end this schedule
        is_active: Whether this schedule is active
        priority: Schedule priority
        notes: Admin notes about schedule
        created_at: Timestamp when schedule was created
        updated_at: Timestamp when schedule was last updated
    """

    __tablename__ = "schedules"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Schedule Info
    schedule_name = Column(String(100), nullable=False)

    # Foreign Keys (nullable - can be tag-based or device-based)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time Settings
    day_of_week = Column(String(20))  # e.g., "0,1,2,3,4" for weekdays
    start_time = Column(Time)
    end_time = Column(Time)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))

    # Settings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=100, nullable=False)
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Schedule(id={self.id}, name='{self.schedule_name}', device_id={self.device_id})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "schedule_name": self.schedule_name,
            "device_id": self.device_id,
            "content_id": self.content_id,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "priority": self.priority,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
