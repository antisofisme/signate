"""
Event Consumer Framework - Stateless, Idempotent, Read-Only

CRITICAL CONSUMER RULES (NON-NEGOTIABLE):
1. Consumers MUST be stateless
2. Consumers MUST be idempotent
3. Consumers MUST be read-only toward Core
4. Consumers MUST NOT mutate decision/workflow

CONSUMERS MAY:
- Update read models
- Trigger notifications
- Forward to external systems

CONSUMERS MAY NOT:
- Call Core mutation API
- Write to core tables
- Create new decisions

Source: Phase 3 Requirements - Consumer Rules
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set, Callable, Awaitable, Dict, Any, Protocol
from uuid import UUID
import logging
import asyncio

from .schemas import EventEnvelope
from .metrics import (
    consumer_lag,
    consumer_messages_processed,
    consumer_processing_duration,
    consumer_idempotency_hits,
)


logger = logging.getLogger(__name__)


# =============================================================================
# CONSUMER CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class ConsumerConfig:
    """Consumer configuration"""
    # Identity
    consumer_group: str
    consumer_id: str  # Unique per instance

    # Topics
    topics: tuple  # Subscribed topics (immutable)

    # Processing
    max_poll_records: int = 100
    poll_timeout_ms: int = 1000
    auto_commit: bool = False  # Manual commit for exactly-once effect

    # Idempotency
    idempotency_window_hours: int = 24  # How long to remember processed events

    # Health
    max_processing_time_seconds: int = 30


# =============================================================================
# IDEMPOTENCY STORE (Protocol)
# =============================================================================

class IdempotencyStore(Protocol):
    """
    Protocol for idempotency store.

    CRITICAL: Consumers MUST use this to achieve idempotent processing.
    """

    async def has_processed(self, event_id: str) -> bool:
        """Check if event was already processed"""
        ...

    async def mark_processed(self, event_id: str, consumer_group: str) -> None:
        """Mark event as processed"""
        ...


class InMemoryIdempotencyStore:
    """
    In-memory idempotency store for testing.

    WARNING: Do not use in production - state is lost on restart.
    Production should use Redis or database.
    """

    def __init__(self, max_size: int = 100000):
        self._processed: Set[str] = set()
        self._max_size = max_size

    async def has_processed(self, event_id: str) -> bool:
        return event_id in self._processed

    async def mark_processed(self, event_id: str, consumer_group: str) -> None:
        if len(self._processed) >= self._max_size:
            # Simple eviction: clear half
            to_remove = list(self._processed)[:self._max_size // 2]
            for item in to_remove:
                self._processed.discard(item)

        self._processed.add(event_id)


# =============================================================================
# CONSUMER HANDLER (Abstract Base)
# =============================================================================

class ConsumerHandler(ABC):
    """
    Base class for event handlers.

    CRITICAL RULES:
    - Handler MUST be idempotent
    - Handler MUST NOT call Core mutation APIs
    - Handler MUST NOT write to core tables
    - Handler SHOULD complete within max_processing_time_seconds
    """

    @abstractmethod
    async def handle(self, event: EventEnvelope) -> bool:
        """
        Handle event.

        CRITICAL:
        - Return True if handled successfully
        - Return False if should be retried
        - Raise exception only for fatal errors

        Args:
            event: Event envelope

        Returns:
            True if handled, False if should retry
        """
        pass

    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """
        Check if handler can process event type.

        Args:
            event_type: Event type string

        Returns:
            True if can handle
        """
        pass


# =============================================================================
# READ MODEL UPDATER (Example Consumer)
# =============================================================================

class ReadModelUpdater(ConsumerHandler):
    """
    Example consumer that updates read models.

    CRITICAL: This is READ-ONLY toward Core.
    It only updates denormalized read models for queries.
    """

    def __init__(
        self,
        update_fn: Callable[[EventEnvelope], Awaitable[bool]],
        event_types: Set[str],
    ):
        """
        Args:
            update_fn: Async function to update read model
            event_types: Set of event types this handler processes
        """
        self._update_fn = update_fn
        self._event_types = event_types

    async def handle(self, event: EventEnvelope) -> bool:
        """Update read model"""
        return await self._update_fn(event)

    def can_handle(self, event_type: str) -> bool:
        return event_type in self._event_types


class NotificationSender(ConsumerHandler):
    """
    Example consumer that sends notifications.

    CRITICAL: Does NOT mutate Core state.
    Only sends external notifications.
    """

    def __init__(
        self,
        send_fn: Callable[[EventEnvelope], Awaitable[bool]],
        event_types: Set[str],
    ):
        self._send_fn = send_fn
        self._event_types = event_types

    async def handle(self, event: EventEnvelope) -> bool:
        """Send notification"""
        return await self._send_fn(event)

    def can_handle(self, event_type: str) -> bool:
        return event_type in self._event_types


# =============================================================================
# EVENT CONSUMER
# =============================================================================

class EventConsumer:
    """
    Event consumer - processes events from event bus.

    CRITICAL ENFORCEMENT:
    - All handlers must be idempotent
    - All handlers must be read-only toward Core
    - Processing failures don't affect source of truth
    """

    def __init__(
        self,
        config: ConsumerConfig,
        handlers: list,  # List[ConsumerHandler]
        idempotency_store: IdempotencyStore,
    ):
        self._config = config
        self._handlers = handlers
        self._idempotency_store = idempotency_store
        self._is_running = False
        self._stop_event = asyncio.Event()

        # Validate handlers
        self._validate_handlers()

    def _validate_handlers(self) -> None:
        """Validate all handlers are proper ConsumerHandler instances"""
        for handler in self._handlers:
            if not isinstance(handler, ConsumerHandler):
                raise ValueError(
                    f"Handler {handler} must be a ConsumerHandler instance"
                )

    async def process_event(self, event: EventEnvelope) -> bool:
        """
        Process single event.

        CRITICAL: Idempotent processing with metrics.

        Returns:
            True if processed (or already processed), False if all handlers failed
        """
        event_id = event.event_id
        event_type = event.event_type

        # Check idempotency first
        if await self._idempotency_store.has_processed(event_id):
            consumer_idempotency_hits.labels(
                consumer_group=self._config.consumer_group,
                event_type=event_type,
            ).inc()

            logger.debug(
                "Event already processed (idempotent)",
                extra={
                    "event_id": event_id,
                    "event_type": event_type,
                    "consumer_group": self._config.consumer_group,
                }
            )
            return True

        # Calculate consumer lag
        try:
            published_at = datetime.fromisoformat(event.published_at)
            lag_seconds = (datetime.utcnow() - published_at).total_seconds()
            consumer_lag.labels(
                consumer_group=self._config.consumer_group,
                event_type=event_type,
            ).observe(lag_seconds)
        except Exception:
            pass  # Don't fail on metric errors

        # Find handlers for this event type
        applicable_handlers = [
            h for h in self._handlers
            if h.can_handle(event_type)
        ]

        if not applicable_handlers:
            # No handler for this event type - skip
            consumer_messages_processed.labels(
                consumer_group=self._config.consumer_group,
                event_type=event_type,
                status="skipped",
            ).inc()

            logger.debug(
                "No handler for event type",
                extra={
                    "event_id": event_id,
                    "event_type": event_type,
                    "consumer_group": self._config.consumer_group,
                }
            )
            return True

        # Process with all applicable handlers
        all_success = True
        start_time = datetime.utcnow()

        for handler in applicable_handlers:
            try:
                success = await asyncio.wait_for(
                    handler.handle(event),
                    timeout=self._config.max_processing_time_seconds
                )

                if not success:
                    all_success = False
                    logger.warning(
                        "Handler returned failure",
                        extra={
                            "event_id": event_id,
                            "event_type": event_type,
                            "handler": handler.__class__.__name__,
                        }
                    )

            except asyncio.TimeoutError:
                all_success = False
                logger.error(
                    "Handler timeout",
                    extra={
                        "event_id": event_id,
                        "event_type": event_type,
                        "handler": handler.__class__.__name__,
                        "timeout_seconds": self._config.max_processing_time_seconds,
                    }
                )

            except Exception as e:
                all_success = False
                logger.error(
                    "Handler exception",
                    extra={
                        "event_id": event_id,
                        "event_type": event_type,
                        "handler": handler.__class__.__name__,
                        "error": str(e),
                    },
                    exc_info=True
                )

        # Record processing duration
        duration = (datetime.utcnow() - start_time).total_seconds()
        consumer_processing_duration.labels(
            consumer_group=self._config.consumer_group,
            event_type=event_type,
        ).observe(duration)

        if all_success:
            # Mark as processed for idempotency
            await self._idempotency_store.mark_processed(
                event_id,
                self._config.consumer_group
            )

            consumer_messages_processed.labels(
                consumer_group=self._config.consumer_group,
                event_type=event_type,
                status="success",
            ).inc()

            logger.info(
                "Event processed successfully",
                extra={
                    "event_id": event_id,
                    "event_type": event_type,
                    "consumer_group": self._config.consumer_group,
                    "duration_seconds": duration,
                }
            )

        else:
            consumer_messages_processed.labels(
                consumer_group=self._config.consumer_group,
                event_type=event_type,
                status="failure",
            ).inc()

        return all_success


# =============================================================================
# FORBIDDEN OPERATIONS CHECK
# =============================================================================

# List of forbidden imports in consumer handlers
FORBIDDEN_CONSUMER_IMPORTS = [
    "create_decision",
    "CreateDecisionUseCase",
    "DecisionRepository",
    "WorkflowRepository",
    "RuleRepository",
    "UnitOfWork",
]

# List of forbidden HTTP endpoints
FORBIDDEN_CONSUMER_ENDPOINTS = [
    "POST /api/v1/decisions",
    "POST /api/v1/workflows",
    "PUT /api/v1/decisions",
    "PUT /api/v1/workflows",
    "DELETE /api/v1/decisions",
    "DELETE /api/v1/workflows",
]


def validate_consumer_handler_imports(handler_module) -> list:
    """
    Validate that handler module doesn't import forbidden modules.

    CRITICAL: Used in bypass tests to ensure consumers don't mutate Core.

    Returns:
        List of violation errors (empty if valid)
    """
    errors = []
    module_attrs = dir(handler_module)

    for forbidden in FORBIDDEN_CONSUMER_IMPORTS:
        if forbidden in module_attrs:
            errors.append(f"Consumer handler imports forbidden: {forbidden}")

    return errors
