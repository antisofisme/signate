"""
Reset Password Use Case

Handles password reset with token.
Updates password and invalidates all sessions.

Source: INFRA-DEC-008-auth-flow.md
"""

import re
from dataclasses import dataclass
from uuid import UUID

from ..interfaces.auth_provider import IAuthProvider
from ..interfaces.token_service import ITokenService
from ..interfaces.user_repository import IUserRepository
from ..domain.events import PasswordReset
from ..exceptions import ValidationError


@dataclass
class ResetPasswordResult:
    """Reset password result."""
    message: str


class ResetPasswordUseCase:
    """Reset password using token."""

    MIN_PASSWORD_LENGTH = 8
    PASSWORD_PATTERN = re.compile(r'^(?=.*[A-Z])(?=.*\d).+$')

    def __init__(
        self,
        auth_provider: IAuthProvider,
        token_service: ITokenService,
        user_repo: IUserRepository,
        event_bus=None,
    ):
        self._auth = auth_provider
        self._tokens = token_service
        self._users = user_repo
        self._events = event_bus

    async def execute(self, token: str, new_password: str) -> ResetPasswordResult:
        """Execute password reset.

        Args:
            token: Reset token from email
            new_password: New password

        Returns:
            ResetPasswordResult with success message

        Raises:
            TokenInvalidError: If token is invalid
            TokenExpiredError: If token is expired
            ValidationError: If password is invalid
        """
        # 1. Validate new password
        self._validate_password(new_password)

        # 2. Verify token and get user_id
        user_id = await self._tokens.verify_password_reset_token(token)

        # 3. Get user
        user = await self._users.get_by_id(UUID(user_id))
        if not user:
            from ..exceptions import TokenInvalidError
            raise TokenInvalidError("User not found")

        # 4. Hash new password
        password_hash = await self._auth.hash_password(new_password)

        # 5. Update password
        await self._users.update_password(user.user_id, password_hash)

        # 6. Mark token as used
        await self._tokens.mark_token_used(token)

        # 7. TODO: Invalidate all existing sessions
        # This would revoke all refresh tokens for this user

        # 8. Emit event
        if self._events:
            await self._events.publish(PasswordReset(
                user_id=user.user_id,
                email=user.email,
            ))

        return ResetPasswordResult(
            message="Password reset successful. Please log in with your new password."
        )

    def _validate_password(self, password: str) -> None:
        """Validate password requirements."""
        if not password:
            raise ValidationError("Password is required", field="new_password")

        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters",
                field="new_password"
            )

        if not self.PASSWORD_PATTERN.match(password):
            raise ValidationError(
                "Password must contain at least 1 uppercase letter and 1 number",
                field="new_password"
            )
