"""
Celery App Configuration
Background tasks for content processing
"""

from celery import Celery
from celery.schedules import crontab
import os

# Get Redis URL from environment or use default
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Create Celery app
app = Celery(
    'signage_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks.content_tasks']  # Import task modules
)

# Import all models to register in SQLAlchemy metadata
# This must be done AFTER app creation to avoid circular imports
def register_models():
    """Import all models to register them in Base.metadata"""
    from services.auth.repositories.models import UserModel, OrganizationModel, AuditLogModel
    from services.content.repositories.models import ContentModel
    # Add other models as needed

register_models()

# Celery Configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jakarta',
    enable_utc=True,

    # Task routing
    task_routes={
        'tasks.content_tasks.transcode_to_hls': {'queue': 'video_processing'},
        'tasks.content_tasks.generate_thumbnail': {'queue': 'image_processing'},
    },

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
    },

    # Task time limits
    task_soft_time_limit=600,  # 10 minutes
    task_time_limit=900,       # 15 minutes

    # Worker settings
    worker_max_tasks_per_child=50,
    worker_disable_rate_limits=True,

    # Beat schedule (periodic tasks)
    beat_schedule={
        'cleanup-old-tasks': {
            'task': 'tasks.content_tasks.cleanup_old_task_results',
            'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        },
    },
)

if __name__ == '__main__':
    app.start()
