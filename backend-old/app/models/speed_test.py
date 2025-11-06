"""
DeviceSpeedTest Model
Network speed test history for devices
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SpeedTestQuality(str, enum.Enum):
    """Speed test quality classification"""
    GOOD = "good"      # Download ≥25 Mbps AND Upload ≥10 Mbps
    FAIR = "fair"      # Download ≥10 Mbps AND Upload ≥5 Mbps
    POOR = "poor"      # Below fair thresholds


class DeviceSpeedTest(Base):
    """
    DeviceSpeedTest model for network speed test history

    Stores results from device speed tests performed by the viewer client.
    Tests are conducted every 30 minutes and stored for historical analysis.

    Attributes:
        id: Primary key
        device_id: Foreign key to devices table
        download_speed: Download speed in Mbps (e.g., 50.35)
        upload_speed: Upload speed in Mbps (e.g., 25.10)
        latency: Ping latency in milliseconds (optional)
        jitter: Network jitter in milliseconds (optional)
        packet_loss: Packet loss percentage 0.00-100.00 (optional)
        dns_server: DNS server IP address (IPv4 or IPv6) (optional)
        quality: Speed quality classification (good/fair/poor)
        tested_at: Timestamp when test was conducted
        test_duration_ms: How long the test took in milliseconds (optional)
        server_endpoint: Which server was used for testing (optional)
        error_message: Error message if test partially failed (optional)

    Relationships:
        device: Back-reference to Device model

    Retention Policy:
        - Keep last 100 tests per device
        - Older tests are automatically deleted when new tests are added

    Quality Thresholds:
        - Good: Download ≥25 Mbps AND Upload ≥10 Mbps
        - Fair: Download ≥10 Mbps AND Upload ≥5 Mbps
        - Poor: Below fair thresholds
    """

    __tablename__ = "device_speed_tests"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to device
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Speed metrics (required)
    download_speed = Column(DECIMAL(10, 2), nullable=False)  # Mbps
    upload_speed = Column(DECIMAL(10, 2), nullable=False)    # Mbps

    # Optional metrics
    latency = Column(Integer, nullable=True)                  # ms
    jitter = Column(Integer, nullable=True)                   # ms
    packet_loss = Column(DECIMAL(5, 2), nullable=True)       # percentage

    # DNS and quality
    dns_server = Column(String(45), nullable=True)           # IPv4 or IPv6
    quality = Column(String(20), nullable=False, index=True)  # 'good', 'fair', 'poor'

    # Test metadata
    tested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    test_duration_ms = Column(Integer, nullable=True)        # audit purpose

    # Additional context
    server_endpoint = Column(String(255), nullable=True)     # which server was used
    error_message = Column(Text, nullable=True)              # partial failure info

    # Relationships
    device = relationship("Device", back_populates="speed_tests")

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "download_speed": float(self.download_speed) if self.download_speed is not None else None,
            "upload_speed": float(self.upload_speed) if self.upload_speed is not None else None,
            "latency": self.latency,
            "jitter": self.jitter,
            "packet_loss": float(self.packet_loss) if self.packet_loss is not None else None,
            "dns_server": self.dns_server,
            "quality": self.quality.value if self.quality else None,
            "tested_at": self.tested_at.isoformat() if self.tested_at else None,
            "test_duration_ms": self.test_duration_ms,
            "server_endpoint": self.server_endpoint,
            "error_message": self.error_message,
        }

    def __repr__(self):
        return f"<DeviceSpeedTest(id={self.id}, device_id={self.device_id}, quality={self.quality}, tested_at={self.tested_at})>"
