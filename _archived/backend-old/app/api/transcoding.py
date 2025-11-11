"""
Video Transcoding API Endpoints
Handles video transcoding operations via Celery tasks
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status, Query, Body
from sqlalchemy.orm import Session
from app.core.logging import StructuredLogger

from app.core.database import get_db
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response
from app.models.content import Content
from app.tasks.transcoding import (
    transcode_video_task,
    check_transcoding_progress,
    cancel_transcoding_task,
    batch_transcode_videos
)
from app.celery_app import get_task_info, health_check as celery_health_check
from app.schemas.transcoding import (
    TranscodingStatus,
    TranscodingStartRequest,
    TranscodingJobResponse,
    TranscodingQueueStatus,
    BatchTranscodingRequest
)

logger = StructuredLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/transcoding",
    tags=["Transcoding"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


# =============================================================================
# TRANSCODING ENDPOINTS
# =============================================================================

@router.post("/{content_id}/start")
def start_transcoding(
    request: Request,
    content_id: int,
    quality_levels: Optional[List[str]] = Query(default=None),
    overwrite: bool = Query(default=False),
    priority: int = Query(default=5, ge=0, le=10),
    db: Session = Depends(get_db)
):
    """
    Start transcoding a video to HLS format

    Args:
        content_id: ID of content to transcode
        quality_levels: Optional list of quality levels (1080p, 720p, 480p, 360p)
        overwrite: Whether to overwrite existing transcoding
        priority: Task priority (0-10, higher = more important)

    Returns:
        Transcoding job information
    """
    request_id = get_request_id(request)

    logger.info(
        "Starting transcoding job",
        request_id=request_id,
        content_id=content_id,
        quality_levels=quality_levels,
        overwrite=overwrite,
        priority=priority
    )

    # Get content from database
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        logger.warning(
            "Content not found for transcoding",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(f"Content {content_id} not found")

    # Check if content is a video
    if content.content_type != "video":
        logger.warning(
            "Cannot transcode non-video content",
            request_id=request_id,
            content_id=content_id,
            content_type=content.content_type
        )
        raise BadRequestException("Content is not a video")

    # Check if already transcoding
    if content.transcoding_status == TranscodingStatus.PROCESSING and not overwrite:
        logger.info(
            "Content is already being transcoded",
            request_id=request_id,
            content_id=content_id,
            job_id=content.transcoding_job_id
        )
        raise ConflictException("Content is already being transcoded")

    # Check if already completed
    if content.transcoding_status == TranscodingStatus.COMPLETED and not overwrite:
        logger.info(
            "Content already transcoded, returning existing result",
            request_id=request_id,
            content_id=content_id
        )
        return success_response(
            data={
                "content_id": content_id,
                "job_id": content.transcoding_job_id,
                "status": content.transcoding_status,
                "hls_url": f"/hls/{content_id}/master.m3u8",
                "variants": content.hls_variants or []
            },
            request_id=request_id
        )

    # Submit transcoding task to Celery
    task = transcode_video_task.apply_async(
        args=[content_id],
        kwargs={
            'quality_levels': quality_levels,
            'overwrite': overwrite
        },
        priority=priority
    )

    # Update content status
    content.transcoding_status = TranscodingStatus.PENDING
    content.transcoding_job_id = task.id
    content.transcoding_progress = 0
    content.transcoding_error = None
    db.commit()

    logger.info(
        "Transcoding job started successfully",
        request_id=request_id,
        content_id=content_id,
        job_id=task.id,
        priority=priority
    )

    return success_response(
        data={
            "content_id": content_id,
            "job_id": task.id,
            "status": TranscodingStatus.PENDING,
            "progress": 0,
            "priority": priority
        },
        request_id=request_id
    )


@router.get("/{content_id}/status")
def get_transcoding_status(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    Get transcoding status for a content

    Args:
        content_id: Content ID

    Returns:
        Transcoding status and progress
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting transcoding status",
        request_id=request_id,
        content_id=content_id
    )

    # Get content from database
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        logger.warning(
            "Content not found",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(f"Content {content_id} not found")

    # Build response
    response_data = {
        "content_id": content_id,
        "status": content.transcoding_status or "not_started",
        "progress": content.transcoding_progress or 0,
        "job_id": content.transcoding_job_id,
        "error": content.transcoding_error
    }

    # If transcoding is in progress, get real-time status from Celery
    if content.transcoding_job_id and content.transcoding_status == TranscodingStatus.PROCESSING:
        try:
            job_info = check_transcoding_progress.apply_async(
                args=[content.transcoding_job_id]
            ).get(timeout=5)

            if job_info:
                response_data.update({
                    "progress": job_info.get('progress', content.transcoding_progress),
                    "message": job_info.get('message'),
                    "current_variant": job_info.get('current_variant'),
                    "completed_variants": job_info.get('variants', [])
                })
                logger.debug(
                    "Retrieved real-time transcoding progress",
                    request_id=request_id,
                    content_id=content_id,
                    progress=job_info.get('progress')
                )
        except Exception as e:
            logger.warning(
                "Failed to get Celery task status",
                request_id=request_id,
                content_id=content_id,
                error=str(e)
            )

    # Add HLS info if completed
    if content.transcoding_status == TranscodingStatus.COMPLETED:
        response_data.update({
            "hls_url": f"/hls/{content_id}/master.m3u8",
            "variants": content.hls_variants or []
        })

    logger.info(
        "Transcoding status retrieved",
        request_id=request_id,
        content_id=content_id,
        status=response_data['status'],
        progress=response_data['progress']
    )

    return success_response(
        data=response_data,
        request_id=request_id
    )


@router.post("/{content_id}/cancel")
def cancel_transcoding(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a running transcoding job

    Args:
        content_id: Content ID

    Returns:
        Cancellation result
    """
    request_id = get_request_id(request)

    logger.info(
        "Cancelling transcoding job",
        request_id=request_id,
        content_id=content_id
    )

    # Get content from database
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        logger.warning(
            "Content not found for cancellation",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(f"Content {content_id} not found")

    # Check if transcoding is in progress
    if content.transcoding_status != TranscodingStatus.PROCESSING:
        logger.warning(
            "No active transcoding job to cancel",
            request_id=request_id,
            content_id=content_id,
            current_status=content.transcoding_status
        )
        raise BadRequestException("No active transcoding job to cancel")

    if not content.transcoding_job_id:
        logger.warning(
            "No job ID found for cancellation",
            request_id=request_id,
            content_id=content_id
        )
        raise BadRequestException("No job ID found")

    # Cancel the task
    try:
        result = cancel_transcoding_task.apply_async(
            args=[content_id, content.transcoding_job_id]
        ).get(timeout=10)

        if result:
            logger.info(
                "Transcoding job cancelled successfully",
                request_id=request_id,
                content_id=content_id,
                job_id=content.transcoding_job_id
            )
            return success_response(
                data={
                    "content_id": content_id,
                    "job_id": content.transcoding_job_id,
                    "status": "cancelled"
                },
                request_id=request_id
            )
        else:
            logger.error(
                "Failed to cancel transcoding job",
                request_id=request_id,
                content_id=content_id,
                job_id=content.transcoding_job_id
            )
            raise BadRequestException("Failed to cancel transcoding job")
    except Exception as e:
        logger.error(
            "Error cancelling transcoding",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(f"Failed to cancel transcoding: {str(e)}")


@router.post("/batch/start")
def start_batch_transcoding(
    request: Request,
    content_ids: List[int] = Body(..., description="List of content IDs to transcode"),
    quality_levels: Optional[List[str]] = Body(None, description="Quality levels"),
    priority: int = Body(5, ge=0, le=10, description="Task priority"),
    db: Session = Depends(get_db)
):
    """
    Start batch transcoding for multiple videos

    Args:
        content_ids: List of content IDs to transcode
        quality_levels: Optional list of quality levels
        priority: Task priority

    Returns:
        Batch transcoding result
    """
    request_id = get_request_id(request)

    logger.info(
        "Starting batch transcoding",
        request_id=request_id,
        content_count=len(content_ids),
        quality_levels=quality_levels,
        priority=priority
    )

    # Validate all content IDs
    contents = db.query(Content).filter(Content.id.in_(content_ids)).all()
    found_ids = {c.id for c in contents}
    missing_ids = set(content_ids) - found_ids

    if missing_ids:
        logger.warning(
            "Some content IDs not found",
            request_id=request_id,
            missing_ids=list(missing_ids)
        )
        raise NotFoundException(f"Content not found: {list(missing_ids)}")

    # Filter only videos
    video_ids = [c.id for c in contents if c.content_type == "video"]
    non_video_ids = [c.id for c in contents if c.content_type != "video"]

    if not video_ids:
        logger.warning(
            "No video content found in batch",
            request_id=request_id,
            content_ids=content_ids
        )
        raise BadRequestException("No video content found in the provided IDs")

    # Submit batch task
    try:
        result = batch_transcode_videos.apply_async(
            args=[video_ids],
            kwargs={
                'quality_levels': quality_levels,
                'priority': priority
            }
        ).get(timeout=30)

        logger.info(
            "Batch transcoding started successfully",
            request_id=request_id,
            video_count=len(video_ids),
            skipped_non_videos=len(non_video_ids)
        )

        return success_response(
            data={
                "queued_videos": video_ids,
                "skipped_non_videos": non_video_ids,
                "total_queued": len(video_ids),
                "result": result
            },
            request_id=request_id
        )
    except Exception as e:
        logger.error(
            "Failed to start batch transcoding",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(f"Failed to start batch transcoding: {str(e)}")


@router.get("/job/{job_id}")
def get_job_status(
    request: Request,
    job_id: str
):
    """
    Get status of a specific transcoding job by Celery task ID

    Args:
        job_id: Celery task ID

    Returns:
        Job status information
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting job status",
        request_id=request_id,
        job_id=job_id
    )

    try:
        job_info = get_task_info(job_id)

        if not job_info:
            logger.warning(
                "Job not found",
                request_id=request_id,
                job_id=job_id
            )
            raise NotFoundException(f"Job {job_id} not found")

        logger.info(
            "Job status retrieved",
            request_id=request_id,
            job_id=job_id,
            job_state=job_info.get('state')
        )

        return success_response(
            data=job_info,
            request_id=request_id
        )
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get job status",
            request_id=request_id,
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(f"Failed to get job status: {str(e)}")


@router.get("/health")
def check_transcoding_health(
    request: Request
):
    """
    Check health of transcoding service (Celery workers)

    Returns:
        Health status of Celery workers
    """
    request_id = get_request_id(request)

    logger.info(
        "Checking transcoding service health",
        request_id=request_id
    )

    try:
        health_status = celery_health_check()

        logger.info(
            "Transcoding health check completed",
            request_id=request_id,
            status=health_status.get('status'),
            workers=health_status.get('workers', 0)
        )

        return success_response(
            data=health_status,
            request_id=request_id
        )
    except Exception as e:
        logger.error(
            "Transcoding health check failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        # Return unhealthy status instead of raising exception
        return success_response(
            data={
                "status": "unhealthy",
                "message": str(e),
                "workers": 0,
                "error": True
            },
            request_id=request_id
        )


@router.get("/queue/status")
def get_queue_status(
    request: Request
):
    """
    Get status of transcoding queues

    Returns:
        Queue statistics including active, reserved, and scheduled tasks
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting queue status",
        request_id=request_id
    )

    try:
        from app.celery_app import celery_app

        # Get queue statistics
        inspect = celery_app.control.inspect()

        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        scheduled = inspect.scheduled() or {}

        # Count tasks per queue
        queue_stats = {
            'default': {'active': 0, 'reserved': 0, 'scheduled': 0},
            'transcoding': {'active': 0, 'reserved': 0, 'scheduled': 0},
            'anthias': {'active': 0, 'reserved': 0, 'scheduled': 0}
        }

        # Count active tasks
        for worker_tasks in active.values():
            for task in worker_tasks:
                queue_name = task.get('delivery_info', {}).get('routing_key', 'default')
                if queue_name in queue_stats:
                    queue_stats[queue_name]['active'] += 1

        # Count reserved tasks
        for worker_tasks in reserved.values():
            for task in worker_tasks:
                queue_name = task.get('delivery_info', {}).get('routing_key', 'default')
                if queue_name in queue_stats:
                    queue_stats[queue_name]['reserved'] += 1

        # Count scheduled tasks
        for worker_tasks in scheduled.values():
            for task in worker_tasks:
                queue_stats['default']['scheduled'] += 1

        total_active = sum(q['active'] for q in queue_stats.values())
        total_reserved = sum(q['reserved'] for q in queue_stats.values())
        total_scheduled = sum(q['scheduled'] for q in queue_stats.values())

        logger.info(
            "Queue status retrieved",
            request_id=request_id,
            total_active=total_active,
            total_reserved=total_reserved,
            total_scheduled=total_scheduled
        )

        return success_response(
            data={
                "queues": queue_stats,
                "total_active": total_active,
                "total_reserved": total_reserved,
                "total_scheduled": total_scheduled
            },
            request_id=request_id
        )
    except Exception as e:
        logger.error(
            "Failed to get queue status",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise BadRequestException(f"Failed to get queue status: {str(e)}")