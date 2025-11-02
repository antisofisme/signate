"""
Command Repository - Database Access untuk Device Commands
===========================================================

CENTRALIZED QUERIES untuk device_commands table
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta

from app.repositories.base import BaseRepository
from app.models.device_command import DeviceCommand, CommandStatus, CommandType


class CommandRepository(BaseRepository):
    """
    Command Repository untuk device command management

    Handles:
    - Command CRUD
    - Command queue operations
    - Status management
    - Expiration handling
    """

    def __init__(self, db: Session):
        super().__init__(DeviceCommand, db)
        self.db = db

    # =========================================================================
    # COMMAND-SPECIFIC QUERIES
    # =========================================================================

    def get_pending_commands(self, device_id: int) -> List[DeviceCommand]:
        """
        Get all pending commands for a device

        Example:
            commands = cmd_repo.get_pending_commands(device_id=5)
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.device_id == device_id,
                self.model.status == CommandStatus.PENDING
            )
        ).order_by(self.model.created_at.asc()).all()

    def get_device_commands(
        self,
        device_id: int,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DeviceCommand]:
        """
        Get commands for a device with optional status filter

        Example:
            commands = cmd_repo.get_device_commands(
                device_id=5,
                status="pending",
                limit=50
            )
        """
        query = self.db.query(self.model).filter(
            self.model.device_id == device_id
        )

        if status:
            query = query.filter(self.model.status == status)

        return query.order_by(
            self.model.created_at.desc()
        ).limit(limit).offset(offset).all()

    def get_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[DeviceCommand]:
        """
        Get commands by status across all devices

        Example:
            pending = cmd_repo.get_by_status(status="pending", limit=20)
        """
        return self.db.query(self.model).filter(
            self.model.status == status
        ).order_by(
            self.model.created_at.desc()
        ).limit(limit).offset(offset).all()

    def queue_command(
        self,
        device_id: int,
        command_type: str,
        reason: Optional[str] = None,
        expires_in_minutes: int = 60
    ) -> DeviceCommand:
        """
        Queue a new command for a device

        Example:
            command = cmd_repo.queue_command(
                device_id=5,
                command_type="reset",
                reason="Manual reset by admin",
                expires_in_minutes=30
            )
        """
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)

        command = DeviceCommand(
            device_id=device_id,
            command_type=command_type,
            reason=reason,
            status=CommandStatus.PENDING,
            expires_at=expires_at
        )

        self.db.add(command)
        self.db.commit()
        self.db.refresh(command)
        return command

    def mark_executed(self, command_id: int) -> Optional[DeviceCommand]:
        """
        Mark a command as executed

        Example:
            command = cmd_repo.mark_executed(command_id=10)
        """
        command = self.get(command_id)
        if command:
            command.status = CommandStatus.EXECUTED
            command.executed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(command)
        return command

    def mark_expired(self, command_id: int) -> Optional[DeviceCommand]:
        """
        Mark a command as expired

        Example:
            command = cmd_repo.mark_expired(command_id=10)
        """
        command = self.get(command_id)
        if command:
            command.status = CommandStatus.EXPIRED
            self.db.commit()
            self.db.refresh(command)
        return command

    def expire_old_commands(self, before_date: Optional[datetime] = None) -> int:
        """
        Mark all pending commands before a certain date as expired

        Example:
            count = cmd_repo.expire_old_commands()
        """
        if not before_date:
            before_date = datetime.utcnow()

        result = self.db.query(self.model).filter(
            and_(
                self.model.status == CommandStatus.PENDING,
                self.model.expires_at < before_date
            )
        ).update(
            {
                "status": CommandStatus.EXPIRED
            },
            synchronize_session=False
        )

        self.db.commit()
        return result

    def get_command_counts_by_status(
        self,
        device_id: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Get count of commands by status

        Example:
            counts = cmd_repo.get_command_counts_by_status(device_id=5)
            # Returns: {"pending": 3, "executed": 10, "expired": 2}
        """
        query = self.db.query(
            self.model.status,
            func.count(self.model.id).label('count')
        )

        if device_id:
            query = query.filter(self.model.device_id == device_id)

        query = query.group_by(self.model.status)

        results = query.all()

        counts = {
            "pending": 0,
            "executed": 0,
            "expired": 0
        }

        for status, count in results:
            counts[status] = count

        return counts

    def cancel_pending_commands(self, device_id: int) -> int:
        """
        Cancel (expire) all pending commands for a device

        Example:
            count = cmd_repo.cancel_pending_commands(device_id=5)
        """
        result = self.db.query(self.model).filter(
            and_(
                self.model.device_id == device_id,
                self.model.status == CommandStatus.PENDING
            )
        ).update(
            {
                "status": CommandStatus.EXPIRED
            },
            synchronize_session=False
        )

        self.db.commit()
        return result

    def delete_old_executed_commands(self, days_old: int = 30) -> int:
        """
        Delete executed commands older than X days

        Example:
            deleted = cmd_repo.delete_old_executed_commands(days_old=30)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = self.db.query(self.model).filter(
            and_(
                self.model.status == CommandStatus.EXECUTED,
                self.model.executed_at < cutoff_date
            )
        ).delete(synchronize_session=False)

        self.db.commit()
        return result
