"""
User Repository Interface

Abstract contract for user data access.
Implementations handle actual database operations.

Source: INFRA-DEC-011-modular-architecture.md
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain.user import User


class IUserRepository(ABC):
    """Interface for user data access."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user.

        Args:
            user: User entity to create

        Returns:
            Created user with generated ID

        Raises:
            EmailExistsError: If email already exists
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User's UUID

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive).

        Args:
            email: User's email

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_oauth(self, provider: str, provider_id: str) -> Optional[User]:
        """Get user by OAuth provider ID.

        Args:
            provider: OAuth provider name (google, github)
            provider_id: Provider's unique user ID

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update user.

        Args:
            user: User entity with updated fields

        Returns:
            Updated user
        """
        pass

    @abstractmethod
    async def update_password(self, user_id: UUID, password_hash: str) -> None:
        """Update user's password hash.

        Args:
            user_id: User's UUID
            password_hash: New password hash
        """
        pass

    @abstractmethod
    async def update_status(self, user_id: UUID, status: str) -> None:
        """Update user's status.

        Args:
            user_id: User's UUID
            status: New status (active, suspended, pending_verification)
        """
        pass

    @abstractmethod
    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User's UUID
        """
        pass

    @abstractmethod
    async def verify_email(self, user_id: UUID) -> None:
        """Mark user's email as verified.

        Args:
            user_id: User's UUID
        """
        pass

    @abstractmethod
    async def link_oauth(
        self,
        user_id: UUID,
        provider: str,
        provider_id: str
    ) -> None:
        """Link OAuth provider to existing user.

        Args:
            user_id: User's UUID
            provider: OAuth provider name
            provider_id: Provider's unique user ID

        Raises:
            OAuthAlreadyLinkedError: If provider_id is linked to another user
        """
        pass

    @abstractmethod
    async def unlink_oauth(self, user_id: UUID, provider: str) -> None:
        """Unlink OAuth provider from user.

        Args:
            user_id: User's UUID
            provider: OAuth provider to unlink

        Raises:
            CannotUnlinkError: If this is the only auth method
        """
        pass

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if email exists.

        Args:
            email: Email to check

        Returns:
            True if email exists
        """
        pass

    # =========================================================================
    # Account Lockout Methods (for brute force protection)
    # =========================================================================

    @abstractmethod
    async def is_account_locked(self, user_id: UUID) -> bool:
        """Check if account is locked.

        Args:
            user_id: User's UUID

        Returns:
            True if account is currently locked
        """
        pass

    @abstractmethod
    async def get_lockout_info(self, user_id: UUID) -> Optional[dict]:
        """Get account lockout information.

        Args:
            user_id: User's UUID

        Returns:
            Dictionary with locked_until, failed_attempts, or None if not locked
        """
        pass

    @abstractmethod
    async def record_failed_login(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None
    ) -> dict:
        """Record a failed login attempt.

        Args:
            user_id: User's UUID
            ip_address: IP address of the failed attempt

        Returns:
            Dictionary with is_locked, lock_duration_minutes, attempts
        """
        pass

    @abstractmethod
    async def reset_failed_logins(self, user_id: UUID) -> None:
        """Reset failed login counter (on successful login).

        Args:
            user_id: User's UUID
        """
        pass

    @abstractmethod
    async def admin_unlock_account(self, user_id: UUID) -> bool:
        """Manually unlock an account (admin action).

        Args:
            user_id: User's UUID

        Returns:
            True if account was unlocked
        """
        pass
