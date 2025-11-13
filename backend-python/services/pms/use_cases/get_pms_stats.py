"""
Get PMS Stats Use Case
Get statistics about PMS data
"""

from sqlalchemy.orm import Session
from typing import Dict, Any

from services.pms.repositories.pms_repo import PMSRepository


class GetPMSStatsUseCase:
    """Use case for getting PMS statistics"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = PMSRepository(db)

    def execute(self, organization_id: int) -> Dict[str, Any]:
        """
        Get PMS integration statistics

        Args:
            organization_id: Organization ID

        Returns:
            Statistics dictionary
        """
        # Get guest stats
        current_guests = self.repo.get_current_guests(organization_id)
        checkins_today = self.repo.get_checkins_today(organization_id)
        checkouts_today = self.repo.get_checkouts_today(organization_id)

        # Get room stats
        room_stats = self.repo.get_room_stats(organization_id)

        # Get last sync time
        config = self.repo.get_config_by_organization(organization_id)
        last_sync = config.last_synced_at.isoformat() if config and config.last_synced_at else None

        return {
            "total_guests": len(current_guests),
            "checkins_today": len(checkins_today),
            "checkouts_today": len(checkouts_today),
            "current_occupancy": len(current_guests),
            "total_rooms": room_stats["total_rooms"],
            "available_rooms": room_stats["available_rooms"],
            "occupied_rooms": room_stats["occupied_rooms"],
            "last_synced_at": last_sync,
        }
