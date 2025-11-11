"""
Sync Rooms Use Case
Handle room status sync from Firebird Bridge Agent
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from services.pms.repositories.pms_repo import PMSRepository


class SyncRoomsUseCase:
    """Use case for syncing room status"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = PMSRepository(db)

    def execute(self, rooms_data: List[Dict[str, Any]], organization_id: int) -> Dict[str, Any]:
        """
        Sync room status from PMS

        Args:
            rooms_data: List of room records
            organization_id: Organization ID

        Returns:
            Summary of sync operation
        """
        created_count = 0
        updated_count = 0
        errors = []

        for room_data in rooms_data:
            try:
                # Validate organization ID matches
                if room_data.get("organization_id") != organization_id:
                    errors.append({
                        "room": room_data.get("room_number"),
                        "error": "Organization ID mismatch"
                    })
                    continue

                # Check if room exists
                existing = self.db.query(
                    self.repo.db.query(self.repo.db.query).first()
                )

                # Upsert room (create or update)
                room = self.repo.upsert_room(room_data)

                # Count operation
                if existing:
                    updated_count += 1
                else:
                    created_count += 1

            except Exception as e:
                errors.append({
                    "room": room_data.get("room_number", "Unknown"),
                    "error": str(e)
                })

        # Update last sync timestamp
        self.repo.update_last_sync(organization_id)

        return {
            "created": created_count,
            "updated": updated_count,
            "total": len(rooms_data),
            "errors": errors,
            "synced_at": datetime.now().isoformat()
        }
