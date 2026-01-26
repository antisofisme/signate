"""
Token Service Interface

Abstract contract for JWT token operations.
Handles access tokens, refresh tokens, and verification tokens.

Source: INFRA-DEC-008-auth-flow.md
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TenantContext:
    """Tenant context in JWT."""
    tenant_id: str
    slug: str
    role: str
    projects: List[dict]


@dataclass
class TokenPayload:
    """Decoded JWT payload."""
    user_id: str
    email: str
    display_name: Optional[str]
    tenants: List[TenantContext]
    active_tenant_id: Optional[str]
    active_project_id: Optional[str]
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    expires_in: int  # Seconds until access token expires


class ITokenService(ABC):
    """Interface for JWT token operations."""

    @abstractmethod
    async def create_access_token(
        self,
        user_id: str,
        email: str,
        display_name: Optional[str],
        tenants: List[TenantContext],
        active_tenant_id: Optional[str] = None,
        active_project_id: Optional[str] = None,
    ) -> str:
        """Create a new access token.

        Args:
            user_id: User's UUID
            email: User's email
            display_name: User's display name
            tenants: List of tenant contexts
            active_tenant_id: Currently selected tenant
            active_project_id: Currently selected project

        Returns:
            JWT access token string
        """
        pass

    @abstractmethod
    async def create_refresh_token(self, user_id: str) -> str:
        """Create a new refresh token.

        Args:
            user_id: User's UUID

        Returns:
            Refresh token string
        """
        pass

    @abstractmethod
    async def create_token_pair(
        self,
        user_id: str,
        email: str,
        display_name: Optional[str],
        tenants: List[TenantContext],
        active_tenant_id: Optional[str] = None,
        active_project_id: Optional[str] = None,
        remember_me: bool = False,
    ) -> TokenPair:
        """Create access and refresh token pair.

        Args:
            user_id: User's UUID
            email: User's email
            display_name: User's display name
            tenants: List of tenant contexts
            active_tenant_id: Currently selected tenant
            active_project_id: Currently selected project
            remember_me: If True, extend refresh token expiry

        Returns:
            TokenPair with both tokens
        """
        pass

    @abstractmethod
    async def verify_access_token(self, token: str) -> TokenPayload:
        """Verify and decode access token.

        Args:
            token: JWT access token

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: If token is expired
            TokenInvalidError: If token is invalid or malformed
            TokenRevokedError: If token has been revoked
        """
        pass

    @abstractmethod
    async def verify_refresh_token(self, token: str) -> str:
        """Verify refresh token and return user_id.

        Args:
            token: Refresh token

        Returns:
            User ID from token

        Raises:
            TokenExpiredError: If token is expired
            TokenInvalidError: If token is invalid
            TokenRevokedError: If token has been revoked
        """
        pass

    @abstractmethod
    async def revoke_token(self, jti: str, expires_at: datetime) -> None:
        """Add token to blacklist.

        Args:
            jti: JWT ID to revoke
            expires_at: Token expiration time (for cleanup)
        """
        pass

    @abstractmethod
    async def is_revoked(self, jti: str) -> bool:
        """Check if token is revoked.

        Args:
            jti: JWT ID to check

        Returns:
            True if token is revoked
        """
        pass

    @abstractmethod
    async def create_verification_token(self, user_id: str) -> str:
        """Create email verification token.

        Args:
            user_id: User's UUID

        Returns:
            Verification token string (random hex)
        """
        pass

    @abstractmethod
    async def verify_verification_token(self, token: str) -> str:
        """Verify email verification token.

        Args:
            token: Verification token

        Returns:
            User ID if token is valid

        Raises:
            TokenExpiredError: If token is expired
            TokenInvalidError: If token is invalid or already used
        """
        pass

    @abstractmethod
    async def create_password_reset_token(self, user_id: str) -> str:
        """Create password reset token.

        Args:
            user_id: User's UUID

        Returns:
            Reset token string
        """
        pass

    @abstractmethod
    async def verify_password_reset_token(self, token: str) -> str:
        """Verify password reset token.

        Args:
            token: Reset token

        Returns:
            User ID if token is valid

        Raises:
            TokenExpiredError: If token is expired
            TokenInvalidError: If token is invalid or already used
        """
        pass

    @abstractmethod
    async def mark_token_used(self, token: str) -> None:
        """Mark a one-time token as used.

        Args:
            token: Token to mark as used
        """
        pass
