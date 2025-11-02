"""
Celery Application Configuration
=================================

Celery worker for background tasks and periodic jobs.
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "signage_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.device_tasks", "app.tasks.content_tasks", "app.tasks.system_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)

# Celery Beat Schedule (Periodic Tasks)
celery_app.conf.beat_schedule = {
    # Check device status every 5 minutes
    "check-offline-devices": {
        "task": "app.tasks.device_tasks.check_offline_devices",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },

    # Cleanup expired content daily at 2 AM
    "cleanup-expired-content": {
        "task": "app.tasks.content_tasks.cleanup_expired_content",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },

    # Generate daily analytics at 3 AM
    "generate-daily-analytics": {
        "task": "app.tasks.system_tasks.generate_daily_analytics",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },

    # Check storage quota every hour
    "check-storage-quota": {
        "task": "app.tasks.system_tasks.check_storage_quota",
        "schedule": crontab(minute=0),  # Every hour
    },

    # Sync device heartbeats every minute
    "sync-device-heartbeats": {
        "task": "app.tasks.device_tasks.sync_device_heartbeats",
        "schedule": crontab(minute="*"),  # Every minute
    },
}

if __name__ == "__main__":
    celery_app.start()
