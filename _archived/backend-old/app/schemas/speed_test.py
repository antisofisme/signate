"""
Speed Test schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class SpeedTestCreate(BaseModel):
    """
    Request schema for creating a speed test record

    Used by viewer devices to submit speed test results.
    Quality classification is calculated automatically by the backend.
    """
    # Required speed metrics
    download_speed: float = Field(..., ge=0, description="Download speed in Mbps")
    upload_speed: float = Field(..., ge=0, description="Upload speed in Mbps")

    # Optional metrics
    latency: Optional[int] = Field(None, ge=0, description="Ping latency in milliseconds")
    jitter: Optional[int] = Field(None, ge=0, description="Jitter in milliseconds")
    packet_loss: Optional[float] = Field(None, ge=0, le=100, description="Packet loss percentage (0-100)")

    # DNS and server info
    dns_server: Optional[str] = Field(None, max_length=45, description="DNS server IP address")
    server_endpoint: Optional[str] = Field(None, max_length=255, description="Speed test server endpoint")

    # Test metadata
    test_duration_ms: Optional[int] = Field(None, ge=0, description="Test duration in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if test partially failed")

    class Config:
        json_schema_extra = {
            "example": {
                "download_speed": 50.35,
                "upload_speed": 25.10,
                "latency": 15,
                "jitter": 2,
                "packet_loss": 0.05,
                "dns_server": "8.8.8.8",
                "server_endpoint": "speedtest.net:8080",
                "test_duration_ms": 12500
            }
        }


class SpeedTestResponse(BaseModel):
    """
    Response schema for speed test records

    Includes all fields from the database including auto-calculated quality.
    """
    id: int
    device_id: int

    # Speed metrics
    download_speed: float
    upload_speed: float
    latency: Optional[int] = None
    jitter: Optional[int] = None
    packet_loss: Optional[float] = None

    # DNS and quality
    dns_server: Optional[str] = None
    quality: str  # 'good', 'fair', 'poor'

    # Timestamps and metadata
    tested_at: datetime
    test_duration_ms: Optional[int] = None
    server_endpoint: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_id": 119,
                "download_speed": 50.35,
                "upload_speed": 25.10,
                "latency": 15,
                "jitter": 2,
                "packet_loss": 0.05,
                "dns_server": "8.8.8.8",
                "quality": "good",
                "tested_at": "2025-10-27T10:30:00Z",
                "test_duration_ms": 12500,
                "server_endpoint": "speedtest.net:8080",
                "error_message": None
            }
        }


class SpeedTestListResponse(BaseModel):
    """
    Response schema for speed test history list

    Used by GET /devices/{id}/speedtest endpoint
    """
    total: int = Field(..., description="Total number of speed tests")
    items: List[SpeedTestResponse] = Field(..., description="List of speed test records")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {
                        "id": 2,
                        "device_id": 119,
                        "download_speed": 52.40,
                        "upload_speed": 26.30,
                        "latency": 14,
                        "jitter": 1,
                        "packet_loss": 0.02,
                        "dns_server": "8.8.8.8",
                        "quality": "good",
                        "tested_at": "2025-10-27T11:00:00Z",
                        "test_duration_ms": 11800,
                        "server_endpoint": "speedtest.net:8080",
                        "error_message": None
                    },
                    {
                        "id": 1,
                        "device_id": 119,
                        "download_speed": 50.35,
                        "upload_speed": 25.10,
                        "latency": 15,
                        "jitter": 2,
                        "packet_loss": 0.05,
                        "dns_server": "8.8.8.8",
                        "quality": "good",
                        "tested_at": "2025-10-27T10:30:00Z",
                        "test_duration_ms": 12500,
                        "server_endpoint": "speedtest.net:8080",
                        "error_message": None
                    }
                ]
            }
        }
