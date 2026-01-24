"""
Decision Repository

Provides data access abstraction for Decision aggregate.
Per MANTRA-LAW-001 §10, stored decisions are immutable.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..domain.schema import Decision, GroupId
from ..domain.decision import StoredDecision, DecisionEvent


class DecisionRepository(ABC):
    """
    Abstract repository interface for Decision aggregate.

    Per MANTRA-L1-IMPL-DECISION-STORE-001:
    - Write-once semantics
    - Append-only storage
    - Immutability enforcement
    """

    @abstractmethod
    def save(self, stored_decision: StoredDecision) -> None:
        """
        Save a decision.

        Per MANTRA-LAW-001 §10:
        - MUST NOT modify existing decisions
        - MUST fail if decision_id already exists
        """
        pass

    @abstractmethod
    def find_by_id(self, decision_id: str) -> Optional[StoredDecision]:
        """Find a decision by its ID."""
        pass

    @abstractmethod
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find all decisions with pagination."""
        pass

    @abstractmethod
    def find_by_group(
        self,
        group_id: GroupId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find decisions by group."""
        pass

    # find_by_status: REMOVED per MANTRA-SPEC-001-AMENDMENT-001
    # Status field no longer exists - evolution via version + supersedes only

    @abstractmethod
    def count(self) -> int:
        """Count total decisions."""
        pass

    @abstractmethod
    def record_event(self, event: DecisionEvent) -> None:
        """Record a domain event for audit trail."""
        pass


class InMemoryDecisionRepository(DecisionRepository):
    """
    In-memory implementation for testing and development.

    NOTE: This is NOT suitable for production.
    Use PostgresDecisionRepository for production.
    """

    def __init__(self):
        self._decisions: dict[str, StoredDecision] = {}
        self._events: List[DecisionEvent] = []

    def save(self, stored_decision: StoredDecision) -> None:
        """
        Save a decision.

        Raises ValueError if decision already exists (immutability).
        """
        decision_id = stored_decision.decision.decision_id

        if decision_id in self._decisions:
            raise ValueError(
                f"Decision {decision_id} already exists. "
                "Per MANTRA-LAW-001 §10, stored decisions are immutable."
            )

        self._decisions[decision_id] = stored_decision

    def find_by_id(self, decision_id: str) -> Optional[StoredDecision]:
        """Find a decision by its ID."""
        return self._decisions.get(decision_id)

    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find all decisions with pagination."""
        decisions = list(self._decisions.values())
        return decisions[offset:offset + limit]

    def find_by_group(
        self,
        group_id: GroupId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find decisions by group."""
        filtered = [
            sd for sd in self._decisions.values()
            if sd.decision.group_id == group_id
        ]
        return filtered[offset:offset + limit]

    # find_by_status: REMOVED per MANTRA-SPEC-001-AMENDMENT-001

    def count(self) -> int:
        """Count total decisions."""
        return len(self._decisions)

    def record_event(self, event: DecisionEvent) -> None:
        """Record a domain event."""
        self._events.append(event)

    def get_events(self) -> List[DecisionEvent]:
        """Get all recorded events (for testing)."""
        return self._events.copy()

    def clear(self) -> None:
        """Clear all data (for testing)."""
        self._decisions.clear()
        self._events.clear()
