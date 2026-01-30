"""
Decision Dependencies - Graph-based Retrieval

Handles decision relationships:
1. If A depends on B, retrieve both
2. If A supersedes B, prefer A
3. Detect circular dependencies
4. Transitive dependency resolution

RELATIONSHIP TYPES:
- depends_on:    A requires B to be understood
- supersedes:    A replaces B (prefer A)
- conflicts_with: A and B cannot both apply
- extends:       A adds to B (retrieve both)
- implements:    A is implementation of B (retrieve both)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from enum import Enum
from collections import defaultdict, deque


class RelationType(str, Enum):
    """Types of decision relationships."""
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"
    CONFLICTS_WITH = "conflicts_with"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"


@dataclass
class DependencyEdge:
    """Single dependency relationship."""
    source_id: str
    target_id: str
    relation_type: RelationType
    strength: str = "NORMAL"  # STRONG, NORMAL, WEAK
    context: Optional[str] = None


@dataclass
class DependencyNode:
    """Node in dependency graph."""
    decision_id: str
    outgoing: List[DependencyEdge] = field(default_factory=list)
    incoming: List[DependencyEdge] = field(default_factory=list)

    @property
    def depends_on(self) -> List[str]:
        return [e.target_id for e in self.outgoing if e.relation_type == RelationType.DEPENDS_ON]

    @property
    def supersedes(self) -> List[str]:
        return [e.target_id for e in self.outgoing if e.relation_type == RelationType.SUPERSEDES]

    @property
    def superseded_by(self) -> List[str]:
        return [e.source_id for e in self.incoming if e.relation_type == RelationType.SUPERSEDES]


class DependencyGraph:
    """
    Graph of decision dependencies.

    Enables efficient traversal and cycle detection.
    """

    def __init__(self):
        self._nodes: Dict[str, DependencyNode] = {}
        self._edges: List[DependencyEdge] = []

    def add_decision(self, decision_id: str):
        """Add decision node to graph."""
        if decision_id not in self._nodes:
            self._nodes[decision_id] = DependencyNode(decision_id=decision_id)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        strength: str = "NORMAL",
        context: Optional[str] = None,
    ):
        """Add relationship edge."""
        # Ensure nodes exist
        self.add_decision(source_id)
        self.add_decision(target_id)

        edge = DependencyEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            context=context,
        )

        self._edges.append(edge)
        self._nodes[source_id].outgoing.append(edge)
        self._nodes[target_id].incoming.append(edge)

    def get_node(self, decision_id: str) -> Optional[DependencyNode]:
        """Get node by decision ID."""
        return self._nodes.get(decision_id)

    def get_dependencies(
        self,
        decision_id: str,
        transitive: bool = True,
        max_depth: int = 5,
    ) -> List[str]:
        """
        Get all dependencies of a decision.

        Args:
            decision_id: Starting decision
            transitive: Include transitive dependencies
            max_depth: Maximum traversal depth

        Returns:
            List of dependent decision IDs
        """
        if decision_id not in self._nodes:
            return []

        if not transitive:
            return self._nodes[decision_id].depends_on

        # BFS for transitive dependencies
        visited = set()
        queue = deque([(decision_id, 0)])
        dependencies = []

        while queue:
            current_id, depth = queue.popleft()

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)

            node = self._nodes.get(current_id)
            if not node:
                continue

            for dep_id in node.depends_on:
                if dep_id not in visited:
                    dependencies.append(dep_id)
                    queue.append((dep_id, depth + 1))

        return dependencies

    def get_supersedes_chain(self, decision_id: str) -> List[str]:
        """Get chain of superseded decisions (newest to oldest)."""
        chain = []
        current = decision_id

        visited = set()
        while current and current not in visited:
            visited.add(current)
            node = self._nodes.get(current)
            if not node:
                break

            supersedes = node.supersedes
            if supersedes:
                chain.extend(supersedes)
                current = supersedes[0]  # Follow first
            else:
                break

        return chain

    def get_latest_version(self, decision_id: str) -> str:
        """Get latest version (newest in supersedes chain)."""
        node = self._nodes.get(decision_id)
        if not node:
            return decision_id

        superseded_by = node.superseded_by
        if superseded_by:
            # Recursively find latest
            return self.get_latest_version(superseded_by[0])

        return decision_id

    def detect_cycle(self, decision_id: str) -> Optional[List[str]]:
        """
        Detect if adding this decision creates a cycle.

        Returns cycle path if found, None otherwise.
        """
        visited = set()
        path = []

        def dfs(node_id: str) -> Optional[List[str]]:
            if node_id in path:
                # Found cycle
                cycle_start = path.index(node_id)
                return path[cycle_start:] + [node_id]

            if node_id in visited:
                return None

            visited.add(node_id)
            path.append(node_id)

            node = self._nodes.get(node_id)
            if node:
                for edge in node.outgoing:
                    if edge.relation_type in (RelationType.DEPENDS_ON, RelationType.SUPERSEDES):
                        cycle = dfs(edge.target_id)
                        if cycle:
                            return cycle

            path.pop()
            return None

        return dfs(decision_id)

    def get_conflicts(self, decision_id: str) -> List[str]:
        """Get decisions that conflict with this one."""
        node = self._nodes.get(decision_id)
        if not node:
            return []

        conflicts = []
        for edge in node.outgoing:
            if edge.relation_type == RelationType.CONFLICTS_WITH:
                conflicts.append(edge.target_id)

        for edge in node.incoming:
            if edge.relation_type == RelationType.CONFLICTS_WITH:
                conflicts.append(edge.source_id)

        return list(set(conflicts))

    def build_from_decisions(self, decisions: List[Dict[str, Any]]):
        """Build graph from list of decisions."""
        # First pass: add all nodes
        for decision in decisions:
            decision_id = decision.get("decision_id")
            if decision_id:
                self.add_decision(decision_id)

        # Second pass: add edges
        for decision in decisions:
            decision_id = decision.get("decision_id")
            if not decision_id:
                continue

            # Supersedes
            supersedes = decision.get("supersedes")
            if supersedes:
                self.add_edge(decision_id, supersedes, RelationType.SUPERSEDES)

            # Relations
            relations = decision.get("relations", [])
            for rel in relations:
                target_id = rel.get("target_id")
                rel_type = rel.get("type", "depends_on")

                if target_id and rel_type in RelationType.__members__:
                    self.add_edge(
                        decision_id,
                        target_id,
                        RelationType(rel_type),
                        strength=rel.get("strength", "NORMAL"),
                        context=rel.get("context"),
                    )

            # Related decisions (legacy, treat as weak depends_on)
            related = decision.get("related_decisions", [])
            for rel_id in related:
                if rel_id != decision_id:
                    self.add_edge(decision_id, rel_id, RelationType.DEPENDS_ON, "WEAK")


class DependencyResolver:
    """
    Resolves dependencies for retrieval.

    Given a set of matched decisions, expands to include
    necessary dependencies.
    """

    def __init__(self, graph: DependencyGraph):
        self.graph = graph

    def resolve(
        self,
        decision_ids: List[str],
        include_dependencies: bool = True,
        include_superseded: bool = False,
        prefer_latest: bool = True,
        max_total: int = 20,
    ) -> List[str]:
        """
        Resolve full set of decisions to retrieve.

        Args:
            decision_ids: Initially matched decisions
            include_dependencies: Add dependency decisions
            include_superseded: Include superseded versions
            prefer_latest: Replace with latest version
            max_total: Maximum total decisions

        Returns:
            Resolved list of decision IDs
        """
        resolved = set()
        to_process = list(decision_ids)

        while to_process and len(resolved) < max_total:
            decision_id = to_process.pop(0)

            if decision_id in resolved:
                continue

            # Prefer latest version
            if prefer_latest:
                latest = self.graph.get_latest_version(decision_id)
                if latest != decision_id:
                    decision_id = latest

            resolved.add(decision_id)

            # Add dependencies
            if include_dependencies:
                deps = self.graph.get_dependencies(decision_id, transitive=True)
                for dep_id in deps:
                    if dep_id not in resolved:
                        to_process.append(dep_id)

            # Add superseded (if requested)
            if include_superseded:
                chain = self.graph.get_supersedes_chain(decision_id)
                for old_id in chain:
                    if old_id not in resolved and len(resolved) < max_total:
                        resolved.add(old_id)

        return list(resolved)[:max_total]

    def check_conflicts(self, decision_ids: List[str]) -> List[Tuple[str, str]]:
        """
        Check for conflicts in a set of decisions.

        Returns list of conflicting pairs.
        """
        conflicts = []
        id_set = set(decision_ids)

        for decision_id in decision_ids:
            conflicting = self.graph.get_conflicts(decision_id)
            for conflict_id in conflicting:
                if conflict_id in id_set:
                    pair = tuple(sorted([decision_id, conflict_id]))
                    if pair not in conflicts:
                        conflicts.append(pair)

        return conflicts

    def get_retrieval_order(self, decision_ids: List[str]) -> List[str]:
        """
        Order decisions for optimal context injection.

        More fundamental decisions first, then specific ones.
        """
        # Calculate depth (how many dependencies each has)
        depths = {}
        for decision_id in decision_ids:
            deps = self.graph.get_dependencies(decision_id, transitive=True)
            depths[decision_id] = len([d for d in deps if d in decision_ids])

        # Sort by depth (fewer dependencies first)
        return sorted(decision_ids, key=lambda x: depths.get(x, 0))


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "RelationType",
    "DependencyEdge",
    "DependencyNode",
    "DependencyGraph",
    "DependencyResolver",
]
