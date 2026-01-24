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

    # Immutability marker
    _is_immutable: bool = field(default=True, repr=False)

    def __post_init__(self):
        """Enforce immutability after storage"""
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
