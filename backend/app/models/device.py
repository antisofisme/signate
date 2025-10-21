"""
Device Model
TV and Monitor devices registered in the system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SQLEnum
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
        location: Physical location of device
        ip_address: IP address of device
        mac_address: MAC address for device identification
        passphrase: Security passphrase for device pairing
        unique_code: Unique identifier code for device registration
        status: Current status of device
        last_seen: Last time device sent heartbeat
        config_json: Additional configuration in JSON format
        notes: Admin notes about device
        created_at: Timestamp when device was registered
        updated_at: Timestamp when device was last updated
    """

    __tablename__ = "devices"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Device Info
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    device_name = Column(String(100), nullable=False)
    location = Column(String(200))

    # Network Info
    ip_address = Column(String(45), index=True)  # IPv6 compatible
    mac_address = Column(String(17), unique=True, index=True)

    # Security
    passphrase = Column(String(50))
    unique_code = Column(String(20), unique=True, nullable=False, index=True)

    # Status
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.PENDING, nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True))

    # Configuration
    config_json = Column(Text)  # JSON string for additional config
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tags = relationship("DeviceTag", back_populates="device", cascade="all, delete-orphan")
    content_assignments = relationship("ContentAssignment", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.device_name}', type='{self.device_type}', status='{self.status}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "device_type": self.device_type.value if self.device_type else None,
            "device_name": self.device_name,
            "location": self.location,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "unique_code": self.unique_code,
            "status": self.status.value if self.status else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
