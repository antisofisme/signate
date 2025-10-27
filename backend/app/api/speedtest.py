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
from app.middleware.request_id import get_request_id
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException
from app.schemas.common import success_response, paginated_response

logger = StructuredLogger(__name__)
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


@router.post("/devices/{device_id}/speedtest", status_code=status.HTTP_201_CREATED)
async def store_speed_test_result(
    device_id: int,
    test_data: SpeedTestCreate,
    request: Request,
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
    request_id = get_request_id(request)

    logger.info(
        "Speed test result submission started",
        request_id=request_id,
        device_id=device_id,
        download_speed=test_data.download_speed,
        upload_speed=test_data.upload_speed,
        latency=test_data.latency
    )

    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        logger.warning(
            "Speed test submission failed - device not found",
            request_id=request_id,
            device_id=device_id
        )
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
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
            deleted_count = db.query(DeviceSpeedTest).filter(
                DeviceSpeedTest.id.in_(test_ids_to_delete)
            ).delete(synchronize_session=False)
            db.commit()

            logger.info(
                "Retention policy applied",
                request_id=request_id,
                device_id=device_id,
                deleted_count=deleted_count
            )

    # Convert to dict for response
    test_dict = {
        "id": speed_test.id,
        "device_id": speed_test.device_id,
        "download_speed": speed_test.download_speed,
        "upload_speed": speed_test.upload_speed,
        "latency": speed_test.latency,
        "jitter": speed_test.jitter,
        "packet_loss": speed_test.packet_loss,
        "dns_server": speed_test.dns_server,
        "quality": speed_test.quality.value if hasattr(speed_test.quality, 'value') else speed_test.quality,
        "tested_at": speed_test.tested_at,
        "test_duration_ms": speed_test.test_duration_ms,
        "server_endpoint": speed_test.server_endpoint,
        "error_message": speed_test.error_message
    }

    logger.info(
        "Speed test stored successfully",
        request_id=request_id,
        test_id=speed_test.id,
        device_id=device_id,
        device_name=device.name,
        download_speed=speed_test.download_speed,
        upload_speed=speed_test.upload_speed,
        latency=speed_test.latency,
        quality=speed_test.quality.value if hasattr(speed_test.quality, 'value') else speed_test.quality,
        test_duration_ms=speed_test.test_duration_ms
    )

    return success_response(
        data=test_dict,
        request_id=request_id
    )


@router.get("/devices/{device_id}/speedtest")
async def get_speed_test_history(
    device_id: int,
    request: Request,
    limit: int = 20,
    offset: int = 0,
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
        offset: Number of records to skip (default: 0)
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        Paginated list of speed tests with total count
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching speed test history",
        request_id=request_id,
        device_id=device_id,
        limit=limit,
        offset=offset
    )

    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        logger.warning(
            "Speed test history fetch failed - device not found",
            request_id=request_id,
            device_id=device_id
        )
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
        )

    # Cap limit at 100
    if limit > 100:
        limit = 100

    # Get speed tests with pagination
    tests = db.query(DeviceSpeedTest).filter(
        DeviceSpeedTest.device_id == device_id
    ).order_by(desc(DeviceSpeedTest.tested_at)).limit(limit).offset(offset).all()

    # Get total count
    total = db.query(func.count(DeviceSpeedTest.id)).filter(
        DeviceSpeedTest.device_id == device_id
    ).scalar()

    # Convert to dict list
    tests_list = []
    for test in tests:
        tests_list.append({
            "id": test.id,
            "device_id": test.device_id,
            "download_speed": test.download_speed,
            "upload_speed": test.upload_speed,
            "latency": test.latency,
            "jitter": test.jitter,
            "packet_loss": test.packet_loss,
            "dns_server": test.dns_server,
            "quality": test.quality.value if hasattr(test.quality, 'value') else test.quality,
            "tested_at": test.tested_at,
            "test_duration_ms": test.test_duration_ms,
            "server_endpoint": test.server_endpoint,
            "error_message": test.error_message
        })

    logger.info(
        "Speed test history retrieved successfully",
        request_id=request_id,
        device_id=device_id,
        device_name=device.name,
        total_tests=total,
        returned_count=len(tests_list)
    )

    return paginated_response(
        data=tests_list,
        total=total,
        page=offset // limit + 1 if limit > 0 else 1,
        page_size=limit,
        request_id=request_id
    )


@router.get("/devices/{device_id}/speedtest/latest")
async def get_latest_speed_test(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get latest speed test result for a device

    Returns the most recent speed test based on tested_at timestamp.

    Args:
        device_id: Device ID
        request: Request object
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        Latest speed test result

    Raises:
        404: Device not found or no speed test results available
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching latest speed test",
        request_id=request_id,
        device_id=device_id
    )

    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        logger.warning(
            "Latest speed test fetch failed - device not found",
            request_id=request_id,
            device_id=device_id
        )
        raise NotFoundException(
            message=f"Device with ID {device_id} not found",
            resource_type="Device",
            resource_id=device_id
        )

    # Get latest speed test
    latest_test = db.query(DeviceSpeedTest).filter(
        DeviceSpeedTest.device_id == device_id
    ).order_by(desc(DeviceSpeedTest.tested_at)).first()

    if not latest_test:
        logger.warning(
            "No speed test results found for device",
            request_id=request_id,
            device_id=device_id,
            device_name=device.name
        )
        raise NotFoundException(
            message=f"No speed test results found for device {device_id}",
            resource_type="SpeedTest",
            resource_id=None
        )

    # Convert to dict
    test_dict = {
        "id": latest_test.id,
        "device_id": latest_test.device_id,
        "download_speed": latest_test.download_speed,
        "upload_speed": latest_test.upload_speed,
        "latency": latest_test.latency,
        "jitter": latest_test.jitter,
        "packet_loss": latest_test.packet_loss,
        "dns_server": latest_test.dns_server,
        "quality": latest_test.quality.value if hasattr(latest_test.quality, 'value') else latest_test.quality,
        "tested_at": latest_test.tested_at,
        "test_duration_ms": latest_test.test_duration_ms,
        "server_endpoint": latest_test.server_endpoint,
        "error_message": latest_test.error_message
    }

    logger.info(
        "Latest speed test retrieved successfully",
        request_id=request_id,
        test_id=latest_test.id,
        device_id=device_id,
        device_name=device.name,
        download_speed=latest_test.download_speed,
        upload_speed=latest_test.upload_speed,
        quality=latest_test.quality.value if hasattr(latest_test.quality, 'value') else latest_test.quality,
        tested_at=latest_test.tested_at
    )

    return success_response(
        data=test_dict,
        request_id=request_id
    )
