"""
Update Organization Use Case
Update organization name and status
"""

from ..domain.organization import Organization
from ..domain.interfaces import IOrganizationRepository
from shared.errors import ValidationError, NotFoundError, ErrorCodes
from shared.validators import sanitize_string


class UpdateOrganizationUseCase:
    """Use case for updating organization"""

    def __init__(self, org_repo: IOrganizationRepository):
        self.org_repo = org_repo

    def execute(self, org_id: int, name: str) -> Organization:
        """
        Update organization

        Args:
            org_id: Organization ID
            name: New organization name

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
                resource_type="organization",
                resource_id=org_id
            )

        # Sanitize input
        name = sanitize_string(name)

        # Check if new name already exists (for another organization)
        existing_org = self.org_repo.find_by_name(name)
        if existing_org and existing_org.id != org_id:
            raise ValidationError(
                message=f"Organization dengan nama '{name}' sudah ada",
                code=ErrorCodes.ALREADY_EXISTS,
                details={"field": "name"}
            )

        # Update organization
        organization.name = name

        # Save changes
        updated_org = self.org_repo.update(organization)

        return updated_org
