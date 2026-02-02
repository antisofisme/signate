"""
List Service Accounts Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IIAMRepository


class ListServiceAccountsUseCase:
    """Use case for listing service accounts in a tenant."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """
        List service accounts in a tenant.

        Args:
            tenant_id: Tenant UUID
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Dict with service accounts list and pagination info
        """
        accounts, total = await self._repository.list_service_accounts(
            tenant_id=tenant_id,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                {
                    "id": str(acc.id),
                    "name": acc.name,
                    "description": acc.description,
                    "client_id": acc.client_id,
                    "status": acc.status.value,
                    "last_used_at": acc.last_used_at.isoformat() if acc.last_used_at else None,
                    "created_at": acc.created_at.isoformat() if acc.created_at else None,
                }
                for acc in accounts
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
