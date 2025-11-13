"""
Organization Repository Implementation
Implements IOrganizationRepository using SQLAlchemy
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..domain.organization import Organization
from ..domain.interfaces import IOrganizationRepository
from services.auth.repositories.models import OrganizationModel, UserModel
from services.device.domain.device import Device


class OrganizationRepository(IOrganizationRepository):
    """Organization repository implementation"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, org_id: int) -> Optional[Organization]:
        """Find organization by ID"""
        org_model = self.db.query(OrganizationModel).filter(
            OrganizationModel.id == org_id
        ).first()
        return self._to_entity(org_model) if org_model else None

    def find_by_name(self, name: str) -> Optional[Organization]:
        """Find organization by name"""
        org_model = self.db.query(OrganizationModel).filter(
            OrganizationModel.name == name
        ).first()
        return self._to_entity(org_model) if org_model else None

    def find_by_pin(self, pin: str) -> Optional[Organization]:
        """Find organization by PIN"""
        org_model = self.db.query(OrganizationModel).filter(
            OrganizationModel.pin == pin
        ).first()
        return self._to_entity(org_model) if org_model else None

    def get_all(self, active_only: bool = False) -> List[Organization]:
        """Get all organizations"""
        query = self.db.query(OrganizationModel)

        if active_only:
            query = query.filter(OrganizationModel.is_active == True)

        org_models = query.order_by(OrganizationModel.created_at.desc()).all()
        return [self._to_entity(org) for org in org_models]

    def create(self, organization: Organization) -> Organization:
        """Create new organization"""
        org_model = OrganizationModel(
            name=organization.name,
            pin=organization.pin,
            description=organization.description,
            address=organization.address,
            contact_email=organization.contact_email,
            contact_phone=organization.contact_phone,
            logo_url=organization.logo_url,
            is_active=organization.is_active
        )
        self.db.add(org_model)
        self.db.commit()
        self.db.refresh(org_model)
        return self._to_entity(org_model)

    def update(self, organization: Organization) -> Organization:
        """Update existing organization"""
        org_model = self.db.query(OrganizationModel).filter(
            OrganizationModel.id == organization.id
        ).first()

        if not org_model:
            raise ValueError(f"Organization with id {organization.id} not found")

        org_model.name = organization.name
        org_model.description = organization.description
        org_model.address = organization.address
        org_model.contact_email = organization.contact_email
        org_model.contact_phone = organization.contact_phone
        org_model.logo_url = organization.logo_url
        org_model.is_active = organization.is_active
        # Note: PIN tidak bisa diubah setelah dibuat (security)

        self.db.commit()
        self.db.refresh(org_model)
        return self._to_entity(org_model)

    def delete(self, org_id: int) -> bool:
        """Delete organization (hard delete - permanently remove)"""
        org_model = self.db.query(OrganizationModel).filter(
            OrganizationModel.id == org_id
        ).first()

        if not org_model:
            return False

        # Hard delete - permanently remove from database
        self.db.delete(org_model)
        self.db.commit()
        return True

    def count_users(self, org_id: int) -> int:
        """Count users in organization"""
        return self.db.query(func.count(UserModel.id)).filter(
            UserModel.organization_id == org_id,
            UserModel.is_active == True
        ).scalar() or 0

    def count_devices(self, org_id: int) -> int:
        """Count devices in organization"""
        # Import here to avoid circular dependency
        from services.device.repositories.device_repo import DeviceModel

        return self.db.query(func.count(DeviceModel.id)).filter(
            DeviceModel.organization_id == org_id
        ).scalar() or 0

    def _to_entity(self, model: OrganizationModel) -> Organization:
        """Convert SQLAlchemy model to domain entity"""
        return Organization(
            id=model.id,
            name=model.name,
            pin=model.pin,
            description=model.description,
            address=model.address,
            contact_email=model.contact_email,
            contact_phone=model.contact_phone,
            logo_url=model.logo_url,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
