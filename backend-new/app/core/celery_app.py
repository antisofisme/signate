"""
Celery Configuration for Background Tasks
Handles async processing for transcoding, notifications, etc.
"""

from celery import Celery
import os
import logging

logger = logging.getLogger(__name__)

# Get Redis URL from environment variable
# Using os.getenv to avoid circular imports with settings
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')

# Create Celery instance
celery_app = Celery(
    'signage_backend',
    broker=redis_url,
    backend=redis_url
)

# Autodiscover tasks
celery_app.autodiscover_tasks([
    'app.tasks',
])

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_always_retry=True,
    result_backend_max_retries=10,

    # Task execution settings
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes hard limit
    task_soft_time_limit=1500,  # 25 minutes soft limit
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    worker_send_task_events=True,

    # Queue routing
    task_routes={
        'transcode_video': {'queue': 'transcoding'},
        'send_notification': {'queue': 'notifications'},
        'cleanup_old_files': {'queue': 'maintenance'},
    },

    # Retry settings
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # Max 10 minutes between retries
    task_retry_jitter=True,

    # Beat schedule (periodic tasks)
    beat_schedule={
        # Device monitoring tasks
        'check-offline-devices': {
            'task': 'app.tasks.device_tasks.check_offline_devices',
            'schedule': 300.0,  # Every 5 minutes
            'options': {'queue': 'maintenance'}
        },
        'sync-device-heartbeats': {
            'task': 'app.tasks.device_tasks.sync_device_heartbeats',
            'schedule': 60.0,  # Every minute
            'options': {'queue': 'maintenance'}
        },

        # Content maintenance tasks
        'cleanup-failed-transcoding': {
            'task': 'app.tasks.content_tasks.cleanup_failed_transcoding',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'maintenance'}
        },

        # System maintenance tasks
        'cleanup-old-files': {
            'task': 'app.tasks.system_tasks.cleanup_old_files',
            'schedule': 86400.0,  # Every 24 hours (daily)
            'options': {'queue': 'maintenance'}
        },
        'check-storage-quotas': {
            'task': 'app.tasks.system_tasks.check_storage_quotas',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'maintenance'}
        },
        'archive-old-activity-logs': {
            'task': 'app.tasks.system_tasks.archive_old_activity_logs',
            'schedule': 86400.0,  # Every 24 hours (daily)
            'options': {'queue': 'maintenance'}
        },

        # Analytics tasks
        'compute-daily-analytics': {
            'task': 'app.tasks.system_tasks.compute_analytics',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'analytics'},
            'kwargs': {'period': 'daily'}
        },
        'generate-daily-report': {
            'task': 'app.tasks.system_tasks.generate_daily_report',
            'schedule': 86400.0,  # Every 24 hours at midnight (UTC)
            'options': {'queue': 'analytics'}
        },
    },

    # Monitoring
    task_send_sent_event=True,
)

# Initialize Celery on import
logger.info("Celery app configured with Redis backend")

if __name__ == '__main__':
    celery_app.start()