"""Menu Media Repository Implementation"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from datetime import datetime

from .models import MenuMediaModel
import logging

logger = logging.getLogger(__name__)


class MenuMediaRepository:
    """Menu Media repository with organization isolation"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        organization_id: int,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        uploaded_by_id: int,
        **kwargs
    ) -> MenuMediaModel:
        """Create new menu media"""
        media = MenuMediaModel(
            organization_id=organization_id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by_id=uploaded_by_id,
            **kwargs
        )
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)

        logger.info(f"Created menu media {media.id} for organization {organization_id}")
        return media

    def find_by_id(
        self,
        media_id: int,
        organization_id: int,
        include_deleted: bool = False
    ) -> Optional[MenuMediaModel]:
        """Find menu media by ID with organization filtering"""
        query = self.db.query(MenuMediaModel).filter(
            MenuMediaModel.id == media_id,
            MenuMediaModel.organization_id == organization_id
        )

        if not include_deleted:
            query = query.filter(MenuMediaModel.deleted_at.is_(None))

        return query.first()

    # Valid sortable columns for menu media
    SORTABLE_COLUMNS = {
        'original_filename': MenuMediaModel.original_filename,
        'mime_type': MenuMediaModel.mime_type,
        'file_size': MenuMediaModel.file_size,
        'width': MenuMediaModel.width,
        'height': MenuMediaModel.height,
        'created_at': MenuMediaModel.created_at,
        'updated_at': MenuMediaModel.updated_at,
        'deleted_at': MenuMediaModel.deleted_at,
    }

    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> Tuple[List[MenuMediaModel], int]:
        """Find all menu media for organization with sorting"""
        query = self.db.query(MenuMediaModel).filter(
            MenuMediaModel.organization_id == organization_id
        )

        if not include_deleted:
            query = query.filter(MenuMediaModel.deleted_at.is_(None))

        if is_active is not None:
            query = query.filter(MenuMediaModel.is_active == is_active)

        # Count total
        total = query.count()

        # Apply sorting
        if sort_by and sort_by in self.SORTABLE_COLUMNS:
            column = self.SORTABLE_COLUMNS[sort_by]
            if sort_dir == 'desc':
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        else:
            # Default sort by created_at desc
            query = query.order_by(desc(MenuMediaModel.created_at))

        # Apply pagination
        media_list = query.offset(skip).limit(limit).all()

        return media_list, total

    def update(self, media: MenuMediaModel, **kwargs) -> MenuMediaModel:
        """Update menu media"""
        for key, value in kwargs.items():
            if hasattr(media, key):
                setattr(media, key, value)

        media.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(media)

        logger.info(f"Updated menu media {media.id}")
        return media

    def soft_delete(self, media: MenuMediaModel, deleted_by_id: int = None) -> MenuMediaModel:
        """Soft delete menu media"""
        media.deleted_at = datetime.utcnow()
        if deleted_by_id:
            media.deleted_by_id = deleted_by_id
        self.db.commit()
        self.db.refresh(media)

        logger.info(f"Soft deleted menu media {media.id}")
        return media

    def find_all_deleted(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> Tuple[List[MenuMediaModel], int]:
        """Find all soft-deleted menu media for organization (Recycle Bin)"""
        query = self.db.query(MenuMediaModel).filter(
            MenuMediaModel.organization_id == organization_id,
            MenuMediaModel.deleted_at.isnot(None)
        )

        # Search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (MenuMediaModel.original_filename.ilike(search_term)) |
                (MenuMediaModel.title.ilike(search_term))
            )

        # Count total
        total = query.count()

        # Apply sorting
        if sort_by and sort_by in self.SORTABLE_COLUMNS:
            column = self.SORTABLE_COLUMNS[sort_by]
            if sort_dir == 'desc':
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        else:
            # Default: order by deleted date (newest first)
            query = query.order_by(MenuMediaModel.deleted_at.desc())

        # Apply pagination
        media_list = query.offset(skip).limit(limit).all()

        return media_list, total

    def restore(self, media: MenuMediaModel) -> MenuMediaModel:
        """Restore soft-deleted menu media"""
        media.deleted_at = None
        media.deleted_by_id = None
        self.db.commit()
        self.db.refresh(media)

        logger.info(f"Restored menu media {media.id}")
        return media

    def hard_delete(self, media: MenuMediaModel) -> bool:
        """Permanently delete menu media from database"""
        import os
        from shared.config import settings

        media_id = media.id
        file_path = media.file_path
        file_hash = media.file_hash

        # Check if other records use the same file (deduplication)
        other_using_same_file = False
        if file_hash:
            other_using_same_file = self.db.query(MenuMediaModel).filter(
                MenuMediaModel.file_hash == file_hash,
                MenuMediaModel.id != media_id
            ).first() is not None

        # Delete from database
        self.db.delete(media)
        self.db.commit()

        # Delete physical file only if no other records use it
        if file_path and not other_using_same_file:
            full_path = os.path.join(settings.UPLOAD_DIR, file_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    logger.info(f"Deleted file: {full_path}")
                except Exception as e:
                    logger.error(f"Failed to delete file {full_path}: {e}")
        elif other_using_same_file:
            logger.info(f"Preserved file {file_path} - still used by other records")

        logger.info(f"Permanently deleted menu media {media_id}")
        return True

    def find_by_hash(
        self,
        file_hash: str,
        organization_id: int
    ) -> Optional[MenuMediaModel]:
        """Find menu media by file hash (for deduplication)"""
        return self.db.query(MenuMediaModel).filter(
            MenuMediaModel.file_hash == file_hash,
            MenuMediaModel.organization_id == organization_id,
            MenuMediaModel.deleted_at.is_(None)
        ).first()

    def find_duplicates_with_usage(self, organization_id: int) -> list:
        """
        Find duplicate files (same hash) with their usage info.
        Returns groups of duplicates.
        """
        from sqlalchemy import text, func

        # Find hashes that have duplicates (count > 1)
        duplicate_hashes = self.db.execute(text("""
            SELECT file_hash, COUNT(*) as cnt, MIN(file_size) as file_size,
                   MIN(mime_type) as mime_type
            FROM menu_media
            WHERE organization_id = :org_id AND deleted_at IS NULL AND file_hash IS NOT NULL
            GROUP BY file_hash
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """), {"org_id": organization_id}).fetchall()

        if not duplicate_hashes:
            return []

        result = []

        for row in duplicate_hashes:
            file_hash = row.file_hash

            # Get all media with this hash
            media_list = self.db.query(MenuMediaModel).filter(
                MenuMediaModel.organization_id == organization_id,
                MenuMediaModel.file_hash == file_hash,
                MenuMediaModel.deleted_at.is_(None)
            ).order_by(MenuMediaModel.created_at.asc()).all()

            media_with_usage = []
            for media in media_list:
                # Get menu items using this media
                usage = self._get_media_usage(media.id)

                media_with_usage.append({
                    "id": media.id,
                    "title": media.title or media.original_filename,
                    "original_filename": media.original_filename,
                    "created_at": media.created_at.isoformat() if media.created_at else None,
                    "is_active": media.is_active,
                    "usage": usage
                })

            result.append({
                "file_hash": file_hash[:16] + "..." if file_hash else None,
                "file_size": row.file_size,
                "mime_type": row.mime_type,
                "duplicate_count": len(media_list),
                "media": media_with_usage
            })

        return result

    def _get_media_usage(self, media_id: int) -> dict:
        """Get usage info for a menu media (which menu items use it)"""
        from sqlalchemy import text

        # Get menu items using this media
        menu_items = self.db.execute(text("""
            SELECT mi.id, mi.name, m.id as menu_id, m.name as menu_name
            FROM menu_items mi
            JOIN menus m ON mi.menu_id = m.id
            WHERE mi.menu_media_id = :media_id
              AND mi.deleted_at IS NULL
              AND m.deleted_at IS NULL
        """), {"media_id": media_id}).fetchall()

        return {
            "menu_items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "menu_id": item.menu_id,
                    "menu_name": item.menu_name
                }
                for item in menu_items
            ],
            "used_count": len(menu_items)
        }
