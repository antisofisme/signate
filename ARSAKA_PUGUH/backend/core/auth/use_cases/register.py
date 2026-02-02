"""
Register Use Case

Handles user registration with email/password.
Creates user, tenant, default project, and membership.

Source: INFRA-DEC-008-auth-flow.md
"""

import re
from dataclasses import dataclass
from typing import Optional

from ..interfaces.auth_provider import IAuthProvider
from ..interfaces.token_service import ITokenService
from ..interfaces.user_repository import IUserRepository
from ..domain.user import User
from ..domain.events import UserRegistered
from ..exceptions import ValidationError, EmailExistsError


@dataclass
class RegisterRequest:
    """Registration request data."""
    email: str
    password: str
    display_name: str


@dataclass
class RegisterResult:
    """Registration result."""
    user_id: str
    email: str
    status: str
    verification_token: Optional[str] = None  # Only in dev/test


class RegisterUseCase:
    """Register a new user with email/password."""

    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_PATTERN = re.compile(r'^(?=.*[A-Z])(?=.*\d).+$')

    # Email pattern
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(
        self,
        auth_provider: IAuthProvider,
        token_service: ITokenService,
        user_repo: IUserRepository,
        tenant_service=None,  # Will be injected for auto-provisioning
        event_bus=None,  # For domain events
    ):
        self._auth = auth_provider
        self._tokens = token_service
        self._users = user_repo
        self._tenants = tenant_service
        self._events = event_bus

    async def execute(self, request: RegisterRequest) -> RegisterResult:
        """Execute registration.

        Args:
            request: Registration data

        Returns:
            RegisterResult with user info

        Raises:
            ValidationError: If input is invalid
            EmailExistsError: If email already exists
        """
        # 1. Validate input
        self._validate_email(request.email)
        self._validate_password(request.password)
        self._validate_display_name(request.display_name)

        # 2. Check email uniqueness
        if await self._users.email_exists(request.email):
            raise EmailExistsError(request.email)

        # 3. Hash password
        password_hash = await self._auth.hash_password(request.password)

        # 4. Create user entity
        user = User.create_local(
            email=request.email,
            password_hash=password_hash,
            display_name=request.display_name,
        )

        # 5. Persist user
        user = await self._users.create(user)

        # 6. Create verification token
        verification_token = await self._tokens.create_verification_token(
            str(user.user_id)
        )

        # 7. Emit domain event
        if self._events:
            await self._events.publish(UserRegistered(
                user_id=user.user_id,
                email=user.email,
                auth_provider=user.auth_provider.value,
                display_name=user.display_name,
            ))

        # 8. TODO: Send verification email
        # await self._email_service.send_verification(user.email, verification_token)

        return RegisterResult(
            user_id=str(user.user_id),
            email=user.email,
            status=user.status.value,
            verification_token=verification_token,  # Remove in production
        )

    def _validate_email(self, email: str) -> None:
        """Validate email format."""
        if not email or not email.strip():
            raise ValidationError("Email is required", field="email")

        if len(email) > 255:
            raise ValidationError("Email must be less than 255 characters", field="email")

        if not self.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format", field="email")

    def _validate_password(self, password: str) -> None:
        """Validate password requirements."""
        if not password:
            raise ValidationError("Password is required", field="password")

        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters",
                field="password"
            )

        if not self.PASSWORD_PATTERN.match(password):
            raise ValidationError(
                "Password must contain at least 1 uppercase letter and 1 number",
                field="password"
            )

    def _validate_display_name(self, display_name: str) -> None:
        """Validate display name."""
        if not display_name or not display_name.strip():
            raise ValidationError("Display name is required", field="display_name")

        if len(display_name) < 2:
            raise ValidationError(
                "Display name must be at least 2 characters",
                field="display_name"
            )

        if len(display_name) > 100:
            raise ValidationError(
                "Display name must be less than 100 characters",
                field="display_name"
            )
