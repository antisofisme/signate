"""
Device Command API Routes
Remote command queue for device management

Commands allow admins to send instructions to devices:
- reset: Clear storage and reload
- refresh: Clear cache only
- reload: Reload page
- reboot: Restart device
- screenshot: Capture screen
- volume: Set volume level
- brightness: Set brightness level
- speed_test: Run network speed test
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.database import get_db
from datetime import datetime, timedelta
from typing import Optional, List
import json

router = APIRouter()


# ============================================================================
# DTOs (Request/Response Models)
# ============================================================================

from pydantic import BaseModel, Field

class SendCommandRequest(BaseModel):
    """Request to send command to device"""
    command_type: str = Field(..., description="Type of command: reset, refresh, reload, reboot, screenshot, volume, brightness, speed_test")
    parameters: Optional[dict] = Field(None, description="Command parameters (e.g., {'level': 75} for volume)")
    reason: Optional[str] = Field(None, description="Why this command was issued")

class CommandResponse(BaseModel):
    """Single command response"""
    id: int
    device_id: int
    command_type: str
    parameters: Optional[dict]
    reason: Optional[str]
    status: str
    sent_at: Optional[datetime]
    executed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]

class CommandListResponse(BaseModel):
    """List of commands response"""
    total: int
    items: List[CommandResponse]


# ============================================================================
# COMMAND ENDPOINTS
# ============================================================================

@router.post("/devices/{device_id}/commands", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
def send_command_to_device(
    device_id: int,
    request: SendCommandRequest,
    db: Session = Depends(get_db)
):
    """
    Send command to device

    Admin queues a command that device will execute during next heartbeat.
    Command expires after 7 days if not executed.
    """
    # Validate command type
    valid_commands = ['reset', 'refresh', 'reload', 'reboot', 'screenshot', 'volume', 'brightness', 'speed_test', 'update_content']
    if request.command_type not in valid_commands:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid command_type. Must be one of: {', '.join(valid_commands)}"
        )

    # Check device exists
    device_check = db.execute(
        text("SELECT id, organization_id, status FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Create command
    query = text("""
        INSERT INTO device_commands (
            device_id, organization_id, command_type, parameters, reason,
            status, expires_at, created_at
        )
        VALUES (
            :device_id, :organization_id, :command_type, :parameters, :reason,
            'pending', :expires_at, NOW()
        )
        RETURNING id, device_id, organization_id, command_type, parameters, reason,
                  status, sent_at, executed_at, error_message, created_at, expires_at
    """)

    params_json = json.dumps(request.parameters) if request.parameters else None
    expires_at = datetime.now() + timedelta(days=7)

    result = db.execute(query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "command_type": request.command_type,
        "parameters": params_json,
        "reason": request.reason,
        "expires_at": expires_at
    }).fetchone()

    db.commit()

    # Convert to response
    return CommandResponse(
        id=result.id,
        device_id=result.device_id,
        command_type=result.command_type,
        parameters=json.loads(result.parameters) if result.parameters else None,
        reason=result.reason,
        status=result.status,
        sent_at=result.sent_at,
        executed_at=result.executed_at,
        error_message=result.error_message,
        created_at=result.created_at,
        expires_at=result.expires_at
    )


@router.get("/devices/{device_id}/commands/pending", response_model=CommandListResponse)
def get_pending_commands(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get pending commands for device (called by player)

    Device polls this endpoint during heartbeat to check for commands to execute.
    Returns only non-expired pending commands.
    """
    query = text("""
        SELECT id, device_id, command_type, parameters, reason,
               status, sent_at, executed_at, error_message, created_at, expires_at
        FROM device_commands
        WHERE device_id = :device_id
          AND status = 'pending'
          AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY created_at ASC
    """)

    results = db.execute(query, {"device_id": device_id}).fetchall()

    commands = []
    for row in results:
        commands.append(CommandResponse(
            id=row.id,
            device_id=row.device_id,
            command_type=row.command_type,
            parameters=json.loads(row.parameters) if row.parameters else None,
            reason=row.reason,
            status=row.status,
            sent_at=row.sent_at,
            executed_at=row.executed_at,
            error_message=row.error_message,
            created_at=row.created_at,
            expires_at=row.expires_at
        ))

    return CommandListResponse(total=len(commands), items=commands)


@router.post("/devices/{device_id}/commands/{command_id}/execute", status_code=status.HTTP_200_OK)
def execute_command(
    device_id: int,
    command_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark command as executed (called by player after execution)

    Device calls this after successfully executing a command.
    Updates command status to 'executed' and records execution timestamp.
    """
    # Update command status
    query = text("""
        UPDATE device_commands
        SET status = 'executed',
            executed_at = NOW(),
            sent_at = COALESCE(sent_at, NOW())
        WHERE id = :command_id
          AND device_id = :device_id
          AND status = 'pending'
        RETURNING id, command_type, executed_at
    """)

    result = db.execute(query, {
        "command_id": command_id,
        "device_id": device_id
    }).fetchone()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command {command_id} not found or already executed"
        )

    db.commit()

    return {
        "success": True,
        "message": f"Command '{result.command_type}' marked as executed",
        "command_id": result.id,
        "executed_at": result.executed_at
    }


@router.get("/devices/{device_id}/commands", response_model=CommandListResponse)
def get_device_commands(
    device_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, executed, failed, expired"),
    limit: int = Query(50, ge=1, le=200, description="Number of commands to return"),
    skip: int = Query(0, ge=0, description="Number of commands to skip"),
    db: Session = Depends(get_db)
):
    """
    Get command history for device (called by CMS)

    Returns paginated list of commands with optional status filter.
    """
    # Build query
    where_clause = "WHERE device_id = :device_id"
    params = {"device_id": device_id, "limit": limit, "skip": skip}

    if status_filter:
        where_clause += " AND status = :status"
        params["status"] = status_filter

    # Get total count
    count_query = text(f"SELECT COUNT(*) as total FROM device_commands {where_clause}")
    total = db.execute(count_query, params).fetchone().total

    # Get commands
    query = text(f"""
        SELECT id, device_id, command_type, parameters, reason,
               status, sent_at, executed_at, error_message, created_at, expires_at
        FROM device_commands
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)

    results = db.execute(query, params).fetchall()

    commands = []
    for row in results:
        commands.append(CommandResponse(
            id=row.id,
            device_id=row.device_id,
            command_type=row.command_type,
            parameters=json.loads(row.parameters) if row.parameters else None,
            reason=row.reason,
            status=row.status,
            sent_at=row.sent_at,
            executed_at=row.executed_at,
            error_message=row.error_message,
            created_at=row.created_at,
            expires_at=row.expires_at
        ))

    return CommandListResponse(total=total, items=commands)


@router.post("/devices/{device_id}/commands/reset", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
def send_reset_command(
    device_id: int,
    reason: Optional[str] = Query("manual_reset", description="Reason for reset"),
    db: Session = Depends(get_db)
):
    """
    Quick endpoint to send reset command

    Convenience endpoint for sending reset command (clear storage + reload).
    """
    request = SendCommandRequest(
        command_type="reset",
        reason=reason
    )

    return send_command_to_device(device_id, request, db)
