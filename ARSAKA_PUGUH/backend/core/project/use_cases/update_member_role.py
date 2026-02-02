"""
Update Project Member Role Use Case
"""

from dataclasses import dataclass
from uuid import UUID

from ..domain import ProjectMembership, ProjectRole
from ..interfaces import IProjectRepository, IProjectMembershipRepository
from ..exceptions import ProjectNotFoundError, ProjectError


@dataclass
class UpdateMemberRoleInput:
    """Input for updating a member's role"""
    project_id: UUID
    tenant_id: UUID
    user_id: UUID
    new_role: str


@dataclass
class UpdateMemberRoleOutput:
    """Output after updating a member's role"""
    membership: ProjectMembership
    success: bool
    old_role: str
    new_role: str


class UpdateMemberRoleUseCase:
    """Update a member's role in a project"""

    def __init__(
        self,
        project_repo: IProjectRepository,
        membership_repo: IProjectMembershipRepository,
    ):
        self.project_repo = project_repo
        self.membership_repo = membership_repo

    async def execute(self, input_data: UpdateMemberRoleInput) -> UpdateMemberRoleOutput:
        """Execute role update"""

        # Verify project exists
        project = await self.project_repo.get_by_id(
            input_data.project_id, input_data.tenant_id
        )
        if not project:
            raise ProjectNotFoundError(str(input_data.project_id))

        # Get existing membership
        membership = await self.membership_repo.get(
            input_data.project_id, input_data.user_id
        )
        if not membership:
            raise ProjectError(
                "User is not a member of this project",
                code="NOT_A_MEMBER",
            )

        old_role = membership.role
        new_role = ProjectRole.from_string(input_data.new_role)

        # Prevent demoting last admin
        if old_role == ProjectRole.ADMIN and new_role != ProjectRole.ADMIN:
            admin_count = await self.membership_repo.count_admins(input_data.project_id)
            if admin_count <= 1:
                raise ProjectError(
                    "Cannot demote the last admin",
                    code="LAST_ADMIN",
                )

        # Update role
        updated_membership = await self.membership_repo.update_role(
            input_data.project_id, input_data.user_id, new_role
        )

        return UpdateMemberRoleOutput(
            membership=updated_membership,
            success=True,
            old_role=old_role.value,
            new_role=new_role.value,
        )
