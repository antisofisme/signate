"""
Reset Password Use Case
Completes password reset process using a valid token

Updated to use centralized password hashing (Fix #5)
"""

from shared.password_reset import get_password_reset_manager
from shared.errors import ValidationError, NotFoundError
from shared.auth import get_password_hash  # Centralized password hashing
from ..repositories.user_repo import UserRepository


class ResetPasswordUseCase:
    """
    Handle password reset with token

    Validates the reset token and updates the user's password.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Args:
            user_repository: UserRepository instance
        """
        self.user_repository = user_repository
        self.reset_manager = get_password_reset_manager()

    def execute(self, token: str, new_password: str) -> dict:
        """
        Execute reset password use case

        Args:
            token: Password reset token
            new_password: New password to set

        Returns:
            Dict with success message

        Raises:
            ValidationError: If token is invalid or expired
            NotFoundError: If user not found

        Example:
            >>> use_case = ResetPasswordUseCase(user_repo)
            >>> result = use_case.execute(token="abc123...", new_password="newpass123")
            >>> print(result["message"])
            Password has been reset successfully
        """
        # Validate and consume token (one-time use)
        is_valid, user_id, error = self.reset_manager.consume_token(token)

        if not is_valid:
            raise ValidationError(error or "Invalid reset token")

        # Get user
        user = self.user_repository.find_by_id(user_id)

        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Check if user is active
        if not user.is_active:
            raise ValidationError("This account is not active")

        # Hash new password using centralized function (Fix #5)
        password_hash = get_password_hash(new_password)

        # Update password
        user.password_hash = password_hash
        self.user_repository.save(user)

        # Invalidate any other reset tokens for this user
        self.reset_manager.invalidate_user_tokens(user_id)

        return {
            "message": "Password has been reset successfully. You can now login with your new password."
        }
