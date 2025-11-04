"""Delete User Use Case"""

from sqlalchemy.orm import Session
from services.auth.repositories.models import UserModel
from shared.errors import ValidationError, NotFoundError, ErrorCodes


class DeleteUserUseCase:
    """Use case for deleting user (soft delete)"""

    def __init__(self, db: Session):
        self.db = db

    def execute(self, user_id: int) -> UserModel:
        """
        Soft delete user (set is_active=False)

        Args:
            user_id: User ID to delete

        Returns:
            Deleted UserModel

        Raises:
            NotFoundError: If user not found
            ValidationError: If user cannot be deleted
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

        # Check if already deleted
        if not user.is_active:
            raise ValidationError(
                message=f"User '{user.username}' sudah tidak aktif",
                code=ErrorCodes.VALIDATION_ERROR,
                details={"user_id": user_id, "username": user.username}
            )

        # Soft delete
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)

        return user
