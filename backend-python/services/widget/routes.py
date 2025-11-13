"""
Widget Routes
FastAPI endpoints for widget management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser

from services.widget.dtos import (
    CreateWidgetRequest,
    UpdateWidgetRequest,
    WidgetResponse,
    WidgetListResponse,
    AssignWidgetToPlaylistRequest,
    UpdatePlaylistWidgetRequest,
    PlaylistWidgetResponse,
    PlaylistWidgetListResponse
)
from services.widget.use_cases.create_widget import create_widget_use_case
from services.widget.use_cases.get_widgets import (
    get_widget_by_id_use_case,
    get_widgets_use_case
)
from services.widget.use_cases.update_widget import (
    update_widget_use_case,
    delete_widget_use_case
)
from services.widget.use_cases.assign_widget_to_playlist import (
    assign_widget_to_playlist_use_case,
    get_playlist_widgets_use_case,
    update_playlist_widget_use_case,
    remove_widget_from_playlist_use_case
)

router = APIRouter(prefix="/widgets", tags=["widgets"])


# ============================================================================
# Widget Endpoints
# ============================================================================

@router.post("", response_model=WidgetResponse, status_code=201)
def create_widget(
    request: CreateWidgetRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new widget

    Permissions: admin, manager
    """
    return create_widget_use_case(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        request=request,
        db=db
    )


@router.get("", response_model=WidgetListResponse)
def get_widgets(
    widget_type: Optional[str] = Query(None, description="Filter by widget type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all widgets for current organization

    Filters:
    - widget_type: clock, weather, news, hotel_info, custom
    - is_active: true/false
    """
    return get_widgets_use_case(
        organization_id=current_user.organization_id,
        widget_type=widget_type,
        is_active=is_active,
        skip=skip,
        limit=limit,
        db=db
    )


@router.get("/{widget_id}", response_model=WidgetResponse)
def get_widget(
    widget_id: int = Path(..., description="Widget ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get widget by ID"""
    return get_widget_by_id_use_case(
        widget_id=widget_id,
        organization_id=current_user.organization_id,
        db=db
    )


@router.put("/{widget_id}", response_model=WidgetResponse)
def update_widget(
    widget_id: int = Path(..., description="Widget ID"),
    request: UpdateWidgetRequest = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update widget

    Permissions: admin, manager
    """
    return update_widget_use_case(
        widget_id=widget_id,
        organization_id=current_user.organization_id,
        request=request,
        db=db
    )


@router.delete("/{widget_id}")
def delete_widget(
    widget_id: int = Path(..., description="Widget ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete widget

    Permissions: admin, manager
    Note: Will cascade delete from playlists
    """
    return delete_widget_use_case(
        widget_id=widget_id,
        organization_id=current_user.organization_id,
        db=db
    )


# ============================================================================
# Playlist Widget Endpoints
# ============================================================================

@router.post("/playlists/{playlist_id}/widgets", response_model=PlaylistWidgetResponse, status_code=201)
def assign_widget_to_playlist(
    playlist_id: int = Path(..., description="Playlist ID"),
    request: AssignWidgetToPlaylistRequest = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign widget to playlist

    Permissions: admin, manager
    """
    return assign_widget_to_playlist_use_case(
        playlist_id=playlist_id,
        organization_id=current_user.organization_id,
        request=request,
        db=db
    )


@router.get("/playlists/{playlist_id}/widgets", response_model=PlaylistWidgetListResponse)
def get_playlist_widgets(
    playlist_id: int = Path(..., description="Playlist ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all widgets assigned to playlist"""
    return get_playlist_widgets_use_case(
        playlist_id=playlist_id,
        db=db
    )


@router.put("/playlist-widgets/{playlist_widget_id}", response_model=PlaylistWidgetResponse)
def update_playlist_widget(
    playlist_widget_id: int = Path(..., description="Playlist Widget ID"),
    request: UpdatePlaylistWidgetRequest = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update playlist widget settings (position, duration, z-index)

    Permissions: admin, manager
    """
    return update_playlist_widget_use_case(
        playlist_widget_id=playlist_widget_id,
        request=request,
        db=db
    )


@router.delete("/playlists/{playlist_id}/widgets/{widget_id}")
def remove_widget_from_playlist(
    playlist_id: int = Path(..., description="Playlist ID"),
    widget_id: int = Path(..., description="Widget ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove widget from playlist

    Permissions: admin, manager
    """
    return remove_widget_from_playlist_use_case(
        playlist_id=playlist_id,
        widget_id=widget_id,
        db=db
    )
