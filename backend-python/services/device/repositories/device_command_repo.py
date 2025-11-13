"""
Device Command Repository
Data access layer for device commands
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from .models import DeviceCommandModel, DeviceHealthMetricModel
from ..domain.device_command import DeviceCommand
from ..domain.device_health import DeviceHealthMetric, HealthAlert, OrganizationHealthSummary


class DeviceCommandRepository:
    """
    Repository for device command persistence
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, command: DeviceCommand) -> DeviceCommand:
        """
        Create new device command

        Args:
            command: DeviceCommand domain model

        Returns:
            Created DeviceCommand with database ID
        """
        db_command = DeviceCommandModel(
            device_id=command.device_id,
            organization_id=command.organization_id,
            command_type=command.command_type,
            command_data=command.command_data,
            status=command.status,
            priority=command.priority,
            created_by_id=command.created_by_id,
            expires_at=command.expires_at,
            max_retries=command.max_retries
        )

        self.db.add(db_command)
        self.db.commit()
        self.db.refresh(db_command)

        return self._to_domain(db_command)

    def find_by_id(self, command_id: int) -> Optional[DeviceCommand]:
        """Find command by ID"""
        db_command = self.db.query(DeviceCommandModel).filter(
            DeviceCommandModel.id == command_id
        ).first()

        return self._to_domain(db_command) if db_command else None

    def get_pending_commands(self, device_id: int, limit: int = 10) -> List[DeviceCommand]:
        """
        Get pending commands for device using stored procedure

        Args:
            device_id: Device ID
            limit: Maximum number of commands to return

        Returns:
            List of pending DeviceCommand objects
        """
        # Use database stored function
        result = self.db.execute(
            text("SELECT * FROM get_pending_device_commands(:device_id)"),
            {"device_id": device_id}
        )

        commands = []
        for row in result:
            # Create simplified DeviceCommand from function result
            command = DeviceCommand(
                id=row.id,
                device_id=device_id,
                organization_id=0,  # Not needed for pending commands
                command_type=row.command_type,
                command_data=row.command_data,
                status='pending',
                priority=row.priority,
                created_at=row.created_at,
                expires_at=row.expires_at
            )
            commands.append(command)

        return commands

    def mark_executed(self, command_id: int, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark command as executed using stored procedure

        Args:
            command_id: Command ID
            result: Execution result

        Returns:
            True if successful
        """
        import json

        result_json = json.dumps(result) if result else '{"status": "success"}'

        db_result = self.db.execute(
            text("SELECT mark_command_executed(:command_id, :result::jsonb)"),
            {"command_id": command_id, "result": result_json}
        )

        self.db.commit()
        return db_result.scalar()

    def mark_failed(self, command_id: int, error_message: str) -> bool:
        """
        Mark command as failed using stored procedure

        Args:
            command_id: Command ID
            error_message: Error message

        Returns:
            True if successful
        """
        db_result = self.db.execute(
            text("SELECT mark_command_failed(:command_id, :error_message)"),
            {"command_id": command_id, "error_message": error_message}
        )

        self.db.commit()
        return db_result.scalar()

    def get_device_commands(
        self,
        device_id: int,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[DeviceCommand]:
        """
        Get commands for a device with optional status filter

        Args:
            device_id: Device ID
            status: Optional status filter
            limit: Maximum number of commands

        Returns:
            List of DeviceCommand objects
        """
        query = self.db.query(DeviceCommandModel).filter(
            DeviceCommandModel.device_id == device_id
        )

        if status:
            query = query.filter(DeviceCommandModel.status == status)

        query = query.order_by(
            DeviceCommandModel.priority.asc(),
            DeviceCommandModel.created_at.desc()
        ).limit(limit)

        return [self._to_domain(cmd) for cmd in query.all()]

    def expire_old_commands(self) -> int:
        """
        Expire old pending commands using stored procedure

        Returns:
            Number of expired commands
        """
        db_result = self.db.execute(
            text("SELECT expire_old_commands()")
        )

        self.db.commit()
        return db_result.scalar()

    def _to_domain(self, db_command: DeviceCommandModel) -> DeviceCommand:
        """Convert database model to domain model"""
        return DeviceCommand(
            id=db_command.id,
            device_id=db_command.device_id,
            organization_id=db_command.organization_id,
            command_type=db_command.command_type,
            command_data=db_command.command_data or {},
            status=db_command.status,
            priority=db_command.priority,
            sent_at=db_command.sent_at,
            executed_at=db_command.executed_at,
            failed_at=db_command.failed_at,
            result=db_command.result,
            error_message=db_command.error_message,
            retry_count=db_command.retry_count,
            max_retries=db_command.max_retries,
            created_by_id=db_command.created_by_id,
            created_at=db_command.created_at,
            updated_at=db_command.updated_at,
            expires_at=db_command.expires_at
        )
