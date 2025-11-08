"""
Extended Device API Routes
Additional device functionality:
- TV/Monitor registration
- Device release
- Content resolution (3-tier priority)
- Speed tests
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.database import get_db
from shared.api_routes import DeviceRoutes
from datetime import datetime, timedelta
from typing import Optional, List
import json
import random
import string

router = APIRouter()


# ============================================================================
# DTOs
# ============================================================================

from pydantic import BaseModel, Field

class TVRegisterRequest(BaseModel):
    """TV device registration"""
    device_name: str
    organization_id: int
    device_uuid: Optional[str] = None
    platform: Optional[str] = "webOS"
    model_name: Optional[str] = None
    firmware_version: Optional[str] = None

class MonitorRegisterRequest(BaseModel):
    """Monitor device registration"""
    organization_id: Optional[int] = None  # Optional - for re-registration
    activation_code: str
    device_name: Optional[str] = None
    platform: Optional[str] = "browser"
    device_type: str = "monitor"

class SpeedTestRequest(BaseModel):
    """Request to run speed test"""
    device_id: int
    download_speed: float
    upload_speed: float
    latency: int
    jitter: Optional[int] = None
    packet_loss: Optional[float] = None
    dns_server: Optional[str] = None
    server_endpoint: Optional[str] = None
    test_duration_ms: Optional[int] = None

class SpeedTestResponse(BaseModel):
    """Speed test result"""
    id: int
    device_id: int
    download_speed: float
    upload_speed: float
    latency: int
    jitter: Optional[int]
    packet_loss: Optional[float]
    dns_server: Optional[str]
    server_endpoint: Optional[str]
    quality: str
    test_duration_ms: Optional[int]
    tested_at: datetime

class ContentItem(BaseModel):
    """Content item in resolution result"""
    id: int
    name: str
    type: str
    uri: str
    duration: int
    priority: int
    source: str  # 'direct', 'tag', or 'playlist'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_activation_code() -> str:
    """Generate 6-digit activation code"""
    # Use alphanumeric excluding confusing chars (0, O, 1, I)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(6))


def calculate_speed_quality(download: float, upload: float) -> str:
    """Calculate speed test quality"""
    if download >= 25 and upload >= 10:
        return 'good'
    elif download >= 10 and upload >= 5:
        return 'fair'
    else:
        return 'poor'


# ============================================================================
# TV/MONITOR REGISTRATION
# ============================================================================

@router.post(DeviceRoutes.TV_REGISTER, status_code=status.HTTP_201_CREATED)
def register_tv_device(
    request: TVRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register TV device (WebOS/native)

    TV devices activate immediately as 'active' (no code needed).
    """
    query = text("""
        INSERT INTO devices (
            device_type, device_name, device_uuid, platform, model_name,
            firmware_version, organization_id, status, created_at
        )
        VALUES (
            'tv', :device_name, :device_uuid, :platform, :model_name,
            :firmware_version, :organization_id, 'active', NOW()
        )
        RETURNING id, device_name, device_uuid, status, created_at
    """)

    result = db.execute(query, {
        "device_name": request.device_name,
        "device_uuid": request.device_uuid,
        "platform": request.platform,
        "model_name": request.model_name,
        "firmware_version": request.firmware_version,
        "organization_id": request.organization_id
    }).fetchone()

    db.commit()

    return {
        "success": True,
        "data": {
            "id": result.id,
            "device_name": result.device_name,
            "device_uuid": result.device_uuid,
            "status": result.status,
            "created_at": result.created_at
        },
        "message": "TV device registered successfully"
    }


@router.post(DeviceRoutes.MONITOR_REGISTER, status_code=status.HTTP_201_CREATED)
def register_monitor_device(
    request: MonitorRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register monitor device (browser-based)

    Uses activation code provided by player (6-digit).
    Device status is 'pending' until admin activates.
    """
    # Use code from player, or generate if not provided
    code = request.activation_code or generate_activation_code()
    code_expires = datetime.now() + timedelta(minutes=10)
    device_name = request.device_name or f"Monitor-{code}"

    query = text("""
        INSERT INTO devices (
            device_type, device_name, unique_code, code_expires_at,
            platform, organization_id, status, created_at
        )
        VALUES (
            'monitor', :device_name, :unique_code, :code_expires_at,
            :platform, :organization_id, 'pending', NOW()
        )
        RETURNING id, device_name, unique_code, code_expires_at, status, created_at, organization_id
    """)

    result = db.execute(query, {
        "device_name": device_name,
        "unique_code": code,
        "code_expires_at": code_expires,
        "platform": request.platform,
        "organization_id": request.organization_id
    }).fetchone()

    db.commit()

    return {
        "success": True,
        "data": {
            "id": result.id,
            "device_name": result.device_name,
            "unique_code": result.unique_code,
            "code_expires_at": result.code_expires_at,
            "organization_id": result.organization_id,
            "status": result.status,
            "created_at": result.created_at
        },
        "message": "Monitor device registered. Use the code to activate."
    }


# ============================================================================
# DEVICE RELEASE
# ============================================================================

@router.post(DeviceRoutes.RELEASE, status_code=status.HTTP_200_OK)
def release_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Release device without deletion

    Sets status to 'inactive', clears code, records release timestamp.
    Sends RESET command to device to clear storage.
    """
    # Check device exists
    device_check = db.execute(
        text("SELECT id, organization_id, device_name FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Update device to inactive
    update_query = text("""
        UPDATE devices
        SET status = 'inactive',
            unique_code = NULL,
            code_expires_at = NULL,
            released_at = NOW()
        WHERE id = :device_id
        RETURNING id, device_name, status, released_at
    """)

    result = db.execute(update_query, {"device_id": device_id}).fetchone()

    # Queue RESET command
    command_query = text("""
        INSERT INTO device_commands (
            device_id, organization_id, command_type, reason,
            status, expires_at, created_at
        )
        VALUES (
            :device_id, :organization_id, 'reset', 'device_released',
            'pending', :expires_at, NOW()
        )
    """)

    db.execute(command_query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "expires_at": datetime.now() + timedelta(days=7)
    })

    db.commit()

    return {
        "success": True,
        "data": {
            "id": result.id,
            "device_name": result.device_name,
            "status": result.status,
            "released_at": result.released_at
        },
        "message": f"Device '{result.device_name}' released successfully"
    }


# ============================================================================
# CONTENT RESOLUTION (3-Tier Priority)
# ============================================================================

@router.get(DeviceRoutes.CONTENT_RESOLVED)
def get_resolved_content(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get content for device using 3-tier priority system

    Priority Order:
    1. Direct assignments (highest priority)
    2. Tag-based assignments
    3. Playlist assignments (lowest priority)

    Returns merged content list sorted by priority.
    """
    # Wrap in try-except to handle missing tables gracefully
    try:
        # Priority 1: Direct content assignments
        direct_query = text("""
        SELECT c.id, c.name, c.type, c.uri, c.duration,
               ca.priority, 'direct' as source
        FROM content_assignments ca
        JOIN contents c ON c.id = ca.content_id
        WHERE ca.device_id = :device_id
          AND (ca.expires_at IS NULL OR ca.expires_at > NOW())
        ORDER BY ca.priority DESC
    """)

    direct_results = db.execute(direct_query, {"device_id": device_id}).fetchall()

    # Priority 2: Tag-based content
    tag_query = text("""
        SELECT DISTINCT c.id, c.name, c.type, c.uri, c.duration,
               0 as priority, 'tag' as source
        FROM device_tags dt
        JOIN content_tags ct ON ct.tag_id = dt.tag_id
        JOIN contents c ON c.id = ct.content_id
        WHERE dt.device_id = :device_id
    """)

    tag_results = db.execute(tag_query, {"device_id": device_id}).fetchall()

    # Priority 3: Playlist content
    playlist_query = text("""
        SELECT DISTINCT c.id, c.name, c.type, c.uri, c.duration,
               0 as priority, 'playlist' as source
        FROM playlist_devices pd
        JOIN playlist_items pi ON pi.playlist_id = pd.playlist_id
        JOIN contents c ON c.id = pi.content_id
        WHERE pd.device_id = :device_id
        ORDER BY pi.order_index ASC
    """)

    playlist_results = db.execute(playlist_query, {"device_id": device_id}).fetchall()

    # Merge all results
    content_items = []

    for row in direct_results:
        content_items.append({
            "id": row.id,
            "name": row.name,
            "type": row.type,
            "uri": row.uri,
            "duration": row.duration,
            "priority": row.priority,
            "source": row.source
        })

    for row in tag_results:
        # Avoid duplicates from direct assignments
        if not any(item['id'] == row.id for item in content_items):
            content_items.append({
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "uri": row.uri,
                "duration": row.duration,
                "priority": row.priority,
                "source": row.source
            })

    for row in playlist_results:
        # Avoid duplicates
        if not any(item['id'] == row.id for item in content_items):
            content_items.append({
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "uri": row.uri,
                "duration": row.duration,
                "priority": row.priority,
                "source": row.source
            })

        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "total": len(content_items),
                "items": content_items,
                "breakdown": {
                    "direct": len(direct_results),
                    "tag": len(tag_results),
                    "playlist": len(playlist_results)
                }
            }
        }
    except Exception as e:
        # Tables don't exist yet (Phase 5+ feature)
        # Return empty content - player will show "No content assigned"
        print(f"[Content Resolution] Tables not ready: {e}")
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "total": 0,
                "items": [],
                "breakdown": {
                    "direct": 0,
                    "tag": 0,
                    "playlist": 0
                }
            }
        }


# ============================================================================
# SPEED TESTS
# ============================================================================

@router.post(DeviceRoutes.SPEED_TEST, response_model=SpeedTestResponse, status_code=status.HTTP_201_CREATED)
def record_speed_test(
    device_id: int,
    request: SpeedTestRequest,
    db: Session = Depends(get_db)
):
    """
    Record speed test result (called by player)

    Stores network speed test results for monitoring.
    Calculates quality based on download/upload speeds.
    """
    # Check device exists
    device_check = db.execute(
        text("SELECT id, organization_id FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Calculate quality
    quality = calculate_speed_quality(request.download_speed, request.upload_speed)

    # Insert speed test
    query = text("""
        INSERT INTO device_speed_tests (
            device_id, organization_id, download_speed, upload_speed,
            latency, jitter, packet_loss, dns_server, server_endpoint,
            quality, test_duration_ms, tested_at
        )
        VALUES (
            :device_id, :organization_id, :download_speed, :upload_speed,
            :latency, :jitter, :packet_loss, :dns_server, :server_endpoint,
            :quality, :test_duration_ms, NOW()
        )
        RETURNING id, device_id, download_speed, upload_speed, latency,
                  jitter, packet_loss, dns_server, server_endpoint,
                  quality, test_duration_ms, tested_at
    """)

    result = db.execute(query, {
        "device_id": device_id,
        "organization_id": device_check.organization_id,
        "download_speed": request.download_speed,
        "upload_speed": request.upload_speed,
        "latency": request.latency,
        "jitter": request.jitter,
        "packet_loss": request.packet_loss,
        "dns_server": request.dns_server,
        "server_endpoint": request.server_endpoint,
        "quality": quality,
        "test_duration_ms": request.test_duration_ms
    }).fetchone()

    db.commit()

    return SpeedTestResponse(
        id=result.id,
        device_id=result.device_id,
        download_speed=result.download_speed,
        upload_speed=result.upload_speed,
        latency=result.latency,
        jitter=result.jitter,
        packet_loss=result.packet_loss,
        dns_server=result.dns_server,
        server_endpoint=result.server_endpoint,
        quality=result.quality,
        test_duration_ms=result.test_duration_ms,
        tested_at=result.tested_at
    )


@router.get(DeviceRoutes.SPEED_TESTS)
def get_speed_test_history(
    device_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get speed test history for device

    Returns recent speed test results, newest first.
    """
    query = text("""
        SELECT id, device_id, download_speed, upload_speed, latency,
               jitter, packet_loss, dns_server, server_endpoint,
               quality, test_duration_ms, tested_at
        FROM device_speed_tests
        WHERE device_id = :device_id
        ORDER BY tested_at DESC
        LIMIT :limit
    """)

    results = db.execute(query, {"device_id": device_id, "limit": limit}).fetchall()

    tests = []
    for row in results:
        tests.append({
            "id": row.id,
            "device_id": row.device_id,
            "download_speed": float(row.download_speed),
            "upload_speed": float(row.upload_speed),
            "latency": row.latency,
            "jitter": row.jitter,
            "packet_loss": float(row.packet_loss) if row.packet_loss else None,
            "dns_server": row.dns_server,
            "server_endpoint": row.server_endpoint,
            "quality": row.quality,
            "test_duration_ms": row.test_duration_ms,
            "tested_at": row.tested_at
        })

    return {
        "success": True,
        "data": {
            "total": len(tests),
            "items": tests
        }
    }
