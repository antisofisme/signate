"""
Organization Repository Implementation
Implements organization data access
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from .models import OrganizationModel


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
            OrganizationModel.organization_pin == pin
        ).first()

    def get_all_active(self) -> List[OrganizationModel]:
        """Get all active organizations"""
        return self.db.query(OrganizationModel).filter(
            OrganizationModel.is_active == True
        ).all()

    def get_user_organizations(self, user_id: int) -> List[OrganizationModel]:
        """
        Get organizations accessible to user
        For now, returns all organizations (user can select which one to use)
        """
        return self.get_all_active()
