"""
List Projects Use Case
"""

from dataclasses import dataclass
from typing import List
from uuid import UUID

from ..domain import Project
from ..interfaces import IProjectRepository


@dataclass
class ListProjectsInput:
    """Input for listing projects"""
    tenant_id: UUID
    include_deleted: bool = False
    limit: int = 100
    offset: int = 0


@dataclass
class ListProjectsOutput:
    """Output after listing projects"""
    projects: List[Project]
    total: int
    limit: int
    offset: int


class ListProjectsUseCase:
    """List all projects for a tenant"""

    def __init__(self, project_repo: IProjectRepository):
        self.project_repo = project_repo

    async def execute(self, input_data: ListProjectsInput) -> ListProjectsOutput:
        """Execute project listing"""

        projects = await self.project_repo.list_by_tenant(
            tenant_id=input_data.tenant_id,
            include_deleted=input_data.include_deleted,
            limit=input_data.limit,
            offset=input_data.offset,
        )

        total = await self.project_repo.count_by_tenant(input_data.tenant_id)

        return ListProjectsOutput(
            projects=projects,
            total=total,
            limit=input_data.limit,
            offset=input_data.offset,
        )
