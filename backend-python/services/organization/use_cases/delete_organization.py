"""
Delete Organization Use Case
Hard delete organization (permanently remove from database)
"""

from ..domain.interfaces import IOrganizationRepository
from shared.errors import ValidationError, NotFoundError


class DeleteOrganizationUseCase:
    """Use case for deleting organization"""

    def __init__(self, org_repo: IOrganizationRepository):
        self.org_repo = org_repo

    def execute(self, org_id: int) -> bool:
        """
        Delete organization (hard delete - permanently remove)

        Args:
            org_id: Organization ID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If organization not found
            ValidationError: If organization has users or devices
        """

        # Find organization
        organization = self.org_repo.find_by_id(org_id)
        if not organization:
            raise NotFoundError(
                message=f"Organization dengan ID {org_id} tidak ditemukan",
                details={"resource_type": "organization", "resource_id": org_id}
            )

        # Check if organization has users
        user_count = self.org_repo.count_users(org_id)
        if user_count > 0:
            raise ValidationError(
                message=f"Tidak bisa menghapus organization yang masih memiliki {user_count} user(s)",
                details={"user_count": user_count}
            )

        # Check if organization has devices
        device_count = self.org_repo.count_devices(org_id)
        if device_count > 0:
            raise ValidationError(
                message=f"Tidak bisa menghapus organization yang masih memiliki {device_count} device(s)",
                details={"device_count": device_count}
            )

        # Hard delete - permanently remove from database
        success = self.org_repo.delete(org_id)

        return success
