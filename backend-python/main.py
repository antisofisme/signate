"""
FastAPI Main Application - Phase 2: Auth + Device
Centralized API with Clean Architecture
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from shared.config import settings
from shared.database import check_db_connection, init_db
from shared.api_routes import API_V1

# Import service routers
from services.auth.routes import router as auth_router
from services.device.routes import router as device_router
from services.device.assignment_routes import router as device_assignment_router
from services.device.command_routes import router as device_command_router
from services.device.health_routes import router as device_health_router
from services.device.log_routes import router as device_log_router
from services.device.extended_routes import router as device_extended_router
from services.device.group_routes import router as device_group_router
from services.organization.routes import router as organization_router
from services.user.routes import router as user_router
from services.audit.routes import router as audit_router
from services.tag.routes import router as tag_router
from services.content.routes import router as content_router
from services.playlist.routes import router as playlist_router
from services.rbac.routes import router as rbac_router
from services.session.routes import router as session_router
from services.analytics.routes import router as analytics_router
from services.pms.sync_routes import router as pms_router
from services.pms.websocket_routes import router as pms_websocket_router
from services.widget.routes import router as widget_router
from services.template.routes import router as template_router
from services.translation.routes import router as translation_router
from services.schedule.routes import router as schedule_router


# =============================================================================
# LIFESPAN EVENT HANDLER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("=" * 80)
    print("🚀 Starting Digital Signage Backend - Phase 1 Day 2: RBAC + Session Management")
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

    print("=" * 80)

    yield

    # Shutdown
    print("👋 Shutting down Digital Signage Backend")


# =============================================================================
# FASTAPI APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title="Digital Signage API",
    description="Clean Architecture FastAPI Backend - Phase 1 Day 2: RBAC + Session Management",
    version="1.0.0-phase1-day2",
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    lifespan=lifespan
)


# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

if settings.ENABLE_CORS:
    cors_origins = settings.get_cors_origins_list()

    if not cors_origins:
        # Default CORS origins if not specified
        cors_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://192.168.5.12:8080",
            "http://192.168.5.12:3000"
        ]

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
        "version": "1.0.0-phase1-day2",
        "status": "running",
        "phase": "Phase 1 Day 2: RBAC + Session Management",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    db_healthy = check_db_connection()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "phase": "Phase 1 Day 2: RBAC + Session Management"
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
app.include_router(device_router, tags=["Device Management"])
app.include_router(device_assignment_router, prefix="/api/v1", tags=["Device Assignments"])
app.include_router(device_command_router, prefix="/api/v1", tags=["Device Commands"])
app.include_router(device_health_router, prefix="/api/v1", tags=["Device Health"])
app.include_router(device_log_router, prefix="/api/v1", tags=["Device Logs"])
app.include_router(device_extended_router, prefix="/api/v1", tags=["Device Extended"])
app.include_router(organization_router, tags=["Organization Management"])
app.include_router(user_router, tags=["User Management"])
app.include_router(audit_router, tags=["Audit Logging"])
app.include_router(tag_router, tags=["Tag Management"])
app.include_router(content_router, tags=["Content Management"])
app.include_router(playlist_router, tags=["Playlist Management"])
app.include_router(rbac_router, tags=["RBAC - Role Management"])
app.include_router(session_router, tags=["Session Management"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics & Reporting"])
app.include_router(pms_router, prefix="/api/v1", tags=["PMS Integration"])
app.include_router(pms_websocket_router, tags=["PMS WebSocket"])
app.include_router(widget_router, prefix="/api/v1", tags=["Widget System"])
app.include_router(template_router, prefix="/api/v1", tags=["Template System"])
app.include_router(translation_router, prefix="/api/v1", tags=["Translation System"])
app.include_router(schedule_router, prefix="/api/v1", tags=["Schedule System"])


# =============================================================================
# STATIC FILES SERVING (for content uploads and thumbnails)
# =============================================================================

# Mount static files for content serving
CONTENT_DIR = Path("/data/signage/content/uploads")
if CONTENT_DIR.exists():
    app.mount("/content", StaticFiles(directory=str(CONTENT_DIR)), name="content")
    print(f"✓ Static files mounted: /content -> {CONTENT_DIR}")
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
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Endpoint not found",
            "phase": "Phase 1 Day 2: RBAC + Session",
            "available_routes": [
                "/docs",
                "/health",
                f"{API_V1}/auth/login",
                f"{API_V1}/auth/register",
                f"{API_V1}/devices/request-code",
                f"{API_V1}/devices/activate",
                f"{API_V1}/devices/heartbeat",
                f"{API_V1}/devices",
                f"{API_V1}/organizations",
                f"{API_V1}/users",
                f"{API_V1}/tags",
                f"{API_V1}/roles",
                f"{API_V1}/sessions"
            ]
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
