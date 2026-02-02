"""
Create Project Use Case
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..domain import Project, ProjectEnvironment, ProjectMembership, ProjectRole
from ..interfaces import IProjectRepository, IProjectMembershipRepository
from ..exceptions import ProjectSlugExistsError, ProjectLimitExceededError


@dataclass
class CreateProjectInput:
    """Input for creating a project"""
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    environment: str = "development"
    created_by: Optional[UUID] = None


@dataclass
class CreateProjectOutput:
    """Output after creating a project"""
    project: Project
    success: bool
    message: str


class CreateProjectUseCase:
    """Create a new project within a tenant"""

    def __init__(
        self,
        project_repo: IProjectRepository,
        membership_repo: IProjectMembershipRepository,
        max_projects_per_tenant: int = 100,  # Default limit, override from billing
    ):
        self.project_repo = project_repo
        self.membership_repo = membership_repo
        self.max_projects = max_projects_per_tenant

    async def execute(self, input_data: CreateProjectInput) -> CreateProjectOutput:
        """Execute project creation"""

        # Check tenant project limit
        current_count = await self.project_repo.count_by_tenant(input_data.tenant_id)
        if current_count >= self.max_projects:
            raise ProjectLimitExceededError(current_count, self.max_projects)

        # Generate slug from name
        slug = Project.generate_slug(input_data.name)

        # Ensure slug uniqueness within tenant
        base_slug = slug
        counter = 1
        while await self.project_repo.slug_exists(slug, input_data.tenant_id):
            slug = f"{base_slug}-{counter}"
            counter += 1
            if counter > 100:
                raise ProjectSlugExistsError(base_slug, str(input_data.tenant_id))

        # Parse environment
        try:
            environment = ProjectEnvironment(input_data.environment.lower())
        except ValueError:
            environment = ProjectEnvironment.DEVELOPMENT

        # Create project entity
        project = Project(
            project_id=uuid4(),
            tenant_id=input_data.tenant_id,
            name=input_data.name,
            slug=slug,
            description=input_data.description,
            environment=environment,
            settings={},
            is_active=True,
            is_deleted=False,
            created_by=input_data.created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Persist project
        created_project = await self.project_repo.create(project)

        # Add creator as project admin if specified
        if input_data.created_by:
            membership = ProjectMembership(
                project_id=created_project.project_id,
                user_id=input_data.created_by,
                role=ProjectRole.ADMIN,
            )
            await self.membership_repo.create(membership)

        return CreateProjectOutput(
            project=created_project,
            success=True,
            message=f"Project '{created_project.name}' created successfully",
        )
