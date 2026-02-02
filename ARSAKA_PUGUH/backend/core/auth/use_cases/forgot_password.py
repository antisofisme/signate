"""
Forgot Password Use Case

Handles password reset request.
Creates reset token and (TODO) sends email.

Source: INFRA-DEC-008-auth-flow.md
"""

from dataclasses import dataclass

from ..interfaces.token_service import ITokenService
from ..interfaces.user_repository import IUserRepository


@dataclass
class ForgotPasswordResult:
    """Forgot password result."""
    message: str
    reset_token: str = None  # Only in dev/test


class ForgotPasswordUseCase:
    """Request password reset."""

    def __init__(
        self,
        token_service: ITokenService,
        user_repo: IUserRepository,
        email_service=None,  # For sending reset email
    ):
        self._tokens = token_service
        self._users = user_repo
        self._email = email_service

    async def execute(self, email: str) -> ForgotPasswordResult:
        """Execute forgot password.

        Always returns success to prevent email enumeration.

        Args:
            email: User's email

        Returns:
            ForgotPasswordResult with generic message
        """
        message = "If an account exists with this email, a password reset link has been sent"
        reset_token = None

        # Find user (don't reveal if not found)
        user = await self._users.get_by_email(email)

        if user:
            # Create reset token
            reset_token = await self._tokens.create_password_reset_token(
                str(user.user_id)
            )

            # TODO: Send reset email
            # if self._email:
            #     await self._email.send_password_reset(user.email, reset_token)

        return ForgotPasswordResult(
            message=message,
            reset_token=reset_token,  # Remove in production
        )
