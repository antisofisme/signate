"""
Database Connection Pool Configuration

Optimized connection pool settings for high throughput.

CRITICAL: This is CONFIGURATION ONLY - does NOT modify Phase 1 database logic.

Source: Phase 2 Design & Execution Plan - Section 4.2
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool

from infrastructure.logging import get_logger
from infrastructure.metrics import database_pool_active_connections, PROMETHEUS_AVAILABLE


logger = get_logger(__name__)


def create_optimized_engine(
    database_url: str,
    pool_size: int = 20,
    max_overflow: int = 10,
    pool_timeout: float = 30.0,
    pool_recycle: int = 3600,
    pool_pre_ping: bool = True,
    echo_pool: bool = False
) -> AsyncEngine:
    """
    Create SQLAlchemy async engine with optimized connection pool

    Configuration is ADDITIVE - does not change Phase 1 database schema or logic.

    Args:
        database_url: PostgreSQL connection URL
        pool_size: Core pool size (connections kept alive)
        max_overflow: Additional connections during peak load
        pool_timeout: Seconds to wait for connection from pool
        pool_recycle: Recycle connections after N seconds
        pool_pre_ping: Test connections before using (detect stale)
        echo_pool: Log pool events (debugging)

    Returns:
        Configured AsyncEngine instance

    Pool Sizing Guidelines:
    - pool_size: Number of concurrent requests * 1.5
    - max_overflow: pool_size * 0.5
    - Total max connections: pool_size + max_overflow

    Example:
        # Phase 1 (default)
        engine = create_async_engine(database_url)

        # Phase 2 (optimized)
        engine = create_optimized_engine(
            database_url,
            pool_size=20,
            max_overflow=10
        )

    Source: Phase 2 Design & Execution Plan - Section 4.2
    """
    # Parse configuration from environment (override defaults)
    pool_size = int(os.getenv("DB_POOL_SIZE", pool_size))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", max_overflow))
    pool_timeout = float(os.getenv("DB_POOL_TIMEOUT", pool_timeout))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", pool_recycle))

    logger.info(
        "Creating optimized database engine",
        extra={
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle,
            "pool_pre_ping": pool_pre_ping
        }
    )

    # Create engine with optimized pool settings
    engine = create_async_engine(
        database_url,
        # Connection pool settings
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
        # Logging
        echo=False,  # Don't log SQL queries (use tracing instead)
        echo_pool=echo_pool,  # Log pool events if debugging
        # Connection arguments
        connect_args={
            "server_settings": {
                "application_name": "core-service-phase2"
            }
        }
    )

    logger.info(
        "Database engine created successfully",
        extra={
            "total_max_connections": pool_size + max_overflow,
            "url": database_url.split("@")[1] if "@" in database_url else database_url
        }
    )

    return engine


def get_pool_stats(engine: AsyncEngine) -> dict:
    """
    Get connection pool statistics

    Args:
        engine: SQLAlchemy AsyncEngine

    Returns:
        Dictionary with pool stats:
        - size: Core pool size
        - checked_in: Available connections
        - checked_out: Active connections
        - overflow: Overflow connections created
        - total: Total connections (checked_in + checked_out)

    Example:
        stats = get_pool_stats(engine)
        print(f"Active connections: {stats['checked_out']}")

        # Update Prometheus gauge
        database_pool_active_connections.set(stats['checked_out'])
    """
    pool = engine.pool

    # Check if pool is NullPool (no pooling)
    if isinstance(pool, NullPool):
        return {
            "size": 0,
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "total": 0,
            "pooling_enabled": False
        }

    stats = {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.checkedin() + pool.checkedout(),
        "pooling_enabled": True
    }

    # Update Prometheus metric
    if database_pool_active_connections:
        database_pool_active_connections.set(stats["checked_out"])

    return stats


def log_pool_stats(engine: AsyncEngine):
    """
    Log current pool statistics

    Args:
        engine: SQLAlchemy AsyncEngine

    Example:
        # In periodic task or health check
        log_pool_stats(engine)
    """
    stats = get_pool_stats(engine)

    logger.info(
        "Database connection pool stats",
        extra=stats
    )


# Connection pool health check
def is_pool_healthy(engine: AsyncEngine, threshold: float = 0.8) -> bool:
    """
    Check if connection pool is healthy

    Args:
        engine: SQLAlchemy AsyncEngine
        threshold: Utilization threshold (0.0-1.0)

    Returns:
        True if pool utilization < threshold, False otherwise

    Example:
        if not is_pool_healthy(engine, threshold=0.8):
            logger.warning("Connection pool approaching capacity")
    """
    stats = get_pool_stats(engine)

    if not stats["pooling_enabled"]:
        return True

    # Calculate utilization
    total_capacity = stats["size"] + stats["overflow"]
    if total_capacity == 0:
        return True

    utilization = stats["total"] / total_capacity

    is_healthy = utilization < threshold

    if not is_healthy:
        logger.warning(
            "Connection pool utilization high",
            extra={
                "utilization": f"{utilization:.2%}",
                "threshold": f"{threshold:.2%}",
                "active_connections": stats["checked_out"],
                "total_capacity": total_capacity
            }
        )

    return is_healthy
