"""
MANTRA Dependency Validation

Validates dependency graphs to prevent:
1. Circular dependencies (A → B → C → A)
2. Self-references (A → A)
3. Missing references (A → X where X doesn't exist)
4. Excessive depth (A → B → C → ... → Z, depth > limit)

ALGORITHM:
Uses DFS-based cycle detection with path tracking.
Time complexity: O(V + E) where V = decisions, E = depends_on edges.
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DependencyError(Exception):
    """Base exception for dependency validation errors."""
    pass


class CyclicDependencyError(DependencyError):
    """Raised when a cyclic dependency is detected."""
    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        cycle_str = " → ".join(cycle_path)
        super().__init__(f"Cyclic dependency detected: {cycle_str}")


class SelfReferenceError(DependencyError):
    """Raised when a decision references itself."""
    def __init__(self, decision_id: str):
        self.decision_id = decision_id
        super().__init__(f"Decision cannot reference itself: {decision_id}")


class MissingReferenceError(DependencyError):
    """Raised when a dependency references a non-existent decision."""
    def __init__(self, source_id: str, missing_id: str):
        self.source_id = source_id
        self.missing_id = missing_id
        super().__init__(f"Decision {source_id} depends on non-existent decision: {missing_id}")


class ExcessiveDepthError(DependencyError):
    """Raised when dependency chain exceeds maximum depth."""
    def __init__(self, decision_id: str, depth: int, max_depth: int):
        self.decision_id = decision_id
        self.depth = depth
        self.max_depth = max_depth
        super().__init__(f"Decision {decision_id} has dependency depth {depth} exceeding maximum {max_depth}")


class ValidationSeverity(str, Enum):
    """Severity of dependency validation issues."""
    ERROR = "ERROR"      # Must be fixed
    WARNING = "WARNING"  # Should be reviewed
    INFO = "INFO"        # Informational


@dataclass
class DependencyIssue:
    """Single dependency validation issue."""
    severity: ValidationSeverity
    issue_type: str
    message: str
    affected_decisions: List[str]
    suggestion: Optional[str] = None


@dataclass
class DependencyValidationResult:
    """Result of dependency validation."""
    is_valid: bool
    issues: List[DependencyIssue] = field(default_factory=list)
    cycle_paths: List[List[str]] = field(default_factory=list)
    missing_references: List[Tuple[str, str]] = field(default_factory=list)
    max_depth_found: int = 0
    graph_stats: Dict[str, int] = field(default_factory=dict)

    def has_errors(self) -> bool:
        """Check if there are any ERROR severity issues."""
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    def has_warnings(self) -> bool:
        """Check if there are any WARNING severity issues."""
        return any(i.severity == ValidationSeverity.WARNING for i in self.issues)


class DependencyValidator:
    """
    Validates decision dependency graphs.

    Usage:
        validator = DependencyValidator()

        # Validate before adding new decision
        result = validator.validate_new_dependency(
            decision_id="dec-new",
            depends_on=["dec-001", "dec-002"],
            existing_graph={"dec-001": ["dec-003"], "dec-002": [], "dec-003": []}
        )

        if not result.is_valid:
            raise DependencyError(result.issues[0].message)
    """

    DEFAULT_MAX_DEPTH = 10

    def __init__(self, max_depth: int = DEFAULT_MAX_DEPTH):
        """
        Initialize validator.

        Args:
            max_depth: Maximum allowed dependency chain depth
        """
        self.max_depth = max_depth

    def validate_graph(
        self,
        graph: Dict[str, List[str]],
        check_missing: bool = True,
    ) -> DependencyValidationResult:
        """
        Validate entire dependency graph.

        Args:
            graph: {decision_id: [depends_on_ids]}
            check_missing: Whether to check for missing references

        Returns:
            DependencyValidationResult
        """
        issues = []
        cycle_paths = []
        missing_refs = []
        max_depth_found = 0

        all_nodes = set(graph.keys())

        # Check for self-references
        for node, deps in graph.items():
            if node in deps:
                issues.append(DependencyIssue(
                    severity=ValidationSeverity.ERROR,
                    issue_type="SELF_REFERENCE",
                    message=f"Decision {node} references itself",
                    affected_decisions=[node],
                    suggestion="Remove self-reference from depends_on",
                ))

        # Check for missing references
        if check_missing:
            for node, deps in graph.items():
                for dep in deps:
                    if dep not in all_nodes:
                        missing_refs.append((node, dep))
                        issues.append(DependencyIssue(
                            severity=ValidationSeverity.ERROR,
                            issue_type="MISSING_REFERENCE",
                            message=f"Decision {node} depends on non-existent decision {dep}",
                            affected_decisions=[node, dep],
                            suggestion=f"Create decision {dep} or remove from depends_on",
                        ))

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def dfs_detect_cycle(node: str, path: List[str]) -> Optional[List[str]]:
            """DFS to detect cycle, returns cycle path if found."""
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]

            if node in visited:
                return None

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor in all_nodes:  # Only traverse existing nodes
                    cycle = dfs_detect_cycle(neighbor, path)
                    if cycle:
                        return cycle

            path.pop()
            rec_stack.remove(node)
            return None

        for node in graph:
            if node not in visited:
                cycle = dfs_detect_cycle(node, [])
                if cycle:
                    cycle_paths.append(cycle)
                    issues.append(DependencyIssue(
                        severity=ValidationSeverity.ERROR,
                        issue_type="CYCLIC_DEPENDENCY",
                        message=f"Cyclic dependency: {' → '.join(cycle)}",
                        affected_decisions=cycle,
                        suggestion="Break the cycle by removing one dependency",
                    ))

        # Calculate depths
        depth_cache: Dict[str, int] = {}

        def calculate_depth(node: str, seen: Set[str]) -> int:
            """Calculate dependency depth for a node."""
            if node in depth_cache:
                return depth_cache[node]

            if node in seen:
                return 0  # Cycle, handled separately

            seen.add(node)
            deps = graph.get(node, [])
            if not deps:
                depth = 0
            else:
                max_child_depth = 0
                for dep in deps:
                    if dep in all_nodes:
                        child_depth = calculate_depth(dep, seen)
                        max_child_depth = max(max_child_depth, child_depth)
                depth = max_child_depth + 1

            seen.remove(node)
            depth_cache[node] = depth
            return depth

        for node in graph:
            depth = calculate_depth(node, set())
            max_depth_found = max(max_depth_found, depth)

            if depth > self.max_depth:
                issues.append(DependencyIssue(
                    severity=ValidationSeverity.WARNING,
                    issue_type="EXCESSIVE_DEPTH",
                    message=f"Decision {node} has dependency depth {depth} (max recommended: {self.max_depth})",
                    affected_decisions=[node],
                    suggestion="Consider flattening dependency chain",
                ))

        # Calculate graph stats
        total_edges = sum(len(deps) for deps in graph.values())
        orphan_nodes = [n for n in graph if not graph.get(n) and not any(n in deps for deps in graph.values())]

        graph_stats = {
            "total_nodes": len(graph),
            "total_edges": total_edges,
            "max_depth": max_depth_found,
            "orphan_nodes": len(orphan_nodes),
            "cycles_found": len(cycle_paths),
            "missing_refs": len(missing_refs),
        }

        is_valid = not any(i.severity == ValidationSeverity.ERROR for i in issues)

        return DependencyValidationResult(
            is_valid=is_valid,
            issues=issues,
            cycle_paths=cycle_paths,
            missing_references=missing_refs,
            max_depth_found=max_depth_found,
            graph_stats=graph_stats,
        )

    def validate_new_dependency(
        self,
        decision_id: str,
        depends_on: List[str],
        existing_graph: Dict[str, List[str]],
        check_missing: bool = True,
    ) -> DependencyValidationResult:
        """
        Validate adding a new decision with dependencies.

        This is the main entry point for write-time validation.

        Args:
            decision_id: ID of new decision being added
            depends_on: Dependencies for the new decision
            existing_graph: Current dependency graph
            check_missing: Whether to check for missing references

        Returns:
            DependencyValidationResult
        """
        issues = []

        # Check self-reference first
        if decision_id in depends_on:
            issues.append(DependencyIssue(
                severity=ValidationSeverity.ERROR,
                issue_type="SELF_REFERENCE",
                message=f"Decision cannot depend on itself",
                affected_decisions=[decision_id],
                suggestion="Remove self from depends_on list",
            ))
            return DependencyValidationResult(
                is_valid=False,
                issues=issues,
            )

        # Build temporary graph with new decision
        temp_graph = {k: list(v) for k, v in existing_graph.items()}
        temp_graph[decision_id] = list(depends_on)

        # Validate the complete graph
        result = self.validate_graph(temp_graph, check_missing=check_missing)

        # Add specific note if new decision caused the issue
        if not result.is_valid:
            for issue in result.issues:
                if decision_id in issue.affected_decisions:
                    issue.message = f"[NEW DECISION] {issue.message}"

        return result

    def would_create_cycle(
        self,
        decision_id: str,
        new_dependency: str,
        existing_graph: Dict[str, List[str]],
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Quick check if adding a dependency would create a cycle.

        More efficient than full validation when just checking one edge.

        Args:
            decision_id: Decision that would gain the dependency
            new_dependency: Decision to depend on
            existing_graph: Current dependency graph

        Returns:
            (would_create_cycle, cycle_path_if_yes)
        """
        # Would create self-reference?
        if decision_id == new_dependency:
            return True, [decision_id, decision_id]

        # Would create cycle? Check if new_dependency can reach decision_id
        visited = set()

        def can_reach(start: str, target: str) -> List[str]:
            """Check if start can reach target, return path if yes."""
            if start == target:
                return [start]

            if start in visited:
                return []

            visited.add(start)

            for dep in existing_graph.get(start, []):
                path = can_reach(dep, target)
                if path:
                    return [start] + path

            return []

        # If new_dependency can currently reach decision_id,
        # then adding decision_id → new_dependency would create cycle
        path = can_reach(new_dependency, decision_id)

        if path:
            # Cycle would be: decision_id → new_dependency → ... → decision_id
            cycle_path = [decision_id] + path + [decision_id]
            return True, cycle_path

        return False, None

    def get_dependency_depth(
        self,
        decision_id: str,
        graph: Dict[str, List[str]],
    ) -> int:
        """
        Get the dependency depth of a decision.

        Depth 0 = no dependencies
        Depth 1 = depends on decisions with no dependencies
        etc.
        """
        visited = set()

        def calculate(node: str) -> int:
            if node in visited:
                return 0  # Cycle, return 0 to not inflate depth

            visited.add(node)
            deps = graph.get(node, [])

            if not deps:
                visited.remove(node)
                return 0

            max_child = max(calculate(d) for d in deps if d in graph)
            visited.remove(node)
            return max_child + 1

        return calculate(decision_id)

    def get_dependents(
        self,
        decision_id: str,
        graph: Dict[str, List[str]],
    ) -> List[str]:
        """
        Get all decisions that depend on the given decision.

        Useful for impact analysis.
        """
        dependents = []
        for node, deps in graph.items():
            if decision_id in deps:
                dependents.append(node)
        return dependents

    def get_transitive_dependencies(
        self,
        decision_id: str,
        graph: Dict[str, List[str]],
    ) -> Set[str]:
        """
        Get all transitive dependencies (recursive).

        Returns all decisions that decision_id depends on,
        directly or indirectly.
        """
        result = set()
        visited = set()

        def collect(node: str):
            if node in visited:
                return
            visited.add(node)

            for dep in graph.get(node, []):
                if dep in graph:
                    result.add(dep)
                    collect(dep)

        collect(decision_id)
        return result


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def validate_dependencies(
    decision_id: str,
    depends_on: List[str],
    existing_decisions: Dict[str, List[str]],
    strict: bool = True,
) -> None:
    """
    Validate dependencies or raise exception.

    This is the simplest API for write-time validation.

    Args:
        decision_id: New decision ID
        depends_on: Dependencies to add
        existing_decisions: Current graph
        strict: If True, raise on any ERROR. If False, only raise on cycles.

    Raises:
        CyclicDependencyError: If cycle would be created
        SelfReferenceError: If self-reference detected
        MissingReferenceError: If dependency doesn't exist (only if strict)
    """
    # Quick self-reference check
    if decision_id in depends_on:
        raise SelfReferenceError(decision_id)

    validator = DependencyValidator()

    # Quick cycle check first
    for dep in depends_on:
        would_cycle, path = validator.would_create_cycle(decision_id, dep, existing_decisions)
        if would_cycle:
            raise CyclicDependencyError(path)

    # Full validation if strict
    if strict:
        result = validator.validate_new_dependency(
            decision_id=decision_id,
            depends_on=depends_on,
            existing_graph=existing_decisions,
            check_missing=True,
        )

        if not result.is_valid:
            # Raise first error
            for issue in result.issues:
                if issue.severity == ValidationSeverity.ERROR:
                    if issue.issue_type == "MISSING_REFERENCE":
                        # Extract missing ref
                        for src, missing in result.missing_references:
                            if src == decision_id:
                                raise MissingReferenceError(src, missing)
                    raise DependencyError(issue.message)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Exceptions
    "DependencyError",
    "CyclicDependencyError",
    "SelfReferenceError",
    "MissingReferenceError",
    "ExcessiveDepthError",
    # Enums/Dataclasses
    "ValidationSeverity",
    "DependencyIssue",
    "DependencyValidationResult",
    # Validator
    "DependencyValidator",
    # Functions
    "validate_dependencies",
]
