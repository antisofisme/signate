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
        Returns device_count and content_count
        """
        # Import content_tags model
        from services.tag.models import ContentTag

        # Count content assignments
        content_count = (
            self.db.query(func.count(ContentTag.id))
            .filter(ContentTag.tag_id == tag_id)
            .scalar()
        ) or 0

        return {
            "device_count": 0,  # TODO: Implement when DeviceTagModel is available
            "content_count": content_count,
        }

    def assign_to_content(self, tag_id: int, content_id: int, organization_id: int) -> bool:
        """Assign tag to a content item"""
        from services.tag.models import ContentTag
        from services.content.repositories.models import ContentModel as Content

        # Verify tag belongs to organization
        tag = self.find_by_id(tag_id, organization_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found or access denied")

        # Verify content belongs to organization
        content = (
            self.db.query(Content)
            .filter(
                Content.id == content_id,
                Content.organization_id == organization_id,
                Content.deleted_at.is_(None)
            )
            .first()
        )
        if not content:
            raise ValueError(f"Content {content_id} not found or access denied")

        # Check if already assigned
        existing = (
            self.db.query(ContentTag)
            .filter(
                ContentTag.content_id == content_id,
                ContentTag.tag_id == tag_id
            )
            .first()
        )
        if existing:
            return False  # Already assigned

        # Create assignment
        assignment = ContentTag(content_id=content_id, tag_id=tag_id)
        self.db.add(assignment)
        self.db.commit()
        return True

    def unassign_from_content(self, tag_id: int, content_id: int, organization_id: int) -> bool:
        """Unassign tag from a content item"""
        from services.tag.models import ContentTag

        # Verify tag belongs to organization
        tag = self.find_by_id(tag_id, organization_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found or access denied")

        # Find and delete assignment
        assignment = (
            self.db.query(ContentTag)
            .filter(
                ContentTag.content_id == content_id,
                ContentTag.tag_id == tag_id
            )
            .first()
        )

        if not assignment:
            return False  # Not assigned

        self.db.delete(assignment)
        self.db.commit()
        return True

    def assign_to_contents(self, tag_id: int, content_ids: List[int], organization_id: int) -> dict:
        """Bulk assign tag to multiple content items"""
        from services.tag.models import ContentTag
        from services.content.repositories.models import ContentModel as Content

        # Verify tag belongs to organization
        tag = self.find_by_id(tag_id, organization_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found or access denied")

        # Get valid content IDs (belong to organization and not deleted)
        valid_content_ids = (
            self.db.query(Content.id)
            .filter(
                Content.id.in_(content_ids),
                Content.organization_id == organization_id,
                Content.deleted_at.is_(None)
            )
            .all()
        )
        valid_ids = [c[0] for c in valid_content_ids]

        # Get already assigned content IDs
        already_assigned = (
            self.db.query(ContentTag.content_id)
            .filter(
                ContentTag.tag_id == tag_id,
                ContentTag.content_id.in_(valid_ids)
            )
            .all()
        )
        assigned_ids = set([c[0] for c in already_assigned])

        # Calculate new assignments
        new_assignments = [cid for cid in valid_ids if cid not in assigned_ids]

        # Bulk insert new assignments
        if new_assignments:
            assignments = [
                ContentTag(content_id=cid, tag_id=tag_id)
                for cid in new_assignments
            ]
            self.db.bulk_save_objects(assignments)
            self.db.commit()

        return {
            "assigned": len(new_assignments),
            "skipped": len(assigned_ids),
            "failed": len(content_ids) - len(valid_ids)
        }

    def unassign_from_contents(self, tag_id: int, content_ids: List[int], organization_id: int) -> dict:
        """Bulk unassign tag from multiple content items"""
        from services.tag.models import ContentTag

        # Verify tag belongs to organization
        tag = self.find_by_id(tag_id, organization_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found or access denied")

        # Delete assignments
        result = (
            self.db.query(ContentTag)
            .filter(
                ContentTag.tag_id == tag_id,
                ContentTag.content_id.in_(content_ids)
            )
            .delete(synchronize_session=False)
        )
        self.db.commit()

        return {
            "unassigned": result,
            "not_found": len(content_ids) - result
        }

    def get_content_tags(self, content_id: int, organization_id: int) -> List[Tag]:
        """Get all tags assigned to a content item"""
        from services.tag.models import ContentTag
        from services.content.repositories.models import ContentModel as Content

        # Verify content belongs to organization
        content = (
            self.db.query(Content)
            .filter(
                Content.id == content_id,
                Content.organization_id == organization_id,
                Content.deleted_at.is_(None)
            )
            .first()
        )
        if not content:
            raise ValueError(f"Content {content_id} not found or access denied")

        # Get tags
        tags = (
            self.db.query(TagModel)
            .join(ContentTag, ContentTag.tag_id == TagModel.id)
            .filter(
                ContentTag.content_id == content_id,
                TagModel.organization_id == organization_id
            )
            .all()
        )

        return [self._model_to_entity(tag) for tag in tags]
