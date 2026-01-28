"""
Message Queue Port - Abstract interface for async message processing.

This port defines the contract for message queue operations used to
enable async processing of validation, embedding sync, and events.

Implementations can use:
- RabbitMQ (primary)
- Redis Streams (fallback)
- In-memory (testing)

Usage:
    class RabbitMQAdapter(MessageQueueProtocol):
        async def publish(self, queue, message):
            # RabbitMQ-specific implementation
            ...
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, Optional, Awaitable
from datetime import datetime
import uuid


@dataclass
class Message:
    """
    Message payload for queue operations.

    Attributes:
        id: Unique message identifier
        event_type: Type of event (e.g., "decision.proposed")
        payload: Event data
        timestamp: ISO format timestamp
        correlation_id: Optional ID for request tracing
        metadata: Additional message metadata
    """
    event_type: str
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize message to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Deserialize message from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            event_type=data["event_type"],
            payload=data["payload"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {}),
        )


class MantraEvents:
    """
    Event types for MANTRA system.

    Naming convention: {domain}.{action}
    """
    # Decision events
    DECISION_PROPOSED = "decision.proposed"
    DECISION_VALIDATED = "decision.validated"
    DECISION_APPROVED = "decision.approved"
    DECISION_REJECTED = "decision.rejected"
    DECISION_UPDATED = "decision.updated"

    # Embedding events
    EMBEDDING_SYNC_REQUESTED = "embedding.sync.requested"
    EMBEDDING_SYNC_COMPLETED = "embedding.sync.completed"
    EMBEDDING_SYNC_FAILED = "embedding.sync.failed"

    # Search events
    SEARCH_INDEX_REQUESTED = "search.index.requested"
    SEARCH_INDEX_COMPLETED = "search.index.completed"

    # System events
    HEALTH_CHECK = "system.health.check"
    CACHE_INVALIDATE = "system.cache.invalidate"


# Type alias for message handlers
MessageHandler = Callable[[Message], Awaitable[None]]


class MessageQueueProtocol(ABC):
    """
    Abstract protocol for message queue operations.

    This interface allows swapping queue implementations
    without changing business logic. Supports:
    - RabbitMQ (primary)
    - Redis Streams (fallback)
    - In-memory (testing/development)
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the message broker.

        Should be called during application startup.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close connection to the message broker.

        Should be called during application shutdown.
        """
        pass

    @abstractmethod
    async def publish(self, queue: str, message: Message) -> None:
        """
        Publish a message to a queue.

        Args:
            queue: Queue name
            message: Message to publish
        """
        pass

    @abstractmethod
    async def subscribe(
        self,
        queue: str,
        handler: MessageHandler,
        prefetch_count: int = 1
    ) -> None:
        """
        Subscribe to a queue and process messages.

        Args:
            queue: Queue name
            handler: Async function to process messages
            prefetch_count: Number of messages to prefetch (default: 1)
        """
        pass

    @abstractmethod
    async def acknowledge(self, message_id: str) -> None:
        """
        Acknowledge successful processing of a message.

        Args:
            message_id: Message ID to acknowledge
        """
        pass

    @abstractmethod
    async def reject(self, message_id: str, requeue: bool = False) -> None:
        """
        Reject a message (failed processing).

        Args:
            message_id: Message ID to reject
            requeue: Whether to requeue the message
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the message queue is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    async def get_queue_stats(self, queue: str) -> Dict[str, Any]:
        """
        Get statistics for a queue.

        Args:
            queue: Queue name

        Returns:
            Dict with queue stats (message_count, consumer_count, etc.)
        """
        pass

    async def close(self) -> None:
        """Alias for disconnect (for consistent interface)."""
        await self.disconnect()
