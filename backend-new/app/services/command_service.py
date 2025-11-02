"""
Command Service
===============

Business logic layer for device command operations.
Handles command queueing, status management, and expiration.

Clean Architecture: API → Service → Repository → Database
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ValidationException
)
from app.repositories.command_repository import CommandRepository
from app.repositories.device_repository import DeviceRepository
from app.models.device_command import DeviceCommand, CommandType, CommandStatus


class CommandService:
    """
    Command Service

    Handles all device command business logic:
    - Command execution (single and batch)
    - Status management
    - Command queue operations
    - Expiration handling
    """

    def __init__(self, db: Session):
        """
        Initialize CommandService

        Args:
            db: Database session
        """
        self.db = db
        self.command_repo = CommandRepository(db)
        self.device_repo = DeviceRepository(db)

    def execute_command(
        self,
        device_id: int,
        command_type: str,
        reason: Optional[str] = None,
        expires_in_minutes: Optional[int] = None
    ) -> DeviceCommand:
        """
        Queue a command for execution on a device

        Args:
            device_id: Target device ID
            command_type: Type of command (reset, refresh, reload)
            reason: Reason for executing command
            expires_in_minutes: Command expiration time

        Returns:
            DeviceCommand model

        Raises:
            NotFoundException: If device not found
            BadRequestException: If command type invalid
        """
        # Validate device exists
        device = self.device_repo.get(device_id)
        if not device:
            raise NotFoundException(
                message=f"Device {device_id} not found"
            )

        # Validate command type
        valid_commands = [cmd.value for cmd in CommandType]
        if command_type not in valid_commands:
            raise BadRequestException(
                message=f"Invalid command type. Must be one of: {', '.join(valid_commands)}"
            )

        # Use default expiration from config if not specified
        if expires_in_minutes is None:
            expires_in_minutes = settings.COMMAND_EXECUTION_TIMEOUT // 60  # Convert seconds to minutes

        # Queue command
        command = self.command_repo.queue_command(
            device_id=device_id,
            command_type=command_type,
            reason=reason,
            expires_in_minutes=expires_in_minutes
        )

        return command

    def batch_execute_command(
        self,
        device_ids: List[int],
        command_type: str,
        reason: Optional[str] = None,
        expires_in_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Queue a command for execution on multiple devices

        Args:
            device_ids: List of target device IDs
            command_type: Type of command
            reason: Reason for executing command
            expires_in_minutes: Command expiration time

        Returns:
            Dict with total, successful, failed counts and command list
        """
        # Validate command type
        valid_commands = [cmd.value for cmd in CommandType]
        if command_type not in valid_commands:
            raise BadRequestException(
                message=f"Invalid command type. Must be one of: {', '.join(valid_commands)}"
            )

        # Limit batch size
        if len(device_ids) > 100:
            raise BadRequestException(
                message="Maximum 100 devices per batch operation"
            )

        commands = []
        errors = []
        successful = 0
        failed = 0

        for device_id in device_ids:
            try:
                command = self.execute_command(
                    device_id=device_id,
                    command_type=command_type,
                    reason=reason,
                    expires_in_minutes=expires_in_minutes
                )
                commands.append(command)
                successful += 1
            except Exception as e:
                errors.append(f"Device {device_id}: {str(e)}")
                failed += 1

        return {
            "total": len(device_ids),
            "successful": successful,
            "failed": failed,
            "commands": commands,
            "errors": errors
        }

    def get_command(self, command_id: int) -> DeviceCommand:
        """
        Get command by ID

        Args:
            command_id: Command ID

        Returns:
            DeviceCommand model

        Raises:
            NotFoundException: If command not found
        """
        command = self.command_repo.get(command_id)

        if not command:
            raise NotFoundException(
                message=f"Command {command_id} not found"
            )

        return command

    def list_commands(
        self,
        device_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List commands with optional filters

        Args:
            device_id: Filter by device ID
            status: Filter by status
            skip: Pagination offset
            limit: Maximum results

        Returns:
            Dict with commands list, total, skip, limit, and status_counts
        """
        # Validate limit
        if limit > 100:
            limit = 100

        # Get commands
        if device_id:
            commands = self.command_repo.get_device_commands(
                device_id=device_id,
                status=status,
                limit=limit,
                offset=skip
            )
            # Get total count for device
            all_commands = self.command_repo.get_device_commands(
                device_id=device_id,
                status=status,
                limit=999999  # Get all for count
            )
            total = len(all_commands)
        elif status:
            commands = self.command_repo.get_by_status(
                status=status,
                limit=limit,
                offset=skip
            )
            # Get total for status
            all_commands = self.command_repo.get_by_status(
                status=status,
                limit=999999
            )
            total = len(all_commands)
        else:
            # Get all commands (paginated)
            commands = self.command_repo.get_all(limit=limit, offset=skip)
            total = self.command_repo.count()

        # Get status counts
        status_counts = self.command_repo.get_command_counts_by_status(device_id=device_id)

        return {
            "commands": commands,
            "total": total,
            "skip": skip,
            "limit": limit,
            "status_counts": status_counts
        }

    def get_pending_commands(self, device_id: int) -> List[DeviceCommand]:
        """
        Get all pending commands for a device

        Args:
            device_id: Device ID

        Returns:
            List of pending DeviceCommand models
        """
        return self.command_repo.get_pending_commands(device_id)

    def mark_command_executed(self, command_id: int) -> DeviceCommand:
        """
        Mark command as executed (called by device)

        Args:
            command_id: Command ID

        Returns:
            Updated DeviceCommand model

        Raises:
            NotFoundException: If command not found
            BadRequestException: If command already executed/expired
        """
        command = self.get_command(command_id)

        # Check if command is in valid state to be executed
        if command.status != CommandStatus.PENDING:
            raise BadRequestException(
                message=f"Command cannot be executed. Current status: {command.status}"
            )

        # Check if command has expired
        if command.expires_at and command.expires_at < datetime.utcnow():
            # Mark as expired instead
            self.command_repo.mark_expired(command_id)
            raise BadRequestException(
                message="Command has expired"
            )

        # Mark as executed
        updated_command = self.command_repo.mark_executed(command_id)

        return updated_command

    def mark_command_expired(self, command_id: int) -> DeviceCommand:
        """
        Mark command as expired

        Args:
            command_id: Command ID

        Returns:
            Updated DeviceCommand model

        Raises:
            NotFoundException: If command not found
        """
        command = self.get_command(command_id)

        # Mark as expired
        updated_command = self.command_repo.mark_expired(command_id)

        return updated_command

    def cancel_device_commands(self, device_id: int) -> int:
        """
        Cancel (expire) all pending commands for a device

        Args:
            device_id: Device ID

        Returns:
            Number of commands cancelled
        """
        count = self.command_repo.cancel_pending_commands(device_id)
        return count

    def expire_old_commands(self) -> int:
        """
        Expire all commands past their expiration date

        This should be called periodically by a background task.

        Returns:
            Number of commands expired
        """
        count = self.command_repo.expire_old_commands()
        return count

    def cleanup_old_commands(self, days_old: int = 30) -> int:
        """
        Delete executed commands older than X days

        Args:
            days_old: Delete commands older than this many days

        Returns:
            Number of commands deleted
        """
        count = self.command_repo.delete_old_executed_commands(days_old=days_old)
        return count

    def get_device_command_stats(self, device_id: int) -> Dict[str, Any]:
        """
        Get command statistics for a device

        Args:
            device_id: Device ID

        Returns:
            Dict with command counts by status
        """
        counts = self.command_repo.get_command_counts_by_status(device_id=device_id)

        return {
            "device_id": device_id,
            "pending": counts.get("pending", 0),
            "executed": counts.get("executed", 0),
            "expired": counts.get("expired", 0),
            "total": sum(counts.values())
        }
