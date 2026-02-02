"""
Row Level Security Context Manager

Sets PostgreSQL session variables for RLS policy evaluation.
Must be called at the start of each request/transaction.

How RLS Works:
1. Migration 016 enables RLS on tenant-scoped tables
2. Policies filter rows using current_setting('app.current_tenant_id')
3. This module sets those session variables from JWT context

Source: Migration 016_row_level_security.sql
"""

from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection


async def set_rls_context(
    session: AsyncSession,
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    is_platform_admin: bool = False,
) -> None:
    """
    Set RLS session variables for the current database session.

    Must be called at the start of each request before any queries.
    The session variables are connection-scoped and reset when connection is returned to pool.

    Args:
        session: SQLAlchemy async session
        tenant_id: Current tenant UUID (from JWT)
        user_id: Current user UUID (from JWT)
        is_platform_admin: Whether user is a platform admin
    """
    # Set tenant context
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
            {"tenant_id": str(tenant_id)}
        )
    else:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', '', false)")
        )

    # Set user context
    if user_id:
        await session.execute(
            text("SELECT set_config('app.current_user_id', :user_id, false)"),
            {"user_id": str(user_id)}
        )
    else:
        await session.execute(
            text("SELECT set_config('app.current_user_id', '', false)")
        )

    # Set admin flag
    await session.execute(
        text("SELECT set_config('app.is_platform_admin', :is_admin, false)"),
        {"is_admin": "true" if is_platform_admin else "false"}
    )


async def clear_rls_context(session: AsyncSession) -> None:
    """
    Clear RLS session variables.

    Should be called when returning connection to pool or on error.
    """
    await session.execute(text("SELECT set_config('app.current_tenant_id', '', false)"))
    await session.execute(text("SELECT set_config('app.current_user_id', '', false)"))
    await session.execute(text("SELECT set_config('app.is_platform_admin', 'false', false)"))


@asynccontextmanager
async def rls_context(
    session: AsyncSession,
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    is_platform_admin: bool = False,
):
    """
    Context manager for RLS-enabled database operations.

    Usage:
        async with rls_context(session, tenant_id=t_id, user_id=u_id):
            # All queries in this block are filtered by RLS
            results = await session.execute(select(MyModel))

    Args:
        session: SQLAlchemy async session
        tenant_id: Current tenant UUID
        user_id: Current user UUID
        is_platform_admin: Whether user is a platform admin
    """
    try:
        await set_rls_context(session, tenant_id, user_id, is_platform_admin)
        yield
    finally:
        await clear_rls_context(session)


# ============================================================================
# FastAPI Middleware
# ============================================================================

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RLSMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that sets RLS context from JWT claims.

    Extracts tenant_id and user_id from the request's JWT token
    and sets them as PostgreSQL session variables.
    """

    # Paths that don't require RLS context
    EXCLUDED_PATHS = {
        "/health",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
    }

    def __init__(self, app, session_factory):
        """Initialize middleware.

        Args:
            app: FastAPI application
            session_factory: SQLAlchemy async session factory
        """
        super().__init__(app)
        self._session_factory = session_factory

    async def dispatch(self, request: Request, call_next) -> Response:
        """Set RLS context before processing request."""
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Extract context from request state (set by auth middleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)
        is_admin = getattr(request.state, "is_platform_admin", False)

        # Set RLS context for this request's database session
        if hasattr(request.state, "db_session"):
            session = request.state.db_session
            await set_rls_context(
                session,
                tenant_id=UUID(tenant_id) if tenant_id else None,
                user_id=UUID(user_id) if user_id else None,
                is_platform_admin=is_admin,
            )

        return await call_next(request)


# ============================================================================
# FastAPI Dependency
# ============================================================================

from typing import AsyncGenerator
from fastapi import Depends


async def get_rls_session(
    request: Request,
    # Assuming you have a get_session dependency
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an RLS-enabled database session.

    Automatically sets RLS context from JWT claims in request.

    Usage:
        @router.get("/items")
        async def list_items(session: AsyncSession = Depends(get_rls_session)):
            # Session is already configured with RLS context
            return await session.execute(select(Item)).scalars().all()
    """
    # This would be integrated with your existing session management
    # For now, this is a placeholder showing the pattern
    pass


# ============================================================================
# Service-Level Context Setting
# ============================================================================

class RLSService:
    """
    Service for managing RLS context in repositories.

    Use this when you need fine-grained control over RLS context,
    such as in background jobs or admin operations.

    Usage:
        rls = RLSService(session)

        # Normal user context
        await rls.set_user_context(tenant_id, user_id)

        # Platform admin context (bypasses some RLS checks)
        await rls.set_admin_context(user_id)

        # Service context (for background jobs)
        await rls.set_service_context()
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def set_user_context(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        """Set context for normal user operations."""
        await set_rls_context(
            self._session,
            tenant_id=tenant_id,
            user_id=user_id,
            is_platform_admin=False,
        )

    async def set_admin_context(self, user_id: UUID) -> None:
        """Set context for platform admin operations."""
        await set_rls_context(
            self._session,
            tenant_id=None,  # Admins can see all tenants
            user_id=user_id,
            is_platform_admin=True,
        )

    async def set_service_context(self) -> None:
        """Set context for service/background job operations.

        WARNING: This bypasses RLS. Use only for trusted operations.
        """
        await set_rls_context(
            self._session,
            tenant_id=None,
            user_id=None,
            is_platform_admin=True,
        )

    async def clear_context(self) -> None:
        """Clear RLS context."""
        await clear_rls_context(self._session)
