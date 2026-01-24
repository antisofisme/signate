"""
Store Decision Use Case

Implements MANTRA-L1-IMPL-DECISION-STORE-001

Per the specification and Human Decisions, the Decision Store:
- PERSISTENCE ONLY
- Stores decisions as-is (subject only to DB constraints)
- Enforces write-once semantics
- Provides append-only storage
- Maintains audit trail

CRITICAL (Human Decision - Phase 2):
- Store service MUST NOT validate decisions
- Store service MUST NOT reject decisions based on validity
- Store service MUST NOT call validator internally
- Validation and storage are SEPARATE concerns
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

from ..domain.schema import Decision
from ..domain.decision import StoredDecision, DecisionEvent, DecisionEventType
from ..repositories.decision_repository import DecisionRepository


class StoreResult(str, Enum):
    """Storage operation result - TECHNICAL OUTCOMES ONLY"""
    STORED = "STORED"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    STORE_ERROR = "STORE_ERROR"


@dataclass
class StoreDecisionResult:
    """Result of store decision operation - TECHNICAL OUTCOMES ONLY"""
    result: StoreResult
    decision_id: Optional[str] = None
    stored_at: Optional[datetime] = None
    error_message: Optional[str] = None


class StoreDecisionUseCase:
    """
    Store Decision Use Case - PERSISTENCE ONLY

    Per MANTRA-L1-IMPL-DECISION-STORE-001:
    - Stores decisions as-is
    - Enforces write-once semantics
    - Provides audit trail

    Per MANTRA-LAW-001 §10:
    - Stored decisions MUST NOT be modified
    - Stored decisions MUST NOT be deleted

    Per Human Decision (Phase 2):
    - Store MUST NOT validate
    - Store MUST NOT reject based on validity
    - Store MUST NOT call validator
    """

    def __init__(self, repository: DecisionRepository):
        self.repository = repository

    def execute(
        self,
        decision: Decision,
        stored_by: str
    ) -> StoreDecisionResult:
        """
        Store a decision.

        Args:
            decision: The decision to store
            stored_by: Human identifier storing the decision

        Returns:
            StoreDecisionResult with TECHNICAL outcome only
        """
        # Step 1: Check if decision already exists (immutability constraint)
        existing = self.repository.find_by_id(decision.decision_id)
        if existing is not None:
            return StoreDecisionResult(
                result=StoreResult.ALREADY_EXISTS,
                decision_id=decision.decision_id,
                error_message="Decision already exists. Per MANTRA-LAW-001 §10, "
                             "stored decisions are immutable."
            )

        # Step 2: Store decision
        try:
            stored_at = datetime.utcnow()
            stored_decision = StoredDecision(
                decision=decision,
                stored_at=stored_at,
                stored_by=stored_by,
                storage_version=1
            )

            self.repository.save(stored_decision)

            # Emit storage event (for audit trail only)
            event = DecisionEvent(
                event_type=DecisionEventType.DECISION_STORED,
                decision_id=decision.decision_id,
                actor=stored_by,
                metadata={"storage_version": 1}
            )
            self.repository.record_event(event)

            return StoreDecisionResult(
                result=StoreResult.STORED,
                decision_id=decision.decision_id,
                stored_at=stored_at
            )

        except Exception as e:
            return StoreDecisionResult(
                result=StoreResult.STORE_ERROR,
                error_message=str(e)
            )


def store_decision(
    decision: Decision,
    stored_by: str,
    repository: DecisionRepository
) -> StoreDecisionResult:
    """
    Store a decision - PERSISTENCE ONLY.

    This is the main entry point for the Decision Store Service
    per MANTRA-L1-IMPL-DECISION-STORE-001.

    Per Human Decision (Phase 2):
    - Store DOES NOT validate
    - Store DOES NOT reject based on validity
    - Store returns technical outcomes only

    Args:
        decision: The decision to store
        stored_by: Human identifier storing the decision
        repository: Decision repository instance

    Returns:
        StoreDecisionResult with TECHNICAL outcome only
    """
    use_case = StoreDecisionUseCase(repository)
    return use_case.execute(decision, stored_by)
