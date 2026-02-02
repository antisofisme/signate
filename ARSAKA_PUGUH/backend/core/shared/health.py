"""
Health Check Utilities

Production-ready health checks for database, cache, and external services.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a single component"""
    name: str
    status: HealthStatus
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """Overall system health"""
    status: HealthStatus
    timestamp: str
    version: str
    environment: str
    components: List[ComponentHealth]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "version": self.version,
            "environment": self.environment,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.components
            ],
        }


class HealthChecker:
    """
    Production health checker.

    Performs actual connectivity tests for all dependencies.
    """

    def __init__(
        self,
        version: str = "1.0.0",
        environment: str = "unknown",
    ):
        self.version = version
        self.environment = environment

    async def check_database(
        self,
        session: AsyncSession,
        timeout_seconds: float = 5.0,
    ) -> ComponentHealth:
        """
        Check database connectivity.

        Executes a simple query to verify connection.
        """
        start = datetime.utcnow()
        try:
            # Execute simple query with timeout
            result = await asyncio.wait_for(
                session.execute(text("SELECT 1")),
                timeout=timeout_seconds,
            )
            row = result.fetchone()

            latency = (datetime.utcnow() - start).total_seconds() * 1000

            if row and row[0] == 1:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    latency_ms=round(latency, 2),
                    message="Connected",
                )
            else:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=round(latency, 2),
                    message="Query returned unexpected result",
                )

        except asyncio.TimeoutError:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection timeout after {timeout_seconds}s",
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)}",
            )

    async def check_redis(
        self,
        redis_client: Optional[Any] = None,
        timeout_seconds: float = 2.0,
    ) -> ComponentHealth:
        """
        Check Redis connectivity.

        Executes PING command to verify connection.
        """
        if redis_client is None:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Disabled (not configured)",
            )

        start = datetime.utcnow()
        try:
            # Execute PING with timeout
            result = await asyncio.wait_for(
                redis_client.ping(),
                timeout=timeout_seconds,
            )

            latency = (datetime.utcnow() - start).total_seconds() * 1000

            if result:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    latency_ms=round(latency, 2),
                    message="Connected",
                )
            else:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=round(latency, 2),
                    message="PING returned False",
                )

        except asyncio.TimeoutError:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection timeout after {timeout_seconds}s",
            )
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)}",
            )

    async def check_external_api(
        self,
        name: str,
        url: str,
        timeout_seconds: float = 5.0,
    ) -> ComponentHealth:
        """
        Check external API connectivity.

        Makes HTTP request to verify the API is reachable.
        """
        try:
            import httpx

            start = datetime.utcnow()

            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.get(url)

            latency = (datetime.utcnow() - start).total_seconds() * 1000

            if response.status_code < 400:
                return ComponentHealth(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}",
                )
            else:
                return ComponentHealth(
                    name=name,
                    status=HealthStatus.DEGRADED,
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}",
                )

        except Exception as e:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Request failed: {str(e)}",
            )

    async def check_all(
        self,
        session: Optional[AsyncSession] = None,
        redis_client: Optional[Any] = None,
        external_apis: Optional[Dict[str, str]] = None,
    ) -> SystemHealth:
        """
        Run all health checks and return system health.

        Args:
            session: Database session for DB health check
            redis_client: Redis client for cache health check
            external_apis: Dict of {name: url} for external API checks

        Returns:
            SystemHealth with aggregated status
        """
        components: List[ComponentHealth] = []

        # Check database
        if session:
            db_health = await self.check_database(session)
            components.append(db_health)

        # Check Redis
        redis_health = await self.check_redis(redis_client)
        components.append(redis_health)

        # Check external APIs
        if external_apis:
            for name, url in external_apis.items():
                api_health = await self.check_external_api(name, url)
                components.append(api_health)

        # Determine overall status
        statuses = [c.status for c in components]

        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return SystemHealth(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            version=self.version,
            environment=self.environment,
            components=components,
        )


# Readiness check (for Kubernetes)
async def readiness_check(session: AsyncSession) -> bool:
    """
    Kubernetes readiness probe.

    Returns True if the service is ready to accept traffic.
    """
    checker = HealthChecker()
    db_health = await checker.check_database(session)
    return db_health.status == HealthStatus.HEALTHY


# Liveness check (for Kubernetes)
async def liveness_check() -> bool:
    """
    Kubernetes liveness probe.

    Returns True if the service is alive (process running).
    """
    return True
