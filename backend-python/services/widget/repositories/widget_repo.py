"""
Widget Repository
Data access layer for widget operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from services.widget.repositories.models import Widget, PlaylistWidget
from services.widget.dtos import (
    CreateWidgetRequest,
    UpdateWidgetRequest,
    AssignWidgetToPlaylistRequest,
    UpdatePlaylistWidgetRequest
)


class WidgetRepository:
    """Repository for widget data access"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Widget Operations
    # ========================================================================

    def create_widget(
        self,
        organization_id: int,
        user_id: int,
        request: CreateWidgetRequest
    ) -> Widget:
        """Create a new widget"""
        widget = Widget(
            organization_id=organization_id,
            name=request.name,
            description=request.description,
            widget_type=request.widget_type,
            config=request.config,
            layout=request.layout,
            is_active=request.is_active,
            created_by_id=user_id
        )
        self.db.add(widget)
        self.db.commit()
        self.db.refresh(widget)
        return widget

    def get_widget_by_id(
        self,
        widget_id: int,
        organization_id: int
    ) -> Optional[Widget]:
        """Get widget by ID (scoped to organization)"""
        return self.db.query(Widget).filter(
            and_(
                Widget.id == widget_id,
                Widget.organization_id == organization_id
            )
        ).first()

    def get_widgets(
        self,
        organization_id: int,
        widget_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Widget], int]:
        """Get widgets with optional filters"""
        query = self.db.query(Widget).filter(
            Widget.organization_id == organization_id
        )

        if widget_type:
            query = query.filter(Widget.widget_type == widget_type)
        if is_active is not None:
            query = query.filter(Widget.is_active == is_active)

        total = query.count()
        widgets = query.order_by(Widget.created_at.desc()).offset(skip).limit(limit).all()

        return widgets, total

    def update_widget(
        self,
        widget_id: int,
        organization_id: int,
        request: UpdateWidgetRequest
    ) -> Optional[Widget]:
        """Update widget"""
        widget = self.get_widget_by_id(widget_id, organization_id)
        if not widget:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(widget, field, value)

        self.db.commit()
        self.db.refresh(widget)
        return widget

    def delete_widget(
        self,
        widget_id: int,
        organization_id: int
    ) -> bool:
        """Delete widget"""
        widget = self.get_widget_by_id(widget_id, organization_id)
        if not widget:
            return False

        self.db.delete(widget)
        self.db.commit()
        return True

    def check_widget_name_exists(
        self,
        organization_id: int,
        name: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """Check if widget name already exists in organization"""
        query = self.db.query(Widget).filter(
            and_(
                Widget.organization_id == organization_id,
                Widget.name == name
            )
        )

        if exclude_id:
            query = query.filter(Widget.id != exclude_id)

        return query.first() is not None

    # ========================================================================
    # Playlist Widget Operations
    # ========================================================================

    def assign_widget_to_playlist(
        self,
        playlist_id: int,
        request: AssignWidgetToPlaylistRequest
    ) -> PlaylistWidget:
        """Assign widget to playlist"""
        playlist_widget = PlaylistWidget(
            playlist_id=playlist_id,
            widget_id=request.widget_id,
            position=request.position,
            display_duration=request.display_duration,
            z_index=request.z_index
        )
        self.db.add(playlist_widget)
        self.db.commit()
        self.db.refresh(playlist_widget)
        return playlist_widget

    def get_playlist_widget(
        self,
        playlist_widget_id: int
    ) -> Optional[PlaylistWidget]:
        """Get playlist widget by ID"""
        return self.db.query(PlaylistWidget).filter(
            PlaylistWidget.id == playlist_widget_id
        ).first()

    def get_playlist_widgets(
        self,
        playlist_id: int
    ) -> List[PlaylistWidget]:
        """Get all widgets assigned to playlist"""
        return self.db.query(PlaylistWidget).filter(
            PlaylistWidget.playlist_id == playlist_id
        ).order_by(PlaylistWidget.position).all()

    def update_playlist_widget(
        self,
        playlist_widget_id: int,
        request: UpdatePlaylistWidgetRequest
    ) -> Optional[PlaylistWidget]:
        """Update playlist widget settings"""
        playlist_widget = self.get_playlist_widget(playlist_widget_id)
        if not playlist_widget:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(playlist_widget, field, value)

        self.db.commit()
        self.db.refresh(playlist_widget)
        return playlist_widget

    def remove_widget_from_playlist(
        self,
        playlist_id: int,
        widget_id: int
    ) -> bool:
        """Remove widget from playlist"""
        playlist_widget = self.db.query(PlaylistWidget).filter(
            and_(
                PlaylistWidget.playlist_id == playlist_id,
                PlaylistWidget.widget_id == widget_id
            )
        ).first()

        if not playlist_widget:
            return False

        self.db.delete(playlist_widget)
        self.db.commit()
        return True

    def check_widget_assigned(
        self,
        playlist_id: int,
        widget_id: int
    ) -> bool:
        """Check if widget is already assigned to playlist"""
        return self.db.query(PlaylistWidget).filter(
            and_(
                PlaylistWidget.playlist_id == playlist_id,
                PlaylistWidget.widget_id == widget_id
            )
        ).first() is not None

    def get_widget_playlists(
        self,
        widget_id: int
    ) -> List[PlaylistWidget]:
        """Get all playlists that have this widget assigned"""
        return self.db.query(PlaylistWidget).filter(
            PlaylistWidget.widget_id == widget_id
        ).all()
