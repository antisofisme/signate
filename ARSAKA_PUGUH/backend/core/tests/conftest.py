"""
Pytest Configuration

Fixtures and configuration for Core Service tests.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)

IMPORTANT: Bypass tests (test_bypass.py) require PostgreSQL with migrations applied.
SQLite does not support the immutability triggers.

To run bypass tests:
1. Set BYPASS_TEST_DATABASE_URL environment variable to PostgreSQL test database
2. Apply migrations 001-003 to the test database
3. Run: pytest core/tests/test_bypass.py -v
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from ..repositories.models import Base


# Test database URLs
# Unit tests: SQLite in-memory (fast, no triggers)
# Bypass tests: PostgreSQL with migrations (triggers required)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)

# PostgreSQL URL for bypass tests (requires migrations 001-003)
BYPASS_TEST_DATABASE_URL = os.getenv(
    "BYPASS_TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/infra_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
