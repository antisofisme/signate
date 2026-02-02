"""
Monitoring API Routes

REST API endpoints for health checks and metrics.
"""

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

from ..monitoring.health import (
    check_all_services,
    liveness_check,
    readiness_check,
    HealthStatus,
)

router = APIRouter(tags=["monitoring"])


# ============================================================================
# Response Models
# ============================================================================


class HealthCheckResult(BaseModel):
    """Individual health check result."""
    name: str
    status: str
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    details: dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Overall health response."""
    status: str
    version: str
    uptime_seconds: float
    checks: list[HealthCheckResult]
    timestamp: str


# ============================================================================
# Health Endpoints
# ============================================================================


@router.get("/health")
async def health_check() -> HealthResponse:
    """
    Comprehensive health check for all services.

    Returns overall health status and individual service checks.
    """
    health = await check_all_services()

    return HealthResponse(
        status=health.status.value,
        version=health.version,
        uptime_seconds=health.uptime_seconds,
        checks=[
            HealthCheckResult(
                name=c.name,
                status=c.status.value,
                message=c.message,
                latency_ms=c.latency_ms,
                details=c.details,
            )
            for c in health.checks
        ],
        timestamp=health.checked_at.isoformat(),
    )


@router.get("/health/live")
async def liveness():
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the service is alive.
    """
    result = await liveness_check()
    return result


@router.get("/health/ready")
async def readiness():
    """
    Kubernetes readiness probe endpoint.

    Returns 200 if the service is ready to accept requests.
    Returns 503 if not ready.
    """
    result = await readiness_check()

    if result["status"] == "ready":
        return result
    else:
        return Response(
            content=str(result),
            status_code=503,
            media_type="application/json",
        )


# ============================================================================
# Metrics Endpoints
# ============================================================================


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from ..monitoring.metrics import metrics

        return PlainTextResponse(
            content=generate_latest(metrics).decode("utf-8"),
            media_type=CONTENT_TYPE_LATEST,
        )
    except ImportError:
        return PlainTextResponse(
            content="# prometheus_client not installed",
            status_code=501,
        )


@router.get("/metrics/json")
async def metrics_json():
    """
    Metrics in JSON format.

    Alternative to Prometheus format for debugging.
    """
    try:
        from ..monitoring.metrics import (
            request_counter,
            decision_counter,
            validation_counter,
            retrieval_counter,
            export_counter,
            job_counter,
        )

        # Collect sample metrics
        # Note: In production, you'd want more comprehensive metric collection
        return {
            "collected_at": datetime.utcnow().isoformat(),
            "note": "Use /metrics for full Prometheus format",
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Debug Endpoints
# ============================================================================


@router.get("/debug/config")
async def debug_config():
    """
    Debug endpoint showing current configuration.

    WARNING: Should be protected or disabled in production.
    """
    from ..runtime.config import get_config

    config = get_config()

    # Return safe subset of config
    return {
        "host": config.host,
        "port": config.port,
        "enable_docs": config.enable_docs,
        "enable_semantic_search": config.enable_semantic_search,
        "vector_store": config.vector_store,
        "cache": config.cache,
        "embedding_service": config.embedding_service,
        "features": {
            "rabbitmq": config.feature_rabbitmq_enabled,
            "meilisearch": config.feature_meilisearch_enabled,
            "redis_enhanced": config.feature_redis_enhanced_cache,
        },
    }


@router.get("/debug/routes")
async def debug_routes():
    """
    Debug endpoint listing all registered routes.
    """
    from fastapi import FastAPI
    from fastapi.routing import APIRoute

    # This requires access to the app instance
    # For now, return a placeholder
    return {
        "note": "Route listing requires app context",
        "endpoints": [
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
            "/api/v1/*",
        ],
    }
