"""
Organization Repository Implementation
Implements organization data access
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from .models import OrganizationModel, UserModel


class OrganizationRepository:
    """Organization repository implementation"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, org_id: int) -> Optional[OrganizationModel]:
        """Find organization by ID"""
        return self.db.query(OrganizationModel).filter(
            OrganizationModel.id == org_id
        ).first()

    def find_by_pin(self, pin: str) -> Optional[OrganizationModel]:
        """Find organization by PIN"""
        return self.db.query(OrganizationModel).filter(
            OrganizationModel.pin == pin
        ).first()

    def get_all_active(self) -> List[OrganizationModel]:
        """Get all active organizations"""
        return self.db.query(OrganizationModel).filter(
            OrganizationModel.is_active == True
        ).all()

    def get_user_organizations(self, user_id: int) -> List[OrganizationModel]:
        """
        Get organizations accessible by a user.
        - SUPER_ADMIN: All active organizations
        - Other roles: Only their own organization
        """
        # Get user with role relationship
        user = self.db.query(UserModel).filter(
            UserModel.id == user_id,
            UserModel.is_active == True
        ).first()

        if not user:
            return []

        # SUPER_ADMIN can see all organizations
        if user.role and user.role.name.lower() == "super_admin":
            return self.get_all_active()

        # Other users only see their organization
        if user.organization_id:
            org = self.db.query(OrganizationModel).filter(
                OrganizationModel.id == user.organization_id,
                OrganizationModel.is_active == True
            ).first()
            return [org] if org else []

        return []
