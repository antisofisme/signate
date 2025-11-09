"""
Login Use Case
Handles user authentication

Updated to use centralized error handling and JWT utilities
Integrated with Session Management (Phase 1 Day 3)
"""

from typing import Dict, Any, Optional
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
        session_repository = None,  # Optional: SessionRepository from services.session
        secret_key: str = None,  # Kept for backward compatibility, but uses shared auth
        algorithm: str = "HS256",
        token_expire_minutes: int = 30
    ):
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.session_repository = session_repository

    def execute(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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

        # Create session if session_repository is available (Phase 1 Day 3)
        if self.session_repository:
            # Create session record (repository will hash the token automatically)
            self.session_repository.create_session(
                user_id=user.id,
                organization_id=user.organization_id,
                access_token=token,  # Will be hashed by repository
                refresh_token=None,  # No refresh token for now
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                device_info=device_info or {},
                session_type="web",
                expires_in_minutes=43200  # 30 days = 43200 minutes
            )

        # Get user's accessible organizations
        organizations = self.organization_repository.get_user_organizations(user.id)

        return {
            "user": user,
            "token": token,
            "organizations": organizations
        }
