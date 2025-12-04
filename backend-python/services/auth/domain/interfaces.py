"""
Repository Interfaces
Contracts for data access
"""

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from .user import User


class IUserRepository(ABC):
    """Interface for user repository"""

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID"""
        pass

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        """Create new user"""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update existing user"""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        pass

    # P0-4: Security methods for account lockout
    def update_login_attempts(
        self,
        user_id: int,
        failed_attempts: int,
        locked_until: Optional[datetime] = None
    ) -> bool:
        """
        Update failed login attempts and lockout status

        Args:
            user_id: User ID to update
            failed_attempts: Number of failed attempts
            locked_until: Timestamp when lockout expires (None if not locked)

        Returns:
            True if update succeeded
        """
        # Default implementation does nothing (for backward compatibility)
        return True

    def update_login_success(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        login_time: Optional[datetime] = None
    ) -> bool:
        """
        Update user record on successful login

        Args:
            user_id: User ID to update
            ip_address: IP address of the login
            login_time: Timestamp of the login

        Returns:
            True if update succeeded
        """
        # Default implementation does nothing (for backward compatibility)
        return True
