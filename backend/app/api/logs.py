"""
Device Logs API endpoints
For remote monitoring and debugging of viewer devices
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis_client import publish_log
from app.models.user import User
from app.models.device import Device
from app.models.device_log import DeviceLog

logger = logging.getLogger(__name__)
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
    db: Session = Depends(get_db)
):
    """
    Create a device log entry
    
    Called by viewer devices to send console logs to backend for remote monitoring.
    
    Args:
        log_data: Log data (device_id, log_level, message, source)
        db: Database session
    
    Returns:
        Success message
    
    Notes:
        - This endpoint does NOT require authentication (for viewer clients)
        - Logs are stored with timestamps for chronological viewing
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == log_data.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {log_data.device_id} not found"
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

    logger.info(f"Device {log_data.device_id} logged [{log_data.log_level}]: {log_data.message[:100]}")

    # Publish to Redis for real-time streaming
    publish_log(log_data.device_id, {
        "id": log_entry.id,
        "device_id": log_entry.device_id,
        "log_level": log_entry.log_level,
        "message": log_entry.message,
        "source": log_entry.source,
        "timestamp": log_entry.timestamp.isoformat()
    })

    return {"message": "Log created successfully"}


@router.post("/client/logs/batch", status_code=status.HTTP_201_CREATED)
def create_device_logs_batch(
    batch_data: DeviceLogBatchCreate,
    db: Session = Depends(get_db)
):
    """
    Create multiple device log entries in one request
    
    Optimized for viewers to send multiple logs at once (batch submission).
    
    Args:
        batch_data: Batch log data (device_id, logs array)
        db: Database session
    
    Returns:
        Success message with count
    
    Notes:
        - This endpoint does NOT require authentication
        - More efficient than sending logs one by one
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == batch_data.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {batch_data.device_id} not found"
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

    logger.info(f"Device {batch_data.device_id} logged {len(log_entries)} entries in batch")

    # Publish each log to Redis for real-time streaming
    for entry in log_entries:
        publish_log(batch_data.device_id, {
            "id": entry.id,
            "device_id": entry.device_id,
            "log_level": entry.log_level,
            "message": entry.message,
            "source": entry.source,
            "timestamp": entry.timestamp.isoformat()
        })

    return {"message": f"{len(log_entries)} logs created successfully"}


# ========================================
# Admin Endpoints (Requires Authentication)
# ========================================

@router.get("/devices/{device_id}/logs", response_model=List[DeviceLogResponse])
def get_device_logs(
    device_id: int,
    log_level: Optional[str] = None,
    hours: Optional[int] = 24,
    limit: Optional[int] = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get logs for a specific device
    
    Args:
        device_id: Device ID
        log_level: Filter by log level (optional: log, warn, error, info)
        hours: Get logs from last N hours (default: 24)
        limit: Maximum number of logs to return (default: 1000)
        db: Database session
        current_user: Authenticated user (required)
    
    Returns:
        List of device logs
    
    Raises:
        HTTPException: If device not found
    
    Notes:
        - Requires JWT authentication (admin only)
        - Logs ordered by timestamp DESC (newest first)
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Build query
    query = db.query(DeviceLog).filter(DeviceLog.device_id == device_id)
    
    # Filter by log level
    if log_level:
        query = query.filter(DeviceLog.log_level == log_level)
    
    # Filter by time range
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(DeviceLog.timestamp >= since)
    
    # Order by timestamp DESC (newest first)
    query = query.order_by(DeviceLog.timestamp.desc())
    
    # Limit results
    if limit:
        query = query.limit(limit)
    
    logs = query.all()
    
    logger.info(f"Retrieved {len(logs)} logs for device {device_id}")
    
    return logs


@router.delete("/devices/{device_id}/logs", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_logs(
    device_id: int,
    older_than_hours: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete logs for a specific device
    
    Args:
        device_id: Device ID
        older_than_hours: Delete logs older than N hours (optional, defaults to all)
        db: Database session
        current_user: Authenticated user (required)
    
    Returns:
        204 No Content
    
    Notes:
        - Requires JWT authentication
        - If older_than_hours not specified, deletes ALL logs for device
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Build delete query
    query = db.query(DeviceLog).filter(DeviceLog.device_id == device_id)
    
    # Filter by age
    if older_than_hours:
        before = datetime.utcnow() - timedelta(hours=older_than_hours)
        query = query.filter(DeviceLog.timestamp < before)
    
    count = query.delete()
    db.commit()
    
    logger.info(f"Deleted {count} logs for device {device_id}")
    
    return None
