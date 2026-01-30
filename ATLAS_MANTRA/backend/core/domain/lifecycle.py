"""
MANTRA Lifecycle Management

Tracks decision lifecycle status WITHOUT violating decision immutability.
Per MANTRA-LAW-001 §2.3: Decisions are append-only, no UPDATE/DELETE.

LIFECYCLE STATES:
- DRAFT:      Initial state, being authored
- REVIEW:     Under review, awaiting approval
- APPROVED:   Active and enforceable
- DEPRECATED: No longer recommended, superseded or outdated

STATE TRANSITIONS:
    DRAFT → REVIEW → APPROVED → DEPRECATED
              ↓           ↑
              └─(reject)──┘ (back to DRAFT for revision)

IMMUTABILITY COMPLIANCE:
- Decision content is NEVER modified
- Lifecycle changes are stored as EVENTS (append-only)
- Current status is COMPUTED from latest event
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


class LifecycleStatus(str, Enum):
    """Decision lifecycle status."""
    DRAFT = "DRAFT"           # Being authored
    REVIEW = "REVIEW"         # Under review
    APPROVED = "APPROVED"     # Active and enforceable
    DEPRECATED = "DEPRECATED" # No longer recommended


# Valid state transitions
VALID_TRANSITIONS: Dict[LifecycleStatus, List[LifecycleStatus]] = {
    LifecycleStatus.DRAFT: [LifecycleStatus.REVIEW],
    LifecycleStatus.REVIEW: [LifecycleStatus.APPROVED, LifecycleStatus.DRAFT],
    LifecycleStatus.APPROVED: [LifecycleStatus.DEPRECATED],
    LifecycleStatus.DEPRECATED: [],  # Terminal state
}


class TransitionReason(str, Enum):
    """Standard reasons for lifecycle transitions."""
    # DRAFT → REVIEW
    READY_FOR_REVIEW = "READY_FOR_REVIEW"

    # REVIEW → APPROVED
    REVIEW_PASSED = "REVIEW_PASSED"
    GATE_VALIDATION_PASSED = "GATE_VALIDATION_PASSED"

    # REVIEW → DRAFT
    REVIEW_REJECTED = "REVIEW_REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"

    # APPROVED → DEPRECATED
    SUPERSEDED = "SUPERSEDED"
    OBSOLETE = "OBSOLETE"
    SECURITY_ISSUE = "SECURITY_ISSUE"

    # Generic
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    OTHER = "OTHER"


@dataclass
class LifecycleEvent:
    """
    Immutable record of a lifecycle state change.

    These events form an append-only audit trail.
    The current status is computed from the latest event.
    """
    event_id: str
    decision_id: str
    status: LifecycleStatus
    previous_status: Optional[LifecycleStatus]
    changed_by: str  # Human who made the change
    changed_at: datetime
    reason: TransitionReason
    reason_detail: Optional[str] = None  # Free-form explanation

    # Gate validation context (if transition triggered by validation)
    gate_result_id: Optional[str] = None

    # Metadata
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None

    def __post_init__(self):
        """Validate the event."""
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.changed_at:
            self.changed_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "decision_id": self.decision_id,
            "status": self.status.value,
            "previous_status": self.previous_status.value if self.previous_status else None,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat(),
            "reason": self.reason.value,
            "reason_detail": self.reason_detail,
            "gate_result_id": self.gate_result_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifecycleEvent":
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            decision_id=data["decision_id"],
            status=LifecycleStatus(data["status"]),
            previous_status=LifecycleStatus(data["previous_status"]) if data.get("previous_status") else None,
            changed_by=data["changed_by"],
            changed_at=datetime.fromisoformat(data["changed_at"]) if isinstance(data["changed_at"], str) else data["changed_at"],
            reason=TransitionReason(data.get("reason", "OTHER")),
            reason_detail=data.get("reason_detail"),
            gate_result_id=data.get("gate_result_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
        )


@dataclass
class LifecycleState:
    """
    Computed current lifecycle state for a decision.

    This is NOT stored - it's computed from the event history.
    """
    decision_id: str
    current_status: LifecycleStatus
    last_changed_at: datetime
    last_changed_by: str
    event_count: int

    # Computed flags
    is_editable: bool = field(init=False)
    is_enforceable: bool = field(init=False)
    can_transition_to: List[LifecycleStatus] = field(init=False)

    def __post_init__(self):
        """Compute derived fields."""
        self.is_editable = self.current_status == LifecycleStatus.DRAFT
        self.is_enforceable = self.current_status == LifecycleStatus.APPROVED
        self.can_transition_to = VALID_TRANSITIONS.get(self.current_status, [])


class LifecycleError(Exception):
    """Base exception for lifecycle operations."""
    pass


class InvalidTransitionError(LifecycleError):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, current: LifecycleStatus, target: LifecycleStatus):
        self.current = current
        self.target = target
        valid = VALID_TRANSITIONS.get(current, [])
        super().__init__(
            f"Invalid transition: {current.value} → {target.value}. "
            f"Valid transitions from {current.value}: {[s.value for s in valid]}"
        )


class LifecycleManager:
    """
    Manages decision lifecycle state transitions.

    This class enforces valid transitions and creates audit events.
    """

    def __init__(self):
        self._events: Dict[str, List[LifecycleEvent]] = {}  # decision_id → events

    def get_current_state(self, decision_id: str) -> Optional[LifecycleState]:
        """
        Get current lifecycle state for a decision.

        Returns None if no events exist (decision not yet in lifecycle).
        """
        events = self._events.get(decision_id, [])
        if not events:
            return None

        # Latest event determines current state
        latest = events[-1]

        return LifecycleState(
            decision_id=decision_id,
            current_status=latest.status,
            last_changed_at=latest.changed_at,
            last_changed_by=latest.changed_by,
            event_count=len(events),
        )

    def get_history(self, decision_id: str) -> List[LifecycleEvent]:
        """Get full lifecycle history for a decision."""
        return self._events.get(decision_id, []).copy()

    def initialize(
        self,
        decision_id: str,
        created_by: str,
        initial_status: LifecycleStatus = LifecycleStatus.DRAFT,
    ) -> LifecycleEvent:
        """
        Initialize lifecycle for a new decision.

        Call this when a decision is first created.
        """
        if decision_id in self._events:
            raise LifecycleError(f"Decision {decision_id} already has lifecycle events")

        event = LifecycleEvent(
            event_id=str(uuid.uuid4()),
            decision_id=decision_id,
            status=initial_status,
            previous_status=None,
            changed_by=created_by,
            changed_at=datetime.now(timezone.utc),
            reason=TransitionReason.OTHER,
            reason_detail="Initial creation",
        )

        self._events[decision_id] = [event]
        return event

    def transition(
        self,
        decision_id: str,
        target_status: LifecycleStatus,
        changed_by: str,
        reason: TransitionReason,
        reason_detail: Optional[str] = None,
        gate_result_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LifecycleEvent:
        """
        Transition a decision to a new lifecycle state.

        Args:
            decision_id: The decision to transition
            target_status: The target state
            changed_by: Human making the change (REQUIRED per LAW §6)
            reason: Standard reason for the transition
            reason_detail: Optional detailed explanation
            gate_result_id: If transition triggered by gate validation
            client_ip: For audit trail
            user_agent: For audit trail

        Returns:
            The created LifecycleEvent

        Raises:
            InvalidTransitionError: If transition is not valid
            LifecycleError: If decision has no lifecycle history
        """
        current_state = self.get_current_state(decision_id)

        if current_state is None:
            raise LifecycleError(
                f"Decision {decision_id} has no lifecycle history. "
                f"Call initialize() first."
            )

        current_status = current_state.current_status

        # Validate transition
        if target_status not in VALID_TRANSITIONS.get(current_status, []):
            raise InvalidTransitionError(current_status, target_status)

        # Create event
        event = LifecycleEvent(
            event_id=str(uuid.uuid4()),
            decision_id=decision_id,
            status=target_status,
            previous_status=current_status,
            changed_by=changed_by,
            changed_at=datetime.now(timezone.utc),
            reason=reason,
            reason_detail=reason_detail,
            gate_result_id=gate_result_id,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        self._events[decision_id].append(event)
        return event

    def submit_for_review(
        self,
        decision_id: str,
        submitted_by: str,
        detail: Optional[str] = None,
    ) -> LifecycleEvent:
        """Convenience: DRAFT → REVIEW."""
        return self.transition(
            decision_id=decision_id,
            target_status=LifecycleStatus.REVIEW,
            changed_by=submitted_by,
            reason=TransitionReason.READY_FOR_REVIEW,
            reason_detail=detail,
        )

    def approve(
        self,
        decision_id: str,
        approved_by: str,
        gate_result_id: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> LifecycleEvent:
        """Convenience: REVIEW → APPROVED."""
        return self.transition(
            decision_id=decision_id,
            target_status=LifecycleStatus.APPROVED,
            changed_by=approved_by,
            reason=TransitionReason.GATE_VALIDATION_PASSED,
            reason_detail=detail,
            gate_result_id=gate_result_id,
        )

    def reject(
        self,
        decision_id: str,
        rejected_by: str,
        detail: str,
    ) -> LifecycleEvent:
        """Convenience: REVIEW → DRAFT (for revision)."""
        return self.transition(
            decision_id=decision_id,
            target_status=LifecycleStatus.DRAFT,
            changed_by=rejected_by,
            reason=TransitionReason.REVIEW_REJECTED,
            reason_detail=detail,
        )

    def deprecate(
        self,
        decision_id: str,
        deprecated_by: str,
        reason: TransitionReason = TransitionReason.OBSOLETE,
        detail: Optional[str] = None,
    ) -> LifecycleEvent:
        """Convenience: APPROVED → DEPRECATED."""
        return self.transition(
            decision_id=decision_id,
            target_status=LifecycleStatus.DEPRECATED,
            changed_by=deprecated_by,
            reason=reason,
            reason_detail=detail,
        )

    def load_events(self, events: List[LifecycleEvent]):
        """
        Load events from storage (e.g., database).

        Used to hydrate the manager from persistent storage.
        """
        for event in events:
            if event.decision_id not in self._events:
                self._events[event.decision_id] = []
            self._events[event.decision_id].append(event)

        # Sort each decision's events by timestamp
        for decision_id in self._events:
            self._events[decision_id].sort(key=lambda e: e.changed_at)

    def get_decisions_by_status(
        self,
        status: LifecycleStatus
    ) -> List[str]:
        """Get all decision IDs currently in a given status."""
        result = []
        for decision_id in self._events:
            state = self.get_current_state(decision_id)
            if state and state.current_status == status:
                result.append(decision_id)
        return result

    def get_pending_reviews(self) -> List[str]:
        """Get all decisions awaiting review."""
        return self.get_decisions_by_status(LifecycleStatus.REVIEW)

    def get_active_decisions(self) -> List[str]:
        """Get all approved (active) decisions."""
        return self.get_decisions_by_status(LifecycleStatus.APPROVED)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "LifecycleStatus",
    "LifecycleEvent",
    "LifecycleState",
    "LifecycleManager",
    "LifecycleError",
    "InvalidTransitionError",
    "TransitionReason",
    "VALID_TRANSITIONS",
]
