"""
Create Organization Use Case
Create new organization with unique name and PIN
"""

import secrets
import string
from typing import Optional
from ..domain.organization import Organization
from ..domain.interfaces import IOrganizationRepository
from shared.errors import ValidationError
from shared.validators import sanitize_string


class CreateOrganizationUseCase:
    """Use case for creating organization"""

    def __init__(self, org_repo: IOrganizationRepository):
        self.org_repo = org_repo

    def execute(
        self,
        name: str,
        pin: Optional[str] = None,
        description: Optional[str] = None,
        address: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        logo_url: Optional[str] = None
    ) -> Organization:
        """
        Create new organization

        Args:
            name: Organization name
            pin: Optional organization PIN (8 digits, auto-generated if not provided)
            description: Optional organization description
            address: Optional organization address
            contact_email: Optional contact email
            contact_phone: Optional contact phone
            logo_url: Optional logo URL

        Returns:
            Created organization

        Raises:
            ValidationError: If name already exists or PIN already used
        """

        # Sanitize inputs
        name = sanitize_string(name)

        # Check if name already exists
        existing_org = self.org_repo.find_by_name(name)
        if existing_org:
            raise ValidationError(
                message=f"Organization dengan nama '{name}' sudah ada",
                details={"field": "name"}
            )

        # Generate PIN if not provided
        if not pin:
            pin = self._generate_pin()
        else:
            pin = pin.upper()

        # Check if PIN already exists
        existing_pin = self.org_repo.find_by_pin(pin)
        if existing_pin:
            raise ValidationError(
                message=f"Organization PIN '{pin}' sudah digunakan",
                details={"field": "organization_pin"}
            )

        # Create organization domain entity
        organization = Organization(
            id=None,
            name=name,
            organization_pin=pin,
            description=description,
            address=address,
            contact_email=contact_email,
            contact_phone=contact_phone,
            logo_url=logo_url,
            is_active=True
        )

        # Save to repository
        created_org = self.org_repo.create(organization)

        return created_org

    def _generate_pin(self) -> str:
        """Generate random 8-digit numeric PIN"""
        pin = ''.join(secrets.choice(string.digits) for _ in range(8))

        # Ensure PIN is unique
        if self.org_repo.find_by_pin(pin):
            return self._generate_pin()  # Retry if collision

        return pin
