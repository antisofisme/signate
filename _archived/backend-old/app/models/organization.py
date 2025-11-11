"""
Organization Model
Multi-tenant organization management
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Organization(Base):
    """
    Organization model for multi-tenant system

    Attributes:
        id: Primary key
        name: Organization display name
        slug: Unique URL-friendly identifier
        description: Optional description
        settings: JSON field for org-specific settings
        max_devices: Maximum allowed devices
        max_users: Maximum allowed users
        max_storage_gb: Maximum storage in GB
        subscription_tier: Subscription level (free, pro, enterprise)
        subscription_expires_at: Subscription expiry date
        is_active: Whether organization is active
        created_at: Timestamp when created
        updated_at: Timestamp when last updated
    """

    __tablename__ = "organizations"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Organization Info
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500))

    # Organization PIN for device registration (8-digit, unique)
    organization_pin = Column(String(20), unique=True, index=True)

    # Organization Settings
    settings = Column(JSON, default=dict)
    max_devices = Column(Integer, default=10)
    max_users = Column(Integer, default=5)
    max_storage_gb = Column(Integer, default=10)

    # Subscription/Billing
    subscription_tier = Column(String(50), default='free')
    subscription_expires_at = Column(DateTime)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    user_organizations = relationship("UserOrganization", back_populates="organization", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="organization", cascade="all, delete-orphan")
    content = relationship("Content", back_populates="organization", cascade="all, delete-orphan")
    playlists = relationship("Playlist", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="organization", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "organization_pin": self.organization_pin,
            "settings": self.settings or {},
            "max_devices": self.max_devices,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
            "subscription_tier": self.subscription_tier,
            "subscription_expires_at": self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def can_add_device(self, current_count: int = 0) -> bool:
        """Check if organization can add more devices"""
        return current_count < self.max_devices

    def can_add_user(self, current_count: int = 0) -> bool:
        """Check if organization can add more users"""
        return current_count < self.max_users

    def is_subscription_active(self) -> bool:
        """Check if subscription is still active"""
        if not self.subscription_expires_at:
            return True  # No expiry means active
        from datetime import datetime
        return datetime.utcnow() < self.subscription_expires_at

    def get_setting(self, key: str, default=None):
        """Get organization setting by key"""
        if not self.settings:
            return default
        return self.settings.get(key, default)

    def set_setting(self, key: str, value):
        """Set organization setting"""
        if not self.settings:
            self.settings = {}
        self.settings[key] = value