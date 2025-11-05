"""
User Repository Interface
Defines contract for data access
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .user import User


class IUserRepository(ABC):
    """User repository interface"""

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
    def get_all(
        self,
        organization_id: Optional[int] = None,
        role: Optional[str] = None,
        active_only: bool = False
    ) -> List[User]:
        """Get all users with filters"""
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
        """Delete user (hard delete - permanently remove)"""
        pass

    @abstractmethod
    def change_password(self, user_id: int, password_hash: str) -> User:
        """Change user password"""
        pass

    @abstractmethod
    def get_organization_name(self, user_id: int) -> Optional[str]:
        """Get organization name for user"""
        pass

    @abstractmethod
    def count_by_status(self, active_only: bool = False) -> int:
        """Count users by active status"""
        pass
