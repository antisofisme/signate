"""
Add Project Member Use Case
"""

from dataclasses import dataclass
from uuid import UUID

from ..domain import ProjectMembership, ProjectRole
from ..interfaces import IProjectRepository, IProjectMembershipRepository
from ..exceptions import ProjectNotFoundError


@dataclass
class AddMemberInput:
    """Input for adding a member"""
    project_id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str = "member"


@dataclass
class AddMemberOutput:
    """Output after adding a member"""
    membership: ProjectMembership
    success: bool
    message: str


class AddMemberUseCase:
    """Add a member to a project"""

    def __init__(
        self,
        project_repo: IProjectRepository,
        membership_repo: IProjectMembershipRepository,
    ):
        self.project_repo = project_repo
        self.membership_repo = membership_repo

    async def execute(self, input_data: AddMemberInput) -> AddMemberOutput:
        """Execute member addition"""

        # Verify project exists
        project = await self.project_repo.get_by_id(
            input_data.project_id, input_data.tenant_id
        )
        if not project:
            raise ProjectNotFoundError(str(input_data.project_id))

        # Parse role
        role = ProjectRole.from_string(input_data.role)

        # Create membership
        membership = ProjectMembership(
            project_id=input_data.project_id,
            user_id=input_data.user_id,
            role=role,
        )

        created_membership = await self.membership_repo.create(membership)

        return AddMemberOutput(
            membership=created_membership,
            success=True,
            message=f"User added to project with role '{role.value}'",
        )
