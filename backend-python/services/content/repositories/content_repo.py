"""
Content Repository Implementation
Database access for content
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..domain.content import Content
from ..domain.interfaces import IContentRepository
from .models import ContentModel
from shared.config import settings


class ContentRepository(IContentRepository):
    """Content repository implementation using SQLAlchemy"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, content: Content) -> Content:
        """Create new content"""
        db_content = ContentModel(
            title=content.title,
            description=content.description,
            content_type=content.content_type,
            file_path=content.file_path,
            file_url=content.file_url,
            storage_key=content.storage_key,
            file_hash=content.file_hash,
            file_size=content.file_size,
            duration=content.duration,
            is_active=content.is_active,
            mime_type=content.mime_type,
            original_filename=content.original_filename,
            file_extension=content.file_extension,
            resolution=content.resolution,
            width=content.width,
            height=content.height,
            codec=content.codec,
            fps=content.fps,
            bitrate=content.bitrate,
            media_duration=content.media_duration,
            video_start_time=content.video_start_time,
            video_end_time=content.video_end_time,
            audio_codec=content.audio_codec,
            audio_bitrate=content.audio_bitrate,
            audio_sample_rate=content.audio_sample_rate,
            audio_channels=content.audio_channels,
            transcoding_status=content.transcoding_status,
            upload_status=content.upload_status,
            organization_id=content.organization_id,
            uploaded_by_id=content.uploaded_by_id)

        self.db.add(db_content)
        self.db.commit()
        self.db.refresh(db_content)

        return self._to_entity(db_content)

    def find_by_id(self, content_id: int, organization_id: int = None) -> Optional[Content]:
        """Find content by ID (organization-scoped if org_id provided)"""
        query = self.db.query(ContentModel).filter(
            ContentModel.id == content_id,
            ContentModel.deleted_at.is_(None)
        )

        if organization_id is not None:
            query = query.filter(ContentModel.organization_id == organization_id)

        db_content = query.first()
        return self._to_entity(db_content) if db_content else None

    def find_by_ids(self, content_ids: List[int], organization_id: int = None) -> List[Content]:
        """
        Batch fetch contents by IDs (performance optimization to prevent N+1 queries)

        ⚡ PERFORMANCE: Use this instead of multiple find_by_id() calls

        Args:
            content_ids: List of content IDs to fetch
            organization_id: Optional organization filter

        Returns:
            List of Content entities (only existing, active contents)
        """
        if not content_ids:
            return []

        query = self.db.query(ContentModel).filter(
            ContentModel.id.in_(content_ids),
            ContentModel.deleted_at.is_(None)
        )

        if organization_id is not None:
            query = query.filter(ContentModel.organization_id == organization_id)

        db_contents = query.all()
        return [self._to_entity(c) for c in db_contents]

    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Content], int]:
        """List content with filters"""
        query = self.db.query(ContentModel).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.is_(None)
        )

        # Apply filters
        if content_type:
            query = query.filter(ContentModel.content_type == content_type)
        if is_active is not None:
            query = query.filter(ContentModel.is_active == is_active)

        # Get total count
        total = query.count()

        # Get paginated results
        db_contents = query.order_by(ContentModel.created_at.desc()).offset(skip).limit(limit).all()

        contents = [self._to_entity(c) for c in db_contents]
        return contents, total

    def find_by_hash(self, file_hash: str, organization_id: int) -> Optional[Content]:
        """Find content by file hash (deduplication)"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.file_hash == file_hash,
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.is_(None)
        ).first()

        return self._to_entity(db_content) if db_content else None

    def update(self, content: Content) -> Content:
        """Update content metadata"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content.id
        ).first()

        if not db_content:
            raise ValueError(f"Content {content.id} not found")

        # Update fields
        db_content.title = content.title
        db_content.description = content.description
        db_content.duration = content.duration
        db_content.is_active = content.is_active
        db_content.transcoding_status = content.transcoding_status
        db_content.transcoding_job_id = content.transcoding_job_id
        db_content.transcoding_progress = content.transcoding_progress
        db_content.transcoding_error = content.transcoding_error
        db_content.hls_master_playlist_path = content.hls_master_playlist_path
        db_content.hls_master_playlist_url = content.hls_master_playlist_url
        db_content.hls_variants = content.hls_variants
        db_content.thumbnail_path = content.thumbnail_path
        db_content.thumbnail_url = content.thumbnail_url
        db_content.thumbnail_generated_at = content.thumbnail_generated_at
        db_content.upload_status = content.upload_status

        self.db.commit()
        self.db.refresh(db_content)

        return self._to_entity(db_content)

    def soft_delete(self, content_id: int, organization_id: int) -> bool:
        """
        Soft delete content and cleanup playlist associations

        CRITICAL FIX: Remove content from all playlists to prevent orphaned data
        """
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id,
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.is_(None)
        ).first()

        if not db_content:
            return False

        # CRITICAL FIX: Remove content from all playlists BEFORE soft delete
        from services.playlist.repositories.models import PlaylistContentModel

        deleted_count = self.db.query(PlaylistContentModel).filter(
            PlaylistContentModel.content_id == content_id
        ).delete(synchronize_session=False)

        # Log cleanup for audit trail
        if deleted_count > 0:
            from shared.logging import logger
            logger.info(
                f"Removed content {content_id} from {deleted_count} playlist(s) during soft delete"
            )

        # Soft delete the content
        db_content.deleted_at = datetime.now(timezone.utc)
        db_content.is_active = False
        self.db.commit()

        # CRITICAL FIX: Invalidate content resolver cache for affected devices
        # This ensures devices fetch updated content immediately
        try:
            from shared.cache import cache
            cache.invalidate_pattern("content_resolution:*")
            logger.info(f"Invalidated content resolution cache for deleted content {content_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
            # Don't fail the deletion if cache invalidation fails

        return True

    def find_deleted_content(self, days: int = 30) -> List[Content]:
        """Find soft-deleted content older than specified days"""
        threshold = datetime.now(timezone.utc) - timedelta(days=days)

        db_contents = self.db.query(ContentModel).filter(
            ContentModel.deleted_at.isnot(None),
            ContentModel.deleted_at < threshold
        ).all()

        return [self._to_entity(c) for c in db_contents]

    def hard_delete(self, content_id: int) -> bool:
        """Permanently delete content"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id
        ).first()

        if not db_content:
            return False

        self.db.delete(db_content)
        self.db.commit()

        return True

    def get_storage_stats(self, organization_id: int) -> Dict[str, Any]:
        """Get storage statistics"""
        # Total files and size
        total_query = self.db.query(
            func.count(ContentModel.id).label('count'),
            func.sum(ContentModel.file_size).label('total_size')
        ).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.is_(None)
        ).first()

        total_files = total_query.count or 0
        total_size_bytes = int(total_query.total_size or 0)

        # By type
        by_type = {}
        for content_type in ['image', 'video', 'audio']:
            type_query = self.db.query(
                func.count(ContentModel.id).label('count'),
                func.sum(ContentModel.file_size).label('total_size')
            ).filter(
                ContentModel.organization_id == organization_id,
                ContentModel.content_type == content_type,
                ContentModel.deleted_at.is_(None)
            ).first()

            count = type_query.count or 0
            size_bytes = int(type_query.total_size or 0)

            by_type[content_type] = {
                'count': count,
                'size_bytes': size_bytes,
                'size_readable': self._format_size(size_bytes)
            }

        return {
            'total_files': total_files,
            'total_size_bytes': total_size_bytes,
            'total_size_readable': self._format_size(total_size_bytes),
            'by_type': by_type
        }

    def update_transcoding_status(
        self,
        content_id: int,
        status: str,
        job_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update transcoding status"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id
        ).first()

        if not db_content:
            return False

        db_content.transcoding_status = status
        if job_id:
            db_content.transcoding_job_id = job_id
        if error:
            db_content.transcoding_error = error

        self.db.commit()
        return True

    def update_hls_info(
        self,
        content_id: int,
        master_playlist_path: str,
        master_playlist_url: str,
        variants: Dict[str, Any]
    ) -> bool:
        """Update HLS transcoding information"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id
        ).first()

        if not db_content:
            return False

        db_content.hls_master_playlist_path = master_playlist_path
        db_content.hls_master_playlist_url = master_playlist_url
        db_content.hls_variants = variants
        db_content.transcoding_status = 'completed'
        db_content.transcoding_progress = 100

        self.db.commit()
        return True

    def update_thumbnail(
        self,
        content_id: int,
        thumbnail_path: str,
        thumbnail_url: str
    ) -> bool:
        """Update thumbnail information"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id
        ).first()

        if not db_content:
            return False

        db_content.thumbnail_path = thumbnail_path
        db_content.thumbnail_url = thumbnail_url
        db_content.thumbnail_generated_at = datetime.now(timezone.utc)

        self.db.commit()
        return True

    def _to_entity(self, db_content: ContentModel) -> Content:
        """Convert database model to domain entity"""
        # Construct HLS master playlist URL if path exists but URL is empty
        hls_master_playlist_url = db_content.hls_master_playlist_url

        if db_content.hls_master_playlist_path and not hls_master_playlist_url:
            # Path format: "2025/11/org_4/e9dff2be-eb88-41c8-b5aa-a47b9e957fd6_hls/master.m3u8"
            # URL format: "http://192.168.5.12:8001/content/hls/2025/11/org_4/e9dff2be-eb88-41c8-b5aa-a47b9e957fd6/master.m3u8"

            path_parts = db_content.hls_master_playlist_path.split('/')
            if len(path_parts) >= 4:
                year = path_parts[0]
                month = path_parts[1]
                org_dir = path_parts[2]  # org_4
                hls_dir = path_parts[3]  # {uuid}_hls

                # Extract UUID from {uuid}_hls folder name
                content_uuid = hls_dir.replace('_hls', '')

                # Construct HLS URL
                hls_master_playlist_url = f"{settings.PUBLIC_BASE_URL}/content/hls/{year}/{month}/{org_dir}/{content_uuid}/master.m3u8"

        return Content(
            id=db_content.id,
            title=db_content.title,
            description=db_content.description,
            content_type=db_content.content_type,
            file_path=db_content.file_path,
            file_url=db_content.file_url,
            storage_key=db_content.storage_key,
            file_hash=db_content.file_hash,
            file_size=db_content.file_size,
            duration=db_content.duration,
            is_active=db_content.is_active,
            mime_type=db_content.mime_type,
            original_filename=db_content.original_filename,
            file_extension=db_content.file_extension,
            resolution=db_content.resolution,
            width=db_content.width,
            height=db_content.height,
            codec=db_content.codec,
            fps=db_content.fps,
            bitrate=db_content.bitrate,
            media_duration=db_content.media_duration,
            video_start_time=db_content.video_start_time,
            video_end_time=db_content.video_end_time,
            audio_codec=db_content.audio_codec,
            audio_bitrate=db_content.audio_bitrate,
            audio_sample_rate=db_content.audio_sample_rate,
            audio_channels=db_content.audio_channels,
            transcoding_status=db_content.transcoding_status,
            transcoding_job_id=db_content.transcoding_job_id,
            transcoding_progress=db_content.transcoding_progress,
            transcoding_error=db_content.transcoding_error,
            hls_master_playlist_path=db_content.hls_master_playlist_path,
            hls_master_playlist_url=hls_master_playlist_url,
            hls_variants=db_content.hls_variants,
            thumbnail_path=db_content.thumbnail_path,
            thumbnail_url=db_content.thumbnail_url,
            thumbnail_generated_at=db_content.thumbnail_generated_at,
            upload_status=db_content.upload_status,
            organization_id=db_content.organization_id,
            uploaded_by_id=db_content.uploaded_by_id,
            created_at=db_content.created_at,
            updated_at=db_content.updated_at,
            deleted_at=db_content.deleted_at
        )

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


# Dependency injection helper
from sqlalchemy.orm import Session
from shared.database import get_db
from fastapi import Depends


def get_content_repository(db: Session = Depends(get_db)) -> ContentRepository:
    """Get content repository instance"""
    return ContentRepository(db)
