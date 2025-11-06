"""
Tag Repository Implementation
Implements ITagRepository using SQLAlchemy
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from ..domain.interfaces import ITagRepository
from ..domain.tag import Tag
from .models import TagModel


class TagRepository(ITagRepository):
    """
    Tag Repository - SQLAlchemy Implementation
    """

    def __init__(self, db: Session):
        self.db = db

    def _model_to_entity(self, model: TagModel) -> Tag:
        """Convert SQLAlchemy model to domain entity"""
        return Tag(
            id=model.id,
            tag_name=model.tag_name,
            description=model.description,
            color=model.color,
            organization_id=model.organization_id,
            created_at=model.created_at,
        )

    def _entity_to_model(self, entity: Tag) -> TagModel:
        """Convert domain entity to SQLAlchemy model"""
        return TagModel(
            id=entity.id,
            tag_name=entity.tag_name,
            description=entity.description,
            color=entity.color,
            organization_id=entity.organization_id,
            created_at=entity.created_at,
        )

    def create(self, tag: Tag) -> Tag:
        """Create a new tag"""
        model = self._entity_to_model(tag)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._model_to_entity(model)

    def find_by_id(self, tag_id: int, organization_id: int) -> Optional[Tag]:
        """Find tag by ID within organization"""
        model = (
            self.db.query(TagModel)
            .filter(
                TagModel.id == tag_id,
                TagModel.organization_id == organization_id
            )
            .first()
        )
        return self._model_to_entity(model) if model else None

    def find_by_name(self, tag_name: str, organization_id: int) -> Optional[Tag]:
        """Find tag by name within organization"""
        model = (
            self.db.query(TagModel)
            .filter(
                TagModel.tag_name == tag_name,
                TagModel.organization_id == organization_id
            )
            .first()
        )
        return self._model_to_entity(model) if model else None

    def find_all(self, organization_id: int, sort_by: str = "newest") -> List[Tag]:
        """Find all tags for organization with sorting"""
        query = self.db.query(TagModel).filter(
            TagModel.organization_id == organization_id
        )

        # Apply sorting
        if sort_by == "oldest":
            query = query.order_by(TagModel.created_at.asc())
        elif sort_by == "name_asc":
            query = query.order_by(TagModel.tag_name.asc())
        elif sort_by == "name_desc":
            query = query.order_by(TagModel.tag_name.desc())
        else:  # newest (default)
            query = query.order_by(TagModel.created_at.desc())

        models = query.all()
        return [self._model_to_entity(model) for model in models]

    def update(self, tag: Tag) -> Tag:
        """Update existing tag"""
        model = (
            self.db.query(TagModel)
            .filter(
                TagModel.id == tag.id,
                TagModel.organization_id == tag.organization_id
            )
            .first()
        )

        if not model:
            raise ValueError(f"Tag with id {tag.id} not found")

        # Update fields
        model.tag_name = tag.tag_name
        model.description = tag.description
        model.color = tag.color

        self.db.commit()
        self.db.refresh(model)
        return self._model_to_entity(model)

    def delete(self, tag_id: int, organization_id: int) -> bool:
        """Delete tag by ID"""
        model = (
            self.db.query(TagModel)
            .filter(
                TagModel.id == tag_id,
                TagModel.organization_id == organization_id
            )
            .first()
        )

        if not model:
            return False

        self.db.delete(model)
        self.db.commit()
        return True

    def get_tag_usage_count(self, tag_id: int, organization_id: int) -> dict:
        """
        Get usage statistics for a tag
        Returns device_count from device_tags table

        TODO: Implement actual device count when DeviceTagModel is available
        """
        # STUB: DeviceTagModel not yet implemented
        # from services.auth.repositories.models import DeviceTagModel
        # device_count = (
        #     self.db.query(func.count(DeviceTagModel.device_id))
        #     .filter(DeviceTagModel.tag_id == tag_id)
        #     .scalar()
        # ) or 0

        return {
            "device_count": 0,  # TODO: Implement when DeviceTagModel is available
            "content_count": 0,  # Placeholder for future content feature
        }
