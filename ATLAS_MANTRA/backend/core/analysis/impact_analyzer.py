"""
MANTRA Impact Analysis

Analyzes what would be affected if a decision or field changes.

USE CASES:
1. "What breaks if I change constraint X?"
2. "What decisions depend on this one?"
3. "What's the blast radius of deprecating decision Y?"

ANALYSIS TYPES:
1. Direct Impact: Immediate dependencies
2. Transitive Impact: Full dependency chain
3. Conflict Impact: What conflicts would be affected
4. Coverage Impact: What applies_to patterns overlap
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from ..domain.field_relation import (
    FieldRelation,
    RelationType,
    RelationGraph,
    FieldPath,
    extract_all_field_paths,
)


class ImpactType(str, Enum):
    """Type of impact."""
    DIRECT_DEPENDENCY = "DIRECT_DEPENDENCY"     # Directly depends on
    TRANSITIVE_DEPENDENCY = "TRANSITIVE_DEPENDENCY"  # Indirectly depends
    IMPLEMENTATION = "IMPLEMENTATION"           # Implements this
    ENFORCEMENT = "ENFORCEMENT"                 # Invariant enforces
    CONFLICT = "CONFLICT"                       # Would create conflict
    COVERAGE_OVERLAP = "COVERAGE_OVERLAP"       # Same applies_to


class ImpactSeverity(str, Enum):
    """Severity of the impact."""
    BREAKING = "BREAKING"       # Would break functionality
    SIGNIFICANT = "SIGNIFICANT" # Major change needed
    MODERATE = "MODERATE"       # Some adjustment needed
    MINOR = "MINOR"             # Informational only


@dataclass
class ImpactedField:
    """A single field that would be impacted."""
    decision_id: str
    decision_code: str
    field_path: str
    field_content: Optional[str]

    impact_type: ImpactType
    severity: ImpactSeverity
    depth: int  # 1 = direct, 2+ = transitive

    reason: str
    resolution_hint: Optional[str] = None

    # Chain info (for transitive impacts)
    via_decision_id: Optional[str] = None
    via_field_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_code": self.decision_code,
            "field_path": self.field_path,
            "field_content": self.field_content[:100] if self.field_content else None,
            "impact_type": self.impact_type.value,
            "severity": self.severity.value,
            "depth": self.depth,
            "reason": self.reason,
            "resolution_hint": self.resolution_hint,
            "via_decision_id": self.via_decision_id,
            "via_field_path": self.via_field_path,
        }


@dataclass
class ImpactAnalysisResult:
    """Result of impact analysis."""
    source_decision_id: str
    source_field_path: Optional[str]
    analysis_type: str  # "field_change", "decision_deprecate", "decision_modify"

    # Impacts by type
    direct_dependencies: List[ImpactedField]
    transitive_dependencies: List[ImpactedField]
    implementations: List[ImpactedField]
    enforcements: List[ImpactedField]
    conflicts: List[ImpactedField]
    coverage_overlaps: List[ImpactedField]

    # Summary
    total_impacted_decisions: int
    total_impacted_fields: int
    max_depth: int
    has_breaking_changes: bool

    # Metadata
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_time_ms: float = 0

    def all_impacts(self) -> List[ImpactedField]:
        """Get all impacts as flat list."""
        return (
            self.direct_dependencies +
            self.transitive_dependencies +
            self.implementations +
            self.enforcements +
            self.conflicts +
            self.coverage_overlaps
        )

    def by_severity(self, severity: ImpactSeverity) -> List[ImpactedField]:
        """Filter impacts by severity."""
        return [i for i in self.all_impacts() if i.severity == severity]

    def by_decision(self, decision_id: str) -> List[ImpactedField]:
        """Get all impacts on a specific decision."""
        return [i for i in self.all_impacts() if i.decision_id == decision_id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_decision_id": self.source_decision_id,
            "source_field_path": self.source_field_path,
            "analysis_type": self.analysis_type,
            "summary": {
                "total_impacted_decisions": self.total_impacted_decisions,
                "total_impacted_fields": self.total_impacted_fields,
                "max_depth": self.max_depth,
                "has_breaking_changes": self.has_breaking_changes,
                "by_type": {
                    "direct_dependencies": len(self.direct_dependencies),
                    "transitive_dependencies": len(self.transitive_dependencies),
                    "implementations": len(self.implementations),
                    "enforcements": len(self.enforcements),
                    "conflicts": len(self.conflicts),
                    "coverage_overlaps": len(self.coverage_overlaps),
                },
            },
            "impacts": {
                "direct_dependencies": [i.to_dict() for i in self.direct_dependencies],
                "transitive_dependencies": [i.to_dict() for i in self.transitive_dependencies],
                "implementations": [i.to_dict() for i in self.implementations],
                "enforcements": [i.to_dict() for i in self.enforcements],
                "conflicts": [i.to_dict() for i in self.conflicts],
                "coverage_overlaps": [i.to_dict() for i in self.coverage_overlaps],
            },
            "analyzed_at": self.analyzed_at.isoformat(),
            "analysis_time_ms": self.analysis_time_ms,
        }


class ImpactAnalyzer:
    """
    Analyzes impact of changes to decisions.

    Uses both decision-level and field-level relationships.
    """

    def __init__(
        self,
        decisions: Optional[List[Dict[str, Any]]] = None,
        relation_graph: Optional[RelationGraph] = None,
        max_depth: int = 10,
    ):
        """
        Initialize analyzer.

        Args:
            decisions: All decisions in the system
            relation_graph: Graph of field-level relationships
            max_depth: Maximum depth to traverse for transitive impacts
        """
        self.decisions = decisions or []
        self.relation_graph = relation_graph or RelationGraph()
        self.max_depth = max_depth

        # Build indexes
        self._decision_index: Dict[str, Dict[str, Any]] = {}
        self._depends_on_index: Dict[str, List[str]] = {}  # dec_id → [depending_dec_ids]
        self._supersedes_index: Dict[str, str] = {}  # dec_id → superseded_by_id

        self._build_indexes()

    def _build_indexes(self):
        """Build lookup indexes from decisions."""
        for decision in self.decisions:
            dec_id = decision.get("decision_id", "")
            if not dec_id:
                continue

            self._decision_index[dec_id] = decision

            # Index depends_on (reverse)
            for dep_id in decision.get("depends_on", []):
                if dep_id not in self._depends_on_index:
                    self._depends_on_index[dep_id] = []
                self._depends_on_index[dep_id].append(dec_id)

            # Index supersedes (reverse)
            supersedes = decision.get("supersedes")
            if supersedes:
                self._supersedes_index[supersedes] = dec_id

    def analyze_field_change(
        self,
        decision_id: str,
        field_path: str,
    ) -> ImpactAnalysisResult:
        """
        Analyze impact of changing a specific field.

        Args:
            decision_id: Decision containing the field
            field_path: Path to the field being changed

        Returns:
            ImpactAnalysisResult with all affected items
        """
        import time
        start_time = time.time()

        direct_deps = []
        transitive_deps = []
        implementations = []
        enforcements = []
        conflicts = []
        overlaps = []

        impacted_decisions: Set[str] = set()
        max_depth_found = 0

        # Get decision info
        decision = self._decision_index.get(decision_id)
        if not decision:
            return self._empty_result(decision_id, field_path, "field_change")

        # 1. Find field-level relations where this field is the source
        outgoing = self.relation_graph.get_relations_from(decision_id, field_path)

        for rel in outgoing:
            target = self._decision_index.get(rel.target_decision_id)
            target_code = target.get("code", "") if target else ""
            target_content = self._get_field_content(target, rel.target_field_path) if target else None

            severity = self._determine_severity(rel.relation_type)

            impact = ImpactedField(
                decision_id=rel.target_decision_id,
                decision_code=target_code,
                field_path=rel.target_field_path,
                field_content=target_content,
                impact_type=self._relation_to_impact_type(rel.relation_type),
                severity=severity,
                depth=1,
                reason=f"Field-level {rel.relation_type.value} relationship",
                resolution_hint=self._get_resolution_hint(rel.relation_type),
            )

            impacted_decisions.add(rel.target_decision_id)

            if rel.relation_type == RelationType.CONFLICTS_WITH:
                conflicts.append(impact)
            elif rel.relation_type == RelationType.IMPLEMENTS:
                implementations.append(impact)
            elif rel.relation_type == RelationType.ENFORCES:
                enforcements.append(impact)
            else:
                direct_deps.append(impact)

        # 2. Follow transitive chains (IMPLEMENTS, ENFORCES)
        visited = {(decision_id, field_path)}
        queue = [(decision_id, field_path, 1)]

        while queue:
            current_dec, current_field, depth = queue.pop(0)

            if depth > self.max_depth:
                continue

            relations = self.relation_graph.get_relations_from(current_dec, current_field)

            for rel in relations:
                key = (rel.target_decision_id, rel.target_field_path)
                if key in visited:
                    continue

                visited.add(key)

                if rel.relation_type in [RelationType.IMPLEMENTS, RelationType.ENFORCES]:
                    target = self._decision_index.get(rel.target_decision_id)
                    target_code = target.get("code", "") if target else ""
                    target_content = self._get_field_content(target, rel.target_field_path) if target else None

                    impact = ImpactedField(
                        decision_id=rel.target_decision_id,
                        decision_code=target_code,
                        field_path=rel.target_field_path,
                        field_content=target_content,
                        impact_type=ImpactType.TRANSITIVE_DEPENDENCY,
                        severity=ImpactSeverity.MODERATE,
                        depth=depth + 1,
                        reason=f"Transitive via {rel.relation_type.value}",
                        via_decision_id=current_dec,
                        via_field_path=current_field,
                    )

                    transitive_deps.append(impact)
                    impacted_decisions.add(rel.target_decision_id)
                    max_depth_found = max(max_depth_found, depth + 1)

                    queue.append((rel.target_decision_id, rel.target_field_path, depth + 1))

        # 3. Find decision-level depends_on impacts
        depending_decisions = self._depends_on_index.get(decision_id, [])

        for dep_dec_id in depending_decisions:
            if dep_dec_id in impacted_decisions:
                continue

            dep_dec = self._decision_index.get(dep_dec_id)
            if not dep_dec:
                continue

            impact = ImpactedField(
                decision_id=dep_dec_id,
                decision_code=dep_dec.get("code", ""),
                field_path="depends_on",
                field_content=f"depends_on: {decision_id}",
                impact_type=ImpactType.DIRECT_DEPENDENCY,
                severity=ImpactSeverity.SIGNIFICANT,
                depth=1,
                reason="Decision-level dependency",
                resolution_hint="Review if dependency is still valid after change",
            )

            direct_deps.append(impact)
            impacted_decisions.add(dep_dec_id)

        # Calculate stats
        total_impacts = (
            len(direct_deps) + len(transitive_deps) + len(implementations) +
            len(enforcements) + len(conflicts) + len(overlaps)
        )

        has_breaking = any(
            i.severity == ImpactSeverity.BREAKING
            for i in direct_deps + transitive_deps + conflicts
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return ImpactAnalysisResult(
            source_decision_id=decision_id,
            source_field_path=field_path,
            analysis_type="field_change",
            direct_dependencies=direct_deps,
            transitive_dependencies=transitive_deps,
            implementations=implementations,
            enforcements=enforcements,
            conflicts=conflicts,
            coverage_overlaps=overlaps,
            total_impacted_decisions=len(impacted_decisions),
            total_impacted_fields=total_impacts,
            max_depth=max_depth_found if max_depth_found > 0 else (1 if total_impacts > 0 else 0),
            has_breaking_changes=has_breaking,
            analysis_time_ms=elapsed_ms,
        )

    def analyze_decision_deprecation(
        self,
        decision_id: str,
    ) -> ImpactAnalysisResult:
        """
        Analyze impact of deprecating a decision.

        Returns all decisions that would be affected.
        """
        import time
        start_time = time.time()

        direct_deps = []
        transitive_deps = []
        implementations = []
        enforcements = []
        conflicts = []
        overlaps = []

        impacted_decisions: Set[str] = set()

        decision = self._decision_index.get(decision_id)
        if not decision:
            return self._empty_result(decision_id, None, "decision_deprecate")

        # 1. Direct dependencies (decisions that depend on this one)
        depending_decisions = self._depends_on_index.get(decision_id, [])

        for dep_dec_id in depending_decisions:
            dep_dec = self._decision_index.get(dep_dec_id)
            if not dep_dec:
                continue

            impact = ImpactedField(
                decision_id=dep_dec_id,
                decision_code=dep_dec.get("code", ""),
                field_path="depends_on",
                field_content=f"depends_on includes: {decision_id}",
                impact_type=ImpactType.DIRECT_DEPENDENCY,
                severity=ImpactSeverity.BREAKING,
                depth=1,
                reason="Decision would lose a dependency",
                resolution_hint="Update depends_on or find alternative decision",
            )

            direct_deps.append(impact)
            impacted_decisions.add(dep_dec_id)

        # 2. Check if anything supersedes this
        superseded_by = self._supersedes_index.get(decision_id)
        if superseded_by:
            superseding = self._decision_index.get(superseded_by)
            if superseding:
                impact = ImpactedField(
                    decision_id=superseded_by,
                    decision_code=superseding.get("code", ""),
                    field_path="supersedes",
                    field_content=f"supersedes: {decision_id}",
                    impact_type=ImpactType.IMPLEMENTATION,
                    severity=ImpactSeverity.MINOR,
                    depth=1,
                    reason="This decision is superseded - deprecation may be expected",
                )

                implementations.append(impact)

        # 3. Field-level relations
        all_paths = extract_all_field_paths(decision)

        for field_path in all_paths:
            outgoing = self.relation_graph.get_relations_from(decision_id, field_path)

            for rel in outgoing:
                target = self._decision_index.get(rel.target_decision_id)
                if not target or rel.target_decision_id in impacted_decisions:
                    continue

                severity = ImpactSeverity.SIGNIFICANT
                if rel.relation_type in [RelationType.IMPLEMENTS, RelationType.ENFORCES]:
                    severity = ImpactSeverity.BREAKING

                impact = ImpactedField(
                    decision_id=rel.target_decision_id,
                    decision_code=target.get("code", ""),
                    field_path=rel.target_field_path,
                    field_content=self._get_field_content(target, rel.target_field_path),
                    impact_type=self._relation_to_impact_type(rel.relation_type),
                    severity=severity,
                    depth=1,
                    reason=f"Field-level {rel.relation_type.value} would be lost",
                    resolution_hint="Review if relationship needs to be migrated",
                )

                if rel.relation_type == RelationType.CONFLICTS_WITH:
                    conflicts.append(impact)
                elif rel.relation_type == RelationType.IMPLEMENTS:
                    implementations.append(impact)
                elif rel.relation_type == RelationType.ENFORCES:
                    enforcements.append(impact)
                else:
                    direct_deps.append(impact)

                impacted_decisions.add(rel.target_decision_id)

        # 4. Coverage overlaps (decisions with same applies_to)
        my_applies = set(decision.get("applies_to", []))

        if my_applies:
            for other in self.decisions:
                other_id = other.get("decision_id", "")
                if other_id == decision_id or other_id in impacted_decisions:
                    continue

                other_applies = set(other.get("applies_to", []))
                overlap = my_applies & other_applies

                if len(overlap) >= 2:  # Significant overlap
                    impact = ImpactedField(
                        decision_id=other_id,
                        decision_code=other.get("code", ""),
                        field_path="applies_to",
                        field_content=f"overlapping patterns: {', '.join(list(overlap)[:3])}",
                        impact_type=ImpactType.COVERAGE_OVERLAP,
                        severity=ImpactSeverity.MINOR,
                        depth=1,
                        reason="Coverage overlap - may need to expand",
                    )

                    overlaps.append(impact)
                    impacted_decisions.add(other_id)

        # Calculate stats
        total_impacts = (
            len(direct_deps) + len(transitive_deps) + len(implementations) +
            len(enforcements) + len(conflicts) + len(overlaps)
        )

        has_breaking = any(
            i.severity == ImpactSeverity.BREAKING
            for i in direct_deps + implementations + enforcements
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return ImpactAnalysisResult(
            source_decision_id=decision_id,
            source_field_path=None,
            analysis_type="decision_deprecate",
            direct_dependencies=direct_deps,
            transitive_dependencies=transitive_deps,
            implementations=implementations,
            enforcements=enforcements,
            conflicts=conflicts,
            coverage_overlaps=overlaps,
            total_impacted_decisions=len(impacted_decisions),
            total_impacted_fields=total_impacts,
            max_depth=1,  # Deprecation is immediate
            has_breaking_changes=has_breaking,
            analysis_time_ms=elapsed_ms,
        )

    def _empty_result(
        self,
        decision_id: str,
        field_path: Optional[str],
        analysis_type: str,
    ) -> ImpactAnalysisResult:
        """Create empty result (e.g., when decision not found)."""
        return ImpactAnalysisResult(
            source_decision_id=decision_id,
            source_field_path=field_path,
            analysis_type=analysis_type,
            direct_dependencies=[],
            transitive_dependencies=[],
            implementations=[],
            enforcements=[],
            conflicts=[],
            coverage_overlaps=[],
            total_impacted_decisions=0,
            total_impacted_fields=0,
            max_depth=0,
            has_breaking_changes=False,
        )

    def _get_field_content(
        self,
        decision: Optional[Dict[str, Any]],
        field_path: str,
    ) -> Optional[str]:
        """Extract field content from decision."""
        if not decision:
            return None

        try:
            path = FieldPath.parse(field_path)
            value = path.get_value(decision)
            if value is None:
                return None
            if isinstance(value, dict):
                return str(value.get("rule", value))
            return str(value)[:200]
        except (ValueError, KeyError):
            return None

    def _relation_to_impact_type(self, relation_type: RelationType) -> ImpactType:
        """Map relation type to impact type."""
        mapping = {
            RelationType.CONFLICTS_WITH: ImpactType.CONFLICT,
            RelationType.STRENGTHENS: ImpactType.DIRECT_DEPENDENCY,
            RelationType.WEAKENS: ImpactType.DIRECT_DEPENDENCY,
            RelationType.IMPLEMENTS: ImpactType.IMPLEMENTATION,
            RelationType.ENFORCES: ImpactType.ENFORCEMENT,
            RelationType.REFERENCES: ImpactType.COVERAGE_OVERLAP,
        }
        return mapping.get(relation_type, ImpactType.DIRECT_DEPENDENCY)

    def _determine_severity(self, relation_type: RelationType) -> ImpactSeverity:
        """Determine severity based on relation type."""
        if relation_type == RelationType.CONFLICTS_WITH:
            return ImpactSeverity.BREAKING
        elif relation_type in [RelationType.IMPLEMENTS, RelationType.ENFORCES]:
            return ImpactSeverity.SIGNIFICANT
        elif relation_type in [RelationType.STRENGTHENS, RelationType.WEAKENS]:
            return ImpactSeverity.MODERATE
        return ImpactSeverity.MINOR

    def _get_resolution_hint(self, relation_type: RelationType) -> str:
        """Get resolution hint for relation type."""
        hints = {
            RelationType.CONFLICTS_WITH: "Resolve conflict before proceeding",
            RelationType.STRENGTHENS: "Verify stronger rule is intended",
            RelationType.WEAKENS: "Verify relaxation is intended",
            RelationType.IMPLEMENTS: "Update implementation if abstract changes",
            RelationType.ENFORCES: "Verify invariant still holds",
            RelationType.REFERENCES: "Update reference if needed",
        }
        return hints.get(relation_type, "Review impact")

    def load_decisions(self, decisions: List[Dict[str, Any]]):
        """Load or reload decisions."""
        self.decisions = decisions
        self._decision_index = {}
        self._depends_on_index = {}
        self._supersedes_index = {}
        self._build_indexes()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def analyze_field_impact(
    decision_id: str,
    field_path: str,
    decisions: List[Dict[str, Any]],
    relation_graph: Optional[RelationGraph] = None,
) -> ImpactAnalysisResult:
    """
    Simple interface to analyze field change impact.
    """
    analyzer = ImpactAnalyzer(
        decisions=decisions,
        relation_graph=relation_graph or RelationGraph(),
    )
    return analyzer.analyze_field_change(decision_id, field_path)


def analyze_deprecation_impact(
    decision_id: str,
    decisions: List[Dict[str, Any]],
    relation_graph: Optional[RelationGraph] = None,
) -> ImpactAnalysisResult:
    """
    Simple interface to analyze decision deprecation impact.
    """
    analyzer = ImpactAnalyzer(
        decisions=decisions,
        relation_graph=relation_graph or RelationGraph(),
    )
    return analyzer.analyze_decision_deprecation(decision_id)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ImpactType",
    "ImpactSeverity",
    "ImpactedField",
    "ImpactAnalysisResult",
    "ImpactAnalyzer",
    "analyze_field_impact",
    "analyze_deprecation_impact",
]
