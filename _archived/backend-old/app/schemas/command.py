"""
Command System Schemas
Enhanced schemas for secure device command execution with comprehensive validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CommandType(str, Enum):
    """
    Supported command types with risk classification
    """
    # Low risk - Display controls
    VOLUME = "volume"
    BRIGHTNESS = "brightness"

    # Low risk - Diagnostics
    SCREENSHOT = "screenshot"
    NETWORK_TEST = "network_test"

    # Medium risk - System controls
    REBOOT = "reboot"
    CLEAR_CACHE = "clear_cache"
    RELOAD = "reload"
    REFRESH = "refresh"

    # High risk - System updates
    UPDATE = "update"

    # Critical risk - Shell access (requires 2FA)
    SHELL = "shell"

    # Legacy support
    RESET = "reset"


class CommandStatus(str, Enum):
    """
    Command execution status
    """
    PENDING = "pending"          # Queued, waiting to be sent
    SENT = "sent"                # Sent to device via WebSocket
    RUNNING = "running"          # Device is executing
    COMPLETED = "completed"      # Successfully executed
    FAILED = "failed"            # Execution failed
    CANCELLED = "cancelled"      # Cancelled by admin
    EXPIRED = "expired"          # Expired before execution


class CommandRiskLevel(str, Enum):
    """
    Risk classification for commands
    """
    LOW = "low"              # Safe commands (volume, brightness)
    MEDIUM = "medium"        # System commands (reboot)
    HIGH = "high"            # Update commands
    CRITICAL = "critical"    # Shell access


class ExecutionMode(str, Enum):
    """
    Execution mode for batch commands
    """
    PARALLEL = "parallel"      # Execute on all devices simultaneously
    SEQUENTIAL = "sequential"  # Execute one by one


# =============================================================================
# COMMAND REQUEST SCHEMAS
# =============================================================================

class CommandParametersBase(BaseModel):
    """Base for command parameters"""
    pass


class VolumeParameters(CommandParametersBase):
    """Parameters for volume control"""
    volume: int = Field(..., ge=0, le=100, description="Volume level (0-100)")

    @field_validator('volume')
    @classmethod
    def validate_volume(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Volume must be between 0 and 100')
        return v


class BrightnessParameters(CommandParametersBase):
    """Parameters for brightness control"""
    brightness: int = Field(..., ge=0, le=100, description="Brightness level (0-100)")

    @field_validator('brightness')
    @classmethod
    def validate_brightness(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Brightness must be between 0 and 100')
        return v


class ScreenshotParameters(CommandParametersBase):
    """Parameters for screenshot capture"""
    quality: int = Field(default=80, ge=1, le=100, description="JPEG quality (1-100)")
    upload: bool = Field(default=True, description="Upload to server immediately")


class RebootParameters(CommandParametersBase):
    """Parameters for reboot command"""
    delay_seconds: int = Field(default=5, ge=0, le=300, description="Delay before reboot (0-300s)")
    force: bool = Field(default=False, description="Force reboot without graceful shutdown")


class ShellParameters(CommandParametersBase):
    """
    Parameters for shell command execution
    SECURITY CRITICAL: Extensive validation required
    """
    command: str = Field(..., min_length=1, max_length=500, description="Shell command to execute")
    timeout: int = Field(default=30, ge=1, le=60, description="Timeout in seconds")
    working_directory: Optional[str] = Field(default=None, max_length=255)

    @field_validator('command')
    @classmethod
    def validate_command(cls, v):
        """Validate shell command against dangerous patterns"""
        if not v or not v.strip():
            raise ValueError('Command cannot be empty')

        # Max length check
        if len(v) > 500:
            raise ValueError('Command too long (max 500 characters)')

        return v.strip()


class UpdateParameters(CommandParametersBase):
    """Parameters for system update"""
    package: Optional[str] = Field(default=None, description="Specific package to update")
    version: Optional[str] = Field(default=None, description="Target version")
    force: bool = Field(default=False, description="Force update even if already up-to-date")


class NetworkTestParameters(CommandParametersBase):
    """Parameters for network testing"""
    test_type: str = Field(default="ping", pattern="^(ping|traceroute|bandwidth)$")
    target: Optional[str] = Field(default=None, max_length=255)
    count: int = Field(default=4, ge=1, le=10)


# =============================================================================
# COMMAND REQUEST SCHEMAS
# =============================================================================

class CommandRequest(BaseModel):
    """
    Request to queue a command for execution
    """
    device_id: int = Field(..., gt=0, description="Target device ID")
    command_type: CommandType = Field(..., description="Type of command to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1=highest, 10=lowest)")
    scheduled_at: Optional[datetime] = Field(default=None, description="Schedule for future execution")
    reason: Optional[str] = Field(default=None, max_length=255, description="Reason for command")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "command_type": "volume",
                "parameters": {"volume": 50},
                "priority": 5,
                "reason": "Adjust for presentation"
            }
        }


class BatchCommandRequest(BaseModel):
    """
    Request to execute command on multiple devices
    """
    device_ids: List[int] = Field(..., min_length=1, max_length=100, description="Target device IDs")
    command_type: CommandType = Field(..., description="Type of command to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    execution_mode: ExecutionMode = Field(default=ExecutionMode.PARALLEL, description="Execution mode")
    priority: int = Field(default=5, ge=1, le=10, description="Priority")
    reason: Optional[str] = Field(default=None, max_length=255, description="Reason for batch command")

    @field_validator('device_ids')
    @classmethod
    def validate_device_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one device ID required')
        if len(v) > 100:
            raise ValueError('Maximum 100 devices per batch')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate device IDs not allowed')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "device_ids": [1, 2, 3],
                "command_type": "volume",
                "parameters": {"volume": 30},
                "execution_mode": "parallel",
                "priority": 5,
                "reason": "Evening mode - reduce volume"
            }
        }


class CommandCancelRequest(BaseModel):
    """Request to cancel a pending command"""
    reason: Optional[str] = Field(default=None, max_length=255, description="Cancellation reason")


class CommandRetryRequest(BaseModel):
    """Request to retry a failed command"""
    reset_parameters: bool = Field(default=False, description="Reset to original parameters")
    new_parameters: Optional[Dict[str, Any]] = Field(default=None, description="New parameters")


# =============================================================================
# COMMAND RESPONSE SCHEMAS
# =============================================================================

class CommandExecutionResult(BaseModel):
    """Result from command execution"""
    success: bool = Field(..., description="Whether command succeeded")
    output: Optional[str] = Field(default=None, description="Command output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    exit_code: Optional[int] = Field(default=None, description="Exit code for shell commands")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CommandResponse(BaseModel):
    """Response for a single command"""
    id: int
    device_id: int
    device_name: Optional[str] = None
    command_type: str
    parameters: Dict[str, Any]
    status: str
    priority: int
    risk_level: str
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_by: Optional[int] = None
    created_by_username: Optional[str] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_id": 1,
                "device_name": "Lobby TV",
                "command_type": "volume",
                "parameters": {"volume": 50},
                "status": "completed",
                "priority": 5,
                "risk_level": "low",
                "created_at": "2025-10-28T10:00:00Z",
                "completed_at": "2025-10-28T10:00:05Z",
                "result": {"success": True, "previous_volume": 70, "new_volume": 50},
                "created_by": 1,
                "created_by_username": "admin",
                "reason": "Adjust for presentation"
            }
        }


class BatchCommandResponse(BaseModel):
    """Response for batch command execution"""
    batch_id: str = Field(..., description="Unique batch identifier")
    total: int = Field(..., description="Total devices in batch")
    successful: int = Field(..., description="Successfully queued commands")
    failed: int = Field(..., description="Failed to queue commands")
    results: List[Dict[str, Any]] = Field(..., description="Individual results")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch-123e4567",
                "total": 3,
                "successful": 2,
                "failed": 1,
                "results": [
                    {"device_id": 1, "success": True, "command_id": 101},
                    {"device_id": 2, "success": True, "command_id": 102},
                    {"device_id": 3, "success": False, "error": "Device offline"}
                ]
            }
        }


class CommandListResponse(BaseModel):
    """Response for list of commands"""
    commands: List[CommandResponse]
    total: int
    pending: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "commands": [],
                "total": 10,
                "pending": 2,
                "running": 1,
                "completed": 6,
                "failed": 1
            }
        }


# =============================================================================
# COMMAND PERMISSIONS
# =============================================================================

class CommandPermission(BaseModel):
    """Command permission definition"""
    command_type: CommandType
    requires_2fa: bool = Field(default=False, description="Requires 2FA verification")
    requires_approval: bool = Field(default=False, description="Requires approval workflow")
    allowed_roles: List[str] = Field(default=["admin"], description="Roles allowed to execute")


class CommandPermissionResponse(BaseModel):
    """Response for command permissions"""
    command_type: str
    allowed: bool
    reason: Optional[str] = None
    requires_2fa: bool = False
    requires_approval: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "command_type": "shell",
                "allowed": False,
                "reason": "Insufficient permissions - requires admin role",
                "requires_2fa": True,
                "requires_approval": True
            }
        }


# =============================================================================
# AUDIT LOG
# =============================================================================

class CommandAuditLog(BaseModel):
    """Audit log entry for command execution"""
    id: int
    command_id: int
    event_type: str  # created, sent, executed, failed, cancelled
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    class Config:
        from_attributes = True


class CommandAuditLogResponse(BaseModel):
    """Response for audit log listing"""
    logs: List[CommandAuditLog]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "logs": [],
                "total": 50
            }
        }


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimitInfo(BaseModel):
    """Rate limit information"""
    command_type: str
    device_id: int
    limit: int = Field(..., description="Requests per minute allowed")
    remaining: int = Field(..., description="Remaining requests in window")
    reset_at: datetime = Field(..., description="When the limit resets")

    class Config:
        json_schema_extra = {
            "example": {
                "command_type": "shell",
                "device_id": 1,
                "limit": 1,
                "remaining": 0,
                "reset_at": "2025-10-28T10:05:00Z"
            }
        }
