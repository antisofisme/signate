"""
API Dependencies

Dependency injection for FastAPI routers.
Wires repositories and use cases.
"""

from typing import AsyncGenerator
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


_session_factory: SessionFactory = None


def init_session_factory(database_url: str):
    """Initialize global session factory"""
    global _session_factory
    _session_factory = SessionFactory(database_url)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    if _session_factory is None:
        raise RuntimeError("SessionFactory not initialized")

    session = await _session_factory.create_session()
    try:
        yield session
    finally:
        await session.close()


async def get_create_decision_use_case(
    session: AsyncSession = Depends(get_session)
) -> CreateDecisionUseCase:
    """Get CreateDecisionUseCase with injected dependencies"""
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
    session: AsyncSession = Depends(get_session)
) -> ApproveWorkflowUseCase:
    """Get ApproveWorkflowUseCase with injected dependencies"""
    uow = UnitOfWork(session)
    workflow_repo = WorkflowRepository(session)

    return ApproveWorkflowUseCase(
        uow=uow,
        workflow_repository=workflow_repo
    )


async def get_reject_workflow_use_case(
    session: AsyncSession = Depends(get_session)
) -> RejectWorkflowUseCase:
    """Get RejectWorkflowUseCase with injected dependencies"""
    uow = UnitOfWork(session)
    workflow_repo = WorkflowRepository(session)

    return RejectWorkflowUseCase(
        uow=uow,
        workflow_repository=workflow_repo
    )


async def get_delegate_workflow_use_case(
    session: AsyncSession = Depends(get_session)
) -> DelegateWorkflowUseCase:
    """Get DelegateWorkflowUseCase with injected dependencies"""
    uow = UnitOfWork(session)
    workflow_repo = WorkflowRepository(session)

    return DelegateWorkflowUseCase(
        uow=uow,
        workflow_repository=workflow_repo
    )


async def get_escalate_workflow_use_case(
    session: AsyncSession = Depends(get_session)
) -> EscalateWorkflowUseCase:
    """Get EscalateWorkflowUseCase with injected dependencies"""
    uow = UnitOfWork(session)
    workflow_repo = WorkflowRepository(session)

    return EscalateWorkflowUseCase(
        uow=uow,
        workflow_repository=workflow_repo
    )
