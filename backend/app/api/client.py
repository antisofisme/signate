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

        # Use proxy URL instead of direct Anthias URL to avoid CORS issues
        # The proxy endpoint will fetch content from Anthias and serve it with proper CORS headers
        proxy_url = f"{settings.API_BASE_URL}/api/client/content-proxy/{content.id}"

        playlist_item = PlaylistItem(
            content_id=content.id,
            title=content.title,
            content_type=content.content_type,
            url=proxy_url,
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


@router.get("/content-proxy/{content_id}")
async def proxy_content(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    Proxy content from Anthias to avoid CORS issues

    This endpoint fetches content from the Anthias server and streams it to the client
    with proper CORS headers, solving the cross-origin issue when the monitor viewer
    tries to load content from Anthias.

    Args:
        content_id: Content ID to proxy
        db: Database session

    Returns:
        StreamingResponse: Content streamed from Anthias with proper headers

    Raises:
        HTTPException: If content not found or Anthias request fails

    Notes:
        - This endpoint does NOT require authentication (for device clients)
        - Content is fetched from Anthias and streamed through
        - CORS headers are automatically added by FastAPI middleware
    """
    # Get content from database
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    # Fetch content from Anthias using internal API
    # Use anthias_asset_id to construct the correct API URL
    # Note: From inside docker network, use anthias-nginx hostname
    anthias_content_url = f"http://anthias-nginx/api/v1/assets/{content.anthias_asset_id}/content"

    logger.info(f"Fetching content from Anthias: {anthias_content_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(anthias_content_url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to fetch content from Anthias: HTTP {response.status_code}"
                )

            # Parse JSON response from Anthias and decode base64 content
            anthias_data = response.json()
            base64_content = anthias_data.get('content', '')

            if not base64_content:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="No content in Anthias response"
                )

            # Decode base64 content
            binary_content = base64.b64decode(base64_content)

            # Return binary content with proper headers
            return Response(
                content=binary_content,
                media_type=content.mime_type or "application/octet-stream",
                headers={
                    "Content-Length": str(len(binary_content)),
                    "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                }
            )
    except httpx.RequestError as e:
        logger.error(f"Error fetching content from Anthias: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch content from Anthias: {str(e)}"
        )
