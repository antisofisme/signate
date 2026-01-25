"""
Database connection management using asyncpg.
"""

import asyncio
from typing import Optional, Any, List, Dict
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool, Connection

from ...config import DatabaseConfig, get_settings
from ...shared.logging import get_logger

logger = get_logger(__name__)


class DatabasePool:
    """
    Async PostgreSQL connection pool.

    Usage:
        pool = DatabasePool(config)
        await pool.connect()

        async with pool.acquire() as conn:
            result = await conn.fetch("SELECT * FROM tenants")

        await pool.close()
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or get_settings().database
        self._pool: Optional[Pool] = None

    @property
    def pool(self) -> Pool:
        """Get connection pool (raises if not connected)."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        return self._pool

    async def connect(self) -> None:
        """Initialize connection pool."""
        if self._pool is not None:
            return

        logger.info(f"Connecting to database at {self.config.host}:{self.config.port}")

        self._pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            min_size=self.config.min_connections,
            max_size=self.config.max_connections,
            command_timeout=60,
        )

        logger.info("Database pool connected")

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from pool.

        Usage:
            async with pool.acquire() as conn:
                await conn.fetch(...)
        """
        async with self.pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self):
        """
        Acquire a connection with transaction.

        Usage:
            async with pool.transaction() as conn:
                await conn.execute(...)
                # Auto-commit on exit, rollback on exception
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def execute(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> str:
        """Execute a query and return status."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    async def fetch(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> List[asyncpg.Record]:
        """Fetch all rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    async def fetchrow(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> Optional[asyncpg.Record]:
        """Fetch single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)

    async def fetchval(
        self,
        query: str,
        *args,
        column: int = 0,
        timeout: Optional[float] = None
    ) -> Any:
        """Fetch single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def executemany(
        self,
        query: str,
        args: List[tuple],
        timeout: Optional[float] = None
    ) -> None:
        """Execute query for multiple argument sets."""
        async with self.acquire() as conn:
            await conn.executemany(query, args, timeout=timeout)

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global pool instance
_pool: Optional[DatabasePool] = None


async def get_pool() -> DatabasePool:
    """Get global database pool instance."""
    global _pool
    if _pool is None:
        _pool = DatabasePool()
        await _pool.connect()
    return _pool


async def close_pool() -> None:
    """Close global database pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
