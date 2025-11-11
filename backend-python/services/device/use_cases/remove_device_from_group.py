"""
Remove Device from Group Use Case
Business logic for removing a device from a group
"""

from sqlalchemy.orm import Session

from services.device.repositories.device_group_repo import DeviceGroupRepository
from services.device.repositories.device_repo import DeviceRepository


class RemoveDeviceFromGroupUseCase:
    """Use case for removing a device from a group"""

    def __init__(self, db: Session):
        self.group_repo = DeviceGroupRepository(db)
        self.device_repo = DeviceRepository(db)

    def execute(self, device_id: int, group_id: int, organization_id: int) -> bool:
        """
        Remove a device from a group

        Args:
            device_id: ID of device to remove
            group_id: ID of group
            organization_id: Organization ID (for authorization)

        Returns:
            True if removed successfully

        Raises:
            ValueError: If validation fails or entities not found
        """
        # Validate device exists
        device = self.device_repo.get_by_id(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")

        # Verify device belongs to organization
        if device.organization_id != organization_id:
            raise ValueError("Device does not belong to this organization")

        # Validate group exists
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        # Verify group belongs to organization
        if group.organization_id != organization_id:
            raise ValueError("Group does not belong to this organization")

        # Remove device from group
        success = self.group_repo.remove_device_from_group(
            device_id=device_id, group_id=group_id
        )

        if not success:
            raise ValueError(
                f"Device {device_id} is not a member of group {group_id}"
            )

        return True
