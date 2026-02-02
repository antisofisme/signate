"""
Control API Dependencies
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import async_sessionmaker

from ...auth.api.dependencies import get_current_user
from ...auth.interfaces.token_service import TokenPayload
from ..interfaces import IControlRepository
from ..adapters import PostgresControlRepository
from ..use_cases import *

_session_factory: Optional[async_sessionmaker] = None


def init_control_dependencies(session_factory: async_sessionmaker) -> None:
    global _session_factory
    _session_factory = session_factory


def get_session_factory() -> async_sessionmaker:
    if _session_factory is None:
        raise RuntimeError("Control dependencies not initialized")
    return _session_factory


def get_control_repository(
    session_factory: async_sessionmaker = Depends(get_session_factory)
) -> IControlRepository:
    return PostgresControlRepository(session_factory)


def get_list_audit_use_case(repo: IControlRepository = Depends(get_control_repository)):
    return ListAuditUseCase(repo)


def get_get_audit_use_case(repo: IControlRepository = Depends(get_control_repository)):
    return GetAuditUseCase(repo)


def get_list_events_use_case(repo: IControlRepository = Depends(get_control_repository)):
    return ListEventsUseCase(repo)


def get_get_event_use_case(repo: IControlRepository = Depends(get_control_repository)):
    return GetEventUseCase(repo)


def get_get_metrics_use_case(repo: IControlRepository = Depends(get_control_repository)):
    return GetMetricsUseCase(repo)


def get_retry_dlq_use_case(repo: IControlRepository = Depends(get_control_repository)):
    return RetryDLQUseCase(repo)


async def get_current_tenant_id(current_user: TokenPayload = Depends(get_current_user)) -> UUID:
    if not current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "TENANT_REQUIRED"})
    return UUID(current_user.tenant_id)
