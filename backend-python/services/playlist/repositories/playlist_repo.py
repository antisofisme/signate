"""
Playlist Repository Implementation
Database access for playlist management with organization isolation
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_

from ..domain.playlist import Playlist, PlaylistContent, PlaylistAssignment
from ..domain.interfaces import IPlaylistRepository
from .models import PlaylistModel, PlaylistContentModel, PlaylistAssignmentModel
from services.content.repositories.models import ContentModel
from shared.cache import cache
import logging

logger = logging.getLogger(__name__)


class PlaylistRepository(IPlaylistRepository):
    """Playlist repository implementation with organization filtering"""

    def __init__(self, db: Session):
        self.db = db

    # ========== Helper: Cache Invalidation (CRITICAL FIX P0-7) ==========

    def _invalidate_content_resolver_cache(self, playlist_id: int, organization_id: int):
        """
        Invalidate content resolver cache for all devices affected by playlist changes

        CRITICAL FIX P0-7: When playlist content changes, all devices playing that
        playlist should receive updated content on next resolution
        """
        try:
            # Get all devices assigned to this playlist (direct assignments)
            device_assignments = self.db.query(PlaylistAssignmentModel).filter(
                PlaylistAssignmentModel.playlist_id == playlist_id,
                PlaylistAssignmentModel.device_id.isnot(None)
            ).all()

            # Invalidate cache for each directly assigned device
            for assignment in device_assignments:
                device_cache_key = f"content_resolution:{assignment.device_id}"
                cache.delete(device_cache_key)
                logger.info(f"Invalidated cache for device {assignment.device_id} (playlist {playlist_id} changed)")

            # Get all tags assigned to this playlist
            tag_assignments = self.db.query(PlaylistAssignmentModel).filter(
                PlaylistAssignmentModel.playlist_id == playlist_id,
                PlaylistAssignmentModel.tag_id.isnot(None)
            ).all()

            # For tag assignments, invalidate cache for all devices with those tags
            if tag_assignments:
                from services.device.repositories.models import DeviceModel
                from services.device.repositories.models import DeviceTagModel

                tag_ids = [a.tag_id for a in tag_assignments]

                # Find all devices with these tags
                device_tag_relations = self.db.query(DeviceTagModel).filter(
                    DeviceTagModel.tag_id.in_(tag_ids)
                ).all()

                for device_tag in device_tag_relations:
                    device_cache_key = f"content_resolution:{device_tag.device_id}"
                    cache.delete(device_cache_key)
                    logger.info(f"Invalidated cache for device {device_tag.device_id} (tag-based playlist {playlist_id} changed)")

            # Also invalidate pattern-based cache for organization
            # (for devices using default playlist or schedule-based resolution)
            cache.invalidate_pattern(f"content_resolution:org_{organization_id}:*")

            logger.info(f"Cache invalidation complete for playlist {playlist_id}")

        except Exception as e:
            # Log but don't fail - cache invalidation is best-effort
            logger.error(f"Failed to invalidate cache for playlist {playlist_id}: {e}")

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
            is_default=model.is_default,
            is_pms_template=model.is_pms_template,
            organization_id=model.organization_id,
            created_by_id=model.created_by_id,
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
            is_default=playlist.is_default,
            is_pms_template=playlist.is_pms_template,
            organization_id=playlist.organization_id,
            created_by_id=playlist.created_by_id,
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
        playlist_model = self.db.query(PlaylistModel).options(
            selectinload(PlaylistModel.contents),
            selectinload(PlaylistModel.assignments)
        ).filter(
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
        db_playlist.is_default = playlist.is_default
        db_playlist.is_pms_template = playlist.is_pms_template
        db_playlist.updated_at = playlist.updated_at

        self.db.commit()
        self.db.refresh(db_playlist)

        # CRITICAL FIX P0-7: Invalidate cache when playlist changes
        self._invalidate_content_resolver_cache(playlist.id, playlist.organization_id)

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
            from datetime import datetime, timezone
            db_playlist.deleted_at = datetime.now(timezone.utc)
            self.db.commit()
        else:
            # Hard delete (cascades to contents and assignments)
            self.db.delete(db_playlist)
            self.db.commit()

        # CRITICAL FIX P0-7: Invalidate cache when playlist deleted
        self._invalidate_content_resolver_cache(playlist_id, organization_id)

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

        # CRITICAL FIX P0-7: Invalidate cache when playlist content changes
        if added_count > 0:
            self._invalidate_content_resolver_cache(playlist_id, organization_id)

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

        # CRITICAL FIX P0-7: Invalidate cache when playlist content removed
        self._invalidate_content_resolver_cache(playlist_id, organization_id)

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

        # CRITICAL FIX P0-7: Invalidate cache when playlist content reordered
        if updated_count > 0:
            self._invalidate_content_resolver_cache(playlist_id, organization_id)

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
        from services.tag.repositories.models import TagModel
        tag_ids = [a.tag_id for a in tag_assignments]
        tags = []
        if tag_ids:
            tags = self.db.query(TagModel).filter(
                TagModel.id.in_(tag_ids)
            ).all()

        return {
            "devices": [{"id": d.id, "device_name": d.device_name, "location": d.location} for d in devices],
            "tags": [{"id": t.id, "name": t.tag_name, "color": t.color} for t in tags]
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

        # CRITICAL FIX P0-7: Invalidate cache when devices assigned
        if assigned_count > 0:
            self._invalidate_content_resolver_cache(playlist_id, organization_id)

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
        from services.tag.repositories.models import TagModel
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

        # CRITICAL FIX P0-7: Invalidate cache when tags assigned
        if assigned_count > 0:
            self._invalidate_content_resolver_cache(playlist_id, organization_id)

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

        # CRITICAL FIX P0-7: Invalidate cache when devices unassigned
        if removed > 0:
            self._invalidate_content_resolver_cache(playlist_id, organization_id)

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

        # CRITICAL FIX P0-7: Invalidate cache when tags unassigned
        if removed > 0:
            self._invalidate_content_resolver_cache(playlist_id, organization_id)

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
        # Note: Cannot eager load content - relationship doesn't exist in PlaylistContentModel
        # This will cause N+1 queries for items without duration, but that's acceptable
        # because most items have explicit durations set
        content_items = self.db.query(PlaylistContentModel).filter(
            PlaylistContentModel.playlist_id == playlist_id
        ).all()

        total_duration = 0
        for item in content_items:
            if item.duration:
                # Use explicit duration (most common case - no extra query)
                total_duration += item.duration
            else:
                # Fallback: fetch content for default duration (rare case - N+1 acceptable)
                content = self.db.query(ContentModel).filter(
                    ContentModel.id == item.content_id
                ).first()
                if content and content.duration:
                    total_duration += content.duration

        return {
            "content_count": content_count,
            "total_duration": total_duration
        }
    
    def find_default_playlist(self, organization_id: int) -> Optional[Playlist]:
        """Find default playlist for organization"""
        # Look for a playlist named "Default" or with is_default flag
        model = self.db.query(PlaylistModel).filter(
            and_(
                PlaylistModel.organization_id == organization_id,
                PlaylistModel.is_active == True,
                or_(
                    PlaylistModel.name.ilike('%default%'),
                    PlaylistModel.is_default == True  # Assuming we add this field
                )
            )
        ).first()
        
        if model:
            return self._model_to_entity(model)
        
        # If no default playlist exists, return the first active playlist
        model = self.db.query(PlaylistModel).filter(
            and_(
                PlaylistModel.organization_id == organization_id,
                PlaylistModel.is_active == True
            )
        ).order_by(PlaylistModel.created_at).first()
        
        return self._model_to_entity(model) if model else None
    
    def find_pms_template(self, organization_id: int) -> Optional[Playlist]:
        """Find PMS template playlist for organization"""
        # Look for playlist with PMS template flag or name
        model = self.db.query(PlaylistModel).filter(
            and_(
                PlaylistModel.organization_id == organization_id,
                PlaylistModel.is_active == True,
                or_(
                    PlaylistModel.name.ilike('%pms%'),
                    PlaylistModel.name.ilike('%guest%'),
                    PlaylistModel.is_pms_template == True  # Assuming we add this field
                )
            )
        ).first()
        
        return self._model_to_entity(model) if model else None
