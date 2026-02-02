"""
Event Schemas - Schema-First, Versioned

CRITICAL:
- Schema version MUST be included in every event
- Breaking changes require new schema version
- Old consumers MUST handle old schema versions

Source: Phase 3 Requirements - Event Bus Infrastructure
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, List
from uuid import UUID
import json


# =============================================================================
# SCHEMA VERSIONING
# =============================================================================

# Schema versions: {event_type: current_version}
SCHEMA_REGISTRY: Dict[str, str] = {
    # Decision events
    "decision.created": "1.0",
    "decision.allowed": "1.0",
    "decision.denied": "1.0",
    "decision.requires_approval": "1.0",
    # Workflow events
    "workflow.created": "1.0",
    "workflow.pending_approval": "1.0",
    "workflow.approved": "1.0",
    "workflow.rejected": "1.0",
    "workflow.delegated": "1.0",
    "workflow.escalated": "1.0",
    "workflow.completed": "1.0",
}


def get_schema_version(event_type: str) -> str:
    """Get current schema version for event type"""
    return SCHEMA_REGISTRY.get(event_type, "1.0")


# =============================================================================
# EVENT ENVELOPE (Wire Format)
# =============================================================================

@dataclass(frozen=True)
class EventEnvelope:
    """
    Standard envelope for all events on the bus.

    CRITICAL: This is the WIRE FORMAT. All events are wrapped in this envelope.

    Source: Phase 3 - Event Schema & Versioning
    """
    # Identity
    event_id: str  # UUID as string
    event_type: str
    schema_version: str

    # Aggregate reference
    aggregate_id: str  # UUID as string (message key for Kafka)
    aggregate_type: str  # "decision" or "workflow"

    # Multi-tenancy
    tenant_id: str  # UUID as string

    # Timestamps
    occurred_at: str  # ISO8601
    recorded_at: str  # ISO8601
    published_at: str  # ISO8601

    # Tracing
    trace_id: Optional[str] = None
    caused_by_user_id: Optional[str] = None

    # Payload (event-specific data)
    payload: Dict[str, Any] = field(default_factory=dict)

    # Source
    source: str = "core"

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "schema_version": self.schema_version,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "tenant_id": self.tenant_id,
            "occurred_at": self.occurred_at,
            "recorded_at": self.recorded_at,
            "published_at": self.published_at,
            "trace_id": self.trace_id,
            "caused_by_user_id": self.caused_by_user_id,
            "payload": self.payload,
            "source": self.source,
        }, default=str)

    def to_bytes(self) -> bytes:
        """Serialize to bytes (UTF-8 encoded JSON)"""
        return self.to_json().encode("utf-8")

    @classmethod
    def from_json(cls, json_str: str) -> "EventEnvelope":
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            schema_version=data["schema_version"],
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            tenant_id=data["tenant_id"],
            occurred_at=data["occurred_at"],
            recorded_at=data["recorded_at"],
            published_at=data["published_at"],
            trace_id=data.get("trace_id"),
            caused_by_user_id=data.get("caused_by_user_id"),
            payload=data.get("payload", {}),
            source=data.get("source", "core"),
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "EventEnvelope":
        """Deserialize from bytes"""
        return cls.from_json(data.decode("utf-8"))


# =============================================================================
# EVENT SCHEMA DEFINITIONS (Documentation)
# =============================================================================

@dataclass(frozen=True)
class EventSchema:
    """
    Schema definition for documentation and validation.

    CRITICAL: This is for DOCUMENTATION only.
    Actual validation is done by consumers based on schema_version.
    """
    event_type: str
    schema_version: str
    description: str
    payload_fields: Dict[str, str]  # field_name -> description
    required_fields: List[str]

    def validate_payload(self, payload: Dict[str, Any]) -> List[str]:
        """
        Validate payload against schema.
        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Check required fields
        for field in self.required_fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")

        return errors


# Decision event schemas
DECISION_CREATED_SCHEMA = EventSchema(
    event_type="decision.created",
    schema_version="1.0",
    description="Emitted when a new decision is created",
    payload_fields={
        "decision_id": "UUID of the decision",
        "tenant_id": "UUID of the tenant",
        "decision_type": "Type of decision (e.g., purchase_order.approval)",
        "outcome": "Decision outcome: ALLOWED, DENIED, or REQUIRE_APPROVAL",
        "rule_matched_id": "UUID of the matched rule (nullable)",
        "rule_version": "Version of the matched rule (nullable)",
        "context_summary": "Sanitized context summary (not full context)",
        "latency_ms": "Decision latency in milliseconds",
    },
    required_fields=["decision_id", "tenant_id", "decision_type", "outcome"],
)

# Workflow event schemas
WORKFLOW_APPROVED_SCHEMA = EventSchema(
    event_type="workflow.approved",
    schema_version="1.0",
    description="Emitted when a workflow is approved",
    payload_fields={
        "workflow_id": "UUID of the workflow",
        "decision_id": "UUID of the parent decision",
        "tenant_id": "UUID of the tenant",
        "approver_role": "Role of the approver",
        "acted_by_user_id": "UUID of the user who approved (nullable)",
        "comment": "Approval comment (nullable)",
        "approved_at": "Timestamp of approval",
    },
    required_fields=["workflow_id", "decision_id", "tenant_id", "approver_role"],
)

WORKFLOW_REJECTED_SCHEMA = EventSchema(
    event_type="workflow.rejected",
    schema_version="1.0",
    description="Emitted when a workflow is rejected",
    payload_fields={
        "workflow_id": "UUID of the workflow",
        "decision_id": "UUID of the parent decision",
        "tenant_id": "UUID of the tenant",
        "approver_role": "Role of the approver",
        "acted_by_user_id": "UUID of the user who rejected (nullable)",
        "reason": "Rejection reason (nullable)",
        "rejected_at": "Timestamp of rejection",
    },
    required_fields=["workflow_id", "decision_id", "tenant_id", "approver_role"],
)


# Schema lookup
EVENT_SCHEMAS: Dict[str, EventSchema] = {
    "decision.created": DECISION_CREATED_SCHEMA,
    "workflow.approved": WORKFLOW_APPROVED_SCHEMA,
    "workflow.rejected": WORKFLOW_REJECTED_SCHEMA,
}


def get_event_schema(event_type: str) -> Optional[EventSchema]:
    """Get schema for event type"""
    return EVENT_SCHEMAS.get(event_type)
