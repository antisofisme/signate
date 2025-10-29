"""
Celery Tasks Module
Background tasks for video transcoding and other async operations
"""

from app.celery_app import celery_app

# Import all tasks to register them with Celery
from app.tasks.transcoding import (
    transcode_video_task,
    check_transcoding_progress,
    cleanup_old_jobs,
    cancel_transcoding_task
)

__all__ = [
    'celery_app',
    'transcode_video_task',
    'check_transcoding_progress',
    'cleanup_old_jobs',
    'cancel_transcoding_task'
]