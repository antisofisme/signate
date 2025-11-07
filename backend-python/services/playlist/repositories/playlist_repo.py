"""
Playlist Repository Implementation
Database access for playlist management with organization isolation
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..domain.playlist import Playlist, PlaylistContent, PlaylistAssignment
from ..domain.interfaces import IPlaylistRepository
from .models import PlaylistModel, PlaylistContentModel, PlaylistAssignmentModel
from services.content.repositories.models import ContentModel


class PlaylistRepository(IPlaylistRepository):
    """Playlist repository implementation with organization filtering"""

    def __init__(self, db: Session):
        self.db = db

    # ========== Helper: Model <-> Entity Conversion ==========

    def _model_to_entity(self, model: PlaylistModel, include_stats: bool = False) -> Playlist:
        """Convert SQLAlchemy model to domain entity"""
        playlist = Playlist(
            id=model.id,
            name=model.name,
            description=model.description,
            is_active=model.is_active,
            priority=model.priority,
            schedule=model.schedule,
            organization_id=model.organization_id,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

        # Include computed stats if requested
        if include_stats:
            stats = self.calculate_playlist_stats(model.id, model.organization_id)
            playlist.content_count = stats["content_count"]
            playlist.total_duration = stats["total_duration"]

        return playlist

    def _content_model_to_entity(self, model: PlaylistContentModel) -> PlaylistContent:
        """Convert content model to entity"""
        return PlaylistContent(
            id=model.id,
            playlist_id=model.playlist_id,
            content_id=model.content_id,
            order_index=model.order_index,
            duration=model.duration,
            created_at=model.created_at,
        )

    def _assignment_model_to_entity(self, model: PlaylistAssignmentModel) -> PlaylistAssignment:
        """Convert assignment model to entity"""
        return PlaylistAssignment(
            id=model.id,
            playlist_id=model.playlist_id,
            device_id=model.device_id,
            tag_id=model.tag_id,
            created_at=model.created_at,
        )

    # ========== Playlist CRUD ==========

    def create(self, playlist: Playlist) -> Playlist:
        """Create new playlist"""
        db_playlist = PlaylistModel(
            name=playlist.name,
            description=playlist.description,
            is_active=playlist.is_active,
            priority=playlist.priority,
            schedule=playlist.schedule,
            organization_id=playlist.organization_id,
            created_by=playlist.created_by,
        )

        self.db.add(db_playlist)
        self.db.commit()
        self.db.refresh(db_playlist)

        return self._model_to_entity(db_playlist, include_stats=True)

    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[Playlist], int]:
        """Find all playlists with organization filter"""
        query = self.db.query(PlaylistModel).filter(
            PlaylistModel.organization_id == organization_id
        )

        # Filter by active status
        if is_active is not None:
            query = query.filter(PlaylistModel.is_active == is_active)

        # Filter deleted
        if not include_deleted:
            query = query.filter(PlaylistModel.deleted_at.is_(None))

        # Get total count
        total = query.count()

        # Pagination and ordering
        playlists_models = query.order_by(
            PlaylistModel.created_at.desc()
        ).offset(skip).limit(limit).all()

        # Convert to entities with stats
        playlists = [self._model_to_entity(p, include_stats=True) for p in playlists_models]

        return playlists, total

    def find_by_id(self, playlist_id: int, organization_id: int) -> Optional[Playlist]:
        """Find playlist by ID with organization filter"""
        playlist_model = self.db.query(PlaylistModel).filter(
            and_(
                PlaylistModel.id == playlist_id,
                PlaylistModel.organization_id == organization_id,
                PlaylistModel.deleted_at.is_(None)
            )
        ).first()

        if not playlist_model:
            return None

        return self._model_to_entity(playlist_model, include_stats=True)

    def update(self, playlist: Playlist) -> Playlist:
        """Update playlist"""
        db_playlist = self.db.query(PlaylistModel).filter(
            and_(
                PlaylistModel.id == playlist.id,
                PlaylistModel.organization_id == playlist.organization_id
            )
        ).first()

        if not db_playlist:
            raise ValueError(f"Playlist {playlist.id} not found")

        # Update fields
        db_playlist.name = playlist.name
        db_playlist.description = playlist.description
        db_playlist.is_active = playlist.is_active
        db_playlist.priority = playlist.priority
        db_playlist.schedule = playlist.schedule
        db_playlist.updated_at = playlist.updated_at

        self.db.commit()
        self.db.refresh(db_playlist)

        return self._model_to_entity(db_playlist, include_stats=True)

    def delete(self, playlist_id: int, organization_id: int, soft: bool = False) -> bool:
        """Delete playlist (soft or hard)"""
        db_playlist = self.db.query(PlaylistModel).filter(
            and_(
                PlaylistModel.id == playlist_id,
                PlaylistModel.organization_id == organization_id
            )
        ).first()

        if not db_playlist:
            return False

        if soft:
            # Soft delete
            from datetime import datetime
            db_playlist.deleted_at = datetime.utcnow()
            self.db.commit()
        else:
            # Hard delete (cascades to contents and assignments)
            self.db.delete(db_playlist)
            self.db.commit()

        return True

    # ========== Content Management ==========

    def get_playlist_contents(
        self,
        playlist_id: int,
        organization_id: int
    ) -> List[PlaylistContent]:
        """Get all content items in playlist (ordered)"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Get content items ordered by order_index
        content_models = self.db.query(PlaylistContentModel).filter(
            PlaylistContentModel.playlist_id == playlist_id
        ).order_by(PlaylistContentModel.order_index).all()

        return [self._content_model_to_entity(c) for c in content_models]

    def add_contents_to_playlist(
        self,
        playlist_id: int,
        content_ids: List[int],
        organization_id: int
    ) -> Dict[str, Any]:
        """Bulk add content to playlist"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Get current max order_index
        max_order = self.db.query(func.max(PlaylistContentModel.order_index)).filter(
            PlaylistContentModel.playlist_id == playlist_id
        ).scalar() or -1

        # Validate content exists and belongs to organization
        valid_content_ids = self.db.query(ContentModel.id).filter(
            and_(
                ContentModel.id.in_(content_ids),
                ContentModel.organization_id == organization_id,
                ContentModel.deleted_at.is_(None)
            )
        ).all()
        valid_ids = [c[0] for c in valid_content_ids]

        # Check already added
        existing = self.db.query(PlaylistContentModel.content_id).filter(
            and_(
                PlaylistContentModel.playlist_id == playlist_id,
                PlaylistContentModel.content_id.in_(valid_ids)
            )
        ).all()
        existing_ids = set([c[0] for c in existing])

        # Calculate what to add
        added_count = 0
        skipped_missing = [cid for cid in content_ids if cid not in valid_ids]
        skipped_duplicate = [cid for cid in valid_ids if cid in existing_ids]
        to_add = [cid for cid in valid_ids if cid not in existing_ids]

        # Bulk insert new content items
        if to_add:
            for content_id in to_add:
                max_order += 1
                # Get content duration as default
                content = self.db.query(ContentModel).filter(ContentModel.id == content_id).first()
                duration = content.duration if content else None

                playlist_content = PlaylistContentModel(
                    playlist_id=playlist_id,
                    content_id=content_id,
                    order_index=max_order,
                    duration=duration
                )
                self.db.add(playlist_content)
                added_count += 1

            self.db.commit()

        return {
            "added": added_count,
            "skipped_missing": skipped_missing,
            "skipped_duplicate": skipped_duplicate
        }

    def remove_content_from_playlist(
        self,
        playlist_content_id: int,
        playlist_id: int,
        organization_id: int
    ) -> bool:
        """Remove content item from playlist"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Find and delete content item
        playlist_content = self.db.query(PlaylistContentModel).filter(
            and_(
                PlaylistContentModel.id == playlist_content_id,
                PlaylistContentModel.playlist_id == playlist_id
            )
        ).first()

        if not playlist_content:
            return False

        self.db.delete(playlist_content)
        self.db.commit()
        return True

    def reorder_playlist_contents(
        self,
        playlist_id: int,
        content_items: List[Dict[str, Any]],
        organization_id: int
    ) -> int:
        """Bulk reorder and update duration of content items"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        updated_count = 0
        for item_data in content_items:
            playlist_content = self.db.query(PlaylistContentModel).filter(
                and_(
                    PlaylistContentModel.id == item_data.get("id"),
                    PlaylistContentModel.playlist_id == playlist_id
                )
            ).first()

            if playlist_content:
                if "order_index" in item_data:
                    playlist_content.order_index = item_data["order_index"]
                if "duration" in item_data:
                    playlist_content.duration = item_data["duration"]
                updated_count += 1

        self.db.commit()
        return updated_count

    # ========== Device/Tag Assignments ==========

    def get_playlist_assignments(
        self,
        playlist_id: int,
        organization_id: int
    ) -> Dict[str, Any]:
        """Get all assignments for playlist"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Get all assignments
        assignments = self.db.query(PlaylistAssignmentModel).filter(
            PlaylistAssignmentModel.playlist_id == playlist_id
        ).all()

        # Separate device and tag assignments
        device_assignments = [a for a in assignments if a.device_id]
        tag_assignments = [a for a in assignments if a.tag_id]

        # Get device details
        from services.device.repositories.models import DeviceModel
        device_ids = [a.device_id for a in device_assignments]
        devices = []
        if device_ids:
            devices = self.db.query(DeviceModel).filter(
                DeviceModel.id.in_(device_ids)
            ).all()

        # Get tag details
        from services.tag.models import Tag as TagModel
        tag_ids = [a.tag_id for a in tag_assignments]
        tags = []
        if tag_ids:
            tags = self.db.query(TagModel).filter(
                TagModel.id.in_(tag_ids)
            ).all()

        return {
            "devices": [{"id": d.id, "device_name": d.device_name, "location": d.location} for d in devices],
            "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in tags]
        }

    def assign_to_devices(
        self,
        playlist_id: int,
        device_ids: List[int],
        organization_id: int
    ) -> Dict[str, Any]:
        """Bulk assign playlist to devices"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Validate devices exist and belong to organization
        from services.device.repositories.models import DeviceModel
        valid_device_ids = self.db.query(DeviceModel.id).filter(
            and_(
                DeviceModel.id.in_(device_ids),
                DeviceModel.organization_id == organization_id
            )
        ).all()
        valid_ids = [d[0] for d in valid_device_ids]

        # Check already assigned
        existing = self.db.query(PlaylistAssignmentModel.device_id).filter(
            and_(
                PlaylistAssignmentModel.playlist_id == playlist_id,
                PlaylistAssignmentModel.device_id.in_(valid_ids)
            )
        ).all()
        existing_ids = set([d[0] for d in existing])

        # Calculate what to add
        assigned_count = 0
        skipped_missing = [did for did in device_ids if did not in valid_ids]
        skipped_duplicate = [did for did in valid_ids if did in existing_ids]
        to_add = [did for did in valid_ids if did not in existing_ids]

        # Bulk insert assignments
        if to_add:
            for device_id in to_add:
                assignment = PlaylistAssignmentModel(
                    playlist_id=playlist_id,
                    device_id=device_id,
                    tag_id=None
                )
                self.db.add(assignment)
                assigned_count += 1

            self.db.commit()

        return {
            "assigned": assigned_count,
            "skipped_missing": skipped_missing,
            "skipped_duplicate": skipped_duplicate
        }

    def assign_to_tags(
        self,
        playlist_id: int,
        tag_ids: List[int],
        organization_id: int
    ) -> Dict[str, Any]:
        """Bulk assign playlist to tags"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Validate tags exist and belong to organization
        from services.tag.models import Tag as TagModel
        valid_tag_ids = self.db.query(TagModel.id).filter(
            and_(
                TagModel.id.in_(tag_ids),
                TagModel.organization_id == organization_id
            )
        ).all()
        valid_ids = [t[0] for t in valid_tag_ids]

        # Check already assigned
        existing = self.db.query(PlaylistAssignmentModel.tag_id).filter(
            and_(
                PlaylistAssignmentModel.playlist_id == playlist_id,
                PlaylistAssignmentModel.tag_id.in_(valid_ids)
            )
        ).all()
        existing_ids = set([t[0] for t in existing])

        # Calculate what to add
        assigned_count = 0
        skipped_missing = [tid for tid in tag_ids if tid not in valid_ids]
        skipped_duplicate = [tid for tid in valid_ids if tid in existing_ids]
        to_add = [tid for tid in valid_ids if tid not in existing_ids]

        # Bulk insert assignments
        if to_add:
            for tag_id in to_add:
                assignment = PlaylistAssignmentModel(
                    playlist_id=playlist_id,
                    device_id=None,
                    tag_id=tag_id
                )
                self.db.add(assignment)
                assigned_count += 1

            self.db.commit()

        return {
            "assigned": assigned_count,
            "skipped_missing": skipped_missing,
            "skipped_duplicate": skipped_duplicate
        }

    def unassign_from_devices(
        self,
        playlist_id: int,
        device_ids: List[int],
        organization_id: int
    ) -> int:
        """Bulk unassign from devices"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Delete assignments
        removed = self.db.query(PlaylistAssignmentModel).filter(
            and_(
                PlaylistAssignmentModel.playlist_id == playlist_id,
                PlaylistAssignmentModel.device_id.in_(device_ids)
            )
        ).delete(synchronize_session=False)

        self.db.commit()
        return removed

    def unassign_from_tags(
        self,
        playlist_id: int,
        tag_ids: List[int],
        organization_id: int
    ) -> int:
        """Bulk unassign from tags"""
        # Verify playlist belongs to organization
        playlist = self.find_by_id(playlist_id, organization_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} not found or access denied")

        # Delete assignments
        removed = self.db.query(PlaylistAssignmentModel).filter(
            and_(
                PlaylistAssignmentModel.playlist_id == playlist_id,
                PlaylistAssignmentModel.tag_id.in_(tag_ids)
            )
        ).delete(synchronize_session=False)

        self.db.commit()
        return removed

    # ========== Utility Methods ==========

    def calculate_playlist_stats(
        self,
        playlist_id: int,
        organization_id: int
    ) -> Dict[str, int]:
        """Calculate content count and total duration"""
        # Count content items
        content_count = self.db.query(func.count(PlaylistContentModel.id)).filter(
            PlaylistContentModel.playlist_id == playlist_id
        ).scalar() or 0

        # Calculate total duration
        content_items = self.db.query(PlaylistContentModel).filter(
            PlaylistContentModel.playlist_id == playlist_id
        ).all()

        total_duration = 0
        for item in content_items:
            if item.duration:
                total_duration += item.duration
            else:
                # Use content's default duration
                content = self.db.query(ContentModel).filter(
                    ContentModel.id == item.content_id
                ).first()
                if content and content.duration:
                    total_duration += content.duration

        return {
            "content_count": content_count,
            "total_duration": total_duration
        }
