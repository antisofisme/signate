"""
Register Use Case
Handles user registration
"""

from ..domain.user import User
from ..domain.interfaces import IUserRepository
from passlib.context import CryptContext
from datetime import datetime


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterUseCase:
    """Register use case - 1 file, 1 responsibility"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    def execute(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        organization_id: int = None,
        role: str = "ADMIN"
    ) -> User:
        """
        Execute register use case

        Args:
            username: Unique username
            email: User email
            password: Plain text password
            full_name: User's full name
            organization_id: Organization ID (optional)
            role: User role (default: ADMIN)

        Returns:
            Created User entity

        Raises:
            ValueError: If validation fails or user exists
        """
        # Validate inputs
        self._validate_username(username)
        self._validate_email(email)
        self._validate_password(password)

        # Check if username exists
        existing_user = self.user_repository.find_by_username(username)
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")

        # Check if email exists
        existing_email = self.user_repository.find_by_email(email)
        if existing_email:
            raise ValueError(f"Email '{email}' already registered")

        # Hash password
        password_hash = pwd_context.hash(password)

        # Create user entity
        user = User(
            id=None,
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            organization_id=organization_id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Save to repository
        created_user = self.user_repository.create(user)

        return created_user

    def _validate_username(self, username: str):
        """Validate username"""
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(username) > 50:
            raise ValueError("Username too long (max 50 characters)")

    def _validate_email(self, email: str):
        """Validate email"""
        if not email or "@" not in email:
            raise ValueError("Invalid email address")

    def _validate_password(self, password: str):
        """Validate password"""
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
