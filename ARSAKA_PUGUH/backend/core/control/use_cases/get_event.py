"""
Get Event Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IControlRepository


class GetEventUseCase:
    def __init__(self, repository: IControlRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, event_id: UUID) -> Optional[dict]:
        evt = await self._repository.get_event(tenant_id, event_id)
        if not evt:
            return None

        return {
            "id": str(evt.id),
            "event_type": evt.event_type,
            "aggregate_id": str(evt.aggregate_id),
            "aggregate_type": evt.aggregate_type,
            "payload": evt.payload,
            "metadata": evt.metadata,
            "occurred_at": evt.occurred_at.isoformat() if evt.occurred_at else None,
            "recorded_at": evt.recorded_at.isoformat() if evt.recorded_at else None,
            "schema_version": evt.schema_version,
        }
