"""Update User Use Case"""

from typing import Optional
from sqlalchemy.orm import Session
from services.auth.repositories.models import UserModel
from shared.errors import ValidationError, NotFoundError, ErrorCodes
from shared.validators import validate_email, sanitize_string


class UpdateUserUseCase:
    """Use case for updating user"""

    def __init__(self, db: Session):
        self.db = db

    def execute(
        self,
        user_id: int,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> UserModel:
        """
        Update user information

        Args:
            user_id: User ID to update
            email: New email (optional)
            full_name: New full name (optional)
            role: New role (optional)
            is_active: Active status (optional)

        Returns:
            Updated UserModel

        Raises:
            NotFoundError: If user not found
            ValidationError: If validation fails
        """

        # Get user
        user = self.db.query(UserModel).filter(
            UserModel.id == user_id
        ).first()

        if not user:
            raise NotFoundError(
                message=f"User dengan ID {user_id} tidak ditemukan",
                code=ErrorCodes.NOT_FOUND,
                resource="User",
                resource_id=str(user_id)
            )

        # Update email if provided
        if email is not None:
            email = validate_email(email)

            # Check email uniqueness (exclude current user)
            existing_email = self.db.query(UserModel).filter(
                UserModel.email == email,
                UserModel.id != user_id
            ).first()

            if existing_email:
                raise ValidationError(
                    message=f"Email '{email}' sudah digunakan",
                    code=ErrorCodes.VALIDATION_ERROR,
                    field="email",
                    details={"email": email}
                )

            user.email = email

        # Update full_name if provided
        if full_name is not None:
            full_name = sanitize_string(full_name)
            if len(full_name.strip()) < 3:
                raise ValidationError(
                    message="Full name minimal 3 karakter",
                    code=ErrorCodes.VALIDATION_ERROR,
                    field="full_name"
                )
            user.full_name = full_name

        # Update role if provided
        if role is not None:
            valid_roles = ['super_admin', 'admin', 'manager', 'viewer']
            if role not in valid_roles:
                raise ValidationError(
                    message=f"Role harus salah satu dari: {', '.join(valid_roles)}",
                    code=ErrorCodes.VALIDATION_ERROR,
                    field="role",
                    details={"valid_roles": valid_roles}
                )
            user.role = role

        # Update is_active if provided
        if is_active is not None:
            user.is_active = is_active

        self.db.commit()
        self.db.refresh(user)

        return user
