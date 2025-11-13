"""
User Repository Implementation
Implements IUserRepository using SQLAlchemy
"""

from typing import Optional
from sqlalchemy.orm import Session, joinedload
from ..domain.user import User
from ..domain.interfaces import IUserRepository
from .models import UserModel
from services.rbac.repositories.models import Role as RoleModel


class UserRepository(IUserRepository):
    """User repository implementation"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID"""
        user_model = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.id == user_id).first()
        return self._to_entity(user_model) if user_model else None

    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        user_model = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.username == username).first()
        return self._to_entity(user_model) if user_model else None

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        user_model = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.email == email).first()
        return self._to_entity(user_model) if user_model else None

    def create(self, user: User) -> User:
        """Create new user"""
        # Find role_id from role name
        role = self.db.query(RoleModel).filter(RoleModel.name == user.role).first()
        if not role:
            raise ValueError(f"Role '{user.role}' not found")

        user_model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            full_name=user.full_name,
            role_id=role.id,
            organization_id=user.organization_id,
            is_active=user.is_active
        )
        self.db.add(user_model)
        self.db.commit()
        self.db.refresh(user_model)
        return self._to_entity(user_model)

    def update(self, user: User) -> User:
        """Update existing user"""
        user_model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not user_model:
            raise ValueError(f"User with id {user.id} not found")

        # Find role_id from role name if role changed
        if user.role:
            role = self.db.query(RoleModel).filter(RoleModel.name == user.role).first()
            if not role:
                raise ValueError(f"Role '{user.role}' not found")
            user_model.role_id = role.id

        user_model.username = user.username
        user_model.email = user.email
        user_model.full_name = user.full_name
        user_model.is_active = user.is_active

        self.db.commit()
        self.db.refresh(user_model)
        return self._to_entity(user_model)

    def delete(self, user_id: int) -> bool:
        """Delete user"""
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user_model:
            return False

        self.db.delete(user_model)
        self.db.commit()
        return True

    def _to_entity(self, model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity"""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=model.role.name if model.role else "ADMIN",  # Get role name from relationship
            organization_id=model.organization_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
