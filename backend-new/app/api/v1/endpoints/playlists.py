"""
Playlists API Endpoints
=======================

Playlist management, content assignment, scheduling, dan device assignment.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status, Query, Path
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.exceptions import NotFoundException, BadRequestException
from app.repositories import PlaylistRepository, OrganizationRepository, ContentRepository, DeviceRepository
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistContentAdd,
    PlaylistContentReorder,
    PlaylistAssignDevice,
    PlaylistDuplicate,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistListResponse,
    PlaylistStatsResponse,
    PlaylistContentAddResponse,
    PlaylistAssignmentResponse,
    DevicePlaylistResponse
)

router = APIRouter()


@router.post(
    "/",
    response_model=PlaylistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Playlist",
    description="Create new playlist with scheduling configuration"
)
async def create_playlist(
    organization_id: int = Query(..., description="Organization ID"),
    playlist_data: PlaylistCreate = ...,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create new playlist.

    **Example**:
    ```json
    {
        "name": "Morning Promotions",
        "description": "Promotional content for morning hours",
        "is_active": true,
        "priority": 5,
        "schedule_mode": "inclusive",
        "schedule_start": "06:00:00",
        "schedule_end": "12:00:00",
        "schedule_days": "[\"mon\",\"tue\",\"wed\"]",
        "schedule_timezone": "Asia/Jakarta"
    }
    ```

    **Schedule Modes**:
    - `inclusive`: Add to existing content rotation
    - `exclusive`: Replace all content during schedule window
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    playlist_repo = PlaylistRepository(db)

    # Create playlist
    playlist = playlist_repo.create({
        "organization_id": organization_id,
        **playlist_data.model_dump()
    })

    playlist_dict = playlist.to_dict()
    playlist_dict["content_count"] = 0
    playlist_dict["total_duration"] = 0
    playlist_dict["device_count"] = 0

    return playlist_dict


@router.get(
    "/{playlist_id}",
    response_model=PlaylistDetailResponse,
    summary="Get Playlist Details",
    description="Get playlist information with content list"
)
async def get_playlist(
    playlist_id: int = Path(..., description="Playlist ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed playlist information including content items.

    **Returns**:
    - Playlist metadata
    - List of content items with order and duration
    - Content details (title, type, file URL)
    """
    playlist_repo = PlaylistRepository(db)
    playlist = playlist_repo.get(playlist_id)

    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Get playlist contents
    contents_data = playlist_repo.get_playlist_contents(playlist_id)

    playlist_dict = playlist.to_dict()

    # Format contents for response
    contents_list = []
    for item in contents_data:
        content = item["content"]
        contents_list.append({
            "content_id": content.id,
            "content_title": content.title,
            "content_type": content.content_type,
            "order_index": item["order_index"],
            "duration": item["duration"],
            "file_url": content.anthias_url if hasattr(content, 'anthias_url') else None
        })

    playlist_dict["contents"] = contents_list

    return playlist_dict


@router.put(
    "/{playlist_id}",
    response_model=PlaylistResponse,
    summary="Update Playlist",
    description="Update playlist metadata and schedule"
)
async def update_playlist(
    playlist_id: int = Path(..., description="Playlist ID"),
    playlist_update: PlaylistUpdate = ...,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update playlist information.

    **Updatable Fields**:
    - name
    - description
    - is_active
    - priority
    - schedule_mode
    - schedule_start / schedule_end
    - schedule_days
    - schedule_timezone
    """
    playlist_repo = PlaylistRepository(db)
    playlist = playlist_repo.get(playlist_id)

    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Build update dict
    update_data = playlist_update.model_dump(exclude_none=True)

    # Update playlist
    updated_playlist = playlist_repo.update(playlist_id, update_data)

    # Get stats
    stats = playlist_repo.get_playlist_stats(playlist_id)

    playlist_dict = updated_playlist.to_dict()
    playlist_dict["content_count"] = stats["total_contents"]
    playlist_dict["total_duration"] = stats["total_duration"]
    playlist_dict["device_count"] = stats["device_count"]

    return playlist_dict


@router.delete(
    "/{playlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Playlist",
    description="Delete playlist (cascades to assignments and content links)"
)
async def delete_playlist(
    playlist_id: int = Path(..., description="Playlist ID"),
    db: Session = Depends(get_db)
):
    """
    Delete playlist.

    **Warning**: This will also delete:
    - All playlist-content associations
    - All device assignments

    Content files themselves are NOT deleted.
    """
    playlist_repo = PlaylistRepository(db)
    playlist = playlist_repo.get(playlist_id)

    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Delete playlist (cascades to playlist_content and playlist_assignments)
    playlist_repo.delete(playlist_id)

    return None


@router.get(
    "/",
    response_model=PlaylistListResponse,
    summary="List Playlists",
    description="List organization playlists with pagination"
)
async def list_playlists(
    organization_id: int = Query(..., description="Organization ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List organization playlists.

    **Filters**:
    - is_active: Filter by active/inactive
    - search: Search in name and description

    **Sorting**: By created_at DESC (newest first)
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    playlist_repo = PlaylistRepository(db)

    # Search if query provided
    if search and len(search.strip()) >= 2:
        playlists = playlist_repo.search_playlists(organization_id, search)
        # Apply active filter if provided
        if is_active is not None:
            playlists = [p for p in playlists if p.is_active == is_active]
        # Apply pagination
        total = len(playlists)
        playlists = playlists[skip:skip+limit]
    else:
        # Get playlists by organization
        playlists = playlist_repo.get_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit
        )

        # Apply active filter if provided
        if is_active is not None:
            playlists = [p for p in playlists if p.is_active == is_active]

        # Get total count
        total = playlist_repo.count({"organization_id": organization_id})

    # Format response with stats
    playlists_list = []
    for playlist in playlists:
        stats = playlist_repo.get_playlist_stats(playlist.id)
        playlist_dict = playlist.to_dict()
        playlist_dict["content_count"] = stats["total_contents"]
        playlist_dict["total_duration"] = stats["total_duration"]
        playlist_dict["device_count"] = stats["device_count"]
        playlists_list.append(playlist_dict)

    return {
        "playlists": playlists_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get(
    "/{playlist_id}/stats",
    response_model=PlaylistStatsResponse,
    summary="Get Playlist Statistics",
    description="Get playlist statistics and content breakdown"
)
async def get_playlist_stats(
    playlist_id: int = Path(..., description="Playlist ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get playlist statistics.

    **Returns**:
    - Total content count
    - Total duration (seconds)
    - Device assignment count
    - Content type breakdown (video, image, web, etc)
    """
    playlist_repo = PlaylistRepository(db)
    playlist = playlist_repo.get(playlist_id)

    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    stats = playlist_repo.get_playlist_stats(playlist_id)

    return stats


@router.post(
    "/{playlist_id}/contents",
    response_model=PlaylistContentAddResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Content to Playlist",
    description="Add content item to playlist with optional order and duration"
)
async def add_content_to_playlist(
    playlist_id: int = Path(..., description="Playlist ID"),
    content_data: PlaylistContentAdd = ...,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Add content to playlist.

    **Parameters**:
    - `content_id`: Content ID to add (required)
    - `order_index`: Position in playlist (auto-increments if not provided)
    - `duration`: Duration in seconds (uses content default if not provided)

    **Example**:
    ```json
    {
        "content_id": 42,
        "order_index": 5,
        "duration": 15
    }
    ```
    """
    playlist_repo = PlaylistRepository(db)
    content_repo = ContentRepository(db)

    # Validate playlist exists
    playlist = playlist_repo.get(playlist_id)
    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Validate content exists
    content = content_repo.get(content_data.content_id)
    if not content:
        raise NotFoundException(
            message=f"Content {content_data.content_id} not found"
        )

    # Validate content belongs to same organization as playlist
    if content.organization_id != playlist.organization_id:
        raise BadRequestException(
            message="Content and playlist must belong to same organization"
        )

    # Add content to playlist
    playlist_content = playlist_repo.add_content_to_playlist(
        playlist_id=playlist_id,
        content_id=content_data.content_id,
        order_index=content_data.order_index,
        duration=content_data.duration
    )

    return {
        "message": "Content added to playlist",
        "playlist_id": playlist_id,
        "content_id": content_data.content_id,
        "order_index": playlist_content.order_index,
        "duration": playlist_content.duration
    }


@router.delete(
    "/{playlist_id}/contents/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Content from Playlist",
    description="Remove content item from playlist"
)
async def remove_content_from_playlist(
    playlist_id: int = Path(..., description="Playlist ID"),
    content_id: int = Path(..., description="Content ID"),
    db: Session = Depends(get_db)
):
    """
    Remove content from playlist.

    **Note**: This only removes the association. The content file itself is NOT deleted.
    """
    playlist_repo = PlaylistRepository(db)

    # Validate playlist exists
    playlist = playlist_repo.get(playlist_id)
    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Remove content from playlist
    success = playlist_repo.remove_content_from_playlist(playlist_id, content_id)

    if not success:
        raise NotFoundException(
            message=f"Content {content_id} not found in playlist {playlist_id}"
        )

    return None


@router.put(
    "/{playlist_id}/contents/reorder",
    status_code=status.HTTP_200_OK,
    summary="Reorder Playlist Content",
    description="Update the play order of content items in playlist"
)
async def reorder_playlist_content(
    playlist_id: int = Path(..., description="Playlist ID"),
    reorder_data: PlaylistContentReorder = ...,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reorder content in playlist.

    **Example**:
    ```json
    {
        "content_orders": [
            {"content_id": 5, "order_index": 1},
            {"content_id": 3, "order_index": 2},
            {"content_id": 7, "order_index": 3}
        ]
    }
    ```

    **Note**: Only content_ids included in the request will be reordered.
    Other content items maintain their original order.
    """
    playlist_repo = PlaylistRepository(db)

    # Validate playlist exists
    playlist = playlist_repo.get(playlist_id)
    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Reorder content
    success = playlist_repo.reorder_playlist_content(
        playlist_id=playlist_id,
        content_orders=reorder_data.content_orders
    )

    if not success:
        raise BadRequestException(
            message="Failed to reorder playlist content"
        )

    return {
        "message": "Playlist content reordered successfully",
        "playlist_id": playlist_id,
        "updated_count": len(reorder_data.content_orders)
    }


@router.post(
    "/{playlist_id}/assign",
    response_model=PlaylistAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign Playlist to Device",
    description="Assign playlist to a device for playback"
)
async def assign_playlist_to_device(
    playlist_id: int = Path(..., description="Playlist ID"),
    assign_data: PlaylistAssignDevice = ...,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Assign playlist to device.

    **Example**:
    ```json
    {
        "device_id": 123
    }
    ```

    **Note**: A device can have multiple playlists assigned.
    Playlists are prioritized by their `priority` field.
    """
    playlist_repo = PlaylistRepository(db)
    device_repo = DeviceRepository(db)

    # Validate playlist exists
    playlist = playlist_repo.get(playlist_id)
    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Validate device exists
    device = device_repo.get(assign_data.device_id)
    if not device:
        raise NotFoundException(
            message=f"Device {assign_data.device_id} not found"
        )

    # Validate device belongs to same organization as playlist
    if device.organization_id != playlist.organization_id:
        raise BadRequestException(
            message="Device and playlist must belong to same organization"
        )

    # Assign playlist to device
    playlist_repo.assign_to_device(
        playlist_id=playlist_id,
        device_id=assign_data.device_id
    )

    return {
        "message": "Playlist assigned to device",
        "playlist_id": playlist_id,
        "device_id": assign_data.device_id
    }


@router.delete(
    "/{playlist_id}/assign/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unassign Playlist from Device",
    description="Remove playlist assignment from device"
)
async def unassign_playlist_from_device(
    playlist_id: int = Path(..., description="Playlist ID"),
    device_id: int = Path(..., description="Device ID"),
    db: Session = Depends(get_db)
):
    """
    Unassign playlist from device.

    **Note**: This removes the assignment but does not delete the playlist or device.
    """
    playlist_repo = PlaylistRepository(db)

    # Validate playlist exists
    playlist = playlist_repo.get(playlist_id)
    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Unassign playlist from device
    success = playlist_repo.unassign_from_device(playlist_id, device_id)

    if not success:
        raise NotFoundException(
            message=f"Playlist {playlist_id} is not assigned to device {device_id}"
        )

    return None


@router.get(
    "/devices/{device_id}/playlists",
    response_model=DevicePlaylistResponse,
    summary="Get Device's Playlists",
    description="Get all playlists assigned to a device"
)
async def get_device_playlists(
    device_id: int = Path(..., description="Device ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all playlists assigned to a device.

    **Returns**:
    - List of playlists with stats
    - Ordered by priority (highest first)
    """
    device_repo = DeviceRepository(db)
    playlist_repo = PlaylistRepository(db)

    # Validate device exists
    device = device_repo.get(device_id)
    if not device:
        raise NotFoundException(
            message=f"Device {device_id} not found"
        )

    # Get device's playlists
    playlists = playlist_repo.get_device_playlists(device_id)

    # Format response with stats
    playlists_list = []
    for playlist in playlists:
        stats = playlist_repo.get_playlist_stats(playlist.id)
        playlist_dict = playlist.to_dict()
        playlist_dict["content_count"] = stats["total_contents"]
        playlist_dict["total_duration"] = stats["total_duration"]
        playlist_dict["device_count"] = stats["device_count"]
        playlists_list.append(playlist_dict)

    return {
        "device_id": device_id,
        "playlists": playlists_list,
        "total": len(playlists_list)
    }


@router.post(
    "/{playlist_id}/duplicate",
    response_model=PlaylistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate Playlist",
    description="Create a copy of playlist with all its content"
)
async def duplicate_playlist(
    playlist_id: int = Path(..., description="Playlist ID"),
    duplicate_data: PlaylistDuplicate = ...,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Duplicate a playlist.

    **Parameters**:
    - `new_name`: Name for the new playlist
    - `copy_assignments`: Whether to copy device assignments (default: false)

    **Example**:
    ```json
    {
        "new_name": "Morning Promotions (Copy)",
        "copy_assignments": true
    }
    ```

    **Copies**:
    - Playlist metadata (name, schedule, priority)
    - All content items with order and duration
    - Optionally: device assignments
    """
    playlist_repo = PlaylistRepository(db)

    # Validate playlist exists
    playlist = playlist_repo.get(playlist_id)
    if not playlist:
        raise NotFoundException(
            message=f"Playlist {playlist_id} not found"
        )

    # Duplicate playlist
    try:
        new_playlist = playlist_repo.duplicate_playlist(
            playlist_id=playlist_id,
            new_name=duplicate_data.new_name,
            copy_assignments=duplicate_data.copy_assignments
        )
    except ValueError as e:
        raise NotFoundException(message=str(e))

    # Get stats for new playlist
    stats = playlist_repo.get_playlist_stats(new_playlist.id)

    playlist_dict = new_playlist.to_dict()
    playlist_dict["content_count"] = stats["total_contents"]
    playlist_dict["total_duration"] = stats["total_duration"]
    playlist_dict["device_count"] = stats["device_count"]

    return playlist_dict
