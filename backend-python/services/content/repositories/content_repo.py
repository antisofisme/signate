"""
Content Repository Implementation
Database access for content
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, asc, desc

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
            # HLS info (for duplicates that reuse existing transcoded files)
            hls_master_playlist_path=content.hls_master_playlist_path,
            hls_master_playlist_url=content.hls_master_playlist_url,
            hls_variants=content.hls_variants,
            # Thumbnail info (for duplicates that reuse existing thumbnails)
            thumbnail_path=content.thumbnail_path,
            thumbnail_url=content.thumbnail_url,
            thumbnail_generated_at=content.thumbnail_generated_at,
            # Status & Transcoding tracking
            transcoding_status=content.transcoding_status,
            transcoding_job_id=content.transcoding_job_id,
            transcoding_progress=content.transcoding_progress,
            transcoding_error=content.transcoding_error,
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

    # Valid sortable columns for content
    SORTABLE_COLUMNS = {
        'original_filename': ContentModel.original_filename,
        'content_type': ContentModel.content_type,
        'file_size': ContentModel.file_size,
        'duration': ContentModel.duration,
        'is_active': ContentModel.is_active,
        'created_at': ContentModel.created_at,
        'updated_at': ContentModel.updated_at,
    }

    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        tag_ids: Optional[List[int]] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> Tuple[List[Content], int]:
        """List content with filters including tag-based filtering and sorting"""
        from services.tag.repositories.models import ContentTag

        query = self.db.query(ContentModel).options(
            selectinload(ContentModel.uploader)  # Load uploader for uploaded_by_name
        ).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.is_(None)
        )

        # Apply filters
        if content_type:
            query = query.filter(ContentModel.content_type == content_type)
        if is_active is not None:
            query = query.filter(ContentModel.is_active == is_active)

        # Filter by tags (content must have ALL specified tags)
        if tag_ids and len(tag_ids) > 0:
            # Subquery to find content IDs that have all the specified tags
            for tag_id in tag_ids:
                subquery = self.db.query(ContentTag.content_id).filter(
                    ContentTag.tag_id == tag_id
                ).subquery()
                query = query.filter(ContentModel.id.in_(subquery))

        # Get total count
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
            query = query.order_by(desc(ContentModel.created_at))

        # Get paginated results
        db_contents = query.offset(skip).limit(limit).all()

        contents = [self._to_entity(c) for c in db_contents]
        return contents, total

    def find_by_hash(self, file_hash: str, organization_id: int) -> Optional[Content]:
        """
        Find content by file hash (deduplication).

        Searches BOTH active and deleted content to prevent duplicate storage.
        Even if a file is in recycle bin, we can still reuse its physical file.
        Prefers active content over deleted if both exist.
        """
        # First try to find active content with this hash
        db_content = self.db.query(ContentModel).filter(
            ContentModel.file_hash == file_hash,
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.is_(None)
        ).first()

        # If no active content, check deleted content (recycle bin)
        # The physical file is still there until permanent delete
        if not db_content:
            db_content = self.db.query(ContentModel).filter(
                ContentModel.file_hash == file_hash,
                ContentModel.organization_id == organization_id,
                ContentModel.deleted_at.isnot(None)
            ).first()

        return self._to_entity(db_content) if db_content else None

    def update(self, content: Content, updated_by_id: Optional[int] = None) -> Content:
        """Update content metadata with audit tracking (excludes soft-deleted)"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content.id,
            ContentModel.deleted_at.is_(None)  # Exclude soft-deleted
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

        # Audit tracking
        if updated_by_id is not None:
            db_content.updated_by_id = updated_by_id

        self.db.commit()
        self.db.refresh(db_content)

        return self._to_entity(db_content)

    def soft_delete(
        self, content_id: int, organization_id: int, deleted_by_id: Optional[int] = None
    ) -> bool:
        """
        Soft delete content and cleanup playlist associations with audit tracking

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
        from shared.logging import app_logger as logger

        deleted_count = self.db.query(PlaylistContentModel).filter(
            PlaylistContentModel.content_id == content_id
        ).delete(synchronize_session=False)

        # Log cleanup for audit trail
        if deleted_count > 0:
            logger.info(
                f"Removed content {content_id} from {deleted_count} playlist(s) during soft delete"
            )

        # Soft delete the content with audit tracking
        db_content.deleted_at = datetime.now(timezone.utc)
        db_content.is_active = False
        if deleted_by_id is not None:
            db_content.deleted_by_id = deleted_by_id
        self.db.commit()

        # CRITICAL FIX: Invalidate content resolver cache for affected devices
        # This ensures devices fetch updated content immediately
        try:
            from shared.cache import cache
            cache.clear_pattern("content_resolution:*")
            cache.invalidate_content(content_id, organization_id)
            logger.info(f"Invalidated cache for deleted content {content_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
            # Don't fail the deletion if cache invalidation fails

        return True

    def find_deleted_content(self, days: int = 30) -> List[Content]:
        """Find soft-deleted content older than specified days (for cleanup)"""
        threshold = datetime.now(timezone.utc) - timedelta(days=days)

        db_contents = self.db.query(ContentModel).filter(
            ContentModel.deleted_at.isnot(None),
            ContentModel.deleted_at < threshold
        ).all()

        return [self._to_entity(c) for c in db_contents]

    def find_all_deleted(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> Tuple[List[Content], int]:
        """List soft-deleted content for an organization (recycle bin)"""
        query = self.db.query(ContentModel).options(
            selectinload(ContentModel.uploader),  # Load uploader for uploaded_by_name
            selectinload(ContentModel.deleter)    # Load deleter for deleted_by_name
        ).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.isnot(None)  # Only deleted content
        )

        # Apply filters
        if content_type:
            query = query.filter(ContentModel.content_type == content_type)

        # Get total count
        total = query.count()

        # Apply sorting
        if sort_by and sort_by in self.SORTABLE_COLUMNS:
            column = self.SORTABLE_COLUMNS[sort_by]
            if sort_dir == 'desc':
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        elif sort_by == 'deleted_at':
            if sort_dir == 'asc':
                query = query.order_by(asc(ContentModel.deleted_at))
            else:
                query = query.order_by(desc(ContentModel.deleted_at))
        else:
            # Default: most recently deleted first
            query = query.order_by(ContentModel.deleted_at.desc())

        # Get paginated results
        db_contents = query.offset(skip).limit(limit).all()

        contents = [self._to_entity(c) for c in db_contents]
        return contents, total

    def restore(self, content_id: int, organization_id: int) -> bool:
        """Restore soft-deleted content"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id,
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.isnot(None)  # Must be deleted
        ).first()

        if not db_content:
            return False

        # Restore content
        db_content.deleted_at = None
        db_content.deleted_by_id = None
        db_content.is_active = True

        self.db.commit()
        return True

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
        """Update transcoding status (excludes soft-deleted)"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id,
            ContentModel.deleted_at.is_(None)  # Exclude soft-deleted
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
        """Update HLS transcoding information (excludes soft-deleted)"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id,
            ContentModel.deleted_at.is_(None)  # Exclude soft-deleted
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
        """Update thumbnail information (excludes soft-deleted)"""
        db_content = self.db.query(ContentModel).filter(
            ContentModel.id == content_id,
            ContentModel.deleted_at.is_(None)  # Exclude soft-deleted
        ).first()

        if not db_content:
            return False

        db_content.thumbnail_path = thumbnail_path
        db_content.thumbnail_url = thumbnail_url
        db_content.thumbnail_generated_at = datetime.now(timezone.utc)

        self.db.commit()
        return True

    def find_duplicates_with_usage(self, organization_id: int) -> List[Dict[str, Any]]:
        """
        Find duplicate files (same hash) with their usage info.
        Returns groups of duplicates with playlist, tag, and device usage.
        """
        from sqlalchemy import text

        # Step 1: Find hashes that have duplicates (count > 1)
        duplicate_hashes = self.db.execute(text("""
            SELECT file_hash, COUNT(*) as cnt, MIN(file_size) as file_size,
                   MIN(content_type) as content_type, MIN(thumbnail_url) as thumbnail_url
            FROM contents
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

            # Get all contents with this hash
            contents = self.db.query(ContentModel).filter(
                ContentModel.organization_id == organization_id,
                ContentModel.file_hash == file_hash,
                ContentModel.deleted_at.is_(None)
            ).order_by(ContentModel.created_at.asc()).all()

            contents_with_usage = []
            for content in contents:
                # Get usage info for this content
                usage = self._get_content_usage(content.id)

                contents_with_usage.append({
                    "id": content.id,
                    "title": content.title,
                    "original_filename": content.original_filename,
                    "created_at": content.created_at.isoformat() if content.created_at else None,
                    "is_active": content.is_active,
                    "usage": usage
                })

            result.append({
                "file_hash": file_hash[:16] + "...",  # Truncate for display
                "file_size": row.file_size,
                "content_type": row.content_type,
                "thumbnail_url": row.thumbnail_url,
                "duplicate_count": len(contents),
                "contents": contents_with_usage
            })

        return result

    def find_deleted_duplicates(self, organization_id: int) -> List[Dict[str, Any]]:
        """
        Find duplicate files (same hash) among deleted content.
        Returns groups of duplicates in recycle bin.
        """
        from sqlalchemy import text

        # Step 1: Find hashes that have duplicates (count > 1) among deleted content
        duplicate_hashes = self.db.execute(text("""
            SELECT file_hash, COUNT(*) as cnt, MIN(file_size) as file_size,
                   MIN(content_type) as content_type, MIN(thumbnail_url) as thumbnail_url
            FROM contents
            WHERE organization_id = :org_id AND deleted_at IS NOT NULL AND file_hash IS NOT NULL
            GROUP BY file_hash
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """), {"org_id": organization_id}).fetchall()

        if not duplicate_hashes:
            return []

        result = []

        for row in duplicate_hashes:
            file_hash = row.file_hash

            # Get all deleted contents with this hash
            contents = self.db.query(ContentModel).filter(
                ContentModel.organization_id == organization_id,
                ContentModel.file_hash == file_hash,
                ContentModel.deleted_at.isnot(None)
            ).order_by(ContentModel.deleted_at.desc()).all()

            contents_list = []
            for content in contents:
                contents_list.append({
                    "id": content.id,
                    "title": content.title,
                    "original_filename": content.original_filename,
                    "deleted_at": content.deleted_at.isoformat() if content.deleted_at else None,
                    "deleted_by_name": None,  # Could join with users table if needed
                    "is_active": content.is_active,
                })

            result.append({
                "file_hash": file_hash[:16] + "...",  # Truncate for display
                "file_size": row.file_size,
                "content_type": row.content_type,
                "thumbnail_url": row.thumbnail_url,
                "duplicate_count": len(contents),
                "contents": contents_list
            })

        return result

    def _get_content_usage(self, content_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get usage info for a content (playlists, tags, devices)"""
        from sqlalchemy import text

        # Get playlists using this content
        playlists = self.db.execute(text("""
            SELECT p.id, p.name
            FROM playlists p
            JOIN playlist_contents pc ON p.id = pc.playlist_id
            WHERE pc.content_id = :content_id AND p.deleted_at IS NULL
        """), {"content_id": content_id}).fetchall()

        # Get tags assigned to this content
        tags = self.db.execute(text("""
            SELECT t.id, t.tag_name, t.color
            FROM tags t
            JOIN content_tags ct ON t.id = ct.tag_id
            WHERE ct.content_id = :content_id AND t.deleted_at IS NULL
        """), {"content_id": content_id}).fetchall()

        # Get devices with direct content assignments
        direct_devices = self.db.execute(text("""
            SELECT d.id, d.device_name, 'direct' as via
            FROM devices d
            JOIN content_assignments ca ON d.id = ca.device_id
            WHERE ca.content_id = :content_id AND d.deleted_at IS NULL
        """), {"content_id": content_id}).fetchall()

        # Get devices via tag assignments
        tag_devices = self.db.execute(text("""
            SELECT DISTINCT d.id, d.device_name, CONCAT('tag:', t.tag_name) as via
            FROM devices d
            JOIN device_tags dt ON d.id = dt.device_id
            JOIN tags t ON dt.tag_id = t.id
            JOIN content_tags ct ON t.id = ct.tag_id
            WHERE ct.content_id = :content_id
              AND d.deleted_at IS NULL
              AND t.deleted_at IS NULL
        """), {"content_id": content_id}).fetchall()

        # Combine device lists (dedupe by id)
        device_dict = {}
        for d in direct_devices:
            device_dict[d.id] = {"id": d.id, "name": d.device_name, "via": d.via}
        for d in tag_devices:
            if d.id not in device_dict:
                device_dict[d.id] = {"id": d.id, "name": d.device_name, "via": d.via}

        return {
            "playlists": [{"id": p.id, "name": p.name} for p in playlists],
            "tags": [{"id": t.id, "name": t.tag_name, "color": t.color} for t in tags],
            "devices": list(device_dict.values())
        }

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

        # Extract user names from relationships (if loaded)
        uploaded_by_name = None
        if hasattr(db_content, 'uploader') and db_content.uploader is not None:
            uploaded_by_name = db_content.uploader.full_name or db_content.uploader.username

        deleted_by_name = None
        if hasattr(db_content, 'deleter') and db_content.deleter is not None:
            deleted_by_name = db_content.deleter.full_name or db_content.deleter.username

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
            # Audit trail fields
            uploaded_by_id=db_content.uploaded_by_id,
            updated_by_id=getattr(db_content, 'updated_by_id', None),
            deleted_by_id=getattr(db_content, 'deleted_by_id', None),
            created_at=db_content.created_at,
            updated_at=db_content.updated_at,
            deleted_at=db_content.deleted_at,
            # User names (from JOINs)
            uploaded_by_name=uploaded_by_name,
            deleted_by_name=deleted_by_name,
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
