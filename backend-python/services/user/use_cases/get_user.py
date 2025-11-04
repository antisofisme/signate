"""Get User Use Case"""

from typing import Optional
from sqlalchemy.orm import Session
from services.auth.repositories.models import UserModel
from shared.errors import NotFoundError, ErrorCodes


class GetUserUseCase:
    """Use case for getting single user"""

    def __init__(self, db: Session):
        self.db = db

    def execute(self, user_id: int) -> UserModel:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            UserModel

        Raises:
            NotFoundError: If user not found
        """

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

        return user
