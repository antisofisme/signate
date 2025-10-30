"""
Tag Models
Tags for categorizing devices and content assignment rules
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Tag(Base):
    """
    Tag model for device categorization

    Tags are used to group devices by location, department, or purpose.
    Content can be assigned to tags instead of individual devices.

    Attributes:
        id: Primary key
        tag_name: Name of the tag
        description: Description of tag purpose
        color: Color code for UI display (hex format)
        tag_priority: Priority among tags (higher number = higher priority in content resolution)
        organization_id: Organization this tag belongs to
        created_by: User who created this tag
        created_at: Timestamp when tag was created
    """

    __tablename__ = "tags"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Tag Info
    tag_name = Column(String(100), nullable=False, index=True)  # Note: unique constraint should be per organization
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")  # Hex color code
    tag_priority = Column(Integer, default=0, nullable=False)  # Priority for content resolution

    # Multi-tenancy fields
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    device_tags = relationship("DeviceTag", back_populates="tag", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="tags")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.tag_name}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "tag_name": self.tag_name,
            "description": self.description,
            "color": self.color,
            "tag_priority": self.tag_priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeviceTag(Base):
    """
    Many-to-many relationship between devices and tags

    Attributes:
        device_id: Foreign key to devices table (composite primary key)
        tag_id: Foreign key to tags table (composite primary key)
        assigned_at: Timestamp when tag was assigned to device
    """

    __tablename__ = "device_tags"

    # Composite Primary Key (device_id, tag_id)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    # Timestamps
    assigned_at = Column(DateTime, server_default=func.now())

    # Relationships
    device = relationship("Device", back_populates="tags")
    tag = relationship("Tag", back_populates="device_tags")

    def __repr__(self):
        return f"<DeviceTag(device_id={self.device_id}, tag_id={self.tag_id})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "device_id": self.device_id,
            "tag_id": self.tag_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
        }
