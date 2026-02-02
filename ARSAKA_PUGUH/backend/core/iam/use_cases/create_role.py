"""
Create Role Use Case
"""

from typing import List, Optional
from uuid import UUID

from ..interfaces import IIAMRepository


class CreateRoleUseCase:
    """Use case for creating a new role."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
    ) -> dict:
        """
        Create a new role.

        Args:
            tenant_id: Tenant UUID
            name: Role name (unique within tenant)
            display_name: Display name for UI
            description: Optional description
            permission_ids: Optional list of permission UUIDs to assign

        Returns:
            Created role dict

        Raises:
            RoleNameExistsError: If role name already exists
        """
        role = await self._repository.create_role(
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            description=description,
            permission_ids=permission_ids,
        )

        # Get permissions for response
        permissions = []
        if permission_ids:
            permissions = await self._repository.get_role_permissions(role.id)

        return {
            "id": str(role.id),
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "is_system": role.is_system,
            "can_delete": role.can_delete(),
            "can_update": role.can_update(),
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
            "permissions": [
                {
                    "id": str(perm.id),
                    "key": perm.key,
                    "resource": perm.resource,
                    "action": perm.action,
                    "description": perm.description,
                }
                for perm in permissions
            ],
        }
