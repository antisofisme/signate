"""
Audit Log Use Case

Records and retrieves audit entries for all ARSAKA_MANTRA operations.
Per MANTRA-LAW-001: All operations must be auditable.

Tracks:
- DECISION_PROPOSED: Validation + preparation (before storage)
- DECISION_VALIDATED: Validation-only operations
- DECISION_STORED: Successful storage events
- DECISION_READ: Read access events
- DECISION_COMPARED: Comparison operations
- CHALLENGE_CREATED: Challenge/supersede operations
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum

from ..domain.decision import AuditEntry, AuditEventType
from ..repositories.decision_repository import DecisionRepository


class AuditResult(Enum):
    """Result of audit operations"""
    RECORDED = "RECORDED"
    RETRIEVED = "RETRIEVED"
    ERROR = "ERROR"


@dataclass
class RecordAuditResult:
    """Result of recording an audit entry"""
    result: AuditResult
    event_id: Optional[str] = None
    recorded_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ListAuditResult:
    """Result of listing audit entries"""
    result: AuditResult
    entries: List[AuditEntry] = None
    total_count: int = 0
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.entries is None:
            self.entries = []


class AuditLogUseCase:
    """
    Use case for audit log operations.

    Per MANTRA-LAW-001:
    - All operations must be auditable
    - Audit entries are append-only
    - Audit entries are immutable
    """

    def __init__(self, repository: DecisionRepository):
        self._repository = repository

    def record(
        self,
        event_type: AuditEventType,
        actor: str,
        actor_type: str = "human",
        decision_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> RecordAuditResult:
        """
        Record an audit entry.

        Args:
            event_type: Type of event being recorded
            actor: Identifier of the actor (human or ai)
            actor_type: "human" or "ai"
            decision_id: Optional decision ID being affected
            metadata: Additional context

        Returns:
            RecordAuditResult with event_id if successful
        """
        try:
            entry = AuditEntry(
                event_type=event_type,
                actor=actor,
                actor_type=actor_type,
                decision_id=decision_id,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
            )

            self._repository.record_audit(entry)

            return RecordAuditResult(
                result=AuditResult.RECORDED,
                event_id=entry.event_id,
                recorded_at=entry.timestamp,
            )

        except Exception as e:
            return RecordAuditResult(
                result=AuditResult.ERROR,
                error_message=str(e),
            )

    def list_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> ListAuditResult:
        """
        List audit entries with optional filtering.

        Args:
            limit: Maximum entries to return
            offset: Pagination offset
            decision_id: Filter by decision ID
            event_type: Filter by event type
            actor: Filter by actor

        Returns:
            ListAuditResult with entries and count
        """
        try:
            entries = self._repository.get_audit_entries(
                limit=limit,
                offset=offset,
                decision_id=decision_id,
                event_type=event_type,
                actor=actor,
            )

            total = self._repository.count_audit_entries(
                decision_id=decision_id,
                event_type=event_type,
                actor=actor,
            )

            return ListAuditResult(
                result=AuditResult.RETRIEVED,
                entries=entries,
                total_count=total,
            )

        except Exception as e:
            return ListAuditResult(
                result=AuditResult.ERROR,
                error_message=str(e),
            )


# =============================================================================
# Convenience Functions
# =============================================================================

def record_audit(
    event_type: AuditEventType,
    actor: str,
    repository: DecisionRepository,
    actor_type: str = "human",
    decision_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> RecordAuditResult:
    """
    Record an audit entry.

    Convenience function for use case execution.
    """
    use_case = AuditLogUseCase(repository)
    return use_case.record(
        event_type=event_type,
        actor=actor,
        actor_type=actor_type,
        decision_id=decision_id,
        metadata=metadata,
    )


def list_audit_entries(
    repository: DecisionRepository,
    limit: int = 100,
    offset: int = 0,
    decision_id: Optional[str] = None,
    event_type: Optional[AuditEventType] = None,
    actor: Optional[str] = None,
) -> ListAuditResult:
    """
    List audit entries.

    Convenience function for use case execution.
    """
    use_case = AuditLogUseCase(repository)
    return use_case.list_entries(
        limit=limit,
        offset=offset,
        decision_id=decision_id,
        event_type=event_type,
        actor=actor,
    )
