"""
Get Pending Commands Use Case
Retrieve pending commands for device (called by player)
"""

from typing import List, Optional, Dict, Any

from ..domain.device_command import DeviceCommand
from ..repositories.device_command_repo import DeviceCommandRepository
from ..repositories.device_repo import DeviceRepository
from shared.errors import NotFoundError


class GetPendingCommandsUseCase:
    """
    Use case for getting pending commands for device
    Called by player to retrieve commands to execute
    """

    def __init__(
        self,
        command_repo: DeviceCommandRepository,
        device_repo: DeviceRepository
    ):
        self.command_repo = command_repo
        self.device_repo = device_repo

    def execute(self, device_id: int, limit: int = 10) -> List[DeviceCommand]:
        """
        Get pending commands for device

        Args:
            device_id: Device ID
            limit: Maximum number of commands to return

        Returns:
            List of pending DeviceCommand objects

        Raises:
            NotFoundError: If device not found
        """

        # Verify device exists
        device = self.device_repo.find_by_id(device_id)
        if not device:
            raise NotFoundError(
                message=f"Device with ID {device_id} not found",
                resource_type="device",
                resource_id=device_id
            )

        # Get pending commands using stored procedure
        commands = self.command_repo.get_pending_commands(device_id, limit)

        return commands


class MarkCommandExecutedUseCase:
    """
    Use case for marking command as executed
    Called by player after successful command execution
    """

    def __init__(self, command_repo: DeviceCommandRepository):
        self.command_repo = command_repo

    def execute(
        self,
        command_id: int,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark command as executed

        Args:
            command_id: Command ID
            result: Execution result

        Returns:
            True if successful
        """

        # Verify command exists
        command = self.command_repo.find_by_id(command_id)
        if not command:
            return False

        # Mark as executed using stored procedure
        success = self.command_repo.mark_executed(command_id, result)

        return success


class MarkCommandFailedUseCase:
    """
    Use case for marking command as failed
    Called by player if command execution fails
    Implements retry logic
    """

    def __init__(self, command_repo: DeviceCommandRepository):
        self.command_repo = command_repo

    def execute(self, command_id: int, error_message: str) -> bool:
        """
        Mark command as failed

        Args:
            command_id: Command ID
            error_message: Error message

        Returns:
            True if successful
        """

        # Verify command exists
        command = self.command_repo.find_by_id(command_id)
        if not command:
            return False

        # Mark as failed using stored procedure (handles retry logic)
        success = self.command_repo.mark_failed(command_id, error_message)

        return success
