"""
Speed Test API endpoints
Provides endpoints for upload speed testing (discards data) and storing test results
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.models.user import User
from app.models.device import Device
from app.models.speed_test import DeviceSpeedTest, SpeedTestQuality
from app.schemas.speed_test import (
    SpeedTestCreate,
    SpeedTestResponse,
    SpeedTestListResponse
)

router = APIRouter(prefix="/api/speedtest", tags=["speedtest"])


@router.post("/upload")
async def upload_speed_test(request: Request):
    """
    Upload speed test endpoint

    Simply receives data and discards it
    Used by clients to measure upload speed
    """
    # Read the body but don't store it
    # This just measures how fast the client can upload
    await request.body()

    # Return minimal response
    return Response(status_code=200, content="OK")


@router.get("/download")
async def download_speed_test(bytes: int = 1000000):
    """
    Download speed test endpoint

    Returns dummy data of specified size for download speed testing
    Default: 1MB
    """
    # Generate dummy data
    dummy_data = b'0' * bytes

    return Response(
        content=dummy_data,
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


# =============================================================================
# SPEED TEST RESULTS STORAGE
# =============================================================================

def calculate_quality(download_speed: float, upload_speed: float) -> SpeedTestQuality:
    """
    Calculate speed test quality based on thresholds

    Thresholds:
    - Good: Download ≥25 Mbps AND Upload ≥10 Mbps
    - Fair: Download ≥10 Mbps AND Upload ≥5 Mbps
    - Poor: Below fair thresholds

    Args:
        download_speed: Download speed in Mbps
        upload_speed: Upload speed in Mbps

    Returns:
        SpeedTestQuality: good, fair, or poor
    """
    if download_speed >= 25 and upload_speed >= 10:
        return SpeedTestQuality.GOOD
    elif download_speed >= 10 and upload_speed >= 5:
        return SpeedTestQuality.FAIR
    else:
        return SpeedTestQuality.POOR


@router.post("/devices/{device_id}/speedtest", response_model=SpeedTestResponse, status_code=status.HTTP_201_CREATED)
async def store_speed_test_result(
    device_id: int,
    test_data: SpeedTestCreate,
    db: Session = Depends(get_db)
):
    """
    Store speed test result for a device

    No authentication required (consistent with heartbeat pattern).
    Automatically calculates quality based on speed thresholds.
    Implements retention policy: keeps last 100 tests per device.

    Quality Thresholds:
    - Good: Download ≥25 Mbps AND Upload ≥10 Mbps
    - Fair: Download ≥10 Mbps AND Upload ≥5 Mbps
    - Poor: Below fair thresholds

    Retention Policy:
    - Keeps last 100 tests per device
    - Older tests are automatically deleted
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Calculate quality based on thresholds
    quality = calculate_quality(test_data.download_speed, test_data.upload_speed)

    # Create speed test record
    speed_test = DeviceSpeedTest(
        device_id=device_id,
        download_speed=test_data.download_speed,
        upload_speed=test_data.upload_speed,
        latency=test_data.latency,
        jitter=test_data.jitter,
        packet_loss=test_data.packet_loss,
        dns_server=test_data.dns_server,
        quality=quality,
        test_duration_ms=test_data.test_duration_ms,
        server_endpoint=test_data.server_endpoint,
        error_message=test_data.error_message
    )

    db.add(speed_test)
    db.commit()
    db.refresh(speed_test)

    # Enforce retention policy: keep last 100 tests per device
    # Get count of tests for this device
    test_count = db.query(func.count(DeviceSpeedTest.id)).filter(
        DeviceSpeedTest.device_id == device_id
    ).scalar()

    if test_count > 100:
        # Delete oldest tests beyond 100
        # Get IDs of oldest tests to delete
        tests_to_delete = db.query(DeviceSpeedTest.id).filter(
            DeviceSpeedTest.device_id == device_id
        ).order_by(DeviceSpeedTest.tested_at.desc()).offset(100).all()

        if tests_to_delete:
            test_ids_to_delete = [t.id for t in tests_to_delete]
            db.query(DeviceSpeedTest).filter(
                DeviceSpeedTest.id.in_(test_ids_to_delete)
            ).delete(synchronize_session=False)
            db.commit()

    return speed_test


@router.get("/devices/{device_id}/speedtest", response_model=SpeedTestListResponse)
async def get_speed_test_history(
    device_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get speed test history for a device

    Returns list of speed tests ordered by tested_at (newest first).
    Default limit is 20 tests.

    Args:
        device_id: Device ID
        limit: Maximum number of tests to return (default: 20, max: 100)
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        SpeedTestListResponse: List of speed tests with total count
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Cap limit at 100
    if limit > 100:
        limit = 100

    # Get speed tests
    tests = db.query(DeviceSpeedTest).filter(
        DeviceSpeedTest.device_id == device_id
    ).order_by(desc(DeviceSpeedTest.tested_at)).limit(limit).all()

    # Get total count
    total = db.query(func.count(DeviceSpeedTest.id)).filter(
        DeviceSpeedTest.device_id == device_id
    ).scalar()

    return SpeedTestListResponse(
        total=total,
        items=tests
    )


@router.get("/devices/{device_id}/speedtest/latest", response_model=SpeedTestResponse)
async def get_latest_speed_test(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get latest speed test result for a device

    Returns the most recent speed test based on tested_at timestamp.

    Args:
        device_id: Device ID
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        SpeedTestResponse: Latest speed test result

    Raises:
        404: Device not found or no speed test results available
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Get latest speed test
    latest_test = db.query(DeviceSpeedTest).filter(
        DeviceSpeedTest.device_id == device_id
    ).order_by(desc(DeviceSpeedTest.tested_at)).first()

    if not latest_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No speed test results found for device {device_id}"
        )

    return latest_test
