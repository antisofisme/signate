"""
Auth Provider Interface

Abstract contract for authentication providers (local, OAuth).
Implementations can be swapped without changing business logic.

Source: INFRA-DEC-011-modular-architecture.md
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    """User info from OAuth provider."""
    provider: str          # "google" or "github"
    provider_id: str       # Provider's unique user ID
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]


class IAuthProvider(ABC):
    """Interface for authentication providers."""

    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """Hash a plaintext password using bcrypt.

        Args:
            password: Plaintext password

        Returns:
            Hashed password string
        """
        pass

    @abstractmethod
    async def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash.

        Args:
            password: Plaintext password to verify
            hashed: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        pass


class IOAuthProvider(ABC):
    """Interface for OAuth providers (Google, GitHub)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'google', 'github')."""
        pass

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL.

        Args:
            redirect_uri: Callback URL after OAuth
            state: CSRF state token

        Returns:
            Authorization URL to redirect user to
        """
        pass

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth provider
            redirect_uri: Same redirect URI used in authorization

        Returns:
            Access token string
        """
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from OAuth provider.

        Args:
            access_token: OAuth access token

        Returns:
            User info from provider
        """
        pass
