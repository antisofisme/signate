"""
Add Device to Group Use Case
Business logic for adding a device to a group
"""

from typing import Optional
from sqlalchemy.orm import Session

from services.device.domain.device_group import DeviceGroupMember
from services.device.repositories.device_group_repo import DeviceGroupRepository
from services.device.repositories.device_repo import DeviceRepository


class AddDeviceToGroupUseCase:
    """Use case for adding a device to a group"""

    def __init__(self, db: Session):
        self.group_repo = DeviceGroupRepository(db)
        self.device_repo = DeviceRepository(db)

    def execute(
        self,
        device_id: int,
        group_id: int,
        organization_id: int,
        added_by: Optional[int] = None,
    ) -> DeviceGroupMember:
        """
        Add a device to a group

        Args:
            device_id: ID of device to add
            group_id: ID of group
            organization_id: Organization ID (for authorization)
            added_by: User ID who added the device

        Returns:
            DeviceGroupMember entity

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

        # Check if device is already in group
        devices_in_group = self.group_repo.get_devices_in_group(group_id)
        if device_id in devices_in_group:
            raise ValueError(f"Device {device_id} is already in group {group_id}")

        # Add device to group
        member = self.group_repo.add_device_to_group(
            device_id=device_id, group_id=group_id, added_by_id=added_by
        )

        return member
