"""
Login Use Case
Handles user authentication

Updated to use centralized error handling and JWT utilities
Integrated with Session Management (Phase 1 Day 3)
P0-3: Updated to include permissions in JWT token
P0-4: Added account lockout mechanism for security
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from ..domain.interfaces import IUserRepository
from ..domain.user import Credentials
from ..repositories.organization_repo import OrganizationRepository
from shared.errors import AuthenticationError, ErrorCodes
from shared.auth import verify_password, create_access_token, create_token_payload

# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5  # Lock after 5 consecutive failed attempts
LOCKOUT_DURATION_MINUTES = 30  # Lock for 30 minutes


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

        # P0-4: Check if account is locked
        if hasattr(user, 'locked_until') and user.locked_until:
            if user.locked_until > datetime.now(timezone.utc):
                minutes_remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
                raise AuthenticationError(
                    message=f"Akun terkunci. Coba lagi dalam {minutes_remaining} menit.",
                    code=ErrorCodes.ACCOUNT_LOCKED
                )

        # Verify password using shared auth utility
        if not verify_password(credentials.password, user.password_hash):
            # P0-4: Increment failed login attempts
            self._handle_failed_login(user)
            raise AuthenticationError(
                message="Username atau password salah"
            )

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError(
                message="Akun Anda telah dinonaktifkan"
            )

        # P0-4: Reset failed login attempts on successful login
        self._handle_successful_login(user, ip_address)

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

    def _handle_failed_login(self, user) -> None:
        """
        Handle failed login attempt - increment counter and lock if necessary

        P0-4: Security feature to prevent brute force attacks

        Args:
            user: User object from repository
        """
        try:
            # Get current failed attempts count
            current_attempts = getattr(user, 'failed_login_attempts', 0) or 0
            new_attempts = current_attempts + 1

            # Check if should lock account
            locked_until = None
            if new_attempts >= MAX_FAILED_ATTEMPTS:
                locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

            # Update user record
            self.user_repository.update_login_attempts(
                user_id=user.id,
                failed_attempts=new_attempts,
                locked_until=locked_until
            )
        except Exception:
            # Silently fail - don't expose lockout mechanism errors
            pass

    def _handle_successful_login(self, user, ip_address: Optional[str] = None) -> None:
        """
        Handle successful login - reset counters and update last login info

        P0-4: Security feature to track login activity

        Args:
            user: User object from repository
            ip_address: IP address of the login request
        """
        try:
            # Reset failed attempts and update last login info
            self.user_repository.update_login_success(
                user_id=user.id,
                ip_address=ip_address,
                login_time=datetime.now(timezone.utc)
            )
        except Exception:
            # Silently fail - don't block login if tracking fails
            pass
