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
        ip_address: IP address for TV devices
        passphrase: Passphrase for TV pairing (WebOS Developer Mode)
        unique_code: Activation code for Monitor devices
        code_expires_at: Expiry timestamp for Monitor activation code
        status: Current status of device (pending/active/inactive)
        last_seen: Last time device sent heartbeat
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

    # Status tracking
    status = Column(String(20), default="pending", nullable=False, index=True)
    last_seen = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tags = relationship("DeviceTag", back_populates="device", cascade="all, delete-orphan")
    content_assignments = relationship("ContentAssignment", back_populates="device", cascade="all, delete-orphan")

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
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
