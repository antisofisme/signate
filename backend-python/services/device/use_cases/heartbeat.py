"""
Device Heartbeat Use Case
Update device last_seen_at and metadata
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from ..domain.device import DeviceHeartbeat
from ..domain.interfaces import IDeviceRepository
from shared.geoip import lookup_geoip


class DeviceHeartbeatUseCase:
    """
    Use case for device heartbeat
    Called by player every 30 seconds
    """

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    async def execute(self, heartbeat_data: DeviceHeartbeat) -> bool:
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

        # Check if device has been released (by CMS admin or hard reset)
        if device.status == 'released':
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device has been released. Please re-register."
            )

        # Only active devices can send heartbeat
        if not device.is_active():
            raise ValueError("Device is not active. Please activate first.")

        # Update last_seen_at
        device.last_seen_at = datetime.now(timezone.utc)

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

        # Connection reliability tracking (Phase 2)
        if heartbeat_data.connection_drops_count is not None:
            device.connection_drops_count = heartbeat_data.connection_drops_count

        # Update device_uuid for WebOS devices
        if heartbeat_data.device_uuid:
            device.device_uuid = heartbeat_data.device_uuid

        # Update local IP (from WebRTC detection on player)
        if heartbeat_data.local_ip:
            device.local_ip = heartbeat_data.local_ip

        # Update IP address from HTTP request
        ip_changed = False
        if heartbeat_data.ip_address:
            if device.ip_address != heartbeat_data.ip_address:
                ip_changed = True
            device.ip_address = heartbeat_data.ip_address

        # Phase 6: GeoIP lookup if IP changed or never looked up
        if ip_changed or (device.ip_address and not device.geo_city):
            try:
                geoip_result = await lookup_geoip(device.ip_address)
                if geoip_result.success:
                    device.geo_city = geoip_result.city
                    device.geo_country = geoip_result.country
                    device.geo_country_code = geoip_result.country_code
                    device.geo_region = geoip_result.region
                    device.geo_isp = geoip_result.isp
                    device.geo_timezone = geoip_result.timezone
                    device.geo_latitude = geoip_result.latitude
                    device.geo_longitude = geoip_result.longitude
                    device.geo_updated_at = datetime.now(timezone.utc)
            except Exception as e:
                # GeoIP lookup failure shouldn't break heartbeat
                import logging
                logging.getLogger(__name__).warning(f"GeoIP lookup failed for {device.ip_address}: {e}")

        # Save changes
        self.device_repo.update(device)

        return True
