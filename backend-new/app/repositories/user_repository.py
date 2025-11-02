"""
User Repository - Database Access untuk User Management
=======================================================

CENTRALIZED QUERIES untuk users dan user_organizations tables
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository):
    """
    User Repository untuk user management

    Handles:
    - User CRUD
    - Authentication queries
    - User-Organization relationships
    - User search
    """

    def __init__(self, db: Session):
        super().__init__(User, db)
        self.db = db

    # =========================================================================
    # USER-SPECIFIC QUERIES
    # =========================================================================

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username (for authentication)

        Example:
            user = user_repo.get_by_username("admin")
        """
        return self.db.query(self.model).filter(
            self.model.username == username
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email

        Example:
            user = user_repo.get_by_email("admin@example.com")
        """
        return self.db.query(self.model).filter(
            self.model.email == email
        ).first()

    def get_organization_users(self, organization_id: int) -> List[User]:
        """
        Get all users in an organization

        Joins through user_organizations table

        Example:
            users = user_repo.get_organization_users(org_id=1)
        """
        from app.models.user_organization import UserOrganization

        return self.db.query(self.model).join(
            UserOrganization,
            UserOrganization.user_id == self.model.id
        ).filter(
            UserOrganization.organization_id == organization_id
        ).all()

    def search_users(self, query: str) -> List[User]:
        """
        Search users by username, email, or full name

        Example:
            results = user_repo.search_users("john")
        """
        search_pattern = f"%{query}%"
        return self.db.query(self.model).filter(
            or_(
                self.model.username.ilike(search_pattern),
                self.model.email.ilike(search_pattern),
                self.model.full_name.ilike(search_pattern)
            )
        ).all()

    def get_user_organizations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all organizations that a user belongs to

        Returns list with organization and role info

        Example:
            orgs = user_repo.get_user_organizations(user_id=1)
        """
        from app.models.organization import Organization
        from app.models.user_organization import UserOrganization
        from app.models.role import Role

        results = self.db.query(
            Organization,
            Role,
            UserOrganization.is_default
        ).join(
            UserOrganization,
            UserOrganization.organization_id == Organization.id
        ).join(
            Role,
            Role.id == UserOrganization.role_id
        ).filter(
            UserOrganization.user_id == user_id
        ).all()

        return [
            {
                "organization": org,
                "role": role,
                "is_default": is_default
            }
            for org, role, is_default in results
        ]

    def update_last_login(self, user_id: int) -> Optional[User]:
        """
        Update user's last_login timestamp to current time

        Example:
            user = user_repo.update_last_login(user_id=1)
        """
        from datetime import datetime
        user = self.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user
