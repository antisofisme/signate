"""
Get Permissions Use Case
"""

from typing import List
from uuid import UUID

from ..interfaces import IIAMRepository


class GetPermissionsUseCase:
    """Use case for getting permissions and permission matrix."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def list_all(self) -> List[dict]:
        """
        List all available permissions.

        Returns:
            List of permission dicts
        """
        permissions = await self._repository.list_permissions()

        return [
            {
                "id": str(perm.id),
                "key": perm.key,
                "resource": perm.resource,
                "action": perm.action,
                "description": perm.description,
            }
            for perm in permissions
        ]

    async def get_matrix(self, tenant_id: UUID) -> dict:
        """
        Get permission matrix for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Permission matrix dict
        """
        matrix = await self._repository.get_permission_matrix(tenant_id)
        all_permissions = await self._repository.list_permissions()

        # Build matrix with all permissions as columns
        return {
            "permissions": [perm.key for perm in all_permissions],
            "roles": matrix["roles"],
        }
