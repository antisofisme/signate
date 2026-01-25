"""
Audit repository.

Audit logs are APPEND-ONLY per CHAT-LAW-006.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_repository import BaseRepository
from ....core.entities import AuditEntry, AuditLog
from ....shared.logging import get_logger

logger = get_logger(__name__)


class AuditRepository(BaseRepository[AuditEntry]):
    """
    Repository for audit log operations.

    IMPORTANT: Audit logs are APPEND-ONLY per CHAT-LAW-006.
    No updates or deletes are allowed.
    """

    def __init__(self, pool):
        super().__init__(pool, "audit_logs")

    def _row_to_entity(self, row) -> AuditEntry:
        """Convert database row to AuditEntry."""
        return AuditEntry(
            id=row["id"],
            tenant_id=row["tenant_id"],
            actor_type=row["actor_type"],
            actor_id=row["actor_id"],
            action=row["action"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            request_id=row["request_id"],
            ip_address=row["ip_address"],
            details=row["details"] or {},
            status=row["status"],
            created_at=row["created_at"],
        )

    async def create(self, entry: AuditEntry) -> str:
        """
        Create audit log entry (APPEND-ONLY).

        Args:
            entry: AuditEntry to log

        Returns:
            Entry ID
        """
        query = """
            INSERT INTO audit_logs (
                id, tenant_id,
                actor_type, actor_id,
                action, resource_type, resource_id,
                request_id, ip_address,
                details, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """

        result = await self._fetchval(
            query,
            entry.id, entry.tenant_id,
            entry.actor_type, entry.actor_id,
            entry.action, entry.resource_type, entry.resource_id,
            entry.request_id, entry.ip_address,
            entry.details, entry.status
        )

        return str(result)

    async def get_logs(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AuditLog:
        """Query audit logs with filters."""
        conditions = ["tenant_id = $1"]
        args = [tenant_id]
        arg_idx = 2

        if filters:
            if "actor_id" in filters:
                conditions.append(f"actor_id = ${arg_idx}")
                args.append(filters["actor_id"])
                arg_idx += 1

            if "actor_type" in filters:
                conditions.append(f"actor_type = ${arg_idx}")
                args.append(filters["actor_type"])
                arg_idx += 1

            if "action" in filters:
                conditions.append(f"action = ${arg_idx}")
                args.append(filters["action"])
                arg_idx += 1

            if "resource_type" in filters:
                conditions.append(f"resource_type = ${arg_idx}")
                args.append(filters["resource_type"])
                arg_idx += 1

            if "resource_id" in filters:
                conditions.append(f"resource_id = ${arg_idx}")
                args.append(filters["resource_id"])
                arg_idx += 1

            if "status" in filters:
                conditions.append(f"status = ${arg_idx}")
                args.append(filters["status"])
                arg_idx += 1

        if start_date:
            conditions.append(f"created_at >= ${arg_idx}")
            args.append(start_date)
            arg_idx += 1

        if end_date:
            conditions.append(f"created_at <= ${arg_idx}")
            args.append(end_date)
            arg_idx += 1

        where_clause = " AND ".join(conditions)

        # Count total
        count_query = f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}"
        total = await self._fetchval(count_query, *args)

        # Fetch page
        args.extend([limit, offset])
        query = f"""
            SELECT * FROM audit_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${arg_idx} OFFSET ${arg_idx + 1}
        """

        rows = await self._fetch(query, *args)
        entries = [self._row_to_entity(row) for row in rows]

        return AuditLog(
            entries=entries,
            total=total,
            limit=limit,
            offset=offset,
            filters=filters or {},
        )

    async def get_by_request_id(
        self,
        request_id: str
    ) -> List[AuditEntry]:
        """Get all entries for a request."""
        query = """
            SELECT * FROM audit_logs
            WHERE request_id = $1
            ORDER BY created_at ASC
        """

        rows = await self._fetch(query, request_id)
        return [self._row_to_entity(row) for row in rows]

    async def get_user_activity(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[AuditEntry]:
        """Get recent activity for a user."""
        query = """
            SELECT * FROM audit_logs
            WHERE tenant_id = $1 AND actor_id = $2
            ORDER BY created_at DESC
            LIMIT $3
        """

        rows = await self._fetch(query, tenant_id, user_id, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_resource_history(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get audit history for a resource."""
        query = """
            SELECT * FROM audit_logs
            WHERE tenant_id = $1
              AND resource_type = $2
              AND resource_id = $3
            ORDER BY created_at DESC
            LIMIT $4
        """

        rows = await self._fetch(query, tenant_id, resource_type, resource_id, limit)
        return [self._row_to_entity(row) for row in rows]

    async def count_by_action(
        self,
        tenant_id: str,
        days: int = 30
    ) -> Dict[str, int]:
        """Count entries by action type."""
        query = """
            SELECT action, COUNT(*) as count
            FROM audit_logs
            WHERE tenant_id = $1
              AND created_at >= NOW() - INTERVAL '%s days'
            GROUP BY action
            ORDER BY count DESC
        """ % days

        rows = await self._fetch(query, tenant_id)
        return {row["action"]: row["count"] for row in rows}

    async def get_stats(
        self,
        tenant_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get audit log statistics."""
        query = """
            SELECT
                COUNT(*) as total_entries,
                COUNT(DISTINCT actor_id) as unique_actors,
                COUNT(DISTINCT action) as unique_actions,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) as failure_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
            FROM audit_logs
            WHERE tenant_id = $1
              AND created_at >= NOW() - INTERVAL '%s days'
        """ % days

        row = await self._fetchrow(query, tenant_id)

        return {
            "total_entries": row["total_entries"] or 0,
            "unique_actors": row["unique_actors"] or 0,
            "unique_actions": row["unique_actions"] or 0,
            "success_count": row["success_count"] or 0,
            "failure_count": row["failure_count"] or 0,
            "error_count": row["error_count"] or 0,
        }
