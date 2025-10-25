"""
Playlists API endpoints
For managing content playlists and scheduling
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
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

router = APIRouter()


@router.get("", response_model=PlaylistListResponse)
def list_playlists(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all playlists with content counts
    """
    playlists = db.query(Playlist).order_by(Playlist.created_at.desc()).all()

    # Add content count and total duration for each playlist
    playlist_responses = []
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

    return PlaylistListResponse(
        total=len(playlist_responses),
        items=playlist_responses
    )


@router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(
    playlist_data: PlaylistCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Create a new playlist
    """
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

    db.add(playlist)
    db.commit()
    db.refresh(playlist)

    playlist_dict = playlist.to_dict()
    playlist_dict['content_count'] = 0
    playlist_dict['total_duration'] = 0

    return PlaylistResponse(**playlist_dict)


@router.get("/{playlist_id}", response_model=PlaylistResponse)
def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a single playlist by ID
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
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

    return PlaylistResponse(**playlist_dict)


@router.patch("/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(
    playlist_id: int,
    playlist_data: PlaylistUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update a playlist
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
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

    return PlaylistResponse(**playlist_dict)


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete a playlist
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
        )

    db.delete(playlist)
    db.commit()

    return None


# ==================== Content Management ====================

@router.get("/{playlist_id}/content", response_model=PlaylistContentResponse)
def get_playlist_content(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all content items in a playlist
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
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

    return PlaylistContentResponse(
        total=len(content_items),
        items=content_items
    )


@router.post("/{playlist_id}/content", status_code=status.HTTP_201_CREATED)
def add_content_to_playlist(
    playlist_id: int,
    content_data: PlaylistContentAdd,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Add content to a playlist
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
        )

    # Get current max order_index
    max_order = db.query(func.max(PlaylistContent.order_index)).filter(
        PlaylistContent.playlist_id == playlist_id
    ).scalar() or -1

    added_count = 0
    for content_id in content_data.content_ids:
        # Check if content exists
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            continue

        # Check if already in playlist
        existing = db.query(PlaylistContent).filter(
            PlaylistContent.playlist_id == playlist_id,
            PlaylistContent.content_id == content_id
        ).first()
        if existing:
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

    return {"message": f"Added {added_count} content item(s) to playlist"}


@router.delete("/{playlist_id}/content/{content_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_content_from_playlist(
    playlist_id: int,
    content_item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove content from a playlist
    """
    playlist_content = db.query(PlaylistContent).filter(
        PlaylistContent.id == content_item_id,
        PlaylistContent.playlist_id == playlist_id
    ).first()

    if not playlist_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found in playlist"
        )

    db.delete(playlist_content)
    db.commit()

    return None


@router.patch("/{playlist_id}/reorder")
def reorder_playlist_content(
    playlist_id: int,
    reorder_data: PlaylistContentReorder,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Reorder and update duration of content in a playlist
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
        )

    # Update order and duration for each item
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

    db.commit()

    return {"message": "Playlist content reordered successfully"}


# ==================== Assignment Management ====================

@router.get("/{playlist_id}/assignments", response_model=PlaylistAssignmentResponse)
def get_playlist_assignments(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all device and tag assignments for a playlist
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
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

    return PlaylistAssignmentResponse(
        devices=device_list,
        tags=tag_list
    )


@router.post("/{playlist_id}/assign/devices", status_code=status.HTTP_201_CREATED)
def assign_playlist_to_devices(
    playlist_id: int,
    assignment_data: PlaylistDeviceAssign,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Assign a playlist to devices
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
        )

    assigned_count = 0
    for device_id in assignment_data.device_ids:
        # Check if device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            continue

        # Check if already assigned
        existing = db.query(PlaylistAssignment).filter(
            PlaylistAssignment.playlist_id == playlist_id,
            PlaylistAssignment.device_id == device_id
        ).first()
        if existing:
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

    return {"message": f"Playlist assigned to {assigned_count} device(s)"}


@router.post("/{playlist_id}/assign/tags", status_code=status.HTTP_201_CREATED)
def assign_playlist_to_tags(
    playlist_id: int,
    assignment_data: PlaylistTagAssign,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Assign a playlist to tags
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID {playlist_id} not found"
        )

    assigned_count = 0
    for tag_id in assignment_data.tag_ids:
        # Check if tag exists
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            continue

        # Check if already assigned
        existing = db.query(PlaylistAssignment).filter(
            PlaylistAssignment.playlist_id == playlist_id,
            PlaylistAssignment.tag_id == tag_id
        ).first()
        if existing:
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

    return {"message": f"Playlist assigned to {assigned_count} tag(s)"}


@router.delete("/{playlist_id}/assign/devices", status_code=status.HTTP_204_NO_CONTENT)
def unassign_playlist_from_devices(
    playlist_id: int,
    assignment_data: PlaylistDeviceAssign,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove playlist assignment from devices
    """
    for device_id in assignment_data.device_ids:
        assignment = db.query(PlaylistAssignment).filter(
            PlaylistAssignment.playlist_id == playlist_id,
            PlaylistAssignment.device_id == device_id
        ).first()

        if assignment:
            db.delete(assignment)

    db.commit()

    return None


@router.delete("/{playlist_id}/assign/tags", status_code=status.HTTP_204_NO_CONTENT)
def unassign_playlist_from_tags(
    playlist_id: int,
    assignment_data: PlaylistTagAssign,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove playlist assignment from tags
    """
    for tag_id in assignment_data.tag_ids:
        assignment = db.query(PlaylistAssignment).filter(
            PlaylistAssignment.playlist_id == playlist_id,
            PlaylistAssignment.tag_id == tag_id
        ).first()

        if assignment:
            db.delete(assignment)

    db.commit()

    return None
