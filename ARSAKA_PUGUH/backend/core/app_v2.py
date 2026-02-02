"""
Core Service FastAPI Application - Phase 2 Enhanced

HTTP API for decision engine with Phase 2 infrastructure:
- Structured logging (JSON)
- Prometheus metrics
- OpenTelemetry tracing

CRITICAL: Phase 1 core logic UNCHANGED. Only adds infrastructure wiring.

Source: Phase 2 Design & Execution Plan - Week 1
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

# Phase 1 imports (UNCHANGED)
from .api import router, EXCEPTION_HANDLERS, init_session_factory

# Phase 2 infrastructure imports (NEW)
from infrastructure.logging import StructuredLogger, set_request_context, clear_request_context
from infrastructure.metrics import (
    initialize_metrics,
    get_metrics_text,
    PrometheusMiddleware,
)
from infrastructure.tracing import initialize_tracing, shutdown_tracing


# Database configuration (Phase 1, UNCHANGED)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://signage_user:signage_password@localhost:5433/signage_db"
)

# CORS origins (Phase 1, UNCHANGED)
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://192.168.5.12:3000,http://72.61.209.158:3000"
).split(",")

# Phase 2 configuration (NEW)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
JAEGER_ENDPOINT = os.getenv("JAEGER_ENDPOINT", None)
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - Phase 2 Enhanced

    Startup:
    - Phase 1: Initialize database session factory
    - Phase 2: Initialize logging, metrics, tracing

    Shutdown:
    - Phase 2: Shutdown tracing gracefully
    """
    # Phase 1 startup (UNCHANGED)
    init_session_factory(DATABASE_URL)
    print(f"✅ Database session factory initialized: {DATABASE_URL}")

    # Phase 2 startup (NEW)
    StructuredLogger.configure(level=LOG_LEVEL, format_json=True)
    print(f"✅ Structured logging configured: level={LOG_LEVEL}, format=JSON")

    initialize_metrics()
    print("✅ Prometheus metrics initialized")

    if ENABLE_TRACING:
        initialize_tracing(
            service_name="core-service",
            service_version="2.0.0",
            jaeger_endpoint=JAEGER_ENDPOINT,
        )

    yield

    # Phase 2 shutdown (NEW)
    if ENABLE_TRACING:
        shutdown_tracing()

    # Phase 1 shutdown (UNCHANGED)
    print("🔻 Application shutdown")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application - Phase 2 Enhanced

    Phase 1 components (UNCHANGED):
    - CORS middleware
    - Exception handlers
    - API routers

    Phase 2 additions (NEW):
    - Prometheus metrics middleware
    - Logging context middleware
    - /metrics endpoint

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="ARSAKA_PUGUH Core Service",
        description="Decision engine and workflow orchestration - Phase 2 Enhanced",
        version="2.0.0",  # Phase 2 version
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Phase 2: Add Prometheus metrics middleware (NEW, before CORS)
    app.add_middleware(PrometheusMiddleware)
    print("✅ Prometheus metrics middleware registered")

    # Phase 1: Register CORS middleware (UNCHANGED)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print(f"✅ CORS enabled for origins: {CORS_ORIGINS}")

    # Phase 1: Register exception handlers (UNCHANGED)
    for exception_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_class, handler)
    print(f"✅ Registered {len(EXCEPTION_HANDLERS)} exception handlers")

    # Phase 1: Register routers (UNCHANGED)
    app.include_router(router)
    print("✅ API router registered")

    return app


# Application instance (for ASGI servers like uvicorn)
app = create_app()


# Phase 1: Health check endpoint (UNCHANGED)
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint

    Returns:
        Service status and version

    Source: INFRA-LAY3-002 §4.5 (Observability)
    """
    return {
        "service": "core",
        "status": "healthy",
        "version": "2.0.0",  # Phase 2 version
        "phase": "Phase 2 - Infrastructure Foundation"
    }


# Phase 2: Prometheus metrics endpoint (NEW)
@app.get("/metrics", tags=["observability"])
async def metrics():
    """
    Prometheus metrics endpoint

    Returns:
        Metrics in Prometheus exposition format

    Source: Phase 2 Design & Execution Plan - Section 3.2
    """
    return Response(
        content=get_metrics_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    uvicorn.run(
        "app_v2:app",  # Note: Changed from app:app to app_v2:app
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
