"""
Core Service FastAPI Application (Phase A)

HTTP API for decision engine and workflow orchestration.
Phase A: Minimal configuration, disabled infrastructure features.

Source: INFRA-LAY3-002 §4 (HTTP API Layer)
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router, read_router, config_router, EXCEPTION_HANDLERS, init_session_factory
from .auth import auth_router, init_auth_dependencies
from .tenant import tenant_router, init_tenant_dependencies
from .billing import billing_router, init_billing_dependencies
from .project import project_router, init_project_dependencies


# ============================================================================
# PHASE A CONFIGURATION
# ============================================================================

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "phase-a-staging")

# Database configuration (REQUIRED)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://atlas_user:CHANGE_PASSWORD@localhost:5433/atlas_puguh"
)

# JWT Authentication (REQUIRED)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Tenant configuration (Phase A: Single tenant)
ALLOWED_TENANT_IDS = os.getenv(
    "ALLOWED_TENANT_IDS",
    "550e8400-e29b-41d4-a716-446655440000"
).split(",")

# CORS origins (configure per environment)
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://admin-puguh.atlashub.com"
).split(",")

# Connection pool (Phase A: Minimal)
POOL_SIZE = int(os.getenv("POOL_SIZE", "2"))
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW", "3"))
POOL_TIMEOUT = int(os.getenv("POOL_TIMEOUT", "10"))
POOL_RECYCLE = int(os.getenv("POOL_RECYCLE", "3600"))
POOL_PRE_PING = os.getenv("POOL_PRE_PING", "true").lower() in ("true", "1", "yes")

# Infrastructure feature flags (Phase A: ALL DISABLED)
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() in ("true", "1", "yes")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() in ("true", "1", "yes")
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "false").lower() in ("true", "1", "yes")
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "false").lower() in ("true", "1", "yes")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")

# Phase A warnings
PHASE_A_WARNING = os.getenv(
    "PHASE_A_WARNING",
    "⚠️ NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED WITHOUT NOTICE"
)
API_VERSION = os.getenv("API_VERSION", "phase-a-unstable")


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager

    Handles startup and shutdown events.
    Source: INFRA-LAY3-002 §4.4 (Lifecycle Management)
    """
    print("=" * 80)
    print(f"🚀 Starting ATLAS_PUGUH Core Service")
    print("=" * 80)

    # Display environment info
    print(f"Environment: {ENVIRONMENT}")
    print(f"API Version: {API_VERSION}")
    print(f"Phase A Warning: {PHASE_A_WARNING}")
    print()

    # Display configuration
    print("📋 Configuration:")
    print(f"   Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'NOT CONFIGURED'}")
    print(f"   Tenant IDs: {', '.join(ALLOWED_TENANT_IDS)}")
    print(f"   JWT Expire: {JWT_EXPIRE_MINUTES} minutes")
    print(f"   CORS Origins: {len(CORS_ORIGINS)} origin(s)")
    print()

    # Display pool settings
    print("🔧 Database Pool:")
    print(f"   Pool Size: {POOL_SIZE}")
    print(f"   Max Overflow: {MAX_OVERFLOW} (total: {POOL_SIZE + MAX_OVERFLOW} connections)")
    print(f"   Timeout: {POOL_TIMEOUT}s")
    print(f"   Recycle: {POOL_RECYCLE}s")
    print(f"   Pre-ping: {POOL_PRE_PING}")
    print()

    # Display infrastructure status (Phase A: All disabled)
    print("🏗️  Infrastructure Status:")
    print(f"   Redis Caching: {'✅ ENABLED' if REDIS_ENABLED else '❌ DISABLED (Phase A)'}")
    print(f"   Rate Limiting: {'✅ ENABLED' if RATE_LIMIT_ENABLED else '❌ DISABLED (Phase A)'}")
    print(f"   Prometheus Metrics: {'✅ ENABLED' if ENABLE_METRICS else '❌ DISABLED (Phase A)'}")
    print(f"   OpenTelemetry Tracing: {'✅ ENABLED' if ENABLE_TRACING else '❌ DISABLED (Phase A)'}")
    print()

    # Initialize database session factory
    print("🔌 Initializing database connection...")
    init_session_factory(DATABASE_URL)
    print("✅ Database session factory initialized")
    print()

    # Initialize auth dependencies
    print("🔐 Initializing auth dependencies...")
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    auth_engine = create_async_engine(DATABASE_URL, pool_size=POOL_SIZE, max_overflow=MAX_OVERFLOW)
    auth_session_factory = async_sessionmaker(auth_engine, expire_on_commit=False)
    init_auth_dependencies(
        session_factory=auth_session_factory,
        jwt_secret=JWT_SECRET_KEY,
        jwt_issuer="atlaspuguh",
    )
    print("✅ Auth dependencies initialized")
    print()

    # Initialize tenant dependencies
    print("🏢 Initializing tenant dependencies...")
    from .auth.adapters.user_repository import PostgresUserRepository
    user_repo = PostgresUserRepository(auth_session_factory)
    init_tenant_dependencies(
        session_factory=auth_session_factory,
        user_repo=user_repo,
    )
    print("✅ Tenant dependencies initialized")
    print()

    # Initialize billing dependencies
    print("💳 Initializing billing dependencies...")
    init_billing_dependencies(
        session_factory=auth_session_factory,
    )
    print("✅ Billing dependencies initialized")
    print()

    # Initialize project dependencies
    print("📁 Initializing project dependencies...")
    init_project_dependencies(
        session_factory=auth_session_factory,
    )
    print("✅ Project dependencies initialized")
    print()

    # Security warnings
    if JWT_SECRET_KEY == "CHANGE_THIS_SECRET_KEY":
        print("⚠️  WARNING: Using default JWT secret key! Change in production!")

    if "CHANGE_PASSWORD" in DATABASE_URL:
        print("⚠️  WARNING: Using default database password! Change in production!")

    print("=" * 80)
    print(f"✅ ATLAS_PUGUH Core Service started successfully")
    print(f"📖 API Documentation: http://localhost:8001/api/docs")
    print(f"🏥 Health Check: http://localhost:8001/health")
    print("=" * 80)
    print()

    yield

    # Shutdown
    print()
    print("=" * 80)
    print("🔻 Shutting down ATLAS_PUGUH Core Service...")
    print("=" * 80)


# ============================================================================
# APPLICATION FACTORY
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application

    Returns:
        Configured FastAPI application instance

    Source: INFRA-LAY3-002 §4.1 (Application Factory)
    """
    app = FastAPI(
        title="ATLAS_PUGUH Core Service",
        description=(
            "Decision engine and workflow orchestration for PUGUH Control Plane.\n\n"
            f"**Environment**: {ENVIRONMENT}\n"
            f"**API Version**: {API_VERSION}\n\n"
            f"**{PHASE_A_WARNING}**\n\n"
            "Phase A is for visibility and debugging only. "
            "Infrastructure features (Redis, metrics, tracing) are disabled."
        ),
        version="1.0.0-phase-a",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Register CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print(f"✅ CORS enabled for origins: {CORS_ORIGINS}")

    # Register exception handlers
    for exception_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_class, handler)
    print(f"✅ Registered {len(EXCEPTION_HANDLERS)} exception handlers")

    # Register routers
    app.include_router(router)
    app.include_router(read_router)  # Phase A+ read-only endpoints
    app.include_router(config_router)  # Configuration master data endpoints
    app.include_router(auth_router, prefix="/api/v1")  # Auth endpoints
    app.include_router(tenant_router, prefix="/api/v1")  # Tenant endpoints
    app.include_router(billing_router, prefix="/api/v1")  # Billing endpoints
    app.include_router(project_router, prefix="/api/v1")  # Project endpoints
    print("✅ API routers registered (core + read-only + configuration + auth + tenant + billing + project)")

    return app


# Application instance (for ASGI servers like uvicorn)
app = create_app()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint (LIMITED SCOPE - Phase A)

    IMPORTANT: This health check ONLY verifies that the API process is alive
    and responding to HTTP requests. It does NOT guarantee:
    - Database connectivity (no actual DB query executed)
    - Infrastructure health (Redis, metrics, tracing all disabled in Phase A)
    - System resource availability (memory, CPU, disk)
    - Downstream service health

    For production health checks, implement:
    - Actual database connectivity test (e.g., SELECT 1)
    - Redis ping (if enabled)
    - Dependency health checks
    - Resource utilization checks

    Phase A Scope: Process alive = "healthy"

    Returns:
        Service status, version, and configuration info

    Source: INFRA-LAY3-002 §4.5 (Observability)
    """
    return {
        "service": "core",
        "status": "healthy",  # Only means: API process is alive
        "version": "1.0.0-phase-a",
        "environment": ENVIRONMENT,
        "api_version": API_VERSION,
        "database": "connected" if DATABASE_URL else "not_configured",  # Config only, not tested
        "tenant_ids": ALLOWED_TENANT_IDS,
        "infrastructure": {
            "redis": REDIS_ENABLED,
            "rate_limiting": RATE_LIMIT_ENABLED,
            "metrics": ENABLE_METRICS,
            "tracing": ENABLE_TRACING,
            "auth": True,  # Auth module enabled
            "tenant": True,  # Tenant module enabled
            "billing": True,  # Billing module enabled
            "project": True,  # Project module enabled
        },
        "pool": {
            "size": POOL_SIZE,
            "max_overflow": MAX_OVERFLOW,
            "total_connections": POOL_SIZE + MAX_OVERFLOW
        },
        "warning": PHASE_A_WARNING,
        "health_check_scope": "process_alive_only"  # Explicit limitation
    }


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
