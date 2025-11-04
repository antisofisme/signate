"""
List Devices Use Case
Get all devices for an organization
"""

from typing import List, Optional

from ..domain.device import Device
from ..domain.interfaces import IDeviceRepository


class ListDevicesUseCase:
    """
    Use case for listing devices
    Called by CMS to display all devices
    """

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    def execute(
        self,
        organization_id: int,
        status_filter: Optional[str] = None,
        online_only: bool = False
    ) -> List[Device]:
        """
        List all devices for organization

        Args:
            organization_id: Organization ID
            status_filter: Optional filter by status ('active', 'pending', 'inactive')
            online_only: If True, only return online devices

        Returns:
            List of Device entities
        """

        # Get all devices for organization
        if online_only:
            devices = self.device_repo.find_online_devices(organization_id)
        else:
            devices = self.device_repo.list_by_organization(organization_id)

        # Filter by status if specified
        if status_filter:
            devices = [d for d in devices if d.status == status_filter]

        return devices

    def count_devices(self, organization_id: int) -> int:
        """
        Count total devices for organization

        Args:
            organization_id: Organization ID

        Returns:
            Total device count
        """
        return self.device_repo.count_by_organization(organization_id)

    def count_online_devices(self, organization_id: int) -> int:
        """
        Count online devices for organization

        Args:
            organization_id: Organization ID

        Returns:
            Online device count
        """
        online_devices = self.device_repo.find_online_devices(organization_id)
        return len(online_devices)
