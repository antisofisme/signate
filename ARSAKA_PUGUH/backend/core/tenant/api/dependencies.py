"""
Tenant API Dependencies

FastAPI dependency injection for tenant operations.

Source: INFRA-DEC-011-modular-architecture.md
"""

from typing import Optional
from uuid import UUID

from ..adapters.tenant_repository import PostgresTenantRepository
from ..adapters.membership_repository import PostgresMembershipRepository
from ..adapters.invitation_repository import PostgresInvitationRepository
from ..use_cases.create_tenant import CreateTenantUseCase
from ..use_cases.update_tenant import UpdateTenantUseCase
from ..use_cases.delete_tenant import DeleteTenantUseCase
from ..use_cases.get_tenant import GetTenantUseCase
from ..use_cases.list_tenants import ListTenantsUseCase
from ..use_cases.invite_member import InviteMemberUseCase
from ..use_cases.accept_invitation import AcceptInvitationUseCase
from ..use_cases.remove_member import RemoveMemberUseCase
from ..use_cases.update_member_role import UpdateMemberRoleUseCase
from ..use_cases.list_members import ListMembersUseCase


# Global state for dependencies
_session_factory = None
_user_repo = None


def init_tenant_dependencies(session_factory, user_repo=None):
    """Initialize tenant dependencies.

    Called during application startup.

    Args:
        session_factory: Async session factory for database access
        user_repo: Optional user repository for user lookups
    """
    global _session_factory, _user_repo
    _session_factory = session_factory
    _user_repo = user_repo


def get_tenant_repo() -> PostgresTenantRepository:
    """Get tenant repository instance."""
    if not _session_factory:
        raise RuntimeError("Tenant dependencies not initialized")
    return PostgresTenantRepository(_session_factory)


def get_membership_repo() -> PostgresMembershipRepository:
    """Get membership repository instance."""
    if not _session_factory:
        raise RuntimeError("Tenant dependencies not initialized")
    return PostgresMembershipRepository(_session_factory)


def get_invitation_repo() -> PostgresInvitationRepository:
    """Get invitation repository instance."""
    if not _session_factory:
        raise RuntimeError("Tenant dependencies not initialized")
    return PostgresInvitationRepository(_session_factory)


def get_create_tenant_use_case() -> CreateTenantUseCase:
    """Get create tenant use case."""
    return CreateTenantUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
    )


def get_update_tenant_use_case() -> UpdateTenantUseCase:
    """Get update tenant use case."""
    return UpdateTenantUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
    )


def get_delete_tenant_use_case() -> DeleteTenantUseCase:
    """Get delete tenant use case."""
    return DeleteTenantUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
    )


def get_get_tenant_use_case() -> GetTenantUseCase:
    """Get get tenant use case."""
    return GetTenantUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
    )


def get_list_tenants_use_case() -> ListTenantsUseCase:
    """Get list tenants use case."""
    return ListTenantsUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
    )


def get_invite_member_use_case() -> InviteMemberUseCase:
    """Get invite member use case."""
    return InviteMemberUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
        invitation_repo=get_invitation_repo(),
        user_repo=_user_repo,
    )


def get_accept_invitation_use_case() -> AcceptInvitationUseCase:
    """Get accept invitation use case."""
    return AcceptInvitationUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
        invitation_repo=get_invitation_repo(),
    )


def get_remove_member_use_case() -> RemoveMemberUseCase:
    """Get remove member use case."""
    return RemoveMemberUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
    )


def get_update_member_role_use_case() -> UpdateMemberRoleUseCase:
    """Get update member role use case."""
    return UpdateMemberRoleUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
    )


def get_list_members_use_case() -> ListMembersUseCase:
    """Get list members use case."""
    return ListMembersUseCase(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
        invitation_repo=get_invitation_repo(),
        user_repo=_user_repo,
    )
