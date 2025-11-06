"""
Command API Endpoints
Secure remote device command execution with comprehensive validation and audit logging
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
import math

from app.core.database import get_db
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException, ValidationException
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response, paginated_response
from app.schemas.command import (
    CommandRequest,
    CommandResponse,
    CommandListResponse,
    BatchCommandRequest,
    BatchCommandResponse,
    CommandCancelRequest,
    CommandRetryRequest,
    CommandPermissionResponse,
    RateLimitInfo,
    CommandType
)
from app.services.command_service import CommandService, ALLOWED_COMMANDS

# Create structured logger
logger = StructuredLogger(__name__)

router = APIRouter(prefix="/api/commands", tags=["Device Commands"])


# =============================================================================
# DEPENDENCY: Get Current User
# =============================================================================

async def get_current_user_id(request: Request) -> int:
    """
    Get current user ID from request
    TODO: Implement actual JWT authentication
    """
    # Placeholder - in production, decode JWT token
    # For now, return admin user ID
    return 1


async def get_client_info(request: Request) -> tuple[str, str]:
    """Get client IP and user agent"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


# =============================================================================
# COMMAND EXECUTION
# =============================================================================

@router.post("/execute", status_code=status.HTTP_201_CREATED)
async def execute_command(
    cmd_request: CommandRequest,
    current_request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Execute a command on a single device

    Security features:
    - Command type validation (whitelist)
    - User permission checking (role-based)
    - Rate limiting (per device per command type)
    - 2FA verification (for critical commands)
    - Dangerous pattern blocking (shell commands)
    - Comprehensive audit logging

    **Rate Limits:**
    - Volume/Brightness: 10/minute
    - Screenshot: 5/minute
    - Reboot: 3/minute
    - Shell: 1/minute (requires 2FA)

    **Risk Levels:**
    - LOW: volume, brightness, screenshot
    - MEDIUM: reboot, clear_cache
    - HIGH: update
    - CRITICAL: shell (requires 2FA + approval)
    """
    request_id = get_request_id(current_request)
    service = CommandService(db)
    ip_address, user_agent = await get_client_info(current_request)

    logger.info(
        "Executing command on device",
        request_id=request_id,
        device_id=cmd_request.device_id,
        command_type=cmd_request.command_type.value,
        user_id=user_id,
        risk_level=ALLOWED_COMMANDS.get(cmd_request.command_type, {}).get('risk', 'UNKNOWN')
    )

    try:
        result = await service.queue_command(
            request=cmd_request,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(
            "Command queued successfully",
            request_id=request_id,
            command_id=result.id,
            device_id=result.device_id,
            command_type=result.command_type,
            status=result.status
        )

        return success_response(
            data=result.model_dump(),
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to queue command",
            request_id=request_id,
            device_id=cmd_request.device_id,
            command_type=cmd_request.command_type.value,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue command: {str(e)}"
        )


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def execute_batch_command(
    batch_request: BatchCommandRequest,
    current_request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Execute a command on multiple devices (batch operation)

    **Execution Modes:**
    - `parallel`: Execute on all devices simultaneously (default)
    - `sequential`: Execute one by one with 1s delay between

    **Limits:**
    - Maximum 100 devices per batch
    - Same rate limits apply per device
    - Partial success possible (some devices may fail)

    **Use Cases:**
    - Adjust volume on all lobby displays
    - Reboot all devices in maintenance window
    - Clear cache on specific device group
    """
    request_id = get_request_id(current_request)
    service = CommandService(db)
    ip_address, user_agent = await get_client_info(current_request)

    logger.info(
        "Executing batch command",
        request_id=request_id,
        device_count=len(batch_request.device_ids),
        command_type=batch_request.command_type.value,
        execution_mode=batch_request.execution_mode.value,
        user_id=user_id
    )

    try:
        result = await service.batch_command(
            request=batch_request,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(
            "Batch command executed",
            request_id=request_id,
            batch_id=result.batch_id,
            total=result.total,
            successful=result.successful,
            failed=result.failed
        )

        return success_response(
            data=result.model_dump(),
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to execute batch command",
            request_id=request_id,
            device_count=len(batch_request.device_ids),
            command_type=batch_request.command_type.value,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute batch command: {str(e)}"
        )


# =============================================================================
# COMMAND STATUS & MANAGEMENT
# =============================================================================

@router.get("/{command_id}")
async def get_command_status(
    command_id: int,
    current_request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get status and details of a specific command

    **Status Values:**
    - `pending`: Queued, waiting to be sent to device
    - `sent`: Sent to device via WebSocket
    - `running`: Device is currently executing
    - `completed`: Successfully executed
    - `failed`: Execution failed
    - `cancelled`: Cancelled by admin
    - `expired`: Expired before execution
    """
    request_id = get_request_id(current_request)
    service = CommandService(db)

    logger.info(
        "Fetching command status",
        request_id=request_id,
        command_id=command_id,
        user_id=user_id
    )

    result = await service.get_command(command_id)

    if not result:
        logger.warning(
            "Command not found",
            request_id=request_id,
            command_id=command_id
        )
        raise NotFoundException(
            message=f"Command {command_id} not found",
            resource_type="command",
            resource_id=command_id
        )

    logger.info(
        "Command status retrieved",
        request_id=request_id,
        command_id=command_id,
        status=result.status,
        device_id=result.device_id
    )

    return success_response(
        data=result.model_dump(),
        request_id=request_id
    )


@router.get("/")
async def list_commands(
    current_request: Request,
    device_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    List commands with optional filters and pagination

    **Filters:**
    - `device_id`: Filter by specific device
    - `status`: Filter by status (pending, completed, failed, etc.)
    - `page`: Page number (1-indexed, default: 1)
    - `limit`: Items per page (default: 100, max: 1000)

    **Response includes:**
    - Total command count
    - Status breakdown (pending, running, completed, failed)
    - Paginated command list with page metadata
    """
    request_id = get_request_id(current_request)

    # Validate pagination parameters
    if page < 1:
        raise BadRequestException("Page must be >= 1")
    if limit < 1 or limit > 1000:
        raise BadRequestException("Limit must be between 1 and 1000")

    # Convert page to offset
    offset = (page - 1) * limit

    logger.info(
        "Listing commands",
        request_id=request_id,
        device_id=device_id,
        status_filter=status,
        page=page,
        limit=limit,
        user_id=user_id
    )

    service = CommandService(db)

    result = await service.list_commands(
        device_id=device_id,
        status=status,
        limit=limit,
        offset=offset
    )

    logger.info(
        "Commands listed successfully",
        request_id=request_id,
        total=result.total,
        page=page,
        returned=len(result.commands)
    )

    # Calculate total pages
    total_pages = math.ceil(result.total / limit) if limit > 0 else 0

    # Return paginated response with status breakdown
    return success_response(
        data={
            "items": [cmd.model_dump() for cmd in result.commands],
            "status_breakdown": {
                "pending": result.pending,
                "running": result.running,
                "completed": result.completed,
                "failed": result.failed
            }
        },
        request_id=request_id,
        total=result.total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )


@router.get("/device/{device_id}")
async def get_device_commands(
    device_id: int,
    current_request: Request,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get all commands for a specific device with pagination

    Useful for:
    - Device command history
    - Troubleshooting command failures
    - Monitoring device command queue

    **Parameters:**
    - `device_id`: Target device ID
    - `status`: Filter by status (optional)
    - `page`: Page number (1-indexed, default: 1)
    - `limit`: Items per page (default: 100, max: 1000)
    """
    request_id = get_request_id(current_request)

    # Validate pagination parameters
    if page < 1:
        raise BadRequestException("Page must be >= 1")
    if limit < 1 or limit > 1000:
        raise BadRequestException("Limit must be between 1 and 1000")

    # Convert page to offset
    offset = (page - 1) * limit

    logger.info(
        "Fetching device commands",
        request_id=request_id,
        device_id=device_id,
        status_filter=status,
        page=page,
        limit=limit,
        user_id=user_id
    )

    service = CommandService(db)

    result = await service.list_commands(
        device_id=device_id,
        status=status,
        limit=limit,
        offset=offset
    )

    logger.info(
        "Device commands retrieved",
        request_id=request_id,
        device_id=device_id,
        total=result.total,
        returned=len(result.commands)
    )

    # Calculate total pages
    total_pages = math.ceil(result.total / limit) if limit > 0 else 0

    return success_response(
        data={
            "items": [cmd.model_dump() for cmd in result.commands],
            "status_breakdown": {
                "pending": result.pending,
                "running": result.running,
                "completed": result.completed,
                "failed": result.failed
            }
        },
        request_id=request_id,
        total=result.total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )


# =============================================================================
# COMMAND ACTIONS
# =============================================================================

@router.delete("/{command_id}")
async def cancel_command(
    command_id: int,
    cancel_request: CommandCancelRequest,
    current_request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Cancel a pending or sent command

    **Requirements:**
    - Command must be in `pending` or `sent` status
    - Cannot cancel running, completed, or failed commands

    **Use Cases:**
    - Cancel accidental command
    - Stop command before device executes
    - Change command parameters (cancel + re-queue)
    """
    request_id = get_request_id(current_request)
    service = CommandService(db)

    logger.info(
        "Cancelling command",
        request_id=request_id,
        command_id=command_id,
        user_id=user_id,
        reason=cancel_request.reason
    )

    try:
        result = await service.cancel_command(
            command_id=command_id,
            user_id=user_id,
            reason=cancel_request.reason
        )

        logger.info(
            "Command cancelled successfully",
            request_id=request_id,
            command_id=command_id,
            device_id=result.device_id
        )

        return success_response(
            data=result.model_dump(),
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to cancel command",
            request_id=request_id,
            command_id=command_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel command: {str(e)}"
        )


@router.post("/{command_id}/retry")
async def retry_command(
    command_id: int,
    retry_request: CommandRetryRequest,
    current_request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Retry a failed command

    **Requirements:**
    - Command must be in `failed` status
    - Same rate limits apply

    **Options:**
    - `reset_parameters`: Use original parameters
    - `new_parameters`: Provide new parameters (not implemented yet)

    **Use Cases:**
    - Retry after temporary device offline
    - Retry after network issue
    - Retry with different parameters
    """
    request_id = get_request_id(current_request)
    service = CommandService(db)

    logger.info(
        "Retrying command",
        request_id=request_id,
        command_id=command_id,
        user_id=user_id,
        reset_parameters=retry_request.reset_parameters
    )

    try:
        result = await service.retry_command(
            command_id=command_id,
            user_id=user_id
        )

        logger.info(
            "Command retry initiated",
            request_id=request_id,
            command_id=command_id,
            new_command_id=result.id,
            device_id=result.device_id
        )

        return success_response(
            data=result.model_dump(),
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retry command",
            request_id=request_id,
            command_id=command_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry command: {str(e)}"
        )


# =============================================================================
# COMMAND INFORMATION
# =============================================================================

@router.get("/available/list")
async def list_available_commands(
    current_request: Request,
    user_id: int = Depends(get_current_user_id)
):
    """
    Get list of available commands with their configurations

    **Returns:**
    - Command types
    - Risk levels
    - Rate limits
    - Timeout values
    - Required permissions
    - 2FA requirements

    **Risk Levels:**
    - LOW: Safe commands (volume, brightness)
    - MEDIUM: System commands (reboot, cache clear)
    - HIGH: Update commands
    - CRITICAL: Shell access (requires 2FA)
    """
    request_id = get_request_id(current_request)

    logger.info(
        "Listing available commands",
        request_id=request_id,
        user_id=user_id
    )

    commands = []

    for cmd_type, config in ALLOWED_COMMANDS.items():
        commands.append({
            'command_type': cmd_type.value,
            'risk_level': config['risk'].value,
            'rate_limit': config['rate_limit'],
            'timeout': config['timeout'],
            'requires_2fa': config['requires_2fa'],
            'requires_approval': config['requires_approval'],
            'allowed_roles': config['allowed_roles'],
            'audit_enabled': config['audit']
        })

    logger.info(
        "Available commands listed",
        request_id=request_id,
        total_commands=len(commands)
    )

    return success_response(
        data={
            'commands': commands,
            'total': len(commands)
        },
        request_id=request_id
    )


@router.get("/permissions/{command_type}")
async def check_command_permission(
    command_type: str,
    current_request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Check if current user has permission to execute a command

    **Checks:**
    - User role vs required roles
    - 2FA status (if required)
    - Approval workflow (if required)

    **Returns:**
    - `allowed`: Whether user can execute command
    - `reason`: Explanation if not allowed
    - `requires_2fa`: Whether 2FA is needed
    - `requires_approval`: Whether approval is needed
    """
    request_id = get_request_id(current_request)

    logger.info(
        "Checking command permission",
        request_id=request_id,
        command_type=command_type,
        user_id=user_id
    )

    try:
        cmd_enum = CommandType(command_type)
    except ValueError:
        logger.warning(
            "Invalid command type requested",
            request_id=request_id,
            command_type=command_type
        )
        raise NotFoundException(
            message=f"Command type '{command_type}' not found",
            resource_type="command_type",
            resource_id=command_type
        )

    config = ALLOWED_COMMANDS.get(cmd_enum)

    if not config:
        logger.warning(
            "Command not whitelisted",
            request_id=request_id,
            command_type=command_type
        )
        return success_response(
            data={
                "command_type": command_type,
                "allowed": False,
                "reason": "Command not whitelisted",
                "requires_2fa": False,
                "requires_approval": False
            },
            request_id=request_id
        )

    # Check user role (simplified - in production, check actual user)
    # For now, assume admin role
    user_role = "admin"

    allowed = user_role in config['allowed_roles']
    reason = None if allowed else f"Requires one of: {', '.join(config['allowed_roles'])}"

    logger.info(
        "Permission check completed",
        request_id=request_id,
        command_type=command_type,
        allowed=allowed,
        user_role=user_role
    )

    return success_response(
        data={
            "command_type": command_type,
            "allowed": allowed,
            "reason": reason,
            "requires_2fa": config['requires_2fa'],
            "requires_approval": config['requires_approval']
        },
        request_id=request_id
    )


@router.get("/rate-limit/{device_id}/{command_type}")
async def get_rate_limit_info(
    device_id: int,
    command_type: str,
    current_request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get rate limit information for a device and command type

    **Returns:**
    - Current limit (requests per minute)
    - Remaining requests in current window
    - When the limit resets

    **Use Cases:**
    - Check before batch operations
    - Display to user in UI
    - Implement client-side throttling
    """
    request_id = get_request_id(current_request)

    logger.info(
        "Fetching rate limit info",
        request_id=request_id,
        device_id=device_id,
        command_type=command_type,
        user_id=user_id
    )

    try:
        cmd_enum = CommandType(command_type)
    except ValueError:
        logger.warning(
            "Invalid command type for rate limit check",
            request_id=request_id,
            command_type=command_type
        )
        raise NotFoundException(
            message=f"Command type '{command_type}' not found",
            resource_type="command_type",
            resource_id=command_type
        )

    config = ALLOWED_COMMANDS.get(cmd_enum)

    if not config:
        raise NotFoundException(
            message="Command not found",
            resource_type="command",
            resource_id=command_type
        )

    service = CommandService(db)
    remaining = await service.rate_limiter.get_remaining(device_id, command_type)

    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    reset_at = now + timedelta(minutes=1)

    logger.info(
        "Rate limit info retrieved",
        request_id=request_id,
        device_id=device_id,
        command_type=command_type,
        remaining=remaining,
        limit=config['rate_limit']
    )

    return success_response(
        data={
            "command_type": command_type,
            "device_id": device_id,
            "limit": config['rate_limit'],
            "remaining": remaining,
            "reset_at": reset_at.isoformat()
        },
        request_id=request_id
    )


# =============================================================================
# INTERNAL ENDPOINTS (Called by Device)
# =============================================================================

@router.post("/{command_id}/execute")
async def mark_command_executed(
    command_id: int,
    current_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark command as executed (called by device after successful execution)

    **Internal Endpoint** - Called by device viewer, not web admin

    Updates:
    - Status to `completed`
    - Execution timestamp
    - Creates audit log entry
    """
    request_id = get_request_id(current_request)
    service = CommandService(db)

    logger.info(
        "Device marking command as executed",
        request_id=request_id,
        command_id=command_id
    )

    try:
        result = await service.execute_command(command_id)

        logger.info(
            "Command marked as executed",
            request_id=request_id,
            command_id=command_id,
            device_id=result.device_id
        )

        return success_response(
            data=result.model_dump(),
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to mark command as executed",
            request_id=request_id,
            command_id=command_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark command as executed: {str(e)}"
        )


@router.post("/{command_id}/fail")
async def mark_command_failed(
    command_id: int,
    error_message: str,
    current_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark command as failed (called by device if execution fails)

    **Internal Endpoint** - Called by device viewer, not web admin

    Updates:
    - Status to `failed`
    - Error message
    - Creates audit log entry
    """
    request_id = get_request_id(current_request)
    service = CommandService(db)

    logger.info(
        "Device marking command as failed",
        request_id=request_id,
        command_id=command_id,
        error_message=error_message[:100]  # Truncate for logging
    )

    try:
        result = await service.fail_command(command_id, error_message)

        logger.warning(
            "Command marked as failed",
            request_id=request_id,
            command_id=command_id,
            device_id=result.device_id,
            error=error_message[:100]
        )

        return success_response(
            data=result.model_dump(),
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to mark command as failed",
            request_id=request_id,
            command_id=command_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark command as failed: {str(e)}"
        )


# =============================================================================
# CLEANUP (Background Task)
# =============================================================================

@router.post("/cleanup/expired")
async def cleanup_expired_commands(
    current_request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Clean up expired commands (admin only)

    **Background Task** - Should be called by scheduler

    Actions:
    - Mark expired pending commands as `expired`
    - Commands expire after 24 hours

    **Returns:**
    - Number of commands marked as expired
    """
    request_id = get_request_id(current_request)
    service = CommandService(db)

    logger.info(
        "Starting command cleanup",
        request_id=request_id,
        user_id=user_id
    )

    try:
        count = await service.cleanup_expired_commands()

        logger.info(
            "Command cleanup completed",
            request_id=request_id,
            expired_count=count
        )

        return success_response(
            data={
                'expired_count': count,
                'message': f'Marked {count} commands as expired'
            },
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to cleanup commands",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup commands: {str(e)}"
        )
