"""
Content Repository - Database Access untuk Content/Media Entity
===============================================================

CENTRALIZED QUERIES untuk contents table
Semua query content WAJIB melalui repository ini
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime

from app.repositories.base import BaseRepository
from app.models.content import Content


class ContentRepository(BaseRepository):
    """
    Content Repository dengan media-specific queries

    Handles: images, videos, HTML templates, URLs
    """

    def __init__(self, db: Session):
        super().__init__(Content, db)
        self.db = db

    # =========================================================================
    # CONTENT-SPECIFIC QUERIES
    # =========================================================================

    def get_by_organization(
        self,
        organization_id: int,
        content_type: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None
    ) -> List[Any]:
        """
        Get content by organization dengan filter

        Example:
            # Get all active videos
            videos = content_repo.get_by_organization(
                org_id=1,
                content_type="video",
                is_active=True
            )
        """
        # Build filters
        query_filters = filters or {}
        query_filters["organization_id"] = organization_id

        if content_type:
            query_filters["content_type"] = content_type

        # Apply filters to query
        query = self.db.query(self.model)
        for key, value in query_filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        # Apply search if provided (search in title, description, and tags)
        if search and len(search.strip()) >= 2:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (self.model.title.ilike(search_term)) |
                (self.model.description.ilike(search_term)) |
                (self.model.tags.astext.ilike(search_term))  # Search in JSON tags array
            )

        # Apply pagination and order
        query = query.order_by(self.model.created_at.desc())
        return query.offset(skip).limit(limit).all()

    def get_by_playlist(self, playlist_id: int) -> List[Any]:
        """
        Get all content dalam playlist tertentu

        Returns content ordered by play_order
        """
        from app.models.playlist_content import PlaylistContent

        query = self.db.query(self.model).join(PlaylistContent).filter(
            PlaylistContent.playlist_id == playlist_id
        ).order_by(PlaylistContent.play_order)

        return query.all()

    def get_active_scheduled_content(
        self,
        organization_id: int,
        current_time: Optional[datetime] = None
    ) -> List[Any]:
        """
        Get content yang scheduled untuk ditampilkan sekarang

        Business rule:
        - is_active = True
        - start_date <= now <= end_date (or NULL)
        - is_enabled = True
        """
        if not current_time:
            current_time = datetime.utcnow()

        query = self.db.query(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.is_active == True,
                self.model.is_enabled == True,
                or_(
                    self.model.start_date.is_(None),
                    self.model.start_date <= current_time
                ),
                or_(
                    self.model.end_date.is_(None),
                    self.model.end_date >= current_time
                )
            )
        )

        return query.all()

    def get_by_tags(
        self,
        organization_id: int,
        tags: List[str],
        content_type: Optional[str] = None
    ) -> List[Any]:
        """
        Get content by tags (stored as JSON array)

        Example:
            # Get content dengan tag "promo" atau "announcement"
            content = content_repo.get_by_tags(
                organization_id=1,
                tags=["promo", "announcement"]
            )

            # Get video content dengan specific tags
            videos = content_repo.get_by_tags(
                organization_id=1,
                tags=["product", "2025"],
                content_type="video"
            )
        """
        conditions = [
            self.model.organization_id == organization_id,
            self.model.is_active == True
        ]

        # Filter by tags (JSON array contains any of the provided tags)
        # Search in JSON array text representation (simple and database-agnostic)
        if tags:
            tag_conditions = []
            for tag in tags:
                # Search tag in JSON text (works with any database)
                tag_conditions.append(
                    self.model.tags.astext.ilike(f'%"{tag}"%')
                )
            conditions.append(or_(*tag_conditions))

        if content_type:
            conditions.append(self.model.content_type == content_type)

        query = self.db.query(self.model).filter(and_(*conditions))
        return query.all()

    def search_content(
        self,
        organization_id: int,
        search_term: str,
        content_type: Optional[str] = None
    ) -> List[Any]:
        """
        Search content by title, description, or filename

        Example:
            results = content_repo.search_content(1, "promo")
        """
        conditions = [
            self.model.organization_id == organization_id,
            or_(
                self.model.title.ilike(f"%{search_term}%"),
                self.model.description.ilike(f"%{search_term}%"),
                self.model.tags.astext.ilike(f"%{search_term}%")  # Search in tags too
            )
        ]

        if content_type:
            conditions.append(self.model.content_type == content_type)

        query = self.db.query(self.model).filter(and_(*conditions))
        return query.all()

    def get_content_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get statistik content untuk dashboard

        Returns:
            {
                "total": 150,
                "by_type": {
                    "image": 80,
                    "video": 50,
                    "html": 15,
                    "url": 5
                },
                "active": 130,
                "inactive": 20,
                "total_size_mb": 5420.5
            }
        """
        total = self.count({"organization_id": organization_id})

        # Count by type
        type_stats = self.db.query(
            self.model.content_type,
            func.count(self.model.id)
        ).filter(
            self.model.organization_id == organization_id
        ).group_by(self.model.content_type).all()

        by_type = {t: c for t, c in type_stats}

        # Active/Inactive count
        active = self.count({
            "organization_id": organization_id,
            "is_active": True
        })

        # Total file size
        total_size_query = self.db.query(
            func.sum(self.model.file_size)
        ).filter(
            self.model.organization_id == organization_id
        ).scalar()

        total_size_mb = (total_size_query or 0) / (1024 * 1024)

        return {
            "total": total,
            "by_type": by_type,
            "active": active,
            "inactive": total - active,
            "total_size_mb": round(total_size_mb, 2)
        }

    def get_expired_content(self, organization_id: int) -> List[Any]:
        """
        Get content yang sudah expired (end_date < now)

        Useful untuk cleanup tasks
        """
        now = datetime.utcnow()

        query = self.db.query(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.end_date.isnot(None),
                self.model.end_date < now
            )
        )

        return query.all()

    def get_large_files(
        self,
        organization_id: int,
        min_size_mb: float = 100.0
    ) -> List[Any]:
        """
        Get content dengan file size > threshold

        Useful untuk storage optimization
        """
        min_bytes = int(min_size_mb * 1024 * 1024)

        query = self.db.query(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.file_size > min_bytes
            )
        ).order_by(self.model.file_size.desc())

        return query.all()

    def update_processing_status(
        self,
        id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update status processing (transcoding, conversion, dll)

        Status: pending, processing, completed, failed
        """
        updates = {
            "processing_status": status,
            "updated_at": datetime.utcnow()
        }

        if error_message:
            updates["error_message"] = error_message

        if status == "completed":
            updates["processed_at"] = datetime.utcnow()

        return self.update(id, updates) is not None

    def mark_as_deleted(self, id: int) -> bool:
        """
        Soft delete - mark sebagai deleted tanpa hapus dari DB

        Set is_active=False, deleted_at=now
        """
        return self.update(id, {
            "is_active": False,
            "deleted_at": datetime.utcnow()
        }) is not None

    def get_content_usage_in_playlists(self, content_id: int) -> List[Dict]:
        """
        Get playlist mana saja yang menggunakan content ini

        Useful sebelum delete content
        """
        from app.models.playlist_content import PlaylistContent
        from app.models.playlist import Playlist

        query = self.db.query(
            Playlist.id,
            Playlist.name,
            PlaylistContent.play_order
        ).join(PlaylistContent).filter(
            PlaylistContent.content_id == content_id
        ).all()

        return [
            {"playlist_id": p.id, "name": p.name, "order": p.play_order}
            for p in query
        ]

    def count_by_organization(
        self,
        organization_id: int,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Count content by organization with filters

        Args:
            organization_id: Organization ID
            filters: Filter criteria
            search: Search query for title/description

        Returns:
            Total count of matching content
        """
        from sqlalchemy import func

        query = self.db.query(func.count(self.model.id))

        # Apply base filter
        query = query.filter(self.model.organization_id == organization_id)

        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and key != "organization_id":
                    query = query.filter(getattr(self.model, key) == value)

        # Apply search
        if search and len(search.strip()) >= 2:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (self.model.title.ilike(search_term)) |
                (self.model.description.ilike(search_term))
            )

        return query.scalar() or 0

    def get_organization_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Alias for get_content_stats for consistency with endpoint naming

        Returns comprehensive content statistics for organization
        """
        return self.get_content_stats(organization_id)

    def get_largest_files(
        self,
        organization_id: int,
        limit: int = 5
    ) -> List[Any]:
        """
        Alias for get_large_files with organization filter

        Returns largest content files for organization
        """
        return self.get_large_files(organization_id=organization_id, limit=limit)
