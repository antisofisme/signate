"""
SQLAlchemy Models
Database representation for Device
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base


class DeviceModel(Base):
    """Device database model"""
    __tablename__ = "devices"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    device_type = Column(String(20), nullable=False)  # 'tv' or 'monitor'
    device_name = Column(String(200), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Activation
    unique_code = Column(String(6), unique=True, nullable=True, index=True)  # 6-digit code
    code_expires_at = Column(DateTime(timezone=True), nullable=True)
    device_uuid = Column(String(100), unique=True, nullable=True, index=True)  # For WebOS

    # Network info
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    platform = Column(String(50), nullable=True)  # 'webOS', 'browser', etc.

    # Device metadata
    screen_width = Column(Integer, nullable=True)
    screen_height = Column(Integer, nullable=True)
    viewport_width = Column(Integer, nullable=True)
    viewport_height = Column(Integer, nullable=True)
    device_pixel_ratio = Column(Float, nullable=True)
    user_agent = Column(String(500), nullable=True)
    connection_type = Column(String(50), nullable=True)
    connection_speed = Column(Float, nullable=True)

    # WebOS specific
    model_name = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)

    # Status
    status = Column(String(20), nullable=False, default='pending', index=True)  # 'pending', 'active', 'inactive'
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Display settings
    rotation = Column(Integer, default=0, nullable=False)  # 0, 90, 180, 270
    volume_enabled = Column(Boolean, default=True, nullable=False)

    # Hotel-specific
    room_number = Column(String(50), nullable=True, index=True)
    location_type = Column(String(50), default='guest_room', nullable=False)
    supports_personalization = Column(Boolean, default=True, nullable=False)
    privacy_mode = Column(String(20), default='limited', nullable=False)  # 'none', 'limited', 'full'

    # Audit tracking
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)  # When device was released/deactivated

    # Relationships
    # organization = relationship("OrganizationModel", back_populates="devices")
    creator = relationship("UserModel", foreign_keys=[created_by])
    updater = relationship("UserModel", foreign_keys=[updated_by])
