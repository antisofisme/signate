"""
Project API Dependencies

Dependency injection setup for FastAPI.
"""

from typing import Callable, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..adapters import PostgresProjectRepository, PostgresMembershipRepository
from ..use_cases import (
    CreateProjectUseCase,
    UpdateProjectUseCase,
    DeleteProjectUseCase,
    GetProjectUseCase,
    ListProjectsUseCase,
    AddMemberUseCase,
    RemoveMemberUseCase,
    UpdateMemberRoleUseCase,
)


# Global session factory (set during init)
_session_factory: Optional[Callable] = None


def init_project_dependencies(session_factory: Callable) -> None:
    """Initialize project dependencies with session factory"""
    global _session_factory
    _session_factory = session_factory


def get_session_factory() -> Callable:
    """Get the configured session factory"""
    if _session_factory is None:
        raise RuntimeError("Project dependencies not initialized. Call init_project_dependencies first.")
    return _session_factory


async def get_project_repo(session: AsyncSession) -> PostgresProjectRepository:
    """Get project repository instance"""
    return PostgresProjectRepository(session)


async def get_membership_repo(session: AsyncSession) -> PostgresMembershipRepository:
    """Get membership repository instance"""
    return PostgresMembershipRepository(session)


async def get_create_project_use_case(
    session: AsyncSession,
    max_projects: int = 100,
) -> CreateProjectUseCase:
    """Get CreateProject use case"""
    project_repo = PostgresProjectRepository(session)
    membership_repo = PostgresMembershipRepository(session)
    return CreateProjectUseCase(project_repo, membership_repo, max_projects)


async def get_update_project_use_case(session: AsyncSession) -> UpdateProjectUseCase:
    """Get UpdateProject use case"""
    project_repo = PostgresProjectRepository(session)
    return UpdateProjectUseCase(project_repo)


async def get_delete_project_use_case(session: AsyncSession) -> DeleteProjectUseCase:
    """Get DeleteProject use case"""
    project_repo = PostgresProjectRepository(session)
    return DeleteProjectUseCase(project_repo)


async def get_get_project_use_case(session: AsyncSession) -> GetProjectUseCase:
    """Get GetProject use case"""
    project_repo = PostgresProjectRepository(session)
    return GetProjectUseCase(project_repo)


async def get_list_projects_use_case(session: AsyncSession) -> ListProjectsUseCase:
    """Get ListProjects use case"""
    project_repo = PostgresProjectRepository(session)
    return ListProjectsUseCase(project_repo)


async def get_add_member_use_case(session: AsyncSession) -> AddMemberUseCase:
    """Get AddMember use case"""
    project_repo = PostgresProjectRepository(session)
    membership_repo = PostgresMembershipRepository(session)
    return AddMemberUseCase(project_repo, membership_repo)


async def get_remove_member_use_case(session: AsyncSession) -> RemoveMemberUseCase:
    """Get RemoveMember use case"""
    project_repo = PostgresProjectRepository(session)
    membership_repo = PostgresMembershipRepository(session)
    return RemoveMemberUseCase(project_repo, membership_repo)


async def get_update_member_role_use_case(session: AsyncSession) -> UpdateMemberRoleUseCase:
    """Get UpdateMemberRole use case"""
    project_repo = PostgresProjectRepository(session)
    membership_repo = PostgresMembershipRepository(session)
    return UpdateMemberRoleUseCase(project_repo, membership_repo)
