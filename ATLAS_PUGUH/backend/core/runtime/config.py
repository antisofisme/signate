"""
Runtime Configuration - Enforced Discipline

This module enforces:
1. Single connection pool using app_runtime_role
2. No dynamic role switching
3. All requests must have tenant/subject/trace context

FAIL RULES:
- Context missing → DENY
- Tenant mismatch → DENY
- Wrong role → DENY

Source: Phase 2 Requirements
"""

import os
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text


# =============================================================================
# RUNTIME CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class RuntimeConfig:
    """
    Immutable runtime configuration.

    All fields are REQUIRED. NO defaults that weaken security.
    """
    # Database connection
    database_url: str
    database_role: str  # MUST be 'app_runtime_role'

    # Connection pool settings
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    pool_pre_ping: bool

    def __post_init__(self):
        # Enforce app_runtime_role
        if self.database_role != "app_runtime_role":
            raise ValueError(
                f"SECURITY: database_role must be 'app_runtime_role', got '{self.database_role}'"
            )


def load_runtime_config() -> RuntimeConfig:
    """
    Load runtime configuration from environment.

    REQUIRED environment variables:
    - DATABASE_URL
    - DATABASE_ROLE (must be 'app_runtime_role')
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is REQUIRED")

    database_role = os.getenv("DATABASE_ROLE", "app_runtime_role")
    if database_role != "app_runtime_role":
        raise ValueError(
            f"SECURITY: DATABASE_ROLE must be 'app_runtime_role', got '{database_role}'"
        )

    return RuntimeConfig(
        database_url=database_url,
        database_role=database_role,
        pool_size=int(os.getenv("POOL_SIZE", "5")),
        max_overflow=int(os.getenv("MAX_OVERFLOW", "10")),
        pool_timeout=int(os.getenv("POOL_TIMEOUT", "30")),
        pool_recycle=int(os.getenv("POOL_RECYCLE", "3600")),
        pool_pre_ping=os.getenv("POOL_PRE_PING", "true").lower() == "true",
    )


# =============================================================================
# REQUEST CONTEXT (ENFORCED)
# =============================================================================

@dataclass(frozen=True)
class RequestContext:
    """
    Request context - REQUIRED for all database operations.

    All fields are REQUIRED. NO implicit defaults.
    """
    tenant_id: UUID
    subject_id: UUID
    subject_type: str  # "user" or "service"
    trace_id: UUID

    def __post_init__(self):
        if self.tenant_id is None:
            raise ValueError("tenant_id is REQUIRED")
        if self.subject_id is None:
            raise ValueError("subject_id is REQUIRED")
        if self.subject_type not in ("user", "service"):
            raise ValueError("subject_type must be 'user' or 'service'")
        if self.trace_id is None:
            raise ValueError("trace_id is REQUIRED")


# =============================================================================
# SESSION FACTORY WITH ENFORCED CONTEXT
# =============================================================================

class EnforcedSessionFactory:
    """
    Session factory that enforces context at every operation.

    Features:
    1. Single connection pool (no dynamic switching)
    2. Automatic tenant context injection
    3. Verification of role at startup

    SECURITY: Uses app_runtime_role which cannot bypass RLS.
    """

    def __init__(self, config: RuntimeConfig):
        self._config = config
        self._engine = None
        self._session_maker = None
        self._verified = False

    async def initialize(self) -> None:
        """
        Initialize connection pool and verify security settings.

        MUST be called before any database operations.
        """
        # Create engine with app_runtime_role credentials
        self._engine = create_async_engine(
            self._config.database_url,
            echo=False,
            pool_size=self._config.pool_size,
            max_overflow=self._config.max_overflow,
            pool_timeout=self._config.pool_timeout,
            pool_recycle=self._config.pool_recycle,
            pool_pre_ping=self._config.pool_pre_ping,
        )

        self._session_maker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Verify security settings
        await self._verify_security()
        self._verified = True

    async def _verify_security(self) -> None:
        """
        Verify that security settings are correct.

        Checks:
        1. Current role is app_runtime_role
        2. Role cannot bypass RLS
        3. FORCE RLS is enabled on all tables
        """
        async with self._session_maker() as session:
            # Check current role
            result = await session.execute(text("SELECT current_user"))
            current_user = result.scalar()

            if current_user != "app_runtime_role":
                raise SecurityError(
                    f"SECURITY: Expected role 'app_runtime_role', got '{current_user}'"
                )

            # Check that role cannot bypass RLS
            result = await session.execute(
                text("SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user")
            )
            can_bypass = result.scalar()

            if can_bypass:
                raise SecurityError(
                    "SECURITY: Role can bypass RLS. This is a security violation."
                )

            # Verify FORCE RLS on critical tables
            tables = ["decisions", "workflows", "event_log", "operations_audit"]
            for table in tables:
                result = await session.execute(
                    text("""
                        SELECT relforcerowsecurity
                        FROM pg_class
                        WHERE relname = :table_name
                    """),
                    {"table_name": table}
                )
                is_forced = result.scalar()

                if not is_forced:
                    raise SecurityError(
                        f"SECURITY: FORCE RLS not enabled on table '{table}'"
                    )

    async def get_session(self, context: RequestContext) -> AsyncSession:
        """
        Get database session with enforced context.

        The tenant context is automatically set as a session variable.
        All RLS policies will use this context.

        Args:
            context: Request context (REQUIRED)

        Returns:
            AsyncSession with tenant context set
        """
        if not self._verified:
            raise SecurityError("Session factory not initialized. Call initialize() first.")

        if context is None:
            raise ContextRequiredError("Request context is REQUIRED")

        session = self._session_maker()

        # Set tenant context for RLS
        await session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(context.tenant_id)}
        )

        # Set trace context for audit
        await session.execute(
            text("SET app.trace_id = :trace_id"),
            {"trace_id": str(context.trace_id)}
        )

        # Set subject context for audit
        await session.execute(
            text("SET app.subject_id = :subject_id"),
            {"subject_id": str(context.subject_id)}
        )

        return session

    async def close(self) -> None:
        """Close connection pool."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None
            self._verified = False


# =============================================================================
# EXCEPTIONS
# =============================================================================

class SecurityError(Exception):
    """
    Raised when a security violation is detected.

    This is a FATAL error. Operation MUST be denied.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"SECURITY ERROR: {message}")


class ContextRequiredError(Exception):
    """
    Raised when required context is missing.

    Operation MUST be denied.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"CONTEXT REQUIRED: {message}")
