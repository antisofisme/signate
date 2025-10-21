"""
Content Assignment Model
Assignment of content to devices with priority and ordering
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ContentAssignment(Base):
    """
    Content assignment to devices

    This model manages which content is displayed on which devices,
    including display order and priority.

    Attributes:
        id: Primary key
        device_id: Foreign key to devices table
        content_id: Foreign key to content table
        priority: Display priority (lower number = higher priority)
        display_order: Order in playlist (for same priority)
        is_active: Whether this assignment is active
        start_date: When to start showing this content
        end_date: When to stop showing this content
        assigned_at: Timestamp when content was assigned
        updated_at: Timestamp when assignment was last updated
    """

    __tablename__ = "content_assignments"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)

    # Display Settings
    priority = Column(Integer, default=100, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Schedule
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))

    # Timestamps
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    device = relationship("Device", back_populates="content_assignments")
    content = relationship("Content", back_populates="assignments")

    def __repr__(self):
        return f"<ContentAssignment(id={self.id}, device_id={self.device_id}, content_id={self.content_id}, priority={self.priority})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "content_id": self.content_id,
            "priority": self.priority,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
