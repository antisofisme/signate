"""
Device Heartbeat Use Case
Update device last_seen_at and metadata
"""

from datetime import datetime
from typing import Optional

from ..domain.device import DeviceHeartbeat
from ..domain.interfaces import IDeviceRepository


class DeviceHeartbeatUseCase:
    """
    Use case for device heartbeat
    Called by player every 30 seconds
    """

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    def execute(self, heartbeat_data: DeviceHeartbeat) -> bool:
        """
        Update device heartbeat and metadata

        Args:
            heartbeat_data: Heartbeat information from device

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If device not found or inactive
        """

        # Find device by unique_code
        device = self.device_repo.find_by_code(heartbeat_data.unique_code)

        if not device:
            raise ValueError("Device not found with this code")

        # Only active devices can send heartbeat
        if not device.is_active():
            raise ValueError("Device is not active. Please activate first.")

        # Update last_seen_at
        device.last_seen_at = datetime.utcnow()

        # Update device metadata if provided
        if heartbeat_data.screen_width:
            device.screen_width = heartbeat_data.screen_width

        if heartbeat_data.screen_height:
            device.screen_height = heartbeat_data.screen_height

        if heartbeat_data.viewport_width:
            device.viewport_width = heartbeat_data.viewport_width

        if heartbeat_data.viewport_height:
            device.viewport_height = heartbeat_data.viewport_height

        if heartbeat_data.device_pixel_ratio:
            device.device_pixel_ratio = heartbeat_data.device_pixel_ratio

        if heartbeat_data.user_agent:
            device.user_agent = heartbeat_data.user_agent

        if heartbeat_data.connection_type:
            device.connection_type = heartbeat_data.connection_type

        if heartbeat_data.connection_speed:
            device.connection_speed = heartbeat_data.connection_speed

        # Update device_uuid for WebOS devices
        if heartbeat_data.device_uuid:
            device.device_uuid = heartbeat_data.device_uuid

        # Save changes
        self.device_repo.update(device)

        return True
