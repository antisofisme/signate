"""
Device Entity - Domain Model
Pure business object, no framework dependencies
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Device:
    """Device domain entity"""
    # Required fields (no defaults) - MUST come first
    id: Optional[int]
    device_type: str  # 'tv' or 'monitor'
    device_name: str
    organization_id: Optional[int]  # None for unassigned devices
    status: str  # 'pending', 'active', 'inactive'

    # Optional fields (no defaults)
    unique_code: Optional[str]  # 6-digit activation code
    code_expires_at: Optional[datetime]
    device_uuid: Optional[str]  # For WebOS
    ip_address: Optional[str]
    platform: Optional[str]  # 'webOS', 'browser', etc.

    # GeoIP data (Phase 6)
    geo_city: Optional[str]
    geo_country: Optional[str]
    geo_country_code: Optional[str]
    geo_region: Optional[str]
    geo_isp: Optional[str]
    geo_timezone: Optional[str]
    geo_latitude: Optional[float]
    geo_longitude: Optional[float]
    geo_updated_at: Optional[datetime]

    screen_width: Optional[int]
    screen_height: Optional[int]
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    device_pixel_ratio: Optional[float]
    user_agent: Optional[str]
    connection_type: Optional[str]
    connection_speed: Optional[float]
    connection_drops_count: Optional[int]  # Number of network disconnections since startup
    model_name: Optional[str]
    firmware_version: Optional[str]
    last_seen_at: Optional[datetime]
    room_number: Optional[str]
    assigned_playlist_id: Optional[int]
    playlist_name: Optional[str]  # Name of assigned playlist (from JOIN)
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    released_at: Optional[datetime]
    deleted_at: Optional[datetime]

    # Audit trail fields
    created_by_id: Optional[int]
    updated_by_id: Optional[int]
    deleted_by_id: Optional[int]

    # Fields WITH defaults - MUST come last
    rotation: int = 0
    is_volume_enabled: bool = True
    location_type: str = 'guest_room'
    is_personalization_supported: bool = True
    privacy_mode: str = 'limited'

    def is_online(self) -> bool:
        """Check if device is online (heartbeat in last 5 minutes)"""
        if not self.last_seen_at:
            return False
        now = datetime.now(timezone.utc)
        diff = (now - self.last_seen_at).total_seconds()
        return diff < 300  # 5 minutes

    def is_active(self) -> bool:
        """Check if device is active"""
        return self.status == 'active'

    def is_pending(self) -> bool:
        """Check if device is pending activation"""
        return self.status == 'pending'

    def can_activate(self) -> bool:
        """Check if device can be activated

        ✨ SIMPLIFIED: No expiry check - codes are valid until activated
        Device can be activated if it's in pending or released status
        """
        return self.status in ('pending', 'released')

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
    """
    Heartbeat data from device

    OPTIMIZED (Phase 2):
    - Static fields now sent via /capabilities endpoint
    - Viewport only sent when changed
    - Added connection_drops_count for reliability tracking
    """
    unique_code: str
    device_uuid: Optional[str]

    # Static fields - DEPRECATED (now in /capabilities)
    screen_width: Optional[int]
    screen_height: Optional[int]
    device_pixel_ratio: Optional[float]
    user_agent: Optional[str]

    # Semi-static fields
    viewport_width: Optional[int]
    viewport_height: Optional[int]

    # Dynamic fields
    connection_type: Optional[str]
    connection_speed: Optional[float]

    # Connection reliability
    connection_drops_count: Optional[int] = None
    ip_address: Optional[str] = None  # Client IP from HTTP request
