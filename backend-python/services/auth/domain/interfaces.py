"""
Repository Interfaces
Contracts for data access
"""

from abc import ABC, abstractmethod
from typing import Optional
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
