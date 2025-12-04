"""
User Repository Implementation
Implements IUserRepository using SQLAlchemy
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, asc, desc
from sqlalchemy.exc import IntegrityError
from ..domain.user import User
from ..domain.interfaces import IUserRepository
from services.auth.repositories.models import UserModel, OrganizationModel
from services.rbac.repositories.models import Role as RoleModel
from shared.errors import ValidationError, ErrorCodes


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
        query = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.id == user_id)

        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)

        user_model = query.first()
        return self._to_entity(user_model) if user_model else None

    def find_by_ids(self, user_ids: List[int]) -> dict:
        """
        Batch fetch users by IDs - returns dict for O(1) lookup
        Optimized for N+1 query prevention

        Args:
            user_ids: List of user IDs to fetch

        Returns:
            Dict mapping user_id -> User entity
        """
        if not user_ids:
            return {}

        user_models = self.db.query(UserModel).options(
            joinedload(UserModel.role)
        ).filter(
            UserModel.id.in_(user_ids)
        ).all()

        return {model.id: self._to_entity(model) for model in user_models}

    def find_by_username(self, username: str, organization_id: Optional[int] = None) -> Optional[User]:
        """
        Find user by username with optional organization isolation

        Args:
            username: Username
            organization_id: Organization ID for isolation (recommended for security)
        """
        query = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.username == username)

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
        query = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.email == email)

        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)

        user_model = query.first()
        return self._to_entity(user_model) if user_model else None

    # Valid sortable columns for users
    SORTABLE_COLUMNS = {
        'username': UserModel.username,
        'email': UserModel.email,
        'is_active': UserModel.is_active,
        'created_at': UserModel.created_at,
        'updated_at': UserModel.updated_at,
    }

    def get_all(
        self,
        organization_id: Optional[int] = None,
        role: Optional[str] = None,
        active_only: bool = False,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> List[User]:
        """Get all users with filters and sorting"""
        query = self.db.query(UserModel).options(joinedload(UserModel.role))

        if organization_id:
            query = query.filter(UserModel.organization_id == organization_id)

        if role:
            # Join Role table to filter by role name (case-insensitive)
            query = query.join(RoleModel).filter(func.lower(RoleModel.name) == role.lower())

        if active_only:
            query = query.filter(UserModel.is_active == True)

        # Apply sorting
        if sort_by and sort_by in self.SORTABLE_COLUMNS:
            column = self.SORTABLE_COLUMNS[sort_by]
            if sort_dir == 'desc':
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        else:
            # Default sort by created_at desc
            query = query.order_by(desc(UserModel.created_at))

        user_models = query.all()
        return [self._to_entity(user) for user in user_models]

    def create(self, user: User) -> User:
        """Create new user with proper role_id assignment"""
        # Map domain role name to database role name
        role_map = {
            'super_admin': 'SUPER_ADMIN',
            'admin': 'ADMIN',
            'manager': 'CONTENT_MANAGER',  # Domain: manager → DB: CONTENT_MANAGER
            'viewer': 'VIEWER'
        }

        db_role_name = role_map.get(user.role.lower(), 'VIEWER')

        # Look up role_id from role name
        role_model = self.db.query(RoleModel).filter(
            RoleModel.name == db_role_name
        ).first()

        if not role_model:
            raise ValidationError(
                message=f"Invalid role: {user.role}",
                code=ErrorCodes.VALIDATION_ERROR,
                field="role"
            )

        # BUG FIX #2: Catch IntegrityError for duplicate username
        try:
            user_model = UserModel(
                username=user.username,
                email=user.email,
                password_hash=user.password_hash,
                full_name=user.full_name,
                role_id=role_model.id,  # Use role_id, not role
                organization_id=user.organization_id,
                is_active=user.is_active
            )
            self.db.add(user_model)
            self.db.commit()
            self.db.refresh(user_model)
            return self._to_entity(user_model)
        except IntegrityError as e:
            self.db.rollback()
            error_str = str(e).lower()
            if "username" in error_str:
                raise ValidationError(
                    message=f"Username '{user.username}' already exists",
                    code=ErrorCodes.DUPLICATE_RESOURCE,
                    field="username"
                )
            elif "email" in error_str:
                raise ValidationError(
                    message=f"Email '{user.email}' already exists",
                    code=ErrorCodes.DUPLICATE_RESOURCE,
                    field="email"
                )
            raise

    def update(self, user: User, organization_id: Optional[int] = None) -> User:
        """Update existing user with organization isolation"""
        query = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.id == user.id)

        # SECURITY: Add organization filtering if provided
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)

        user_model = query.first()

        if not user_model:
            if organization_id is not None:
                raise ValueError(f"User with id {user.id} not found in organization {organization_id}")
            else:
                raise ValueError(f"User with id {user.id} not found")

        # Map domain role name to database role name
        role_map = {
            'super_admin': 'SUPER_ADMIN',
            'admin': 'ADMIN',
            'manager': 'CONTENT_MANAGER',
            'viewer': 'VIEWER'
        }

        db_role_name = role_map.get(user.role.lower(), 'VIEWER')

        # Look up role_id from role name
        role_model = self.db.query(RoleModel).filter(
            RoleModel.name == db_role_name
        ).first()

        if not role_model:
            raise ValidationError(
                message=f"Invalid role: {user.role}",
                code=ErrorCodes.VALIDATION_ERROR,
                field="role"
            )

        user_model.email = user.email
        user_model.full_name = user.full_name
        user_model.role_id = role_model.id  # Use role_id, not role
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

    def assign_role(self, user_id: int, role_id: int, organization_id: Optional[int] = None) -> User:
        """
        Assign a role to user by role_id

        Args:
            user_id: User ID
            role_id: Role ID to assign
            organization_id: Organization ID for isolation (recommended for security)

        Returns:
            Updated User entity
        """
        # Verify role exists
        role_model = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role_model:
            raise ValidationError(
                message=f"Role with id {role_id} not found",
                code=ErrorCodes.NOT_FOUND,
                field="role_id"
            )

        # Get user with org isolation
        query = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.id == user_id)
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)

        user_model = query.first()
        if not user_model:
            raise ValidationError(
                message=f"User with id {user_id} not found",
                code=ErrorCodes.NOT_FOUND,
                field="user_id"
            )

        # Assign role
        user_model.role_id = role_id
        self.db.commit()
        self.db.refresh(user_model)
        return self._to_entity(user_model)

    def get_user_role(self, user_id: int, organization_id: Optional[int] = None) -> Optional[dict]:
        """
        Get user's current role details

        Args:
            user_id: User ID
            organization_id: Organization ID for isolation

        Returns:
            Role details dict or None
        """
        query = self.db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.id == user_id)
        if organization_id is not None:
            query = query.filter(UserModel.organization_id == organization_id)

        user_model = query.first()
        if not user_model or not user_model.role:
            return None

        role = user_model.role
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role,
            "permissions": role.permissions or {}
        }

    def _to_entity(self, model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity with proper role mapping"""
        # Map database role to domain role (DB is UPPERCASE, domain is lowercase)
        role_map = {
            'SUPER_ADMIN': 'super_admin',
            'ADMIN': 'admin',
            'CONTENT_MANAGER': 'manager',  # DB: CONTENT_MANAGER → Domain: manager
            'VIEWER': 'viewer'
        }

        role_name = 'viewer'  # Default role
        if model.role and hasattr(model.role, 'name'):
            db_role_name = model.role.name
            role_name = role_map.get(db_role_name, 'viewer')

        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=role_name,  # Mapped domain role name
            organization_id=model.organization_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
