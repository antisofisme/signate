"""
Retrieval Module Contract

Defines the interface for search and context retrieval.
Teams implementing retrieval must conform to this contract.

Owner: Search & Retrieval Team
Dependencies: Domain models, embedding service
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum


# =============================================================================
# DATA TRANSFER OBJECTS
# =============================================================================

class QueryIntent(str, Enum):
    """Detected intent of the query."""
    LIST = "list"           # User wants to list/browse decisions
    ENFORCE = "enforce"     # User wants to enforce/apply a decision
    UNDERSTAND = "understand"  # User wants to understand a concept
    REVIEW = "review"       # User wants to review decisions
    EXPLORE = "explore"     # User wants to explore related decisions
    FULL = "full"           # User wants complete information


class SearchStrategy(str, Enum):
    """Search strategy based on intent."""
    BROAD = "broad"           # High recall, lower precision
    PRECISE = "precise"       # High precision, lower recall
    BALANCED = "balanced"     # Default balanced approach
    EXHAUSTIVE = "exhaustive" # Get everything related


@dataclass
class RetrievalRequest:
    """Request for decision retrieval."""
    query: str
    limit: int = 10
    offset: int = 0
    # Filters
    domain_ids: Optional[List[str]] = None
    aspect_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    impact_levels: Optional[List[str]] = None
    # Options
    include_dependencies: bool = True
    expand_query: bool = True
    check_conflicts: bool = False
    # Context
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class RetrievalResult:
    """A single retrieval result."""
    decision_id: str
    code: str
    title: str
    statement: str
    domain_id: str
    aspect_id: str
    impact: str
    # Scoring
    relevance_score: float
    ranking_score: float
    # Metadata
    version: str
    created_at: Optional[datetime] = None
    # Optional expanded fields
    rationale: Optional[str] = None
    constraints: Optional[List[Dict[str, Any]]] = None
    # Retrieval metadata
    match_reason: Optional[str] = None
    triggered_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "code": self.code,
            "title": self.title,
            "statement": self.statement,
            "domain_id": self.domain_id,
            "aspect_id": self.aspect_id,
            "impact": self.impact,
            "relevance_score": self.relevance_score,
            "ranking_score": self.ranking_score,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "rationale": self.rationale,
            "constraints": self.constraints,
            "match_reason": self.match_reason,
            "triggered_by": self.triggered_by,
        }


@dataclass
class RetrievalResponse:
    """Response from retrieval system."""
    query: str
    results: List[RetrievalResult]
    total_count: int
    # Query analysis
    detected_intent: QueryIntent
    search_strategy: SearchStrategy
    expanded_queries: List[str] = field(default_factory=list)
    # Filters applied
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    # Conflicts detected (if check_conflicts=True)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    # Performance
    search_time_ms: float = 0.0
    ranking_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total_count": self.total_count,
            "detected_intent": self.detected_intent.value,
            "search_strategy": self.search_strategy.value,
            "expanded_queries": self.expanded_queries,
            "filters_applied": self.filters_applied,
            "conflicts": self.conflicts,
            "search_time_ms": self.search_time_ms,
            "ranking_time_ms": self.ranking_time_ms,
        }


# =============================================================================
# SEARCH CONTRACT
# =============================================================================

class SearchContract(ABC):
    """
    Search Contract

    Responsibilities:
    - Keyword search
    - Semantic (vector) search
    - Hybrid search combining both
    """

    @abstractmethod
    async def search_keyword(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword search.

        Args:
            query: Search query
            limit: Max results
            filters: Optional filters

        Returns:
            List of matching decision records
        """
        pass

    @abstractmethod
    async def search_semantic(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.65,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic (vector) search.

        Args:
            query: Search query
            limit: Max results
            similarity_threshold: Minimum similarity score
            filters: Optional filters

        Returns:
            List of matching decisions with similarity scores
        """
        pass

    @abstractmethod
    async def search_hybrid(
        self,
        query: str,
        limit: int = 10,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining keyword and semantic.

        Args:
            query: Search query
            limit: Max results
            keyword_weight: Weight for keyword results
            semantic_weight: Weight for semantic results
            filters: Optional filters

        Returns:
            Combined and ranked results
        """
        pass


# =============================================================================
# RANKER CONTRACT
# =============================================================================

class RankerContract(ABC):
    """
    Ranker Contract

    Responsibilities:
    - Rank search results by relevance
    - Apply blast radius priority
    - Consider usage analytics
    """

    @abstractmethod
    def rank(
        self,
        results: List[Dict[str, Any]],
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank search results.

        Ranking factors:
        1. Relevance score from search
        2. Impact level (CRITICAL > IMPORTANT > REFERENCE)
        3. Blast radius (CRITICAL > HIGH > MEDIUM > LOW)
        4. Recency (newer decisions rank higher)
        5. Usage frequency (popular decisions rank higher)

        Args:
            results: Search results to rank
            query: Original query for context
            context: Optional context for ranking

        Returns:
            Ranked results (highest rank first)
        """
        pass

    @abstractmethod
    def get_ranking_weights(self) -> Dict[str, float]:
        """
        Get current ranking weights.

        Returns:
            Dict mapping factor name to weight
        """
        pass


# =============================================================================
# RETRIEVAL CONTRACT
# =============================================================================

class RetrievalContract(ABC):
    """
    Retrieval Contract

    Orchestrates the full retrieval process:
    1. Query understanding (intent detection)
    2. Query expansion
    3. Search (keyword + semantic)
    4. Ranking
    5. Dependency traversal
    6. Conflict detection

    Usage:
        retriever = RetrievalEngine()
        response = await retriever.retrieve(request)

        for result in response.results:
            print(f"{result.code}: {result.title}")
    """

    @abstractmethod
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """
        Retrieve relevant decisions for a query.

        Args:
            request: RetrievalRequest with query and options

        Returns:
            RetrievalResponse with ranked results
        """
        pass

    @abstractmethod
    async def get_by_id(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Get decision by ID.

        Args:
            decision_id: Decision UUID

        Returns:
            Decision record or None
        """
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get decision by code.

        Args:
            code: Decision code (e.g., "ARCH-A06-001")

        Returns:
            Decision record or None
        """
        pass

    @abstractmethod
    async def get_dependencies(
        self,
        decision_id: str,
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get decisions that this decision depends on.

        Args:
            decision_id: Source decision ID
            depth: How deep to traverse (1 = direct only)

        Returns:
            List of dependency decisions
        """
        pass

    @abstractmethod
    async def get_dependents(
        self,
        decision_id: str,
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get decisions that depend on this decision.

        Args:
            decision_id: Source decision ID
            depth: How deep to traverse

        Returns:
            List of dependent decisions
        """
        pass

    @abstractmethod
    async def check_context_triggers(
        self,
        context: Dict[str, Any],
    ) -> List[str]:
        """
        Check which decisions should be auto-injected based on context.

        Args:
            context: Current context (files, keywords, etc.)

        Returns:
            List of decision IDs to inject
        """
        pass


__all__ = [
    "QueryIntent",
    "SearchStrategy",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalResponse",
    "SearchContract",
    "RankerContract",
    "RetrievalContract",
]
