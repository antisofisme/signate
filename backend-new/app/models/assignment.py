"""
Content Assignment Model
Assignment of content to devices with priority and ordering
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ContentAssignment(Base):
    """
    Content assignment to devices or tags

    This model manages which content is displayed on which devices/tags,
    including priority, scheduling, and ordering.

    Attributes:
        id: Primary key
        content_id: Foreign key to content table
        device_id: Foreign key to devices table (nullable, mutually exclusive with tag_id)
        tag_id: Foreign key to tags table (nullable, mutually exclusive with device_id)
        priority: Display priority (higher number = higher priority)
        display_order: Order of content within the same assignment group (0-indexed)
        is_active: Whether this assignment is currently active (soft delete)
        start_date: Optional start date for scheduled content
        end_date: Optional end date for scheduled content
        notes: Admin notes about this assignment
        created_at: Timestamp when content was assigned
        updated_at: Timestamp when content assignment was last updated

    Constraints:
        - Either device_id OR tag_id must be set, but not both
    """

    __tablename__ = "content_assignments"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), index=True)

    # Display Settings
    priority = Column(Integer, default=0)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Scheduling
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("Device", back_populates="content_assignments")
    content = relationship("Content", back_populates="assignments")

    def __repr__(self):
        return f"<ContentAssignment(id={self.id}, device_id={self.device_id}, tag_id={self.tag_id}, content_id={self.content_id}, priority={self.priority}, is_active={self.is_active})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "content_id": self.content_id,
            "device_id": self.device_id,
            "tag_id": self.tag_id,
            "priority": self.priority,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
