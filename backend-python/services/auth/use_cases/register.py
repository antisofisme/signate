"""
Register Use Case
Handles user registration

Updated to use centralized validators and error handling
Added organization validation (Critical Fix)
"""

from typing import Optional
from ..domain.user import User
from ..domain.interfaces import IUserRepository
from ..repositories.organization_repo import OrganizationRepository
from shared.auth import get_password_hash  # Use centralized password hashing
from datetime import datetime, timezone
from shared.errors import ValidationError, NotFoundError
from shared.validators import validate_username, validate_email, validate_password, sanitize_string


class RegisterUseCase:
    """Register use case - 1 file, 1 responsibility"""

    def __init__(
        self,
        user_repository: IUserRepository,
        organization_repository: Optional[OrganizationRepository] = None
    ):
        self.user_repository = user_repository
        self.organization_repository = organization_repository

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

        # Validate organization exists if provided (Critical Fix)
        if organization_id is not None and self.organization_repository:
            org = self.organization_repository.find_by_id(organization_id)
            if not org:
                raise NotFoundError(
                    message=f"Organization dengan ID {organization_id} tidak ditemukan",
                    details={"field": "organization_id", "organization_id": organization_id}
                )
            # Check if organization is active
            if hasattr(org, 'is_active') and not org.is_active:
                raise ValidationError(
                    message="Organization tidak aktif",
                    details={"field": "organization_id", "organization_id": organization_id}
                )

        # Check if username exists within organization (per-org unique)
        # Username is unique per-organization, allowing same username in different organizations
        if organization_id:
            existing_user = self.user_repository.find_by_username_in_org(username, organization_id)
        else:
            # For super_admin registration without organization, check globally
            existing_user = self.user_repository.find_by_username(username)

        if existing_user:
            raise ValidationError(
                message=f"Username '{username}' sudah digunakan",
                code=ErrorCodes.DUPLICATE_ENTRY,
                details={"field": "username"}
            )

        # Check if email exists globally (email stays globally unique for login)
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

        # Hash password using centralized function (Fix #5)
        password_hash = get_password_hash(password)

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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Save to repository
        created_user = self.user_repository.create(user)

        return created_user
