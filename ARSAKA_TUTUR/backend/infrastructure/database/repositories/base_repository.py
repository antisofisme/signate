"""
Base repository with common database operations.
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from uuid import UUID
from datetime import datetime

import asyncpg

from ..connection import DatabasePool
from ....shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.

    Subclasses should implement entity-specific mapping.
    """

    def __init__(self, pool: DatabasePool, table_name: str):
        self.pool = pool
        self.table_name = table_name

    async def _execute(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> str:
        """Execute query."""
        return await self.pool.execute(query, *args, timeout=timeout)

    async def _fetch(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> List[asyncpg.Record]:
        """Fetch all rows."""
        return await self.pool.fetch(query, *args, timeout=timeout)

    async def _fetchrow(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> Optional[asyncpg.Record]:
        """Fetch single row."""
        return await self.pool.fetchrow(query, *args, timeout=timeout)

    async def _fetchval(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> Any:
        """Fetch single value."""
        return await self.pool.fetchval(query, *args, timeout=timeout)

    def _record_to_dict(self, record: asyncpg.Record) -> Dict[str, Any]:
        """Convert asyncpg Record to dict."""
        return dict(record)

    def _uuid_to_str(self, value: Any) -> Any:
        """Convert UUID to string."""
        if isinstance(value, UUID):
            return str(value)
        return value

    def _datetime_to_str(self, value: Any) -> Any:
        """Convert datetime to ISO string."""
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    async def count(
        self,
        tenant_id: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records with optional conditions.

        Args:
            tenant_id: Tenant ID
            conditions: Additional WHERE conditions

        Returns:
            Record count
        """
        query = f"SELECT COUNT(*) FROM {self.table_name} WHERE tenant_id = $1"
        args = [tenant_id]

        if conditions:
            for i, (key, value) in enumerate(conditions.items(), start=2):
                query += f" AND {key} = ${i}"
                args.append(value)

        return await self._fetchval(query, *args)

    async def exists(
        self,
        id: str,
        tenant_id: str
    ) -> bool:
        """
        Check if record exists.

        Args:
            id: Record ID
            tenant_id: Tenant ID

        Returns:
            True if exists
        """
        query = f"SELECT 1 FROM {self.table_name} WHERE id = $1 AND tenant_id = $2 LIMIT 1"
        result = await self._fetchval(query, id, tenant_id)
        return result is not None

    async def delete_soft(
        self,
        id: str,
        tenant_id: str,
        deleted_by: str
    ) -> bool:
        """
        Soft delete record.

        Args:
            id: Record ID
            tenant_id: Tenant ID
            deleted_by: Who deleted

        Returns:
            True if deleted
        """
        query = f"""
            UPDATE {self.table_name}
            SET is_deleted = TRUE, deleted_at = NOW(), deleted_by = $3, updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2 AND is_deleted = FALSE
        """
        result = await self._execute(query, id, tenant_id, deleted_by)
        return "UPDATE 1" in result


class CRUDMixin:
    """Mixin for basic CRUD operations."""

    async def get_by_id(
        self,
        id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get record by ID."""
        query = f"SELECT * FROM {self.table_name} WHERE id = $1 AND tenant_id = $2"
        row = await self._fetchrow(query, id, tenant_id)
        return self._record_to_dict(row) if row else None

    async def get_all(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all records for tenant."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        rows = await self._fetch(query, tenant_id, limit, offset)
        return [self._record_to_dict(row) for row in rows]
