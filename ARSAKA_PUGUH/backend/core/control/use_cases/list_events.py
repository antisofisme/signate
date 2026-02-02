"""
List Events Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IControlRepository


class ListEventsUseCase:
    def __init__(self, repository: IControlRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        event_type: Optional[str] = None,
        aggregate_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        events, total = await self._repository.list_events(
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_id=aggregate_id,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                {
                    "id": str(evt.id),
                    "event_type": evt.event_type,
                    "aggregate_id": str(evt.aggregate_id),
                    "aggregate_type": evt.aggregate_type,
                    "occurred_at": evt.occurred_at.isoformat() if evt.occurred_at else None,
                }
                for evt in events
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0,
        }

    async def list_dlq(self, tenant_id: UUID, page: int = 1, limit: int = 20) -> dict:
        events, total = await self._repository.list_dlq_events(tenant_id, page, limit)
        return {
            "items": events,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
