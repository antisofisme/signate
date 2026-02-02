"""
Job queue interfaces for background processing.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator, Tuple


class JobQueue(ABC):
    """
    Interface for job queue (Redis Streams).

    Implementations: RedisJobQueue
    """

    @abstractmethod
    async def publish(
        self,
        queue: str,
        job: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """
        Add job to queue.

        Args:
            queue: Queue name
            job: Job data
            priority: Job priority (higher = more urgent)

        Returns:
            Job ID
        """
        pass

    @abstractmethod
    async def consume(
        self,
        queue: str,
        group: str,
        consumer: str,
        count: int = 1,
        block_ms: int = 5000
    ) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
        """
        Consume jobs from queue.

        Args:
            queue: Queue name
            group: Consumer group name
            consumer: Consumer ID
            count: Max jobs to fetch
            block_ms: Block timeout

        Yields:
            Tuple of (job_id, job_data)
        """
        pass

    @abstractmethod
    async def ack(
        self,
        queue: str,
        group: str,
        job_id: str
    ) -> None:
        """
        Acknowledge job completion.

        Args:
            queue: Queue name
            group: Consumer group
            job_id: Job ID to acknowledge
        """
        pass

    @abstractmethod
    async def retry(
        self,
        queue: str,
        job_id: str,
        job: Dict[str, Any],
        delay_seconds: int = 0
    ) -> bool:
        """
        Retry failed job.

        Args:
            queue: Queue name
            job_id: Original job ID
            job: Job data (may be modified)
            delay_seconds: Delay before retry

        Returns:
            True if queued for retry
        """
        pass

    @abstractmethod
    async def get_queue_info(
        self,
        queue: str
    ) -> Dict[str, Any]:
        """
        Get queue statistics.

        Args:
            queue: Queue name

        Returns:
            Dict with length, pending, consumers, etc.
        """
        pass

    @abstractmethod
    async def create_group(
        self,
        queue: str,
        group: str
    ) -> bool:
        """
        Create consumer group.

        Args:
            queue: Queue name
            group: Group name

        Returns:
            True if created
        """
        pass
