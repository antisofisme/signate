"""
API v1 Router
=============

Main router for API version 1 endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    organizations,
    content,
    devices,
    playlists,
    tags,
    commands,
    health,
    celery_monitor
)

api_router = APIRouter()

# Include all endpoint routers

# Health checks (no prefix, accessible at /api/v1/health)
api_router.include_router(
    health.router,
    tags=["health"]
)

# Authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    organizations.router,
    prefix="/organizations",
    tags=["organizations"]
)

api_router.include_router(
    tags.router,
    prefix="/tags",
    tags=["tags"]
)

api_router.include_router(
    content.router,
    prefix="/content",
    tags=["content"]
)

api_router.include_router(
    devices.router,
    prefix="/devices",
    tags=["devices"]
)

api_router.include_router(
    playlists.router,
    prefix="/playlists",
    tags=["playlists"]
)

api_router.include_router(
    commands.router,
    prefix="/commands",
    tags=["commands"]
)

api_router.include_router(
    celery_monitor.router,
    prefix="/celery",
    tags=["celery_monitor"]
)
