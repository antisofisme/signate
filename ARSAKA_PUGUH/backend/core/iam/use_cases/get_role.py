"""
Get Role Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IIAMRepository


class GetRoleUseCase:
    """Use case for getting a role with permissions."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, role_id: UUID) -> Optional[dict]:
        """
        Get role by ID with its permissions.

        Args:
            tenant_id: Tenant UUID
            role_id: Role UUID

        Returns:
            Role dict with permissions or None if not found
        """
        role = await self._repository.get_role(tenant_id, role_id)
        if not role:
            return None

        # Get role's permissions
        permissions = await self._repository.get_role_permissions(role_id)

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
