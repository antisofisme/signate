"""
Update Project Use Case
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID

from ..domain import Project, ProjectEnvironment
from ..interfaces import IProjectRepository
from ..exceptions import ProjectNotFoundError, ProjectSlugExistsError


@dataclass
class UpdateProjectInput:
    """Input for updating a project"""
    project_id: UUID
    tenant_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


@dataclass
class UpdateProjectOutput:
    """Output after updating a project"""
    project: Project
    success: bool
    changes: Dict[str, Any]


class UpdateProjectUseCase:
    """Update an existing project"""

    def __init__(self, project_repo: IProjectRepository):
        self.project_repo = project_repo

    async def execute(self, input_data: UpdateProjectInput) -> UpdateProjectOutput:
        """Execute project update"""

        # Get existing project
        project = await self.project_repo.get_by_id(
            input_data.project_id, input_data.tenant_id
        )
        if not project:
            raise ProjectNotFoundError(str(input_data.project_id))

        changes = {}

        # Update name (regenerate slug if name changed)
        if input_data.name is not None and input_data.name != project.name:
            new_slug = Project.generate_slug(input_data.name)

            # Check slug uniqueness
            if await self.project_repo.slug_exists(
                new_slug, input_data.tenant_id, exclude_id=project.project_id
            ):
                # Try with suffix
                base_slug = new_slug
                counter = 1
                while await self.project_repo.slug_exists(
                    new_slug, input_data.tenant_id, exclude_id=project.project_id
                ):
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                    if counter > 100:
                        raise ProjectSlugExistsError(base_slug, str(input_data.tenant_id))

            changes["name"] = {"old": project.name, "new": input_data.name}
            changes["slug"] = {"old": project.slug, "new": new_slug}
            project.name = input_data.name
            project.slug = new_slug

        # Update description
        if input_data.description is not None:
            changes["description"] = {"old": project.description, "new": input_data.description}
            project.description = input_data.description

        # Update environment
        if input_data.environment is not None:
            try:
                new_env = ProjectEnvironment(input_data.environment.lower())
                if new_env != project.environment:
                    changes["environment"] = {
                        "old": project.environment.value,
                        "new": new_env.value,
                    }
                    project.environment = new_env
            except ValueError:
                pass  # Keep existing environment

        # Update settings
        if input_data.settings is not None:
            changes["settings"] = {"old": project.settings, "new": input_data.settings}
            project.settings = input_data.settings

        # Update active status
        if input_data.is_active is not None and input_data.is_active != project.is_active:
            changes["is_active"] = {"old": project.is_active, "new": input_data.is_active}
            project.is_active = input_data.is_active

        # Persist changes
        if changes:
            updated_project = await self.project_repo.update(project)
        else:
            updated_project = project

        return UpdateProjectOutput(
            project=updated_project,
            success=True,
            changes=changes,
        )
