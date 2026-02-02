"""
Scope DAG (Directed Acyclic Graph) Model

Supports hierarchical scopes with:
- Multiple parents (shared child: api under both FE and BE)
- Multiple children (umbrella: architecture above FE and BE)
- Inheritance (decisions flow down)
- Wildcard matching (*.api matches fe.api and be.api)

Structure Example:
                    project
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   architecture       fe             be
   (umbrella)          │              │
        │         ┌────┴────┐    ┌────┴────┐
        │         ▼    ▼    ▼    ▼    ▼    ▼
        │       api  state  ui  api  db  service
        │         │              │
        └─────────┴──────────────┘
                  │
           Shared concepts

Usage:
    from core.domain.scope_dag import ScopeTree, ScopeNode, InheritanceType

    tree = ScopeTree()
    tree.add_node("fe", parents=["project"])
    tree.add_node("api", parents=["fe", "be"])  # Multiple parents!

    # Get all ancestors (for inheritance)
    ancestors = tree.get_ancestors("fe.api")  # ["fe", "project"]

    # Get all descendants (for umbrella decisions)
    descendants = tree.get_descendants("architecture")  # ["fe", "be", ...]
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple
from enum import Enum
import re


# =============================================================================
# ENUMS
# =============================================================================

class InheritanceType(str, Enum):
    """How a decision's scope inherits."""
    UMBRELLA = "umbrella"        # Above multiple branches, inherits DOWN
    SHARED_CHILD = "shared_child"  # Under multiple parents
    LEAF = "leaf"                # Single path, no special inheritance
    WILDCARD = "wildcard"        # Uses * pattern


class ScopeRelation(str, Enum):
    """Relationship between two scopes."""
    SAME = "same"                # Exact match
    ANCESTOR = "ancestor"        # A is ancestor of B
    DESCENDANT = "descendant"    # A is descendant of B
    SIBLING = "sibling"          # Share common parent
    UNRELATED = "unrelated"      # No direct relationship
    OVERLAPPING = "overlapping"  # Partial overlap (DAG)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ScopeNode:
    """
    A node in the scope DAG.

    Attributes:
        id: Unique identifier (e.g., "fe", "api", "react")
        label: Human-readable label
        description: What this scope covers
        parents: Parent node IDs (can have multiple for DAG)
        children: Child node IDs
        aliases: Alternative names for matching
        tags: Additional tags for categorization
    """
    id: str
    label: str
    description: str = ""
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Ensure no self-reference
        if self.id in self.parents:
            raise ValueError(f"Node {self.id} cannot be its own parent")
        if self.id in self.children:
            raise ValueError(f"Node {self.id} cannot be its own child")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "parents": self.parents,
            "children": self.children,
            "aliases": self.aliases,
            "tags": self.tags,
        }


@dataclass
class InheritanceInfo:
    """
    Describes how a decision's scope inherits.

    Used by AI retriever to understand scope relationships.
    """
    type: InheritanceType
    primary_scope: str
    alternative_scopes: List[str] = field(default_factory=list)
    affects: List[str] = field(default_factory=list)  # What scopes are affected
    affected_by: List[str] = field(default_factory=list)  # What scopes affect this
    description: str = ""  # Human-readable for AI

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "primary_scope": self.primary_scope,
            "alternative_scopes": self.alternative_scopes,
            "affects": self.affects,
            "affected_by": self.affected_by,
            "description": self.description,
        }


@dataclass
class ScopeDefinition:
    """
    Complete scope definition for a decision.

    This is what gets stored with each decision.
    """
    # Primary scope path (what user inputs)
    primary_path: str

    # Alternative paths (for shared child scenarios)
    alternative_paths: List[str] = field(default_factory=list)

    # Inheritance type
    inheritance_type: InheritanceType = InheritanceType.LEAF

    # PRE-COMPUTED: All paths this decision applies to (for AI retrieval)
    applies_to: List[str] = field(default_factory=list)

    # Human-readable description (for AI context)
    applies_to_description: str = ""

    # Inheritance info
    inheritance_info: Optional[InheritanceInfo] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_path": self.primary_path,
            "alternative_paths": self.alternative_paths,
            "inheritance_type": self.inheritance_type.value,
            "applies_to": self.applies_to,
            "applies_to_description": self.applies_to_description,
            "inheritance_info": self.inheritance_info.to_dict() if self.inheritance_info else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScopeDefinition":
        inheritance_info = None
        if data.get("inheritance_info"):
            info = data["inheritance_info"]
            inheritance_info = InheritanceInfo(
                type=InheritanceType(info["type"]),
                primary_scope=info["primary_scope"],
                alternative_scopes=info.get("alternative_scopes", []),
                affects=info.get("affects", []),
                affected_by=info.get("affected_by", []),
                description=info.get("description", ""),
            )

        return cls(
            primary_path=data["primary_path"],
            alternative_paths=data.get("alternative_paths", []),
            inheritance_type=InheritanceType(data.get("inheritance_type", "leaf")),
            applies_to=data.get("applies_to", []),
            applies_to_description=data.get("applies_to_description", ""),
            inheritance_info=inheritance_info,
        )


# =============================================================================
# SCOPE TREE (DAG)
# =============================================================================

class ScopeTree:
    """
    Directed Acyclic Graph for scope hierarchy.

    Supports:
    - Multiple parents per node (shared child)
    - Multiple children per node (umbrella)
    - Path-based access (fe.api.rest)
    - Wildcard matching (*.api)
    """

    def __init__(self):
        self._nodes: Dict[str, ScopeNode] = {}
        self._path_cache: Dict[str, List[str]] = {}  # Cache for path lookups

    # =========================================================================
    # Node Management
    # =========================================================================

    def add_node(
        self,
        node_id: str,
        label: Optional[str] = None,
        description: str = "",
        parents: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> ScopeNode:
        """
        Add a node to the tree.

        Args:
            node_id: Unique identifier
            label: Human-readable label (defaults to node_id)
            description: What this scope covers
            parents: Parent node IDs
            aliases: Alternative names
            tags: Categorization tags

        Returns:
            Created ScopeNode
        """
        if node_id in self._nodes:
            raise ValueError(f"Node {node_id} already exists")

        parents = parents or []
        aliases = aliases or []
        tags = tags or []

        # Validate parents exist
        for parent_id in parents:
            if parent_id not in self._nodes:
                raise ValueError(f"Parent node {parent_id} does not exist")

        node = ScopeNode(
            id=node_id,
            label=label or node_id.replace("_", " ").title(),
            description=description,
            parents=parents,
            children=[],
            aliases=aliases,
            tags=tags,
        )

        self._nodes[node_id] = node

        # Update parent's children
        for parent_id in parents:
            if node_id not in self._nodes[parent_id].children:
                self._nodes[parent_id].children.append(node_id)

        # Clear cache
        self._path_cache.clear()

        return node

    def get_node(self, node_id: str) -> Optional[ScopeNode]:
        """Get node by ID."""
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        return node_id in self._nodes

    def get_all_nodes(self) -> List[ScopeNode]:
        """Get all nodes."""
        return list(self._nodes.values())

    # =========================================================================
    # Path Operations
    # =========================================================================

    def parse_path(self, path: str) -> List[str]:
        """
        Parse a scope path into node IDs.

        Args:
            path: Dot-separated path (e.g., "fe.api.rest")

        Returns:
            List of node IDs
        """
        if not path or path == "*":
            return []
        return path.split(".")

    def build_path(self, node_ids: List[str]) -> str:
        """Build path from node IDs."""
        return ".".join(node_ids)

    def get_node_by_path(self, path: str) -> Optional[ScopeNode]:
        """
        Get node by full path.

        Args:
            path: Dot-separated path

        Returns:
            ScopeNode at the path's leaf, or None
        """
        parts = self.parse_path(path)
        if not parts:
            return None
        return self.get_node(parts[-1])

    def path_exists(self, path: str) -> bool:
        """Check if a path is valid in the tree."""
        parts = self.parse_path(path)
        if not parts:
            return True  # Root/wildcard

        # Check each node exists
        for part in parts:
            if part != "*" and not self.has_node(part):
                return False

        # Verify parent-child relationships
        for i in range(1, len(parts)):
            parent_id = parts[i - 1]
            child_id = parts[i]

            if parent_id == "*" or child_id == "*":
                continue

            parent = self.get_node(parent_id)
            if parent and child_id not in parent.children:
                return False

        return True

    # =========================================================================
    # Ancestor/Descendant Operations
    # =========================================================================

    def get_ancestors(self, node_id: str, include_self: bool = False) -> List[str]:
        """
        Get all ancestors of a node (parents, grandparents, etc.).

        For DAG, this returns all paths to root.

        Args:
            node_id: Node to get ancestors for
            include_self: Include the node itself

        Returns:
            List of ancestor node IDs (closest first)
        """
        if node_id not in self._nodes:
            return []

        ancestors: List[str] = []
        if include_self:
            ancestors.append(node_id)

        visited: Set[str] = set()
        to_visit = list(self._nodes[node_id].parents)

        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)
            ancestors.append(current)

            node = self._nodes.get(current)
            if node:
                to_visit.extend(node.parents)

        return ancestors

    def get_descendants(self, node_id: str, include_self: bool = False) -> List[str]:
        """
        Get all descendants of a node (children, grandchildren, etc.).

        Args:
            node_id: Node to get descendants for
            include_self: Include the node itself

        Returns:
            List of descendant node IDs (closest first)
        """
        if node_id not in self._nodes:
            return []

        descendants: List[str] = []
        if include_self:
            descendants.append(node_id)

        visited: Set[str] = set()
        to_visit = list(self._nodes[node_id].children)

        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)
            descendants.append(current)

            node = self._nodes.get(current)
            if node:
                to_visit.extend(node.children)

        return descendants

    def get_all_paths_to_node(self, node_id: str) -> List[List[str]]:
        """
        Get all paths from roots to a node.

        For DAG, a node can have multiple paths.

        Args:
            node_id: Target node

        Returns:
            List of paths (each path is a list of node IDs)
        """
        if node_id not in self._nodes:
            return []

        node = self._nodes[node_id]

        # Base case: root node
        if not node.parents:
            return [[node_id]]

        # Recursive: get paths through each parent
        all_paths: List[List[str]] = []
        for parent_id in node.parents:
            parent_paths = self.get_all_paths_to_node(parent_id)
            for path in parent_paths:
                all_paths.append(path + [node_id])

        return all_paths

    # =========================================================================
    # Relationship Operations
    # =========================================================================

    def get_relationship(self, node_a: str, node_b: str) -> ScopeRelation:
        """
        Determine relationship between two nodes.

        Args:
            node_a: First node ID
            node_b: Second node ID

        Returns:
            ScopeRelation enum
        """
        if node_a == node_b:
            return ScopeRelation.SAME

        if node_a not in self._nodes or node_b not in self._nodes:
            return ScopeRelation.UNRELATED

        # Check if A is ancestor of B
        ancestors_of_b = self.get_ancestors(node_b)
        if node_a in ancestors_of_b:
            return ScopeRelation.ANCESTOR

        # Check if A is descendant of B
        ancestors_of_a = self.get_ancestors(node_a)
        if node_b in ancestors_of_a:
            return ScopeRelation.DESCENDANT

        # Check for siblings (share parent)
        parents_a = set(self._nodes[node_a].parents)
        parents_b = set(self._nodes[node_b].parents)
        if parents_a & parents_b:
            return ScopeRelation.SIBLING

        # Check for overlapping (share ancestor but not siblings)
        ancestors_a = set(ancestors_of_a)
        ancestors_b = set(ancestors_of_b)
        if ancestors_a & ancestors_b:
            return ScopeRelation.OVERLAPPING

        return ScopeRelation.UNRELATED

    def get_common_ancestors(self, node_a: str, node_b: str) -> List[str]:
        """Get common ancestors of two nodes."""
        ancestors_a = set(self.get_ancestors(node_a))
        ancestors_b = set(self.get_ancestors(node_b))
        return list(ancestors_a & ancestors_b)

    # =========================================================================
    # Wildcard Operations
    # =========================================================================

    def expand_wildcard(self, pattern: str) -> List[str]:
        """
        Expand a wildcard pattern to all matching paths.

        Patterns:
        - "*" → All root nodes
        - "*.api" → All nodes named "api" under any parent
        - "fe.*" → All children of "fe"
        - "fe.*.component" → All "component" nodes under fe's children

        Args:
            pattern: Pattern with * wildcards

        Returns:
            List of matching full paths
        """
        if pattern == "*":
            # Return all root nodes
            return [n.id for n in self._nodes.values() if not n.parents]

        parts = pattern.split(".")
        matches: List[List[str]] = [[]]  # Start with empty path

        for part in parts:
            new_matches: List[List[str]] = []

            for current_path in matches:
                if part == "*":
                    # Wildcard: expand to all valid children
                    if not current_path:
                        # At root: get all root nodes
                        for node in self._nodes.values():
                            if not node.parents:
                                new_matches.append([node.id])
                    else:
                        # Get all children of current node
                        parent = self._nodes.get(current_path[-1])
                        if parent:
                            for child_id in parent.children:
                                new_matches.append(current_path + [child_id])
                else:
                    # Exact match
                    if not current_path:
                        # At root: check if node exists
                        if part in self._nodes:
                            new_matches.append([part])
                    else:
                        # Check if this is a valid child
                        parent = self._nodes.get(current_path[-1])
                        if parent and part in parent.children:
                            new_matches.append(current_path + [part])

            matches = new_matches

        return [self.build_path(path) for path in matches]

    def matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches a wildcard pattern.

        Args:
            path: Full path to check
            pattern: Pattern (may contain *)

        Returns:
            True if path matches pattern
        """
        if pattern == "*":
            return True

        path_parts = path.split(".")
        pattern_parts = pattern.split(".")

        if len(path_parts) != len(pattern_parts):
            return False

        for p_part, pat_part in zip(path_parts, pattern_parts):
            if pat_part != "*" and p_part != pat_part:
                return False

        return True

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tree to dictionary."""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self._nodes.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScopeTree":
        """Deserialize tree from dictionary."""
        tree = cls()

        # First pass: create all nodes without parents
        nodes_data = data.get("nodes", {})
        for node_id, node_data in nodes_data.items():
            # Temporarily create without parents to avoid dependency issues
            tree._nodes[node_id] = ScopeNode(
                id=node_id,
                label=node_data.get("label", node_id),
                description=node_data.get("description", ""),
                parents=[],
                children=[],
                aliases=node_data.get("aliases", []),
                tags=node_data.get("tags", []),
            )

        # Second pass: set up relationships
        for node_id, node_data in nodes_data.items():
            node = tree._nodes[node_id]
            node.parents = node_data.get("parents", [])
            node.children = node_data.get("children", [])

        return tree


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def determine_inheritance_type(
    tree: ScopeTree,
    scope_paths: List[str],
) -> InheritanceType:
    """
    Determine the inheritance type based on scope paths.

    Args:
        tree: Scope tree
        scope_paths: List of scope paths for a decision

    Returns:
        InheritanceType
    """
    if not scope_paths:
        return InheritanceType.LEAF

    # Check for wildcards
    if any("*" in path for path in scope_paths):
        return InheritanceType.WILDCARD

    # Check for multiple paths (shared child)
    if len(scope_paths) > 1:
        return InheritanceType.SHARED_CHILD

    # Single path - check if it has multiple children (umbrella)
    path = scope_paths[0]
    parts = path.split(".")
    if parts:
        node = tree.get_node(parts[-1])
        if node and len(node.children) > 1:
            return InheritanceType.UMBRELLA

    return InheritanceType.LEAF


def create_scope_definition(
    tree: ScopeTree,
    primary_path: str,
    alternative_paths: Optional[List[str]] = None,
) -> ScopeDefinition:
    """
    Create a complete ScopeDefinition with pre-computed fields.

    Args:
        tree: Scope tree
        primary_path: Primary scope path
        alternative_paths: Alternative scope paths

    Returns:
        ScopeDefinition with all fields populated
    """
    alternative_paths = alternative_paths or []
    all_paths = [primary_path] + alternative_paths

    # Determine inheritance type
    inheritance_type = determine_inheritance_type(tree, all_paths)

    # Compute applies_to
    applies_to: Set[str] = set()

    for path in all_paths:
        if "*" in path:
            # Expand wildcard
            expanded = tree.expand_wildcard(path)
            applies_to.update(expanded)
        else:
            applies_to.add(path)

            # Add all descendant paths
            parts = path.split(".")
            if parts:
                leaf_node = parts[-1]
                descendants = tree.get_descendants(leaf_node)
                for desc in descendants:
                    # Build full path
                    desc_path = path + "." + desc
                    applies_to.add(desc_path)

    # Build inheritance info
    affects = list(applies_to - set(all_paths))
    affected_by = []

    for path in all_paths:
        parts = path.split(".")
        if parts:
            ancestors = tree.get_ancestors(parts[-1])
            affected_by.extend(ancestors)

    # Generate description
    description = generate_applies_to_description(
        primary_path,
        alternative_paths,
        inheritance_type,
        list(applies_to),
    )

    inheritance_info = InheritanceInfo(
        type=inheritance_type,
        primary_scope=primary_path,
        alternative_scopes=alternative_paths,
        affects=affects,
        affected_by=list(set(affected_by)),
        description=description,
    )

    return ScopeDefinition(
        primary_path=primary_path,
        alternative_paths=alternative_paths,
        inheritance_type=inheritance_type,
        applies_to=sorted(applies_to),
        applies_to_description=description,
        inheritance_info=inheritance_info,
    )


def generate_applies_to_description(
    primary_path: str,
    alternative_paths: List[str],
    inheritance_type: InheritanceType,
    applies_to: List[str],
) -> str:
    """
    Generate human-readable description for AI context.

    Args:
        primary_path: Primary scope
        alternative_paths: Alternative scopes
        inheritance_type: Type of inheritance
        applies_to: Expanded list of applicable scopes

    Returns:
        Human-readable description
    """
    all_paths = [primary_path] + alternative_paths

    if inheritance_type == InheritanceType.UMBRELLA:
        return f"Applies to {primary_path} and all code underneath it (umbrella decision)"

    if inheritance_type == InheritanceType.SHARED_CHILD:
        paths_str = ", ".join(all_paths)
        return f"Applies to multiple areas: {paths_str}"

    if inheritance_type == InheritanceType.WILDCARD:
        return f"Applies to all paths matching pattern: {primary_path}"

    if inheritance_type == InheritanceType.LEAF:
        if len(applies_to) > 1:
            return f"Applies specifically to {primary_path} and its children"
        return f"Applies specifically to {primary_path}"

    return f"Applies to {primary_path}"


__all__ = [
    # Enums
    "InheritanceType",
    "ScopeRelation",
    # Data classes
    "ScopeNode",
    "InheritanceInfo",
    "ScopeDefinition",
    # Main class
    "ScopeTree",
    # Functions
    "determine_inheritance_type",
    "create_scope_definition",
    "generate_applies_to_description",
]
