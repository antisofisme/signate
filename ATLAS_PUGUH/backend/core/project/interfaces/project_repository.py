"""
Project Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain import Project


class IProjectRepository(ABC):
    """Interface for project persistence"""

    @abstractmethod
    async def create(self, project: Project) -> Project:
        """Create a new project"""
        pass

    @abstractmethod
    async def get_by_id(self, project_id: UUID, tenant_id: UUID) -> Optional[Project]:
        """Get project by ID within tenant"""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str, tenant_id: UUID) -> Optional[Project]:
        """Get project by slug within tenant"""
        pass

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Project]:
        """List all projects for a tenant"""
        pass

    @abstractmethod
    async def update(self, project: Project) -> Project:
        """Update an existing project"""
        pass

    @abstractmethod
    async def delete(self, project_id: UUID, tenant_id: UUID) -> bool:
        """Soft delete a project"""
        pass

    @abstractmethod
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count active projects for a tenant"""
        pass

    @abstractmethod
    async def slug_exists(self, slug: str, tenant_id: UUID, exclude_id: Optional[UUID] = None) -> bool:
        """Check if slug exists in tenant"""
        pass
