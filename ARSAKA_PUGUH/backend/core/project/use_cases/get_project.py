"""
Get Project Use Case
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..domain import Project
from ..interfaces import IProjectRepository
from ..exceptions import ProjectNotFoundError


@dataclass
class GetProjectInput:
    """Input for getting a project"""
    tenant_id: UUID
    project_id: Optional[UUID] = None
    slug: Optional[str] = None


class GetProjectUseCase:
    """Get a project by ID or slug"""

    def __init__(self, project_repo: IProjectRepository):
        self.project_repo = project_repo

    async def execute(self, input_data: GetProjectInput) -> Project:
        """Execute project retrieval"""

        project = None

        if input_data.project_id:
            project = await self.project_repo.get_by_id(
                input_data.project_id, input_data.tenant_id
            )
        elif input_data.slug:
            project = await self.project_repo.get_by_slug(
                input_data.slug, input_data.tenant_id
            )

        if not project:
            identifier = str(input_data.project_id or input_data.slug)
            raise ProjectNotFoundError(identifier)

        return project
