"""List Users Use Case"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from services.auth.repositories.models import UserModel, OrganizationModel


class ListUsersUseCase:
    """Use case for listing users"""

    def __init__(self, db: Session):
        self.db = db

    def execute(
        self,
        organization_id: Optional[int] = None,
        role: Optional[str] = None,
        active_only: bool = False
    ) -> Dict[str, Any]:
        """
        List users with filters

        Args:
            organization_id: Filter by organization
            role: Filter by role
            active_only: Only active users

        Returns:
            Dictionary with users list and stats
        """

        query = self.db.query(UserModel)

        # Apply filters
        if organization_id:
            query = query.filter(UserModel.organization_id == organization_id)

        if role:
            query = query.filter(UserModel.role == role)

        if active_only:
            query = query.filter(UserModel.is_active == True)

        users = query.order_by(UserModel.created_at.desc()).all()

        # Calculate stats
        total = len(users)
        active = sum(1 for user in users if user.is_active)

        return {
            "users": users,
            "total": total,
            "active": active
        }

    def get_user_organization_name(self, user_id: int) -> Optional[str]:
        """Get organization name for user"""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user and user.organization_id:
            org = self.db.query(OrganizationModel).filter(
                OrganizationModel.id == user.organization_id
            ).first()
            return org.name if org else None
        return None
