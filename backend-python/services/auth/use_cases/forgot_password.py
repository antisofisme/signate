"""
Forgot Password Use Case
Initiates password reset process for a user
"""

from shared.password_reset import get_password_reset_manager
from shared.errors import NotFoundError
from ..repositories.user_repo import UserRepository


class ForgotPasswordUseCase:
    """
    Handle forgot password request

    Generates a secure reset token for the user.
    In production, this would send an email with the reset link.
    For development/testing, the token is returned in the response.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Args:
            user_repository: UserRepository instance
        """
        self.user_repository = user_repository
        self.reset_manager = get_password_reset_manager()

    def execute(self, email: str) -> dict:
        """
        Execute forgot password use case

        Args:
            email: User's email address

        Returns:
            Dict with token and message

        Raises:
            NotFoundError: If user with email not found

        Example:
            >>> use_case = ForgotPasswordUseCase(user_repo)
            >>> result = use_case.execute("user@example.com")
            >>> print(result["reset_token"])
        """
        # Find user by email
        user = self.user_repository.find_by_email(email)

        if not user:
            # Security: Don't reveal if email exists or not
            # Return success but don't actually send anything
            # This prevents email enumeration attacks
            return {
                "message": "If an account with that email exists, a password reset link has been sent.",
                "reset_token": None  # No token for non-existent user
            }

        # Check if user is active
        if not user.is_active:
            # Return same message for security (don't reveal account status)
            return {
                "message": "If an account with that email exists, a password reset link has been sent.",
                "reset_token": None
            }

        # Generate reset token
        reset_token = self.reset_manager.generate_token(user.id, user.email)

        # TODO Production: Send email with reset link
        # email_service.send_password_reset(
        #     to_email=user.email,
        #     reset_link=f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
        #     user_name=user.full_name
        # )

        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "reset_token": reset_token  # Include token in response for development/testing
        }
