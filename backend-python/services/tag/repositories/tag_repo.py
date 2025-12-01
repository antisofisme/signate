"""
Tag Repository Implementation
Implements ITagRepository using SQLAlchemy
"""

from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, select, text
from ..domain.interfaces import ITagRepository
from ..domain.tag import Tag
from .models import TagModel, ContentTag
from services.device.repositories.models import DeviceTagModel


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
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            priority=model.priority,
            assigned_playlist_id=model.assigned_playlist_id,
            # Audit trail
            created_by_id=model.created_by_id,
            updated_by_id=model.updated_by_id,
            deleted_by_id=model.deleted_by_id,
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
            priority=entity.priority,
            assigned_playlist_id=entity.assigned_playlist_id,
            # Audit trail
            created_by_id=entity.created_by_id,
        )

    def create(self, tag: Tag) -> Tag:
        """Create a new tag"""
        model = self._entity_to_model(tag)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._model_to_entity(model)

    def find_by_id(self, tag_id: int, organization_id: int) -> Optional[Tag]:
        """Find tag by ID within organization (excludes soft deleted)"""
        model = (
            self.db.query(TagModel)
            .filter(
                TagModel.id == tag_id,
                TagModel.organization_id == organization_id,
                TagModel.deleted_at.is_(None)  # Exclude soft deleted
            )
            .first()
        )
        return self._model_to_entity(model) if model else None

    def find_by_name(self, tag_name: str, organization_id: int) -> Optional[Tag]:
        """Find tag by name within organization (excludes soft deleted)"""
        model = (
            self.db.query(TagModel)
            .filter(
                TagModel.tag_name == tag_name,
                TagModel.organization_id == organization_id,
                TagModel.deleted_at.is_(None)  # Exclude soft deleted
            )
            .first()
        )
        return self._model_to_entity(model) if model else None

    def find_all(self, organization_id: int, sort_by: str = "newest") -> List[Tag]:
        """Find all tags for organization with sorting and counts (excludes soft deleted)"""
        # Subquery for device count
        device_count_subq = (
            self.db.query(
                DeviceTagModel.tag_id,
                func.count(DeviceTagModel.device_id).label('device_count')
            )
            .group_by(DeviceTagModel.tag_id)
            .subquery()
        )

        # Subquery for content count
        content_count_subq = (
            self.db.query(
                ContentTag.tag_id,
                func.count(ContentTag.content_id).label('content_count')
            )
            .group_by(ContentTag.tag_id)
            .subquery()
        )

        # Main query with counts
        query = (
            self.db.query(
                TagModel,
                func.coalesce(device_count_subq.c.device_count, 0).label('device_count'),
                func.coalesce(content_count_subq.c.content_count, 0).label('content_count')
            )
            .outerjoin(device_count_subq, TagModel.id == device_count_subq.c.tag_id)
            .outerjoin(content_count_subq, TagModel.id == content_count_subq.c.tag_id)
            .filter(
                TagModel.organization_id == organization_id,
                TagModel.deleted_at.is_(None)  # Exclude soft deleted
            )
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

        results = query.all()

        # Convert to entities with counts
        tags = []
        for result in results:
            model = result[0]  # TagModel
            device_count = result[1]  # device_count
            content_count = result[2]  # content_count
            tag = self._model_to_entity_with_counts(model, device_count, content_count)
            tags.append(tag)

        return tags

    def _model_to_entity_with_counts(self, model: TagModel, device_count: int, content_count: int) -> Tag:
        """Convert SQLAlchemy model to domain entity with counts"""
        return Tag(
            id=model.id,
            tag_name=model.tag_name,
            description=model.description,
            color=model.color,
            organization_id=model.organization_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            priority=model.priority,
            assigned_playlist_id=model.assigned_playlist_id,
            # Audit trail
            created_by_id=model.created_by_id,
            updated_by_id=model.updated_by_id,
            deleted_by_id=model.deleted_by_id,
            # Counts
            device_count=device_count,
            content_count=content_count,
        )

    def update(self, tag: Tag, updated_by_id: Optional[int] = None) -> Tag:
        """Update existing tag with audit tracking"""
        model = (
            self.db.query(TagModel)
            .filter(
                TagModel.id == tag.id,
                TagModel.organization_id == tag.organization_id,
                TagModel.deleted_at.is_(None)  # Cannot update deleted tags
            )
            .first()
        )

        if not model:
            raise ValueError(f"Tag with id {tag.id} not found")

        # Update fields
        model.tag_name = tag.tag_name
        model.description = tag.description
        model.color = tag.color

        # Audit trail
        if updated_by_id is not None:
            model.updated_by_id = updated_by_id

        self.db.commit()
        self.db.refresh(model)
        return self._model_to_entity(model)

    def delete(self, tag_id: int, organization_id: int, deleted_by_id: Optional[int] = None) -> bool:
        """Soft delete tag by ID with audit tracking and cleanup relationships"""
        from datetime import datetime, timezone
        from sqlalchemy import text

        model = (
            self.db.query(TagModel)
            .filter(
                TagModel.id == tag_id,
                TagModel.organization_id == organization_id,
                TagModel.deleted_at.is_(None)  # Not already deleted
            )
            .first()
        )

        if not model:
            return False

        # Clean up all related records BEFORE soft delete
        # 1. Remove content_tags (unassign all content from this tag)
        self.db.execute(
            text("DELETE FROM content_tags WHERE tag_id = :tag_id"),
            {"tag_id": tag_id}
        )

        # 2. Remove device_tags (unassign all devices from this tag)
        self.db.execute(
            text("DELETE FROM device_tags WHERE tag_id = :tag_id"),
            {"tag_id": tag_id}
        )

        # 3. Remove content_assignments (remove tag-based content assignments)
        self.db.execute(
            text("DELETE FROM content_assignments WHERE tag_id = :tag_id"),
            {"tag_id": tag_id}
        )

        # 4. Remove playlist_assignments (remove tag-based playlist assignments)
        self.db.execute(
            text("DELETE FROM playlist_assignments WHERE tag_id = :tag_id"),
            {"tag_id": tag_id}
        )

        # Soft delete with audit trail
        model.deleted_at = datetime.now(timezone.utc)
        if deleted_by_id is not None:
            model.deleted_by_id = deleted_by_id

        self.db.commit()
        return True

    def get_tag_usage_count(self, tag_id: int, organization_id: int) -> dict:
        """
        Get usage statistics for a tag
        Returns device_count and content_count
        """
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

    def assign_to_content(
        self, tag_id: int, content_id: int, organization_id: int, assigned_by_id: Optional[int] = None
    ) -> bool:
        """Assign tag to a content item with audit tracking"""
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

        # Create assignment with audit tracking
        assignment = ContentTag(
            content_id=content_id,
            tag_id=tag_id,
            assigned_by_id=assigned_by_id
        )
        self.db.add(assignment)
        self.db.commit()
        return True

    def unassign_from_content(self, tag_id: int, content_id: int, organization_id: int) -> bool:
        """Unassign tag from a content item"""
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

    def assign_to_contents(
        self, tag_id: int, content_ids: List[int], organization_id: int, assigned_by_id: Optional[int] = None
    ) -> dict:
        """Bulk assign tag to multiple content items with audit tracking"""
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

        # Bulk insert new assignments with audit tracking
        if new_assignments:
            assignments = [
                ContentTag(content_id=cid, tag_id=tag_id, assigned_by_id=assigned_by_id)
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
    
    def find_by_device_id(self, device_id: int) -> List[Tag]:
        """Find all tags assigned to a device"""
        from services.device.repositories.models import device_tags

        # Query tags through device_tags junction table using ORM
        tags = (
            self.db.query(TagModel)
            .options(
                selectinload(TagModel.assigned_playlist)
            )
            .join(device_tags, device_tags.c.tag_id == TagModel.id)
            .filter(device_tags.c.device_id == device_id)
            .order_by(TagModel.tag_name)
            .all()
        )

        return [self._model_to_entity(tag) for tag in tags]

    # ==========================================================================
    # DEVICE-TAG OPERATIONS
    # ==========================================================================

    def get_devices_by_tag(self, tag_id: int, organization_id: int) -> List[dict]:
        """Get all devices assigned to a tag"""
        from sqlalchemy import text
        from services.device.repositories.models import DeviceModel

        # First verify tag exists and belongs to org
        tag = self.find_by_id(tag_id, organization_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found or access denied")

        # Query devices through device_tags junction table
        query = text("""
            SELECT d.id, d.device_name, d.device_type, d.status, dt.assigned_at
            FROM devices d
            JOIN device_tags dt ON dt.device_id = d.id
            WHERE dt.tag_id = :tag_id
              AND d.organization_id = :organization_id
            ORDER BY d.device_name
        """)

        results = self.db.execute(query, {
            "tag_id": tag_id,
            "organization_id": organization_id
        }).fetchall()

        return [
            {
                "id": row.id,
                "device_name": row.device_name,
                "device_type": row.device_type,
                "status": row.status,
                "assigned_at": row.assigned_at
            }
            for row in results
        ]

    def assign_tag_to_devices(self, tag_id: int, device_ids: List[int], organization_id: int) -> dict:
        """Bulk assign tag to multiple devices"""
        from sqlalchemy import text
        from datetime import datetime, timezone

        # Verify tag exists and belongs to org
        tag = self.find_by_id(tag_id, organization_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found or access denied")

        # Get valid device IDs (same org)
        valid_devices_query = text("""
            SELECT id FROM devices
            WHERE id = ANY(:device_ids) AND organization_id = :organization_id
        """)
        valid_devices = self.db.execute(valid_devices_query, {
            "device_ids": device_ids,
            "organization_id": organization_id
        }).fetchall()
        valid_ids = [d.id for d in valid_devices]

        assigned = 0
        skipped = 0
        failed = len(device_ids) - len(valid_ids)  # Devices not found or wrong org

        for device_id in valid_ids:
            # Check if already assigned
            check_query = text("""
                SELECT id FROM device_tags
                WHERE device_id = :device_id AND tag_id = :tag_id
            """)
            existing = self.db.execute(check_query, {
                "device_id": device_id,
                "tag_id": tag_id
            }).fetchone()

            if existing:
                skipped += 1
                continue

            # Insert new assignment
            insert_query = text("""
                INSERT INTO device_tags (device_id, tag_id, assigned_at)
                VALUES (:device_id, :tag_id, :assigned_at)
            """)
            self.db.execute(insert_query, {
                "device_id": device_id,
                "tag_id": tag_id,
                "assigned_at": datetime.now(timezone.utc)
            })
            assigned += 1

        self.db.commit()

        return {
            "success": True,
            "assigned": assigned,
            "skipped": skipped,
            "failed": failed,
            "message": f"Assigned tag to {assigned} device(s)"
        }

    def unassign_tag_from_devices(self, tag_id: int, device_ids: List[int], organization_id: int) -> dict:
        """Bulk unassign tag from multiple devices"""
        from sqlalchemy import text

        # Verify tag exists and belongs to org
        tag = self.find_by_id(tag_id, organization_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found or access denied")

        # Get valid device IDs (same org)
        valid_devices_query = text("""
            SELECT id FROM devices
            WHERE id = ANY(:device_ids) AND organization_id = :organization_id
        """)
        valid_devices = self.db.execute(valid_devices_query, {
            "device_ids": device_ids,
            "organization_id": organization_id
        }).fetchall()
        valid_ids = [d.id for d in valid_devices]

        unassigned = 0
        not_found = len(device_ids) - len(valid_ids)  # Devices not found or wrong org

        for device_id in valid_ids:
            # Delete assignment
            delete_query = text("""
                DELETE FROM device_tags
                WHERE device_id = :device_id AND tag_id = :tag_id
            """)
            result = self.db.execute(delete_query, {
                "device_id": device_id,
                "tag_id": tag_id
            })

            if result.rowcount > 0:
                unassigned += 1
            else:
                not_found += 1  # Was not assigned

        self.db.commit()

        return {
            "success": True,
            "unassigned": unassigned,
            "not_found": not_found,
            "message": f"Unassigned tag from {unassigned} device(s)"
        }
