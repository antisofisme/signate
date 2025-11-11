"""
Assign Widget to Playlist Use Case
Business logic for assigning widgets to playlists
"""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.widget.dtos import (
    AssignWidgetToPlaylistRequest,
    UpdatePlaylistWidgetRequest,
    PlaylistWidgetResponse,
    PlaylistWidgetListResponse
)
from services.widget.repositories.widget_repo import WidgetRepository


def assign_widget_to_playlist_use_case(
    playlist_id: int,
    organization_id: int,
    request: AssignWidgetToPlaylistRequest,
    db: Session
) -> PlaylistWidgetResponse:
    """
    Assign widget to playlist

    Business Rules:
    - Widget must exist and belong to same organization as playlist
    - Widget cannot be assigned to same playlist twice
    - Playlist must exist and belong to organization (checked in routes)
    """
    repo = WidgetRepository(db)

    # Check if widget exists and belongs to organization
    widget = repo.get_widget_by_id(request.widget_id, organization_id)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Widget with id {request.widget_id} not found"
        )

    # Check if widget is already assigned to this playlist
    if repo.check_widget_assigned(playlist_id, request.widget_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Widget {request.widget_id} is already assigned to playlist {playlist_id}"
        )

    # Assign widget to playlist
    playlist_widget = repo.assign_widget_to_playlist(playlist_id, request)

    # Load widget details for response
    response = PlaylistWidgetResponse.model_validate(playlist_widget)
    response.widget = widget  # Attach widget details

    return response


def get_playlist_widgets_use_case(
    playlist_id: int,
    db: Session
) -> PlaylistWidgetListResponse:
    """Get all widgets assigned to playlist"""
    repo = WidgetRepository(db)

    playlist_widgets = repo.get_playlist_widgets(playlist_id)

    # Build response with widget details
    responses: List[PlaylistWidgetResponse] = []
    for pw in playlist_widgets:
        response = PlaylistWidgetResponse.model_validate(pw)
        # Load widget details
        widget = repo.get_widget_by_id(pw.widget_id, organization_id=None)  # Already filtered
        if widget:
            from services.widget.dtos import WidgetResponse
            response.widget = WidgetResponse.model_validate(widget)
        responses.append(response)

    return PlaylistWidgetListResponse(
        playlist_widgets=responses,
        total=len(responses)
    )


def update_playlist_widget_use_case(
    playlist_widget_id: int,
    request: UpdatePlaylistWidgetRequest,
    db: Session
) -> PlaylistWidgetResponse:
    """Update playlist widget settings"""
    repo = WidgetRepository(db)

    playlist_widget = repo.get_playlist_widget(playlist_widget_id)
    if not playlist_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist widget with id {playlist_widget_id} not found"
        )

    # Update settings
    updated = repo.update_playlist_widget(playlist_widget_id, request)

    return PlaylistWidgetResponse.model_validate(updated)


def remove_widget_from_playlist_use_case(
    playlist_id: int,
    widget_id: int,
    db: Session
) -> dict:
    """Remove widget from playlist"""
    repo = WidgetRepository(db)

    success = repo.remove_widget_from_playlist(playlist_id, widget_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Widget {widget_id} not found in playlist {playlist_id}"
        )

    return {"message": f"Widget {widget_id} removed from playlist {playlist_id}"}
