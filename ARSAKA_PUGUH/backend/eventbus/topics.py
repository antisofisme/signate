"""
Topic Definitions

CRITICAL:
- Topic per event category (decision, workflow, audit)
- Message key = aggregate_id (ensures ordering per aggregate)
- Topics are APPEND-ONLY

Source: Phase 3 Requirements - Event Bus Infrastructure
"""

from typing import Optional


# =============================================================================
# TOPIC DEFINITIONS
# =============================================================================

# Topic naming convention: {namespace}.{category}.events
# Example: infra.decisions.events

TOPIC_PREFIX = "infra"

# Decision events topic
TOPIC_DECISIONS = f"{TOPIC_PREFIX}.decisions.events"

# Workflow events topic
TOPIC_WORKFLOWS = f"{TOPIC_PREFIX}.workflows.events"

# Audit events topic (operations_audit, system events)
TOPIC_AUDIT = f"{TOPIC_PREFIX}.audit.events"


# =============================================================================
# TOPIC ROUTING
# =============================================================================

# Map event types to topics
EVENT_TYPE_TO_TOPIC = {
    # Decision events → decisions topic
    "decision.created": TOPIC_DECISIONS,
    "decision.allowed": TOPIC_DECISIONS,
    "decision.denied": TOPIC_DECISIONS,
    "decision.requires_approval": TOPIC_DECISIONS,

    # Workflow events → workflows topic
    "workflow.created": TOPIC_WORKFLOWS,
    "workflow.pending_approval": TOPIC_WORKFLOWS,
    "workflow.approved": TOPIC_WORKFLOWS,
    "workflow.rejected": TOPIC_WORKFLOWS,
    "workflow.delegated": TOPIC_WORKFLOWS,
    "workflow.escalated": TOPIC_WORKFLOWS,
    "workflow.completed": TOPIC_WORKFLOWS,
}


def get_topic_for_event(event_type: str) -> str:
    """
    Get topic for event type.

    CRITICAL: Unknown event types go to audit topic (fallback).

    Args:
        event_type: Event type string (e.g., "decision.created")

    Returns:
        Topic name
    """
    return EVENT_TYPE_TO_TOPIC.get(event_type, TOPIC_AUDIT)


def get_message_key(aggregate_id: str) -> bytes:
    """
    Get message key for Kafka partitioning.

    CRITICAL: Message key = aggregate_id ensures:
    - All events for same aggregate go to same partition
    - Events are ordered per aggregate

    Args:
        aggregate_id: UUID as string

    Returns:
        Key as bytes
    """
    return aggregate_id.encode("utf-8")


# =============================================================================
# TOPIC CONFIGURATION
# =============================================================================

# Topic configuration for Kafka admin
TOPIC_CONFIG = {
    TOPIC_DECISIONS: {
        "num_partitions": 12,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(7 * 24 * 60 * 60 * 1000),  # 7 days
            "cleanup.policy": "delete",
            "min.insync.replicas": "2",
        }
    },
    TOPIC_WORKFLOWS: {
        "num_partitions": 12,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(7 * 24 * 60 * 60 * 1000),  # 7 days
            "cleanup.policy": "delete",
            "min.insync.replicas": "2",
        }
    },
    TOPIC_AUDIT: {
        "num_partitions": 6,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(30 * 24 * 60 * 60 * 1000),  # 30 days
            "cleanup.policy": "delete",
            "min.insync.replicas": "2",
        }
    },
}


def get_all_topics() -> list:
    """Get list of all topic names"""
    return [TOPIC_DECISIONS, TOPIC_WORKFLOWS, TOPIC_AUDIT]
