"""
Device Entity - Domain Model
Pure business object, no framework dependencies
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Device:
    """Device domain entity"""
    # Required fields (no defaults) - MUST come first
    id: Optional[int]
    device_type: str  # 'tv' or 'monitor'
    device_name: str
    organization_id: int
    status: str  # 'pending', 'active', 'inactive'

    # Optional fields (no defaults)
    unique_code: Optional[str]  # 6-digit activation code
    code_expires_at: Optional[datetime]
    device_uuid: Optional[str]  # For WebOS
    ip_address: Optional[str]
    platform: Optional[str]  # 'webOS', 'browser', etc.
    screen_width: Optional[int]
    screen_height: Optional[int]
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    device_pixel_ratio: Optional[float]
    user_agent: Optional[str]
    connection_type: Optional[str]
    connection_speed: Optional[float]
    model_name: Optional[str]
    firmware_version: Optional[str]
    last_seen: Optional[datetime]
    room_number: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    released_at: Optional[datetime]

    # Fields WITH defaults - MUST come last
    rotation: int = 0
    volume_enabled: bool = True
    location_type: str = 'guest_room'
    supports_personalization: bool = True
    privacy_mode: str = 'limited'

    def is_online(self) -> bool:
        """Check if device is online (heartbeat in last 5 minutes)"""
        if not self.last_seen:
            return False
        now = datetime.utcnow()
        diff = (now - self.last_seen).total_seconds()
        return diff < 300  # 5 minutes

    def is_active(self) -> bool:
        """Check if device is active"""
        return self.status == 'active'

    def is_pending(self) -> bool:
        """Check if device is pending activation"""
        return self.status == 'pending'

    def can_activate(self) -> bool:
        """Check if device can be activated"""
        if not self.code_expires_at:
            return False
        return datetime.utcnow() < self.code_expires_at

    def needs_heartbeat(self) -> bool:
        """Check if device needs heartbeat (offline > 5 min)"""
        return not self.is_online() and self.is_active()


@dataclass(frozen=True)
class ActivationCode:
    """Activation code value object (immutable)"""
    code: str

    def __post_init__(self):
        """Validation"""
        if not self.code or len(self.code) != 6:
            raise ValueError("Activation code must be exactly 6 characters")
        if not self.code.isalnum():
            raise ValueError("Activation code must be alphanumeric")


@dataclass
class DeviceHeartbeat:
    """Heartbeat data from device"""
    unique_code: str
    device_uuid: Optional[str]
    screen_width: Optional[int]
    screen_height: Optional[int]
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    device_pixel_ratio: Optional[float]
    user_agent: Optional[str]
    connection_type: Optional[str]
    connection_speed: Optional[float]
