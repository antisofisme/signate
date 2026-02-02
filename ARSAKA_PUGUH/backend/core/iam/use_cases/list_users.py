"""
List Users Use Case
"""

from typing import List, Optional
from uuid import UUID

from ..interfaces import IIAMRepository


class ListUsersUseCase:
    """Use case for listing users in a tenant."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        role_id: Optional[UUID] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """
        List users in a tenant.

        Args:
            tenant_id: Tenant UUID
            role_id: Optional filter by role
            search: Optional search query
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Dict with users list and pagination info
        """
        users, total = await self._repository.list_users(
            tenant_id=tenant_id,
            role_id=role_id,
            search=search,
            page=page,
            limit=limit,
        )

        return {
            "items": users,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0,
        }

    async def get_stats(self, tenant_id: UUID) -> dict:
        """Get user statistics for tenant."""
        return await self._repository.get_user_stats(tenant_id=tenant_id)
