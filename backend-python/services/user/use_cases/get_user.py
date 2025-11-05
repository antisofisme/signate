"""Get User Use Case"""

from ..domain.user import User
from ..domain.interfaces import IUserRepository
from shared.errors import NotFoundError


class GetUserUseCase:
    """Use case for getting single user"""

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> User:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User entity

        Raises:
            NotFoundError: If user not found
        """

        user = self.user_repo.find_by_id(user_id)

        if not user:
            raise NotFoundError(
                message=f"User dengan ID {user_id} tidak ditemukan",
                details={"resource_type": "user", "resource_id": user_id}
            )

        return user
