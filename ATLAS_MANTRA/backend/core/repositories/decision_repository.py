"""
Decision Repository

Provides data access abstraction for Decision aggregate.
Per MANTRA-LAW-001 §10, stored decisions are immutable.

Architecture Note:
    This ABC defines both sync and async methods. FastAPI routes MUST use
    async methods (_async suffix) to avoid blocking the event loop.
    Sync methods are provided for testing and non-async contexts.

Deprecation Notice:
    Sync methods are DEPRECATED and will emit warnings when called.
    All new code should use async methods exclusively.
"""

import warnings
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from functools import wraps

from ..domain.schema import Decision, DomainId, AspectId
from ..domain.decision import StoredDecision, DecisionEvent, AuditEntry, AuditEventType


def deprecated_sync(async_method_name: str):
    """
    Decorator to mark sync methods as deprecated.

    Emits a DeprecationWarning when the method is called,
    directing users to the async version.

    Args:
        async_method_name: Name of the async method to use instead
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__}() is deprecated. "
                f"Use {async_method_name}() for async operations. "
                "Sync methods may not work correctly in async contexts.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


class DecisionRepository(ABC):
    """
    Abstract repository interface for Decision aggregate.

    Per MANTRA-L1-IMPL-DECISION-STORE-001:
    - Write-once semantics
    - Append-only storage
    - Immutability enforcement

    IMPORTANT: FastAPI routes MUST use async methods (suffix _async).
    Sync methods are DEPRECATED and may not work correctly in async contexts.

    Migration Guide:
        OLD (deprecated):
            repo.save(decision)
            result = repo.find_by_id(id)

        NEW (recommended):
            await repo.save_async(decision)
            result = await repo.find_by_id_async(id)
    """

    # =========================================================================
    # Sync Methods (DEPRECATED - for testing and non-async contexts only)
    # WARNING: These emit DeprecationWarning and may not work in async contexts
    # =========================================================================

    @abstractmethod
    def save(self, stored_decision: StoredDecision) -> None:
        """
        Save a decision (sync version).

        .. deprecated::
            Use :meth:`save_async` instead.

        Per MANTRA-LAW-001 §10:
        - MUST NOT modify existing decisions
        - MUST fail if decision_id already exists
        """
        pass

    @abstractmethod
    def find_by_id(self, decision_id: str) -> Optional[StoredDecision]:
        """
        Find a decision by its ID (sync version).

        .. deprecated::
            Use :meth:`find_by_id_async` instead.
        """
        pass

    @abstractmethod
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """
        Find all decisions (sync version).

        .. deprecated::
            Use :meth:`find_all_async` instead.
        """
        pass

    @abstractmethod
    def find_by_domain(
        self,
        domain_id: DomainId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """
        Find decisions by domain (sync version).

        .. deprecated::
            Use :meth:`find_by_domain_async` instead.
        """
        pass

    # find_by_status: REMOVED per MANTRA-SPEC-001-AMENDMENT-001
    # Status field no longer exists - evolution via version + supersedes only

    @abstractmethod
    def count(self) -> int:
        """
        Count total decisions (sync version).

        .. deprecated::
            Use :meth:`count_async` instead.
        """
        pass

    @abstractmethod
    def count_by_aspect(self, aspect_id: AspectId) -> int:
        """
        Count decisions by aspect (sync version).

        .. deprecated::
            Use :meth:`count_by_aspect_async` instead.

        Used for generating decision_code sequence numbers.
        Returns the count of all decisions with the given aspect_id.
        """
        pass

    @abstractmethod
    def record_event(self, event: DecisionEvent) -> None:
        """
        Record a domain event (sync version).

        .. deprecated::
            Use :meth:`record_event_async` instead.
        """
        pass

    @abstractmethod
    def record_audit(self, entry: AuditEntry) -> None:
        """
        Record an audit entry (sync version).

        .. deprecated::
            Use :meth:`record_audit_async` instead.

        Per MANTRA-LAW-001: All operations must be auditable.
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

        .. deprecated::
            Use :meth:`get_audit_entries_async` instead.

        Returns entries ordered by timestamp descending (most recent first).
        """
        pass

    @abstractmethod
    def count_audit_entries(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """
        Count audit entries (sync version).

        .. deprecated::
            Use :meth:`count_audit_entries_async` instead.
        """
        pass

    @abstractmethod
    def find_supersedes_chain(self, decision_id: str) -> List[StoredDecision]:
        """
        Find the complete supersedes chain (sync version).

        .. deprecated::
            Use :meth:`find_supersedes_chain_async` instead.

        Returns: List of decisions in chain order (oldest first).
        - If decision A supersedes B, and B supersedes C:
          Returns [C, B, A] (chain from oldest to newest)
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
    async def find_by_domain_async(
        self,
        domain_id: DomainId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find decisions by domain (async version - USE THIS IN ROUTES)."""
        pass

    @abstractmethod
    async def count_async(self) -> int:
        """Count total decisions (async version - USE THIS IN ROUTES)."""
        pass

    @abstractmethod
    async def count_by_aspect_async(self, aspect_id: AspectId) -> int:
        """
        Count decisions by aspect (async version - USE THIS IN ROUTES).

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

    Sync methods emit DeprecationWarning to encourage async usage.
    """

    def __init__(self):
        self._decisions: dict[str, StoredDecision] = {}
        self._events: List[DecisionEvent] = []
        self._audit_entries: List[AuditEntry] = []

    @deprecated_sync("save_async")
    def save(self, stored_decision: StoredDecision) -> None:
        """
        Save a decision (deprecated - use save_async).

        Raises ValueError if decision already exists (immutability).
        """
        self._save_impl(stored_decision)

    def _save_impl(self, stored_decision: StoredDecision) -> None:
        """Internal save implementation (no deprecation warning)."""
        decision_id = stored_decision.decision.decision_id

        if decision_id in self._decisions:
            raise ValueError(
                f"Decision {decision_id} already exists. "
                "Per MANTRA-LAW-001 §10, stored decisions are immutable."
            )

        self._decisions[decision_id] = stored_decision

    @deprecated_sync("find_by_id_async")
    def find_by_id(self, decision_id: str) -> Optional[StoredDecision]:
        """Find a decision by its ID (deprecated - use find_by_id_async)."""
        return self._decisions.get(decision_id)

    @deprecated_sync("find_all_async")
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find all decisions with pagination (deprecated - use find_all_async)."""
        decisions = list(self._decisions.values())
        return decisions[offset:offset + limit]

    @deprecated_sync("find_by_domain_async")
    def find_by_domain(
        self,
        domain_id: DomainId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find decisions by domain (deprecated - use find_by_domain_async)."""
        filtered = [
            sd for sd in self._decisions.values()
            if sd.decision.domain_id == domain_id
        ]
        return filtered[offset:offset + limit]

    # find_by_status: REMOVED per MANTRA-SPEC-001-AMENDMENT-001

    @deprecated_sync("count_async")
    def count(self) -> int:
        """Count total decisions (deprecated - use count_async)."""
        return len(self._decisions)

    @deprecated_sync("count_by_aspect_async")
    def count_by_aspect(self, aspect_id: AspectId) -> int:
        """Count decisions by aspect (deprecated - use count_by_aspect_async)."""
        return sum(
            1 for sd in self._decisions.values()
            if sd.decision.aspect_id == aspect_id
        )

    @deprecated_sync("record_event_async")
    def record_event(self, event: DecisionEvent) -> None:
        """Record a domain event (deprecated - use record_event_async)."""
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

    @deprecated_sync("record_audit_async")
    def record_audit(self, entry: AuditEntry) -> None:
        """Record an audit entry (deprecated - use record_audit_async)."""
        self._record_audit_impl(entry)

    def _record_audit_impl(self, entry: AuditEntry) -> None:
        """Internal record_audit implementation."""
        self._audit_entries.append(entry)

    @deprecated_sync("get_audit_entries_async")
    def get_audit_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """Get audit entries (deprecated - use get_audit_entries_async)."""
        return self._get_audit_entries_impl(limit, offset, decision_id, event_type, actor)

    def _get_audit_entries_impl(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """Internal get_audit_entries implementation."""
        entries = self._audit_entries.copy()

        if decision_id:
            entries = [e for e in entries if e.decision_id == decision_id]

        if event_type:
            entries = [e for e in entries if e.event_type == event_type]

        if actor:
            entries = [e for e in entries if e.actor == actor]

        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[offset:offset + limit]

    @deprecated_sync("count_audit_entries_async")
    def count_audit_entries(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Count audit entries (deprecated - use count_audit_entries_async)."""
        return self._count_audit_entries_impl(decision_id, event_type, actor)

    def _count_audit_entries_impl(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Internal count_audit_entries implementation."""
        entries = self._audit_entries.copy()

        if decision_id:
            entries = [e for e in entries if e.decision_id == decision_id]

        if event_type:
            entries = [e for e in entries if e.event_type == event_type]

        if actor:
            entries = [e for e in entries if e.actor == actor]

        return len(entries)

    @deprecated_sync("find_supersedes_chain_async")
    def find_supersedes_chain(self, decision_id: str) -> List[StoredDecision]:
        """Find supersedes chain (deprecated - use find_supersedes_chain_async)."""
        return self._find_supersedes_chain_impl(decision_id)

    def _find_supersedes_chain_impl(self, decision_id: str) -> List[StoredDecision]:
        """Internal find_supersedes_chain implementation."""
        chain = []
        current_id = decision_id

        # Build chain going backwards (to older versions)
        while current_id:
            stored = self._decisions.get(current_id)
            if not stored:
                break
            chain.append(stored)
            current_id = stored.decision.supersedes

        # Find decisions that supersede the given decision (newer versions)
        current_id = decision_id
        newer_versions = []

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
        chain.reverse()
        chain.extend(newer_versions)

        return chain

    def get_all_audit_entries(self) -> List[AuditEntry]:
        """Get all audit entries (for testing)."""
        return self._audit_entries.copy()

    # =========================================================================
    # Async Methods (RECOMMENDED - use these in FastAPI routes)
    # These use internal implementations to avoid deprecation warnings.
    # =========================================================================

    async def save_async(self, stored_decision: StoredDecision) -> None:
        """Save a decision (async - RECOMMENDED)."""
        self._save_impl(stored_decision)

    async def find_by_id_async(self, decision_id: str) -> Optional[StoredDecision]:
        """Find a decision by ID (async - RECOMMENDED)."""
        return self._decisions.get(decision_id)

    async def find_all_async(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find all decisions (async - RECOMMENDED)."""
        decisions = list(self._decisions.values())
        return decisions[offset:offset + limit]

    async def find_by_domain_async(
        self,
        domain_id: DomainId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find decisions by domain (async - RECOMMENDED)."""
        filtered = [
            sd for sd in self._decisions.values()
            if sd.decision.domain_id == domain_id
        ]
        return filtered[offset:offset + limit]

    async def count_async(self) -> int:
        """Count total decisions (async - RECOMMENDED)."""
        return len(self._decisions)

    async def count_by_aspect_async(self, aspect_id: AspectId) -> int:
        """Count decisions by aspect (async - RECOMMENDED)."""
        return sum(
            1 for sd in self._decisions.values()
            if sd.decision.aspect_id == aspect_id
        )

    async def record_event_async(self, event: DecisionEvent) -> None:
        """Record a domain event (async - RECOMMENDED)."""
        self._events.append(event)

    async def record_audit_async(self, entry: AuditEntry) -> None:
        """Record an audit entry (async - RECOMMENDED)."""
        self._record_audit_impl(entry)

    async def get_audit_entries_async(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """Get audit entries (async - RECOMMENDED)."""
        return self._get_audit_entries_impl(limit, offset, decision_id, event_type, actor)

    async def count_audit_entries_async(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Count audit entries (async - RECOMMENDED)."""
        return self._count_audit_entries_impl(decision_id, event_type, actor)

    async def find_supersedes_chain_async(self, decision_id: str) -> List[StoredDecision]:
        """Find supersedes chain (async - RECOMMENDED)."""
        return self._find_supersedes_chain_impl(decision_id)
