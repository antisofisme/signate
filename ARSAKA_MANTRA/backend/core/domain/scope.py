"""
MANTRA Hierarchical Scoping System

Provides hierarchical scope paths for decisions to minimize conflicts.

SCOPE PATH FORMAT:
    layer.technology.sublayer.specific

EXAMPLES:
    fe.react.components.forms
    fe.react.css.tailwind
    be.python.fastapi.auth
    be.go.api.handlers
    infra.docker.compose
    shared.utils.validation

RULES:
1. Scope paths are dot-separated
2. Each segment is lowercase alphanumeric + underscore
3. Wildcards (*) match any segment at that level
4. Decisions in same/parent/child scope CAN conflict
5. Decisions in different branches CANNOT conflict

INHERITANCE:
- scope_inheritance=True: Decision applies to all descendants
- scope_inheritance=False: Decision only applies to exact scope

CONFLICT LOGIC:
    fe.react.css vs fe.react.css.tailwind → CAN conflict (parent-child)
    fe.react.css vs fe.vue.css → CANNOT conflict (different branch)
    fe.react.* vs fe.react.components → CAN conflict (wildcard match)
"""

from typing import List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re


class ScopeLayer(str, Enum):
    """Standard top-level scope layers."""
    FRONTEND = "fe"
    BACKEND = "be"
    INFRASTRUCTURE = "infra"
    SHARED = "shared"
    DATA = "data"
    MOBILE = "mobile"
    TESTING = "test"
    DOCS = "docs"


# Common scope path templates
SCOPE_TEMPLATES = {
    # Frontend
    "fe.react": "React frontend",
    "fe.react.components": "React components",
    "fe.react.components.forms": "React form components",
    "fe.react.components.layout": "React layout components",
    "fe.react.hooks": "React custom hooks",
    "fe.react.state": "React state management",
    "fe.react.state.zustand": "Zustand state",
    "fe.react.state.redux": "Redux state",
    "fe.react.css": "React styling",
    "fe.react.css.tailwind": "Tailwind CSS",
    "fe.react.css.styled": "Styled components",
    "fe.vue": "Vue frontend",
    "fe.vue.components": "Vue components",
    "fe.angular": "Angular frontend",

    # Backend
    "be.python": "Python backend",
    "be.python.fastapi": "FastAPI framework",
    "be.python.fastapi.api": "FastAPI endpoints",
    "be.python.fastapi.auth": "FastAPI authentication",
    "be.python.fastapi.middleware": "FastAPI middleware",
    "be.python.django": "Django framework",
    "be.python.db": "Python database layer",
    "be.python.db.postgres": "PostgreSQL specific",
    "be.python.db.redis": "Redis specific",
    "be.go": "Go backend",
    "be.go.api": "Go API handlers",
    "be.node": "Node.js backend",

    # Infrastructure
    "infra.docker": "Docker configuration",
    "infra.docker.compose": "Docker Compose",
    "infra.k8s": "Kubernetes",
    "infra.k8s.deployment": "K8s deployments",
    "infra.nomad": "Nomad orchestration",
    "infra.ci": "CI/CD pipelines",
    "infra.ci.github": "GitHub Actions",

    # Shared
    "shared.utils": "Shared utilities",
    "shared.types": "Shared type definitions",
    "shared.constants": "Shared constants",
    "shared.validation": "Shared validation",

    # Data
    "data.schema": "Data schemas",
    "data.migration": "Database migrations",
    "data.seed": "Seed data",

    # Testing
    "test.unit": "Unit tests",
    "test.integration": "Integration tests",
    "test.e2e": "End-to-end tests",
}


class ScopeValidationError(Exception):
    """Raised when scope path is invalid."""
    pass


@dataclass
class ScopePath:
    """
    Parsed and validated scope path.

    Attributes:
        raw: Original string (e.g., "fe.react.css.tailwind")
        segments: Parsed segments (e.g., ["fe", "react", "css", "tailwind"])
        depth: Number of segments (e.g., 4)
        layer: Top-level layer (e.g., "fe")
        has_wildcard: Contains wildcard segment
    """
    raw: str
    segments: List[str] = field(default_factory=list)
    depth: int = 0
    layer: str = ""
    has_wildcard: bool = False

    # Pattern for valid segment
    SEGMENT_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
    WILDCARD = "*"

    def __post_init__(self):
        """Parse and validate the scope path."""
        if not self.segments:
            self._parse()

    def _parse(self):
        """Parse the raw scope path."""
        if not self.raw:
            raise ScopeValidationError("Scope path cannot be empty")

        # Normalize
        path = self.raw.lower().strip()

        # Split by dots
        self.segments = path.split(".")

        # Validate each segment
        for i, seg in enumerate(self.segments):
            if seg == self.WILDCARD:
                self.has_wildcard = True
                continue

            if not seg:
                raise ScopeValidationError(f"Empty segment at position {i} in '{self.raw}'")

            if not self.SEGMENT_PATTERN.match(seg):
                raise ScopeValidationError(
                    f"Invalid segment '{seg}' at position {i}. "
                    f"Must be lowercase alphanumeric starting with letter."
                )

        self.depth = len(self.segments)
        self.layer = self.segments[0] if self.segments else ""

    @classmethod
    def parse(cls, path: str) -> 'ScopePath':
        """Parse a scope path string."""
        return cls(raw=path)

    @classmethod
    def is_valid(cls, path: str) -> bool:
        """Check if a scope path is valid without raising."""
        try:
            cls.parse(path)
            return True
        except ScopeValidationError:
            return False

    def __str__(self) -> str:
        return self.raw

    def __eq__(self, other) -> bool:
        if isinstance(other, ScopePath):
            return self.raw == other.raw
        if isinstance(other, str):
            return self.raw == other.lower()
        return False

    def __hash__(self) -> int:
        return hash(self.raw)

    def parent(self) -> Optional['ScopePath']:
        """Get parent scope (one level up)."""
        if self.depth <= 1:
            return None
        return ScopePath(raw=".".join(self.segments[:-1]))

    def child(self, segment: str) -> 'ScopePath':
        """Create child scope by appending segment."""
        return ScopePath(raw=f"{self.raw}.{segment}")

    def ancestors(self) -> List['ScopePath']:
        """Get all ancestor scopes (from root to parent)."""
        result = []
        for i in range(1, self.depth):
            result.append(ScopePath(raw=".".join(self.segments[:i])))
        return result

    def is_ancestor_of(self, other: 'ScopePath') -> bool:
        """Check if this scope is an ancestor of other."""
        if self.depth >= other.depth:
            return False
        return other.raw.startswith(self.raw + ".")

    def is_descendant_of(self, other: 'ScopePath') -> bool:
        """Check if this scope is a descendant of other."""
        return other.is_ancestor_of(self)

    def matches_wildcard(self, pattern: 'ScopePath') -> bool:
        """
        Check if this scope matches a wildcard pattern.

        Examples:
            "fe.react.css" matches "fe.*.css" → True
            "fe.react.css" matches "fe.react.*" → True
            "fe.vue.css" matches "fe.react.*" → False
        """
        if not pattern.has_wildcard:
            return self.raw == pattern.raw

        if len(self.segments) != len(pattern.segments):
            return False

        for mine, theirs in zip(self.segments, pattern.segments):
            if theirs == self.WILDCARD:
                continue
            if mine != theirs:
                return False

        return True

    def common_ancestor(self, other: 'ScopePath') -> Optional['ScopePath']:
        """Find common ancestor scope with another path."""
        common = []
        for a, b in zip(self.segments, other.segments):
            if a == b:
                common.append(a)
            else:
                break

        if not common:
            return None

        return ScopePath(raw=".".join(common))

    def distance_to(self, other: 'ScopePath') -> int:
        """
        Calculate distance between two scopes.

        Distance = (depth to common ancestor from self) + (depth to common ancestor from other)

        Same scope = 0
        Parent-child = 1
        Siblings = 2
        """
        if self.raw == other.raw:
            return 0

        common = self.common_ancestor(other)

        if common is None:
            # No common ancestor (different top-level layers)
            return self.depth + other.depth

        return (self.depth - common.depth) + (other.depth - common.depth)


class ScopeRelation(str, Enum):
    """Relationship between two scopes."""
    SAME = "SAME"               # Identical scopes
    PARENT = "PARENT"           # First is parent of second
    CHILD = "CHILD"             # First is child of second
    SIBLING = "SIBLING"         # Same parent
    COUSIN = "COUSIN"           # Share ancestor but not parent
    UNRELATED = "UNRELATED"     # Different top-level branches


def get_scope_relation(scope_a: ScopePath, scope_b: ScopePath) -> ScopeRelation:
    """Determine relationship between two scopes."""
    if scope_a.raw == scope_b.raw:
        return ScopeRelation.SAME

    if scope_a.is_ancestor_of(scope_b):
        return ScopeRelation.PARENT

    if scope_b.is_ancestor_of(scope_a):
        return ScopeRelation.CHILD

    # Check if different top-level layer
    if scope_a.layer != scope_b.layer:
        return ScopeRelation.UNRELATED

    # Check if siblings (same parent)
    parent_a = scope_a.parent()
    parent_b = scope_b.parent()

    if parent_a and parent_b and parent_a.raw == parent_b.raw:
        return ScopeRelation.SIBLING

    # Check if they share any ancestor
    common = scope_a.common_ancestor(scope_b)
    if common:
        return ScopeRelation.COUSIN

    return ScopeRelation.UNRELATED


def scopes_can_conflict(
    scope_a: str,
    scope_b: str,
    inheritance_a: bool = True,
    inheritance_b: bool = True,
) -> Tuple[bool, str]:
    """
    Determine if two scopes can potentially conflict.

    Args:
        scope_a: First scope path
        scope_b: Second scope path
        inheritance_a: Does first scope apply to descendants?
        inheritance_b: Does second scope apply to descendants?

    Returns:
        (can_conflict, reason)

    Conflict Rules:
    - SAME: Always can conflict
    - PARENT/CHILD: Can conflict if parent has inheritance
    - SIBLING: Cannot conflict (different branches)
    - COUSIN: Cannot conflict (different branches)
    - UNRELATED: Cannot conflict (different layers)
    """
    try:
        path_a = ScopePath.parse(scope_a)
        path_b = ScopePath.parse(scope_b)
    except ScopeValidationError as e:
        return True, f"Invalid scope: {e}"  # Assume can conflict if invalid

    relation = get_scope_relation(path_a, path_b)

    if relation == ScopeRelation.SAME:
        return True, "Same scope"

    if relation == ScopeRelation.PARENT:
        if inheritance_a:
            return True, f"'{scope_a}' is parent with inheritance"
        return False, f"'{scope_a}' is parent but no inheritance"

    if relation == ScopeRelation.CHILD:
        if inheritance_b:
            return True, f"'{scope_b}' is parent with inheritance"
        return False, f"'{scope_b}' is parent but no inheritance"

    if relation == ScopeRelation.SIBLING:
        return False, "Sibling scopes (different branches)"

    if relation == ScopeRelation.COUSIN:
        return False, "Cousin scopes (share ancestor but different branches)"

    if relation == ScopeRelation.UNRELATED:
        return False, "Unrelated scopes (different layers)"

    return True, "Unknown relation"


def find_related_scopes(
    scope: str,
    all_scopes: List[str],
    include_ancestors: bool = True,
    include_descendants: bool = True,
    include_siblings: bool = False,
) -> List[str]:
    """
    Find scopes related to the given scope.

    Args:
        scope: The scope to find relations for
        all_scopes: All available scopes
        include_ancestors: Include parent scopes
        include_descendants: Include child scopes
        include_siblings: Include sibling scopes

    Returns:
        List of related scope paths
    """
    try:
        path = ScopePath.parse(scope)
    except ScopeValidationError:
        return []

    related = []

    for other_scope in all_scopes:
        if other_scope == scope:
            continue

        try:
            other_path = ScopePath.parse(other_scope)
        except ScopeValidationError:
            continue

        relation = get_scope_relation(path, other_path)

        if relation == ScopeRelation.PARENT and include_descendants:
            related.append(other_scope)
        elif relation == ScopeRelation.CHILD and include_ancestors:
            related.append(other_scope)
        elif relation == ScopeRelation.SIBLING and include_siblings:
            related.append(other_scope)

    return related


def suggest_scope_path(
    keywords: List[str],
    file_path: Optional[str] = None,
) -> Optional[str]:
    """
    Suggest a scope path based on keywords and file path.

    Args:
        keywords: Keywords from the decision
        file_path: Optional file path for context

    Returns:
        Suggested scope path or None
    """
    # Normalize keywords
    keywords_lower = {k.lower() for k in keywords}

    # Detect layer from keywords
    layer = None
    if any(k in keywords_lower for k in ["react", "vue", "angular", "frontend", "ui", "component"]):
        layer = "fe"
    elif any(k in keywords_lower for k in ["fastapi", "django", "flask", "backend", "api", "server"]):
        layer = "be"
    elif any(k in keywords_lower for k in ["docker", "kubernetes", "k8s", "nomad", "infra", "deploy"]):
        layer = "infra"
    elif any(k in keywords_lower for k in ["test", "testing", "unittest", "pytest"]):
        layer = "test"

    if not layer:
        return None

    # Detect technology
    tech = None
    if layer == "fe":
        if "react" in keywords_lower:
            tech = "react"
        elif "vue" in keywords_lower:
            tech = "vue"
        elif "angular" in keywords_lower:
            tech = "angular"
    elif layer == "be":
        if "python" in keywords_lower or "fastapi" in keywords_lower or "django" in keywords_lower:
            tech = "python"
            if "fastapi" in keywords_lower:
                tech = "python.fastapi"
            elif "django" in keywords_lower:
                tech = "python.django"
        elif "go" in keywords_lower or "golang" in keywords_lower:
            tech = "go"
        elif "node" in keywords_lower or "nodejs" in keywords_lower:
            tech = "node"

    if tech:
        base = f"{layer}.{tech}"
    else:
        base = layer

    # Detect sublayer
    sublayer = None
    if any(k in keywords_lower for k in ["css", "style", "tailwind", "styled"]):
        sublayer = "css"
    elif any(k in keywords_lower for k in ["component", "components"]):
        sublayer = "components"
    elif any(k in keywords_lower for k in ["hook", "hooks"]):
        sublayer = "hooks"
    elif any(k in keywords_lower for k in ["state", "store", "zustand", "redux"]):
        sublayer = "state"
    elif any(k in keywords_lower for k in ["auth", "authentication", "login"]):
        sublayer = "auth"
    elif any(k in keywords_lower for k in ["api", "endpoint", "route"]):
        sublayer = "api"
    elif any(k in keywords_lower for k in ["db", "database", "postgres", "mysql"]):
        sublayer = "db"

    if sublayer:
        return f"{base}.{sublayer}"

    return base


def get_scope_tree(scopes: List[str]) -> dict:
    """
    Build a tree structure from a list of scopes.

    Args:
        scopes: List of scope paths

    Returns:
        Nested dictionary representing the scope tree
    """
    tree = {}

    for scope in scopes:
        try:
            path = ScopePath.parse(scope)
        except ScopeValidationError:
            continue

        current = tree
        for segment in path.segments:
            if segment not in current:
                current[segment] = {}
            current = current[segment]

    return tree


def print_scope_tree(tree: dict, prefix: str = "", is_last: bool = True) -> str:
    """
    Format scope tree as ASCII art.

    Returns string like:
    fe
    ├── react
    │   ├── components
    │   └── css
    └── vue
    """
    lines = []
    items = list(tree.items())

    for i, (key, subtree) in enumerate(items):
        is_last_item = (i == len(items) - 1)

        if prefix:
            connector = "└── " if is_last_item else "├── "
            lines.append(f"{prefix}{connector}{key}")

            if subtree:
                new_prefix = prefix + ("    " if is_last_item else "│   ")
                lines.append(print_scope_tree(subtree, new_prefix, is_last_item))
        else:
            lines.append(key)
            if subtree:
                lines.append(print_scope_tree(subtree, "", is_last_item))

    return "\n".join(filter(None, lines))


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "ScopeLayer",
    "ScopeRelation",
    # Classes
    "ScopePath",
    "ScopeValidationError",
    # Functions
    "get_scope_relation",
    "scopes_can_conflict",
    "find_related_scopes",
    "suggest_scope_path",
    "get_scope_tree",
    "print_scope_tree",
    # Constants
    "SCOPE_TEMPLATES",
]
