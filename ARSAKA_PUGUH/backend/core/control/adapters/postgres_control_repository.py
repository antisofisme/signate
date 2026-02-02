"""
PostgreSQL Control Repository Implementation
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..interfaces import IControlRepository
from ..domain import AuditRecord, SystemEvent


class PostgresControlRepository(IControlRepository):
    """PostgreSQL implementation of Control repository."""

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def list_audit(
        self,
        tenant_id: UUID,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[AuditRecord], int]:
        async with self._session_factory() as session:
            base_query = """
                SELECT
                    audit_id, tenant_id, operation_type, resource_type, resource_id,
                    actor_user_id, actor_role, action_status, reason_if_denied,
                    timestamp, trace_id
                FROM operations_audit
                WHERE tenant_id = :tenant_id
            """
            params = {"tenant_id": str(tenant_id)}

            if resource_type:
                base_query += " AND resource_type = :resource_type"
                params["resource_type"] = resource_type

            if action:
                base_query += " AND operation_type = :operation_type"
                params["operation_type"] = action

            count_query = f"SELECT COUNT(*) FROM ({base_query}) sub"
            result = await session.execute(text(count_query), params)
            total = result.scalar() or 0

            offset = (page - 1) * limit
            paginated_query = f"{base_query} ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await session.execute(text(paginated_query), params)
            rows = result.fetchall()

            records = [
                AuditRecord(
                    id=row.audit_id,
                    tenant_id=row.tenant_id,
                    operation_type=row.operation_type,
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    actor_user_id=row.actor_user_id,
                    actor_role=row.actor_role,
                    action_status=row.action_status,
                    reason_if_denied=row.reason_if_denied,
                    timestamp=row.timestamp,
                    trace_id=row.trace_id,
                )
                for row in rows
            ]

            return records, total

    async def get_audit(self, tenant_id: UUID, audit_id: UUID) -> Optional[AuditRecord]:
        async with self._session_factory() as session:
            query = """
                SELECT
                    audit_id, tenant_id, operation_type, resource_type, resource_id,
                    actor_user_id, actor_role, action_status, reason_if_denied,
                    timestamp, trace_id
                FROM operations_audit
                WHERE audit_id = :audit_id AND tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"audit_id": str(audit_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return AuditRecord(
                id=row.audit_id,
                tenant_id=row.tenant_id,
                operation_type=row.operation_type,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                actor_user_id=row.actor_user_id,
                actor_role=row.actor_role,
                action_status=row.action_status,
                reason_if_denied=row.reason_if_denied,
                timestamp=row.timestamp,
                trace_id=row.trace_id,
            )

    async def list_events(
        self,
        tenant_id: UUID,
        event_type: Optional[str] = None,
        aggregate_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[SystemEvent], int]:
        async with self._session_factory() as session:
            base_query = """
                SELECT
                    event_id, event_type, tenant_id, aggregate_id, aggregate_type,
                    payload, metadata, occurred_at, recorded_at, schema_version
                FROM event_log
                WHERE tenant_id = :tenant_id
            """
            params = {"tenant_id": str(tenant_id)}

            if event_type:
                base_query += " AND event_type = :event_type"
                params["event_type"] = event_type

            if aggregate_id:
                base_query += " AND aggregate_id = :aggregate_id"
                params["aggregate_id"] = str(aggregate_id)

            count_query = f"SELECT COUNT(*) FROM ({base_query}) sub"
            result = await session.execute(text(count_query), params)
            total = result.scalar() or 0

            offset = (page - 1) * limit
            paginated_query = f"{base_query} ORDER BY occurred_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await session.execute(text(paginated_query), params)
            rows = result.fetchall()

            events = [
                SystemEvent(
                    id=row.event_id,
                    event_type=row.event_type,
                    tenant_id=row.tenant_id,
                    aggregate_id=row.aggregate_id,
                    aggregate_type=row.aggregate_type,
                    payload=row.payload or {},
                    metadata=row.metadata,
                    occurred_at=row.occurred_at,
                    recorded_at=row.recorded_at,
                    schema_version=row.schema_version or "1.0",
                )
                for row in rows
            ]

            return events, total

    async def get_event(self, tenant_id: UUID, event_id: UUID) -> Optional[SystemEvent]:
        async with self._session_factory() as session:
            query = """
                SELECT
                    event_id, event_type, tenant_id, aggregate_id, aggregate_type,
                    payload, metadata, occurred_at, recorded_at, schema_version
                FROM event_log
                WHERE event_id = :event_id AND tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"event_id": str(event_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return SystemEvent(
                id=row.event_id,
                event_type=row.event_type,
                tenant_id=row.tenant_id,
                aggregate_id=row.aggregate_id,
                aggregate_type=row.aggregate_type,
                payload=row.payload or {},
                metadata=row.metadata,
                occurred_at=row.occurred_at,
                recorded_at=row.recorded_at,
                schema_version=row.schema_version or "1.0",
            )

    async def list_dlq_events(
        self, tenant_id: UUID, page: int = 1, limit: int = 20
    ) -> tuple[List[dict], int]:
        """List events in the dead-letter queue for a tenant."""
        async with self._session_factory() as session:
            # Query the event_dlq table joined with event_log for full event details
            base_query = """
                SELECT
                    d.dlq_entry_id,
                    d.event_id,
                    d.tenant_id,
                    d.failure_reason,
                    d.retry_count,
                    d.moved_at,
                    d.reprocessed_at,
                    e.event_type,
                    e.aggregate_id,
                    e.aggregate_type,
                    e.payload
                FROM event_dlq d
                LEFT JOIN event_log e ON d.event_id = e.event_id
                WHERE d.tenant_id = :tenant_id
                  AND d.reprocessed_at IS NULL
            """
            params = {"tenant_id": str(tenant_id)}

            # Count total
            count_query = f"SELECT COUNT(*) FROM ({base_query}) sub"
            result = await session.execute(text(count_query), params)
            total = result.scalar() or 0

            # Add pagination
            offset = (page - 1) * limit
            paginated_query = f"{base_query} ORDER BY d.moved_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await session.execute(text(paginated_query), params)
            rows = result.fetchall()

            dlq_events = [
                {
                    "dlq_entry_id": str(row.dlq_entry_id),
                    "event_id": str(row.event_id),
                    "tenant_id": str(row.tenant_id),
                    "event_type": row.event_type,
                    "aggregate_id": str(row.aggregate_id) if row.aggregate_id else None,
                    "aggregate_type": row.aggregate_type,
                    "payload": row.payload or {},
                    "failure_reason": row.failure_reason,
                    "retry_count": row.retry_count,
                    "moved_at": row.moved_at.isoformat() if row.moved_at else None,
                    "reprocessed_at": row.reprocessed_at.isoformat() if row.reprocessed_at else None,
                }
                for row in rows
            ]

            return dlq_events, total

    async def get_metrics(self, tenant_id: UUID) -> dict:
        async with self._session_factory() as session:
            # Decision counts
            decision_query = """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'ALLOWED' THEN 1 END) as allowed,
                    COUNT(CASE WHEN outcome = 'DENIED' THEN 1 END) as denied,
                    COUNT(CASE WHEN outcome = 'REQUIRE_APPROVAL' THEN 1 END) as pending
                FROM decisions
                WHERE tenant_id = :tenant_id
            """
            result = await session.execute(text(decision_query), {"tenant_id": str(tenant_id)})
            dec_row = result.fetchone()

            # Workflow counts
            workflow_query = """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN current_state = 'PENDING_APPROVAL' THEN 1 END) as pending,
                    COUNT(CASE WHEN current_state = 'APPROVED' THEN 1 END) as approved,
                    COUNT(CASE WHEN current_state = 'REJECTED' THEN 1 END) as rejected
                FROM workflows
                WHERE tenant_id = :tenant_id
            """
            result = await session.execute(text(workflow_query), {"tenant_id": str(tenant_id)})
            wf_row = result.fetchone()

            # Rule counts
            rule_query = """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'DRAFT' THEN 1 END) as draft,
                    COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active
                FROM rules
                WHERE tenant_id = :tenant_id AND deleted_at IS NULL
            """
            result = await session.execute(text(rule_query), {"tenant_id": str(tenant_id)})
            rule_row = result.fetchone()

            return {
                "decisions": {
                    "total": dec_row.total or 0,
                    "allowed": dec_row.allowed or 0,
                    "denied": dec_row.denied or 0,
                    "pending": dec_row.pending or 0,
                },
                "workflows": {
                    "total": wf_row.total or 0,
                    "pending": wf_row.pending or 0,
                    "approved": wf_row.approved or 0,
                    "rejected": wf_row.rejected or 0,
                },
                "rules": {
                    "total": rule_row.total or 0,
                    "draft": rule_row.draft or 0,
                    "active": rule_row.active or 0,
                },
            }

    async def get_decision_metrics(self, tenant_id: UUID) -> dict:
        metrics = await self.get_metrics(tenant_id)
        return metrics["decisions"]

    async def get_workflow_metrics(self, tenant_id: UUID) -> dict:
        metrics = await self.get_metrics(tenant_id)
        return metrics["workflows"]

    async def get_metrics_trends(self, tenant_id: UUID, period: str = "7d") -> List[dict]:
        """Get metrics trends over time."""
        # Parse period (7d, 30d, 90d)
        days = 7
        if period == "30d":
            days = 30
        elif period == "90d":
            days = 90

        async with self._session_factory() as session:
            # Get daily decision counts for the period
            query = """
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'ALLOWED' THEN 1 END) as allowed,
                    COUNT(CASE WHEN outcome = 'DENIED' THEN 1 END) as denied
                FROM decisions
                WHERE tenant_id = :tenant_id
                  AND created_at >= NOW() - INTERVAL '%s days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """ % days

            result = await session.execute(text(query), {"tenant_id": str(tenant_id)})
            rows = result.fetchall()

            return [
                {
                    "date": row.date.isoformat() if row.date else None,
                    "total": row.total or 0,
                    "allowed": row.allowed or 0,
                    "denied": row.denied or 0,
                }
                for row in rows
            ]

    async def get_dlq_event(
        self, tenant_id: UUID, dlq_entry_id: UUID
    ) -> Optional[dict]:
        """Get a single DLQ event by its entry ID."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    d.dlq_entry_id,
                    d.event_id,
                    d.tenant_id,
                    d.failure_reason,
                    d.retry_count,
                    d.moved_at,
                    d.reprocessed_at,
                    e.event_type,
                    e.aggregate_id,
                    e.aggregate_type,
                    e.payload
                FROM event_dlq d
                LEFT JOIN event_log e ON d.event_id = e.event_id
                WHERE d.dlq_entry_id = :dlq_entry_id AND d.tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"dlq_entry_id": str(dlq_entry_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return {
                "dlq_entry_id": str(row.dlq_entry_id),
                "event_id": str(row.event_id),
                "tenant_id": str(row.tenant_id),
                "event_type": row.event_type,
                "aggregate_id": str(row.aggregate_id) if row.aggregate_id else None,
                "aggregate_type": row.aggregate_type,
                "payload": row.payload or {},
                "failure_reason": row.failure_reason,
                "retry_count": row.retry_count,
                "moved_at": row.moved_at.isoformat() if row.moved_at else None,
                "reprocessed_at": row.reprocessed_at.isoformat() if row.reprocessed_at else None,
            }

    async def retry_dlq_event(
        self, tenant_id: UUID, dlq_entry_id: UUID
    ) -> dict:
        """
        Retry a DLQ event by resetting it for reprocessing.
        Updates the event_log to clear the DLQ status and reset for publishing.
        """
        async with self._session_factory() as session:
            # First get the DLQ entry to verify it exists and belongs to tenant
            dlq_entry = await self.get_dlq_event(tenant_id, dlq_entry_id)
            if not dlq_entry:
                raise ValueError(f"DLQ entry {dlq_entry_id} not found in tenant")

            if dlq_entry.get("reprocessed_at"):
                raise ValueError(f"DLQ entry {dlq_entry_id} has already been reprocessed")

            event_id = dlq_entry["event_id"]

            # Mark DLQ entry as reprocessed
            update_dlq_query = """
                UPDATE event_dlq
                SET reprocessed_at = NOW()
                WHERE dlq_entry_id = :dlq_entry_id AND tenant_id = :tenant_id
            """
            await session.execute(
                text(update_dlq_query),
                {"dlq_entry_id": str(dlq_entry_id), "tenant_id": str(tenant_id)}
            )

            # Reset the event in event_log for republishing
            # Clear dlq_at and reset published_at so poller picks it up again
            reset_event_query = """
                UPDATE event_log
                SET
                    dlq_at = NULL,
                    published_at = NULL,
                    publish_attempts = 0,
                    last_publish_error = NULL
                WHERE event_id = :event_id AND tenant_id = :tenant_id
            """
            await session.execute(
                text(reset_event_query),
                {"event_id": event_id, "tenant_id": str(tenant_id)}
            )

            await session.commit()

            return {
                "dlq_entry_id": str(dlq_entry_id),
                "event_id": event_id,
                "status": "queued_for_retry",
                "message": "Event has been queued for retry",
            }
