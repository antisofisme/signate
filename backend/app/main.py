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
    ContentAssignment, Schedule, FirebirdConfig, DeviceLog
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart TV Digital Signage - Backend API for managing TV/Monitor devices and content",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
)

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
from app.api import auth, devices, content, client, tags, logs, websocket

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(content.router, prefix="/api/content", tags=["Content"])
app.include_router(client.router, prefix="/api/client", tags=["Client"])
app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])
app.include_router(logs.router, prefix="/api", tags=["Device Logs"])
app.include_router(websocket.router, prefix="/api", tags=["WebSocket"])

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
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
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

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
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


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Smart TV Digital Signage - Backend API Shutting Down...")
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
