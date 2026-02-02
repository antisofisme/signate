"""
Get User Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IIAMRepository


class GetUserUseCase:
    """Use case for getting a user with roles."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, user_id: UUID) -> Optional[dict]:
        """
        Get user by ID with their roles.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID

        Returns:
            User dict with roles or None if not found
        """
        user = await self._repository.get_user(tenant_id, user_id)
        if not user:
            return None

        # Get user's roles
        roles = await self._repository.get_user_roles(tenant_id, user_id)
        user["roles"] = [
            {
                "id": str(role.id),
                "name": role.name,
                "display_name": role.display_name,
            }
            for role in roles
        ]

        return user
