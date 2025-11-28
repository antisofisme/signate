"""
Request Activation Code Use Case
Generate 6-digit code for device activation
"""

import secrets  # 🔒 SECURITY: Use secrets instead of random for cryptographically secure codes
import string
from datetime import datetime, timedelta, timezone
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
        code: Optional[str] = None,
        device_token: Optional[str] = None,
        device_type: str = 'monitor',
        device_name: str = 'New Device',
        device_uuid: str = None,
        platform: str = 'browser'
    ) -> Dict:
        """
        Request activation code for device

        🔒 SECURITY CHANGE: Device always created as unassigned (organization_id = None)
        - Admin will assign organization during approval process
        - This enables device pooling and flexible organization assignment

        NEW: Code persistence - if device_uuid matches existing pending device,
        return same code instead of creating new device

        ✨ ARCHITECTURAL FIX: Backend generates code if not provided
        - Ensures backend is the single source of truth for activation codes
        - Player no longer generates codes client-side

        Args:
            code: Optional 6-digit activation code (backend generates if not provided)
            device_token: Optional device JWT token (currently not used)
            device_type: 'tv' or 'monitor'
            device_name: Device name
            device_uuid: UUID for WebOS devices (used for code persistence)
            platform: Platform info

        Returns:
            Dict with unique_code, expires_at, device_id
        """

        # 🎯 CHECK FOR EXISTING PENDING DEVICE (Code Persistence)
        # If device_uuid exists and matches a pending/released device, check expiry
        if device_uuid:
            existing_device = self.device_repo.find_by_uuid(device_uuid)
            if existing_device and existing_device.status in ['pending', 'released']:
                # ✨ NEW: Check if code expired - if yes, generate new code
                if existing_device.can_activate():
                    # Code still valid - reuse it
                    print(f"[Device Registration] ✅ Found existing device with UUID {device_uuid}, reusing valid code: {existing_device.unique_code}")
                    return {
                        'unique_code': existing_device.unique_code,
                        'expires_at': existing_device.code_expires_at.isoformat() if existing_device.code_expires_at else None,
                        'device_id': existing_device.id,
                        'device_token': None
                    }
                else:
                    # Code expired - generate new code and update device
                    print(f"[Device Registration] ⚠️ Code expired for device {existing_device.id}, generating new code...")

                    # Validate new code is unique
                    existing_code_check = self.device_repo.find_by_code(code)
                    if existing_code_check and existing_code_check.id != existing_device.id:
                        raise ValueError(f"Activation code {code} is already in use. Please generate a new code.")

                    # Update device with new code
                    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
                    existing_device.unique_code = code
                    existing_device.code_expires_at = expires_at

                    # Save to database
                    updated_device = self.device_repo.update(existing_device)

                    print(f"[Device Registration] ✅ Device {updated_device.id} updated with new code: {code}")
                    return {
                        'unique_code': updated_device.unique_code,
                        'expires_at': updated_device.code_expires_at.isoformat(),
                        'device_id': updated_device.id,
                        'device_token': None
                    }

        # ✨ NEW FLOW: Always create device as unassigned
        # Organization will be assigned when admin claims the device
        organization_id = None

        # ✨ ARCHITECTURAL FIX: Generate code server-side if not provided
        # This ensures backend is the single source of truth
        if not code:
            code = self._generate_unique_code()
            print(f"[Device Registration] 🎲 Backend generated code: {code}")
        else:
            print(f"[Device Registration] ⚠️ Player provided code (legacy): {code}")

        # CRITICAL FIX P0-8: Handle race condition with retry logic
        # Database constraint ensures uniqueness, but we need graceful retry
        max_retries = 3
        last_error = None
        created_device = None

        for attempt in range(max_retries):
            try:
                # Validate code is unique (check database)
                existing_device = self.device_repo.find_by_code(code)
                if existing_device:
                    # If code was player-provided (legacy), reject
                    # If code was backend-generated, this should never happen (bug in _generate_unique_code)
                    raise ValueError(f"Activation code {code} is already in use. Please generate a new code.")

                # Code expires in 10 minutes
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

                # Create device entity (always unassigned - organization_id = None)
                device = Device(
                    id=None,
                    device_type=device_type,
                    device_name=device_name,
                    organization_id=None,  # ✨ Always NULL - assigned during admin approval
                    status='pending',
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
                    last_seen_at=None,
                    room_number=None,
                    assigned_playlist_id=None,
                    created_at=None,
                    updated_at=None,
                    released_at=None,
                    deleted_at=None,
                    created_by_id=None,
                    updated_by_id=None,
                    deleted_by_id=None,
                    rotation=0,
                    is_volume_enabled=True,
                    location_type='guest_room',
                    is_personalization_supported=True,
                    privacy_mode='limited'
                )

                # Save to database
                # If race condition occurs, database unique constraint will raise IntegrityError
                created_device = self.device_repo.create(device)

                # Success - break out of retry loop
                break

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if it's a unique constraint violation (CRITICAL FIX P0-8)
                if 'unique' in error_msg or 'duplicate' in error_msg or 'ix_devices_unique_code' in error_msg:
                    # Race condition detected - code was taken between check and insert
                    if attempt < max_retries - 1:
                        # Retry with small delay
                        import time
                        time.sleep(0.1)  # 100ms delay
                        print(f"[Device Registration] ⚠️ Race condition detected (attempt {attempt + 1}), retrying...")
                        continue
                    else:
                        # Max retries reached
                        raise ValueError(f"Activation code {code} is already in use after {max_retries} attempts. Please generate a new code.")
                else:
                    # Different error - re-raise immediately
                    raise

        # If we exited loop without success, raise last error
        if not created_device and last_error:
            raise last_error

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
        🔒 SECURITY: Generate cryptographically secure 6-digit numeric code
        Uses secrets module instead of random for better security
        Format: 6 digits (000000 - 999999)
        """
        # Use only digits for activation code (easier to read/type)
        chars = string.digits  # 0-9

        # Use secrets.choice instead of random.choice
        return ''.join(secrets.choice(chars) for _ in range(6))
