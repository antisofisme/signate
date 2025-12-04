"""Change User Password Use Case"""

from ..domain.user import User
from ..domain.interfaces import IUserRepository
from ..repositories.password_history_repo import PasswordHistoryRepository
from shared.errors import ValidationError, NotFoundError, ErrorCodes
from shared.auth import get_password_hash, verify_password  # Centralized password hashing (Fix #5)


class ChangePasswordUseCase:
    """Use case for changing user password"""

    # Number of recent passwords to check for reuse
    PASSWORD_HISTORY_LIMIT = 5

    def __init__(
        self,
        user_repo: IUserRepository,
        session_repository=None,
        password_history_repo: PasswordHistoryRepository = None
    ):
        """
        Initialize change password use case

        Args:
            user_repo: User repository
            session_repository: Optional session repository for revoking sessions (P0-16)
            password_history_repo: Optional password history repository for reuse prevention
        """
        self.user_repo = user_repo
        self.session_repository = session_repository
        self.password_history_repo = password_history_repo

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

        # SECURITY: Check password history to prevent reuse
        if self.password_history_repo:
            recent_hashes = self.password_history_repo.get_recent_hashes(
                user_id,
                limit=self.PASSWORD_HISTORY_LIMIT
            )
            for old_hash in recent_hashes:
                if verify_password(new_password, old_hash):
                    raise ValidationError(
                        message=f"Password tidak boleh sama dengan {self.PASSWORD_HISTORY_LIMIT} password terakhir",
                        code=ErrorCodes.VALIDATION_ERROR,
                        field="new_password"
                    )

        # Hash new password using centralized function (Fix #5)
        password_hash = get_password_hash(new_password)

        # Change password via repository
        updated_user = self.user_repo.change_password(user_id, password_hash)

        # SECURITY: Save new password to history
        if self.password_history_repo:
            self.password_history_repo.add_to_history(user_id, password_hash)
            # Cleanup old history entries (keep only last N)
            self.password_history_repo.cleanup_old_history(user_id, self.PASSWORD_HISTORY_LIMIT)

        # CRITICAL FIX P0-16: Revoke all user sessions after password change
        if self.session_repository:
            try:
                revoked_count = self.session_repository.revoke_all_user_sessions(user_id)
                print(f"[Password Change] Revoked {revoked_count} sessions for user {user_id}")
            except Exception as e:
                print(f"[Password Change] Failed to revoke sessions: {e}")
                # Don't fail password change if session revocation fails

        return updated_user
