"""
Client API endpoints
For TV/Monitor devices to fetch playlist and check status
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import List
import logging
import httpx
import base64
import json

from app.core.database import get_db
from app.core.config import settings
from app.models.device import Device
from app.models.content import Content
from app.models.assignment import ContentAssignment
from app.models.tag import DeviceTag
from app.schemas.client import PlaylistResponse, PlaylistItem, DeviceStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/playlist", response_model=PlaylistResponse)
def get_device_playlist(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get playlist for a device

    This endpoint is called by TV/Monitor devices to fetch their assigned content.

    Logic:
    1. Get device info
    2. Get device's tags
    3. Query content assignments for:
       - Content assigned directly to this device, OR
       - Content assigned to any of this device's tags
    4. Filter only active content
    5. Sort by priority (higher priority first)
    6. Return playlist with Anthias URLs

    Args:
        device_id: Device ID
        db: Database session

    Returns:
        PlaylistResponse: Playlist with content items

    Raises:
        HTTPException: If device not found

    Notes:
        - This endpoint does NOT require authentication (for device clients)
        - Content is served from Anthias URLs
        - Playlist is regenerated on each request (real-time)
    """
    # Get device
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Get device's tags
    device_tags = db.query(DeviceTag).filter(DeviceTag.device_id == device_id).all()
    tag_ids = [dt.tag_id for dt in device_tags]

    logger.info(f"Device {device_id} has {len(tag_ids)} tags: {tag_ids}")

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
            (ContentAssignment.device_id == device_id) |
            (ContentAssignment.tag_id.in_(tag_ids))
        )
    else:
        assignments_query = assignments_query.filter(
            ContentAssignment.device_id == device_id
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

        # Use direct Anthias static file URL (CORS enabled via nginx config)
        # Performance: Browser caching, no decode overhead, direct binary streaming
        # Pattern: Control Plane (backend API) / Data Plane (Anthias static files) separation

        # Fetch asset URI from Anthias to get actual file path
        try:
            anthias_asset_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}"

            # Synchronous HTTP client for playlist generation
            with httpx.Client(timeout=5.0) as client:
                response = client.get(anthias_asset_url)

                if response.status_code == 200:
                    asset_data = response.json()
                    asset_uri = asset_data.get('uri', '')  # e.g., /data/screenly_assets/51ef3ffb...

                    if asset_uri and asset_uri.startswith('/data/screenly_assets/'):
                        # Convert internal path to nginx static URL
                        filename = asset_uri.replace('/data/screenly_assets/', '')
                        direct_content_url = f"{settings.ANTHIAS_API_URL}/screenly_assets/{filename}"
                        logger.debug(f"Direct URL for content {content.id}: {direct_content_url}")
                    else:
                        logger.warning(f"Unexpected URI format for asset {content.anthias_asset_id}: {asset_uri}")
                        # Fallback to API endpoint (will return base64 JSON, not ideal but works)
                        direct_content_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}/content"
                else:
                    logger.error(f"Failed to fetch asset {content.anthias_asset_id} from Anthias: HTTP {response.status_code}")
                    # Fallback to API endpoint
                    direct_content_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}/content"
        except Exception as e:
            logger.error(f"Error fetching asset URI for {content.anthias_asset_id}: {e}")
            # Fallback to API endpoint
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

    logger.info(f"Generated playlist for device {device_id}: {len(playlist_items)} items")

    return PlaylistResponse(
        device_id=device.id,
        device_name=device.device_name,
        device_type=device.device_type,
        total_items=len(playlist_items),
        playlist=playlist_items
    )


@router.get("/status", response_model=DeviceStatusResponse)
def check_device_status(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Check device status

    Used by devices to check if they are still active and authorized.

    Args:
        device_id: Device ID
        db: Database session

    Returns:
        DeviceStatusResponse: Device status information

    Raises:
        HTTPException: If device not found

    Notes:
        - This endpoint does NOT require authentication
        - Devices can poll this to check their status
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    is_active = device.status == "active"

    if is_active:
        message = "Device is active and authorized"
    elif device.status == "pending":
        message = "Device is pending activation"
    elif device.status == "inactive":
        message = "Device is inactive"
    else:
        message = f"Device status: {device.status}"

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
