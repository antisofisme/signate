"""
Send Device Command Use Case
Send command to device for remote management
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from ..domain.device_command import DeviceCommand
from ..repositories.device_command_repo import DeviceCommandRepository
from ..repositories.device_repo import DeviceRepository
from shared.errors import ValidationError, NotFoundError


class SendDeviceCommandUseCase:
    """
    Use case for sending command to device
    """

    def __init__(
        self,
        command_repo: DeviceCommandRepository,
        device_repo: DeviceRepository
    ):
        self.command_repo = command_repo
        self.device_repo = device_repo

    def execute(
        self,
        device_id: int,
        organization_id: int,
        command_type: str,
        command_data: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        created_by: Optional[int] = None,
        expires_in_minutes: int = 60
    ) -> DeviceCommand:
        """
        Send command to device

        Args:
            device_id: Target device ID
            organization_id: Organization ID (from JWT)
            command_type: Type of command to send
            command_data: Additional command parameters
            priority: Command priority (1-10)
            created_by: User ID who created command
            expires_in_minutes: Command expiration time

        Returns:
            Created DeviceCommand

        Raises:
            NotFoundError: If device not found
            ValidationError: If validation fails
        """

        # Validate command type
        if not DeviceCommand.validate_command_type(command_type):
            raise ValidationError(
                message=f"Invalid command type: {command_type}",
                details={"command_type": command_type}
            )

        # Validate priority
        if not DeviceCommand.validate_priority(priority):
            raise ValidationError(
                message=f"Priority must be between 1 and 10, got {priority}",
                details={"priority": priority}
            )

        # Verify device exists and belongs to organization
        device = self.device_repo.find_by_id(device_id)
        if not device:
            raise NotFoundError(
                message=f"Device with ID {device_id} not found",
                resource_type="device",
                resource_id=device_id
            )

        if device.organization_id != organization_id:
            raise ValidationError(
                message="Device does not belong to your organization",
                details={"device_id": device_id, "organization_id": organization_id}
            )

        # Create new command
        command = DeviceCommand.create_new(
            device_id=device_id,
            organization_id=organization_id,
            command_type=command_type,
            command_data=command_data,
            priority=priority,
            created_by=created_by,
            expires_in_minutes=expires_in_minutes
        )

        # Save to database
        created_command = self.command_repo.create(command)

        return created_command


class BulkSendDeviceCommandUseCase:
    """
    Use case for sending command to multiple devices
    """

    def __init__(
        self,
        command_repo: DeviceCommandRepository,
        device_repo: DeviceRepository
    ):
        self.command_repo = command_repo
        self.device_repo = device_repo

    def execute(
        self,
        device_ids: list[int],
        organization_id: int,
        command_type: str,
        command_data: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        created_by: Optional[int] = None,
        expires_in_minutes: int = 60
    ) -> list[DeviceCommand]:
        """
        Send command to multiple devices

        Args:
            device_ids: List of target device IDs
            organization_id: Organization ID (from JWT)
            command_type: Type of command to send
            command_data: Additional command parameters
            priority: Command priority (1-10)
            created_by: User ID who created command
            expires_in_minutes: Command expiration time

        Returns:
            List of created DeviceCommand objects

        Raises:
            ValidationError: If validation fails
        """

        # Validate command type
        if not DeviceCommand.validate_command_type(command_type):
            raise ValidationError(
                message=f"Invalid command type: {command_type}",
                details={"command_type": command_type}
            )

        # Validate priority
        if not DeviceCommand.validate_priority(priority):
            raise ValidationError(
                message=f"Priority must be between 1 and 10, got {priority}",
                details={"priority": priority}
            )

        # Validate device count
        if not device_ids or len(device_ids) > 100:
            raise ValidationError(
                message="Must provide 1-100 device IDs",
                details={"count": len(device_ids)}
            )

        created_commands = []

        for device_id in device_ids:
            # Verify device exists and belongs to organization
            device = self.device_repo.find_by_id(device_id)
            if not device:
                # Skip devices that don't exist
                continue

            if device.organization_id != organization_id:
                # Skip devices from other organizations
                continue

            # Create command for this device
            command = DeviceCommand.create_new(
                device_id=device_id,
                organization_id=organization_id,
                command_type=command_type,
                command_data=command_data,
                priority=priority,
                created_by=created_by,
                expires_in_minutes=expires_in_minutes
            )

            # Save to database
            created_command = self.command_repo.create(command)
            created_commands.append(created_command)

        return created_commands
