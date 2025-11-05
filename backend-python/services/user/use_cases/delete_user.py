"""Delete User Use Case"""

from ..domain.user import User
from ..domain.interfaces import IUserRepository
from shared.errors import ValidationError, NotFoundError


class DeleteUserUseCase:
    """Use case for deleting user (hard delete - permanently remove)"""

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> User:
        """
        Hard delete user (permanently remove from database)

        Args:
            user_id: User ID to delete

        Returns:
            User entity BEFORE deletion (for audit logging)

        Raises:
            NotFoundError: If user not found
            ValidationError: If user cannot be deleted
        """

        # Get user before deletion
        user = self.user_repo.find_by_id(user_id)

        if not user:
            raise NotFoundError(
                message=f"User dengan ID {user_id} tidak ditemukan",
                details={"resource_type": "user", "resource_id": user_id}
            )

        # TODO: Check if user has devices before deleting
        # For now, we'll allow deletion

        # Hard delete via repository
        success = self.user_repo.delete(user_id)

        if not success:
            raise ValidationError(
                message="Gagal menghapus user",
                details={"user_id": user_id}
            )

        # Return the user data before deletion
        return user
