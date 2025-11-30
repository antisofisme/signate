"""Menu Media Repository Implementation"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
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

    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> Tuple[List[MenuMediaModel], int]:
        """Find all menu media for organization"""
        query = self.db.query(MenuMediaModel).filter(
            MenuMediaModel.organization_id == organization_id
        )

        if not include_deleted:
            query = query.filter(MenuMediaModel.deleted_at.is_(None))

        if is_active is not None:
            query = query.filter(MenuMediaModel.is_active == is_active)

        # Count total
        total = query.count()

        # Apply pagination and order
        media_list = query.order_by(MenuMediaModel.created_at.desc()).offset(skip).limit(limit).all()

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

    def soft_delete(self, media: MenuMediaModel) -> MenuMediaModel:
        """Soft delete menu media"""
        media.deleted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(media)

        logger.info(f"Soft deleted menu media {media.id}")
        return media
