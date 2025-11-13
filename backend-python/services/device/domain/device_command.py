"""
Device Command Domain Model
Business logic for device remote commands
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any


@dataclass
class DeviceCommand:
    """
    Device Command entity - represents a command sent to a device
    """
    id: int
    device_id: int
    organization_id: int

    # Command details
    command_type: str  # 'reboot', 'refresh_content', 'update_settings', 'clear_cache', 'screenshot'
    command_data: Dict[str, Any]  # Additional command parameters

    # Status tracking
    status: str  # 'pending', 'sent', 'executed', 'failed', 'expired'
    priority: int  # 1 (highest) to 10 (lowest)

    # Execution tracking
    sent_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Audit tracking
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def is_pending(self) -> bool:
        """Check if command is pending execution"""
        return self.status == 'pending'

    def is_executed(self) -> bool:
        """Check if command was successfully executed"""
        return self.status == 'executed'

    def is_failed(self) -> bool:
        """Check if command failed permanently"""
        return self.status == 'failed'

    def is_expired(self) -> bool:
        """Check if command has expired"""
        if self.status == 'expired':
            return True
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return True
        return False

    def can_retry(self) -> bool:
        """Check if command can be retried"""
        return (
            self.status in ('pending', 'failed') and
            self.retry_count < self.max_retries and
            not self.is_expired()
        )

    def mark_sent(self) -> None:
        """Mark command as sent to device"""
        self.status = 'sent'
        self.sent_at = datetime.now(timezone.utc)

    def mark_executed(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark command as successfully executed"""
        self.status = 'executed'
        self.executed_at = datetime.now(timezone.utc)
        self.result = result or {"status": "success"}

    def mark_failed(self, error_message: str) -> None:
        """Mark command as failed"""
        self.retry_count += 1

        if self.retry_count >= self.max_retries:
            self.status = 'failed'
            self.failed_at = datetime.now(timezone.utc)
        else:
            # Reset to pending for retry
            self.status = 'pending'

        self.error_message = error_message

    def mark_expired(self) -> None:
        """Mark command as expired"""
        self.status = 'expired'

    @staticmethod
    def create_new(
        device_id: int,
        organization_id: int,
        command_type: str,
        command_data: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        created_by: Optional[int] = None,
        expires_in_minutes: int = 60
    ) -> 'DeviceCommand':
        """
        Create a new device command

        Args:
            device_id: Device to send command to
            organization_id: Organization ID
            command_type: Type of command
            command_data: Additional command parameters
            priority: Command priority (1-10)
            created_by: User ID who created the command
            expires_in_minutes: Command expiration time in minutes

        Returns:
            New DeviceCommand instance
        """
        now = datetime.now(timezone.utc)

        return DeviceCommand(
            id=0,  # Will be set by database
            device_id=device_id,
            organization_id=organization_id,
            command_type=command_type,
            command_data=command_data or {},
            status='pending',
            priority=priority,
            created_by_id=created_by,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(minutes=expires_in_minutes)
        )

    @staticmethod
    def validate_command_type(command_type: str) -> bool:
        """Validate command type"""
        valid_types = [
            'reboot',
            'refresh_content',
            'update_settings',
            'clear_cache',
            'screenshot',
            'update_playlist'
        ]
        return command_type in valid_types

    @staticmethod
    def validate_priority(priority: int) -> bool:
        """Validate command priority"""
        return 1 <= priority <= 10
