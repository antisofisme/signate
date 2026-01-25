"""
Decision Aggregate

This module implements the Decision aggregate for ATLAS_MANTRA.
Per MANTRA-LAW-001, decisions are ABSOLUTELY IMMUTABLE once stored.

Per Human Decision (Phase 4):
- NO status field in domain
- Evolution via version + supersedes only
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum
import uuid

from .schema import (
    Decision,
    GroupId,
    FeatureId,
    Scope,
    BlastRadius,
    Constraint,
)


class DecisionEventType(str, Enum):
    """Domain events for Decision aggregate"""
    DECISION_VALIDATED = "DECISION_VALIDATED"
    DECISION_STORED = "DECISION_STORED"
    DECISION_RETRIEVED = "DECISION_RETRIEVED"


class AuditEventType(str, Enum):
    """
    Audit event types for command-style API operations.

    Per MANTRA-LAW-001: All operations must be auditable.
    """
    DECISION_PROPOSED = "DECISION_PROPOSED"
    DECISION_VALIDATED = "DECISION_VALIDATED"
    DECISION_STORED = "DECISION_STORED"
    DECISION_READ = "DECISION_READ"
    DECISION_COMPARED = "DECISION_COMPARED"
    CHALLENGE_CREATED = "CHALLENGE_CREATED"


# ============================================================================
# Typed Audit Metadata Models
# ============================================================================
# These provide consistent, queryable structure for audit trail entries

@dataclass
class ProposedMetadata:
    """
    Typed metadata for DECISION_PROPOSED events.

    Records:
    - proposal_id: Ephemeral proposal identifier
    - validation_status: Result of validation (VALID, INVALID, REJECTED)
    - violations_count: Number of validation violations found
    """
    proposal_id: str
    validation_status: str
    violations_count: int

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "validation_status": self.validation_status,
            "violations_count": self.violations_count,
            "_metadata_type": "ProposedMetadata",
        }


@dataclass
class StoredMetadata:
    """
    Typed metadata for DECISION_STORED events.

    Records:
    - storage_version: Immutability version (always 1 for new decisions)
    - supersedes: ID of decision this one supersedes (if any)
    - version: Semantic version of the decision
    """
    storage_version: int
    supersedes: Optional[str]
    version: str

    def to_dict(self) -> dict:
        return {
            "storage_version": self.storage_version,
            "supersedes": self.supersedes,
            "version": self.version,
            "_metadata_type": "StoredMetadata",
        }


@dataclass
class ChallengeMetadata:
    """
    Typed metadata for CHALLENGE_CREATED events.

    Records:
    - challenged_decision_id: ID of the decision being challenged
    - challenge_rationale: Human explanation for the challenge
    - new_decision_id: ID of the new superseding decision
    """
    challenged_decision_id: str
    challenge_rationale: str
    new_decision_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "challenged_decision_id": self.challenged_decision_id,
            "challenge_rationale": self.challenge_rationale,
            "new_decision_id": self.new_decision_id,
            "_metadata_type": "ChallengeMetadata",
        }


@dataclass
class CompareMetadata:
    """
    Typed metadata for DECISION_COMPARED events.

    Records:
    - compared_with: ID of the other decision in comparison
    - differences_count: Number of fields that differ
    - is_supersedes_chain: Whether decisions are in same supersedes chain
    - common_group: Whether decisions share same group
    - common_feature: Whether decisions share same feature
    """
    compared_with: str
    differences_count: int
    is_supersedes_chain: bool
    common_group: bool
    common_feature: bool

    def to_dict(self) -> dict:
        return {
            "compared_with": self.compared_with,
            "differences_count": self.differences_count,
            "is_supersedes_chain": self.is_supersedes_chain,
            "common_group": self.common_group,
            "common_feature": self.common_feature,
            "_metadata_type": "CompareMetadata",
        }


@dataclass
class ReadMetadata:
    """
    Typed metadata for DECISION_READ events.

    Records:
    - operation: Type of read operation (get, list, history, etc.)
    - additional context fields depending on operation
    """
    operation: str
    chain_length: Optional[int] = None
    filters: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {
            "operation": self.operation,
            "_metadata_type": "ReadMetadata",
        }
        if self.chain_length is not None:
            result["chain_length"] = self.chain_length
        if self.filters:
            result["filters"] = self.filters
        return result


@dataclass
class AuditEntry:
    """
    Audit entry for tracking all operations.

    Records:
    - What happened (event_type)
    - Who did it (actor, actor_type)
    - When (timestamp)
    - What was affected (decision_id)
    - Additional context (metadata)
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.DECISION_READ
    actor: str = ""
    actor_type: str = "human"  # "human" or "ai"
    decision_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate actor_type"""
        if self.actor_type not in ("human", "ai"):
            raise ValueError(f"actor_type must be 'human' or 'ai', got: {self.actor_type}")


@dataclass
class DecisionEvent:
    """
    Domain event for decision operations.

    NOTE: Per MANTRA-L1-IMPL-VALIDATOR-001 §2.3, the validator
    MUST NOT emit events. These events are for the Store and
    Read components only.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: DecisionEventType = DecisionEventType.DECISION_RETRIEVED
    decision_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    actor: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class StoredDecision:
    """
    Stored decision record with immutability enforcement.

    Per MANTRA-LAW-001 §10:
    - Stored decisions MUST NOT be modified
    - Stored decisions MUST NOT be deleted
    """
    decision: Decision
    stored_at: datetime
    stored_by: str
    storage_version: int = 1

    # Immutability marker - starts False to allow dataclass construction
    _is_immutable: bool = field(default=False, repr=False)

    def __post_init__(self):
        """Enforce immutability after storage is complete"""
        # Set immutability flag AFTER construction is complete
        object.__setattr__(self, "_is_immutable", True)

    def __setattr__(self, name, value):
        """Prevent modification after initialization"""
        if hasattr(self, "_is_immutable") and self._is_immutable:
            if name != "_is_immutable":
                raise AttributeError(
                    "StoredDecision is immutable per MANTRA-LAW-001 §10. "
                    "Modification is INVALID."
                )
        super().__setattr__(name, value)


def create_decision(
    group_id: GroupId,
    feature_id: FeatureId,
    statement: str,
    rationale: str,
    scope: Scope,
    blast_radius: BlastRadius,
    version: str,
    created_by: str,
    constraints: Optional[List[Constraint]] = None,
    invariants: Optional[List[str]] = None,
    supersedes: Optional[str] = None,
    related_decisions: Optional[List[str]] = None,
) -> Decision:
    """
    Factory function to create a new Decision.

    Per MANTRA-LAW-001 §6, this function MUST be invoked by a human.
    AI MUST NOT create decisions.

    Per Human Decision (Phase 4):
    - NO status field (lifecycle not encoded)
    - Evolution via version + supersedes only
    """
    return Decision(
        decision_id=str(uuid.uuid4()),
        group_id=group_id,
        feature_id=feature_id,
        statement=statement,
        rationale=rationale,
        constraints=constraints or [],
        invariants=invariants or [],
        scope=scope,
        blast_radius=blast_radius,
        version=version,
        created_by=created_by,
        created_at=datetime.utcnow(),
        supersedes=supersedes,
        related_decisions=related_decisions or [],
    )
