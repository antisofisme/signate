"""
FastAPI Main Application - Phase 2: Auth + Device
Centralized API with Clean Architecture
"""

# Application Version
__version__ = "1.0.0"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from prometheus_client import make_asgi_app

from shared.config import settings
from shared.database import check_db_connection, init_db
from shared.api_routes import API_V1
from shared.cache import cache
from shared.metrics import init_app_metrics, MetricsMiddleware
from shared.security_headers import configure_security_headers
from shared.rate_limiter import cleanup_rate_limiter
from shared.websocket_manager import init_websocket_manager, websocket_manager
from shared.range_static_files import RangeStaticFiles
from services.schedule.domain.schedule_executor import init_schedule_executor, get_schedule_executor

# Import service routers
from services.auth.routes import router as auth_router
from services.device.routes import router as device_router
from services.device.assignment_routes import router as device_assignment_router
from services.device.command_routes import router as device_command_router
from services.device.health_routes import router as device_health_router
from services.device.log_routes import router as device_log_router
from services.device.connection_log_routes import router as device_connection_log_router
from services.device.console_routes import router as device_console_router
from services.device.console_control_routes import router as device_console_control_router
from services.device.extended_routes import router as device_extended_router
from services.device.group_routes import router as device_group_router
from services.organization.routes import router as organization_router
from services.user.routes import router as user_router
from services.audit.routes import router as audit_router
from services.tag.routes import router as tag_router
from services.content.routes import router as content_router
from services.content.video_routes import router as video_router
from services.content.hls_routes import router as hls_router
from services.playlist.routes import router as playlist_router
from services.playlist.client_routes import router as playlist_client_router
from services.rbac.routes import router as rbac_router
from services.session.routes import router as session_router
from services.analytics.routes import router as analytics_router
from services.pms.sync_routes import router as pms_router
from services.pms.websocket_routes import router as pms_websocket_router
from services.widget.routes import router as widget_router
from services.template.routes import router as template_router
from services.translation.routes import router as translation_router
from services.schedule.routes import router as schedule_router
from services.weather.routes import router as weather_router
from shared.websocket_routes import router as websocket_router


# =============================================================================
# LIFESPAN EVENT HANDLER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("=" * 80)
    print("🚀 Starting Digital Signage Backend - Phase 6: Performance & Production")
    print("=" * 80)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")

    # Check database connection
    if check_db_connection():
        print("✓ Database connection: OK")

        # Initialize database tables (creates if not exist)
        try:
            init_db()
            print("✓ Database tables: OK")
        except Exception as e:
            print(f"⚠ Database initialization warning: {e}")
    else:
        print("✗ Database connection: FAILED")
    
    # Check Redis connection
    redis_health = cache.health_check()
    if redis_health["status"] == "healthy":
        print("✓ Redis cache: OK")
        print(f"  - Connected clients: {redis_health.get('connected_clients', 0)}")
        print(f"  - Memory used: {redis_health.get('used_memory_human', 'N/A')}")
    else:
        print(f"⚠ Redis cache: {redis_health.get('message', 'Not connected')}")

    # Initialize WebSocket manager with Redis pub/sub
    ws_manager = init_websocket_manager(
        redis_url=settings.REDIS_URL,
        use_redis=settings.USE_REDIS_PUBSUB
    )
    if settings.USE_REDIS_PUBSUB:
        await ws_manager.start_redis_listener()
        print("✓ WebSocket manager: Redis pub/sub enabled")
    else:
        print("✓ WebSocket manager: In-memory mode")

    # Start WebSocket ping task
    await ws_manager.start_ping_task()
    print("✓ WebSocket ping task: Started")

    # Initialize metrics
    init_app_metrics(version="1.0.0", environment=settings.ENVIRONMENT)
    print("✓ Prometheus metrics: Initialized")

    # Initialize schedule executor
    from shared.database import get_db_context
    schedule_executor = init_schedule_executor(get_db_context)
    print("✓ Schedule executor: Initialized")

    print("=" * 80)

    yield

    # Shutdown
    print("👋 Shutting down Digital Signage Backend")

    # Stop WebSocket manager
    try:
        await websocket_manager.stop_ping_task()
        await websocket_manager.stop_redis_listener()
        print("✓ WebSocket manager stopped")
    except:
        pass

    # Stop schedule executor
    try:
        schedule_executor = get_schedule_executor()
        await schedule_executor.stop()
    except:
        pass


# =============================================================================
# FASTAPI APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title="Digital Signage API",
    description="Clean Architecture FastAPI Backend - Phase 6: Performance & Production",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    lifespan=lifespan
)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Configure security headers
configure_security_headers(app)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Schedule periodic cleanup of rate limiter
import asyncio
from contextlib import suppress

async def periodic_cleanup():
    """Run periodic cleanup tasks"""
    while True:
        with suppress(Exception):
            cleanup_rate_limiter()
        await asyncio.sleep(300)  # Every 5 minutes

# Start background tasks
@app.on_event("startup")
async def startup_background_tasks():
    asyncio.create_task(periodic_cleanup())
    # Start WebSocket ping task
    await websocket_manager.start_ping_task()
    # Start schedule executor
    schedule_executor = get_schedule_executor()
    asyncio.create_task(schedule_executor.start())


# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

if settings.ENABLE_CORS:
    cors_origins = settings.get_cors_origins_list()

    if not cors_origins:
        raise ValueError("CORS_ORIGINS must be configured in .env file")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    print(f"✓ CORS enabled for origins: {cors_origins}")


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@app.get("/")
def root():
    """Root endpoint - Health check"""
    return {
        "service": "Digital Signage API",
        "version": "1.0.0",
        "status": "running",
        "phase": "Phase 6: Performance & Production",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
def health_check():
    """Health check endpoint with version info"""
    db_healthy = check_db_connection()
    redis_health = cache.health_check()

    overall_healthy = db_healthy and redis_health["status"] == "healthy"

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "version": __version__,
        "database": "connected" if db_healthy else "disconnected",
        "cache": redis_health["status"],
        "phase": "Phase 6: Performance & Production",
        "metrics": "/metrics"
    }


# =============================================================================
# API ROUTERS (Phase 1 Day 2: + RBAC + Session)
# =============================================================================

# Note: Routes already include full path from Route classes
# So we don't add prefix here
app.include_router(auth_router, tags=["Authentication"])
# IMPORTANT: Device Groups must be registered BEFORE Device Management
# to avoid /devices/groups being caught by /devices/{device_id}
app.include_router(device_group_router, prefix="/api/v1/devices", tags=["Device Groups"])
# IMPORTANT: Device Logs must be registered BEFORE Device Management
# to avoid /devices/{device_id}/logs/batch being caught by /devices/{device_id}
app.include_router(device_log_router, prefix="/api/v1", tags=["Device Logs"])
app.include_router(device_connection_log_router, prefix="/api/v1", tags=["Device Connection Logs"])
app.include_router(device_console_router, prefix="/api/v1", tags=["Device Console Logs"])
app.include_router(device_console_control_router, prefix="/api/v1", tags=["Device Console Control"])
app.include_router(device_router, tags=["Device Management"])
app.include_router(device_assignment_router, prefix="/api/v1", tags=["Device Assignments"])
app.include_router(device_command_router, prefix="/api/v1", tags=["Device Commands"])
app.include_router(device_health_router, prefix="/api/v1", tags=["Device Health"])
app.include_router(device_extended_router, tags=["Device Extended"])  # Routes already include /api/v1
app.include_router(organization_router, tags=["Organization Management"])
app.include_router(user_router, tags=["User Management"])
app.include_router(audit_router, tags=["Audit Logging"])
app.include_router(tag_router, tags=["Tag Management"])
app.include_router(content_router, tags=["Content Management"])
app.include_router(video_router, tags=["Video Streaming"])  # Range-supporting video streaming
app.include_router(hls_router, tags=["HLS Streaming"])  # HLS adaptive bitrate streaming
app.include_router(playlist_router, tags=["Playlist Management"])
app.include_router(playlist_client_router, tags=["Client - Player/Viewer"])
app.include_router(rbac_router, tags=["RBAC - Role Management"])
app.include_router(session_router, tags=["Session Management"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics & Reporting"])
app.include_router(pms_router, prefix="/api/v1", tags=["PMS Integration"])
app.include_router(pms_websocket_router, tags=["PMS WebSocket"])
app.include_router(widget_router, prefix="/api/v1", tags=["Widget System"])
app.include_router(template_router, prefix="/api/v1", tags=["Template System"])
app.include_router(translation_router, prefix="/api/v1", tags=["Translation System"])
app.include_router(schedule_router, prefix="/api/v1", tags=["Schedule System"])
app.include_router(weather_router, prefix="/api/v1", tags=["Weather Service"])
app.include_router(websocket_router, prefix="/api", tags=["WebSocket"])


# =============================================================================
# STATIC FILES SERVING (for content uploads and thumbnails)
# =============================================================================

# Content serving is now handled by dedicated video/image streaming routes
# See services/content/video_routes.py for Range request support
CONTENT_DIR = Path("/data/signage/content/uploads")
if CONTENT_DIR.exists():
    print(f"✓ Content directory found: {CONTENT_DIR}")
    print(f"  Video/image serving via /content/videos/* and /content/images/* routes")
else:
    print(f"⚠ Content directory not found: {CONTENT_DIR}")

# Mount static files for thumbnails
THUMBNAILS_DIR = Path("/data/signage/content/thumbnails")
if THUMBNAILS_DIR.exists():
    app.mount("/thumbnails", StaticFiles(directory=str(THUMBNAILS_DIR)), name="thumbnails")
    print(f"✓ Static files mounted: /thumbnails -> {THUMBNAILS_DIR}")
else:
    print(f"⚠ Thumbnails directory not found: {THUMBNAILS_DIR}")


# =============================================================================
# ERROR HANDLERS
# =============================================================================

from shared.errors import AppException, AuthenticationError, AuthorizationError

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    """Handle custom AppException and convert to HTTP response"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "code": exc.code,
            "details": exc.details
        }
    )


@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request, exc: AuthenticationError):
    """Handle AuthenticationError specifically"""
    return JSONResponse(
        status_code=401,
        content={
            "message": exc.message,
            "code": exc.code,
            "details": exc.details
        }
    )


@app.exception_handler(AuthorizationError)
async def authz_exception_handler(request, exc: AuthorizationError):
    """Handle AuthorizationError specifically"""
    return JSONResponse(
        status_code=403,
        content={
            "message": exc.message,
            "code": exc.code,
            "details": exc.details
        }
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler with dynamic route list"""
    # Generate routes dynamically from app
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append(route.path)

    return JSONResponse(
        status_code=404,
        content={
            "detail": "Endpoint not found",
            "phase": "Phase 1 Day 2: RBAC + Session",
            "requested_path": str(request.url.path),
            "available_routes": sorted(set(routes))
        }
    )


# =============================================================================
# MAIN ENTRY POINT (for local development)
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.AUTH_SERVICE_PORT,  # From .env
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level=settings.LOG_LEVEL.lower()
    )
