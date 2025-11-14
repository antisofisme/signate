"""Update User Use Case"""

from typing import Optional
from ..domain.user import User
from ..domain.interfaces import IUserRepository
from shared.errors import ValidationError, NotFoundError
from shared.validators import validate_email, sanitize_string


class UpdateUserUseCase:
    """Use case for updating user"""

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(
        self,
        user_id: int,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """
        Update user information

        Args:
            user_id: User ID to update
            email: New email (optional)
            full_name: New full name (optional)
            role: New role (optional)
            is_active: Active status (optional)

        Returns:
            Updated User entity

        Raises:
            NotFoundError: If user not found
            ValidationError: If validation fails
        """

        # Get user
        user = self.user_repo.find_by_id(user_id)

        if not user:
            raise NotFoundError(
                message=f"User dengan ID {user_id} tidak ditemukan",
                details={"resource_type": "user", "resource_id": user_id}
            )

        # Update email if provided
        if email is not None:
            # Sanitize and validate email
            email = sanitize_string(email.lower())
            if not validate_email(email):
                raise ValidationError(
                    message="Format email tidak valid",
                    details={"field": "email", "email": email}
                )

            # Check email uniqueness within organization (CRITICAL FIX P0-6)
            # Note: user.organization_id is from the fetched user above
            existing_email = self.user_repo.find_by_email_in_org(email, user.organization_id)

            if existing_email and existing_email.id != user_id:
                raise ValidationError(
                    message=f"Email '{email}' sudah digunakan",
                    details={"field": "email", "email": email}
                )

            user.email = email

        # Update full_name if provided
        if full_name is not None:
            full_name = sanitize_string(full_name)
            if len(full_name.strip()) < 3:
                raise ValidationError(
                    message="Full name minimal 3 karakter",
                    details={"field": "full_name"}
                )
            user.full_name = full_name

        # Update role if provided
        if role is not None:
            valid_roles = ['super_admin', 'admin', 'manager', 'viewer']
            if role not in valid_roles:
                raise ValidationError(
                    message=f"Role harus salah satu dari: {', '.join(valid_roles)}",
                    details={"field": "role", "valid_roles": valid_roles}
                )
            user.role = role

        # Update is_active if provided
        if is_active is not None:
            user.is_active = is_active

        # Save changes via repository
        return self.user_repo.update(user)
