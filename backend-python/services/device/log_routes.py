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
from shared.responses import success_response
from shared.errors import NotFoundError
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
    recorded_at: datetime

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
            stack_trace, user_agent, url, recorded_at
        )
        VALUES (
            :device_id, :organization_id, :log_level, :message, :source,
            :stack_trace, :user_agent, :url, NOW()
        )
        RETURNING id, device_id, log_level, message, source,
                  stack_trace, user_agent, url, recorded_at
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
        recorded_at=result.recorded_at)


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
               stack_trace, user_agent, url, recorded_at
        FROM device_logs
        {where_clause}
        ORDER BY recorded_at DESC
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
            recorded_at=row.recorded_at))

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
               stack_trace, user_agent, url, recorded_at
        FROM device_logs
        WHERE device_id = :device_id
        ORDER BY recorded_at DESC
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
            recorded_at=row.recorded_at))

    return LogListResponse(total=len(logs), items=logs)


@router.get("/devices/{device_id}/test-endpoint")
def test_endpoint(device_id: int):
    """Simple test endpoint to verify routing works"""
    return {"message": f"Test endpoint works for device {device_id}", "success": True}


# ============================================================================
# CONNECTION LOG ENDPOINTS
# ============================================================================

class ConnectionLogEntryDTO(BaseModel):
    """Single connection log entry from player"""
    logged_at: datetime = Field(..., description="Timestamp when event occurred on player device")
    event_type: str = Field(..., description="Type of event: network, server, speed_test")
    status: str = Field(..., max_length=20, description="Event status")
    latency_ms: Optional[int] = Field(None, ge=0, description="Network latency in milliseconds")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error details if failed")
    download_speed_mbps: Optional[float] = Field(None, ge=0, description="Download speed in Mbps")
    upload_speed_mbps: Optional[float] = Field(None, ge=0, description="Upload speed in Mbps")
    metadata: Optional[dict] = Field(default={}, description="Additional metadata")

class SaveConnectionLogsDTO(BaseModel):
    """Batch connection logs from player - sent every 5 minutes"""
    logs: List[ConnectionLogEntryDTO] = Field(..., min_items=1, max_items=100, description="Connection log entries")

@router.post("/devices/{device_id}/connection-logs", status_code=status.HTTP_201_CREATED)
def save_connection_logs(
    device_id: int,
    dto: SaveConnectionLogsDTO,
    db: Session = Depends(get_db)
):
    """
    Save batch of connection logs from player device

    Player automatically sends logs every 5 minutes containing:
    - Network status changes (online/offline)
    - Server connectivity (connected/disconnected)
    - Speed test results (hourly)

    This endpoint is called by the player device after activation.
    No JWT auth required - device_id verification is sufficient.

    Request body format:
    ```json
    {
      "logs": [
        {
          "logged_at": "2025-01-15T10:30:00Z",
          "event_type": "network",
          "status": "online",
          "latency_ms": 45,
          "error_message": null,
          "download_speed_mbps": null,
          "upload_speed_mbps": null,
          "metadata": {}
        }
      ]
    }
    ```
    """
    from services.device.use_cases.save_connection_logs import SaveConnectionLogs

    try:
        use_case = SaveConnectionLogs(db)
        result = use_case.execute(device_id=device_id, dto=dto)

        return success_response(
            data=result,
            message=f"Successfully saved {result['count']} connection logs"
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
