"""
Domain Value Objects for ATLAS_PUGUH Core Service

Value objects are immutable and represent domain concepts.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime
from uuid import UUID


class Outcome(str, Enum):
    """
    Decision outcome - LOCKED at creation time
    Source: INFRA-LAY3-002 §2.1
    """
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"

    def is_terminal(self) -> bool:
        """Check if outcome is terminal (no further action needed)"""
        return self in (Outcome.ALLOWED, Outcome.DENIED)

    def requires_workflow(self) -> bool:
        """Check if outcome requires approval workflow"""
        return self == Outcome.REQUIRE_APPROVAL


class WorkflowState(str, Enum):
    """
    Workflow state machine states
    Source: INFRA-LAY3-002 §3.1
    """
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELEGATED = "DELEGATED"
    ESCALATED = "ESCALATED"

    def is_terminal(self) -> bool:
        """Check if workflow state is terminal"""
        return self in (WorkflowState.APPROVED, WorkflowState.REJECTED)

    def can_transition_to(self, target: 'WorkflowState') -> bool:
        """
        Check if transition is allowed per state machine
        Source: INFRA-LAY3-002 §3.1
        """
        allowed_transitions = {
            WorkflowState.PENDING_APPROVAL: {
                WorkflowState.APPROVED,
                WorkflowState.REJECTED,
                WorkflowState.DELEGATED,
                WorkflowState.ESCALATED
            },
            WorkflowState.DELEGATED: {
                WorkflowState.PENDING_APPROVAL
            },
            WorkflowState.ESCALATED: {
                WorkflowState.PENDING_APPROVAL
            },
            # Terminal states cannot transition
            WorkflowState.APPROVED: set(),
            WorkflowState.REJECTED: set()
        }

        return target in allowed_transitions.get(self, set())


class WorkflowAction(str, Enum):
    """
    Workflow transition actions
    Source: INFRA-LAY3-002 §3.2
    """
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELEGATED = "DELEGATED"
    ESCALATED = "ESCALATED"


@dataclass(frozen=True)
class Context:
    """
    Decision context - immutable snapshot
    Source: INFRA-LAY3-002 §2.1

    Context is a flat dictionary of key-value pairs (no nesting allowed)
    """
    data: Dict[str, Any]

    def __post_init__(self):
        """Validate context structure"""
        if not isinstance(self.data, dict):
            raise ValueError("Context data must be a dictionary")

        # Ensure flat structure (no nested objects)
        for key, value in self.data.items():
            if isinstance(value, dict) or isinstance(value, list):
                raise ValueError(
                    f"Context must be flat (no nested objects). "
                    f"Field '{key}' contains nested structure"
                )

    def get(self, key: str, default=None) -> Any:
        """Get context value by key"""
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """Check if key exists in context"""
        return key in self.data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return dict(self.data)


@dataclass(frozen=True)
class TenantId:
    """
    Tenant identifier - ensures multi-tenancy isolation
    Source: INFRA-DEC-002 (Tenancy Model)
    """
    value: UUID

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class DecisionId:
    """Decision unique identifier"""
    value: UUID

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class WorkflowId:
    """Workflow unique identifier"""
    value: UUID

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class RuleId:
    """Rule unique identifier"""
    value: UUID

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class IdempotencyKey:
    """
    Idempotency key for deduplication
    Source: INFRA-LAY3-002 §2.2

    Format: Application-controlled, max 255 chars
    Recommended: "{operation}:{entity_type}:{entity_id}:{timestamp}"
    """
    value: str

    def __post_init__(self):
        """Validate idempotency key"""
        if not self.value:
            raise ValueError("Idempotency key cannot be empty")
        if len(self.value) > 255:
            raise ValueError("Idempotency key cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RuleVersion:
    """
    Rule version identifier
    Source: Architecture Layer 2.7 (Rule Versioning)

    Format: MAJOR.MINOR (identifier-only, NOT SemVer compatibility)
    Example: "1.0", "1.1", "2.0"
    """
    version: str

    def __post_init__(self):
        """Validate version format"""
        if not self.version:
            raise ValueError("Rule version cannot be empty")

        # Basic validation: should look like "MAJOR.MINOR"
        parts = self.version.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Rule version must be MAJOR.MINOR format, got: {self.version}"
            )

        try:
            int(parts[0])  # MAJOR
            int(parts[1])  # MINOR
        except ValueError:
            raise ValueError(
                f"Rule version components must be integers, got: {self.version}"
            )

    def __str__(self) -> str:
        return self.version


@dataclass(frozen=True)
class Metadata:
    """
    Decision/Workflow metadata
    Source: INFRA-LAY3-002 §2.1

    Contains: trace_id, requester_user_id, source, etc.
    """
    trace_id: UUID | None = None
    requester_user_id: UUID | None = None
    source: str | None = None
    additional_data: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence"""
        result = {}
        if self.trace_id:
            result['trace_id'] = str(self.trace_id)
        if self.requester_user_id:
            result['requester_user_id'] = str(self.requester_user_id)
        if self.source:
            result['source'] = self.source
        if self.additional_data:
            result.update(self.additional_data)
        return result
