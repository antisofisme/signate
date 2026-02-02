"""
Delete Project Use Case
"""

from dataclasses import dataclass
from uuid import UUID

from ..interfaces import IProjectRepository
from ..exceptions import ProjectNotFoundError


@dataclass
class DeleteProjectInput:
    """Input for deleting a project"""
    project_id: UUID
    tenant_id: UUID


@dataclass
class DeleteProjectOutput:
    """Output after deleting a project"""
    success: bool
    message: str


class DeleteProjectUseCase:
    """Soft delete a project"""

    def __init__(self, project_repo: IProjectRepository):
        self.project_repo = project_repo

    async def execute(self, input_data: DeleteProjectInput) -> DeleteProjectOutput:
        """Execute project deletion"""

        # Verify project exists
        project = await self.project_repo.get_by_id(
            input_data.project_id, input_data.tenant_id
        )
        if not project:
            raise ProjectNotFoundError(str(input_data.project_id))

        # Soft delete
        deleted = await self.project_repo.delete(
            input_data.project_id, input_data.tenant_id
        )

        if deleted:
            return DeleteProjectOutput(
                success=True,
                message=f"Project '{project.name}' deleted successfully",
            )
        else:
            return DeleteProjectOutput(
                success=False,
                message="Failed to delete project",
            )
