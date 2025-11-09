"""
Delete Role Use Case
Delete custom role
"""

from ..repositories.role_repo import RoleRepository
from shared.errors import NotFoundError, AuthorizationError


class DeleteRoleUseCase:
    """Delete custom role"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    def execute(self, role_id: int) -> bool:
        """
        Delete role

        Args:
            role_id: Role ID

        Returns:
            True if deleted

        Raises:
            NotFoundError: If role not found
            AuthorizationError: If trying to delete system role
        """
        # Find role
        role = self.role_repository.find_by_id(role_id)
        if not role:
            raise NotFoundError(message=f"Role with ID {role_id} not found")

        # Can't delete system roles
        if role.is_system_role:
            raise AuthorizationError(
                message="System roles cannot be deleted"
            )

        # Delete role
        return self.role_repository.delete(role_id)
