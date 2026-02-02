"""
Background Job System

Async job processing for MANTRA using Celery with RabbitMQ.

Jobs:
- Embedding computation
- Document generation
- Export synchronization
- Analytics aggregation
"""

from .celery_app import celery_app
from .tasks import (
    compute_embeddings_task,
    generate_document_task,
    export_document_task,
    aggregate_analytics_task,
    sync_export_task,
    reindex_decisions_task,
)

__all__ = [
    "celery_app",
    "compute_embeddings_task",
    "generate_document_task",
    "export_document_task",
    "aggregate_analytics_task",
    "sync_export_task",
    "reindex_decisions_task",
]
