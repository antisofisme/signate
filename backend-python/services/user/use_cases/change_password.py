"""Change User Password Use Case"""

from passlib.context import CryptContext
from ..domain.user import User
from ..domain.interfaces import IUserRepository
from shared.errors import ValidationError, NotFoundError, ErrorCodes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ChangePasswordUseCase:
    """Use case for changing user password"""

    def __init__(self, user_repo: IUserRepository, session_repository=None):
        """
        Initialize change password use case

        Args:
            user_repo: User repository
            session_repository: Optional session repository for revoking sessions (P0-16)
        """
        self.user_repo = user_repo
        self.session_repository = session_repository

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
        updated_user = self.user_repo.change_password(user_id, password_hash)

        # CRITICAL FIX P0-16: Revoke all user sessions after password change
        if self.session_repository:
            try:
                revoked_count = self.session_repository.revoke_all_user_sessions(user_id)
                print(f"[Password Change] Revoked {revoked_count} sessions for user {user_id}")
            except Exception as e:
                print(f"[Password Change] Failed to revoke sessions: {e}")
                # Don't fail password change if session revocation fails

        return updated_user
