"""
List Organizations Use Case
Get all organizations with stats
"""

from typing import List, Dict, Any
from ..domain.interfaces import IOrganizationRepository


class ListOrganizationsUseCase:
    """Use case for listing organizations"""

    def __init__(self, org_repo: IOrganizationRepository):
        self.org_repo = org_repo

    def execute(self, active_only: bool = False) -> Dict[str, Any]:
        """
        List all organizations

        Args:
            active_only: Only return active organizations (default: False - show all)

        Returns:
            Dictionary with organizations list and stats
        """

        organizations = self.org_repo.get_all(active_only=active_only)

        # Calculate stats
        total = len(organizations)
        active = sum(1 for org in organizations if org.is_active)

        return {
            "organizations": organizations,
            "total": total,
            "active": active
        }

    def get_organization_stats(self, org_id: int) -> Dict[str, int]:
        """
        Get stats for a specific organization

        Args:
            org_id: Organization ID

        Returns:
            Dictionary with user_count and device_count
        """

        user_count = self.org_repo.count_users(org_id)
        device_count = self.org_repo.count_devices(org_id)

        return {
            "user_count": user_count,
            "device_count": device_count
        }
