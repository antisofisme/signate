"""
Login Use Case
Handles user authentication

Updated to use centralized error handling
"""

from typing import Dict, Any
from ..domain.interfaces import IUserRepository
from ..domain.user import Credentials
from ..repositories.organization_repo import OrganizationRepository
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from shared.errors import AuthenticationError, ErrorCodes


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginUseCase:
    """Login use case - 1 file, 1 responsibility"""

    def __init__(
        self,
        user_repository: IUserRepository,
        organization_repository: OrganizationRepository,
        secret_key: str,
        algorithm: str = "HS256",
        token_expire_minutes: int = 30
    ):
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes

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
                message="Username atau password salah",
                code=ErrorCodes.INVALID_CREDENTIALS
            )

        # Verify password
        if not pwd_context.verify(credentials.password, user.password_hash):
            raise AuthenticationError(
                message="Username atau password salah",
                code=ErrorCodes.INVALID_CREDENTIALS
            )

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError(
                message="Akun Anda telah dinonaktifkan",
                code=ErrorCodes.ACCOUNT_DISABLED
            )

        # Generate JWT token with organization_id
        token = self._create_access_token(
            user.id,
            user.username,
            user.role,
            user.organization_id
        )

        # Get user's accessible organizations
        organizations = self.organization_repository.get_user_organizations(user.id)

        return {
            "user": user,
            "token": token,
            "organizations": organizations
        }

    def _create_access_token(
        self,
        user_id: int,
        username: str,
        role: str,
        organization_id: int = None
    ) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "organization_id": organization_id,
            "exp": expire
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
