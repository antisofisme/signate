"""
Delete Device Group Use Case
Business logic for soft-deleting a device group
"""

from typing import Optional
from sqlalchemy.orm import Session

from services.device.repositories.device_group_repo import DeviceGroupRepository


class DeleteDeviceGroupUseCase:
    """Use case for deleting a device group"""

    def __init__(self, db: Session):
        self.repo = DeviceGroupRepository(db)

    def execute(
        self,
        group_id: int,
        organization_id: int,
        deleted_by_id: Optional[int] = None,
    ) -> bool:
        """
        Soft delete a device group

        Args:
            group_id: ID of group to delete
            organization_id: Organization ID (for authorization)
            deleted_by_id: User ID who deleted the group (for audit trail)

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If validation fails or group not found
        """
        # Get existing group
        existing_group = self.repo.get_by_id(group_id)
        if not existing_group:
            raise ValueError(f"Group {group_id} not found")

        # Verify organization ownership
        if existing_group.organization_id != organization_id:
            raise ValueError("Group does not belong to this organization")

        # Check if group has children
        children = self.repo.get_children(group_id)
        if children:
            raise ValueError(
                f"Cannot delete group with {len(children)} child groups. "
                "Delete or reassign child groups first."
            )

        # Soft delete with deleted_by_id tracking
        success = self.repo.soft_delete(group_id, deleted_by_id=deleted_by_id)

        if not success:
            raise ValueError(f"Failed to delete group {group_id}")

        return True
