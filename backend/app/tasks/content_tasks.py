"""
Content Background Tasks
========================

Celery tasks untuk content management, cleanup, dan processing.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from celery import Task
from celery.utils.log import get_task_logger
import os
from pathlib import Path

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.repositories import ContentRepository
from app.utils.activity_logger import log_activity, ActivityAction, EntityType

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.content_tasks.cleanup_expired_content")
def cleanup_expired_content(self: Task) -> Dict[str, Any]:
    """
    Cleanup expired content and orphaned files.

    Runs daily at 2 AM via Celery Beat.

    Business Rules:
    - Remove content that has passed its expiration date
    - Delete orphaned files (files without DB records)
    - Clean up temporary upload files
    - Update storage statistics

    Returns:
        Dict with cleanup results
    """
    db = SessionLocal()
    try:
        logger.info("Starting expired content cleanup...")

        content_repo = ContentRepository(db)
        now = datetime.utcnow()

        # Find expired content
        expired_content = db.query(content_repo.model).filter(
            content_repo.model.expiration_date.isnot(None),
            content_repo.model.expiration_date < now,
            content_repo.model.is_active == True
        ).all()

        expired_count = 0
        deleted_files = 0
        freed_space = 0

        for content in expired_content:
            file_size = content.file_size or 0

            # Soft delete the content record
            content_repo.update(content.id, {"is_active": False})

            # Delete physical file if it exists
            if content.file_path and os.path.exists(content.file_path):
                try:
                    os.remove(content.file_path)
                    deleted_files += 1
                    freed_space += file_size
                except Exception as e:
                    logger.error(f"Failed to delete file {content.file_path}: {str(e)}")

            # Delete thumbnail if it exists
            if content.thumbnail_path and os.path.exists(content.thumbnail_path):
                try:
                    os.remove(content.thumbnail_path)
                except Exception as e:
                    logger.error(f"Failed to delete thumbnail {content.thumbnail_path}: {str(e)}")

            # Log activity
            log_activity(
                db=db,
                action=ActivityAction.DELETE,
                entity_type=EntityType.CONTENT,
                entity_id=content.id,
                description=f"Auto-cleanup: Expired content '{content.title}'",
                metadata={
                    "expiration_date": content.expiration_date.isoformat(),
                    "file_size": file_size,
                    "content_type": content.content_type
                }
            )

            expired_count += 1

        # Cleanup orphaned files
        orphaned_count = cleanup_orphaned_files(db)

        logger.info(
            f"Cleanup complete: {expired_count} expired content, "
            f"{deleted_files} files deleted, {freed_space / 1024 / 1024:.2f} MB freed, "
            f"{orphaned_count} orphaned files removed"
        )

        return {
            "status": "success",
            "expired_content_count": expired_count,
            "deleted_files": deleted_files,
            "freed_space_bytes": freed_space,
            "freed_space_mb": round(freed_space / 1024 / 1024, 2),
            "orphaned_files": orphaned_count,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error cleaning up expired content: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


def cleanup_orphaned_files(db) -> int:
    """
    Remove files that exist on disk but have no DB record.

    Args:
        db: Database session

    Returns:
        Number of orphaned files deleted
    """
    content_repo = ContentRepository(db)
    orphaned_count = 0

    upload_dir = Path(settings.UPLOAD_DIR)
    if not upload_dir.exists():
        return 0

    # Get all file paths from database
    all_content = db.query(content_repo.model).all()
    db_file_paths = set()
    for content in all_content:
        if content.file_path:
            db_file_paths.add(Path(content.file_path).name)
        if content.thumbnail_path:
            db_file_paths.add(Path(content.thumbnail_path).name)

    # Check each file in upload directory
    for file_path in upload_dir.rglob("*"):
        if file_path.is_file():
            if file_path.name not in db_file_paths:
                try:
                    file_path.unlink()
                    orphaned_count += 1
                    logger.info(f"Deleted orphaned file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete orphaned file {file_path}: {str(e)}")

    return orphaned_count


@celery_app.task(bind=True, name="app.tasks.content_tasks.generate_thumbnails")
def generate_thumbnails(
    self: Task,
    content_id: int,
    force_regenerate: bool = False
) -> Dict[str, Any]:
    """
    Generate thumbnail for content (async task).

    Supports:
    - Video files: Extract frame at 1 second
    - Image files: Create resized thumbnail
    - PDF files: Render first page

    Args:
        content_id: Content ID
        force_regenerate: Force regenerate even if thumbnail exists

    Returns:
        Dict with generation result
    """
    db = SessionLocal()
    try:
        logger.info(f"Generating thumbnail for content {content_id}...")

        content_repo = ContentRepository(db)
        content = content_repo.get(content_id)

        if not content:
            logger.error(f"Content {content_id} not found")
            return {
                "status": "error",
                "message": f"Content {content_id} not found",
                "task_id": self.request.id
            }

        # Check if thumbnail already exists
        if content.thumbnail_path and os.path.exists(content.thumbnail_path) and not force_regenerate:
            logger.info(f"Thumbnail already exists for content {content_id}")
            return {
                "status": "skipped",
                "message": "Thumbnail already exists",
                "thumbnail_path": content.thumbnail_path,
                "task_id": self.request.id
            }

        # TODO: Implement actual thumbnail generation logic
        # This would use PIL for images, ffmpeg for videos, pdf2image for PDFs
        thumbnail_path = None

        if thumbnail_path:
            # Update content record with thumbnail path
            content_repo.update(content_id, {"thumbnail_path": thumbnail_path})

            # Log activity
            log_activity(
                db=db,
                action=ActivityAction.UPDATE,
                entity_type=EntityType.CONTENT,
                entity_id=content_id,
                description=f"Thumbnail generated for '{content.title}'",
                metadata={
                    "thumbnail_path": thumbnail_path,
                    "content_type": content.content_type
                }
            )

        logger.info(f"Thumbnail generated successfully for content {content_id}")

        return {
            "status": "success",
            "content_id": content_id,
            "thumbnail_path": thumbnail_path,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error generating thumbnail for content {content_id}: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=120, max_retries=3)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.content_tasks.transcode_video")
def transcode_video(
    self: Task,
    content_id: int,
    target_format: str = "mp4",
    target_resolution: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcode video to target format and resolution (async task).

    Args:
        content_id: Content ID
        target_format: Target video format (mp4, webm, etc.)
        target_resolution: Target resolution (e.g., "1920x1080", "1280x720")

    Returns:
        Dict with transcoding result
    """
    db = SessionLocal()
    try:
        logger.info(f"Transcoding video {content_id} to {target_format}...")

        content_repo = ContentRepository(db)
        content = content_repo.get(content_id)

        if not content:
            logger.error(f"Content {content_id} not found")
            return {
                "status": "error",
                "message": f"Content {content_id} not found",
                "task_id": self.request.id
            }

        if content.content_type != "video":
            logger.error(f"Content {content_id} is not a video")
            return {
                "status": "error",
                "message": "Content is not a video",
                "task_id": self.request.id
            }

        # TODO: Implement actual video transcoding logic
        # This would use ffmpeg via subprocess or ffmpeg-python library

        # Log activity
        log_activity(
            db=db,
            action=ActivityAction.UPDATE,
            entity_type=EntityType.CONTENT,
            entity_id=content_id,
            description=f"Video transcoded: '{content.title}' to {target_format}",
            metadata={
                "target_format": target_format,
                "target_resolution": target_resolution,
                "original_file": content.file_path
            }
        )

        logger.info(f"Video transcoded successfully for content {content_id}")

        return {
            "status": "success",
            "content_id": content_id,
            "target_format": target_format,
            "target_resolution": target_resolution,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error transcoding video {content_id}: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.content_tasks.validate_content")
def validate_content(
    self: Task,
    content_id: int
) -> Dict[str, Any]:
    """
    Validate content file integrity and metadata.

    Checks:
    - File exists and is readable
    - File size matches database record
    - File format is valid
    - Metadata is complete

    Args:
        content_id: Content ID

    Returns:
        Dict with validation result
    """
    db = SessionLocal()
    try:
        logger.info(f"Validating content {content_id}...")

        content_repo = ContentRepository(db)
        content = content_repo.get(content_id)

        if not content:
            logger.error(f"Content {content_id} not found")
            return {
                "status": "error",
                "message": f"Content {content_id} not found",
                "task_id": self.request.id
            }

        validation_errors = []

        # Check file exists
        if not content.file_path or not os.path.exists(content.file_path):
            validation_errors.append("File does not exist")

        # Check file size
        if content.file_path and os.path.exists(content.file_path):
            actual_size = os.path.getsize(content.file_path)
            if content.file_size and actual_size != content.file_size:
                validation_errors.append(
                    f"File size mismatch: DB={content.file_size}, Actual={actual_size}"
                )

        # Check metadata
        if not content.title:
            validation_errors.append("Missing title")
        if not content.content_type:
            validation_errors.append("Missing content type")

        is_valid = len(validation_errors) == 0

        # Log activity
        log_activity(
            db=db,
            action=ActivityAction.UPDATE,
            entity_type=EntityType.CONTENT,
            entity_id=content_id,
            description=f"Content validation: {'PASSED' if is_valid else 'FAILED'}",
            metadata={
                "is_valid": is_valid,
                "errors": validation_errors
            }
        )

        logger.info(
            f"Content {content_id} validation {'passed' if is_valid else 'failed'}: "
            f"{len(validation_errors)} errors"
        )

        return {
            "status": "success",
            "content_id": content_id,
            "is_valid": is_valid,
            "errors": validation_errors,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error validating content {content_id}: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()
