"""
Update Device Use Case
Update device settings from CMS
"""

from typing import Optional

from ..domain.device import Device
from ..domain.interfaces import IDeviceRepository


class UpdateDeviceUseCase:
    """
    Use case for updating device settings
    Called by CMS admin to modify device configuration
    """

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    def execute(
        self,
        device_id: int,
        device_name: Optional[str] = None,
        room_number: Optional[str] = None,
        location_type: Optional[str] = None,
        rotation: Optional[int] = None,
        volume_enabled: Optional[bool] = None,
        supports_personalization: Optional[bool] = None,
        privacy_mode: Optional[str] = None
    ) -> Device:
        """
        Update device settings

        Args:
            device_id: Device ID to update
            device_name: Optional new device name
            room_number: Optional new room number
            location_type: Optional new location type
            rotation: Optional screen rotation (0, 90, 180, 270)
            volume_enabled: Optional volume setting
            supports_personalization: Optional personalization support
            privacy_mode: Optional privacy mode setting

        Returns:
            Updated Device entity

        Raises:
            ValueError: If device not found or validation fails
        """

        # Find device
        device = self.device_repo.find_by_id(device_id)

        if not device:
            raise ValueError(f"Device with ID {device_id} not found")

        # Update fields if provided
        if device_name is not None:
            device.device_name = device_name

        if room_number is not None:
            device.room_number = room_number

        if location_type is not None:
            # Validate location_type
            valid_types = ['guest_room', 'lobby', 'conference_room', 'restaurant', 'other']
            if location_type not in valid_types:
                raise ValueError(f"Invalid location_type. Must be one of: {', '.join(valid_types)}")
            device.location_type = location_type

        if rotation is not None:
            # Validate rotation
            if rotation not in [0, 90, 180, 270]:
                raise ValueError("Rotation must be 0, 90, 180, or 270 degrees")
            device.rotation = rotation

        if volume_enabled is not None:
            device.volume_enabled = volume_enabled

        if supports_personalization is not None:
            device.supports_personalization = supports_personalization

        if privacy_mode is not None:
            # Validate privacy_mode
            valid_modes = ['none', 'limited', 'full']
            if privacy_mode not in valid_modes:
                raise ValueError(f"Invalid privacy_mode. Must be one of: {', '.join(valid_modes)}")
            device.privacy_mode = privacy_mode

        # Save changes
        updated_device = self.device_repo.update(device)

        return updated_device

    def deactivate_device(self, device_id: int) -> Device:
        """
        Deactivate a device (set status to 'inactive')

        Args:
            device_id: Device ID to deactivate

        Returns:
            Updated Device entity
        """
        device = self.device_repo.find_by_id(device_id)

        if not device:
            raise ValueError(f"Device with ID {device_id} not found")

        device.status = 'inactive'
        return self.device_repo.update(device)

    def delete_device(self, device_id: int) -> bool:
        """
        Delete a device permanently

        Args:
            device_id: Device ID to delete

        Returns:
            True if deleted successfully, False if device not found
        """
        # Repository delete() handles device not found case
        return self.device_repo.delete(device_id)
