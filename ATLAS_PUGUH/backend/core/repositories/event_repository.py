"""
Event Repository Implementation

Persists domain events to event_log table.
Source: INFRA-DEC-006 (Event & Audit as Immutable Facts)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from ..domain.events import DomainEvent
from ..domain.value_objects import TenantId
from ..use_cases.interfaces import IEventRepository
from .models import EventLogModel


class EventRepository(IEventRepository):
    """
    Event repository implementation
    Persists events to event_log table (immutable, append-only)
    Source: INFRA-DEC-006 §3
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def persist_events(
        self,
        tenant_id: TenantId,
        events: List[DomainEvent]
    ) -> None:
        """
        Persist domain events to event_log table
        MUST be called within the same transaction as decision/workflow save

        Source: INFRA-DEC-006 §3.1 - Events are persisted synchronously,
        within the same transaction boundary as the decision/workflow.
        """
        if not events:
            return

        for event in events:
            event_model = EventLogModel(
                event_id=uuid4(),
                event_type=event.event_type,
                tenant_id=tenant_id.value,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                payload=event.to_payload(),
                metadata={
                    "trace_id": str(event.trace_id) if event.trace_id else None,
                    "caused_by_user_id": str(event.caused_by_user_id) if event.caused_by_user_id else None,
                    "source": event.source
                },
                occurred_at=event.occurred_at,
                recorded_at=datetime.utcnow(),
                schema_version=event.schema_version
            )
            self._session.add(event_model)

    async def find_by_aggregate(
        self,
        tenant_id: TenantId,
        aggregate_id: UUID,
        aggregate_type: str
    ) -> List[dict]:
        """
        Find events by aggregate (decision or workflow)
        Source: INFRA-DEC-006 §4 (Event Query)
        """
        stmt = (
            select(EventLogModel)
            .where(EventLogModel.tenant_id == tenant_id.value)
            .where(EventLogModel.aggregate_id == aggregate_id)
            .where(EventLogModel.aggregate_type == aggregate_type)
            .order_by(EventLogModel.occurred_at.asc())
        )

        result = await self._session.execute(stmt)
        events = result.scalars().all()

        return [
            {
                "event_id": str(e.event_id),
                "event_type": e.event_type,
                "aggregate_id": str(e.aggregate_id),
                "aggregate_type": e.aggregate_type,
                "payload": e.payload,
                "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                "recorded_at": e.recorded_at.isoformat() if e.recorded_at else None
            }
            for e in events
        ]
