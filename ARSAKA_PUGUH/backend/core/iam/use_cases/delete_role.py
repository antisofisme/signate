"""
Delete Role Use Case
"""

from uuid import UUID

from ..interfaces import IIAMRepository


class DeleteRoleUseCase:
    """Use case for deleting a role."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, role_id: UUID) -> bool:
        """
        Delete a role.

        Args:
            tenant_id: Tenant UUID
            role_id: Role UUID

        Returns:
            True if deleted successfully

        Raises:
            RoleNotFoundError: If role not found
            SystemRoleError: If attempting to delete a system role
            RoleInUseError: If role is assigned to users
        """
        return await self._repository.delete_role(tenant_id, role_id)
