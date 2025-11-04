"""Create User Use Case"""

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from services.auth.repositories.models import UserModel, OrganizationModel
from shared.errors import ValidationError, NotFoundError, ErrorCodes
from shared.validators import validate_username, validate_email, sanitize_string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CreateUserUseCase:
    """Use case for creating new user"""

    def __init__(self, db: Session):
        self.db = db

    def execute(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: str,
        organization_id: int
    ) -> UserModel:
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
            Created UserModel

        Raises:
            ValidationError: If validation fails
            NotFoundError: If organization not found
        """

        # Validate organization exists
        organization = self.db.query(OrganizationModel).filter(
            OrganizationModel.id == organization_id,
            OrganizationModel.is_active == True
        ).first()

        if not organization:
            raise NotFoundError(
                message=f"Organization dengan ID {organization_id} tidak ditemukan",
                code=ErrorCodes.NOT_FOUND,
                resource="Organization",
                resource_id=str(organization_id)
            )

        # Validate username
        username = validate_username(username)

        # Check username uniqueness
        existing_user = self.db.query(UserModel).filter(
            UserModel.username == username
        ).first()

        if existing_user:
            raise ValidationError(
                message=f"Username '{username}' sudah digunakan",
                code=ErrorCodes.VALIDATION_ERROR,
                field="username",
                details={"username": username}
            )

        # Validate email
        email = validate_email(email)

        # Check email uniqueness
        existing_email = self.db.query(UserModel).filter(
            UserModel.email == email
        ).first()

        if existing_email:
            raise ValidationError(
                message=f"Email '{email}' sudah digunakan",
                code=ErrorCodes.VALIDATION_ERROR,
                field="email",
                details={"email": email}
            )

        # Validate password strength
        if len(password) < 8:
            raise ValidationError(
                message="Password minimal 8 karakter",
                code=ErrorCodes.VALIDATION_ERROR,
                field="password"
            )

        # Sanitize full_name
        full_name = sanitize_string(full_name)

        # Hash password
        password_hash = pwd_context.hash(password)

        # Create user
        user = UserModel(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            organization_id=organization_id,
            is_active=True
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user
