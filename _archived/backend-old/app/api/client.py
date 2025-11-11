"""
Client API endpoints
For TV/Monitor devices to fetch playlist and check status
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import httpx
import time

from app.core.database import get_db
from app.core.config import settings
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, InternalServerException
from app.core.deps import get_current_device
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response
from app.models.device import Device
from app.models.content import Content
from app.models.assignment import ContentAssignment
from app.models.tag import DeviceTag
from app.schemas.client import PlaylistResponse, PlaylistItem, DeviceStatusResponse

logger = StructuredLogger(__name__)
router = APIRouter()


@router.get("/playlist", response_model=PlaylistResponse)
def get_device_playlist(
    request: Request,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Get playlist for authenticated device

    This endpoint is called by TV/Monitor devices to fetch their assigned content.
    Device must provide JWT token in Authorization header.

    Logic:
    1. Verify device token
    2. Get device's tags
    3. Query content assignments for:
       - Content assigned directly to this device, OR
       - Content assigned to any of this device's tags
    4. Filter only active content
    5. Sort by priority (higher priority first)
    6. Return playlist with Anthias URLs

    Args:
        request: FastAPI Request object (for request_id tracking)
        device: Authenticated device from JWT token
        db: Database session

    Returns:
        PlaylistResponse: Playlist with content items

    Raises:
        401: If device token is invalid
        403: If device is not active
        InternalServerException: If Anthias API call fails

    Notes:
        - Requires device JWT authentication
        - Content is served from Anthias URLs
        - Playlist is regenerated on each request (real-time)
    """
    request_id = get_request_id(request)

    # Start performance timer for Phase 2 optimization metrics
    start_time = time.time()

    logger.info(
        "Fetching device playlist",
        request_id=request_id,
        device_id=device.id,
        device_name=device.device_name
    )

    # Device is already verified and active via get_current_device dependency

    # Get device's tags
    device_tags = db.query(DeviceTag).filter(DeviceTag.device_id == device.id).all()
    tag_ids = [dt.tag_id for dt in device_tags]

    logger.info(
        "Retrieved device tags",
        request_id=request_id,
        device_id=device.id,
        tag_count=len(tag_ids),
        tag_ids=tag_ids
    )

    # Query content assignments
    # Get content assigned to this device OR to any of its tags
    assignments_query = db.query(ContentAssignment, Content).join(
        Content, ContentAssignment.content_id == Content.id
    ).filter(
        Content.is_active == True  # Only active content
    )

    # Filter by device_id OR tag_id
    if tag_ids:
        assignments_query = assignments_query.filter(
            (ContentAssignment.device_id == device.id) |
            (ContentAssignment.tag_id.in_(tag_ids))
        )
    else:
        assignments_query = assignments_query.filter(
            ContentAssignment.device_id == device.id
        )

    # Order by priority (higher first)
    assignments = assignments_query.order_by(
        ContentAssignment.priority.desc()
    ).all()

    # Build playlist
    playlist_items = []
    seen_content_ids = set()  # Avoid duplicates

    for assignment, content in assignments:
        # Skip if already added (e.g., assigned to both device and tag)
        if content.id in seen_content_ids:
            continue

        seen_content_ids.add(content.id)

        # PHASE 2 OPTIMIZATION: Use cached anthias_file_uri from database
        # Eliminates +130ms Anthias API call per content item
        # Performance: Control Plane (backend API) / Data Plane (Anthias static files) separation

        if content.anthias_file_uri and content.anthias_file_uri.startswith('/data/screenly_assets/'):
            # Use cached URI from database (FAST PATH - no API call!)
            filename = content.anthias_file_uri.replace('/data/screenly_assets/', '')
            direct_content_url = f"{settings.ANTHIAS_PUBLIC_URL}/screenly_assets/{filename}"

            logger.debug(
                "Using cached URI (Phase 2 optimization)",
                request_id=request_id,
                content_id=content.id,
                cached_uri=content.anthias_file_uri,
                direct_url=direct_content_url
            )
        else:
            # FALLBACK: For legacy content or NULL anthias_file_uri, fetch from Anthias API (SLOW PATH)
            logger.warning(
                "Missing cached URI, falling back to Anthias API",
                request_id=request_id,
                content_id=content.id,
                anthias_asset_id=content.anthias_asset_id,
                anthias_file_uri=content.anthias_file_uri
            )

            try:
                anthias_asset_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}"

                # Synchronous HTTP client for playlist generation
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(anthias_asset_url)

                    if response.status_code == 200:
                        asset_data = response.json()
                        asset_uri = asset_data.get('uri', '')

                        if asset_uri and asset_uri.startswith('/data/screenly_assets/'):
                            filename = asset_uri.replace('/data/screenly_assets/', '')
                            direct_content_url = f"{settings.ANTHIAS_PUBLIC_URL}/screenly_assets/{filename}"
                        else:
                            # Fallback to API endpoint
                            direct_content_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}/content"
                    else:
                        # Fallback to API endpoint
                        direct_content_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}/content"
            except Exception as e:
                logger.error(
                    "Error fetching asset URI from Anthias (fallback path)",
                    request_id=request_id,
                    anthias_asset_id=content.anthias_asset_id,
                    error=str(e),
                    exc_info=True
                )
                # Final fallback to API endpoint
                direct_content_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}/content"

        playlist_item = PlaylistItem(
            content_id=content.id,
            title=content.title,
            content_type=content.content_type,
            url=direct_content_url,
            duration=content.duration,
            mime_type=content.mime_type
        )
        playlist_items.append(playlist_item)

    # Calculate performance metrics
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000

    logger.info(
        "Playlist generated successfully",
        request_id=request_id,
        device_id=device.id,
        total_items=len(playlist_items),
        duration_ms=round(duration_ms, 2),
        avg_per_item_ms=round(duration_ms / len(playlist_items), 2) if playlist_items else 0
    )

    return PlaylistResponse(
        device_id=device.id,
        device_name=device.device_name,
        device_type=device.device_type,
        total_items=len(playlist_items),
        playlist=playlist_items
    )


@router.get("/status", response_model=DeviceStatusResponse)
def check_device_status(
    request: Request,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Check device status

    Used by authenticated devices to check if they are still active and authorized.

    Args:
        request: FastAPI Request object (for request_id tracking)
        device: Authenticated device from JWT token
        db: Database session

    Returns:
        DeviceStatusResponse: Device status information

    Raises:
        401: If device token is invalid
        403: If device is not active

    Notes:
        - Requires device JWT authentication
        - Devices can poll this to check their status
    """
    request_id = get_request_id(request)

    logger.info(
        "Checking device status",
        request_id=request_id,
        device_id=device.id,
        device_name=device.device_name
    )

    # Device is already verified via get_current_device dependency

    is_active = device.status == "active"

    if is_active:
        message = "Device is active and authorized"
    elif device.status == "pending":
        message = "Device is pending activation"
    elif device.status == "inactive":
        message = "Device is inactive"
    else:
        message = f"Device status: {device.status}"

    logger.info(
        "Device status retrieved",
        request_id=request_id,
        device_id=device.id,
        status=device.status,
        is_active=is_active
    )

    return DeviceStatusResponse(
        device_id=device.id,
        status=device.status,
        is_active=is_active,
        message=message
    )


# Proxy endpoint removed - no longer needed
# CORS is now enabled directly on Anthias nginx for /screenly_assets/
# This allows direct binary file access without base64 decode overhead
# See: anthias/docker/nginx/nginx.development.conf
