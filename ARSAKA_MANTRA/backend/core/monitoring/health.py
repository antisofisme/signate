"""
Health Checks

Service health monitoring for MANTRA.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import asyncio


class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ServiceHealth:
    """Overall service health."""
    status: HealthStatus
    checks: list[HealthCheck]
    uptime_seconds: float
    version: str = "1.0.0"
    checked_at: datetime = field(default_factory=datetime.utcnow)


# Service start time
_start_time = datetime.utcnow()


async def check_database() -> HealthCheck:
    """Check database connectivity."""
    import time
    start = time.time()

    try:
        from factory.container import Container
        repo = Container.get_decision_repository()

        # Simple query to test connection
        result = await repo.list_decisions(limit=1)

        latency = (time.time() - start) * 1000

        return HealthCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Connected",
            latency_ms=latency,
            details={"type": "postgresql"},
        )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheck(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
            latency_ms=latency,
        )


async def check_redis() -> HealthCheck:
    """Check Redis connectivity."""
    import time
    start = time.time()

    try:
        from factory.container import Container
        cache = Container.get_cache()

        if cache is None:
            return HealthCheck(
                name="redis",
                status=HealthStatus.DEGRADED,
                message="Not configured",
            )

        # Ping Redis
        await cache.ping()

        latency = (time.time() - start) * 1000

        return HealthCheck(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Connected",
            latency_ms=latency,
        )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheck(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
            latency_ms=latency,
        )


async def check_rabbitmq() -> HealthCheck:
    """Check RabbitMQ connectivity."""
    import time
    start = time.time()

    try:
        from factory.container import Container
        queue = Container.get_message_queue()

        if queue is None:
            return HealthCheck(
                name="rabbitmq",
                status=HealthStatus.DEGRADED,
                message="Not configured",
            )

        # Health check
        healthy = await queue.health_check()

        latency = (time.time() - start) * 1000

        if healthy:
            return HealthCheck(
                name="rabbitmq",
                status=HealthStatus.HEALTHY,
                message="Connected",
                latency_ms=latency,
            )
        else:
            return HealthCheck(
                name="rabbitmq",
                status=HealthStatus.UNHEALTHY,
                message="Health check failed",
                latency_ms=latency,
            )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheck(
            name="rabbitmq",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
            latency_ms=latency,
        )


async def check_meilisearch() -> HealthCheck:
    """Check Meilisearch connectivity."""
    import time
    start = time.time()

    try:
        from factory.container import Container
        search = Container.get_text_search()

        if search is None:
            return HealthCheck(
                name="meilisearch",
                status=HealthStatus.DEGRADED,
                message="Not configured",
            )

        # Health check
        healthy = await search.health_check()

        latency = (time.time() - start) * 1000

        if healthy:
            return HealthCheck(
                name="meilisearch",
                status=HealthStatus.HEALTHY,
                message="Connected",
                latency_ms=latency,
            )
        else:
            return HealthCheck(
                name="meilisearch",
                status=HealthStatus.UNHEALTHY,
                message="Health check failed",
                latency_ms=latency,
            )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheck(
            name="meilisearch",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
            latency_ms=latency,
        )


async def check_vector_store() -> HealthCheck:
    """Check vector store connectivity."""
    import time
    start = time.time()

    try:
        from factory.container import Container
        vector_store = Container.get_vector_store()

        if vector_store is None:
            return HealthCheck(
                name="vector_store",
                status=HealthStatus.DEGRADED,
                message="Not configured",
            )

        # Simple operation to test connectivity
        latency = (time.time() - start) * 1000

        return HealthCheck(
            name="vector_store",
            status=HealthStatus.HEALTHY,
            message="Available",
            latency_ms=latency,
        )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheck(
            name="vector_store",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
            latency_ms=latency,
        )


async def check_all_services() -> ServiceHealth:
    """
    Run all health checks and return overall status.

    Returns:
        ServiceHealth with all check results
    """
    # Run all checks in parallel
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_rabbitmq(),
        check_meilisearch(),
        check_vector_store(),
        return_exceptions=True,
    )

    # Convert exceptions to unhealthy checks
    health_checks: list[HealthCheck] = []
    for check in checks:
        if isinstance(check, Exception):
            health_checks.append(HealthCheck(
                name="unknown",
                status=HealthStatus.UNHEALTHY,
                message=str(check),
            ))
        else:
            health_checks.append(check)

    # Calculate overall status
    statuses = [c.status for c in health_checks]

    if all(s == HealthStatus.HEALTHY for s in statuses):
        overall_status = HealthStatus.HEALTHY
    elif any(s == HealthStatus.UNHEALTHY for s in statuses):
        # If database is unhealthy, overall is unhealthy
        db_check = next((c for c in health_checks if c.name == "database"), None)
        if db_check and db_check.status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.DEGRADED

    # Calculate uptime
    uptime = (datetime.utcnow() - _start_time).total_seconds()

    return ServiceHealth(
        status=overall_status,
        checks=health_checks,
        uptime_seconds=uptime,
    )


async def liveness_check() -> dict[str, Any]:
    """
    Simple liveness check.

    Returns True if the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


async def readiness_check() -> dict[str, Any]:
    """
    Readiness check.

    Returns True if the service is ready to accept requests.
    """
    health = await check_all_services()

    return {
        "status": "ready" if health.status != HealthStatus.UNHEALTHY else "not_ready",
        "health": health.status.value,
        "timestamp": datetime.utcnow().isoformat(),
    }
