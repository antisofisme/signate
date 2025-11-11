"""
Device Logs API endpoints
For remote monitoring and debugging of viewer devices

Quick Wins Standards:
- StructuredLogger for consistent logging
- Custom exceptions (NotFoundException)
- Standardized response wrappers (success_response, paginated_response)
- Request ID tracking for distributed tracing
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis_client import publish_log
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException
from app.schemas.common import success_response, paginated_response
from app.middleware.request_id import get_request_id
from app.models.user import User
from app.models.device import Device
from app.models.device_log import DeviceLog

logger = StructuredLogger(__name__)
router = APIRouter()


# ========================================
# Pydantic Schemas
# ========================================

class DeviceLogCreate(BaseModel):
    """Schema for creating a device log"""
    device_id: int
    log_level: str  # 'log', 'warn', 'error', 'info'
    message: str
    source: Optional[str] = None


class DeviceLogResponse(BaseModel):
    """Schema for device log response"""
    id: int
    device_id: int
    log_level: str
    message: str
    source: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class DeviceLogBatchCreate(BaseModel):
    """Schema for batch log submission"""
    device_id: int
    logs: List[dict]  # List of {level, message, source?, timestamp?}


# ========================================
# Client Endpoints (No Authentication)
# ========================================

@router.post("/client/logs", status_code=status.HTTP_201_CREATED)
def create_device_log(
    log_data: DeviceLogCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a device log entry

    Called by viewer devices to send console logs to backend for remote monitoring.

    Args:
        log_data: Log data (device_id, log_level, message, source)
        request: FastAPI Request object (for request_id)
        db: Database session

    Returns:
        Success response with created log data

    Notes:
        - This endpoint does NOT require authentication (for viewer clients)
        - Logs are stored with timestamps for chronological viewing
        - Publishes to Redis for real-time streaming
    """
    request_id = get_request_id(request)

    logger.info(
        "Device log creation started",
        request_id=request_id,
        device_id=log_data.device_id,
        log_level=log_data.log_level
    )

    # Verify device exists
    device = db.query(Device).filter(Device.id == log_data.device_id).first()
    if not device:
        raise NotFoundException(
            message=f"Device with ID {log_data.device_id} not found",
            resource_type="Device",
            resource_id=log_data.device_id
        )

    # Create log entry
    log_entry = DeviceLog(
        device_id=log_data.device_id,
        log_level=log_data.log_level,
        message=log_data.message,
        source=log_data.source,
        timestamp=datetime.utcnow()
    )

    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    # Publish to Redis for real-time streaming
    redis_success = publish_log(log_data.device_id, {
        "id": log_entry.id,
        "device_id": log_entry.device_id,
        "log_level": log_entry.log_level,
        "message": log_entry.message,
        "source": log_entry.source,
        "timestamp": log_entry.timestamp.isoformat()
    })

    logger.info(
        "Device log created successfully",
        request_id=request_id,
        log_id=log_entry.id,
        device_id=log_data.device_id,
        log_level=log_data.log_level,
        redis_published=redis_success,
        message_preview=log_data.message[:100]
    )

    # Convert to dict for response
    log_dict = {
        "id": log_entry.id,
        "device_id": log_entry.device_id,
        "log_level": log_entry.log_level,
        "message": log_entry.message,
        "source": log_entry.source,
        "timestamp": log_entry.timestamp.isoformat()
    }

    return success_response(
        data=log_dict,
        request_id=request_id
    )


@router.post("/client/logs/batch", status_code=status.HTTP_201_CREATED)
def create_device_logs_batch(
    batch_data: DeviceLogBatchCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create multiple device log entries in one request

    Optimized for viewers to send multiple logs at once (batch submission).

    Args:
        batch_data: Batch log data (device_id, logs array)
        request: FastAPI Request object (for request_id)
        db: Database session

    Returns:
        Success response with batch creation summary

    Notes:
        - This endpoint does NOT require authentication
        - More efficient than sending logs one by one
        - Publishes each log to Redis for real-time streaming
    """
    request_id = get_request_id(request)

    logger.info(
        "Device log batch creation started",
        request_id=request_id,
        device_id=batch_data.device_id,
        logs_count=len(batch_data.logs)
    )

    # Verify device exists
    device = db.query(Device).filter(Device.id == batch_data.device_id).first()
    if not device:
        raise NotFoundException(
            message=f"Device with ID {batch_data.device_id} not found",
            resource_type="Device",
            resource_id=batch_data.device_id
        )

    # Create log entries
    log_entries = []
    for log in batch_data.logs:
        log_entry = DeviceLog(
            device_id=batch_data.device_id,
            log_level=log.get('level', 'log'),
            message=log.get('message', ''),
            source=log.get('source'),
            timestamp=datetime.fromisoformat(log['timestamp']) if 'timestamp' in log else datetime.utcnow()
        )
        log_entries.append(log_entry)

    db.add_all(log_entries)
    db.commit()

    # Refresh to get IDs
    for entry in log_entries:
        db.refresh(entry)

    # Publish each log to Redis for real-time streaming
    redis_success_count = 0
    for entry in log_entries:
        redis_success = publish_log(batch_data.device_id, {
            "id": entry.id,
            "device_id": entry.device_id,
            "log_level": entry.log_level,
            "message": entry.message,
            "source": entry.source,
            "timestamp": entry.timestamp.isoformat()
        })
        if redis_success:
            redis_success_count += 1

    logger.info(
        "Device log batch created successfully",
        request_id=request_id,
        device_id=batch_data.device_id,
        logs_created=len(log_entries),
        redis_published_count=redis_success_count
    )

    return success_response(
        data={
            "message": f"{len(log_entries)} logs created successfully",
            "logs_created": len(log_entries),
            "device_id": batch_data.device_id
        },
        request_id=request_id
    )


# ========================================
# Admin Endpoints (Requires Authentication)
# ========================================

@router.get("/devices/{device_id}/logs")
def get_device_logs(
    device_id: int,
    request: Request,
    log_level: Optional[str] = None,
    hours: Optional[int] = 24,
    limit: Optional[int] = 1000,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get logs for a specific device with filtering and pagination

    Args:
        device_id: Device ID
        request: FastAPI Request object (for request_id)
        log_level: Filter by log level (optional: log, warn, error, info)
        hours: Get logs from last N hours (default: 24)
        limit: Maximum number of logs to return (default: 1000)
        offset: Number of logs to skip for pagination (default: 0)
        db: Database session
        current_user: Authenticated user (required)

    Returns:
        Paginated list of device logs

    Raises:
        NotFoundException: If device not found

    Notes:
        - Requires JWT authentication (admin only)
        - Logs ordered by timestamp DESC (newest first)
        - Supports pagination via limit/offset
    """
    request_id = get_request_id(request)

    logger.info(
        "Device logs retrieval started",
        request_id=request_id,
        device_id=device_id,
        log_level=log_level,
        hours=hours,
        limit=limit,
        offset=offset,
        user_id=current_user.id
    )

    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
        )

    # Build query for total count
    count_query = db.query(DeviceLog).filter(DeviceLog.device_id == device_id)

    # Filter by log level
    if log_level:
        count_query = count_query.filter(DeviceLog.log_level == log_level)

    # Filter by time range
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
        count_query = count_query.filter(DeviceLog.timestamp >= since)

    # Get total count
    total_count = count_query.count()

    # Build query for data
    query = count_query.order_by(DeviceLog.timestamp.desc())

    # Apply pagination
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    logs = query.all()

    # Convert to dict list
    logs_list = [
        {
            "id": log.id,
            "device_id": log.device_id,
            "log_level": log.log_level,
            "message": log.message,
            "source": log.source,
            "timestamp": log.timestamp.isoformat()
        }
        for log in logs
    ]

    logger.info(
        "Device logs retrieved successfully",
        request_id=request_id,
        device_id=device_id,
        logs_count=len(logs),
        total_count=total_count,
        filtered_by_level=log_level,
        time_range_hours=hours
    )

    # Calculate page number from offset and limit
    page = (offset // limit) + 1 if limit > 0 else 1

    return paginated_response(
        data=logs_list,
        total=total_count,
        page=page,
        page_size=limit,
        request_id=request_id
    )


@router.delete("/devices/{device_id}/logs")
def delete_device_logs(
    device_id: int,
    request: Request,
    older_than_hours: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete logs for a specific device

    Args:
        device_id: Device ID
        request: FastAPI Request object (for request_id)
        older_than_hours: Delete logs older than N hours (optional, defaults to all)
        db: Database session
        current_user: Authenticated user (required)

    Returns:
        Success response with deletion count

    Raises:
        NotFoundException: If device not found

    Notes:
        - Requires JWT authentication
        - If older_than_hours not specified, deletes ALL logs for device
        - Returns 200 with success message (Quick Wins standard)
    """
    request_id = get_request_id(request)

    logger.info(
        "Device logs deletion started",
        request_id=request_id,
        device_id=device_id,
        older_than_hours=older_than_hours,
        user_id=current_user.id
    )

    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
        )

    # Build delete query
    query = db.query(DeviceLog).filter(DeviceLog.device_id == device_id)

    # Filter by age
    if older_than_hours:
        before = datetime.utcnow() - timedelta(hours=older_than_hours)
        query = query.filter(DeviceLog.timestamp < before)

    count = query.delete()
    db.commit()

    logger.info(
        "Device logs deleted successfully",
        request_id=request_id,
        device_id=device_id,
        logs_deleted=count,
        older_than_hours=older_than_hours
    )

    return success_response(
        data={
            "message": f"Deleted {count} logs for device {device_id}",
            "logs_deleted": count,
            "device_id": device_id,
            "older_than_hours": older_than_hours
        },
        request_id=request_id
    )
