"""
Request Activation Code Use Case
Generate 6-digit code for device activation
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict

from ..domain.device import Device
from ..domain.interfaces import IDeviceRepository


class RequestActivationCodeUseCase:
    """
    Use case for requesting activation code
    Called by player/browser to get activation code
    """

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    def execute(
        self,
        organization_id: int,
        device_type: str = 'monitor',
        device_name: str = 'New Device',
        device_uuid: str = None,
        platform: str = 'browser'
    ) -> Dict:
        """
        Generate activation code for device

        Args:
            organization_id: Organization ID
            device_type: 'tv' or 'monitor'
            device_name: Device name
            device_uuid: UUID for WebOS devices
            platform: Platform info

        Returns:
            Dict with unique_code and expires_at
        """

        # Generate 6-digit alphanumeric code
        code = self._generate_code()

        # Code expires in 10 minutes
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Create device entity
        device = Device(
            id=None,
            device_type=device_type,
            device_name=device_name,
            organization_id=organization_id,
            unique_code=code,
            code_expires_at=expires_at,
            device_uuid=device_uuid,
            platform=platform,
            ip_address=None,
            screen_width=None,
            screen_height=None,
            viewport_width=None,
            viewport_height=None,
            device_pixel_ratio=None,
            user_agent=None,
            connection_type=None,
            connection_speed=None,
            model_name=None,
            firmware_version=None,
            status='pending',
            last_seen=None,
            rotation=0,
            volume_enabled=True,
            room_number=None,
            location_type='guest_room',
            supports_personalization=True,
            privacy_mode='limited',
            created_at=None,
            updated_at=None,
            released_at=None
        )

        # Save to database
        created_device = self.device_repo.create(device)

        return {
            'unique_code': created_device.unique_code,
            'expires_at': created_device.code_expires_at.isoformat(),
            'device_id': created_device.id
        }

    def _generate_code(self) -> str:
        """Generate random 6-digit alphanumeric code"""
        # Use uppercase letters and numbers for readability
        chars = string.ascii_uppercase + string.digits
        # Exclude confusing characters: O, 0, I, 1
        chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        return ''.join(random.choice(chars) for _ in range(6))
