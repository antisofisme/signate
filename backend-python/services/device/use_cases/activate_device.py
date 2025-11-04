"""
Activate Device Use Case
Activate device using 6-digit code from CMS
"""

from datetime import datetime
from typing import Dict, Optional

from ..domain.device import Device, ActivationCode
from ..domain.interfaces import IDeviceRepository


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
            ValueError: If code invalid or expired
        """

        # Validate code format
        try:
            activation_code = ActivationCode(code=unique_code.upper())
        except ValueError as e:
            raise ValueError(f"Invalid activation code: {str(e)}")

        # Find device by code
        device = self.device_repo.find_by_code(activation_code.code)

        if not device:
            raise ValueError("Device not found with this code")

        # Check if already activated
        if device.is_active():
            raise ValueError("Device already activated")

        # Check if code expired
        if not device.can_activate():
            raise ValueError("Activation code expired. Please request a new code from the device.")

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
