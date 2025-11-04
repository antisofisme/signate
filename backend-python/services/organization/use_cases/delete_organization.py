"""
Delete Organization Use Case
Soft delete organization (set inactive)
"""

from ..domain.interfaces import IOrganizationRepository
from shared.errors import ValidationError, NotFoundError, ErrorCodes


class DeleteOrganizationUseCase:
    """Use case for deleting organization"""

    def __init__(self, org_repo: IOrganizationRepository):
        self.org_repo = org_repo

    def execute(self, org_id: int) -> bool:
        """
        Delete organization (soft delete - set inactive)

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
                resource_type="organization",
                resource_id=org_id
            )

        # Check if organization has users
        user_count = self.org_repo.count_users(org_id)
        if user_count > 0:
            raise ValidationError(
                message=f"Tidak bisa menghapus organization yang masih memiliki {user_count} user(s)",
                code=ErrorCodes.VALIDATION_ERROR,
                details={"user_count": user_count}
            )

        # Check if organization has devices
        device_count = self.org_repo.count_devices(org_id)
        if device_count > 0:
            raise ValidationError(
                message=f"Tidak bisa menghapus organization yang masih memiliki {device_count} device(s)",
                code=ErrorCodes.VALIDATION_ERROR,
                details={"device_count": device_count}
            )

        # Soft delete
        success = self.org_repo.delete(org_id)

        return success
