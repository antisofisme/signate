"""
User Repository Implementation
Implements IUserRepository using SQLAlchemy
"""

from typing import Optional
from datetime import datetime
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

    # CRITICAL FIX P0-6: Multi-tenancy safe methods
    def find_by_username_in_org(self, username: str, organization_id: int) -> Optional[User]:
        """
        Find user by username within specific organization

        SECURITY: Enforces organization isolation to prevent data leaks
        Use this method instead of find_by_username() when checking uniqueness
        """
        user_model = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(
            UserModel.username == username,
            UserModel.organization_id == organization_id
        ).first()
        return self._to_entity(user_model) if user_model else None

    def find_by_email_in_org(self, email: str, organization_id: int) -> Optional[User]:
        """
        Find user by email within specific organization

        SECURITY: Enforces organization isolation to prevent data leaks
        Use this method instead of find_by_email() when checking uniqueness
        """
        user_model = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(
            UserModel.email == email,
            UserModel.organization_id == organization_id
        ).first()
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

    def save(self, user: User) -> User:
        """
        Save/update existing user

        CRITICAL FIX: Added for password reset functionality
        This method is an alias for update() to maintain compatibility
        """
        return self.update(user)

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
        user = User(
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
        # P0-4: Add security fields if available
        if hasattr(model, 'failed_login_attempts'):
            user.failed_login_attempts = model.failed_login_attempts
        if hasattr(model, 'locked_until'):
            user.locked_until = model.locked_until
        if hasattr(model, 'last_login_ip'):
            user.last_login_ip = model.last_login_ip
        if hasattr(model, 'last_login_at'):
            user.last_login_at = model.last_login_at
        return user

    # P0-4: Security methods for account lockout
    def update_login_attempts(
        self,
        user_id: int,
        failed_attempts: int,
        locked_until: Optional[datetime] = None
    ) -> bool:
        """
        Update failed login attempts and lockout status

        Args:
            user_id: User ID to update
            failed_attempts: Number of failed attempts
            locked_until: Timestamp when lockout expires (None if not locked)

        Returns:
            True if update succeeded
        """
        try:
            user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user_model:
                return False

            # Update security fields if they exist on the model
            if hasattr(user_model, 'failed_login_attempts'):
                user_model.failed_login_attempts = failed_attempts
            if hasattr(user_model, 'locked_until'):
                user_model.locked_until = locked_until

            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def update_login_success(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        login_time: Optional[datetime] = None
    ) -> bool:
        """
        Update user record on successful login

        Args:
            user_id: User ID to update
            ip_address: IP address of the login
            login_time: Timestamp of the login

        Returns:
            True if update succeeded
        """
        try:
            user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user_model:
                return False

            # Reset security fields
            if hasattr(user_model, 'failed_login_attempts'):
                user_model.failed_login_attempts = 0
            if hasattr(user_model, 'locked_until'):
                user_model.locked_until = None

            # Update last login info
            if hasattr(user_model, 'last_login_ip') and ip_address:
                user_model.last_login_ip = ip_address
            if hasattr(user_model, 'last_login_at') and login_time:
                user_model.last_login_at = login_time

            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
