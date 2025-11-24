"""
SaveDeviceLogsBatch Use Case
Handles saving batch console logs from player devices
"""

from sqlalchemy.orm import Session
from typing import Dict, Any

from ..dtos import BatchDeviceLogsRequest
from ..repositories.device_log_repository import DeviceLogRepository
from ..repositories.device_repo import DeviceRepository
from shared.errors import NotFoundError


class SaveDeviceLogsBatch:
    """Use case for saving device console logs in batch"""

    def __init__(self, db: Session):
        self.db = db
        self.device_log_repo = DeviceLogRepository(db)
        self.device_repo = DeviceRepository(db)

    def execute(
        self,
        device_id: int,
        dto: BatchDeviceLogsRequest
    ) -> Dict[str, Any]:
        """
        Save batch of console logs from player browser

        Args:
            device_id: Device ID
            dto: Batch device logs DTO containing log entries

        Returns:
            Dict with success status, count, and message

        Raises:
            NotFoundError: If device not found
        """
        # Validate device exists
        device = self.device_repo.find_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device with ID {device_id} not found")

        # Ensure device has organization_id (multi-tenancy)
        if not device.organization_id:
            raise NotFoundError(f"Device {device_id} is not assigned to any organization")

        # Convert DTO logs to dict format for repository
        logs_data = [
            {
                'level': log.level,
                'message': log.message,
                'timestamp': log.timestamp,
                'source': log.source,
                'stack_trace': log.stack_trace,
                'user_agent': log.user_agent,
                'url': log.url
            }
            for log in dto.logs
        ]

        # Save logs in batch (single SQL INSERT)
        count = self.device_log_repo.save_logs_batch(
            device_id=device_id,
            organization_id=device.organization_id,
            logs=logs_data
        )

        return {
            "success": True,
            "logs_saved": count,
            "device_id": device_id,
            "organization_id": device.organization_id,
            "message": f"Successfully saved {count} console logs"
        }
