"""
Base Worker - Abstract base class for MANTRA workers.

All workers inherit from this base class which provides:
- Connection management
- Graceful shutdown
- Health checking
- Logging infrastructure

Usage:
    class MyWorker(BaseWorker):
        async def setup(self):
            await self.queue.subscribe("my_queue", self.handle_message)

        async def handle_message(self, message):
            # Process message
            ...
"""

import logging
import asyncio
import signal
from abc import ABC, abstractmethod
from typing import Optional, Set

from core.ports.message_queue import MessageQueueProtocol, Message

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """
    Abstract base class for MANTRA background workers.

    Provides common functionality:
    - Lifecycle management (start/stop)
    - Signal handling (SIGTERM, SIGINT)
    - Health reporting
    - Error recovery
    """

    def __init__(
        self,
        queue: MessageQueueProtocol,
        name: str = "worker",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize base worker.

        Args:
            queue: Message queue implementation
            name: Worker name for logging
            max_retries: Maximum retries for failed messages
            retry_delay: Delay between retries in seconds
        """
        self.queue = queue
        self.name = name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.running = False
        self._tasks: Set[asyncio.Task] = set()
        self._processed_count = 0
        self._error_count = 0
        logger.info(f"Worker initialized: {name}")

    async def start(self) -> None:
        """
        Start the worker.

        Connects to queue, sets up subscriptions, and begins processing.
        """
        logger.info(f"Starting worker: {self.name}")
        self.running = True

        # Setup signal handlers
        self._setup_signals()

        try:
            # Connect to queue
            await self.queue.connect()
            logger.info(f"Worker {self.name} connected to queue")

            # Run worker-specific setup
            await self.setup()

            # Keep running until stopped
            while self.running:
                await asyncio.sleep(0.1)
                await self.process()

        except asyncio.CancelledError:
            logger.info(f"Worker {self.name} cancelled")
        except Exception as e:
            logger.error(f"Worker {self.name} error: {e}")
            raise
        finally:
            await self.cleanup()

    async def stop(self) -> None:
        """
        Stop the worker gracefully.

        Waits for pending tasks to complete before shutdown.
        """
        logger.info(f"Stopping worker: {self.name}")
        self.running = False

        # Wait for pending tasks
        if self._tasks:
            logger.info(f"Waiting for {len(self._tasks)} pending tasks...")
            await asyncio.gather(*self._tasks, return_exceptions=True)

        await self.queue.disconnect()
        logger.info(f"Worker {self.name} stopped")

    def _setup_signals(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.stop())
            )

    @abstractmethod
    async def setup(self) -> None:
        """
        Worker-specific setup.

        Override to subscribe to queues and configure handlers.
        """
        pass

    async def process(self) -> None:
        """
        Main processing loop iteration.

        Override for custom processing logic. Default does nothing
        (relies on subscription callbacks).
        """
        pass

    async def cleanup(self) -> None:
        """
        Cleanup resources before shutdown.

        Override for custom cleanup logic.
        """
        pass

    async def handle_message_with_retry(
        self,
        message: Message,
        handler,
    ) -> bool:
        """
        Handle a message with retry logic.

        Args:
            message: Message to process
            handler: Async handler function

        Returns:
            True if processed successfully
        """
        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                await handler(message)
                self._processed_count += 1
                await self.queue.acknowledge(message.id)
                return True

            except Exception as e:
                last_error = e
                retries += 1
                self._error_count += 1
                logger.warning(
                    f"Message {message.id} failed (attempt {retries}/{self.max_retries}): {e}"
                )

                if retries <= self.max_retries:
                    await asyncio.sleep(self.retry_delay * retries)

        # Max retries exceeded
        logger.error(f"Message {message.id} failed after {self.max_retries} retries: {last_error}")
        await self.queue.reject(message.id, requeue=False)
        return False

    def get_stats(self) -> dict:
        """
        Get worker statistics.

        Returns:
            Dict with worker stats
        """
        return {
            "name": self.name,
            "running": self.running,
            "processed_count": self._processed_count,
            "error_count": self._error_count,
            "pending_tasks": len(self._tasks),
        }

    async def health_check(self) -> dict:
        """
        Perform health check.

        Returns:
            Dict with health status
        """
        queue_healthy = await self.queue.health_check()

        return {
            "healthy": self.running and queue_healthy,
            "worker_running": self.running,
            "queue_connected": queue_healthy,
            "stats": self.get_stats(),
        }


class WorkerManager:
    """
    Manager for running multiple workers.

    Handles starting/stopping workers and coordinating shutdown.
    """

    def __init__(self):
        """Initialize worker manager."""
        self.workers: list[BaseWorker] = []
        self._tasks: list[asyncio.Task] = []

    def add_worker(self, worker: BaseWorker) -> None:
        """Add a worker to the manager."""
        self.workers.append(worker)

    async def start_all(self) -> None:
        """Start all workers."""
        logger.info(f"Starting {len(self.workers)} workers...")

        for worker in self.workers:
            task = asyncio.create_task(worker.start())
            self._tasks.append(task)

        # Wait for all workers
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop_all(self) -> None:
        """Stop all workers gracefully."""
        logger.info(f"Stopping {len(self.workers)} workers...")

        for worker in self.workers:
            await worker.stop()

        # Cancel remaining tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

    async def health_check(self) -> dict:
        """Check health of all workers."""
        results = {}
        for worker in self.workers:
            results[worker.name] = await worker.health_check()
        return results
