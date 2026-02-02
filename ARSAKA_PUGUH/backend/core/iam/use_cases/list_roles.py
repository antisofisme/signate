"""
List Roles Use Case
"""

from typing import List
from uuid import UUID

from ..interfaces import IIAMRepository


class ListRolesUseCase:
    """Use case for listing roles in a tenant."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID) -> List[dict]:
        """
        List roles in a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of role dicts
        """
        roles = await self._repository.list_roles(tenant_id)

        return [
            {
                "id": str(role.id),
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "is_system": role.is_system,
                "created_at": role.created_at.isoformat() if role.created_at else None,
            }
            for role in roles
        ]
