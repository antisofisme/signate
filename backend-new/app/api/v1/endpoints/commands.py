"""
Device Commands API Endpoints
==============================

Remote device command execution and management.

Clean Architecture: API → Service → Repository → Database
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.core.logging import StructuredLogger
from app.middleware.request_id import get_request_id
from app.services.command_service import CommandService
from app.schemas.command import (
    CommandExecute,
    BatchCommandExecute,
    CommandResponse,
    BatchCommandResponse,
    CommandListResponse,
    CommandStatusUpdate
)
from app.models.user import User

logger = StructuredLogger(__name__)
router = APIRouter()


@router.post(
    "/execute",
    response_model=CommandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Command",
    description="Queue a command for execution on a device"
)
async def execute_command(
    command_data: CommandExecute,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute a command on a single device.

    **Command Types**:
    - `reset`: Force device to reset (clear localStorage + cache)
    - `refresh`: Refresh content cache only
    - `reload`: Reload player only

    **Flow**:
    1. Validate device exists
    2. Validate command type
    3. Queue command with expiration
    4. Return command details

    **Expiration**: Commands expire after specified time (default: 60 minutes)
    """
    request_id = get_request_id(request)

    logger.info(
        "Executing command on device",
        request_id=request_id,
        device_id=command_data.device_id,
        command_type=command_data.command_type,
        user_id=current_user.id,
        reason=command_data.reason
    )

    service = CommandService(db)
    command = service.execute_command(
        device_id=command_data.device_id,
        command_type=command_data.command_type,
        reason=command_data.reason,
        expires_in_minutes=command_data.expires_in_minutes
    )

    logger.info(
        "Command queued successfully",
        request_id=request_id,
        command_id=command.id,
        device_id=command.device_id,
        expires_at=command.expires_at.isoformat()
    )

    return command.to_dict()


@router.post(
    "/batch",
    response_model=BatchCommandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Batch Command",
    description="Queue a command for execution on multiple devices"
)
async def execute_batch_command(
    batch_data: BatchCommandExecute,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute a command on multiple devices (batch operation).

    **Limits**:
    - Maximum 100 devices per batch
    - Partial success possible (some devices may fail)

    **Use Cases**:
    - Reset all devices in a location
    - Refresh content on multiple displays
    - Reload players after content update
    """
    request_id = get_request_id(request)

    logger.info(
        "Executing batch command",
        request_id=request_id,
        device_count=len(batch_data.device_ids),
        command_type=batch_data.command_type,
        user_id=current_user.id
    )

    service = CommandService(db)
    result = service.batch_execute_command(
        device_ids=batch_data.device_ids,
        command_type=batch_data.command_type,
        reason=batch_data.reason,
        expires_in_minutes=batch_data.expires_in_minutes
    )

    logger.info(
        "Batch command executed",
        request_id=request_id,
        total=result["total"],
        successful=result["successful"],
        failed=result["failed"]
    )

    # Convert command objects to dicts
    commands_dict = [cmd.to_dict() for cmd in result["commands"]]

    return {
        "total": result["total"],
        "successful": result["successful"],
        "failed": result["failed"],
        "commands": commands_dict,
        "errors": result["errors"]
    }


@router.get(
    "/{command_id}",
    response_model=CommandResponse,
    summary="Get Command Status",
    description="Get status and details of a specific command"
)
async def get_command(
    command_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get command status and details.

    **Status Values**:
    - `pending`: Queued, waiting for device to execute
    - `executed`: Device executed successfully
    - `expired`: Command expired (not executed within timeout)
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching command status",
        request_id=request_id,
        command_id=command_id,
        user_id=current_user.id
    )

    service = CommandService(db)
    command = service.get_command(command_id)

    logger.info(
        "Command status retrieved",
        request_id=request_id,
        command_id=command_id,
        status=command.status,
        device_id=command.device_id
    )

    return command.to_dict()


@router.get(
    "/",
    response_model=CommandListResponse,
    summary="List Commands",
    description="List commands with optional filters and pagination"
)
async def list_commands(
    request: Request,
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending, executed, expired)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results (max: 100)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List commands with optional filters.

    **Filters**:
    - `device_id`: Show commands for specific device
    - `status`: Filter by command status
    - Pagination with skip/limit

    **Returns**:
    - Paginated command list
    - Status counts (pending, executed, expired)
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing commands",
        request_id=request_id,
        device_id=device_id,
        status_filter=status,
        skip=skip,
        limit=limit,
        user_id=current_user.id
    )

    service = CommandService(db)
    result = service.list_commands(
        device_id=device_id,
        status=status,
        skip=skip,
        limit=limit
    )

    logger.info(
        "Commands listed",
        request_id=request_id,
        total=result["total"],
        returned=len(result["commands"])
    )

    # Convert commands to dicts
    commands_dict = [cmd.to_dict() for cmd in result["commands"]]

    return {
        "commands": commands_dict,
        "total": result["total"],
        "skip": result["skip"],
        "limit": result["limit"],
        "status_counts": result["status_counts"]
    }


@router.get(
    "/device/{device_id}",
    response_model=CommandListResponse,
    summary="Get Device Commands",
    description="Get all commands for a specific device"
)
async def get_device_commands(
    device_id: int,
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get command history for a specific device.

    Useful for:
    - Device troubleshooting
    - Command audit trail
    - Monitoring command queue
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching device commands",
        request_id=request_id,
        device_id=device_id,
        status_filter=status,
        user_id=current_user.id
    )

    service = CommandService(db)
    result = service.list_commands(
        device_id=device_id,
        status=status,
        skip=skip,
        limit=limit
    )

    logger.info(
        "Device commands retrieved",
        request_id=request_id,
        device_id=device_id,
        total=result["total"],
        returned=len(result["commands"])
    )

    # Convert commands to dicts
    commands_dict = [cmd.to_dict() for cmd in result["commands"]]

    return {
        "commands": commands_dict,
        "total": result["total"],
        "skip": result["skip"],
        "limit": result["limit"],
        "status_counts": result["status_counts"]
    }


@router.get(
    "/device/{device_id}/pending",
    summary="Get Pending Commands",
    description="Get all pending commands for a device"
)
async def get_pending_commands(
    device_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all pending commands for a device.

    **Use Case**: Device polls this endpoint to get commands to execute
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching pending commands",
        request_id=request_id,
        device_id=device_id
    )

    service = CommandService(db)
    commands = service.get_pending_commands(device_id)

    logger.info(
        "Pending commands retrieved",
        request_id=request_id,
        device_id=device_id,
        count=len(commands)
    )

    return {
        "device_id": device_id,
        "commands": [cmd.to_dict() for cmd in commands],
        "count": len(commands)
    }


@router.post(
    "/{command_id}/executed",
    response_model=CommandResponse,
    summary="Mark Command Executed",
    description="Mark command as executed (called by device)"
)
async def mark_command_executed(
    command_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Mark command as executed (called by device after successful execution).

    **Internal Endpoint** - Called by device viewer, not web admin
    """
    request_id = get_request_id(request)

    logger.info(
        "Device marking command as executed",
        request_id=request_id,
        command_id=command_id
    )

    service = CommandService(db)
    command = service.mark_command_executed(command_id)

    logger.info(
        "Command marked as executed",
        request_id=request_id,
        command_id=command_id,
        device_id=command.device_id
    )

    return command.to_dict()


@router.delete(
    "/device/{device_id}",
    summary="Cancel Device Commands",
    description="Cancel all pending commands for a device"
)
async def cancel_device_commands(
    device_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel (expire) all pending commands for a device.

    **Use Cases**:
    - Device going offline for maintenance
    - Clearing command queue
    - Cancelling batch operation
    """
    request_id = get_request_id(request)

    logger.info(
        "Cancelling device commands",
        request_id=request_id,
        device_id=device_id,
        user_id=current_user.id
    )

    service = CommandService(db)
    count = service.cancel_device_commands(device_id)

    logger.info(
        "Device commands cancelled",
        request_id=request_id,
        device_id=device_id,
        count=count
    )

    return {
        "device_id": device_id,
        "cancelled": count,
        "message": f"Cancelled {count} pending commands"
    }


@router.post(
    "/cleanup/expired",
    summary="Expire Old Commands",
    description="Mark expired commands as expired (admin/cron only)"
)
async def expire_old_commands(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Expire all commands past their expiration date.

    **Background Task** - Should be called by scheduler
    """
    request_id = get_request_id(request)

    logger.info(
        "Expiring old commands",
        request_id=request_id,
        user_id=current_user.id
    )

    service = CommandService(db)
    count = service.expire_old_commands()

    logger.info(
        "Commands expired",
        request_id=request_id,
        count=count
    )

    return {
        "expired": count,
        "message": f"Marked {count} commands as expired"
    }


@router.get(
    "/stats/{device_id}",
    summary="Get Command Statistics",
    description="Get command statistics for a device"
)
async def get_command_stats(
    device_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get command statistics for a device.

    **Returns**:
    - Total commands
    - Count by status (pending, executed, expired)
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching command stats",
        request_id=request_id,
        device_id=device_id,
        user_id=current_user.id
    )

    service = CommandService(db)
    stats = service.get_device_command_stats(device_id)

    logger.info(
        "Command stats retrieved",
        request_id=request_id,
        device_id=device_id,
        total=stats["total"]
    )

    return stats
