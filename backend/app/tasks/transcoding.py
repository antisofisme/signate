"""
Video Transcoding Celery Tasks
Handles background video transcoding to HLS format
"""

import os
import shutil
import tempfile
import logging
from app.core.logging import StructuredLogger
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

from celery import Task, current_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from app.celery_app import celery_app, BaseTask
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.content import Content
from app.services.transcoding_service import TranscodingService, TranscodingError
from app.services.anthias_client import AnthiasClient, AnthiasClientError
from app.schemas.transcoding import TranscodingStatus, TranscodingProgress

logger = StructuredLogger(__name__)


class TranscodingTask(BaseTask):
    """
    Base class for transcoding tasks with progress tracking
    """

    def update_progress(
        self,
        content_id: int,
        status: str,
        progress: int,
        message: str = None,
        error: str = None,
        variants: List[Dict] = None
    ):
        """
        Update transcoding progress in database

        Args:
            content_id: Content ID
            status: Transcoding status
            progress: Progress percentage (0-100)
            message: Optional status message
            error: Optional error message
            variants: Optional list of completed variants
        """
        try:
            # Update task state for monitoring
            current_task.update_state(
                state=status.upper(),
                meta={
                    'content_id': content_id,
                    'progress': progress,
                    'message': message,
                    'error': error,
                    'variants': variants
                }
            )

            # Update database
            with SessionLocal() as db:
                content = db.query(Content).filter(Content.id == content_id).first()
                if content:
                    content.transcoding_status = status
                    content.transcoding_progress = progress

                    if error:
                        content.transcoding_error = error

                    if variants:
                        content.hls_variants = variants

                    db.commit()
                    logger.debug(f"Updated progress for content {content_id}: {status} ({progress}%)")

        except Exception as e:
            logger.error(f"Failed to update progress for content {content_id}: {e}")


@celery_app.task(
    bind=True,
    base=TranscodingTask,
    name='app.tasks.transcoding.transcode_video_task',
    max_retries=3,
    default_retry_delay=60,
    time_limit=7200,  # 2 hours hard limit
    soft_time_limit=3600,  # 1 hour soft limit
)
def transcode_video_task(
    self,
    content_id: int,
    source_url: str = None,
    quality_levels: List[str] = None,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Celery task to transcode video to HLS format

    Args:
        content_id: ID of content to transcode
        source_url: Optional source URL (uses anthias_url if not provided)
        quality_levels: List of quality levels to generate
        overwrite: Whether to overwrite existing transcoding

    Returns:
        Dictionary with transcoding results

    Raises:
        TranscodingError: If transcoding fails
    """
    logger.info(f"Starting transcoding task for content {content_id}")

    temp_dir = None
    anthias_client = None

    try:
        # Initialize progress
        self.update_progress(content_id, TranscodingStatus.PENDING, 0, "Initializing transcoding")

        # Get content from database
        with SessionLocal() as db:
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise ValueError(f"Content {content_id} not found")

            # Update job ID
            content.transcoding_job_id = self.request.id
            db.commit()

            # Get source URL
            if not source_url:
                source_url = content.anthias_url

            asset_id = content.anthias_asset_id

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix=f"transcode_{content_id}_")
        logger.info(f"Created temp directory: {temp_dir}")

        # Initialize Anthias client
        anthias_client = AnthiasClient()

        # Step 1: Download source video from Anthias (10%)
        self.update_progress(
            content_id,
            TranscodingStatus.PROCESSING,
            5,
            "Downloading source video from Anthias"
        )

        source_path = os.path.join(temp_dir, f"source_{content_id}.mp4")

        def download_progress(progress):
            # Map download progress from 0-100 to 5-15 in overall progress
            overall_progress = 5 + int(progress * 0.1)
            self.update_progress(
                content_id,
                TranscodingStatus.PROCESSING,
                overall_progress,
                f"Downloading source video: {progress}%"
            )

        # Download video from Anthias
        if asset_id:
            try:
                anthias_client.download_file(
                    asset_id=asset_id,
                    destination=source_path,
                    progress_callback=download_progress
                )
            except AnthiasClientError:
                # Fallback to direct URL download if asset ID fails
                logger.warning(f"Failed to download via asset ID, trying direct URL: {source_url}")
                # You might want to implement direct URL download here
                raise
        else:
            # No asset ID, need to implement direct URL download
            raise NotImplementedError("Direct URL download not yet implemented")

        # Step 2: Transcode video to HLS (15-85%)
        self.update_progress(
            content_id,
            TranscodingStatus.PROCESSING,
            15,
            "Starting video transcoding"
        )

        # Output directory for HLS files
        hls_output_dir = os.path.join(temp_dir, "hls")
        os.makedirs(hls_output_dir, exist_ok=True)

        # Initialize transcoding service
        transcoding_service = TranscodingService(base_hls_dir=temp_dir)

        # Determine quality levels
        if not quality_levels:
            quality_levels = settings.HLS_QUALITY_LEVELS

        # Progress callback for transcoding
        def transcoding_progress_callback(progress: TranscodingProgress):
            # Map transcoding progress from 0-100 to 15-85 in overall progress
            overall_progress = 15 + int(progress.progress * 0.7)

            self.update_progress(
                content_id,
                TranscodingStatus.PROCESSING,
                overall_progress,
                f"Transcoding {progress.current_variant or 'video'}",
                variants=[{
                    'quality': v,
                    'status': 'completed'
                } for v in progress.completed_variants]
            )

        # Perform transcoding (synchronous in Celery context)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            transcoding_result = loop.run_until_complete(
                transcoding_service.transcode_to_hls(
                    source_path=source_path,
                    output_dir=hls_output_dir,
                    content_id=content_id,
                    quality_levels=quality_levels,
                    segment_duration=settings.HLS_SEGMENT_DURATION,
                    progress_callback=transcoding_progress_callback,
                    overwrite=overwrite
                )
            )
        finally:
            loop.close()

        # Step 3: Upload HLS files to Anthias (85-95%)
        self.update_progress(
            content_id,
            TranscodingStatus.PROCESSING,
            85,
            "Uploading HLS files to Anthias"
        )

        def upload_progress(progress):
            # Map upload progress from 0-100 to 85-95 in overall progress
            overall_progress = 85 + int(progress * 0.1)
            self.update_progress(
                content_id,
                TranscodingStatus.PROCESSING,
                overall_progress,
                f"Uploading HLS files: {progress}%"
            )

        # Upload HLS directory to Anthias
        hls_asset_id = f"hls_{content_id}"
        upload_result = anthias_client.upload_directory(
            directory_path=hls_output_dir,
            asset_id=hls_asset_id,
            progress_callback=upload_progress
        )

        # Step 4: Update database with results (95-100%)
        self.update_progress(
            content_id,
            TranscodingStatus.PROCESSING,
            95,
            "Updating database"
        )

        # Prepare HLS variants info
        hls_variants = []
        for variant in transcoding_result.variants:
            hls_variants.append({
                'quality': variant.quality,
                'resolution': variant.resolution,
                'bitrate': variant.bitrate,
                'bandwidth': variant.bandwidth,
                'playlist_path': variant.playlist_path,
                'size_bytes': variant.size_bytes,
                'segment_count': variant.segment_count
            })

        # Update content in database
        with SessionLocal() as db:
            content = db.query(Content).filter(Content.id == content_id).first()
            if content:
                # Construct public URL for HLS master playlist
                hls_base_url = f"{settings.API_BASE_URL}/hls/{content_id}"

                content.hls_master_playlist_path = transcoding_result.master_playlist_path
                content.transcoding_status = TranscodingStatus.COMPLETED
                content.transcoding_progress = 100
                content.transcoding_error = None
                content.hls_variants = hls_variants

                db.commit()

                logger.info(f"Successfully completed transcoding for content {content_id}")

        # Final progress update
        self.update_progress(
            content_id,
            TranscodingStatus.COMPLETED,
            100,
            "Transcoding completed successfully",
            variants=hls_variants
        )

        # Prepare result
        result = {
            'content_id': content_id,
            'status': TranscodingStatus.COMPLETED,
            'job_id': self.request.id,
            'master_playlist_url': f"/hls/{content_id}/master.m3u8",
            'variants': hls_variants,
            'total_size_bytes': transcoding_result.total_size_bytes,
            'transcoding_time_seconds': transcoding_result.transcoding_time_seconds
        }

        return result

    except SoftTimeLimitExceeded:
        # Soft time limit exceeded, wrap up gracefully
        logger.warning(f"Soft time limit exceeded for content {content_id}")

        error_msg = "Transcoding exceeded time limit (1 hour)"
        self.update_progress(
            content_id,
            TranscodingStatus.FAILED,
            -1,
            error=error_msg
        )

        # Retry with exponential backoff
        raise self.retry(exc=TimeoutError(error_msg), countdown=60 * (2 ** self.request.retries))

    except Exception as e:
        logger.error(f"Transcoding failed for content {content_id}: {e}", exc_info=True)

        # Update status to failed
        self.update_progress(
            content_id,
            TranscodingStatus.FAILED,
            -1,
            error=str(e)
        )

        # Retry if retries available
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        else:
            # Max retries reached, mark as permanently failed
            with SessionLocal() as db:
                content = db.query(Content).filter(Content.id == content_id).first()
                if content:
                    content.transcoding_status = TranscodingStatus.FAILED
                    content.transcoding_error = f"Max retries exceeded: {str(e)}"
                    db.commit()

            raise

    finally:
        # Cleanup
        if anthias_client:
            anthias_client.close()

        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup temp directory {temp_dir}: {e}")


@celery_app.task(
    name='app.tasks.transcoding.check_transcoding_progress',
    max_retries=1
)
def check_transcoding_progress(job_id: str) -> Dict[str, Any]:
    """
    Check progress of a transcoding job

    Args:
        job_id: Celery task ID

    Returns:
        Dictionary with job status and progress
    """
    try:
        from app.celery_app import get_task_info

        task_info = get_task_info(job_id)

        # Get additional info from task meta
        if task_info.get('info'):
            meta = task_info['info']
            return {
                'job_id': job_id,
                'status': task_info.get('state', 'UNKNOWN'),
                'progress': meta.get('progress', 0),
                'message': meta.get('message'),
                'error': meta.get('error'),
                'variants': meta.get('variants', []),
                'ready': task_info.get('ready', False),
                'successful': task_info.get('successful', False),
                'failed': task_info.get('failed', False)
            }

        return task_info

    except Exception as e:
        logger.error(f"Failed to check progress for job {job_id}: {e}")
        return {
            'job_id': job_id,
            'status': 'ERROR',
            'error': str(e)
        }


@celery_app.task(
    name='app.tasks.transcoding.cancel_transcoding_task',
    max_retries=1
)
def cancel_transcoding_task(content_id: int, job_id: str) -> bool:
    """
    Cancel a running transcoding job

    Args:
        content_id: Content ID
        job_id: Celery task ID

    Returns:
        True if cancelled successfully
    """
    try:
        from app.celery_app import cancel_task

        # Cancel the task
        cancelled = cancel_task(job_id)

        if cancelled:
            # Update database
            with SessionLocal() as db:
                content = db.query(Content).filter(Content.id == content_id).first()
                if content:
                    content.transcoding_status = TranscodingStatus.CANCELLED
                    content.transcoding_error = "Cancelled by user"
                    db.commit()

            logger.info(f"Successfully cancelled transcoding job {job_id} for content {content_id}")

        return cancelled

    except Exception as e:
        logger.error(f"Failed to cancel transcoding job {job_id}: {e}")
        return False


@celery_app.task(
    name='app.tasks.transcoding.cleanup_old_jobs',
    max_retries=1
)
def cleanup_old_jobs(days: int = 7) -> Dict[str, Any]:
    """
    Clean up old transcoding jobs and temporary files

    Args:
        days: Delete jobs older than this many days

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        cleaned_count = 0
        error_count = 0

        with SessionLocal() as db:
            # Find old completed/failed jobs
            old_contents = db.query(Content).filter(
                Content.transcoding_status.in_([
                    TranscodingStatus.COMPLETED,
                    TranscodingStatus.FAILED,
                    TranscodingStatus.CANCELLED
                ]),
                Content.updated_at < cutoff_date,
                Content.transcoding_job_id.isnot(None)
            ).all()

            for content in old_contents:
                try:
                    # Clear job ID to free up memory
                    content.transcoding_job_id = None
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"Failed to cleanup job for content {content.id}: {e}")
                    error_count += 1

            db.commit()

        # Clean up temporary directories
        temp_dir = tempfile.gettempdir()
        pattern = "transcode_*"

        for temp_path in Path(temp_dir).glob(pattern):
            try:
                if temp_path.is_dir():
                    # Check if directory is old enough
                    mtime = datetime.fromtimestamp(temp_path.stat().st_mtime)
                    if mtime < cutoff_date:
                        shutil.rmtree(temp_path)
                        logger.info(f"Removed old temp directory: {temp_path}")
                        cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to remove temp directory {temp_path}: {e}")
                error_count += 1

        result = {
            'cleaned_count': cleaned_count,
            'error_count': error_count,
            'cutoff_date': cutoff_date.isoformat()
        }

        logger.info(f"Cleanup completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {e}")
        raise


@celery_app.task(
    bind=True,
    base=TranscodingTask,
    name='app.tasks.transcoding.batch_transcode_videos',
    max_retries=1
)
def batch_transcode_videos(
    self,
    content_ids: List[int],
    quality_levels: List[str] = None,
    priority: int = 5
) -> Dict[str, Any]:
    """
    Batch transcode multiple videos

    Args:
        content_ids: List of content IDs to transcode
        quality_levels: Quality levels to generate
        priority: Task priority (higher = more important)

    Returns:
        Dictionary with batch results
    """
    try:
        results = {
            'total': len(content_ids),
            'submitted': 0,
            'failed': 0,
            'jobs': []
        }

        for content_id in content_ids:
            try:
                # Submit individual transcoding task
                task = transcode_video_task.apply_async(
                    args=[content_id],
                    kwargs={'quality_levels': quality_levels},
                    priority=priority
                )

                results['jobs'].append({
                    'content_id': content_id,
                    'job_id': task.id,
                    'status': 'submitted'
                })
                results['submitted'] += 1

            except Exception as e:
                logger.error(f"Failed to submit transcoding for content {content_id}: {e}")
                results['jobs'].append({
                    'content_id': content_id,
                    'error': str(e),
                    'status': 'failed'
                })
                results['failed'] += 1

        return results

    except Exception as e:
        logger.error(f"Batch transcoding failed: {e}")
        raise