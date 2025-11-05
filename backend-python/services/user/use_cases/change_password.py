"""Change User Password Use Case"""

from passlib.context import CryptContext
from ..domain.user import User
from ..domain.interfaces import IUserRepository
from shared.errors import ValidationError, NotFoundError, ErrorCodes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ChangePasswordUseCase:
    """Use case for changing user password"""

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int, new_password: str) -> User:
        """
        Change user password

        Args:
            user_id: User ID
            new_password: New password (plain text, will be hashed)

        Returns:
            Updated User entity

        Raises:
            NotFoundError: If user not found
            ValidationError: If password validation fails
        """

        # Get user
        user = self.user_repo.find_by_id(user_id)

        if not user:
            raise NotFoundError(
                message=f"User dengan ID {user_id} tidak ditemukan",
                code=ErrorCodes.NOT_FOUND,
                resource="User",
                resource_id=str(user_id)
            )

        # Validate password strength
        if len(new_password) < 8:
            raise ValidationError(
                message="Password minimal 8 karakter",
                code=ErrorCodes.VALIDATION_ERROR,
                field="new_password"
            )

        # Hash new password
        password_hash = pwd_context.hash(new_password)

        # Change password via repository
        return self.user_repo.change_password(user_id, password_hash)
