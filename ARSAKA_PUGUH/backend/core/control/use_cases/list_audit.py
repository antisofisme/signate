"""
List Audit Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IControlRepository


class ListAuditUseCase:
    def __init__(self, repository: IControlRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        records, total = await self._repository.list_audit(
            tenant_id=tenant_id,
            resource_type=resource_type,
            action=action,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                {
                    "id": str(rec.id),
                    "operation_type": rec.operation_type,
                    "resource_type": rec.resource_type,
                    "resource_id": str(rec.resource_id) if rec.resource_id else None,
                    "actor_user_id": str(rec.actor_user_id) if rec.actor_user_id else None,
                    "actor_role": rec.actor_role,
                    "action_status": rec.action_status,
                    "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
                }
                for rec in records
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
