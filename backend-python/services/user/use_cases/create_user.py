"""Create User Use Case"""

from passlib.context import CryptContext
from ..domain.user import User
from ..domain.interfaces import IUserRepository
from services.organization.repositories.organization_repo import OrganizationRepository
from sqlalchemy.orm import Session
from shared.errors import ValidationError, NotFoundError
from shared.validators import sanitize_string, validate_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CreateUserUseCase:
    """Use case for creating new user"""

    def __init__(self, user_repo: IUserRepository, org_repo: OrganizationRepository):
        self.user_repo = user_repo
        self.org_repo = org_repo

    def execute(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: str,
        organization_id: int
    ) -> User:
        """
        Create new user

        Args:
            username: Unique username
            email: Email address
            password: Plain text password (will be hashed)
            full_name: User's full name
            role: User role (super_admin, admin, manager, viewer)
            organization_id: Organization ID

        Returns:
            Created User entity

        Raises:
            ValidationError: If validation fails
            NotFoundError: If organization not found
        """

        # Validate organization exists
        organization = self.org_repo.find_by_id(organization_id)

        if not organization or not organization.is_active:
            raise NotFoundError(
                message=f"Organization dengan ID {organization_id} tidak ditemukan",
                details={"resource_type": "organization", "resource_id": organization_id}
            )

        # Sanitize username
        username = sanitize_string(username.strip().lower())

        # Basic username validation
        if len(username) < 3:
            raise ValidationError(
                message="Username minimal 3 karakter",
                details={"field": "username"}
            )

        # Check username uniqueness
        existing_user = self.user_repo.find_by_username(username)

        if existing_user:
            raise ValidationError(
                message=f"Username '{username}' sudah digunakan",
                details={"field": "username", "username": username}
            )

        # Sanitize and validate email
        email = sanitize_string(email.strip().lower())

        if not validate_email(email):
            raise ValidationError(
                message="Format email tidak valid",
                details={"field": "email", "email": email}
            )

        # Check email uniqueness
        existing_email = self.user_repo.find_by_email(email)

        if existing_email:
            raise ValidationError(
                message=f"Email '{email}' sudah digunakan",
                details={"field": "email", "email": email}
            )

        # Validate password strength
        if len(password) < 8:
            raise ValidationError(
                message="Password minimal 8 karakter",
                details={"field": "password"}
            )

        # Sanitize full_name
        full_name = sanitize_string(full_name)

        if len(full_name.strip()) < 3:
            raise ValidationError(
                message="Full name minimal 3 karakter",
                details={"field": "full_name"}
            )

        # Validate role
        valid_roles = ['super_admin', 'admin', 'manager', 'viewer']
        if role not in valid_roles:
            raise ValidationError(
                message=f"Role harus salah satu dari: {', '.join(valid_roles)}",
                details={"field": "role", "valid_roles": valid_roles}
            )

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
            is_active=True
        )

        # Save via repository
        return self.user_repo.create(user)
