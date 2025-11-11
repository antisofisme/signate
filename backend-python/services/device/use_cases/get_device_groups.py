"""
Get Device Groups Use Case
Business logic for retrieving device groups
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from services.device.domain.device_group import DeviceGroup
from services.device.repositories.device_group_repo import DeviceGroupRepository


class GetDeviceGroupsUseCase:
    """Use case for retrieving device groups"""

    def __init__(self, db: Session):
        self.repo = DeviceGroupRepository(db)

    def get_by_id(self, group_id: int, organization_id: int) -> Optional[DeviceGroup]:
        """
        Get a single device group by ID

        Args:
            group_id: ID of group to retrieve
            organization_id: Organization ID (for authorization)

        Returns:
            DeviceGroup entity or None if not found

        Raises:
            ValueError: If group doesn't belong to organization
        """
        group = self.repo.get_by_id(group_id)

        if not group:
            return None

        # Verify organization ownership
        if group.organization_id != organization_id:
            raise ValueError("Group does not belong to this organization")

        return group

    def get_all_by_organization(
        self, organization_id: int, include_deleted: bool = False
    ) -> List[DeviceGroup]:
        """
        Get all groups for an organization

        Args:
            organization_id: Organization ID
            include_deleted: Include soft-deleted groups

        Returns:
            List of DeviceGroup entities
        """
        groups = self.repo.get_by_organization(organization_id, include_deleted)
        return groups

    def get_root_groups(self, organization_id: int) -> List[DeviceGroup]:
        """
        Get root groups (no parent) for an organization

        Args:
            organization_id: Organization ID

        Returns:
            List of root DeviceGroup entities
        """
        groups = self.repo.get_root_groups(organization_id)
        return groups

    def get_children(
        self, group_id: int, organization_id: int
    ) -> List[DeviceGroup]:
        """
        Get child groups of a parent group

        Args:
            group_id: Parent group ID
            organization_id: Organization ID (for authorization)

        Returns:
            List of child DeviceGroup entities

        Raises:
            ValueError: If parent group doesn't belong to organization
        """
        # Verify parent group belongs to organization
        parent = self.repo.get_by_id(group_id)
        if not parent:
            raise ValueError(f"Group {group_id} not found")

        if parent.organization_id != organization_id:
            raise ValueError("Group does not belong to this organization")

        children = self.repo.get_children(group_id)
        return children

    def get_devices_in_group(
        self, group_id: int, organization_id: int, recursive: bool = False
    ) -> List[int]:
        """
        Get device IDs in a group

        Args:
            group_id: Group ID
            organization_id: Organization ID (for authorization)
            recursive: Include devices in child groups

        Returns:
            List of device IDs

        Raises:
            ValueError: If group doesn't belong to organization
        """
        # Verify group belongs to organization
        group = self.repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        if group.organization_id != organization_id:
            raise ValueError("Group does not belong to this organization")

        if recursive:
            device_ids = self.repo.get_devices_in_group_recursive(group_id)
        else:
            device_ids = self.repo.get_devices_in_group(group_id)

        return device_ids

    def get_group_stats(self, group_id: int, organization_id: int) -> dict:
        """
        Get group statistics (device count, online/offline)

        Args:
            group_id: Group ID
            organization_id: Organization ID (for authorization)

        Returns:
            Dictionary with stats (total_devices, online_devices, offline_devices)

        Raises:
            ValueError: If group doesn't belong to organization
        """
        # Verify group belongs to organization
        group = self.repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        if group.organization_id != organization_id:
            raise ValueError("Group does not belong to this organization")

        stats = self.repo.get_group_stats(group_id)
        return stats
