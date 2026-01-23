"""
Event Bus Module - Phase 3

CRITICAL RULES:
- Event = DELIVERY, not COMMAND
- Event = FACT already happened
- Publish failure NEVER rolls back decision
- No business logic in consumers

Source: Phase 3 Requirements
"""

from .schemas import (
    EventEnvelope,
    EventSchema,
    SCHEMA_REGISTRY,
    get_schema_version,
)
from .publisher import (
    EventPublisher,
    PublisherConfig,
)
from .outbox import (
    OutboxPoller,
    OutboxConfig,
    RetryConfig,
)
from .consumer import (
    EventConsumer,
    ConsumerConfig,
    ConsumerHandler,
)
from .topics import (
    TOPIC_DECISIONS,
    TOPIC_WORKFLOWS,
    TOPIC_AUDIT,
    get_topic_for_event,
)

__all__ = [
    # Schemas
    "EventEnvelope",
    "EventSchema",
    "SCHEMA_REGISTRY",
    "get_schema_version",
    # Publisher
    "EventPublisher",
    "PublisherConfig",
    # Outbox
    "OutboxPoller",
    "OutboxConfig",
    "RetryConfig",
    # Consumer
    "EventConsumer",
    "ConsumerConfig",
    "ConsumerHandler",
    # Topics
    "TOPIC_DECISIONS",
    "TOPIC_WORKFLOWS",
    "TOPIC_AUDIT",
    "get_topic_for_event",
]
