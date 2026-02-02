"""
Update Role Use Case
"""

from typing import List, Optional
from uuid import UUID

from ..interfaces import IIAMRepository


class UpdateRoleUseCase:
    """Use case for updating an existing role."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        role_id: UUID,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
    ) -> dict:
        """
        Update an existing role.

        Args:
            tenant_id: Tenant UUID
            role_id: Role UUID
            name: Optional new name
            display_name: Optional new display name
            description: Optional new description
            permission_ids: Optional new list of permission UUIDs (replaces existing)

        Returns:
            Updated role dict

        Raises:
            RoleNotFoundError: If role not found
            SystemRoleError: If attempting to modify a system role
            RoleNameExistsError: If new name already exists
        """
        role = await self._repository.update_role(
            tenant_id=tenant_id,
            role_id=role_id,
            name=name,
            display_name=display_name,
            description=description,
            permission_ids=permission_ids,
        )

        # Get permissions for response
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
