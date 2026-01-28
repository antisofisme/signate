"""
Read Decision Use Case

Implements MANTRA-L1-IMPL-PUBLIC-READ-API-001

Per the specification and Human Decisions, the Public Read API:
- PURE DATA ACCESS ONLY
- Provides read-only access to stored decisions
- Has no modification capability
- Eventual consistency is acceptable

CRITICAL (Human Decision - Phase 3):
- Read API MUST NOT determine "current", "active", "valid", or "effective"
- Read API MUST NOT collapse versions or resolve supersedes
- Read API MUST NOT filter by lifecycle semantics
- Interpretation is the responsibility of the CONSUMER, not the system
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from ..domain.schema import Decision, DomainId, AspectId
from ..domain.decision import StoredDecision, DecisionEvent, DecisionEventType
from ..repositories.decision_repository import DecisionRepository


class ReadResult(str, Enum):
    """Read operation result"""
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"


@dataclass
class ReadDecisionResult:
    """Result of read decision operation"""
    result: ReadResult
    decision: Optional[Decision] = None
    stored_at: Optional[str] = None
    stored_by: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ListDecisionsResult:
    """Result of list decisions operation"""
    result: ReadResult
    decisions: List[Decision] = None
    total_count: int = 0
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.decisions is None:
            self.decisions = []


class ReadDecisionUseCase:
    """
    Read Decision Use Case

    Per MANTRA-L1-IMPL-PUBLIC-READ-API-001:
    - Read-only access to stored decisions
    - No modification capability
    - Eventual consistency acceptable

    Per MANTRA-LAW-001 §6.2, AI MAY:
    - Read decision records
    - Detect potential conflicts
    - Flag potential gaps
    - Generate advisory warnings
    - Produce analysis for human review
    """

    def __init__(self, repository: DecisionRepository):
        self.repository = repository

    def get_by_id(self, decision_id: str) -> ReadDecisionResult:
        """
        Get a decision by ID.

        Args:
            decision_id: UUID of the decision

        Returns:
            ReadDecisionResult with decision if found
        """
        try:
            stored = self.repository.find_by_id(decision_id)

            if stored is None:
                return ReadDecisionResult(
                    result=ReadResult.NOT_FOUND,
                    error_message=f"Decision {decision_id} not found"
                )

            # Record read event (for audit)
            event = DecisionEvent(
                event_type=DecisionEventType.DECISION_RETRIEVED,
                decision_id=decision_id,
                metadata={"access_type": "by_id"}
            )
            self.repository.record_event(event)

            return ReadDecisionResult(
                result=ReadResult.FOUND,
                decision=stored.decision,
                stored_at=stored.stored_at.isoformat(),
                stored_by=stored.stored_by
            )

        except Exception as e:
            return ReadDecisionResult(
                result=ReadResult.ERROR,
                error_message=str(e)
            )

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> ListDecisionsResult:
        """
        List all decisions with pagination.

        Args:
            limit: Maximum number of decisions to return
            offset: Number of decisions to skip

        Returns:
            ListDecisionsResult with list of decisions
        """
        try:
            stored_decisions = self.repository.find_all(limit=limit, offset=offset)
            total = self.repository.count()

            decisions = [sd.decision for sd in stored_decisions]

            return ListDecisionsResult(
                result=ReadResult.FOUND,
                decisions=decisions,
                total_count=total
            )

        except Exception as e:
            return ListDecisionsResult(
                result=ReadResult.ERROR,
                error_message=str(e)
            )

    def list_by_domain(
        self,
        domain_id: DomainId,
        limit: int = 100,
        offset: int = 0
    ) -> ListDecisionsResult:
        """
        List decisions by domain.

        Args:
            domain_id: Domain ID to filter by
            limit: Maximum number of decisions to return
            offset: Number of decisions to skip

        Returns:
            ListDecisionsResult with filtered decisions
        """
        try:
            stored_decisions = self.repository.find_by_domain(
                domain_id, limit=limit, offset=offset
            )

            decisions = [sd.decision for sd in stored_decisions]

            return ListDecisionsResult(
                result=ReadResult.FOUND,
                decisions=decisions,
                total_count=len(decisions)
            )

        except Exception as e:
            return ListDecisionsResult(
                result=ReadResult.ERROR,
                error_message=str(e)
            )

    def list_by_domain_aspect(
        self,
        domain_id: DomainId,
        aspect_id: AspectId
    ) -> ListDecisionsResult:
        """
        List ALL decisions for a specific domain/aspect combination.

        Per Human Decision (Phase 3):
        - Returns ALL matching records (no filtering)
        - Consumer interprets which is "current" or "active"

        Args:
            domain_id: Domain ID to filter by
            aspect_id: Aspect ID to filter by

        Returns:
            ListDecisionsResult with ALL matching decisions
        """
        try:
            stored_decisions = self.repository.find_by_domain(domain_id)

            # Structural filter only - by aspect_id
            decisions = [
                sd.decision for sd in stored_decisions
                if sd.decision.aspect_id == aspect_id
            ]

            return ListDecisionsResult(
                result=ReadResult.FOUND,
                decisions=decisions,
                total_count=len(decisions)
            )

        except Exception as e:
            return ListDecisionsResult(
                result=ReadResult.ERROR,
                error_message=str(e)
            )

    def group_all_by_domain_aspect(self) -> dict:
        """
        Group ALL decisions by domain/aspect - PURE DATA ACCESS.

        Per Human Decision (Phase 3):
        - Returns ALL decisions grouped structurally
        - NO filtering by status, active, valid, or any semantic criteria
        - Consumer interprets the data

        Returns:
            Dictionary with domain/aspect mapping of ALL decisions
        """
        grouped = {}

        for domain in DomainId:
            grouped[domain.value] = {}
            stored_decisions = self.repository.find_by_domain(domain)

            for sd in stored_decisions:
                aspect_key = sd.decision.aspect_id.value
                if aspect_key not in grouped[domain.value]:
                    grouped[domain.value][aspect_key] = []

                # Return ALL decisions, no filtering
                grouped[domain.value][aspect_key].append({
                    "decision_id": sd.decision.decision_id,
                    "statement": sd.decision.statement,
                    "scope": sd.decision.scope.value,
                    "blast_radius": sd.decision.blast_radius.value,
                    "version": sd.decision.version,
                    "supersedes": sd.decision.supersedes,
                    "created_at": sd.decision.created_at.isoformat() if sd.decision.created_at else None
                })

        return grouped


# ============================================================================
# Public API Functions
# ============================================================================

def get_decision(
    decision_id: str,
    repository: DecisionRepository
) -> ReadDecisionResult:
    """
    Get a decision by ID.

    This is a main entry point for the Public Read API
    per MANTRA-L1-IMPL-PUBLIC-READ-API-001.
    """
    use_case = ReadDecisionUseCase(repository)
    return use_case.get_by_id(decision_id)


def list_decisions(
    repository: DecisionRepository,
    limit: int = 100,
    offset: int = 0
) -> ListDecisionsResult:
    """
    List all decisions with pagination.

    This is a main entry point for the Public Read API
    per MANTRA-L1-IMPL-PUBLIC-READ-API-001.
    """
    use_case = ReadDecisionUseCase(repository)
    return use_case.list_all(limit=limit, offset=offset)


def group_decisions_by_domain_aspect(repository: DecisionRepository) -> dict:
    """
    Group ALL decisions by domain/aspect - PURE DATA ACCESS.

    Per Human Decision (Phase 3):
    - Returns ALL decisions grouped by structural criteria only
    - NO semantic filtering (active, valid, current)
    - Consumer interprets the data
    """
    use_case = ReadDecisionUseCase(repository)
    return use_case.group_all_by_domain_aspect()
