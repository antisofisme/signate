"""
MANTRA-GRAPH-001: Decision Graph Validation Service

This module provides graph-level validation that cannot be done at schema level:
- Cycle detection (prevents circular DEPENDS_ON)
- Supersede auto-sync (updates predecessor's successor_id)
- Stale reference detection (finds references to deprecated decisions)
- Impact propagation (notifies dependents on changes)

These validations operate on the decision GRAPH, not individual records.
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..domain.schema_v3_enhanced import (
    StaleReferenceWarning,
    NotificationTrigger,
    ConflictStatus,
)


# ============================================================================
# SECTION 1: Data Structures
# ============================================================================

@dataclass
class GraphNode:
    """Represents a decision in the graph."""
    decision_id: str
    decision_code: Optional[str]
    domain_id: str
    aspect_id: str
    stability_status: str
    successor_id: Optional[str]
    supersedes: Optional[str]


@dataclass
class GraphEdge:
    """Represents a relation between decisions."""
    source_id: str
    target_id: str
    relation_type: str
    strength: str = "NORMAL"


@dataclass
class CycleDetectionResult:
    """Result of cycle detection."""
    has_cycle: bool
    cycle_path: List[str]  # Decision IDs in the cycle
    cycle_description: Optional[str]


@dataclass
class ValidationResult:
    """Result of graph validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cycle_result: Optional[CycleDetectionResult]
    stale_references: List[StaleReferenceWarning]


@dataclass
class ImpactAssessment:
    """Assessment of impact from changing a decision."""
    decision_id: str
    directly_affected: List[str]  # Decisions that directly depend on this
    transitively_affected: List[str]  # All decisions affected via chains
    total_affected_count: int
    max_depth: int
    breaking_change_impact: str  # "none", "low", "medium", "high", "critical"
    requires_notification: bool
    affected_teams: List[str]


class RelationType(str, Enum):
    """Relation types for graph traversal."""
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    INFORMED_BY = "informed_by"
    SUPERSEDED_BY = "superseded_by"
    ENABLES = "enables"
    CONSTRAINS = "constrains"
    IMPLEMENTS = "implements"
    EXTENDS = "extends"


# ============================================================================
# SECTION 2: Cycle Detection
# ============================================================================

class CycleDetector:
    """
    Detects cycles in the decision graph.

    Uses DFS-based algorithm to find cycles in DEPENDS_ON relations.
    """

    def __init__(self, edges: List[GraphEdge]):
        """
        Initialize with graph edges.

        Args:
            edges: List of GraphEdge representing relations
        """
        self.adjacency: Dict[str, List[str]] = {}
        self._build_adjacency(edges)

    def _build_adjacency(self, edges: List[GraphEdge]):
        """Build adjacency list from edges."""
        for edge in edges:
            # Only track DEPENDS_ON for cycle detection
            if edge.relation_type == RelationType.DEPENDS_ON.value:
                if edge.source_id not in self.adjacency:
                    self.adjacency[edge.source_id] = []
                self.adjacency[edge.source_id].append(edge.target_id)

    def detect_cycle(self, start_node: str) -> CycleDetectionResult:
        """
        Detect if adding start_node would create a cycle.

        Uses DFS with recursion stack to detect back edges.

        Args:
            start_node: Decision ID to check

        Returns:
            CycleDetectionResult with cycle info if found
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.adjacency.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle - extract the cycle path
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return None

        cycle_path = dfs(start_node)

        if cycle_path:
            return CycleDetectionResult(
                has_cycle=True,
                cycle_path=cycle_path,
                cycle_description=f"Circular dependency detected: {' -> '.join(cycle_path)}"
            )

        return CycleDetectionResult(
            has_cycle=False,
            cycle_path=[],
            cycle_description=None
        )

    def detect_all_cycles(self) -> List[CycleDetectionResult]:
        """
        Detect all cycles in the graph.

        Returns:
            List of CycleDetectionResult for each cycle found
        """
        cycles: List[CycleDetectionResult] = []
        visited: Set[str] = set()

        for node in self.adjacency.keys():
            if node not in visited:
                result = self.detect_cycle(node)
                if result.has_cycle:
                    cycles.append(result)
                    # Mark cycle nodes as visited
                    visited.update(result.cycle_path)

        return cycles

    def would_create_cycle(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "depends_on"
    ) -> CycleDetectionResult:
        """
        Check if adding a new edge would create a cycle.

        Args:
            source_id: Source decision ID
            target_id: Target decision ID
            relation_type: Type of relation

        Returns:
            CycleDetectionResult indicating if cycle would be created
        """
        if relation_type != RelationType.DEPENDS_ON.value:
            # Only DEPENDS_ON can create problematic cycles
            return CycleDetectionResult(
                has_cycle=False,
                cycle_path=[],
                cycle_description=None
            )

        # Temporarily add the edge
        if source_id not in self.adjacency:
            self.adjacency[source_id] = []
        self.adjacency[source_id].append(target_id)

        # Check for cycle
        result = self.detect_cycle(source_id)

        # Remove the temporary edge
        self.adjacency[source_id].remove(target_id)

        return result


# ============================================================================
# SECTION 3: Supersede Auto-Sync
# ============================================================================

@dataclass
class SupersedeAction:
    """Action to perform for supersede synchronization."""
    action_type: str  # "update_successor", "deprecate", "notify"
    target_decision_id: str
    field_path: Optional[str]
    new_value: Any
    reason: str


class SupersedeSync:
    """
    Handles automatic synchronization when a decision supersedes another.

    When Decision B supersedes A:
    1. A.stability.successor_id = B.decision_id
    2. A.stability.stability_status = "deprecated"
    3. All decisions referencing A should be notified
    """

    @staticmethod
    def generate_sync_actions(
        new_decision_id: str,
        superseded_decision_id: str,
        superseded_decision_code: Optional[str] = None
    ) -> List[SupersedeAction]:
        """
        Generate actions needed when a decision supersedes another.

        Args:
            new_decision_id: ID of the new decision
            superseded_decision_id: ID of the decision being superseded
            superseded_decision_code: Code of superseded decision (for logging)

        Returns:
            List of SupersedeAction to execute
        """
        actions = []

        # Action 1: Update successor_id on old decision
        actions.append(SupersedeAction(
            action_type="update_successor",
            target_decision_id=superseded_decision_id,
            field_path="stability.successor_id",
            new_value=new_decision_id,
            reason=f"Superseded by {new_decision_id}"
        ))

        # Action 2: Set stability_status to deprecated
        actions.append(SupersedeAction(
            action_type="deprecate",
            target_decision_id=superseded_decision_id,
            field_path="stability.stability_status",
            new_value="deprecated",
            reason=f"Superseded by {new_decision_id}"
        ))

        # Action 3: Trigger notification for dependents
        actions.append(SupersedeAction(
            action_type="notify",
            target_decision_id=superseded_decision_id,
            field_path=None,
            new_value=NotificationTrigger.DECISION_SUPERSEDED.value,
            reason=f"Decision {superseded_decision_code or superseded_decision_id} has been superseded"
        ))

        return actions

    @staticmethod
    def generate_sql_updates(actions: List[SupersedeAction]) -> List[str]:
        """
        Generate SQL statements for sync actions.

        Args:
            actions: List of SupersedeAction

        Returns:
            List of SQL statements to execute
        """
        sql_statements = []

        for action in actions:
            if action.action_type == "update_successor":
                sql = f"""
                UPDATE decisions
                SET stability = jsonb_set(
                    COALESCE(stability, '{{}}'::jsonb),
                    '{{successor_id}}',
                    '"{action.new_value}"'::jsonb
                )
                WHERE decision_id = '{action.target_decision_id}'
                """
                sql_statements.append(sql.strip())

            elif action.action_type == "deprecate":
                sql = f"""
                UPDATE decisions
                SET stability = jsonb_set(
                    jsonb_set(
                        COALESCE(stability, '{{}}'::jsonb),
                        '{{stability_status}}',
                        '"deprecated"'::jsonb
                    ),
                    '{{deprecation_date}}',
                    '"{datetime.utcnow().date().isoformat()}"'::jsonb
                )
                WHERE decision_id = '{action.target_decision_id}'
                """
                sql_statements.append(sql.strip())

        return sql_statements


# ============================================================================
# SECTION 4: Stale Reference Detection
# ============================================================================

class StaleReferenceDetector:
    """
    Detects references to deprecated or superseded decisions.
    """

    def __init__(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge]
    ):
        """
        Initialize with graph data.

        Args:
            nodes: List of decision nodes
            edges: List of relation edges
        """
        self.nodes = {n.decision_id: n for n in nodes}
        self.edges = edges

    def find_stale_references(self) -> List[StaleReferenceWarning]:
        """
        Find all references to deprecated decisions.

        Returns:
            List of StaleReferenceWarning for each stale reference
        """
        warnings: List[StaleReferenceWarning] = []

        # Find deprecated/archived decisions
        deprecated_ids = {
            node_id: node
            for node_id, node in self.nodes.items()
            if node.stability_status in ["deprecated", "archived"]
        }

        if not deprecated_ids:
            return warnings

        # Find references to deprecated decisions
        for edge in self.edges:
            if edge.target_id in deprecated_ids:
                deprecated_node = deprecated_ids[edge.target_id]

                warning = StaleReferenceWarning(
                    referenced_decision_id=edge.target_id,
                    referenced_decision_code=deprecated_node.decision_code,
                    reference_type=edge.relation_type,
                    successor_id=deprecated_node.successor_id,
                    successor_code=self._get_code(deprecated_node.successor_id),
                    migration_available=deprecated_node.successor_id is not None,
                    detected_at=datetime.utcnow()
                )
                warnings.append(warning)

        return warnings

    def _get_code(self, decision_id: Optional[str]) -> Optional[str]:
        """Get decision code by ID."""
        if decision_id and decision_id in self.nodes:
            return self.nodes[decision_id].decision_code
        return None

    def find_stale_references_for_decision(
        self,
        decision_id: str,
        relations: List[Dict[str, Any]]
    ) -> List[StaleReferenceWarning]:
        """
        Find stale references for a specific decision.

        Args:
            decision_id: Decision to check
            relations: Relations of the decision

        Returns:
            List of warnings for stale references
        """
        warnings: List[StaleReferenceWarning] = []

        for rel in relations:
            target_id = rel.get("target_id")
            if target_id and target_id in self.nodes:
                target_node = self.nodes[target_id]
                if target_node.stability_status in ["deprecated", "archived"]:
                    warnings.append(StaleReferenceWarning(
                        referenced_decision_id=target_id,
                        referenced_decision_code=target_node.decision_code,
                        reference_type=rel.get("type", "unknown"),
                        successor_id=target_node.successor_id,
                        migration_available=target_node.successor_id is not None
                    ))

        return warnings


# ============================================================================
# SECTION 5: Impact Analysis
# ============================================================================

class ImpactAnalyzer:
    """
    Analyzes impact of changes to a decision.
    """

    def __init__(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge]
    ):
        """Initialize with graph data."""
        self.nodes = {n.decision_id: n for n in nodes}

        # Build reverse adjacency (who depends on me)
        self.reverse_adjacency: Dict[str, List[str]] = {}
        for edge in edges:
            if edge.relation_type == RelationType.DEPENDS_ON.value:
                if edge.target_id not in self.reverse_adjacency:
                    self.reverse_adjacency[edge.target_id] = []
                self.reverse_adjacency[edge.target_id].append(edge.source_id)

    def analyze_impact(
        self,
        decision_id: str,
        is_breaking_change: bool = False
    ) -> ImpactAssessment:
        """
        Analyze impact of changing a decision.

        Args:
            decision_id: Decision being changed
            is_breaking_change: Whether the change is breaking

        Returns:
            ImpactAssessment with affected decisions
        """
        directly_affected = self.reverse_adjacency.get(decision_id, [])

        # BFS to find transitive dependencies
        transitively_affected: Set[str] = set()
        queue = list(directly_affected)
        max_depth = 0
        current_depth = 1
        level_end = len(queue)

        while queue:
            current_id = queue.pop(0)
            if current_id not in transitively_affected:
                transitively_affected.add(current_id)
                # Add this node's dependents
                for dependent in self.reverse_adjacency.get(current_id, []):
                    if dependent not in transitively_affected:
                        queue.append(dependent)

            level_end -= 1
            if level_end == 0:
                current_depth += 1
                max_depth = max(max_depth, current_depth)
                level_end = len(queue)

        # Determine impact level
        total_affected = len(transitively_affected)
        if total_affected == 0:
            impact = "none"
        elif total_affected <= 5:
            impact = "low"
        elif total_affected <= 20:
            impact = "medium"
        elif total_affected <= 50:
            impact = "high"
        else:
            impact = "critical"

        # Collect affected teams (would need team info in nodes)
        affected_teams: List[str] = []

        return ImpactAssessment(
            decision_id=decision_id,
            directly_affected=directly_affected,
            transitively_affected=list(transitively_affected),
            total_affected_count=total_affected,
            max_depth=max_depth,
            breaking_change_impact=impact if is_breaking_change else "none",
            requires_notification=total_affected > 0 and is_breaking_change,
            affected_teams=affected_teams
        )


# ============================================================================
# SECTION 6: Complete Graph Validator
# ============================================================================

class DecisionGraphValidator:
    """
    Complete validation service for the decision graph.

    Combines cycle detection, stale reference detection, and impact analysis.
    """

    def __init__(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge]
    ):
        """
        Initialize validator with graph data.

        Args:
            nodes: All decision nodes
            edges: All relation edges
        """
        self.nodes = nodes
        self.edges = edges
        self.cycle_detector = CycleDetector(edges)
        self.stale_detector = StaleReferenceDetector(nodes, edges)
        self.impact_analyzer = ImpactAnalyzer(nodes, edges)

    def validate_new_decision(
        self,
        decision_id: str,
        relations: List[Dict[str, Any]],
        supersedes: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a new decision before insertion.

        Checks:
        1. No cycles would be created
        2. No references to deprecated decisions (warning)
        3. Supersede target exists (if applicable)

        Args:
            decision_id: New decision ID
            relations: Relations to add
            supersedes: ID of decision being superseded

        Returns:
            ValidationResult with errors and warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        cycle_result = None
        stale_references: List[StaleReferenceWarning] = []

        # Check for cycles
        for rel in relations:
            if rel.get("type") == "depends_on":
                result = self.cycle_detector.would_create_cycle(
                    decision_id,
                    rel.get("target_id"),
                    "depends_on"
                )
                if result.has_cycle:
                    errors.append(f"Cycle detected: {result.cycle_description}")
                    cycle_result = result

        # Check for stale references
        stale_refs = self.stale_detector.find_stale_references_for_decision(
            decision_id,
            relations
        )
        for ref in stale_refs:
            if ref.migration_available:
                warnings.append(
                    f"Reference to deprecated decision {ref.referenced_decision_code}. "
                    f"Consider using successor {ref.successor_code}"
                )
            else:
                warnings.append(
                    f"Reference to deprecated decision {ref.referenced_decision_code} "
                    f"with no successor"
                )
            stale_references.append(ref)

        # Validate supersedes target
        if supersedes:
            node_ids = {n.decision_id for n in self.nodes}
            if supersedes not in node_ids:
                errors.append(f"Supersedes target {supersedes} does not exist")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cycle_result=cycle_result,
            stale_references=stale_references
        )

    def validate_graph_integrity(self) -> ValidationResult:
        """
        Validate entire graph integrity.

        Returns:
            ValidationResult with all issues found
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check for cycles
        cycles = self.cycle_detector.detect_all_cycles()
        for cycle in cycles:
            errors.append(f"Cycle detected: {cycle.cycle_description}")

        # Check for stale references
        stale_refs = self.stale_detector.find_stale_references()
        for ref in stale_refs:
            warnings.append(
                f"Stale reference to {ref.referenced_decision_code or ref.referenced_decision_id}"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cycle_result=cycles[0] if cycles else None,
            stale_references=stale_refs
        )

    def get_supersede_actions(
        self,
        new_decision_id: str,
        superseded_decision_id: str
    ) -> List[SupersedeAction]:
        """
        Get actions needed for supersede synchronization.

        Args:
            new_decision_id: ID of new decision
            superseded_decision_id: ID of decision being superseded

        Returns:
            List of actions to execute
        """
        superseded_code = None
        for node in self.nodes:
            if node.decision_id == superseded_decision_id:
                superseded_code = node.decision_code
                break

        return SupersedeSync.generate_sync_actions(
            new_decision_id,
            superseded_decision_id,
            superseded_code
        )

    def get_impact_assessment(
        self,
        decision_id: str,
        is_breaking_change: bool = False
    ) -> ImpactAssessment:
        """
        Get impact assessment for a decision change.

        Args:
            decision_id: Decision being changed
            is_breaking_change: Whether change is breaking

        Returns:
            ImpactAssessment
        """
        return self.impact_analyzer.analyze_impact(decision_id, is_breaking_change)


# ============================================================================
# SECTION 7: SQL Queries for Graph Operations
# ============================================================================

GRAPH_QUERIES = {
    "get_all_nodes": """
        SELECT
            decision_id,
            decision_code,
            domain_id,
            aspect_id,
            COALESCE(stability->>'stability_status', 'stable') as stability_status,
            stability->>'successor_id' as successor_id,
            supersedes
        FROM decisions
        WHERE 1=1
    """,

    "get_all_edges": """
        SELECT
            d.decision_id as source_id,
            (r->>'target_id') as target_id,
            (r->>'type') as relation_type,
            COALESCE(r->>'strength', 'NORMAL') as strength
        FROM decisions d,
             jsonb_array_elements(COALESCE(d.relations, '[]'::jsonb)) r
        WHERE r->>'target_id' IS NOT NULL
    """,

    "find_stale_references": """
        SELECT
            d.decision_id as referencing_id,
            d.decision_code as referencing_code,
            (r->>'target_id') as deprecated_id,
            dep.decision_code as deprecated_code,
            dep.stability->>'successor_id' as successor_id,
            (r->>'type') as reference_type
        FROM decisions d,
             jsonb_array_elements(COALESCE(d.relations, '[]'::jsonb)) r
             JOIN decisions dep ON dep.decision_id = (r->>'target_id')::uuid
        WHERE COALESCE(dep.stability->>'stability_status', 'stable') IN ('deprecated', 'archived')
    """,

    "get_reverse_dependencies": """
        SELECT
            d.decision_id as dependent_id,
            d.decision_code as dependent_code
        FROM decisions d,
             jsonb_array_elements(COALESCE(d.relations, '[]'::jsonb)) r
        WHERE (r->>'target_id') = :decision_id
          AND (r->>'type') = 'depends_on'
    """,

    "detect_cycles_cte": """
        WITH RECURSIVE dependency_chain AS (
            -- Base case: start from a specific decision
            SELECT
                decision_id as start_id,
                decision_id as current_id,
                ARRAY[decision_id] as path,
                false as has_cycle
            FROM decisions
            WHERE decision_id = :start_decision_id

            UNION ALL

            -- Recursive case: follow depends_on relations
            SELECT
                dc.start_id,
                (r->>'target_id')::uuid as current_id,
                dc.path || (r->>'target_id')::uuid,
                (r->>'target_id')::uuid = ANY(dc.path) as has_cycle
            FROM dependency_chain dc
            JOIN decisions d ON d.decision_id = dc.current_id
            CROSS JOIN jsonb_array_elements(COALESCE(d.relations, '[]'::jsonb)) r
            WHERE (r->>'type') = 'depends_on'
              AND NOT dc.has_cycle
              AND array_length(dc.path, 1) < 50  -- Prevent infinite recursion
        )
        SELECT * FROM dependency_chain WHERE has_cycle = true
    """
}


# ============================================================================
# SECTION 8: Materialized View for Performance
# ============================================================================

MATERIALIZED_VIEW_SQL = """
-- Materialized view for decision graph (for fast traversal)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_decision_graph AS
SELECT
    d.decision_id as source_id,
    d.decision_code as source_code,
    (r->>'target_id')::uuid as target_id,
    r->>'type' as relation_type,
    COALESCE(r->>'strength', 'NORMAL') as strength,
    COALESCE(d.stability->>'stability_status', 'stable') as source_status,
    d.supersedes
FROM decisions d
CROSS JOIN jsonb_array_elements(COALESCE(d.relations, '[]'::jsonb)) r
WHERE r->>'target_id' IS NOT NULL;

-- Indexes for the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_graph_unique
    ON mv_decision_graph(source_id, target_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_mv_graph_target
    ON mv_decision_graph(target_id);
CREATE INDEX IF NOT EXISTS idx_mv_graph_type
    ON mv_decision_graph(relation_type);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_decision_graph()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_decision_graph;
END;
$$ LANGUAGE plpgsql;

-- Trigger to refresh on changes (optional - can be expensive)
-- Better to refresh periodically via cron
"""
