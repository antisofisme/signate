"""
User Repository Implementation
Implements IUserRepository using SQLAlchemy
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..domain.user import User
from ..domain.interfaces import IUserRepository
from services.auth.repositories.models import UserModel, OrganizationModel


class UserRepository(IUserRepository):
    """User repository implementation"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, user_id: int, organization_id: Optional[int] = None) -> Optional[User]:
        """
        Find user by ID with optional organization isolation
        
        Args:
            user_id: User ID
            organization_id: Organization ID for isolation (recommended for security)
        """
        query = self.db.query(UserModel).filter(UserModel.id == user_id)
        
        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)
        
        user_model = query.first()
        return self._to_entity(user_model) if user_model else None

    def find_by_username(self, username: str, organization_id: Optional[int] = None) -> Optional[User]:
        """
        Find user by username with optional organization isolation
        
        Args:
            username: Username
            organization_id: Organization ID for isolation (recommended for security)
        """
        query = self.db.query(UserModel).filter(UserModel.username == username)
        
        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)
        
        user_model = query.first()
        return self._to_entity(user_model) if user_model else None

    def find_by_email(self, email: str, organization_id: Optional[int] = None) -> Optional[User]:
        """
        Find user by email with optional organization isolation
        
        Args:
            email: Email address
            organization_id: Organization ID for isolation (recommended for security)
        """
        query = self.db.query(UserModel).filter(UserModel.email == email)
        
        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)
        
        user_model = query.first()
        return self._to_entity(user_model) if user_model else None

    def get_all(
        self,
        organization_id: Optional[int] = None,
        role: Optional[str] = None,
        active_only: bool = False
    ) -> List[User]:
        """Get all users with filters"""
        query = self.db.query(UserModel)

        if organization_id:
            query = query.filter(UserModel.organization_id == organization_id)

        if role:
            query = query.filter(UserModel.role == role)

        if active_only:
            query = query.filter(UserModel.is_active == True)

        user_models = query.order_by(UserModel.created_at.desc()).all()
        return [self._to_entity(user) for user in user_models]

    def create(self, user: User) -> User:
        """Create new user"""
        user_model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            full_name=user.full_name,
            role=user.role,
            organization_id=user.organization_id,
            is_active=user.is_active
        )
        self.db.add(user_model)
        self.db.commit()
        self.db.refresh(user_model)
        return self._to_entity(user_model)

    def update(self, user: User, organization_id: Optional[int] = None) -> User:
        """Update existing user with organization isolation"""
        query = self.db.query(UserModel).filter(UserModel.id == user.id)
        
        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)
        
        user_model = query.first()
        
        if not user_model:
            if organization_id is not None:
                raise ValueError(f"User with id {user.id} not found in organization {organization_id}")
            else:
                raise ValueError(f"User with id {user.id} not found")

        user_model.email = user.email
        user_model.full_name = user.full_name
        user_model.role = user.role
        user_model.is_active = user.is_active
        # Note: username tidak bisa diubah setelah dibuat
        # Note: password diubah via change_password()

        self.db.commit()
        self.db.refresh(user_model)
        return self._to_entity(user_model)

    def delete(self, user_id: int, organization_id: Optional[int] = None) -> bool:
        """Delete user (hard delete - permanently remove) with organization isolation"""
        query = self.db.query(UserModel).filter(UserModel.id == user_id)
        
        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)
        
        user_model = query.first()
        
        if not user_model:
            return False

        # Hard delete - permanently remove from database
        self.db.delete(user_model)
        self.db.commit()
        return True

    def change_password(self, user_id: int, password_hash: str, organization_id: Optional[int] = None) -> User:
        """Change user password with organization isolation"""
        query = self.db.query(UserModel).filter(UserModel.id == user_id)
        
        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)
        
        user_model = query.first()
        
        if not user_model:
            if organization_id is not None:
                raise ValueError(f"User with id {user_id} not found in organization {organization_id}")
            else:
                raise ValueError(f"User with id {user_id} not found")

        user_model.password_hash = password_hash
        self.db.commit()
        self.db.refresh(user_model)
        return self._to_entity(user_model)

    def get_organization_name(self, user_id: int, organization_id: Optional[int] = None) -> Optional[str]:
        """Get organization name for user with organization isolation"""
        query = self.db.query(OrganizationModel.name).join(
            UserModel, UserModel.organization_id == OrganizationModel.id
        ).filter(
            UserModel.id == user_id
        )
        
        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)
        
        result = query.first()
        return result[0] if result else None

    def count_by_status(self, active_only: bool = False) -> int:
        """Count users by active status"""
        query = self.db.query(func.count(UserModel.id))

        if active_only:
            query = query.filter(UserModel.is_active == True)

        return query.scalar() or 0

    def _to_entity(self, model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity"""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=model.role,
            organization_id=model.organization_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
