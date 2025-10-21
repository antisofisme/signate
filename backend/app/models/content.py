"""
Content Model
Media content (images, videos) served to devices
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ContentType(str, enum.Enum):
    """Content type enumeration"""
    IMAGE = "image"
    VIDEO = "video"


class Content(Base):
    """
    Content model for media files

    Attributes:
        id: Primary key
        title: Display title of content
        description: Description of content
        content_type: Type of content (image or video)
        anthias_url: URL to content in Anthias system
        anthias_asset_id: Asset ID in Anthias
        duration: Display duration in seconds
        file_size: File size in bytes
        mime_type: MIME type of file
        is_active: Whether content is active
        created_at: Timestamp when content was uploaded
        updated_at: Timestamp when content was last updated
    """

    __tablename__ = "content"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Content Info
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_type = Column(String(20), nullable=False)

    # Anthias Integration
    anthias_url = Column(String(500), nullable=False)
    anthias_asset_id = Column(String(100), index=True)

    # Display Settings
    duration = Column(Integer, default=10, nullable=False)  # seconds

    # File Info
    file_size = Column(Integer)  # bytes (bigint in DB)
    mime_type = Column(String(100))

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    assignments = relationship("ContentAssignment", back_populates="content", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title}', type='{self.content_type}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content_type": self.content_type,
            "anthias_url": self.anthias_url,
            "anthias_asset_id": self.anthias_asset_id,
            "duration": self.duration,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
