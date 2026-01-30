"""
Celery Application Configuration

Configures Celery with RabbitMQ broker and Redis result backend.
"""

import os
from celery import Celery
from kombu import Queue, Exchange

# Configuration from environment
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "mantra_jobs",
    broker=RABBITMQ_URL,
    backend=REDIS_URL,
    include=["core.jobs.tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # Soft limit 9 minutes

    # Result backend
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # Rate limiting
    task_default_rate_limit="100/m",

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Queue configuration
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("embeddings", Exchange("embeddings"), routing_key="embeddings"),
        Queue("documents", Exchange("documents"), routing_key="documents"),
        Queue("exports", Exchange("exports"), routing_key="exports"),
        Queue("analytics", Exchange("analytics"), routing_key="analytics"),
    ),
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",

    # Task routing
    task_routes={
        "core.jobs.tasks.compute_embeddings_task": {"queue": "embeddings"},
        "core.jobs.tasks.reindex_decisions_task": {"queue": "embeddings"},
        "core.jobs.tasks.generate_document_task": {"queue": "documents"},
        "core.jobs.tasks.export_document_task": {"queue": "exports"},
        "core.jobs.tasks.sync_export_task": {"queue": "exports"},
        "core.jobs.tasks.aggregate_analytics_task": {"queue": "analytics"},
    },
)


# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "aggregate-analytics-hourly": {
        "task": "core.jobs.tasks.aggregate_analytics_task",
        "schedule": 3600.0,  # Every hour
        "args": (),
    },
    "sync-exports-daily": {
        "task": "core.jobs.tasks.sync_export_task",
        "schedule": 86400.0,  # Every 24 hours
        "args": (),
    },
}


def get_celery_app() -> Celery:
    """Get the Celery app instance."""
    return celery_app
