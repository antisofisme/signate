"""
Authentication interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class TokenPayload:
    """JWT token payload."""
    sub: str  # Subject (user_id or api_key_id)
    tenant_id: str
    type: str = "user"  # "user" or "api_key"
    permissions: List[str] = field(default_factory=list)
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


class IAuthService(ABC):
    """
    Interface for authentication service.

    Implementations: JWTAuthService
    """

    @abstractmethod
    async def validate_token(self, token: str) -> Optional[TokenPayload]:
        """
        Validate JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenPayload if valid, None otherwise
        """
        pass

    @abstractmethod
    async def validate_api_key(
        self,
        api_key: str,
        tenant_id: str
    ) -> Optional[TokenPayload]:
        """
        Validate API key.

        Args:
            api_key: API key string (format: prefix.secret)
            tenant_id: Tenant ID to validate against

        Returns:
            TokenPayload if valid, None otherwise
        """
        pass

    @abstractmethod
    async def create_token(
        self,
        user_id: str,
        tenant_id: str,
        permissions: List[str],
        expires_in_seconds: int = 3600
    ) -> str:
        """
        Create JWT token for user.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            permissions: List of permissions
            expires_in_seconds: Token expiry

        Returns:
            JWT token string
        """
        pass

    @abstractmethod
    async def create_api_key(
        self,
        tenant_id: str,
        name: str,
        permissions: List[str],
        created_by: str,
        expires_in_days: Optional[int] = None
    ) -> tuple[str, str]:
        """
        Create API key for programmatic access.

        Args:
            tenant_id: Tenant ID
            name: Key name
            permissions: List of permissions
            created_by: Creator user ID
            expires_in_days: Optional expiry

        Returns:
            Tuple of (key_id, full_api_key)
            Note: Full API key is only returned once!
        """
        pass

    @abstractmethod
    async def revoke_api_key(
        self,
        key_id: str,
        tenant_id: str
    ) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: API key ID
            tenant_id: Tenant ID

        Returns:
            True if revoked
        """
        pass
