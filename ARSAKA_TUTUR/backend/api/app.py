"""
FastAPI Application Factory.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import api_router
from .middleware import (
    TenantMiddleware,
    ErrorHandlerMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    AuditMiddleware,
)
from ..config import Settings, get_settings
from ..container import get_container, close_container
from ..shared.logging import setup_logging, get_logger

logger = get_logger(__name__)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        settings: Optional settings (uses get_settings() if not provided)

    Returns:
        Configured FastAPI app
    """
    settings = settings or get_settings()

    # Setup logging
    setup_logging(
        level=settings.log_level,
        format_type="colored" if settings.is_development else "json",
    )

    # Create app with lifespan
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan - startup and shutdown."""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")

        # Initialize container
        container = await get_container()
        logger.info("Container initialized")

        yield

        # Cleanup
        await close_container()
        logger.info("Shutdown complete")

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-tenant AI Chat Service with RAG and Memory capabilities",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # =========================================================================
    # Middleware Stack (applied in reverse order - last added runs first)
    # Request flow: RequestId → Error → RateLimit → Tenant → Audit → Handler
    # =========================================================================

    # 5. Audit logging (logs after request completes)
    app.add_middleware(AuditMiddleware)

    # 4. Tenant resolution (extracts tenant from header/path)
    app.add_middleware(TenantMiddleware)

    # 3. Rate limiting (Redis backed, lazy initialization)
    app.add_middleware(
        RateLimitMiddleware,
        redis_cache=None,  # Obtained lazily from container
        default_limit=settings.rate_limit.general_per_minute,
        default_window=60,
    )

    # 2. Error handler (catches all exceptions)
    app.add_middleware(ErrorHandlerMiddleware)

    # 1. Request ID (first middleware - adds X-Request-ID)
    app.add_middleware(RequestIdMiddleware)

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Root redirect to docs
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return app


# Create default app instance
app = create_app()
