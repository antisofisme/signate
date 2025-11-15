"""
Create Device Group Use Case
Business logic for creating a new device group
"""

from typing import Optional
from sqlalchemy.orm import Session

from services.device.domain.device_group import DeviceGroup
from services.device.repositories.device_group_repo import DeviceGroupRepository


class CreateDeviceGroupUseCase:
    """Use case for creating a device group"""

    def __init__(self, db: Session):
        self.repo = DeviceGroupRepository(db)

    def execute(
        self,
        name: str,
        organization_id: int,
        description: Optional[str] = None,
        parent_group_id: Optional[int] = None,
        group_type: Optional[str] = None,
        sort_order: int = 0,
        default_playlist_id: Optional[int] = None,
        created_by: Optional[int] = None,
    ) -> DeviceGroup:
        """
        Create a new device group

        Args:
            name: Group name (required)
            organization_id: Organization ID (required)
            description: Optional description
            parent_group_id: Optional parent group for hierarchy
            group_type: Type of group (chain, hotel, floor, location, custom)
            sort_order: Display order
            default_playlist_id: Default playlist for devices in this group
            created_by: User ID who created the group

        Returns:
            Created DeviceGroup entity

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("Group name is required")

        if not organization_id or organization_id <= 0:
            raise ValueError("Valid organization_id is required")

        # Validate parent group exists if provided
        if parent_group_id:
            parent = self.repo.get_by_id(parent_group_id)
            if not parent:
                raise ValueError(f"Parent group {parent_group_id} not found")

            # Ensure parent belongs to same organization
            if parent.organization_id != organization_id:
                raise ValueError("Parent group must belong to same organization")

        # Create domain entity
        group = DeviceGroup(
            name=name.strip(),
            description=description.strip() if description else None,
            parent_group_id=parent_group_id,
            organization_id=organization_id,
            group_type=group_type,
            sort_order=sort_order,
            default_playlist_id=default_playlist_id,
            created_by=created_by,
        )

        # Persist to database
        created_group = self.repo.create(group)

        return created_group
