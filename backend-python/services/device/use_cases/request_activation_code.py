"""
Request Activation Code Use Case
Generate 6-digit code for device activation
"""

import secrets  # 🔒 SECURITY: Use secrets instead of random for cryptographically secure codes
import string
from datetime import datetime, timedelta
from typing import Dict, Optional

from ..domain.device import Device
from ..domain.interfaces import IDeviceRepository
from shared.auth import create_device_token, extract_device_from_token


class RequestActivationCodeUseCase:
    """
    Use case for requesting activation code
    Called by player/browser to get activation code
    """

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    def execute(
        self,
        device_token: Optional[str] = None,
        device_type: str = 'monitor',
        device_name: str = 'New Device',
        device_uuid: str = None,
        platform: str = 'browser'
    ) -> Dict:
        """
        Generate activation code for device

        🔒 SECURITY: organization_id is NO LONGER accepted as parameter
        - First-time registration: organization_id = None (assigned during activation by admin)
        - Re-registration: organization_id extracted from device_token JWT

        Args:
            device_token: Optional device JWT token for re-registration (from localStorage)
            device_type: 'tv' or 'monitor'
            device_name: Device name
            device_uuid: UUID for WebOS devices
            platform: Platform info

        Returns:
            Dict with unique_code, expires_at, device_id, and device_token
        """

        # 🔒 SECURITY: Extract organization_id from device_token (if re-registration)
        organization_id = None
        if device_token:
            try:
                device_info = extract_device_from_token(device_token)
                organization_id = device_info['organization_id']
                print(f"[Device Registration] 🔄 Re-registration with org_id: {organization_id} (from JWT)")
            except Exception as e:
                # Invalid token - treat as first-time registration
                print(f"[Device Registration] ⚠️ Invalid device_token, treating as first-time registration: {e}")
                organization_id = None

        # 🔒 SECURITY: Generate unique cryptographically secure 6-digit code
        code = self._generate_unique_code()

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

        # 🔑 Generate device JWT token for future re-registration
        # Token includes organization_id so player can re-register to same org
        device_jwt_token = None
        if created_device.organization_id:
            device_jwt_token = create_device_token(
                device_id=created_device.id,
                organization_id=created_device.organization_id
            )
            print(f"[Device Registration] 🔑 Device JWT token generated for device {created_device.id}")

        return {
            'unique_code': created_device.unique_code,
            'expires_at': created_device.code_expires_at.isoformat(),
            'device_id': created_device.id,
            'device_token': device_jwt_token  # JWT token for re-registration (only if org assigned)
        }

    def _generate_unique_code(self) -> str:
        """
        🔒 SECURITY: Generate unique cryptographically secure 6-digit code
        Checks database to ensure code is not already in use
        Retries up to 10 times to find unique code (collision extremely rare with 6 chars)
        """
        max_attempts = 10
        for attempt in range(max_attempts):
            code = self._generate_secure_code()

            # Check if code already exists in database
            existing_device = self.device_repo.find_by_code(code)

            if not existing_device:
                # Code is unique
                if attempt > 0:
                    print(f"[Device Registration] 🔒 Generated unique code after {attempt + 1} attempts: {code}")
                return code
            else:
                # Code collision - try again
                print(f"[Device Registration] ⚠️ Code collision detected (attempt {attempt + 1}): {code}")

        # Fallback: append timestamp to ensure uniqueness (should never happen)
        fallback_code = self._generate_secure_code()
        print(f"[Device Registration] ⚠️ WARNING: Max attempts reached, using fallback code: {fallback_code}")
        return fallback_code

    def _generate_secure_code(self) -> str:
        """
        🔒 SECURITY: Generate cryptographically secure 6-digit code
        Uses secrets module instead of random for better security
        """
        # Use uppercase letters and numbers for readability
        chars = string.ascii_uppercase + string.digits
        # Exclude confusing characters: O, 0, I, 1
        chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')

        # Use secrets.choice instead of random.choice
        return ''.join(secrets.choice(chars) for _ in range(6))
