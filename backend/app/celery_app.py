"""
Celery Application Configuration
Handles background tasks for video transcoding and other async operations
"""

import os
from celery import Celery, Task
from celery.signals import worker_ready, worker_shutdown, task_failure, task_success, task_retry
from kombu import Queue
import logging
from app.core.logging import StructuredLogger
from typing import Any

from app.core.config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = StructuredLogger(__name__)

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

# Create Celery instance
celery_app = Celery(
    "signage",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.transcoding"]  # Auto-discover tasks
)

# =============================================================================
# CELERY SETTINGS
# =============================================================================

celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,  # Results expire after 1 hour
    timezone="UTC",
    enable_utc=True,

    # Task time limits
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,  # Hard limit (2 hours)
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,  # Soft limit (1 hour)

    # Retry settings
    task_default_retry_delay=settings.CELERY_TASK_DEFAULT_RETRY_DELAY,
    task_max_retries=settings.CELERY_TASK_MAX_RETRIES,

    # Worker settings
    worker_prefetch_multiplier=1,  # Disable prefetching for long-running tasks
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks to prevent memory leaks
    worker_disable_rate_limits=True,

    # Result backend settings
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 7200,  # 2 hours
        'fanout_prefix': True,
        'fanout_patterns': True
    },

    # Task routing
    task_routes={
        'app.tasks.transcoding.*': {'queue': 'transcoding'},
        'app.tasks.anthias.*': {'queue': 'anthias'},
        'app.tasks.default.*': {'queue': 'default'}
    },

    # Queue configuration
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',

    # Beat schedule (periodic tasks) - if needed
    beat_schedule={
        # Example: Clean up old transcoding jobs every hour
        'cleanup-old-jobs': {
            'task': 'app.tasks.transcoding.cleanup_old_jobs',
            'schedule': 3600.0,  # Every hour
        },
    },

    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,

    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Redis-specific settings
    redis_max_connections=50,
    redis_socket_keepalive=True,
    redis_socket_keepalive_options={
        1: 3,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 3,  # TCP_KEEPCNT
    },
)

# =============================================================================
# QUEUE CONFIGURATION
# =============================================================================

celery_app.conf.task_queues = (
    Queue('default', routing_key='default', queue_arguments={'x-max-priority': 5}),
    Queue('transcoding', routing_key='transcoding', queue_arguments={'x-max-priority': 10}),
    Queue('anthias', routing_key='anthias', queue_arguments={'x-max-priority': 5}),
)

# =============================================================================
# CUSTOM TASK BASE CLASS
# =============================================================================

class BaseTask(Task):
    """
    Base task with database session management and error handling
    """

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_jitter = True  # Add randomness to retry delays

    def __init__(self):
        super().__init__()
        self._db = None

    @property
    def db(self):
        """
        Lazy database session getter
        Creates a new session if not exists
        """
        if self._db is None:
            from app.core.database import SessionLocal
            self._db = SessionLocal()
        return self._db

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Clean up database session after task completion
        """
        if self._db is not None:
            try:
                self._db.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")
            finally:
                self._db = None

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Handle task failure - rollback database session
        """
        if self._db is not None:
            try:
                self._db.rollback()
            except Exception as e:
                logger.error(f"Error rolling back database session: {e}")

        logger.error(
            f"Task {self.name}[{task_id}] failed: {exc}",
            exc_info=True,
            extra={
                'task_id': task_id,
                'task_name': self.name,
                'args': args,
                'kwargs': kwargs
            }
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Handle task retry
        """
        logger.warning(
            f"Task {self.name}[{task_id}] retrying: {exc}",
            extra={
                'task_id': task_id,
                'task_name': self.name,
                'args': args,
                'kwargs': kwargs,
                'retry_count': self.request.retries
            }
        )

    def on_success(self, retval, task_id, args, kwargs):
        """
        Handle task success - commit database changes
        """
        if self._db is not None:
            try:
                self._db.commit()
            except Exception as e:
                logger.error(f"Error committing database session: {e}")
                self._db.rollback()
                raise

# Set base task for all tasks
celery_app.Task = BaseTask

# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

@worker_ready.connect
def on_worker_ready(**kwargs):
    """
    Called when worker is ready to accept tasks
    """
    logger.info("✓ Celery worker ready to accept tasks")
    logger.info(f"  Broker: {settings.CELERY_BROKER_URL}")
    logger.info(f"  Backend: {settings.CELERY_RESULT_BACKEND}")
    logger.info(f"  Queues: default, transcoding, anthias")

@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """
    Called when worker is shutting down
    """
    logger.info("Celery worker shutting down...")

@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """
    Called when a task fails
    """
    logger.error(
        f"Task failed: {sender.name}[{task_id}] - {exception}",
        extra={
            'task_id': task_id,
            'task_name': sender.name if sender else 'unknown',
            'exception': str(exception)
        }
    )

@task_success.connect
def on_task_success(sender=None, result=None, **kwargs):
    """
    Called when a task succeeds
    """
    task_id = sender.request.id if sender else 'unknown'
    logger.info(
        f"Task succeeded: {sender.name}[{task_id}]",
        extra={
            'task_id': task_id,
            'task_name': sender.name if sender else 'unknown'
        }
    )

@task_retry.connect
def on_task_retry(sender=None, reason=None, **kwargs):
    """
    Called when a task is retried
    """
    task_id = sender.request.id if sender else 'unknown'
    logger.warning(
        f"Task retry: {sender.name}[{task_id}] - {reason}",
        extra={
            'task_id': task_id,
            'task_name': sender.name if sender else 'unknown',
            'reason': str(reason)
        }
    )

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_task_info(task_id: str) -> dict:
    """
    Get task information by ID

    Args:
        task_id: Celery task ID

    Returns:
        Dictionary with task info
    """
    result = celery_app.AsyncResult(task_id)
    return {
        'task_id': task_id,
        'state': result.state,
        'result': result.result,
        'info': result.info,
        'successful': result.successful(),
        'failed': result.failed(),
        'ready': result.ready()
    }

def cancel_task(task_id: str) -> bool:
    """
    Cancel a running task

    Args:
        task_id: Celery task ID

    Returns:
        True if cancelled, False otherwise
    """
    try:
        celery_app.control.revoke(task_id, terminate=True, signal='SIGTERM')
        logger.info(f"Task {task_id} cancelled")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return False

def get_active_tasks() -> list:
    """
    Get list of active tasks

    Returns:
        List of active task dictionaries
    """
    inspect = celery_app.control.inspect()
    active = inspect.active()

    if not active:
        return []

    tasks = []
    for worker, task_list in active.items():
        for task in task_list:
            tasks.append({
                'worker': worker,
                'task_id': task['id'],
                'name': task['name'],
                'args': task['args'],
                'kwargs': task['kwargs']
            })

    return tasks

def purge_queue(queue_name: str = None) -> int:
    """
    Purge all pending tasks from a queue

    Args:
        queue_name: Name of queue to purge (None = all queues)

    Returns:
        Number of tasks purged
    """
    if queue_name:
        return celery_app.control.purge(queue=queue_name)
    else:
        return celery_app.control.purge()

# =============================================================================
# HEALTH CHECK
# =============================================================================

def health_check() -> dict:
    """
    Check Celery health status

    Returns:
        Dictionary with health status
    """
    try:
        # Check if we can connect to broker
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if not stats:
            return {
                'status': 'unhealthy',
                'message': 'No workers available',
                'workers': 0
            }

        # Get worker info
        active_tasks = inspect.active() or {}
        reserved_tasks = inspect.reserved() or {}

        worker_count = len(stats)
        total_active = sum(len(tasks) for tasks in active_tasks.values())
        total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())

        return {
            'status': 'healthy',
            'workers': worker_count,
            'active_tasks': total_active,
            'reserved_tasks': total_reserved,
            'broker_url': settings.CELERY_BROKER_URL.split('@')[-1] if '@' in settings.CELERY_BROKER_URL else 'redis',
            'stats': stats
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': str(e),
            'workers': 0
        }

# Export the celery app
__all__ = ['celery_app', 'BaseTask', 'get_task_info', 'cancel_task', 'health_check']