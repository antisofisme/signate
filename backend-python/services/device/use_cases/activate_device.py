"""
Activate Device Use Case
Activate device using 6-digit code from CMS

Updated to use centralized validators and error handling
"""

from datetime import datetime
from typing import Dict, Optional

from ..domain.device import Device, ActivationCode
from ..domain.interfaces import IDeviceRepository
from shared.errors import ValidationError, NotFoundError, ErrorCodes
from shared.validators import validate_activation_code


class ActivateDeviceUseCase:
    """
    Use case for activating device
    Called by CMS admin to activate device with code
    """

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    def execute(
        self,
        unique_code: str,
        device_name: Optional[str] = None,
        room_number: Optional[str] = None,
        location_type: Optional[str] = None
    ) -> Device:
        """
        Activate device with unique code

        Args:
            unique_code: 6-digit activation code
            device_name: Optional custom name
            room_number: Optional room number
            location_type: Optional location type

        Returns:
            Activated Device

        Raises:
            ValidationError: If code invalid or expired
            NotFoundError: If device not found
        """

        # Validate code format using centralized validator
        is_valid_code, error_msg = validate_activation_code(unique_code)
        if not is_valid_code:
            raise ValidationError(
                message=error_msg,
                code=ErrorCodes.VALIDATION_ERROR,
                details={"field": "unique_code"}
            )

        # Normalize code to uppercase
        normalized_code = unique_code.upper()

        # Find device by code
        device = self.device_repo.find_by_code(normalized_code)

        if not device:
            raise NotFoundError(
                message="Device dengan kode ini tidak ditemukan",
                resource_type="device",
                resource_id=normalized_code
            )

        # Check if already activated
        if device.is_active():
            raise ValidationError(
                message="Device sudah diaktivasi sebelumnya",
                code=ErrorCodes.ALREADY_EXISTS,
                details={"device_id": device.id, "status": device.status}
            )

        # Check if code expired
        if not device.can_activate():
            raise ValidationError(
                message="Kode aktivasi sudah kadaluarsa. Silakan request kode baru dari device.",
                code=ErrorCodes.EXPIRED_CODE,
                details={"expires_at": device.expires_at.isoformat() if device.expires_at else None}
            )

        # Update device
        device.status = 'active'
        device.last_seen = datetime.utcnow()

        if device_name:
            device.device_name = device_name

        if room_number:
            device.room_number = room_number

        if location_type:
            device.location_type = location_type

        # Save changes
        updated_device = self.device_repo.update(device)

        return updated_device
