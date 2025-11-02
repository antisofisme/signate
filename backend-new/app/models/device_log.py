"""
Device Log Model
Stores console logs from viewer devices for remote monitoring and debugging
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DeviceLog(Base):
    """
    Device Log model
    Stores console logs from TV/Monitor devices
    """
    __tablename__ = "device_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    log_level = Column(String(20), nullable=False, index=True)  # log, warn, error, info
    message = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)  # Optional: file/function where log originated
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationship
    device = relationship("Device", back_populates="logs")

    def __repr__(self):
        return f"<DeviceLog(id={self.id}, device_id={self.device_id}, level={self.log_level}, timestamp={self.timestamp})>"
