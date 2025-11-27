"""
Login Use Case
Handles user authentication

Updated to use centralized error handling and JWT utilities
Integrated with Session Management (Phase 1 Day 3)
P0-3: Updated to include permissions in JWT token
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
        role_repository = None,  # Optional: RoleRepository for permissions (P0-3)
        secret_key: str = None,  # Kept for backward compatibility, but uses shared auth
        algorithm: str = "HS256",
        token_expire_minutes: int = 30
    ):
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.session_repository = session_repository
        self.role_repository = role_repository  # P0-3: For fetching role permissions

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

        # P0-3: Fetch user's role permissions for embedding in JWT
        permissions = {}
        if self.role_repository:
            try:
                role = self.role_repository.find_by_name(user.role.upper() if user.role else "VIEWER")
                if role and role.permissions:
                    permissions = role.permissions
            except Exception:
                # Fallback: continue without permissions if role lookup fails
                pass

        # Generate JWT token with organization_id and permissions using shared auth utility
        payload = create_token_payload(
            user_id=user.id,
            username=user.username,
            role=user.role,
            organization_id=user.organization_id,
            permissions=permissions  # P0-3: Embed permissions for fast checking
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
