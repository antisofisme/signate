"""
Update Organization Use Case
Update organization information (name, description, address, contact info, active status)
"""

from typing import Optional
from ..domain.organization import Organization
from ..domain.interfaces import IOrganizationRepository
from shared.errors import ValidationError, NotFoundError
from shared.validators import sanitize_string


class UpdateOrganizationUseCase:
    """Use case for updating organization"""

    def __init__(self, org_repo: IOrganizationRepository):
        self.org_repo = org_repo

    def execute(
        self,
        org_id: int,
        name: str,
        description: Optional[str] = None,
        address: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        logo_url: Optional[str] = None,
        is_active: bool = True
    ) -> Organization:
        """
        Update organization

        Args:
            org_id: Organization ID
            name: New organization name
            description: Optional organization description
            address: Optional organization address
            contact_email: Optional contact email
            contact_phone: Optional contact phone
            logo_url: Optional logo URL
            is_active: Organization active status

        Returns:
            Updated organization

        Raises:
            NotFoundError: If organization not found
            ValidationError: If name already exists
        """

        # Find existing organization
        organization = self.org_repo.find_by_id(org_id)
        if not organization:
            raise NotFoundError(
                message=f"Organization dengan ID {org_id} tidak ditemukan",
                details={"resource_type": "organization", "resource_id": org_id}
            )

        # Sanitize input
        name = sanitize_string(name)

        # Check if new name already exists (for another organization)
        existing_org = self.org_repo.find_by_name(name)
        if existing_org and existing_org.id != org_id:
            raise ValidationError(
                message=f"Organization dengan nama '{name}' sudah ada",
                details={"field": "name"}
            )

        # Update organization fields
        organization.name = name
        organization.description = description
        organization.address = address
        organization.contact_email = contact_email
        organization.contact_phone = contact_phone
        organization.logo_url = logo_url
        organization.is_active = is_active

        # Save changes
        updated_org = self.org_repo.update(organization)

        return updated_org
