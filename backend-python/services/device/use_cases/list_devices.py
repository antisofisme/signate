"""
List Devices Use Case
Get all devices for an organization

Device Status Flow:
- pending: New player requested code, not yet assigned to organization
- active: Device is active and assigned to organization (shows in Device List)
- inactive: Device is not playing content but still assigned (shows in Device List)
- released: Device was deleted from Device List (shows in Unsigned Pool for same org)
"""

from typing import List, Optional, Union

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
        organization_id: Optional[Union[int, str]] = None,
        status_filter: Optional[str] = None,
        online_only: bool = False,
        scope: str = "my_org",
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> List[Device]:
        """
        List devices with scope support

        Args:
            organization_id: Organization ID (None for pending devices, "all" for super admin)
            status_filter: Optional filter by status ('active', 'pending', 'inactive', 'released')
            online_only: If True, only return online devices
            scope: Query scope:
                - 'my_org': Active/inactive devices in Device List (status IN ['active', 'inactive'])
                - 'released': Released devices in Unsigned Pool (status = 'released', same org)
                - 'pending': Devices waiting to be claimed (status = 'pending', org_id = NULL)
                - 'all': All devices (super admin only)
            sort_by: Column to sort by (device_name, status, device_type, ip_address, last_seen_at)
            sort_dir: Sort direction ('asc' or 'desc')

        Returns:
            List of Device entities
        """

        # Handle different scopes
        if scope == "released":
            # Unsigned Pool: Released devices for this organization
            # These are devices that were deleted from Device List
            if not organization_id or organization_id == "all":
                # Released devices MUST have an organization_id
                return []
            devices = self.device_repo.list_released_by_organization(organization_id)
        elif scope == "pending" or scope == "unassigned":
            # Pending devices: org_id = NULL, waiting to be claimed
            # Note: "unassigned" is kept for backward compatibility
            devices = self.device_repo.list_by_organization(None)
        elif scope == "all":
            # Super admin - get all devices regardless of organization
            devices = self.device_repo.list_all()
        else:  # my_org (default)
            # Device List: Only active/inactive devices
            if online_only:
                devices = self.device_repo.find_online_devices(organization_id)
            else:
                # Use list_active_by_organization which filters for active/inactive only
                devices = self.device_repo.list_active_by_organization(
                    organization_id,
                    sort_by=sort_by,
                    sort_dir=sort_dir
                )

        # Filter by status if specified (additional filter on top of scope filter)
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
