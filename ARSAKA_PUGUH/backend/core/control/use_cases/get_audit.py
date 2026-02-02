"""
Get Audit Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IControlRepository


class GetAuditUseCase:
    def __init__(self, repository: IControlRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, audit_id: UUID) -> Optional[dict]:
        rec = await self._repository.get_audit(tenant_id, audit_id)
        if not rec:
            return None

        return {
            "id": str(rec.id),
            "operation_type": rec.operation_type,
            "resource_type": rec.resource_type,
            "resource_id": str(rec.resource_id) if rec.resource_id else None,
            "actor_user_id": str(rec.actor_user_id) if rec.actor_user_id else None,
            "actor_role": rec.actor_role,
            "action_status": rec.action_status,
            "reason_if_denied": rec.reason_if_denied,
            "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
            "trace_id": str(rec.trace_id) if rec.trace_id else None,
        }
