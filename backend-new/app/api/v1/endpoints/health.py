"""
Health Check API Endpoints
===========================

Comprehensive health status for all system dependencies.
Supports Docker, Kubernetes, and load balancer health checks.

Clean Architecture: Mostly API layer (health checks are simple status checks)
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.deps import get_db
from app.core.config import settings
from app.core.logging import StructuredLogger
from app.middleware.request_id import get_request_id

logger = StructuredLogger(__name__)
router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Basic Health Check",
    description="Simple health check for Docker/LB (no dependency checks)"
)
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Basic health check - returns 200 if service is up.

    **Used by**:
    - Docker health checks
    - Load balancers
    - Uptime monitors

    **Performance**: < 10ms
    **No Authentication Required**
    """
    request_id = get_request_id(request)

    logger.debug(
        "Basic health check requested",
        request_id=request_id
    )

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


@router.get(
    "/health/detailed",
    summary="Detailed Health Check",
    description="Full dependency health check (DB, Redis, Anthias)"
)
async def detailed_health_check(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Detailed health check - checks all dependencies.

    **Checks**:
    - Database connection (PostgreSQL) - CRITICAL
    - Redis connection - NON-CRITICAL (caching)
    - Anthias service - NON-CRITICAL (storage)

    **Returns**:
    - 200 OK if all dependencies healthy
    - 200 OK (degraded) if non-critical dependencies unhealthy
    - 503 Service Unavailable if critical dependencies unhealthy

    **Performance**: < 100ms
    **No Authentication Required**
    """
    request_id = get_request_id(request)

    logger.info(
        "Detailed health check requested",
        request_id=request_id
    )

    health_status = {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }

    # Check database connection (CRITICAL)
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "type": "postgresql",
            "critical": True
        }
        logger.debug(
            "Database health check: healthy",
            request_id=request_id
        )
    except Exception as e:
        logger.error(
            "Database health check failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "type": "postgresql",
            "critical": True,
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check Redis connection (NON-CRITICAL)
    try:
        import redis
        r = redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        r.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "type": "cache",
            "critical": False
        }
        logger.debug(
            "Redis health check: healthy",
            request_id=request_id
        )
    except Exception as e:
        logger.error(
            "Redis health check failed",
            request_id=request_id,
            error=str(e)
        )
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "type": "cache",
            "critical": False,
            "error": str(e),
            "impact": "Caching disabled, performance may be degraded"
        }
        # Redis is not critical, mark as degraded
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    # Check Anthias service (NON-CRITICAL)
    try:
        import requests
        response = requests.get(
            f"{settings.ANTHIAS_INTERNAL_URL}/",
            timeout=5
        )
        if response.status_code == 200:
            health_status["checks"]["anthias"] = {
                "status": "healthy",
                "type": "storage",
                "critical": False
            }
            logger.debug(
                "Anthias health check: healthy",
                request_id=request_id
            )
        else:
            health_status["checks"]["anthias"] = {
                "status": "degraded",
                "type": "storage",
                "critical": False,
                "http_status": response.status_code
            }
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
    except requests.exceptions.Timeout:
        logger.warning(
            "Anthias health check timed out",
            request_id=request_id
        )
        health_status["checks"]["anthias"] = {
            "status": "unavailable",
            "type": "storage",
            "critical": False,
            "error": "Connection timeout",
            "impact": "File uploads will fail"
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        logger.warning(
            "Anthias health check failed",
            request_id=request_id,
            error=str(e)
        )
        health_status["checks"]["anthias"] = {
            "status": "unavailable",
            "type": "storage",
            "critical": False,
            "error": str(e),
            "impact": "File uploads will fail"
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    # Determine HTTP status code
    if health_status["status"] == "unhealthy":
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.error(
            "Detailed health check: unhealthy",
            request_id=request_id,
            checks=health_status["checks"]
        )
    elif health_status["status"] == "degraded":
        http_status = status.HTTP_200_OK  # Still operational
        logger.warning(
            "Detailed health check: degraded",
            request_id=request_id,
            checks=health_status["checks"]
        )
    else:
        http_status = status.HTTP_200_OK
        logger.info(
            "Detailed health check: healthy",
            request_id=request_id
        )

    return JSONResponse(
        status_code=http_status,
        content={
            "success": True,
            "data": health_status,
            "meta": {
                "request_id": request_id,
                "version": "1.0.0"
            }
        }
    )


@router.get(
    "/health/ready",
    summary="Readiness Probe",
    description="Kubernetes readiness probe (checks critical dependencies)"
)
async def readiness_check(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Readiness probe - checks if service is ready to accept traffic.

    **Used by**: Kubernetes readiness probes
    **Checks**: Database connection only (critical dependency)

    **Returns**:
    - 200 OK if service is ready
    - 503 Service Unavailable if not ready

    **Performance**: < 50ms
    **No Authentication Required**
    """
    request_id = get_request_id(request)

    logger.debug(
        "Readiness check requested",
        request_id=request_id
    )

    try:
        # Check database connection
        db.execute(text("SELECT 1"))

        logger.debug(
            "Readiness check: ready",
            request_id=request_id
        )

        return {
            "status": "ready",
            "service": settings.PROJECT_NAME
        }
    except Exception as e:
        logger.error(
            "Readiness check failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "data": {
                    "status": "not_ready",
                    "service": settings.PROJECT_NAME,
                    "error": "Database connection failed"
                },
                "meta": {
                    "request_id": request_id,
                    "version": "1.0.0"
                }
            }
        )


@router.get(
    "/health/live",
    summary="Liveness Probe",
    description="Kubernetes liveness probe (no dependency checks)"
)
async def liveness_check(request: Request) -> Dict[str, Any]:
    """
    Liveness probe - checks if service is alive.

    **Used by**: Kubernetes liveness probes
    **Checks**: None (only checks if process is running)

    Returns 200 OK if service is alive.

    **Performance**: < 10ms
    **No Authentication Required**
    """
    request_id = get_request_id(request)

    logger.debug(
        "Liveness check requested",
        request_id=request_id
    )

    return {
        "status": "alive",
        "service": settings.PROJECT_NAME
    }
