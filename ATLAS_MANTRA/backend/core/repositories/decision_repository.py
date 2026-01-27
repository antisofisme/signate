"""
Decision Repository

Provides data access abstraction for Decision aggregate.
Per MANTRA-LAW-001 §10, stored decisions are immutable.

Architecture Note:
    This ABC defines both sync and async methods. FastAPI routes MUST use
    async methods (_async suffix) to avoid blocking the event loop.
    Sync methods are provided for testing and non-async contexts.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..domain.schema import Decision, GroupId, FeatureId
from ..domain.decision import StoredDecision, DecisionEvent, AuditEntry, AuditEventType


class DecisionRepository(ABC):
    """
    Abstract repository interface for Decision aggregate.

    Per MANTRA-L1-IMPL-DECISION-STORE-001:
    - Write-once semantics
    - Append-only storage
    - Immutability enforcement

    IMPORTANT: FastAPI routes MUST use async methods (suffix _async).
    Sync methods may not work correctly in async contexts for DB implementations.
    """

    # =========================================================================
    # Sync Methods (for testing and non-async contexts)
    # WARNING: These may return None/[] in async contexts for DB implementations
    # =========================================================================

    @abstractmethod
    def save(self, stored_decision: StoredDecision) -> None:
        """
        Save a decision (sync version).

        Per MANTRA-LAW-001 §10:
        - MUST NOT modify existing decisions
        - MUST fail if decision_id already exists

        NOTE: Use save_async() in FastAPI routes.
        """
        pass

    @abstractmethod
    def find_by_id(self, decision_id: str) -> Optional[StoredDecision]:
        """Find a decision by its ID (sync version). Use find_by_id_async() in routes."""
        pass

    @abstractmethod
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find all decisions (sync version). Use find_all_async() in routes."""
        pass

    @abstractmethod
    def find_by_group(
        self,
        group_id: GroupId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find decisions by group (sync version). Use find_by_group_async() in routes."""
        pass

    # find_by_status: REMOVED per MANTRA-SPEC-001-AMENDMENT-001
    # Status field no longer exists - evolution via version + supersedes only

    @abstractmethod
    def count(self) -> int:
        """Count total decisions (sync version). Use count_async() in routes."""
        pass

    @abstractmethod
    def count_by_feature(self, feature_id: FeatureId) -> int:
        """
        Count decisions by feature (sync version).

        Used for generating decision_code sequence numbers.
        Returns the count of all decisions with the given feature_id.
        Use count_by_feature_async() in routes.
        """
        pass

    @abstractmethod
    def record_event(self, event: DecisionEvent) -> None:
        """Record a domain event (sync version). Use record_event_async() in routes."""
        pass

    @abstractmethod
    def record_audit(self, entry: AuditEntry) -> None:
        """
        Record an audit entry (sync version).

        Per MANTRA-LAW-001: All operations must be auditable.
        Use record_audit_async() in routes.
        """
        pass

    @abstractmethod
    def get_audit_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """
        Get audit entries (sync version).

        Returns entries ordered by timestamp descending (most recent first).
        Use get_audit_entries_async() in routes.
        """
        pass

    @abstractmethod
    def count_audit_entries(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Count audit entries (sync version). Use count_audit_entries_async() in routes."""
        pass

    @abstractmethod
    def find_supersedes_chain(self, decision_id: str) -> List[StoredDecision]:
        """
        Find the complete supersedes chain (sync version).

        Returns: List of decisions in chain order (oldest first).
        - If decision A supersedes B, and B supersedes C:
          Returns [C, B, A] (chain from oldest to newest)

        Use find_supersedes_chain_async() in routes.
        """
        pass

    # =========================================================================
    # Async Methods (REQUIRED for FastAPI routes)
    # These are the primary interface for database implementations
    # =========================================================================

    @abstractmethod
    async def save_async(self, stored_decision: StoredDecision) -> None:
        """
        Save a decision (async version - USE THIS IN ROUTES).

        Per MANTRA-LAW-001 §10:
        - MUST NOT modify existing decisions
        - MUST fail if decision_id already exists
        """
        pass

    @abstractmethod
    async def find_by_id_async(self, decision_id: str) -> Optional[StoredDecision]:
        """Find a decision by its ID (async version - USE THIS IN ROUTES)."""
        pass

    @abstractmethod
    async def find_all_async(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find all decisions with pagination (async version - USE THIS IN ROUTES)."""
        pass

    @abstractmethod
    async def find_by_group_async(
        self,
        group_id: GroupId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find decisions by group (async version - USE THIS IN ROUTES)."""
        pass

    @abstractmethod
    async def count_async(self) -> int:
        """Count total decisions (async version - USE THIS IN ROUTES)."""
        pass

    @abstractmethod
    async def count_by_feature_async(self, feature_id: FeatureId) -> int:
        """
        Count decisions by feature (async version - USE THIS IN ROUTES).

        Used for generating decision_code sequence numbers.
        """
        pass

    @abstractmethod
    async def record_event_async(self, event: DecisionEvent) -> None:
        """Record a domain event (async version - USE THIS IN ROUTES)."""
        pass

    @abstractmethod
    async def record_audit_async(self, entry: AuditEntry) -> None:
        """
        Record an audit entry (async version - USE THIS IN ROUTES).

        Per MANTRA-LAW-001: All operations must be auditable.
        """
        pass

    @abstractmethod
    async def get_audit_entries_async(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """
        Get audit entries (async version - USE THIS IN ROUTES).

        Returns entries ordered by timestamp descending (most recent first).
        """
        pass

    @abstractmethod
    async def count_audit_entries_async(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Count audit entries (async version - USE THIS IN ROUTES)."""
        pass

    @abstractmethod
    async def find_supersedes_chain_async(self, decision_id: str) -> List[StoredDecision]:
        """
        Find the complete supersedes chain (async version - USE THIS IN ROUTES).

        Returns: List of decisions in chain order (oldest first).
        """
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
        self._audit_entries: List[AuditEntry] = []

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

    def count_by_feature(self, feature_id: FeatureId) -> int:
        """Count decisions by feature for sequence generation."""
        return sum(
            1 for sd in self._decisions.values()
            if sd.decision.feature_id == feature_id
        )

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
        self._audit_entries.clear()

    # =========================================================================
    # Audit Trail Methods Implementation
    # =========================================================================

    def record_audit(self, entry: AuditEntry) -> None:
        """Record an audit entry."""
        self._audit_entries.append(entry)

    def get_audit_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """Get audit entries with optional filtering."""
        # Filter entries
        entries = self._audit_entries.copy()

        if decision_id:
            entries = [e for e in entries if e.decision_id == decision_id]

        if event_type:
            entries = [e for e in entries if e.event_type == event_type]

        if actor:
            entries = [e for e in entries if e.actor == actor]

        # Sort by timestamp descending (most recent first)
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return entries[offset:offset + limit]

    def count_audit_entries(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Count audit entries with optional filtering."""
        entries = self._audit_entries.copy()

        if decision_id:
            entries = [e for e in entries if e.decision_id == decision_id]

        if event_type:
            entries = [e for e in entries if e.event_type == event_type]

        if actor:
            entries = [e for e in entries if e.actor == actor]

        return len(entries)

    def find_supersedes_chain(self, decision_id: str) -> List[StoredDecision]:
        """
        Find the complete supersedes chain for a decision.

        Returns: List of decisions in chain order (oldest first).
        """
        chain = []
        current_id = decision_id

        # Build chain going backwards (to older versions)
        while current_id:
            stored = self._decisions.get(current_id)
            if not stored:
                break
            chain.append(stored)
            current_id = stored.decision.supersedes

        # Also find decisions that supersede the given decision
        # (newer versions of the decision)
        current_id = decision_id
        newer_versions = []

        # Find all decisions that supersede this one
        while True:
            found_newer = None
            for sd in self._decisions.values():
                if sd.decision.supersedes == current_id:
                    found_newer = sd
                    break

            if found_newer:
                newer_versions.append(found_newer)
                current_id = found_newer.decision.decision_id
            else:
                break

        # Combine: older first, then current, then newer
        # chain is [current, older, oldest...], so reverse it
        chain.reverse()
        # Now add newer versions
        chain.extend(newer_versions)

        return chain

    def get_all_audit_entries(self) -> List[AuditEntry]:
        """Get all audit entries (for testing)."""
        return self._audit_entries.copy()

    # =========================================================================
    # Async Methods (for FastAPI route compatibility)
    # These wrap the sync methods since in-memory operations are instant.
    # =========================================================================

    async def save_async(self, stored_decision: StoredDecision) -> None:
        """Async version of save."""
        self.save(stored_decision)

    async def find_by_id_async(self, decision_id: str) -> Optional[StoredDecision]:
        """Async version of find_by_id."""
        return self.find_by_id(decision_id)

    async def find_all_async(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Async version of find_all."""
        return self.find_all(limit, offset)

    async def find_by_group_async(
        self,
        group_id: GroupId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Async version of find_by_group."""
        return self.find_by_group(group_id, limit, offset)

    async def count_async(self) -> int:
        """Async version of count."""
        return self.count()

    async def count_by_feature_async(self, feature_id: FeatureId) -> int:
        """Async version of count_by_feature."""
        return self.count_by_feature(feature_id)

    async def record_event_async(self, event: DecisionEvent) -> None:
        """Async version of record_event."""
        self.record_event(event)

    async def record_audit_async(self, entry: AuditEntry) -> None:
        """Async version of record_audit."""
        self.record_audit(entry)

    async def get_audit_entries_async(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """Async version of get_audit_entries."""
        return self.get_audit_entries(limit, offset, decision_id, event_type, actor)

    async def count_audit_entries_async(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Async version of count_audit_entries."""
        return self.count_audit_entries(decision_id, event_type, actor)

    async def find_supersedes_chain_async(self, decision_id: str) -> List[StoredDecision]:
        """Async version of find_supersedes_chain."""
        return self.find_supersedes_chain(decision_id)
