"""
Health check endpoint.
"""

from fastapi import APIRouter

from ..schemas import HealthResponse, HealthChecks
from ...container import get_container
from ...shared.logging import get_logger
from ... import __version__

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns status of all dependent services.
    """
    container = await get_container()
    checks = await container.health_check()

    # Convert bool to status string
    check_results = HealthChecks(
        database="ok" if checks.get("database") else "error",
        qdrant="ok" if checks.get("qdrant", False) else "unavailable",
        redis="ok" if checks.get("redis", False) else "unavailable",
    )

    # Overall status
    status = "healthy" if checks.get("database") else "degraded"

    return HealthResponse(
        status=status,
        version=__version__,
        checks=check_results,
    )


@router.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "ARSAKA_TUTUR",
        "version": __version__,
        "docs": "/docs",
    }
