"""
SMART TV DIGITAL SIGNAGE - BACKEND API
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.database import engine, check_db_connection

# Import models to register them with SQLAlchemy Base
from app.models import (
    User, Device, Content, Tag, DeviceTag,
    ContentAssignment, Schedule, FirebirdConfig, DeviceLog,
    Playlist, PlaylistContent, PlaylistAssignment,
    ActivityLog, ActivityAction, EntityType
)

# =============================================================================
# QUICK WINS: Structured Logging Setup
# =============================================================================
from app.core.logging import setup_logging

# Setup structured logging (JSON format in production, text in development)
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart TV Digital Signage - Backend API for managing TV/Monitor devices and content",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
)

# =============================================================================
# QUICK WINS: Request ID Tracking Middleware
# =============================================================================
from app.middleware.request_id import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)
logger.info("✓ Request ID tracking middleware registered")

# CORS Middleware
if settings.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled for origins: {settings.CORS_ORIGINS}")

# =============================================================================
# API ROUTERS
# =============================================================================
from app.api import auth, devices, content, client, tags, logs, websocket, speedtest, playlists, firebird, activities
from app.api import settings as settings_api  # Renamed to avoid conflict with app.core.config.settings

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(content.router, prefix="/api/content", tags=["Content"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["Playlists"])
app.include_router(client.router, prefix="/api/client", tags=["Client"])
app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])
app.include_router(settings_api.router, prefix="/api", tags=["Settings"])
app.include_router(activities.router, prefix="/api", tags=["Activity Logs"])  # ✅ Enabled
app.include_router(logs.router, prefix="/api", tags=["Device Logs"])
app.include_router(websocket.router, prefix="/api", tags=["WebSocket"])
app.include_router(speedtest.router, tags=["Speed Test"])
app.include_router(firebird.router, tags=["Firebird Integration"])

# Quick Wins Demo Router (only in DEBUG mode)
if settings.DEBUG:
    from app.api import quickwins_demo
    app.include_router(quickwins_demo.router, prefix="/api/demo", tags=["Quick Wins Demo"])
    logger.info("✓ Quick Wins demo endpoints registered (DEBUG mode)")

# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "message": "Smart TV Digital Signage - Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.ENABLE_API_DOCS else "disabled",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected",  # Will add actual DB check in Phase 1.3
        "redis": "connected",  # Will add actual Redis check later
    }


@app.get("/api/ping")
async def ping():
    """Ping endpoint for monitoring"""
    return {"ping": "pong"}


# =============================================================================
# QUICK WINS: Exception Handlers
# =============================================================================
from app.core.exceptions import (
    APIException,
    register_exception_handlers
)

# Register all Quick Wins exception handlers
register_exception_handlers(app)
logger.info("✓ Quick Wins exception handlers registered")

# Keep legacy error handlers for non-Quick Wins exceptions
@app.exception_handler(404)
async def not_found_handler(request, exc):
    # Preserve HTTPException detail messages from application logic
    # Only use generic message for routing 404s
    if hasattr(exc, 'detail') and exc.detail != exc.status_code:
        detail = exc.detail
    else:
        detail = "Endpoint not found"

    return JSONResponse(
        status_code=404,
        content={"detail": detail}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# =============================================================================
# STARTUP & SHUTDOWN EVENTS
# =============================================================================

import asyncio
from app.utils.log_cleanup import cleanup_old_logs

# Background task handle
cleanup_task = None


async def periodic_log_cleanup():
    """Background task to cleanup old device logs every hour"""
    logger.info("🧹 Starting periodic log cleanup task (every 1 hour)")

    while True:
        try:
            # Run cleanup every hour
            await asyncio.sleep(3600)  # 1 hour = 3600 seconds

            # Cleanup logs older than 24 hours (1 day retention)
            deleted_count = cleanup_old_logs(retention_hours=24)

            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old device logs (retention: 24 hours)")

        except Exception as e:
            logger.error(f"❌ Error in periodic log cleanup: {e}")


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    global cleanup_task

    logger.info("=" * 60)
    logger.info("Smart TV Digital Signage - Backend API Starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"API Docs: {'Enabled' if settings.ENABLE_API_DOCS else 'Disabled'}")
    logger.info("=" * 60)

    # Test database connection
    try:
        if check_db_connection():
            logger.info("✓ Database connection successful")
            # Count registered tables
            from sqlalchemy import inspect
            inspector = inspect(engine)
            table_count = len(inspector.get_table_names())
            logger.info(f"✓ Database tables found: {table_count}")
        else:
            logger.warning("⚠ Database connection check returned False")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")

    # Run initial cleanup on startup
    try:
        deleted_count = cleanup_old_logs(retention_hours=24)
        if deleted_count > 0:
            logger.info(f"🧹 Initial cleanup: Deleted {deleted_count} old device logs")
    except Exception as e:
        logger.error(f"❌ Initial cleanup failed: {e}")

    # Start background task for log cleanup
    cleanup_task = asyncio.create_task(periodic_log_cleanup())
    logger.info("✓ Background log cleanup task started")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    global cleanup_task

    logger.info("Smart TV Digital Signage - Backend API Shutting Down...")

    # Cancel background tasks
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("✓ Background log cleanup task cancelled")

    # Cleanup Firebird connection pools
    try:
        from app.services.firebird_service import firebird_service
        firebird_service.shutdown()
        logger.info("✓ Firebird connection pools closed")
    except Exception as e:
        logger.error(f"❌ Error closing Firebird pools: {e}")

    # Cleanup resources here


# =============================================================================
# DEV TESTING ENDPOINTS (Remove in production)
# =============================================================================

if settings.DEBUG:
    @app.get("/debug/settings")
    async def debug_settings():
        """Debug endpoint to view current settings"""
        return {
            "PROJECT_NAME": settings.PROJECT_NAME,
            "ENVIRONMENT": settings.ENVIRONMENT,
            "DEBUG": settings.DEBUG,
            "DATABASE_URL": settings.DATABASE_URL[:30] + "...",  # Partial URL for security
            "REDIS_URL": settings.REDIS_URL[:30] + "...",
            "ANTHIAS_API_URL": settings.ANTHIAS_API_URL,
            "CORS_ORIGINS": settings.CORS_ORIGINS,
        }
