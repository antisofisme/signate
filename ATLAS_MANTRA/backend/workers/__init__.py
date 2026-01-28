"""
MANTRA Workers - Background task processors.

Workers consume messages from the queue and process them asynchronously.
This enables non-blocking operations for:
- Decision validation
- Embedding synchronization
- Search index updates

Usage:
    # Start all workers
    python -m workers

    # Start specific worker
    python -m workers --worker validation

Available workers:
- ValidationWorker: Processes decision validation requests
- SyncWorker: Handles embedding synchronization
"""

from .base import BaseWorker
from .validation_worker import ValidationWorker
from .sync_worker import SyncWorker

__all__ = [
    "BaseWorker",
    "ValidationWorker",
    "SyncWorker",
]
