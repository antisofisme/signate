"""
Workflow API Dependencies
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import async_sessionmaker

from ...auth.api.dependencies import get_current_user
from ...auth.interfaces.token_service import TokenPayload
from ..interfaces import IWorkflowRepository
from ..adapters import PostgresWorkflowRepository
from ..use_cases import *

_session_factory: Optional[async_sessionmaker] = None


def init_workflow_dependencies(session_factory: async_sessionmaker) -> None:
    global _session_factory
    _session_factory = session_factory


def get_session_factory() -> async_sessionmaker:
    if _session_factory is None:
        raise RuntimeError("Workflow dependencies not initialized")
    return _session_factory


def get_workflow_repository(
    session_factory: async_sessionmaker = Depends(get_session_factory)
) -> IWorkflowRepository:
    return PostgresWorkflowRepository(session_factory)


def get_list_workflows_use_case(repo: IWorkflowRepository = Depends(get_workflow_repository)):
    return ListWorkflowsUseCase(repo)


def get_get_workflow_use_case(repo: IWorkflowRepository = Depends(get_workflow_repository)):
    return GetWorkflowUseCase(repo)


def get_approve_workflow_use_case(repo: IWorkflowRepository = Depends(get_workflow_repository)):
    return ApproveWorkflowUseCase(repo)


def get_reject_workflow_use_case(repo: IWorkflowRepository = Depends(get_workflow_repository)):
    return RejectWorkflowUseCase(repo)


def get_delegate_workflow_use_case(repo: IWorkflowRepository = Depends(get_workflow_repository)):
    return DelegateWorkflowUseCase(repo)


def get_escalate_workflow_use_case(repo: IWorkflowRepository = Depends(get_workflow_repository)):
    return EscalateWorkflowUseCase(repo)


async def get_current_user_id(current_user: TokenPayload = Depends(get_current_user)) -> UUID:
    return UUID(current_user.sub)


async def get_current_tenant_id(current_user: TokenPayload = Depends(get_current_user)) -> UUID:
    if not current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "TENANT_REQUIRED"})
    return UUID(current_user.tenant_id)
