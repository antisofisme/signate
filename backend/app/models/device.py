"""
Device Model
TV and Monitor devices registered in the system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class DeviceType(str, enum.Enum):
    """Device type enumeration"""
    TV = "tv"
    MONITOR = "monitor"


class DeviceStatus(str, enum.Enum):
    """Device status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class Device(Base):
    """
    Device model for TV/Monitor management

    Attributes:
        id: Primary key
        device_type: Type of device (tv or monitor)
        device_name: Display name for the device
        ip_address: IP address for TV devices
        passphrase: Passphrase for TV pairing (WebOS Developer Mode)
        unique_code: Activation code for Monitor devices
        code_expires_at: Expiry timestamp for Monitor activation code
        status: Current status of device (pending/active/inactive)
        last_seen: Last time device sent heartbeat
        room_number: Room number for hotel guest room devices
        location_type: Type of location (guest_room, public_area, staff_area, meeting_room)
        supports_personalization: Whether device supports guest personalization
        privacy_mode: full (show all PII), limited (welcome only), none (generic)
        created_at: Timestamp when device was registered
        updated_at: Timestamp when device was last updated
    """

    __tablename__ = "devices"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Device Info
    device_type = Column(String(20), nullable=False)
    device_name = Column(String(100), nullable=False)

    # For TV: IP address & passphrase
    ip_address = Column(String(45))  # IPv4 or IPv6
    passphrase = Column(String(50))

    # For Monitor: unique activation code
    unique_code = Column(String(20), unique=True, index=True)
    code_expires_at = Column(DateTime)

    # Permanent Device Identifier (UUID)
    device_uuid = Column(String(36), unique=True, index=True)  # UUID v4 format

    # Platform Information (WebOS or Browser)
    platform = Column(String(20))  # 'webOS', 'browser', etc.
    model_name = Column(String(100))  # WebOS TV model name
    firmware_version = Column(String(50))  # WebOS firmware version

    # Status tracking
    status = Column(String(20), default="pending", nullable=False, index=True)
    last_seen = Column(DateTime)

    # Device Information (from viewer)
    screen_width = Column(Integer)
    screen_height = Column(Integer)
    viewport_width = Column(Integer)
    viewport_height = Column(Integer)
    device_pixel_ratio = Column(Float)
    user_agent = Column(Text)
    connection_type = Column(String(50))
    connection_speed = Column(Float)

    # Display Settings (configurable from admin)
    rotation = Column(Integer, default=0)  # 0, 90, 180, 270
    volume_enabled = Column(Boolean, default=True)

    # Hotel-specific fields (Phase 0 enhancement)
    room_number = Column(String(20), nullable=True)  # Room number for guest room devices
    location_type = Column(String(50), default='guest_room', nullable=True)  # guest_room, public_area, staff_area, meeting_room
    supports_personalization = Column(Boolean, default=True, nullable=True)  # Whether device supports personalization
    privacy_mode = Column(String(50), default='limited', nullable=True)  # full, limited, none

    # Multi-tenancy fields
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    released_at = Column(DateTime)  # Timestamp when device was released (orphaned from viewer)

    # Relationships
    tags = relationship("DeviceTag", back_populates="device", cascade="all, delete-orphan")
    playlist_assignments = relationship("PlaylistAssignment", back_populates="device", cascade="all, delete-orphan")
    content_assignments = relationship("ContentAssignment", back_populates="device", cascade="all, delete-orphan")
    logs = relationship("DeviceLog", back_populates="device", cascade="all, delete-orphan")
    commands = relationship("DeviceCommand", back_populates="device", cascade="all, delete-orphan")
    speed_tests = relationship("DeviceSpeedTest", back_populates="device", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="devices")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.device_name}', type='{self.device_type}', status='{self.status}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "device_type": self.device_type,
            "device_name": self.device_name,
            "ip_address": self.ip_address,
            "passphrase": self.passphrase,
            "unique_code": self.unique_code,
            "code_expires_at": self.code_expires_at.isoformat() if self.code_expires_at else None,
            "device_uuid": self.device_uuid,
            "platform": self.platform,
            "model_name": self.model_name,
            "firmware_version": self.firmware_version,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            # Device information
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "device_pixel_ratio": self.device_pixel_ratio,
            "user_agent": self.user_agent,
            "connection_type": self.connection_type,
            "connection_speed": self.connection_speed,
            # Display settings
            "rotation": self.rotation,
            "volume_enabled": self.volume_enabled,
            # Hotel-specific fields
            "room_number": self.room_number,
            "location_type": self.location_type,
            "supports_personalization": self.supports_personalization,
            "privacy_mode": self.privacy_mode,
        }
