"""
Device Command Model
Queue system for remote commands to devices (reset, release, etc.)
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class CommandType(str, enum.Enum):
    """Command type enumeration"""
    RESET = "reset"  # Force device to reset (clear localStorage + cache)
    REFRESH = "refresh"  # Refresh content cache only
    RELOAD = "reload"  # Reload player only


class CommandStatus(str, enum.Enum):
    """Command status enumeration"""
    PENDING = "pending"  # Waiting for device to execute
    EXECUTED = "executed"  # Device executed successfully
    EXPIRED = "expired"  # Command expired (not executed within timeout)


class DeviceCommand(Base):
    """
    Device Command model for remote command queue system

    Attributes:
        id: Primary key
        device_id: Foreign key to devices table
        command_type: Type of command (reset/refresh/reload)
        reason: Why command was issued (deleted_by_admin, released_by_admin, etc.)
        status: Current status (pending/executed/expired)
        created_at: When command was queued
        executed_at: When device executed the command
        expires_at: When command will expire if not executed
    """

    __tablename__ = "device_commands"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key to Device
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Command Info
    command_type = Column(String(20), nullable=False, index=True)
    reason = Column(String(100))  # Why command was issued

    # Status tracking
    status = Column(String(20), default="pending", nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    executed_at = Column(DateTime)
    expires_at = Column(DateTime, index=True)  # Auto-expire old commands

    # Relationships
    device = relationship("Device", back_populates="commands")

    def __repr__(self):
        return f"<DeviceCommand(id={self.id}, device_id={self.device_id}, type='{self.command_type}', status='{self.status}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "command_type": self.command_type,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
