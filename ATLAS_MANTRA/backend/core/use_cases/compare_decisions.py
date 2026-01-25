"""
Compare Decisions Use Case

Compares two decision versions side-by-side.
Shows differences, supersedes chain, common group/feature.

Per Human Decision (Phase 3):
- Read operations are PURE DATA ACCESS
- NO semantic filtering
- Consumer interprets the data
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any
from enum import Enum

from ..domain.schema import Decision, GroupId, FeatureId
from ..domain.decision import StoredDecision, AuditEventType, CompareMetadata, ReadMetadata
from .audit_log import record_audit
from ..repositories.decision_repository import DecisionRepository


class CompareResult(Enum):
    """Result of comparison operation"""
    COMPARABLE = "COMPARABLE"  # Both decisions found
    NOT_FOUND_A = "NOT_FOUND_A"  # Decision A not found
    NOT_FOUND_B = "NOT_FOUND_B"  # Decision B not found
    NOT_FOUND_BOTH = "NOT_FOUND_BOTH"  # Neither found
    ERROR = "ERROR"  # Technical error


@dataclass
class FieldDifference:
    """Represents a difference in a single field"""
    field_name: str
    value_a: Any
    value_b: Any
    change_type: str  # "modified", "added", "removed"


@dataclass
class DecisionComparison:
    """
    Result of comparing two decisions.

    Contains:
    - Both decisions (if found)
    - List of field differences
    - Relationship information
    """
    result: CompareResult
    decision_a: Optional[Decision] = None
    decision_b: Optional[Decision] = None
    stored_at_a: Optional[datetime] = None
    stored_at_b: Optional[datetime] = None
    differences: List[FieldDifference] = field(default_factory=list)
    is_supersedes_chain: bool = False  # A supersedes B or B supersedes A
    supersedes_direction: Optional[str] = None  # "a_supersedes_b" or "b_supersedes_a"
    common_group: bool = False
    common_feature: bool = False
    error_message: Optional[str] = None


@dataclass
class VersionChainResult:
    """Result of getting version chain for a decision"""
    result: CompareResult
    decision_id: str = ""
    chain: List[Decision] = field(default_factory=list)
    chain_stored_at: List[datetime] = field(default_factory=list)
    total_versions: int = 0
    error_message: Optional[str] = None


class CompareDecisionsUseCase:
    """
    Compares two decisions side-by-side.

    Per MANTRA-LAW-001:
    - Both decisions are immutable
    - Comparison is read-only
    - Consumer interprets the differences
    """

    def __init__(self, repository: DecisionRepository):
        self._repository = repository

    def compare(
        self,
        decision_id_a: str,
        decision_id_b: str,
        actor: str,
    ) -> DecisionComparison:
        """
        Compare two decisions.

        Args:
            decision_id_a: First decision ID
            decision_id_b: Second decision ID
            actor: Human identifier performing comparison

        Returns:
            DecisionComparison with differences
        """
        try:
            # Fetch both decisions
            stored_a = self._repository.find_by_id(decision_id_a)
            stored_b = self._repository.find_by_id(decision_id_b)

            # Handle not found cases
            if not stored_a and not stored_b:
                return DecisionComparison(
                    result=CompareResult.NOT_FOUND_BOTH,
                    error_message=f"Neither decision found: {decision_id_a}, {decision_id_b}",
                )
            elif not stored_a:
                return DecisionComparison(
                    result=CompareResult.NOT_FOUND_A,
                    decision_b=stored_b.decision if stored_b else None,
                    stored_at_b=stored_b.stored_at if stored_b else None,
                    error_message=f"Decision A not found: {decision_id_a}",
                )
            elif not stored_b:
                return DecisionComparison(
                    result=CompareResult.NOT_FOUND_B,
                    decision_a=stored_a.decision if stored_a else None,
                    stored_at_a=stored_a.stored_at if stored_a else None,
                    error_message=f"Decision B not found: {decision_id_b}",
                )

            decision_a = stored_a.decision
            decision_b = stored_b.decision

            # Calculate differences
            differences = self._calculate_differences(decision_a, decision_b)

            # Check supersedes relationship
            is_supersedes, direction = self._check_supersedes_chain(decision_a, decision_b)

            # Check common group/feature
            common_group = decision_a.group_id == decision_b.group_id
            common_feature = decision_a.feature_id == decision_b.feature_id

            # Record audit event using typed metadata
            compare_metadata = CompareMetadata(
                compared_with=decision_id_b,
                differences_count=len(differences),
                is_supersedes_chain=is_supersedes,
                common_group=common_group,
                common_feature=common_feature,
            )
            record_audit(
                event_type=AuditEventType.DECISION_COMPARED,
                actor=actor,
                actor_type="human",
                decision_id=decision_id_a,
                repository=self._repository,
                metadata=compare_metadata.to_dict(),
            )

            return DecisionComparison(
                result=CompareResult.COMPARABLE,
                decision_a=decision_a,
                decision_b=decision_b,
                stored_at_a=stored_a.stored_at,
                stored_at_b=stored_b.stored_at,
                differences=differences,
                is_supersedes_chain=is_supersedes,
                supersedes_direction=direction,
                common_group=common_group,
                common_feature=common_feature,
            )

        except Exception as e:
            return DecisionComparison(
                result=CompareResult.ERROR,
                error_message=str(e),
            )

    def get_version_chain(
        self,
        decision_id: str,
        actor: str,
    ) -> VersionChainResult:
        """
        Get the complete version chain for a decision.

        Returns all decisions in the supersedes chain.

        Args:
            decision_id: Decision ID to get chain for
            actor: Human identifier

        Returns:
            VersionChainResult with chain
        """
        try:
            chain = self._repository.find_supersedes_chain(decision_id)

            if not chain:
                return VersionChainResult(
                    result=CompareResult.NOT_FOUND_A,
                    decision_id=decision_id,
                    error_message=f"Decision not found: {decision_id}",
                )

            # Record audit event using typed metadata
            read_metadata = ReadMetadata(
                operation="version_chain",
                chain_length=len(chain),
            )
            record_audit(
                event_type=AuditEventType.DECISION_READ,
                actor=actor,
                actor_type="human",
                decision_id=decision_id,
                repository=self._repository,
                metadata=read_metadata.to_dict(),
            )

            return VersionChainResult(
                result=CompareResult.COMPARABLE,
                decision_id=decision_id,
                chain=[sd.decision for sd in chain],
                chain_stored_at=[sd.stored_at for sd in chain],
                total_versions=len(chain),
            )

        except Exception as e:
            return VersionChainResult(
                result=CompareResult.ERROR,
                decision_id=decision_id,
                error_message=str(e),
            )

    def _calculate_differences(
        self,
        decision_a: Decision,
        decision_b: Decision,
    ) -> List[FieldDifference]:
        """Calculate field-by-field differences between two decisions."""
        differences = []

        # Fields to compare (excluding auto-generated/metadata)
        compare_fields = [
            "group_id",
            "feature_id",
            "statement",
            "rationale",
            "scope",
            "blast_radius",
            "version",
            "supersedes",
        ]

        for field_name in compare_fields:
            value_a = getattr(decision_a, field_name, None)
            value_b = getattr(decision_b, field_name, None)

            # Convert enums to values for comparison
            if hasattr(value_a, "value"):
                value_a = value_a.value
            if hasattr(value_b, "value"):
                value_b = value_b.value

            if value_a != value_b:
                differences.append(FieldDifference(
                    field_name=field_name,
                    value_a=value_a,
                    value_b=value_b,
                    change_type="modified",
                ))

        # Compare constraints (more complex)
        constraints_a = {c.constraint_id: c for c in decision_a.constraints}
        constraints_b = {c.constraint_id: c for c in decision_b.constraints}

        # Constraints in A but not B
        for cid in set(constraints_a.keys()) - set(constraints_b.keys()):
            differences.append(FieldDifference(
                field_name=f"constraint:{cid}",
                value_a=constraints_a[cid].model_dump(),
                value_b=None,
                change_type="removed",
            ))

        # Constraints in B but not A
        for cid in set(constraints_b.keys()) - set(constraints_a.keys()):
            differences.append(FieldDifference(
                field_name=f"constraint:{cid}",
                value_a=None,
                value_b=constraints_b[cid].model_dump(),
                change_type="added",
            ))

        # Constraints in both but different
        for cid in set(constraints_a.keys()) & set(constraints_b.keys()):
            if constraints_a[cid] != constraints_b[cid]:
                differences.append(FieldDifference(
                    field_name=f"constraint:{cid}",
                    value_a=constraints_a[cid].model_dump(),
                    value_b=constraints_b[cid].model_dump(),
                    change_type="modified",
                ))

        # Compare invariants
        inv_a = set(decision_a.invariants)
        inv_b = set(decision_b.invariants)

        for inv in inv_a - inv_b:
            differences.append(FieldDifference(
                field_name="invariant",
                value_a=inv,
                value_b=None,
                change_type="removed",
            ))

        for inv in inv_b - inv_a:
            differences.append(FieldDifference(
                field_name="invariant",
                value_a=None,
                value_b=inv,
                change_type="added",
            ))

        return differences

    def _check_supersedes_chain(
        self,
        decision_a: Decision,
        decision_b: Decision,
    ) -> tuple[bool, Optional[str]]:
        """Check if there's a supersedes relationship between decisions."""
        # Direct supersedes
        if decision_a.supersedes == decision_b.decision_id:
            return True, "a_supersedes_b"
        if decision_b.supersedes == decision_a.decision_id:
            return True, "b_supersedes_a"

        # Check indirect chain (A supersedes chain includes B or vice versa)
        chain_a = self._repository.find_supersedes_chain(decision_a.decision_id)
        chain_b_ids = {sd.decision.decision_id for sd in self._repository.find_supersedes_chain(decision_b.decision_id)}

        for sd in chain_a:
            if sd.decision.decision_id in chain_b_ids:
                return True, "shared_chain"

        return False, None


# =============================================================================
# Convenience Functions
# =============================================================================

def compare_decisions(
    decision_id_a: str,
    decision_id_b: str,
    actor: str,
    repository: DecisionRepository,
) -> DecisionComparison:
    """
    Compare two decisions.

    Convenience function for use case execution.
    """
    use_case = CompareDecisionsUseCase(repository)
    return use_case.compare(decision_id_a, decision_id_b, actor)


def get_decision_history(
    decision_id: str,
    actor: str,
    repository: DecisionRepository,
) -> VersionChainResult:
    """
    Get version chain for a decision.

    Convenience function for use case execution.
    """
    use_case = CompareDecisionsUseCase(repository)
    return use_case.get_version_chain(decision_id, actor)
