"""
Tag SQLAlchemy Models
Database models for tags and content_tags tables
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.database import Base


class Tag(Base):
    """Tag model for organizing content"""
    __tablename__ = "tags"
    __table_args__ = {'extend_existing': True}

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=False, default="#3B82F6")  # Hex color
    description = Column(Text, nullable=True)

    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    # Note: Organization relationship omitted - organization service uses Clean Architecture (no SQLAlchemy model)
    content_tags = relationship("ContentTag", back_populates="tag", cascade="all, delete-orphan")


class ContentTag(Base):
    """Content-Tag junction table (many-to-many)"""
    __tablename__ = "content_tags"
    __table_args__ = {'extend_existing': True}

    # Identity
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tag = relationship("Tag", back_populates="content_tags")
