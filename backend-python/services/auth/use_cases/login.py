"""
Login Use Case
Handles user authentication

Updated to use centralized error handling and JWT utilities
"""

from typing import Dict, Any
from ..domain.interfaces import IUserRepository
from ..domain.user import Credentials
from ..repositories.organization_repo import OrganizationRepository
from shared.errors import AuthenticationError
from shared.auth import verify_password, create_access_token, create_token_payload


class LoginUseCase:
    """Login use case - 1 file, 1 responsibility"""

    def __init__(
        self,
        user_repository: IUserRepository,
        organization_repository: OrganizationRepository,
        secret_key: str = None,  # Kept for backward compatibility, but uses shared auth
        algorithm: str = "HS256",
        token_expire_minutes: int = 30
    ):
        self.user_repository = user_repository
        self.organization_repository = organization_repository

    def execute(self, username: str, password: str) -> Dict[str, Any]:
        """
        Execute login use case

        Args:
            username: User's username
            password: User's password (plain text)

        Returns:
            Dict with user, token, and organizations

        Raises:
            AuthenticationError: If credentials are invalid or user is disabled
        """
        # Validate credentials
        credentials = Credentials(username=username, password=password)

        # Find user
        user = self.user_repository.find_by_username(credentials.username)
        if not user:
            raise AuthenticationError(
                message="Username atau password salah"
            )

        # Verify password using shared auth utility
        if not verify_password(credentials.password, user.password_hash):
            raise AuthenticationError(
                message="Username atau password salah"
            )

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError(
                message="Akun Anda telah dinonaktifkan"
            )

        # Generate JWT token with organization_id using shared auth utility
        payload = create_token_payload(
            user_id=user.id,
            username=user.username,
            role=user.role,
            organization_id=user.organization_id
        )
        token = create_access_token(payload)

        # Get user's accessible organizations
        organizations = self.organization_repository.get_user_organizations(user.id)

        return {
            "user": user,
            "token": token,
            "organizations": organizations
        }
