"""
Health Check Endpoints

Provides comprehensive health status for all system dependencies.

Quick Wins Pattern Compliant:
- StructuredLogger with request_id tracking
- success_response wrapper for responses
- Standardized response formats
- Fast response times (<100ms) for monitoring
- Supports Kubernetes liveness/readiness probes

Endpoints:
- GET /health - Basic health check (Docker/LB)
- GET /health/detailed - Full dependency health check
- GET /health/ready - Kubernetes readiness probe
- GET /health/live - Kubernetes liveness probe
"""

from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.core.logging import StructuredLogger
from app.core.config import settings
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response
import redis
import requests


router = APIRouter(tags=["Health"])
logger = StructuredLogger(__name__)


@router.get("/health")
async def health_check(request: Request):
    """
    Simple health check - returns 200 if service is up

    Used by Docker health checks and load balancers.
    Returns immediately without checking dependencies.

    **Performance:** < 10ms
    **No Authentication Required**
    """
    request_id = get_request_id(request)

    logger.debug(
        "Basic health check requested",
        request_id=request_id
    )

    return success_response(
        data={
            "status": "healthy",
            "service": "backend-api",
            "version": "1.0.0"
        },
        request_id=request_id
    )


@router.get("/health/detailed")
async def detailed_health_check(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Detailed health check - checks all dependencies

    Checks:
    - Database connection (PostgreSQL)
    - Redis connection
    - Anthias service availability

    Returns:
    - 200 OK if all dependencies are healthy
    - 200 OK (degraded) if non-critical dependencies are unhealthy
    - 503 Service Unavailable if any critical dependency is unhealthy

    **Performance:** < 100ms
    **No Authentication Required**
    """
    request_id = get_request_id(request)

    logger.info(
        "Detailed health check requested",
        request_id=request_id
    )

    health_status = {
        "service": "backend-api",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }

    # Check database connection
    try:
        db.execute("SELECT 1")
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

    # Check Redis connection
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
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
        # Redis is not critical, mark as degraded instead of unhealthy
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    # Check Anthias service (optional)
    try:
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
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.error(
            "Detailed health check: unhealthy",
            request_id=request_id,
            checks=health_status["checks"]
        )
    elif health_status["status"] == "degraded":
        status_code = status.HTTP_200_OK  # Still operational, just degraded
        logger.warning(
            "Detailed health check: degraded",
            request_id=request_id,
            checks=health_status["checks"]
        )
    else:
        status_code = status.HTTP_200_OK
        logger.info(
            "Detailed health check: healthy",
            request_id=request_id
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": health_status,
            "meta": {
                "request_id": request_id,
                "version": "1.0.0"
            }
        }
    )


@router.get("/health/ready")
async def readiness_check(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Readiness probe - checks if service is ready to accept traffic

    Used by Kubernetes readiness probes.
    Only checks critical dependencies (database).

    Returns:
    - 200 OK if service is ready
    - 503 Service Unavailable if not ready

    **Performance:** < 50ms
    **No Authentication Required**
    """
    request_id = get_request_id(request)

    logger.debug(
        "Readiness check requested",
        request_id=request_id
    )

    try:
        # Check database connection
        db.execute("SELECT 1")

        logger.debug(
            "Readiness check: ready",
            request_id=request_id
        )

        return success_response(
            data={
                "status": "ready",
                "service": "backend-api"
            },
            request_id=request_id
        )
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
                    "service": "backend-api",
                    "error": "Database connection failed"
                },
                "meta": {
                    "request_id": request_id,
                    "version": "1.0.0"
                }
            }
        )


@router.get("/health/live")
async def liveness_check(request: Request):
    """
    Liveness probe - checks if service is alive

    Used by Kubernetes liveness probes.
    Does not check dependencies, only checks if process is running.

    Returns 200 OK if service is alive.

    **Performance:** < 10ms
    **No Authentication Required**
    """
    request_id = get_request_id(request)

    logger.debug(
        "Liveness check requested",
        request_id=request_id
    )

    return success_response(
        data={
            "status": "alive",
            "service": "backend-api"
        },
        request_id=request_id
    )
