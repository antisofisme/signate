"""
Base Worker

Abstract base class for background workers.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Any
from datetime import datetime

from ..shared.logging import get_logger

logger = get_logger(__name__)


class BaseWorker(ABC):
    """
    Base class for background workers.

    Features:
    - Graceful shutdown
    - Error handling with retry
    - Logging
    - Health reporting
    """

    def __init__(
        self,
        name: str,
        poll_interval: float = 5.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.name = name
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_run: Optional[datetime] = None
        self._error_count = 0
        self._success_count = 0

    async def start(self) -> None:
        """Start the worker."""
        if self._running:
            logger.warning(f"Worker {self.name} already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Worker {self.name} started")

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(f"Worker {self.name} stopped")

    async def _run_loop(self) -> None:
        """Main worker loop."""
        while self._running:
            try:
                # Process work
                await self._process_with_retry()
                self._last_run = datetime.utcnow()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {self.name} loop error: {e}")
                self._error_count += 1

            # Wait before next poll
            if self._running:
                await asyncio.sleep(self.poll_interval)

    async def _process_with_retry(self) -> None:
        """Process with retry logic."""
        for attempt in range(self.max_retries):
            try:
                await self.process()
                self._success_count += 1
                return
            except Exception as e:
                logger.warning(
                    f"Worker {self.name} attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

    @abstractmethod
    async def process(self) -> None:
        """
        Process work items.

        Override in subclasses to implement actual work.
        Should be idempotent and handle partial failures.
        """
        pass

    def get_health(self) -> dict:
        """Get worker health status."""
        return {
            "name": self.name,
            "running": self._running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "success_count": self._success_count,
            "error_count": self._error_count,
        }

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running


class QueueWorker(BaseWorker):
    """
    Worker that processes items from a queue (Redis Streams).
    """

    def __init__(
        self,
        name: str,
        queue_name: str,
        consumer_group: str,
        poll_interval: float = 1.0,
        batch_size: int = 10,
        **kwargs,
    ):
        super().__init__(name, poll_interval, **kwargs)
        self.queue_name = queue_name
        self.consumer_group = consumer_group
        self.batch_size = batch_size

    async def process(self) -> None:
        """Process items from queue."""
        # Override in subclass with actual queue processing
        pass

    @abstractmethod
    async def process_item(self, item: dict) -> None:
        """
        Process a single queue item.

        Override in subclasses.
        """
        pass


class ScheduledWorker(BaseWorker):
    """
    Worker that runs on a schedule (cron-like).
    """

    def __init__(
        self,
        name: str,
        schedule_seconds: int = 3600,  # Default: hourly
        **kwargs,
    ):
        super().__init__(name, poll_interval=schedule_seconds, **kwargs)
        self.schedule_seconds = schedule_seconds
        self._next_run: Optional[datetime] = None

    async def start(self) -> None:
        """Start with immediate first run option."""
        self._next_run = datetime.utcnow()
        await super().start()

    async def _run_loop(self) -> None:
        """Scheduled run loop."""
        while self._running:
            try:
                now = datetime.utcnow()

                if self._next_run and now >= self._next_run:
                    await self._process_with_retry()
                    self._last_run = now
                    self._next_run = datetime.utcnow()
                    # Add schedule_seconds for next run
                    from datetime import timedelta
                    self._next_run += timedelta(seconds=self.schedule_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduled worker {self.name} error: {e}")
                self._error_count += 1

            # Short sleep to check schedule
            if self._running:
                await asyncio.sleep(min(60, self.poll_interval))

    def get_health(self) -> dict:
        """Get health with next run time."""
        health = super().get_health()
        health["next_run"] = self._next_run.isoformat() if self._next_run else None
        return health
