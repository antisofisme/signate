"""
Propose Decision Use Case

Validates a decision and prepares it for storage WITHOUT actually storing.
Per Human Decision (Phase 4): Propose is PREPARATION, not storage.

Flow:
1. Validate decision (call validator)
2. Generate proposal_id + decision_id
3. Return validation result + prepared decision
4. Consumer decides: call POST /decisions to store, or discard

Key Principle:
- Propose DOES NOT store the decision
- Consumer must explicitly call POST /decisions to store
- Proposal is ephemeral (not persisted)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid

from ..domain.schema import (
    Decision,
    DecisionCreate,
    GroupId,
    FeatureId,
    Scope,
    BlastRadius,
    Constraint,
    AuthorshipMetadata,
)
from ..domain.decision import AuditEventType, ProposedMetadata
from .validate_decision import (
    validate_decision,
    ValidationResult,
    ValidationStatus,
)
from .audit_log import record_audit
from ..repositories.decision_repository import DecisionRepository


class ProposeResult(Enum):
    """
    Result of proposal operation.

    READY: Decision is valid and ready to store
    INVALID: Decision failed validation
    """
    READY = "READY"
    INVALID = "INVALID"


@dataclass
class ProposeDecisionResult:
    """
    Result of propose operation.

    Contains:
    - result: READY or INVALID
    - proposal_id: Unique ID for this proposal (ephemeral)
    - decision_id: Pre-generated UUID for the decision (to be used if stored)
    - decision: The prepared decision (not stored yet)
    - validation_result: Full validation result
    - proposed_at: Timestamp of proposal
    - proposed_by: Human identifier who proposed
    """
    result: ProposeResult
    proposal_id: str = ""
    decision_id: str = ""
    decision: Optional[Decision] = None
    validation_result: Optional[ValidationResult] = None
    proposed_at: datetime = field(default_factory=datetime.utcnow)
    proposed_by: str = ""
    advisory_notes: list = field(default_factory=list)


class ProposeDecisionUseCase:
    """
    Proposes a decision for storage.

    This use case:
    1. Validates the decision
    2. Prepares the decision with generated IDs
    3. Returns the prepared decision (NOT stored)

    The consumer then decides whether to store by calling POST /decisions.

    Per MANTRA-LAW-001:
    - Human authority required to propose
    - AI can validate but cannot store
    """

    def __init__(self, repository: DecisionRepository):
        self._repository = repository

    def execute(
        self,
        decision_create: DecisionCreate,
        proposed_by: str,
        authorship_metadata: Optional[AuthorshipMetadata] = None,
    ) -> ProposeDecisionResult:
        """
        Propose a decision.

        Args:
            decision_create: The decision to propose (without IDs)
            proposed_by: Human identifier proposing the decision
            authorship_metadata: Optional metadata for L-rules validation

        Returns:
            ProposeDecisionResult with prepared decision or validation errors
        """
        # Generate IDs
        proposal_id = str(uuid.uuid4())
        decision_id = str(uuid.uuid4())

        # Create the full Decision object for validation
        decision = Decision(
            decision_id=decision_id,
            group_id=decision_create.group_id,
            feature_id=decision_create.feature_id,
            statement=decision_create.statement,
            rationale=decision_create.rationale,
            constraints=decision_create.constraints,
            invariants=decision_create.invariants,
            scope=decision_create.scope,
            blast_radius=decision_create.blast_radius,
            version=decision_create.version,
            created_by=decision_create.created_by or proposed_by,
            created_at=datetime.utcnow(),
            supersedes=decision_create.supersedes,
            related_decisions=decision_create.related_decisions,
            tags=decision_create.tags,
            tech_stack=decision_create.tech_stack,
        )

        # Convert to dict for validation
        decision_dict = decision.model_dump()
        decision_dict["group_id"] = decision.group_id.value
        decision_dict["feature_id"] = decision.feature_id.value
        decision_dict["scope"] = decision.scope.value
        decision_dict["blast_radius"] = decision.blast_radius.value
        decision_dict["constraints"] = [
            {
                "constraint_id": c.constraint_id,
                "statement": c.statement,
                "type": c.type.value,
            }
            for c in decision.constraints
        ]

        # Validate the decision
        validation_result = validate_decision(decision_dict, authorship_metadata)

        # Record audit event using typed metadata
        proposed_metadata = ProposedMetadata(
            proposal_id=proposal_id,
            validation_status=validation_result.status.value,
            violations_count=len(validation_result.violations),
        )
        record_audit(
            event_type=AuditEventType.DECISION_PROPOSED,
            actor=proposed_by,
            actor_type="human",
            decision_id=decision_id,
            repository=self._repository,
            metadata=proposed_metadata.to_dict(),
        )

        # Determine result
        if validation_result.status == ValidationStatus.VALID:
            return ProposeDecisionResult(
                result=ProposeResult.READY,
                proposal_id=proposal_id,
                decision_id=decision_id,
                decision=decision,
                validation_result=validation_result,
                proposed_at=datetime.utcnow(),
                proposed_by=proposed_by,
                advisory_notes=[
                    "Decision is valid and ready to store.",
                    f"Use decision_id={decision_id} when calling POST /decisions",
                    "Call POST /api/v1/decisions with this decision to store it.",
                ],
            )
        else:
            return ProposeDecisionResult(
                result=ProposeResult.INVALID,
                proposal_id=proposal_id,
                decision_id=decision_id,
                decision=decision,
                validation_result=validation_result,
                proposed_at=datetime.utcnow(),
                proposed_by=proposed_by,
                advisory_notes=[
                    f"Decision validation failed: {validation_result.status.value}",
                    f"Found {len(validation_result.violations)} violation(s)",
                    "Fix the violations and re-propose.",
                ],
            )


# =============================================================================
# Convenience Function
# =============================================================================

def propose_decision(
    decision_create: DecisionCreate,
    proposed_by: str,
    repository: DecisionRepository,
    authorship_metadata: Optional[AuthorshipMetadata] = None,
) -> ProposeDecisionResult:
    """
    Propose a decision for storage.

    Convenience function for use case execution.

    Args:
        decision_create: The decision to propose
        proposed_by: Human identifier
        repository: Repository instance
        authorship_metadata: Optional metadata for L-rules

    Returns:
        ProposeDecisionResult
    """
    use_case = ProposeDecisionUseCase(repository)
    return use_case.execute(decision_create, proposed_by, authorship_metadata)
