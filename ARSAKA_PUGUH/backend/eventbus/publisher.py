"""
Event Publisher - Publishes events from outbox to event bus

CRITICAL RULES:
- Event publish is ALWAYS async (never in request path)
- Publish failure DOES NOT rollback decision
- Event bus DOES NOT call Core API
- At-least-once delivery guarantee

Source: Phase 3 Requirements - Event Bus Infrastructure
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol, List
from uuid import UUID
import logging
import asyncio

from .schemas import EventEnvelope, get_schema_version
from .topics import get_topic_for_event, get_message_key


logger = logging.getLogger(__name__)


# =============================================================================
# PUBLISHER PROTOCOL (Interface)
# =============================================================================

class EventBusProducer(Protocol):
    """
    Protocol for event bus producer (Kafka, Redpanda, etc.)

    CRITICAL: This is an interface. Actual implementation depends on
    the message broker being used.
    """

    async def send(
        self,
        topic: str,
        key: bytes,
        value: bytes,
        headers: Optional[dict] = None
    ) -> None:
        """
        Send message to event bus.

        Args:
            topic: Target topic
            key: Message key (for partitioning)
            value: Message value (serialized event)
            headers: Optional message headers

        Raises:
            Exception: If send fails
        """
        ...

    async def flush(self) -> None:
        """Flush pending messages"""
        ...

    async def close(self) -> None:
        """Close producer connection"""
        ...


# =============================================================================
# PUBLISHER CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class PublisherConfig:
    """
    Publisher configuration.

    CRITICAL: These values affect delivery guarantees.
    """
    # Kafka connection
    bootstrap_servers: str = "localhost:9092"

    # Producer settings
    acks: str = "all"  # Wait for all replicas
    retries: int = 3   # Internal Kafka retries (not our retry)
    retry_backoff_ms: int = 100

    # Timeouts
    request_timeout_ms: int = 30000
    delivery_timeout_ms: int = 120000

    # Batch settings
    batch_size: int = 16384  # 16KB
    linger_ms: int = 5       # Wait up to 5ms for batching

    # Compression
    compression_type: str = "gzip"


# =============================================================================
# EVENT PUBLISHER
# =============================================================================

class EventPublisher:
    """
    Event publisher - converts domain events to wire format and publishes.

    CRITICAL RULES:
    - NEVER called from request handler (always async)
    - NEVER blocks decision creation
    - Publish failure = metric + log, NOT exception propagation
    """

    def __init__(
        self,
        producer: EventBusProducer,
        config: Optional[PublisherConfig] = None
    ):
        self._producer = producer
        self._config = config or PublisherConfig()
        self._is_running = False

    async def publish(
        self,
        event_id: UUID,
        event_type: str,
        aggregate_id: UUID,
        aggregate_type: str,
        tenant_id: UUID,
        payload: dict,
        occurred_at: datetime,
        recorded_at: datetime,
        trace_id: Optional[UUID] = None,
        caused_by_user_id: Optional[UUID] = None,
        schema_version: Optional[str] = None,
    ) -> bool:
        """
        Publish single event to event bus.

        CRITICAL: Returns True/False, NEVER raises exception to caller.

        Args:
            event_id: Event UUID
            event_type: Event type (e.g., "decision.created")
            aggregate_id: Aggregate UUID (decision_id or workflow_id)
            aggregate_type: "decision" or "workflow"
            tenant_id: Tenant UUID
            payload: Event payload dict
            occurred_at: When event occurred
            recorded_at: When event was recorded in DB
            trace_id: Optional trace ID
            caused_by_user_id: Optional user ID
            schema_version: Optional schema version (defaults to latest)

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Build envelope
            envelope = EventEnvelope(
                event_id=str(event_id),
                event_type=event_type,
                schema_version=schema_version or get_schema_version(event_type),
                aggregate_id=str(aggregate_id),
                aggregate_type=aggregate_type,
                tenant_id=str(tenant_id),
                occurred_at=occurred_at.isoformat(),
                recorded_at=recorded_at.isoformat(),
                published_at=datetime.utcnow().isoformat(),
                trace_id=str(trace_id) if trace_id else None,
                caused_by_user_id=str(caused_by_user_id) if caused_by_user_id else None,
                payload=payload,
                source="core",
            )

            # Get topic and key
            topic = get_topic_for_event(event_type)
            key = get_message_key(str(aggregate_id))

            # Headers for tracing
            headers = {}
            if trace_id:
                headers["trace_id"] = str(trace_id).encode("utf-8")
            if tenant_id:
                headers["tenant_id"] = str(tenant_id).encode("utf-8")

            # Publish
            await self._producer.send(
                topic=topic,
                key=key,
                value=envelope.to_bytes(),
                headers=headers if headers else None
            )

            logger.info(
                "Event published",
                extra={
                    "event_id": str(event_id),
                    "event_type": event_type,
                    "aggregate_id": str(aggregate_id),
                    "topic": topic,
                    "trace_id": str(trace_id) if trace_id else None,
                }
            )

            return True

        except Exception as e:
            # CRITICAL: Log error but DON'T propagate
            # Publish failure MUST NOT affect decision
            logger.error(
                "Event publish failed",
                extra={
                    "event_id": str(event_id),
                    "event_type": event_type,
                    "aggregate_id": str(aggregate_id),
                    "error": str(e),
                    "trace_id": str(trace_id) if trace_id else None,
                },
                exc_info=True
            )
            return False

    async def publish_batch(
        self,
        events: List[dict]
    ) -> tuple:
        """
        Publish batch of events.

        Args:
            events: List of event dicts with all required fields

        Returns:
            Tuple of (success_count, failure_count, failed_event_ids)
        """
        success_count = 0
        failure_count = 0
        failed_event_ids = []

        for event in events:
            success = await self.publish(
                event_id=event["event_id"],
                event_type=event["event_type"],
                aggregate_id=event["aggregate_id"],
                aggregate_type=event["aggregate_type"],
                tenant_id=event["tenant_id"],
                payload=event["payload"],
                occurred_at=event["occurred_at"],
                recorded_at=event["recorded_at"],
                trace_id=event.get("trace_id"),
                caused_by_user_id=event.get("caused_by_user_id"),
                schema_version=event.get("schema_version"),
            )

            if success:
                success_count += 1
            else:
                failure_count += 1
                failed_event_ids.append(event["event_id"])

        return success_count, failure_count, failed_event_ids

    async def flush(self) -> None:
        """Flush pending messages"""
        await self._producer.flush()

    async def close(self) -> None:
        """Close publisher"""
        await self._producer.close()


# =============================================================================
# MOCK PRODUCER (for testing without Kafka)
# =============================================================================

class MockEventBusProducer:
    """
    Mock producer for testing.

    CRITICAL: Use only in tests. Never in production.
    """

    def __init__(self):
        self.messages: List[dict] = []
        self.should_fail: bool = False
        self.fail_count: int = 0
        self.max_failures: int = 0

    async def send(
        self,
        topic: str,
        key: bytes,
        value: bytes,
        headers: Optional[dict] = None
    ) -> None:
        """Mock send - stores message or fails if configured"""
        if self.should_fail and self.fail_count < self.max_failures:
            self.fail_count += 1
            raise Exception("Mock publish failure")

        self.messages.append({
            "topic": topic,
            "key": key,
            "value": value,
            "headers": headers,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def flush(self) -> None:
        """Mock flush - no-op"""
        pass

    async def close(self) -> None:
        """Mock close - no-op"""
        pass

    def get_messages(self) -> List[dict]:
        """Get all sent messages"""
        return self.messages

    def clear(self) -> None:
        """Clear message store"""
        self.messages.clear()
        self.fail_count = 0

    def set_fail_mode(self, fail: bool, max_failures: int = 1) -> None:
        """Configure failure mode for testing"""
        self.should_fail = fail
        self.max_failures = max_failures
        self.fail_count = 0
