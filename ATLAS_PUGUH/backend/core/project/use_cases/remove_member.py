"""
Remove Project Member Use Case
"""

from dataclasses import dataclass
from uuid import UUID

from ..domain import ProjectRole
from ..interfaces import IProjectRepository, IProjectMembershipRepository
from ..exceptions import ProjectNotFoundError, ProjectError


@dataclass
class RemoveMemberInput:
    """Input for removing a member"""
    project_id: UUID
    tenant_id: UUID
    user_id: UUID


@dataclass
class RemoveMemberOutput:
    """Output after removing a member"""
    success: bool
    message: str


class RemoveMemberUseCase:
    """Remove a member from a project"""

    def __init__(
        self,
        project_repo: IProjectRepository,
        membership_repo: IProjectMembershipRepository,
    ):
        self.project_repo = project_repo
        self.membership_repo = membership_repo

    async def execute(self, input_data: RemoveMemberInput) -> RemoveMemberOutput:
        """Execute member removal"""

        # Verify project exists
        project = await self.project_repo.get_by_id(
            input_data.project_id, input_data.tenant_id
        )
        if not project:
            raise ProjectNotFoundError(str(input_data.project_id))

        # Check if user is a member
        membership = await self.membership_repo.get(
            input_data.project_id, input_data.user_id
        )
        if not membership:
            return RemoveMemberOutput(
                success=False,
                message="User is not a member of this project",
            )

        # Prevent removing last admin
        if membership.role == ProjectRole.ADMIN:
            admin_count = await self.membership_repo.count_admins(input_data.project_id)
            if admin_count <= 1:
                raise ProjectError(
                    "Cannot remove the last admin from the project",
                    code="LAST_ADMIN",
                )

        # Remove membership
        removed = await self.membership_repo.delete(
            input_data.project_id, input_data.user_id
        )

        if removed:
            return RemoveMemberOutput(
                success=True,
                message="User removed from project",
            )
        else:
            return RemoveMemberOutput(
                success=False,
                message="Failed to remove user from project",
            )
