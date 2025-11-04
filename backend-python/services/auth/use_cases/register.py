"""
Register Use Case
Handles user registration

Updated to use centralized validators and error handling
"""

from ..domain.user import User
from ..domain.interfaces import IUserRepository
from passlib.context import CryptContext
from datetime import datetime
from shared.errors import ValidationError, ErrorCodes
from shared.validators import validate_username, validate_email, validate_password, sanitize_string


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
            ValidationError: If validation fails or user exists
        """
        # Validate username using centralized validator
        is_valid_username, error_msg = validate_username(username)
        if not is_valid_username:
            raise ValidationError(
                message=error_msg,
                code=ErrorCodes.VALIDATION_ERROR,
                details={"field": "username"}
            )

        # Validate email using centralized validator
        is_valid_email, error_msg = validate_email(email)
        if not is_valid_email:
            raise ValidationError(
                message=error_msg,
                code=ErrorCodes.VALIDATION_ERROR,
                details={"field": "email"}
            )

        # Validate password using centralized validator
        is_valid_password, error_msg = validate_password(password, min_length=8)
        if not is_valid_password:
            raise ValidationError(
                message=error_msg,
                code=ErrorCodes.VALIDATION_ERROR,
                details={"field": "password"}
            )

        # Validate full_name
        if not full_name or len(full_name.strip()) < 3:
            raise ValidationError(
                message="Nama lengkap minimal 3 karakter",
                code=ErrorCodes.VALIDATION_ERROR,
                details={"field": "full_name"}
            )

        # Check if username exists
        existing_user = self.user_repository.find_by_username(username)
        if existing_user:
            raise ValidationError(
                message=f"Username '{username}' sudah digunakan",
                code=ErrorCodes.DUPLICATE_ENTRY,
                details={"field": "username"}
            )

        # Check if email exists
        existing_email = self.user_repository.find_by_email(email)
        if existing_email:
            raise ValidationError(
                message=f"Email '{email}' sudah terdaftar",
                code=ErrorCodes.DUPLICATE_ENTRY,
                details={"field": "email"}
            )

        # Sanitize inputs
        username = sanitize_string(username)
        email = sanitize_string(email)
        full_name = sanitize_string(full_name)

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
