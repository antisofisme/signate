"""
IAM API Dependencies

Dependency injection for IAM use cases.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import async_sessionmaker

from ...auth.api.dependencies import get_current_user
from ...auth.interfaces.token_service import TokenPayload
from ..interfaces import IIAMRepository
from ..adapters import PostgresIAMRepository
from ..use_cases import (
    ListUsersUseCase,
    GetUserUseCase,
    ListRolesUseCase,
    GetRoleUseCase,
    GetPermissionsUseCase,
    ListServiceAccountsUseCase,
    CreateRoleUseCase,
    UpdateRoleUseCase,
    DeleteRoleUseCase,
    AssignRoleToUserUseCase,
    RevokeRoleFromUserUseCase,
)


# Global session factory - initialized at startup
_session_factory: Optional[async_sessionmaker] = None


def init_iam_dependencies(session_factory: async_sessionmaker) -> None:
    """Initialize IAM dependencies with database session factory.

    Called during application startup.

    Args:
        session_factory: SQLAlchemy async session factory
    """
    global _session_factory
    _session_factory = session_factory


def get_session_factory() -> async_sessionmaker:
    """Get session factory dependency."""
    if _session_factory is None:
        raise RuntimeError("IAM dependencies not initialized. Call init_iam_dependencies first.")
    return _session_factory


def get_iam_repository(
    session_factory: async_sessionmaker = Depends(get_session_factory)
) -> IIAMRepository:
    """Get IAM repository dependency."""
    return PostgresIAMRepository(session_factory)


# =============================================================================
# Use Case Dependencies
# =============================================================================

def get_list_users_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> ListUsersUseCase:
    """Get list users use case."""
    return ListUsersUseCase(repository)


def get_get_user_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> GetUserUseCase:
    """Get get user use case."""
    return GetUserUseCase(repository)


def get_list_roles_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> ListRolesUseCase:
    """Get list roles use case."""
    return ListRolesUseCase(repository)


def get_get_role_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> GetRoleUseCase:
    """Get get role use case."""
    return GetRoleUseCase(repository)


def get_get_permissions_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> GetPermissionsUseCase:
    """Get get permissions use case."""
    return GetPermissionsUseCase(repository)


def get_list_service_accounts_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> ListServiceAccountsUseCase:
    """Get list service accounts use case."""
    return ListServiceAccountsUseCase(repository)


# =============================================================================
# Write Use Case Dependencies
# =============================================================================

def get_create_role_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> CreateRoleUseCase:
    """Get create role use case."""
    return CreateRoleUseCase(repository)


def get_update_role_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> UpdateRoleUseCase:
    """Get update role use case."""
    return UpdateRoleUseCase(repository)


def get_delete_role_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> DeleteRoleUseCase:
    """Get delete role use case."""
    return DeleteRoleUseCase(repository)


def get_assign_role_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> AssignRoleToUserUseCase:
    """Get assign role to user use case."""
    return AssignRoleToUserUseCase(repository)


def get_revoke_role_use_case(
    repository: IIAMRepository = Depends(get_iam_repository)
) -> RevokeRoleFromUserUseCase:
    """Get revoke role from user use case."""
    return RevokeRoleFromUserUseCase(repository)


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
    """Extract tenant ID from JWT token.

    Raises HTTPException if no tenant context.
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TENANT_REQUIRED",
                "message": "Tenant context required. Please select a tenant.",
            }
        )
    return UUID(current_user.tenant_id)
