"""
Unit of Work Implementation

Transaction boundary management for Core service.
Source: INFRA-LAY3-002 §2.3 (Decision Creation Transaction)
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from ..use_cases.interfaces import IUnitOfWork


class UnitOfWork(IUnitOfWork):
    """
    Unit of Work implementation using SQLAlchemy async sessions
    Manages transaction boundaries for atomic operations
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self._transaction = None

    async def __aenter__(self):
        """
        Begin transaction
        Source: INFRA-LAY3-002 §2.3 (BEGIN TRANSACTION)
        """
        self._transaction = await self._session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Commit or rollback transaction
        Source: INFRA-LAY3-002 §2.3 (COMMIT / ROLLBACK)
        """
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self):
        """
        Commit transaction
        All inserts (decision, workflow, event_log, idempotency) committed atomically
        """
        if self._transaction:
            await self._transaction.commit()
            self._transaction = None

    async def rollback(self):
        """
        Rollback transaction
        All operations rolled back (no partial state)
        """
        if self._transaction:
            await self._transaction.rollback()
            self._transaction = None


class SessionFactory:
    """
    Factory for creating database sessions
    Manages database engine and session lifecycle

    Phase A: Configurable via environment variables
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = None,
        max_overflow: int = None,
        pool_timeout: int = None,
        pool_recycle: int = None,
        pool_pre_ping: bool = None
    ):
        """
        Initialize session factory with configurable pool settings

        Args:
            database_url: PostgreSQL connection string (async)
                         Example: postgresql+asyncpg://user:pass@host:port/db
            pool_size: Number of permanent connections (default: from env or 2)
            max_overflow: Max additional connections (default: from env or 3)
            pool_timeout: Connection timeout in seconds (default: from env or 10)
            pool_recycle: Connection recycle time in seconds (default: from env or 3600)
            pool_pre_ping: Test connection before use (default: from env or True)

        Phase A defaults (if not specified):
            pool_size=2, max_overflow=3, pool_timeout=10, pool_recycle=3600, pool_pre_ping=True

        Phase B defaults (if infrastructure enabled):
            pool_size=10, max_overflow=10, pool_timeout=30, pool_recycle=3600, pool_pre_ping=True
        """
        # Read from environment variables if not explicitly passed
        if pool_size is None:
            pool_size = int(os.getenv("POOL_SIZE", "2"))

        if max_overflow is None:
            max_overflow = int(os.getenv("MAX_OVERFLOW", "3"))

        if pool_timeout is None:
            pool_timeout = int(os.getenv("POOL_TIMEOUT", "10"))

        if pool_recycle is None:
            pool_recycle = int(os.getenv("POOL_RECYCLE", "3600"))

        if pool_pre_ping is None:
            pool_pre_ping_str = os.getenv("POOL_PRE_PING", "true").lower()
            pool_pre_ping = pool_pre_ping_str in ("true", "1", "yes")

        # Create async engine with configurable pool
        self._engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging (debug)
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle
        )

        # Create session maker
        self._session_maker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Log pool configuration
        print(f"✅ Database pool configured: pool_size={pool_size}, max_overflow={max_overflow}, "
              f"timeout={pool_timeout}s, recycle={pool_recycle}s, pre_ping={pool_pre_ping}")

    async def create_session(self) -> AsyncSession:
        """Create new database session"""
        return self._session_maker()

    async def close(self):
        """Close database engine and dispose connections"""
        await self._engine.dispose()
