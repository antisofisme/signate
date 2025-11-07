"""
Device Log API Routes
Remote debugging system for devices

Devices send console logs to backend for remote debugging.
Helps diagnose viewer issues without physical access.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.database import get_db
from datetime import datetime
from typing import Optional, List

router = APIRouter()


# ============================================================================
# DTOs (Request/Response Models)
# ============================================================================

from pydantic import BaseModel, Field

class CreateLogRequest(BaseModel):
    """Request to create device log (called by player)"""
    device_id: int
    log_level: str = Field(..., description="Log level: log, info, warn, error, debug")
    message: str = Field(..., description="Log message")
    source: Optional[str] = Field(None, description="Source file/function")
    stack_trace: Optional[str] = Field(None, description="Error stack trace")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    url: Optional[str] = Field(None, description="Current page URL")

class LogResponse(BaseModel):
    """Single log entry response"""
    id: int
    device_id: int
    log_level: str
    message: str
    source: Optional[str]
    stack_trace: Optional[str]
    user_agent: Optional[str]
    url: Optional[str]
    timestamp: datetime

class LogListResponse(BaseModel):
    """List of logs response"""
    total: int
    items: List[LogResponse]


# ============================================================================
# LOG ENDPOINTS
# ============================================================================

@router.post("/devices/{device_id}/logs", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
def create_device_log(
    device_id: int,
    request: CreateLogRequest,
    db: Session = Depends(get_db)
):
    """
    Create device log entry (called by player)

    Devices send console logs to backend for remote debugging.
    No authentication required (device sends with device_id).
    """
    # Validate log level
    valid_levels = ['log', 'info', 'warn', 'error', 'debug']
    if request.log_level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log_level. Must be one of: {', '.join(valid_levels)}"
        )

    # Check device exists and get organization_id
    device_check = db.execute(
        text("SELECT id, organization_id FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Insert log
    query = text("""
        INSERT INTO device_logs (
            device_id, organization_id, log_level, message, source,
            stack_trace, user_agent, url, timestamp
        )
        VALUES (
            :device_id, :organization_id, :log_level, :message, :source,
            :stack_trace, :user_agent, :url, NOW()
        )
        RETURNING id, device_id, log_level, message, source,
                  stack_trace, user_agent, url, timestamp
    """)

    result = db.execute(query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "log_level": request.log_level,
        "message": request.message,
        "source": request.source,
        "stack_trace": request.stack_trace,
        "user_agent": request.user_agent,
        "url": request.url
    }).fetchone()

    db.commit()

    return LogResponse(
        id=result.id,
        device_id=result.device_id,
        log_level=result.log_level,
        message=result.message,
        source=result.source,
        stack_trace=result.stack_trace,
        user_agent=result.user_agent,
        url=result.url,
        timestamp=result.timestamp
    )


@router.get("/devices/{device_id}/logs", response_model=LogListResponse)
def get_device_logs(
    device_id: int,
    log_level: Optional[str] = Query(None, description="Filter by log level: log, info, warn, error, debug"),
    limit: int = Query(100, ge=1, le=500, description="Number of logs to return"),
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    db: Session = Depends(get_db)
):
    """
    Get device logs (called by CMS)

    Returns paginated list of device logs with optional level filter.
    Sorted by timestamp DESC (newest first).
    """
    # Build query
    where_clause = "WHERE device_id = :device_id"
    params = {"device_id": device_id, "limit": limit, "skip": skip}

    if log_level:
        where_clause += " AND log_level = :log_level"
        params["log_level"] = log_level

    # Get total count
    count_query = text(f"SELECT COUNT(*) as total FROM device_logs {where_clause}")
    total = db.execute(count_query, params).fetchone().total

    # Get logs
    query = text(f"""
        SELECT id, device_id, log_level, message, source,
               stack_trace, user_agent, url, timestamp
        FROM device_logs
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :skip
    """)

    results = db.execute(query, params).fetchall()

    logs = []
    for row in results:
        logs.append(LogResponse(
            id=row.id,
            device_id=row.device_id,
            log_level=row.log_level,
            message=row.message,
            source=row.source,
            stack_trace=row.stack_trace,
            user_agent=row.user_agent,
            url=row.url,
            timestamp=row.timestamp
        ))

    return LogListResponse(total=total, items=logs)


@router.delete("/devices/{device_id}/logs", status_code=status.HTTP_204_NO_CONTENT)
def clear_device_logs(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Clear all logs for device (called by CMS)

    Permanently deletes all log entries for the specified device.
    """
    query = text("""
        DELETE FROM device_logs
        WHERE device_id = :device_id
    """)

    db.execute(query, {"device_id": device_id})
    db.commit()

    return None


@router.get("/devices/{device_id}/logs/latest", response_model=LogListResponse)
def get_latest_device_logs(
    device_id: int,
    count: int = Query(20, ge=1, le=100, description="Number of latest logs to return"),
    db: Session = Depends(get_db)
):
    """
    Get latest N logs for device (called by CMS)

    Convenience endpoint to quickly get recent logs.
    """
    query = text("""
        SELECT id, device_id, log_level, message, source,
               stack_trace, user_agent, url, timestamp
        FROM device_logs
        WHERE device_id = :device_id
        ORDER BY timestamp DESC
        LIMIT :count
    """)

    results = db.execute(query, {"device_id": device_id, "count": count}).fetchall()

    logs = []
    for row in results:
        logs.append(LogResponse(
            id=row.id,
            device_id=row.device_id,
            log_level=row.log_level,
            message=row.message,
            source=row.source,
            stack_trace=row.stack_trace,
            user_agent=row.user_agent,
            url=row.url,
            timestamp=row.timestamp
        ))

    return LogListResponse(total=len(logs), items=logs)
