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
    Content assignment to devices or tags

    This model manages which content is displayed on which devices/tags,
    including priority.

    Attributes:
        id: Primary key
        content_id: Foreign key to content table
        device_id: Foreign key to devices table (nullable, mutually exclusive with tag_id)
        tag_id: Foreign key to tags table (nullable, mutually exclusive with device_id)
        priority: Display priority (higher number = higher priority)
        created_at: Timestamp when content was assigned

    Constraints:
        - Either device_id OR tag_id must be set, but not both
    """

    __tablename__ = "content_assignments"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), index=True)

    # Display Settings
    priority = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    device = relationship("Device", back_populates="content_assignments")
    content = relationship("Content", back_populates="assignments")

    def __repr__(self):
        return f"<ContentAssignment(id={self.id}, device_id={self.device_id}, tag_id={self.tag_id}, content_id={self.content_id}, priority={self.priority})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "content_id": self.content_id,
            "device_id": self.device_id,
            "tag_id": self.tag_id,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
