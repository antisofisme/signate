"""
Get Organization Use Case
Get single organization by ID
"""

from ..domain.organization import Organization
from ..domain.interfaces import IOrganizationRepository
from shared.errors import NotFoundError


class GetOrganizationUseCase:
    """Use case for getting organization by ID"""

    def __init__(self, org_repo: IOrganizationRepository):
        self.org_repo = org_repo

    def execute(self, org_id: int) -> Organization:
        """
        Get organization by ID

        Args:
            org_id: Organization ID

        Returns:
            Organization

        Raises:
            NotFoundError: If organization not found
        """

        organization = self.org_repo.find_by_id(org_id)

        if not organization:
            raise NotFoundError(
                message=f"Organization dengan ID {org_id} tidak ditemukan",
                resource_type="organization",
                resource_id=org_id
            )

        return organization
