"""
Sync Guests Use Case
Handle guest data sync from Firebird Bridge Agent
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timezone

from services.pms.repositories.pms_repo import PMSRepository


class SyncGuestsUseCase:
    """Use case for syncing guest data"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = PMSRepository(db)

    def execute(self, guests_data: List[Dict[str, Any]], organization_id: int) -> Dict[str, Any]:
        """
        Sync guest data from PMS

        Args:
            guests_data: List of guest records
            organization_id: Organization ID

        Returns:
            Summary of sync operation
        """
        created_count = 0
        errors = []

        for guest_data in guests_data:
            try:
                # Validate organization ID matches
                if guest_data.get("organization_id") != organization_id:
                    errors.append({
                        "guest": guest_data.get("guest_name"),
                        "error": "Organization ID mismatch"
                    })
                    continue

                # Parse dates
                guest_data["checkin_date"] = datetime.fromisoformat(guest_data["checkin_date"])
                guest_data["checkout_date"] = datetime.fromisoformat(guest_data["checkout_date"])
                guest_data["synced_at"] = datetime.now(timezone.utc)

                # Create guest record
                self.repo.create_guest(guest_data)
                created_count += 1

            except Exception as e:
                errors.append({
                    "guest": guest_data.get("guest_name", "Unknown"),
                    "error": str(e)
                })

        # Update last sync timestamp
        self.repo.update_last_sync(organization_id)

        return {
            "synced": created_count,
            "total": len(guests_data),
            "errors": errors,
            "synced_at": datetime.now(timezone.utc).isoformat()
        }
