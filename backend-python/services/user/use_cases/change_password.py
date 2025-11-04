"""Change User Password Use Case"""

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from services.auth.repositories.models import UserModel
from shared.errors import ValidationError, NotFoundError, ErrorCodes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ChangePasswordUseCase:
    """Use case for changing user password"""

    def __init__(self, db: Session):
        self.db = db

    def execute(self, user_id: int, new_password: str) -> UserModel:
        """
        Change user password

        Args:
            user_id: User ID
            new_password: New password (plain text, will be hashed)

        Returns:
            Updated UserModel

        Raises:
            NotFoundError: If user not found
            ValidationError: If password validation fails
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

        # Validate password strength
        if len(new_password) < 8:
            raise ValidationError(
                message="Password minimal 8 karakter",
                code=ErrorCodes.VALIDATION_ERROR,
                field="new_password"
            )

        # Hash new password
        password_hash = pwd_context.hash(new_password)

        # Update password
        user.password_hash = password_hash
        self.db.commit()
        self.db.refresh(user)

        return user
