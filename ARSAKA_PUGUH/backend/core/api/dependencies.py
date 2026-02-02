"""
API Dependencies

Dependency injection for FastAPI routers.
Wires repositories and use cases.

SECURITY: Uses RLS-enabled sessions by default for tenant isolation.
Source: Migration 016_row_level_security.sql
"""

from typing import AsyncGenerator, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import (
    SessionFactory,
    UnitOfWork,
    DecisionRepository,
    WorkflowRepository,
    RuleRepository,
    IdempotencyRepository,
    RuleEvaluationService
)
from ..use_cases import (
    CreateDecisionUseCase,
    ApproveWorkflowUseCase,
    RejectWorkflowUseCase,
    DelegateWorkflowUseCase,
    EscalateWorkflowUseCase
)
# SECURITY: Import RLS context functions
from infrastructure.database.rls_context import set_rls_context, clear_rls_context
# SECURITY: Import authenticated context
from ..auth.api.dependencies import (
    get_authenticated_context,
    get_authenticated_context_optional,
    AuthenticatedContext,
)


_session_factory: SessionFactory = None


def init_session_factory(database_url: str):
    """Initialize global session factory"""
    global _session_factory
    _session_factory = SessionFactory(database_url)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (without RLS context).

    WARNING: This returns a session WITHOUT RLS context.
    Use get_rls_session() for tenant-scoped queries.
    Only use this for:
    - Platform admin operations that span all tenants
    - System initialization/migration
    - Health checks
    """
    if _session_factory is None:
        raise RuntimeError("SessionFactory not initialized")

    session = await _session_factory.create_session()
    try:
        yield session
    finally:
        await session.close()


async def get_rls_session(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session with RLS context set.

    SECURITY: This is the preferred way to get a database session.
    It automatically sets PostgreSQL RLS session variables from the
    authenticated context, ensuring tenant isolation at database level.

    The RLS policies in the database will filter rows based on:
    - app.current_tenant_id: Only rows for this tenant
    - app.current_user_id: For user-level access control
    - app.is_platform_admin: Platform admins can bypass tenant filter

    Usage:
        @router.get("/decisions")
        async def list_decisions(
            ctx: AuthenticatedContext = Depends(get_authenticated_context),
            session: AsyncSession = Depends(get_rls_session),
        ):
            # All queries are automatically filtered by tenant_id
            return await session.execute(select(Decision)).scalars().all()
    """
    if _session_factory is None:
        raise RuntimeError("SessionFactory not initialized")

    session = await _session_factory.create_session()
    try:
        # SECURITY: Set RLS context from authenticated context
        tenant_id = UUID(ctx.tenant_id) if ctx.tenant_id else None
        user_id = UUID(ctx.user_id) if ctx.user_id else None
        is_admin = "platform_admin" in (ctx.roles or [])

        await set_rls_context(
            session,
            tenant_id=tenant_id,
            user_id=user_id,
            is_platform_admin=is_admin,
        )

        yield session
    finally:
        # SECURITY: Clear RLS context when done
        await clear_rls_context(session)
        await session.close()


async def get_rls_session_optional(
    ctx: Optional[AuthenticatedContext] = Depends(get_authenticated_context_optional),
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session with optional RLS context.

    For endpoints that work both authenticated and unauthenticated.
    If authenticated, RLS context is set. Otherwise, no context is set
    (which may result in empty results due to RLS policies).
    """
    if _session_factory is None:
        raise RuntimeError("SessionFactory not initialized")

    session = await _session_factory.create_session()
    try:
        if ctx is not None:
            tenant_id = UUID(ctx.tenant_id) if ctx.tenant_id else None
            user_id = UUID(ctx.user_id) if ctx.user_id else None
            is_admin = "platform_admin" in (ctx.roles or [])

            await set_rls_context(
                session,
                tenant_id=tenant_id,
                user_id=user_id,
                is_platform_admin=is_admin,
            )

        yield session
    finally:
        if ctx is not None:
            await clear_rls_context(session)
        await session.close()


async def get_create_decision_use_case(
    session: AsyncSession = Depends(get_rls_session)  # SECURITY: Use RLS-enabled session
) -> CreateDecisionUseCase:
    """Get CreateDecisionUseCase with injected dependencies.

    SECURITY: Uses RLS-enabled session for tenant isolation.
    """
    uow = UnitOfWork(session)
    decision_repo = DecisionRepository(session)
    workflow_repo = WorkflowRepository(session)
    rule_repo = RuleRepository(session)
    idempotency_repo = IdempotencyRepository(session)
    rule_eval_service = RuleEvaluationService()

    return CreateDecisionUseCase(
        uow=uow,
        decision_repository=decision_repo,
        workflow_repository=workflow_repo,
        rule_repository=rule_repo,
        idempotency_repository=idempotency_repo,
        rule_evaluation_service=rule_eval_service
    )


async def get_approve_workflow_use_case(
    session: AsyncSession = Depends(get_rls_session)  # SECURITY: Use RLS-enabled session
) -> ApproveWorkflowUseCase:
    """Get ApproveWorkflowUseCase with injected dependencies.

    SECURITY: Uses RLS-enabled session for tenant isolation.
    """
    uow = UnitOfWork(session)
    workflow_repo = WorkflowRepository(session)

    return ApproveWorkflowUseCase(
        uow=uow,
        workflow_repository=workflow_repo
    )


async def get_reject_workflow_use_case(
    session: AsyncSession = Depends(get_rls_session)  # SECURITY: Use RLS-enabled session
) -> RejectWorkflowUseCase:
    """Get RejectWorkflowUseCase with injected dependencies.

    SECURITY: Uses RLS-enabled session for tenant isolation.
    """
    uow = UnitOfWork(session)
    workflow_repo = WorkflowRepository(session)

    return RejectWorkflowUseCase(
        uow=uow,
        workflow_repository=workflow_repo
    )


async def get_delegate_workflow_use_case(
    session: AsyncSession = Depends(get_rls_session)  # SECURITY: Use RLS-enabled session
) -> DelegateWorkflowUseCase:
    """Get DelegateWorkflowUseCase with injected dependencies.

    SECURITY: Uses RLS-enabled session for tenant isolation.
    """
    uow = UnitOfWork(session)
    workflow_repo = WorkflowRepository(session)

    return DelegateWorkflowUseCase(
        uow=uow,
        workflow_repository=workflow_repo
    )


async def get_escalate_workflow_use_case(
    session: AsyncSession = Depends(get_rls_session)  # SECURITY: Use RLS-enabled session
) -> EscalateWorkflowUseCase:
    """Get EscalateWorkflowUseCase with injected dependencies.

    SECURITY: Uses RLS-enabled session for tenant isolation.
    """
    uow = UnitOfWork(session)
    workflow_repo = WorkflowRepository(session)

    return EscalateWorkflowUseCase(
        uow=uow,
        workflow_repository=workflow_repo
    )
