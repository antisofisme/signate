"""
Playlists API endpoints
For managing content playlists and scheduling

MIGRATED TO QUICK WINS STANDARDS:
- Structured logging with StructuredLogger
- Custom exceptions (NotFoundException, BadRequestException)
- Standardized success_response wrapper
- Request ID tracking
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response
from app.models.user import User
from app.models.playlist import Playlist, PlaylistContent, PlaylistAssignment
from app.models.content import Content
from app.models.device import Device
from app.models.tag import Tag
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistListResponse,
    PlaylistContentResponse,
    PlaylistContentItem,
    PlaylistContentAdd,
    PlaylistContentReorder,
    PlaylistDeviceAssign,
    PlaylistTagAssign,
    PlaylistAssignmentResponse
)

logger = StructuredLogger(__name__)
router = APIRouter()


# =============================================================================
# PLAYLIST CRUD ENDPOINTS (5 endpoints)
# =============================================================================

@router.get("")
def list_playlists(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all playlists with content counts and total duration
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing all playlists",
        request_id=request_id
    )

    # Filter by organization_id if user is authenticated
    query = db.query(Playlist)
    if current_user and hasattr(current_user, 'current_organization_id'):
        query = query.filter(Playlist.organization_id == current_user.current_organization_id)

    playlists = query.order_by(Playlist.created_at.desc()).all()

    # Add content count and total duration for each playlist
    playlist_responses = []
    total_calculated_duration = 0

    for playlist in playlists:
        content_count = db.query(func.count(PlaylistContent.id)).filter(
            PlaylistContent.playlist_id == playlist.id
        ).scalar()

        # Calculate total duration
        content_items = db.query(PlaylistContent).filter(
            PlaylistContent.playlist_id == playlist.id
        ).all()

        total_duration = 0
        for item in content_items:
            if item.duration:
                total_duration += item.duration
            else:
                # Use content's default duration
                content = db.query(Content).filter(Content.id == item.content_id).first()
                if content and content.duration:
                    total_duration += content.duration

        playlist_dict = playlist.to_dict()
        playlist_dict['content_count'] = content_count or 0
        playlist_dict['total_duration'] = total_duration
        playlist_responses.append(PlaylistResponse(**playlist_dict))
        total_calculated_duration += total_duration

    logger.info(
        "Playlists listed successfully",
        request_id=request_id,
        total_playlists=len(playlist_responses),
        total_duration_calculated=total_calculated_duration
    )

    return success_response(
        data={
            "total": len(playlist_responses),
            "items": [p.model_dump() for p in playlist_responses]
        },
        request_id=request_id
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_playlist(
    playlist_data: PlaylistCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Create a new playlist
    """
    request_id = get_request_id(request)

    logger.info(
        "Creating new playlist",
        request_id=request_id,
        playlist_name=playlist_data.name,
        is_active=playlist_data.is_active,
        priority=playlist_data.priority
    )

    # Convert schedule to dict if it's a Pydantic model
    schedule_dict = None
    if playlist_data.schedule:
        schedule_dict = playlist_data.schedule.model_dump() if hasattr(playlist_data.schedule, 'model_dump') else playlist_data.schedule

    playlist = Playlist(
        name=playlist_data.name,
        description=playlist_data.description,
        is_active=playlist_data.is_active,
        priority=playlist_data.priority,
        schedule=schedule_dict
    )

    # Set organization_id and created_by if user is authenticated
    if current_user:
        if hasattr(current_user, 'current_organization_id'):
            playlist.organization_id = current_user.current_organization_id
        else:
            # Fallback for backward compatibility
            playlist.organization_id = 1
        playlist.created_by = current_user.id

    db.add(playlist)
    db.commit()
    db.refresh(playlist)

    playlist_dict = playlist.to_dict()
    playlist_dict['content_count'] = 0
    playlist_dict['total_duration'] = 0

    logger.info(
        "Playlist created successfully",
        request_id=request_id,
        playlist_id=playlist.id,
        playlist_name=playlist.name
    )

    return success_response(
        data=playlist_dict,
        request_id=request_id
    )


@router.get("/{playlist_id}")
def get_playlist(
    playlist_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a single playlist by ID with content count and total duration
    """
    request_id = get_request_id(request)

    logger.info(
        "Retrieving playlist",
        request_id=request_id,
        playlist_id=playlist_id
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not playlist:
        logger.warning(
            "Playlist not found",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    content_count = db.query(PlaylistContent).filter(
        PlaylistContent.playlist_id == playlist.id
    ).count()

    # Calculate total duration
    content_items = db.query(PlaylistContent).filter(
        PlaylistContent.playlist_id == playlist.id
    ).all()

    total_duration = 0
    for item in content_items:
        if item.duration:
            total_duration += item.duration
        else:
            content = db.query(Content).filter(Content.id == item.content_id).first()
            if content and content.duration:
                total_duration += content.duration

    playlist_dict = playlist.to_dict()
    playlist_dict['content_count'] = content_count
    playlist_dict['total_duration'] = total_duration

    logger.info(
        "Playlist retrieved successfully",
        request_id=request_id,
        playlist_id=playlist.id,
        playlist_name=playlist.name,
        content_count=content_count,
        total_duration=total_duration
    )

    return success_response(
        data=playlist_dict,
        request_id=request_id
    )


@router.patch("/{playlist_id}")
def update_playlist(
    playlist_id: int,
    playlist_data: PlaylistUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update a playlist
    """
    request_id = get_request_id(request)

    logger.info(
        "Updating playlist",
        request_id=request_id,
        playlist_id=playlist_id,
        update_fields={
            "name": playlist_data.name,
            "is_active": playlist_data.is_active,
            "priority": playlist_data.priority
        }
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not playlist:
        logger.warning(
            "Playlist not found for update",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    # Update fields
    if playlist_data.name is not None:
        playlist.name = playlist_data.name
    if playlist_data.description is not None:
        playlist.description = playlist_data.description
    if playlist_data.is_active is not None:
        playlist.is_active = playlist_data.is_active
    if playlist_data.priority is not None:
        playlist.priority = playlist_data.priority
    if playlist_data.schedule is not None:
        # Convert schedule to dict if it's a Pydantic model
        schedule_dict = playlist_data.schedule
        if hasattr(playlist_data.schedule, 'model_dump'):
            schedule_dict = playlist_data.schedule.model_dump()
        playlist.schedule = schedule_dict

    db.commit()
    db.refresh(playlist)

    content_count = db.query(PlaylistContent).filter(
        PlaylistContent.playlist_id == playlist.id
    ).count()

    # Calculate total duration
    content_items = db.query(PlaylistContent).filter(
        PlaylistContent.playlist_id == playlist.id
    ).all()

    total_duration = 0
    for item in content_items:
        if item.duration:
            total_duration += item.duration
        else:
            content = db.query(Content).filter(Content.id == item.content_id).first()
            if content and content.duration:
                total_duration += content.duration

    playlist_dict = playlist.to_dict()
    playlist_dict['content_count'] = content_count
    playlist_dict['total_duration'] = total_duration

    logger.info(
        "Playlist updated successfully",
        request_id=request_id,
        playlist_id=playlist.id,
        playlist_name=playlist.name,
        content_count=content_count
    )

    return success_response(
        data=playlist_dict,
        request_id=request_id
    )


@router.delete("/{playlist_id}")
def delete_playlist(
    playlist_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete a playlist (cascades to content items and assignments)
    """
    request_id = get_request_id(request)

    logger.info(
        "Deleting playlist",
        request_id=request_id,
        playlist_id=playlist_id
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not playlist:
        logger.warning(
            "Playlist not found for deletion",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    playlist_name = playlist.name
    db.delete(playlist)
    db.commit()

    logger.info(
        "Playlist deleted successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        playlist_name=playlist_name
    )

    return success_response(
        data={"message": f"Playlist '{playlist_name}' deleted successfully"},
        request_id=request_id
    )


# =============================================================================
# CONTENT MANAGEMENT ENDPOINTS (4 endpoints)
# =============================================================================

@router.get("/{playlist_id}/content")
def get_playlist_content(
    playlist_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all content items in a playlist with content details
    """
    request_id = get_request_id(request)

    logger.info(
        "Retrieving playlist content",
        request_id=request_id,
        playlist_id=playlist_id
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        logger.warning(
            "Playlist not found",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    playlist_items = db.query(PlaylistContent).filter(
        PlaylistContent.playlist_id == playlist_id
    ).order_by(PlaylistContent.order_index).all()

    content_items = []
    for item in playlist_items:
        content = db.query(Content).filter(Content.id == item.content_id).first()
        if content:
            content_items.append(PlaylistContentItem(
                id=item.id,
                content_id=item.content_id,
                content_name=content.title,
                content_type=content.content_type,
                order_index=item.order_index,
                duration=item.duration if item.duration else content.duration,
                created_at=item.created_at
            ))

    logger.info(
        "Playlist content retrieved successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        content_items_count=len(content_items)
    )

    return success_response(
        data={
            "total": len(content_items),
            "items": [item.model_dump() for item in content_items]
        },
        request_id=request_id
    )


@router.post("/{playlist_id}/content", status_code=status.HTTP_201_CREATED)
def add_content_to_playlist(
    playlist_id: int,
    content_data: PlaylistContentAdd,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Add content items to playlist (bulk add with content_ids list)
    Sets display_order automatically
    """
    request_id = get_request_id(request)

    logger.info(
        "Adding content to playlist",
        request_id=request_id,
        playlist_id=playlist_id,
        content_ids=content_data.content_ids,
        content_ids_count=len(content_data.content_ids)
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        logger.warning(
            "Playlist not found",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    # Get current max order_index
    max_order = db.query(func.max(PlaylistContent.order_index)).filter(
        PlaylistContent.playlist_id == playlist_id
    ).scalar() or -1

    added_count = 0
    skipped_missing = []
    skipped_duplicate = []

    for content_id in content_data.content_ids:
        # Check if content exists
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            skipped_missing.append(content_id)
            continue

        # Check if already in playlist
        existing = db.query(PlaylistContent).filter(
            PlaylistContent.playlist_id == playlist_id,
            PlaylistContent.content_id == content_id
        ).first()
        if existing:
            skipped_duplicate.append(content_id)
            continue

        # Add to playlist
        max_order += 1
        playlist_content = PlaylistContent(
            playlist_id=playlist_id,
            content_id=content_id,
            order_index=max_order,
            duration=content.duration  # Use content's default duration
        )
        db.add(playlist_content)
        added_count += 1

    db.commit()

    # Log warnings if some items were skipped
    if skipped_missing:
        logger.warning(
            "Some content items not found",
            request_id=request_id,
            playlist_id=playlist_id,
            missing_content_ids=skipped_missing
        )

    if skipped_duplicate:
        logger.warning(
            "Some content items already in playlist",
            request_id=request_id,
            playlist_id=playlist_id,
            duplicate_content_ids=skipped_duplicate
        )

    logger.info(
        "Content added to playlist successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        added_count=added_count,
        skipped_missing_count=len(skipped_missing),
        skipped_duplicate_count=len(skipped_duplicate)
    )

    return success_response(
        data={
            "message": f"Added {added_count} content item(s) to playlist",
            "added_count": added_count,
            "skipped_missing": skipped_missing,
            "skipped_duplicate": skipped_duplicate
        },
        request_id=request_id
    )


@router.delete("/{playlist_id}/content/{content_item_id}")
def remove_content_from_playlist(
    playlist_id: int,
    content_item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove content item from playlist
    """
    request_id = get_request_id(request)

    logger.info(
        "Removing content from playlist",
        request_id=request_id,
        playlist_id=playlist_id,
        content_item_id=content_item_id
    )

    playlist_content = db.query(PlaylistContent).filter(
        PlaylistContent.id == content_item_id,
        PlaylistContent.playlist_id == playlist_id
    ).first()

    if not playlist_content:
        logger.warning(
            "Content not found in playlist",
            request_id=request_id,
            playlist_id=playlist_id,
            content_item_id=content_item_id
        )
        raise NotFoundException(
            message="Content not found in playlist",
            resource_type="PlaylistContent",
            resource_id=content_item_id
        )

    content_id = playlist_content.content_id
    db.delete(playlist_content)
    db.commit()

    logger.info(
        "Content removed from playlist successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        content_item_id=content_item_id,
        content_id=content_id
    )

    return success_response(
        data={"message": "Content removed from playlist successfully"},
        request_id=request_id
    )


@router.patch("/{playlist_id}/reorder")
def reorder_playlist_content(
    playlist_id: int,
    reorder_data: PlaylistContentReorder,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Reorder and update duration of content in a playlist
    Bulk update display_order for content items
    """
    request_id = get_request_id(request)

    logger.info(
        "Reordering playlist content",
        request_id=request_id,
        playlist_id=playlist_id,
        items_to_reorder=len(reorder_data.content_items)
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        logger.warning(
            "Playlist not found for reorder",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    # Update order and duration for each item
    updated_count = 0
    for item_data in reorder_data.content_items:
        playlist_content = db.query(PlaylistContent).filter(
            PlaylistContent.id == item_data.get('id'),
            PlaylistContent.playlist_id == playlist_id
        ).first()

        if playlist_content:
            if 'order_index' in item_data:
                playlist_content.order_index = item_data['order_index']
            if 'duration' in item_data:
                playlist_content.duration = item_data['duration']
            updated_count += 1

    db.commit()

    logger.info(
        "Playlist content reordered successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        updated_count=updated_count
    )

    return success_response(
        data={
            "message": "Playlist content reordered successfully",
            "updated_count": updated_count
        },
        request_id=request_id
    )


# =============================================================================
# ASSIGNMENT MANAGEMENT ENDPOINTS (5 endpoints)
# =============================================================================

@router.get("/{playlist_id}/assignments")
def get_playlist_assignments(
    playlist_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all device and tag assignments for a playlist
    Complex query: device assignments + tag assignments
    """
    request_id = get_request_id(request)

    logger.info(
        "Retrieving playlist assignments",
        request_id=request_id,
        playlist_id=playlist_id
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        logger.warning(
            "Playlist not found",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    # Get all assignments
    assignments = db.query(PlaylistAssignment).filter(
        PlaylistAssignment.playlist_id == playlist_id
    ).all()

    # Get assigned devices
    device_assignments = [a for a in assignments if a.device_id]
    device_ids = [a.device_id for a in device_assignments]
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all() if device_ids else []
    device_list = [device.to_dict() for device in devices]

    # Get assigned tags
    tag_assignments = [a for a in assignments if a.tag_id]
    tag_ids = [a.tag_id for a in tag_assignments]
    tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all() if tag_ids else []
    tag_list = [tag.to_dict() for tag in tags]

    logger.info(
        "Playlist assignments retrieved successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        device_count=len(device_list),
        tag_count=len(tag_list)
    )

    return success_response(
        data={
            "devices": device_list,
            "tags": tag_list
        },
        request_id=request_id
    )


@router.post("/{playlist_id}/assign/devices", status_code=status.HTTP_201_CREATED)
def assign_playlist_to_devices(
    playlist_id: int,
    assignment_data: PlaylistDeviceAssign,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Assign playlist to multiple devices (bulk assign with device_ids list)
    Validation: playlist exists, all devices exist, no duplicates
    """
    request_id = get_request_id(request)

    logger.info(
        "Assigning playlist to devices",
        request_id=request_id,
        playlist_id=playlist_id,
        device_ids=assignment_data.device_ids,
        device_ids_count=len(assignment_data.device_ids)
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        logger.warning(
            "Playlist not found for device assignment",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    assigned_count = 0
    skipped_missing = []
    skipped_duplicate = []

    for device_id in assignment_data.device_ids:
        # Check if device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            skipped_missing.append(device_id)
            continue

        # Check if already assigned
        existing = db.query(PlaylistAssignment).filter(
            PlaylistAssignment.playlist_id == playlist_id,
            PlaylistAssignment.device_id == device_id
        ).first()
        if existing:
            skipped_duplicate.append(device_id)
            continue

        # Create assignment
        assignment = PlaylistAssignment(
            playlist_id=playlist_id,
            device_id=device_id,
            tag_id=None
        )
        db.add(assignment)
        assigned_count += 1

    db.commit()

    # Log warnings if some items were skipped
    if skipped_missing:
        logger.warning(
            "Some devices not found",
            request_id=request_id,
            playlist_id=playlist_id,
            missing_device_ids=skipped_missing
        )

    if skipped_duplicate:
        logger.warning(
            "Some devices already assigned",
            request_id=request_id,
            playlist_id=playlist_id,
            duplicate_device_ids=skipped_duplicate
        )

    logger.info(
        "Playlist assigned to devices successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        assigned_count=assigned_count,
        skipped_missing_count=len(skipped_missing),
        skipped_duplicate_count=len(skipped_duplicate)
    )

    return success_response(
        data={
            "message": f"Playlist assigned to {assigned_count} device(s)",
            "assigned_count": assigned_count,
            "skipped_missing": skipped_missing,
            "skipped_duplicate": skipped_duplicate
        },
        request_id=request_id
    )


@router.post("/{playlist_id}/assign/tags", status_code=status.HTTP_201_CREATED)
def assign_playlist_to_tags(
    playlist_id: int,
    assignment_data: PlaylistTagAssign,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Assign playlist to multiple tags (bulk assign with tag_ids list)
    Validation: playlist exists, all tags exist, no duplicates
    """
    request_id = get_request_id(request)

    logger.info(
        "Assigning playlist to tags",
        request_id=request_id,
        playlist_id=playlist_id,
        tag_ids=assignment_data.tag_ids,
        tag_ids_count=len(assignment_data.tag_ids)
    )

    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        logger.warning(
            "Playlist not found for tag assignment",
            request_id=request_id,
            playlist_id=playlist_id
        )
        raise NotFoundException(
            message=f"Playlist with ID {playlist_id} not found",
            resource_type="Playlist",
            resource_id=playlist_id
        )

    assigned_count = 0
    skipped_missing = []
    skipped_duplicate = []

    for tag_id in assignment_data.tag_ids:
        # Check if tag exists
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            skipped_missing.append(tag_id)
            continue

        # Check if already assigned
        existing = db.query(PlaylistAssignment).filter(
            PlaylistAssignment.playlist_id == playlist_id,
            PlaylistAssignment.tag_id == tag_id
        ).first()
        if existing:
            skipped_duplicate.append(tag_id)
            continue

        # Create assignment
        assignment = PlaylistAssignment(
            playlist_id=playlist_id,
            device_id=None,
            tag_id=tag_id
        )
        db.add(assignment)
        assigned_count += 1

    db.commit()

    # Log warnings if some items were skipped
    if skipped_missing:
        logger.warning(
            "Some tags not found",
            request_id=request_id,
            playlist_id=playlist_id,
            missing_tag_ids=skipped_missing
        )

    if skipped_duplicate:
        logger.warning(
            "Some tags already assigned",
            request_id=request_id,
            playlist_id=playlist_id,
            duplicate_tag_ids=skipped_duplicate
        )

    logger.info(
        "Playlist assigned to tags successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        assigned_count=assigned_count,
        skipped_missing_count=len(skipped_missing),
        skipped_duplicate_count=len(skipped_duplicate)
    )

    return success_response(
        data={
            "message": f"Playlist assigned to {assigned_count} tag(s)",
            "assigned_count": assigned_count,
            "skipped_missing": skipped_missing,
            "skipped_duplicate": skipped_duplicate
        },
        request_id=request_id
    )


@router.delete("/{playlist_id}/assign/devices")
def unassign_playlist_from_devices(
    playlist_id: int,
    assignment_data: PlaylistDeviceAssign,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove playlist assignment from devices (bulk unassign with device_ids list)
    """
    request_id = get_request_id(request)

    logger.info(
        "Unassigning playlist from devices",
        request_id=request_id,
        playlist_id=playlist_id,
        device_ids=assignment_data.device_ids,
        device_ids_count=len(assignment_data.device_ids)
    )

    removed_count = 0
    for device_id in assignment_data.device_ids:
        assignment = db.query(PlaylistAssignment).filter(
            PlaylistAssignment.playlist_id == playlist_id,
            PlaylistAssignment.device_id == device_id
        ).first()

        if assignment:
            db.delete(assignment)
            removed_count += 1

    db.commit()

    logger.info(
        "Playlist unassigned from devices successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        removed_count=removed_count
    )

    return success_response(
        data={
            "message": f"Playlist unassigned from {removed_count} device(s)",
            "removed_count": removed_count
        },
        request_id=request_id
    )


@router.delete("/{playlist_id}/assign/tags")
def unassign_playlist_from_tags(
    playlist_id: int,
    assignment_data: PlaylistTagAssign,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove playlist assignment from tags (bulk unassign with tag_ids list)
    """
    request_id = get_request_id(request)

    logger.info(
        "Unassigning playlist from tags",
        request_id=request_id,
        playlist_id=playlist_id,
        tag_ids=assignment_data.tag_ids,
        tag_ids_count=len(assignment_data.tag_ids)
    )

    removed_count = 0
    for tag_id in assignment_data.tag_ids:
        assignment = db.query(PlaylistAssignment).filter(
            PlaylistAssignment.playlist_id == playlist_id,
            PlaylistAssignment.tag_id == tag_id
        ).first()

        if assignment:
            db.delete(assignment)
            removed_count += 1

    db.commit()

    logger.info(
        "Playlist unassigned from tags successfully",
        request_id=request_id,
        playlist_id=playlist_id,
        removed_count=removed_count
    )

    return success_response(
        data={
            "message": f"Playlist unassigned from {removed_count} tag(s)",
            "removed_count": removed_count
        },
        request_id=request_id
    )
