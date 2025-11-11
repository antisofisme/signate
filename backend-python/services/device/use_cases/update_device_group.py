"""
Update Device Group Use Case
Business logic for updating an existing device group
"""

from typing import Optional
from sqlalchemy.orm import Session

from services.device.domain.device_group import DeviceGroup
from services.device.repositories.device_group_repo import DeviceGroupRepository


class UpdateDeviceGroupUseCase:
    """Use case for updating a device group"""

    def __init__(self, db: Session):
        self.repo = DeviceGroupRepository(db)

    def execute(
        self,
        group_id: int,
        organization_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent_group_id: Optional[int] = None,
        group_type: Optional[str] = None,
        sort_order: Optional[int] = None,
        default_playlist_id: Optional[int] = None,
    ) -> DeviceGroup:
        """
        Update an existing device group

        Args:
            group_id: ID of group to update
            organization_id: Organization ID (for authorization)
            name: New name (optional)
            description: New description (optional)
            parent_group_id: New parent group (optional)
            group_type: New group type (optional)
            sort_order: New sort order (optional)
            default_playlist_id: New default playlist (optional)

        Returns:
            Updated DeviceGroup entity

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

        # Validate name if provided
        if name is not None and not name.strip():
            raise ValueError("Group name cannot be empty")

        # Validate parent group if provided
        if parent_group_id is not None:
            # Prevent circular reference (group cannot be its own parent)
            if parent_group_id == group_id:
                raise ValueError("Group cannot be its own parent")

            # Check parent exists
            parent = self.repo.get_by_id(parent_group_id)
            if not parent:
                raise ValueError(f"Parent group {parent_group_id} not found")

            # Ensure parent belongs to same organization
            if parent.organization_id != organization_id:
                raise ValueError("Parent group must belong to same organization")

        # Create updated domain entity
        updated_group = DeviceGroup(
            id=group_id,
            name=name.strip() if name else existing_group.name,
            description=description.strip() if description is not None else existing_group.description,
            parent_group_id=parent_group_id if parent_group_id is not None else existing_group.parent_group_id,
            organization_id=organization_id,
            group_type=group_type if group_type is not None else existing_group.group_type,
            sort_order=sort_order if sort_order is not None else existing_group.sort_order,
            default_playlist_id=default_playlist_id if default_playlist_id is not None else existing_group.default_playlist_id,
        )

        # Persist changes
        result = self.repo.update(updated_group)

        return result
