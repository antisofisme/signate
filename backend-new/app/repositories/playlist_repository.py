"""
Playlist Repository - Database Access untuk Playlist Management
==============================================================

CENTRALIZED QUERIES untuk playlists, playlist_contents, and playlist_assignments tables
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.repositories.base import BaseRepository
from app.models.playlist import Playlist, PlaylistContent, PlaylistAssignment


class PlaylistRepository(BaseRepository):
    """
    Playlist Repository untuk playlist management

    Handles:
    - Playlist CRUD
    - Content assignment to playlists
    - Device assignment to playlists
    - Play order management
    - Playlist scheduling
    """

    def __init__(self, db: Session):
        super().__init__(Playlist, db)
        self.db = db

    # =========================================================================
    # PLAYLIST-SPECIFIC QUERIES
    # =========================================================================

    def get_by_organization(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Playlist]:
        """
        Get all playlists untuk organization

        Example:
            playlists = playlist_repo.get_by_organization(org_id=1)
        """
        return self.db.query(self.model).filter(
            self.model.organization_id == organization_id
        ).offset(skip).limit(limit).all()

    def get_device_playlists(self, device_id: int) -> List[Playlist]:
        """
        Get all playlists assigned to a device

        Joins through playlist_assignments table

        Example:
            playlists = playlist_repo.get_device_playlists(device_id=123)
        """
        return self.db.query(self.model).join(
            PlaylistAssignment,
            PlaylistAssignment.playlist_id == self.model.id
        ).filter(
            PlaylistAssignment.device_id == device_id
        ).all()

    def get_playlist_contents(
        self,
        playlist_id: int,
        ordered: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all contents in a playlist with metadata

        Args:
            playlist_id: Playlist ID
            ordered: If True, order by play_order (default)

        Returns list of dicts with content + playlist metadata:
            [
                {
                    "content": Content object,
                    "order_index": 1,
                    "duration": 10
                },
                ...
            ]
        """
        from app.models.content import Content

        query = self.db.query(
            Content,
            PlaylistContent.order_index,
            PlaylistContent.duration
        ).join(
            PlaylistContent,
            PlaylistContent.content_id == Content.id
        ).filter(
            PlaylistContent.playlist_id == playlist_id
        )

        if ordered:
            query = query.order_by(PlaylistContent.order_index)

        results = query.all()

        return [
            {
                "content": content,
                "order_index": order_index,
                "duration": duration
            }
            for content, order_index, duration in results
        ]

    def add_content_to_playlist(
        self,
        playlist_id: int,
        content_id: int,
        order_index: Optional[int] = None,
        duration: Optional[int] = None
    ) -> PlaylistContent:
        """
        Add content to playlist

        Args:
            playlist_id: Playlist ID
            content_id: Content ID
            order_index: Order in playlist (auto-increments if not provided)
            duration: Duration in seconds (optional)

        Returns:
            PlaylistContent object
        """
        # Auto-generate order_index if not provided
        if order_index is None:
            max_order = self.db.query(
                func.max(PlaylistContent.order_index)
            ).filter(
                PlaylistContent.playlist_id == playlist_id
            ).scalar() or 0

            order_index = max_order + 1

        playlist_content = PlaylistContent(
            playlist_id=playlist_id,
            content_id=content_id,
            order_index=order_index,
            duration=duration
        )

        self.db.add(playlist_content)
        self.db.commit()
        self.db.refresh(playlist_content)

        return playlist_content

    def remove_content_from_playlist(
        self,
        playlist_id: int,
        content_id: int
    ) -> bool:
        """
        Remove content from playlist

        Returns:
            True if deleted, False if not found
        """
        result = self.db.query(PlaylistContent).filter(
            and_(
                PlaylistContent.playlist_id == playlist_id,
                PlaylistContent.content_id == content_id
            )
        ).delete()

        self.db.commit()
        return result > 0

    def reorder_playlist_content(
        self,
        playlist_id: int,
        content_orders: List[Dict[str, int]]
    ) -> bool:
        """
        Reorder content in playlist

        Args:
            playlist_id: Playlist ID
            content_orders: List of {"content_id": X, "order_index": Y}

        Example:
            playlist_repo.reorder_playlist_content(
                playlist_id=1,
                content_orders=[
                    {"content_id": 5, "order_index": 1},
                    {"content_id": 3, "order_index": 2},
                    {"content_id": 7, "order_index": 3}
                ]
            )
        """
        for item in content_orders:
            self.db.query(PlaylistContent).filter(
                and_(
                    PlaylistContent.playlist_id == playlist_id,
                    PlaylistContent.content_id == item["content_id"]
                )
            ).update({"order_index": item["order_index"]})

        self.db.commit()
        return True

    def assign_to_device(
        self,
        playlist_id: int,
        device_id: int,
        priority: int = 0
    ) -> PlaylistAssignment:
        """
        Assign playlist to device

        Args:
            playlist_id: Playlist ID
            device_id: Device ID
            priority: Priority level (higher = more important)

        Returns:
            PlaylistAssignment object
        """
        # Check if already assigned
        existing = self.db.query(PlaylistAssignment).filter(
            and_(
                PlaylistAssignment.playlist_id == playlist_id,
                PlaylistAssignment.device_id == device_id
            )
        ).first()

        if existing:
            # Update priority if already exists
            existing.priority = priority
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new assignment
        assignment = PlaylistAssignment(
            playlist_id=playlist_id,
            device_id=device_id,
            priority=priority
        )

        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        return assignment

    def unassign_from_device(
        self,
        playlist_id: int,
        device_id: int
    ) -> bool:
        """
        Unassign playlist from device

        Returns:
            True if deleted, False if not found
        """
        result = self.db.query(PlaylistAssignment).filter(
            and_(
                PlaylistAssignment.playlist_id == playlist_id,
                PlaylistAssignment.device_id == device_id
            )
        ).delete()

        self.db.commit()
        return result > 0

    def get_device_assignments(self, device_id: int) -> List[PlaylistAssignment]:
        """
        Get all playlist assignments for a device

        Ordered by priority (desc), then created_at

        Example:
            assignments = playlist_repo.get_device_assignments(device_id=123)
        """
        return self.db.query(PlaylistAssignment).filter(
            PlaylistAssignment.device_id == device_id
        ).order_by(
            desc(PlaylistAssignment.priority),
            PlaylistAssignment.created_at
        ).all()

    def get_playlist_stats(self, playlist_id: int) -> Dict[str, Any]:
        """
        Get statistics for a playlist

        Returns:
            {
                "total_contents": 10,
                "total_duration": 300,  # seconds
                "device_count": 5,      # devices using this playlist
                "content_types": {"image": 5, "video": 3, "html": 2}
            }
        """
        from app.models.content import Content

        # Count contents
        total_contents = self.db.query(func.count(PlaylistContent.id)).filter(
            PlaylistContent.playlist_id == playlist_id
        ).scalar() or 0

        # Sum durations
        total_duration = self.db.query(
            func.coalesce(func.sum(PlaylistContent.duration), 0)
        ).filter(
            PlaylistContent.playlist_id == playlist_id
        ).scalar() or 0

        # Count devices
        device_count = self.db.query(func.count(PlaylistAssignment.id)).filter(
            PlaylistAssignment.playlist_id == playlist_id
        ).scalar() or 0

        # Get content types breakdown
        content_types = {}
        type_counts = self.db.query(
            Content.content_type,
            func.count(Content.id)
        ).join(
            PlaylistContent,
            PlaylistContent.content_id == Content.id
        ).filter(
            PlaylistContent.playlist_id == playlist_id
        ).group_by(Content.content_type).all()

        for content_type, count in type_counts:
            content_types[content_type] = count

        return {
            "total_contents": total_contents,
            "total_duration": total_duration,
            "device_count": device_count,
            "content_types": content_types
        }

    def search_playlists(
        self,
        organization_id: int,
        query: str
    ) -> List[Playlist]:
        """
        Search playlists by name or description

        Example:
            results = playlist_repo.search_playlists(
                organization_id=1,
                query="promo"
            )
        """
        search_pattern = f"%{query}%"
        return self.db.query(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                or_(
                    self.model.name.ilike(search_pattern),
                    self.model.description.ilike(search_pattern)
                )
            )
        ).all()

    def duplicate_playlist(
        self,
        playlist_id: int,
        new_name: str,
        copy_assignments: bool = False
    ) -> Playlist:
        """
        Duplicate a playlist with all its contents

        Args:
            playlist_id: Source playlist ID
            new_name: Name for the new playlist
            copy_assignments: Whether to copy device assignments

        Returns:
            New Playlist object
        """
        # Get source playlist
        source = self.get(playlist_id)
        if not source:
            raise ValueError(f"Playlist {playlist_id} not found")

        # Create new playlist
        new_playlist = Playlist(
            organization_id=source.organization_id,
            name=new_name,
            description=f"Copy of {source.name}",
            is_active=source.is_active
        )
        self.db.add(new_playlist)
        self.db.commit()
        self.db.refresh(new_playlist)

        # Copy contents
        contents = self.db.query(PlaylistContent).filter(
            PlaylistContent.playlist_id == playlist_id
        ).all()

        for content in contents:
            new_content = PlaylistContent(
                playlist_id=new_playlist.id,
                content_id=content.content_id,
                order_index=content.order_index,
                duration=content.duration
            )
            self.db.add(new_content)

        # Optionally copy assignments
        if copy_assignments:
            assignments = self.db.query(PlaylistAssignment).filter(
                PlaylistAssignment.playlist_id == playlist_id
            ).all()

            for assignment in assignments:
                new_assignment = PlaylistAssignment(
                    playlist_id=new_playlist.id,
                    device_id=assignment.device_id,
                    priority=assignment.priority
                )
                self.db.add(new_assignment)

        self.db.commit()
        self.db.refresh(new_playlist)

        return new_playlist
