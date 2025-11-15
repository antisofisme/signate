"""
SaveConnectionLogs Use Case
Handles saving batch connection logs from player devices
"""

from sqlalchemy.orm import Session
from typing import Dict, Any

from ..dtos import SaveConnectionLogsDTO
from ..repositories.device_connection_log_repo import DeviceConnectionLogRepository
from ..repositories.device_repo import DeviceRepository
from shared.errors import NotFoundError


class SaveConnectionLogs:
    """Use case for saving device connection logs"""

    def __init__(self, db: Session):
        self.db = db
        self.connection_log_repo = DeviceConnectionLogRepository(db)
        self.device_repo = DeviceRepository(db)

    def execute(
        self,
        device_id: int,
        dto: SaveConnectionLogsDTO
    ) -> Dict[str, Any]:
        """
        Save batch of connection logs from player

        Args:
            device_id: Device ID
            dto: Connection logs DTO

        Returns:
            Dict with success status and count

        Raises:
            NotFoundError: If device not found
        """
        # Validate device exists
        device = self.device_repo.find_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device with ID {device_id} not found")

        # Save logs in batch
        count = self.connection_log_repo.save_logs_batch(
            device_id=device_id,
            logs=dto.logs
        )

        return {
            "success": True,
            "count": count,
            "device_id": device_id,
            "message": f"Successfully saved {count} connection logs"
        }
