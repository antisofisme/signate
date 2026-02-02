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
from typing import Optional, List
from enum import Enum

from ..domain.schema import Decision, generate_decision_code
from ..domain.decision import (
    StoredDecision,
    DecisionEvent,
    DecisionEventType,
    AuditEntry,
    AuditEventType,
    StoredMetadata,
)
from ..repositories.decision_repository import DecisionRepository


class StoreResult(str, Enum):
    """Storage operation result - TECHNICAL OUTCOMES ONLY"""
    STORED = "STORED"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    STORE_ERROR = "STORE_ERROR"
    INVALID_SUPERSEDES = "INVALID_SUPERSEDES"  # Supersedes target not found or circular


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

    Data Integrity (Phase 5):
    - Store MUST validate supersedes chain integrity
    - Prevents orphaned pointers and circular references
    """

    def __init__(self, repository: DecisionRepository):
        self.repository = repository

    def _validate_supersedes_chain(self, decision: Decision) -> List[str]:
        """
        Validate supersedes pointer is valid.

        Checks:
        1. Target exists (prevents orphaned pointers)
        2. No circular reference (prevents infinite loops)
        3. No multiple decisions superseding same ID (ambiguous current version)

        Args:
            decision: The decision to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if decision.supersedes:
            # Check 1: Target exists
            target = self.repository.find_by_id(decision.supersedes)
            if not target:
                errors.append(
                    f"Supersedes target '{decision.supersedes}' not found. "
                    "Cannot supersede a non-existent decision."
                )
                return errors  # Early return - no need to check further

            # Check 2: No circular reference
            # Traverse the chain to see if we'd create a cycle
            chain = self.repository.find_supersedes_chain(decision.supersedes)
            chain_ids = {sd.decision.decision_id for sd in chain}
            if decision.decision_id in chain_ids:
                errors.append(
                    f"Circular supersedes chain detected. "
                    f"Decision '{decision.decision_id}' already exists in the chain."
                )

            # Check 3: No multiple decisions superseding same target
            # (prevent ambiguous "current" version)
            all_decisions = self.repository.find_all(limit=10000, offset=0)
            superseding_same = [
                sd for sd in all_decisions
                if sd.decision.supersedes == decision.supersedes
                and sd.decision.decision_id != decision.decision_id
            ]
            if superseding_same:
                existing_ids = [sd.decision.decision_id for sd in superseding_same]
                errors.append(
                    f"Multiple decisions cannot supersede the same target. "
                    f"Decision(s) {existing_ids} already supersede '{decision.supersedes}'."
                )

        return errors

    def execute(
        self,
        decision: Decision,
        stored_by: str
    ) -> StoreDecisionResult:
        """
        Store a decision (synchronous version - for non-async contexts).

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

        # Step 2: Validate supersedes chain (data integrity)
        supersedes_errors = self._validate_supersedes_chain(decision)
        if supersedes_errors:
            return StoreDecisionResult(
                result=StoreResult.INVALID_SUPERSEDES,
                decision_id=decision.decision_id,
                error_message=" | ".join(supersedes_errors)
            )

        # Step 3: Generate decision_code if not already set
        if not decision.decision_code:
            # Get sequence number for this aspect (1-based)
            sequence = self.repository.count_by_aspect(decision.aspect_id) + 1
            decision.decision_code = generate_decision_code(
                domain_id=decision.domain_id,
                aspect_id=decision.aspect_id,
                sequence=sequence,
                version=decision.version
            )

        # Step 4: Store decision
        try:
            stored_at = datetime.utcnow()
            stored_decision = StoredDecision(
                decision=decision,
                stored_at=stored_at,
                stored_by=stored_by,
                storage_version=1
            )

            self.repository.save(stored_decision)

            # Emit storage event (for legacy audit trail)
            event = DecisionEvent(
                event_type=DecisionEventType.DECISION_STORED,
                decision_id=decision.decision_id,
                actor=stored_by,
                metadata={"storage_version": 1}
            )
            self.repository.record_event(event)

            # Record audit entry (command-style API audit) - using typed metadata
            stored_metadata = StoredMetadata(
                storage_version=1,
                supersedes=decision.supersedes,
                version=decision.version,
            )
            audit_entry = AuditEntry(
                event_type=AuditEventType.DECISION_STORED,
                actor=stored_by,
                actor_type="human",
                decision_id=decision.decision_id,
                metadata=stored_metadata.to_dict()
            )
            self.repository.record_audit(audit_entry)

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

    async def execute_async(
        self,
        decision: Decision,
        stored_by: str
    ) -> StoreDecisionResult:
        """
        Store a decision (async version - for FastAPI routes).

        Args:
            decision: The decision to store
            stored_by: Human identifier storing the decision

        Returns:
            StoreDecisionResult with TECHNICAL outcome only
        """
        # Step 1: Check if decision already exists (immutability constraint)
        existing = await self.repository.find_by_id_async(decision.decision_id)
        if existing is not None:
            return StoreDecisionResult(
                result=StoreResult.ALREADY_EXISTS,
                decision_id=decision.decision_id,
                error_message="Decision already exists. Per MANTRA-LAW-001 §10, "
                             "stored decisions are immutable."
            )

        # Step 2: Validate supersedes chain (data integrity) - async
        supersedes_errors = await self._validate_supersedes_chain_async(decision)
        if supersedes_errors:
            return StoreDecisionResult(
                result=StoreResult.INVALID_SUPERSEDES,
                decision_id=decision.decision_id,
                error_message=" | ".join(supersedes_errors)
            )

        # Step 3: Generate decision_code if not already set
        if not decision.decision_code:
            # Get sequence number for this aspect (1-based)
            sequence = await self.repository.count_by_aspect_async(decision.aspect_id) + 1
            decision.decision_code = generate_decision_code(
                domain_id=decision.domain_id,
                aspect_id=decision.aspect_id,
                sequence=sequence,
                version=decision.version
            )

        # Step 4: Store decision
        try:
            stored_at = datetime.utcnow()
            stored_decision = StoredDecision(
                decision=decision,
                stored_at=stored_at,
                stored_by=stored_by,
                storage_version=1
            )

            # CRITICAL: await the async save method
            await self.repository.save_async(stored_decision)

            # Emit storage event (for legacy audit trail)
            event = DecisionEvent(
                event_type=DecisionEventType.DECISION_STORED,
                decision_id=decision.decision_id,
                actor=stored_by,
                metadata={"storage_version": 1}
            )
            await self.repository.record_event_async(event)

            # Record audit entry (command-style API audit) - using typed metadata
            stored_metadata = StoredMetadata(
                storage_version=1,
                supersedes=decision.supersedes,
                version=decision.version,
            )
            audit_entry = AuditEntry(
                event_type=AuditEventType.DECISION_STORED,
                actor=stored_by,
                actor_type="human",
                decision_id=decision.decision_id,
                metadata=stored_metadata.to_dict()
            )
            await self.repository.record_audit_async(audit_entry)

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

    async def _validate_supersedes_chain_async(self, decision: Decision) -> List[str]:
        """Async version of supersedes chain validation."""
        errors = []

        if decision.supersedes:
            # Check 1: Target exists
            target = await self.repository.find_by_id_async(decision.supersedes)
            if not target:
                errors.append(
                    f"Supersedes target '{decision.supersedes}' not found. "
                    "Cannot supersede a non-existent decision."
                )
                return errors

            # Check 2: No circular reference
            chain = await self.repository.find_supersedes_chain_async(decision.supersedes)
            chain_ids = {sd.decision.decision_id for sd in chain}
            if decision.decision_id in chain_ids:
                errors.append(
                    f"Circular supersedes chain detected. "
                    f"Decision '{decision.decision_id}' already exists in the chain."
                )

            # Check 3: No multiple decisions superseding same target
            all_decisions = await self.repository.find_all_async(limit=10000, offset=0)
            superseding_same = [
                sd for sd in all_decisions
                if sd.decision.supersedes == decision.supersedes
                and sd.decision.decision_id != decision.decision_id
            ]
            if superseding_same:
                existing_ids = [sd.decision.decision_id for sd in superseding_same]
                errors.append(
                    f"Multiple decisions cannot supersede the same target. "
                    f"Decision(s) {existing_ids} already supersede '{decision.supersedes}'."
                )

        return errors


def store_decision(
    decision: Decision,
    stored_by: str,
    repository: DecisionRepository
) -> StoreDecisionResult:
    """
    Store a decision - PERSISTENCE ONLY (synchronous).

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


async def store_decision_async(
    decision: Decision,
    stored_by: str,
    repository: DecisionRepository
) -> StoreDecisionResult:
    """
    Store a decision - PERSISTENCE ONLY (async version for FastAPI).

    This is the async entry point for the Decision Store Service
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
    return await use_case.execute_async(decision, stored_by)
