"""
Project Membership Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain import ProjectMembership, ProjectRole


class IProjectMembershipRepository(ABC):
    """Interface for project membership persistence"""

    @abstractmethod
    async def create(self, membership: ProjectMembership) -> ProjectMembership:
        """Add a member to a project"""
        pass

    @abstractmethod
    async def get(self, project_id: UUID, user_id: UUID) -> Optional[ProjectMembership]:
        """Get membership for user in project"""
        pass

    @abstractmethod
    async def list_by_project(self, project_id: UUID) -> List[ProjectMembership]:
        """List all members of a project"""
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID, tenant_id: UUID) -> List[ProjectMembership]:
        """List all project memberships for a user within tenant"""
        pass

    @abstractmethod
    async def update_role(
        self, project_id: UUID, user_id: UUID, new_role: ProjectRole
    ) -> Optional[ProjectMembership]:
        """Update member's role"""
        pass

    @abstractmethod
    async def delete(self, project_id: UUID, user_id: UUID) -> bool:
        """Remove member from project"""
        pass

    @abstractmethod
    async def has_access(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if user has any access to project"""
        pass

    @abstractmethod
    async def count_admins(self, project_id: UUID) -> int:
        """Count admins in project (for preventing last admin removal)"""
        pass
