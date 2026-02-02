"""
Decision API Dependencies

Dependency injection for decision use cases.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import async_sessionmaker

from ...auth.api.dependencies import get_current_user
from ...auth.interfaces.token_service import TokenPayload
from ..interfaces import IDecisionRepository
from ..adapters import PostgresDecisionRepository
from ..use_cases import (
    ListRulesUseCase,
    GetRuleUseCase,
    CreateRuleUseCase,
    UpdateRuleUseCase,
    DeleteRuleUseCase,
    ActivateRuleUseCase,
    DeactivateRuleUseCase,
    ListDecisionsUseCase,
    GetDecisionUseCase,
)


# Global session factory - initialized at startup
_session_factory: Optional[async_sessionmaker] = None


def init_decision_dependencies(session_factory: async_sessionmaker) -> None:
    """Initialize Decision dependencies with database session factory."""
    global _session_factory
    _session_factory = session_factory


def get_session_factory() -> async_sessionmaker:
    """Get session factory dependency."""
    if _session_factory is None:
        raise RuntimeError("Decision dependencies not initialized")
    return _session_factory


def get_decision_repository(
    session_factory: async_sessionmaker = Depends(get_session_factory)
) -> IDecisionRepository:
    """Get Decision repository dependency."""
    return PostgresDecisionRepository(session_factory)


# =============================================================================
# Use Case Dependencies
# =============================================================================

def get_list_rules_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> ListRulesUseCase:
    return ListRulesUseCase(repository)


def get_get_rule_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> GetRuleUseCase:
    return GetRuleUseCase(repository)


def get_create_rule_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> CreateRuleUseCase:
    return CreateRuleUseCase(repository)


def get_update_rule_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> UpdateRuleUseCase:
    return UpdateRuleUseCase(repository)


def get_delete_rule_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> DeleteRuleUseCase:
    return DeleteRuleUseCase(repository)


def get_activate_rule_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> ActivateRuleUseCase:
    return ActivateRuleUseCase(repository)


def get_deactivate_rule_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> DeactivateRuleUseCase:
    return DeactivateRuleUseCase(repository)


def get_list_decisions_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> ListDecisionsUseCase:
    return ListDecisionsUseCase(repository)


def get_get_decision_use_case(
    repository: IDecisionRepository = Depends(get_decision_repository)
) -> GetDecisionUseCase:
    return GetDecisionUseCase(repository)


# =============================================================================
# Auth Helpers
# =============================================================================

async def get_current_user_id(
    current_user: TokenPayload = Depends(get_current_user)
) -> UUID:
    """Extract user ID from JWT token."""
    return UUID(current_user.sub)


async def get_current_tenant_id(
    current_user: TokenPayload = Depends(get_current_user)
) -> UUID:
    """Extract tenant ID from JWT token."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TENANT_REQUIRED",
                "message": "Tenant context required",
            }
        )
    return UUID(current_user.tenant_id)
