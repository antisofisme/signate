"""
Scope Resolver for AI Retrieval

Bridges the scope DAG system with the retrieval engine to enable:
- Scope-aware filtering and ranking
- Denormalized scope information in results
- Hierarchical scope matching (umbrella, shared child, etc.)

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────┐
│                      ScopeResolver                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Scope Registry │  │  Decision Scope │  │   Query Scope   │  │
│  │  (Default Tree) │  │   (Cached)      │  │   Matching      │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                     │          │
│           └────────────────────┼─────────────────────┘          │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │               Scope-Aware Retrieval                         ││
│  │  - Filter by scope hierarchy                                ││
│  │  - Boost related scopes                                     ││
│  │  - Denormalize scope info                                   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘

Usage:
    from core.retrieval.scope_resolver import ScopeResolver, resolve_query_scopes

    resolver = ScopeResolver()

    # Filter decisions by scope
    filtered = resolver.filter_by_scope(decisions, "fe.api")

    # Boost ranking by scope relevance
    boosted = resolver.boost_by_scope_relevance(results, "fe.api")

    # Expand query scope to include related
    expanded = resolve_query_scopes("fe.api")  # ["fe.api", "api.rest", "api.graphql", ...]
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
from threading import Lock

from ..domain.scope_dag import (
    ScopeTree,
    ScopeNode,
    ScopeDefinition,
    InheritanceType,
    ScopeRelation,
    create_scope_definition,
)
from ..domain.scope_registry import (
    get_default_tree,
    resolve_scope,
    scope_matches_query,
    get_applies_to_for_retrieval,
    find_scope_by_alias,
    get_umbrella_scopes,
    get_shared_scopes,
    suggest_scopes,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ScopeMatch:
    """Result of scope matching between decision and query."""
    decision_id: str
    decision_scope: str
    query_scope: str
    match_type: str  # "exact", "ancestor", "descendant", "shared", "umbrella"
    relevance_score: float  # 0.0 to 1.0
    match_path: List[str]  # Path from decision scope to query scope
    is_direct: bool  # Direct match vs through hierarchy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_scope": self.decision_scope,
            "query_scope": self.query_scope,
            "match_type": self.match_type,
            "relevance_score": self.relevance_score,
            "match_path": self.match_path,
            "is_direct": self.is_direct,
        }


@dataclass
class ScopeContext:
    """Context information about a query scope for AI."""
    scope_path: str
    scope_label: str
    scope_description: str
    parent_scopes: List[str]
    child_scopes: List[str]
    sibling_scopes: List[str]
    related_umbrella_scopes: List[str]
    ai_description: str  # Human-readable for AI context

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope_path": self.scope_path,
            "scope_label": self.scope_label,
            "scope_description": self.scope_description,
            "parent_scopes": self.parent_scopes,
            "child_scopes": self.child_scopes,
            "sibling_scopes": self.sibling_scopes,
            "related_umbrella_scopes": self.related_umbrella_scopes,
            "ai_description": self.ai_description,
        }


@dataclass
class DecisionScopeInfo:
    """Cached scope information for a decision."""
    decision_id: str
    primary_scope: str
    all_scopes: List[str]
    inheritance_type: str
    applies_to_description: str
    ancestors: List[str]
    descendants: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "primary_scope": self.primary_scope,
            "all_scopes": self.all_scopes,
            "inheritance_type": self.inheritance_type,
            "applies_to_description": self.applies_to_description,
            "ancestors": self.ancestors,
            "descendants": self.descendants,
        }


# =============================================================================
# SCOPE MATCHING WEIGHTS
# =============================================================================

# Match type weights for ranking
MATCH_WEIGHTS: Dict[str, float] = {
    "exact": 1.0,           # Same scope
    "umbrella_covers": 0.95,  # Umbrella decision covers query scope
    "shared_child": 0.9,    # Shared child applies to query scope
    "ancestor": 0.8,        # Decision is ancestor of query scope
    "descendant": 0.7,      # Decision is descendant of query scope
    "sibling": 0.5,         # Same parent, different path
    "wildcard": 0.85,       # Wildcard match
    "none": 0.0,            # No match
}


# =============================================================================
# SCOPE RESOLVER
# =============================================================================

class ScopeResolver:
    """
    Resolves scope relationships for retrieval.

    Caches scope information for decisions and provides efficient
    scope-based filtering and ranking.
    """

    def __init__(self, tree: Optional[ScopeTree] = None):
        """
        Initialize scope resolver.

        Args:
            tree: Scope tree to use (defaults to default tree)
        """
        self._tree = tree or get_default_tree()
        self._decision_cache: Dict[str, DecisionScopeInfo] = {}
        self._cache_lock = Lock()

    # =========================================================================
    # DECISION SCOPE CACHING
    # =========================================================================

    def cache_decision_scope(
        self,
        decision_id: str,
        scope_paths: List[str],
    ) -> DecisionScopeInfo:
        """
        Cache scope information for a decision.

        Args:
            decision_id: Decision ID
            scope_paths: Scope paths for the decision

        Returns:
            Cached DecisionScopeInfo
        """
        # Get denormalized scope info
        scope_info = get_applies_to_for_retrieval(scope_paths, self._tree)

        info = DecisionScopeInfo(
            decision_id=decision_id,
            primary_scope=scope_info["primary_scope"],
            all_scopes=scope_info["all_scopes"],
            inheritance_type=scope_info["inheritance_type"],
            applies_to_description=scope_info["description"],
            ancestors=scope_info["ancestors"],
            descendants=scope_info["descendants"],
        )

        with self._cache_lock:
            self._decision_cache[decision_id] = info

        return info

    def get_decision_scope(self, decision_id: str) -> Optional[DecisionScopeInfo]:
        """Get cached scope info for a decision."""
        return self._decision_cache.get(decision_id)

    def cache_decisions(self, decisions: List[Dict[str, Any]]) -> int:
        """
        Cache scope information for multiple decisions.

        Args:
            decisions: List of decision dicts

        Returns:
            Number of decisions cached
        """
        cached = 0
        for decision in decisions:
            decision_id = decision.get("decision_id", "")
            if not decision_id:
                continue

            # Get scope paths from decision
            scope_paths = []
            scope = decision.get("scope")
            if isinstance(scope, str):
                scope_paths = [scope]
            elif isinstance(scope, dict):
                scope_paths = [scope.get("primary_path", "")]
                scope_paths.extend(scope.get("alternative_paths", []))
            elif isinstance(scope, list):
                scope_paths = scope

            if scope_paths:
                self.cache_decision_scope(decision_id, scope_paths)
                cached += 1

        return cached

    # =========================================================================
    # SCOPE MATCHING
    # =========================================================================

    def match_scope(
        self,
        decision_scope: Dict,
        query_scope: str,
    ) -> ScopeMatch:
        """
        Match a decision's scope against a query scope.

        Args:
            decision_scope: Decision's scope info (from cache or get_applies_to_for_retrieval)
            query_scope: Scope being queried

        Returns:
            ScopeMatch with relevance score
        """
        decision_id = decision_scope.get("decision_id", "")
        primary_scope = decision_scope.get("primary_scope", "")
        all_scopes = decision_scope.get("all_scopes", [])
        inheritance_type = decision_scope.get("inheritance_type", "leaf")

        # Check for exact match first
        if query_scope in all_scopes:
            return ScopeMatch(
                decision_id=decision_id,
                decision_scope=primary_scope,
                query_scope=query_scope,
                match_type="exact",
                relevance_score=MATCH_WEIGHTS["exact"],
                match_path=[query_scope],
                is_direct=True,
            )

        # Check if decision is umbrella covering query scope
        if inheritance_type == "umbrella":
            descendants = decision_scope.get("descendants", [])
            if any(query_scope.startswith(d) for d in descendants):
                return ScopeMatch(
                    decision_id=decision_id,
                    decision_scope=primary_scope,
                    query_scope=query_scope,
                    match_type="umbrella_covers",
                    relevance_score=MATCH_WEIGHTS["umbrella_covers"],
                    match_path=[primary_scope, query_scope],
                    is_direct=False,
                )

        # Check if decision is shared child that applies
        if inheritance_type == "shared_child":
            for scope in all_scopes:
                if scope.endswith(query_scope.split(".")[-1]):
                    return ScopeMatch(
                        decision_id=decision_id,
                        decision_scope=primary_scope,
                        query_scope=query_scope,
                        match_type="shared_child",
                        relevance_score=MATCH_WEIGHTS["shared_child"],
                        match_path=[scope, query_scope],
                        is_direct=False,
                    )

        # Check ancestor relationship
        ancestors = decision_scope.get("ancestors", [])
        for ancestor in ancestors:
            if query_scope == ancestor or query_scope.startswith(f"{ancestor}."):
                return ScopeMatch(
                    decision_id=decision_id,
                    decision_scope=primary_scope,
                    query_scope=query_scope,
                    match_type="ancestor",
                    relevance_score=MATCH_WEIGHTS["ancestor"],
                    match_path=[primary_scope, ancestor, query_scope],
                    is_direct=False,
                )

        # Check descendant relationship
        for scope in all_scopes:
            if scope.startswith(f"{query_scope}."):
                return ScopeMatch(
                    decision_id=decision_id,
                    decision_scope=primary_scope,
                    query_scope=query_scope,
                    match_type="descendant",
                    relevance_score=MATCH_WEIGHTS["descendant"],
                    match_path=[query_scope, scope],
                    is_direct=False,
                )

        # Check sibling (same parent)
        query_parts = query_scope.split(".")
        if len(query_parts) > 1:
            query_parent = ".".join(query_parts[:-1])
            for scope in all_scopes:
                scope_parts = scope.split(".")
                if len(scope_parts) > 1:
                    scope_parent = ".".join(scope_parts[:-1])
                    if query_parent == scope_parent:
                        return ScopeMatch(
                            decision_id=decision_id,
                            decision_scope=primary_scope,
                            query_scope=query_scope,
                            match_type="sibling",
                            relevance_score=MATCH_WEIGHTS["sibling"],
                            match_path=[scope_parent, primary_scope, query_scope],
                            is_direct=False,
                        )

        # No match
        return ScopeMatch(
            decision_id=decision_id,
            decision_scope=primary_scope,
            query_scope=query_scope,
            match_type="none",
            relevance_score=MATCH_WEIGHTS["none"],
            match_path=[],
            is_direct=False,
        )

    # =========================================================================
    # FILTERING & RANKING
    # =========================================================================

    def filter_by_scope(
        self,
        decisions: List[Dict[str, Any]],
        query_scope: str,
        min_relevance: float = 0.0,
    ) -> List[Tuple[Dict[str, Any], ScopeMatch]]:
        """
        Filter decisions by scope relevance.

        Args:
            decisions: Decisions to filter
            query_scope: Query scope path
            min_relevance: Minimum relevance score (0.0 = include all matches)

        Returns:
            List of (decision, match) tuples sorted by relevance
        """
        results: List[Tuple[Dict[str, Any], ScopeMatch]] = []

        for decision in decisions:
            decision_id = decision.get("decision_id", "")

            # Get scope info from cache or compute
            scope_info = self.get_decision_scope(decision_id)
            if not scope_info:
                # Try to compute from decision
                scope_paths = self._extract_scope_paths(decision)
                if scope_paths:
                    scope_info = self.cache_decision_scope(decision_id, scope_paths)

            if scope_info:
                match = self.match_scope(scope_info.to_dict(), query_scope)
                if match.relevance_score >= min_relevance:
                    results.append((decision, match))

        # Sort by relevance
        results.sort(key=lambda x: x[1].relevance_score, reverse=True)

        return results

    def boost_by_scope_relevance(
        self,
        results: List[Dict[str, Any]],
        query_scope: str,
        boost_factor: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Boost result ranking scores by scope relevance.

        Args:
            results: Retrieval results (must have rank_score field)
            query_scope: Query scope for matching
            boost_factor: Maximum boost (0.3 = up to 30% boost)

        Returns:
            Results with boosted scores
        """
        boosted_results = []

        for result in results:
            decision_id = result.get("decision_id", "")

            # Get scope info
            scope_info = self.get_decision_scope(decision_id)
            if scope_info:
                match = self.match_scope(scope_info.to_dict(), query_scope)
                scope_boost = match.relevance_score * boost_factor

                # Create boosted result
                boosted = dict(result)
                original_score = boosted.get("rank_score", 0.5)
                boosted["rank_score"] = min(1.0, original_score + scope_boost)
                boosted["scope_boost"] = scope_boost
                boosted["scope_match"] = match.to_dict()

                boosted_results.append(boosted)
            else:
                boosted_results.append(result)

        # Re-sort by boosted score
        boosted_results.sort(key=lambda x: x.get("rank_score", 0), reverse=True)

        return boosted_results

    # =========================================================================
    # QUERY SCOPE EXPANSION
    # =========================================================================

    def expand_query_scope(self, query_scope: str) -> List[str]:
        """
        Expand a query scope to include related scopes.

        Useful for broadening search to catch related decisions.

        Args:
            query_scope: Initial query scope

        Returns:
            List of expanded scope paths
        """
        expanded: Set[str] = {query_scope}

        # Add ancestors (decisions higher up apply)
        node = self._tree.get_node(query_scope.split(".")[-1])
        if node:
            ancestors = self._tree.get_ancestors(node.id)
            for ancestor in ancestors:
                expanded.add(ancestor)

        # Add children (more specific decisions)
        if node:
            descendants = self._tree.get_descendants(node.id)
            for desc in descendants:
                expanded.add(f"{query_scope}.{desc}")

        # Add umbrella scopes that cover this area
        umbrella_scopes = get_umbrella_scopes(self._tree)
        for umbrella in umbrella_scopes:
            descendants = self._tree.get_descendants(umbrella.id)
            if node and node.id in descendants:
                expanded.add(umbrella.id)

        # Add shared scopes
        shared_scopes = get_shared_scopes(self._tree)
        for shared in shared_scopes:
            if any(p.endswith(query_scope.split(".")[-1]) for p in shared.parents):
                expanded.add(shared.id)

        return sorted(list(expanded))

    # =========================================================================
    # CONTEXT GENERATION FOR AI
    # =========================================================================

    def get_scope_context(self, scope_path: str) -> ScopeContext:
        """
        Get rich context information about a scope for AI.

        Args:
            scope_path: Scope path to get context for

        Returns:
            ScopeContext with hierarchy and relationships
        """
        node = self._tree.get_node(scope_path.split(".")[-1])

        if not node:
            return ScopeContext(
                scope_path=scope_path,
                scope_label=scope_path,
                scope_description="Unknown scope",
                parent_scopes=[],
                child_scopes=[],
                sibling_scopes=[],
                related_umbrella_scopes=[],
                ai_description=f"Scope '{scope_path}' is not in the standard scope tree.",
            )

        # Get parents, children, siblings
        parents = node.parents
        children = node.children
        siblings = []
        for parent in parents:
            parent_node = self._tree.get_node(parent)
            if parent_node:
                for child in parent_node.children:
                    if child != node.id:
                        siblings.append(child)

        # Get related umbrella scopes
        umbrella_ids = []
        umbrella_scopes = get_umbrella_scopes(self._tree)
        for umbrella in umbrella_scopes:
            descendants = self._tree.get_descendants(umbrella.id)
            if node.id in descendants:
                umbrella_ids.append(umbrella.id)

        # Generate AI description
        ai_description = self._generate_scope_ai_description(
            node, parents, children, siblings, umbrella_ids
        )

        return ScopeContext(
            scope_path=scope_path,
            scope_label=node.label,
            scope_description=node.description,
            parent_scopes=parents,
            child_scopes=children,
            sibling_scopes=siblings,
            related_umbrella_scopes=umbrella_ids,
            ai_description=ai_description,
        )

    def _generate_scope_ai_description(
        self,
        node: ScopeNode,
        parents: List[str],
        children: List[str],
        siblings: List[str],
        umbrella_ids: List[str],
    ) -> str:
        """Generate human-readable description for AI context."""
        parts = [f"'{node.label}' ({node.id})"]

        if node.description:
            parts.append(f"- {node.description}")

        if parents:
            parent_str = ", ".join(parents)
            parts.append(f"- Under: {parent_str}")

        if children:
            child_str = ", ".join(children[:5])
            if len(children) > 5:
                child_str += f" (and {len(children) - 5} more)"
            parts.append(f"- Contains: {child_str}")

        if siblings:
            sibling_str = ", ".join(siblings[:5])
            parts.append(f"- Related: {sibling_str}")

        if umbrella_ids:
            umbrella_str = ", ".join(umbrella_ids)
            parts.append(f"- Covered by umbrella decisions: {umbrella_str}")

        return "\n".join(parts)

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def _extract_scope_paths(self, decision: Dict[str, Any]) -> List[str]:
        """Extract scope paths from a decision."""
        scope = decision.get("scope")

        if isinstance(scope, str):
            return [scope] if scope else []
        elif isinstance(scope, dict):
            paths = [scope.get("primary_path", "")]
            paths.extend(scope.get("alternative_paths", []))
            return [p for p in paths if p]
        elif isinstance(scope, list):
            return scope

        return []

    def clear_cache(self):
        """Clear the decision scope cache."""
        with self._cache_lock:
            self._decision_cache.clear()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Singleton resolver
_default_resolver: Optional[ScopeResolver] = None
_resolver_lock = Lock()


def get_scope_resolver() -> ScopeResolver:
    """Get the default scope resolver (singleton)."""
    global _default_resolver

    if _default_resolver is None:
        with _resolver_lock:
            if _default_resolver is None:
                _default_resolver = ScopeResolver()

    return _default_resolver


def resolve_query_scopes(query_scope: str) -> List[str]:
    """
    Expand a query scope to include all related scopes.

    Convenience function using default resolver.

    Args:
        query_scope: Query scope path

    Returns:
        List of expanded scope paths
    """
    return get_scope_resolver().expand_query_scope(query_scope)


def get_scope_context_for_ai(scope_path: str) -> Dict[str, Any]:
    """
    Get scope context information for AI.

    Convenience function using default resolver.

    Args:
        scope_path: Scope path

    Returns:
        Dict with scope context
    """
    return get_scope_resolver().get_scope_context(scope_path).to_dict()


def filter_decisions_by_scope(
    decisions: List[Dict[str, Any]],
    query_scope: str,
    min_relevance: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Filter decisions by scope relevance.

    Convenience function using default resolver.

    Args:
        decisions: Decisions to filter
        query_scope: Query scope path
        min_relevance: Minimum relevance score

    Returns:
        Filtered and sorted decisions
    """
    resolver = get_scope_resolver()
    results = resolver.filter_by_scope(decisions, query_scope, min_relevance)
    return [r[0] for r in results]


__all__ = [
    # Data classes
    "ScopeMatch",
    "ScopeContext",
    "DecisionScopeInfo",
    # Constants
    "MATCH_WEIGHTS",
    # Main class
    "ScopeResolver",
    # Convenience functions
    "get_scope_resolver",
    "resolve_query_scopes",
    "get_scope_context_for_ai",
    "filter_decisions_by_scope",
]
