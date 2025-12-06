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
        is_volume_enabled: Optional[bool] = None,
        is_personalization_supported: Optional[bool] = None,
        privacy_mode: Optional[str] = None,
        current_user_org_id: Optional[int] = None,
        updated_by_id: Optional[int] = None
    ) -> Device:
        """
        Update device settings

        Args:
            device_id: Device ID to update
            device_name: Optional new device name
            room_number: Optional new room number
            location_type: Optional new location type
            rotation: Optional screen rotation (0, 90, 180, 270)
            is_volume_enabled: Optional volume setting
            is_personalization_supported: Optional personalization support
            privacy_mode: Optional privacy mode setting
            current_user_org_id: Current user's organization ID for authorization
            updated_by_id: User ID who updates this device (audit trail)

        Returns:
            Updated Device entity

        Raises:
            ValueError: If device not found or validation fails
            PermissionError: If user tries to update device from another organization
        """

        # Find device
        device = self.device_repo.find_by_id(device_id)

        if not device:
            raise ValueError(f"Device with ID {device_id} not found")

        # SECURITY: Verify user can only update devices in their organization
        if current_user_org_id is not None and device.organization_id != current_user_org_id:
            raise PermissionError(
                f"Cannot update device {device_id}: belongs to organization {device.organization_id}, "
                f"user belongs to organization {current_user_org_id}"
            )

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

        if is_volume_enabled is not None:
            device.is_volume_enabled = is_volume_enabled

        if is_personalization_supported is not None:
            device.is_personalization_supported = is_personalization_supported

        if privacy_mode is not None:
            # Validate privacy_mode
            valid_modes = ['none', 'limited', 'full']
            if privacy_mode not in valid_modes:
                raise ValueError(f"Invalid privacy_mode. Must be one of: {', '.join(valid_modes)}")
            device.privacy_mode = privacy_mode

        # Set audit trail
        if updated_by_id is not None:
            device.updated_by_id = updated_by_id

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

    def delete_device(
        self,
        device_id: int,
        current_user_org_id: Optional[int] = None,
        deleted_by_id: Optional[int] = None
    ) -> bool:
        """
        Release a device (move to Unsigned Pool)

        When admin deletes a device from Device List:
        - status = 'released' (not 'inactive')
        - released_at = current timestamp
        - organization_id = KEPT (device still belongs to same org)
        - Device will appear in Unsigned Pool for same organization
        - Device can be re-claimed from Unsigned Pool

        Args:
            device_id: Device ID to delete/release
            current_user_org_id: Current user's organization ID for authorization
            deleted_by_id: User ID who deleted this device (audit trail)

        Returns:
            True if released successfully, False if device not found

        Raises:
            PermissionError: If user tries to delete device from another organization
        """
        from datetime import datetime, timezone

        # SECURITY: Verify user can only delete devices in their organization
        device = self.device_repo.find_by_id(device_id)
        if not device:
            return False

        if current_user_org_id is not None and device.organization_id != current_user_org_id:
            raise PermissionError(
                f"Cannot delete device {device_id}: belongs to organization {device.organization_id}, "
                f"user belongs to organization {current_user_org_id}"
            )

        now = datetime.now(timezone.utc)

        # Check current status to determine action:
        # - If device is active/inactive → Release to Unsigned Pool (soft release)
        # - If device is already released → HARD DELETE (permanent, so player can re-register)
        if device.status == 'released':
            # Already in Unsigned Pool - perform HARD DELETE
            # This allows the player to re-register with fresh device record
            return self.device_repo.delete(device_id)
        else:
            # Release device (move to Unsigned Pool)
            # Note: organization_id is KEPT - device still belongs to same org
            device.status = 'released'
            device.released_at = now
            if deleted_by_id is not None:
                device.deleted_by_id = deleted_by_id

            self.device_repo.update(device)
            return True
