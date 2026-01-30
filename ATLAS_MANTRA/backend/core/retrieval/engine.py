"""
Retrieval Engine - Main Entry Point

Orchestrates all retrieval components:
1. Hybrid Search (vector + keyword)
2. Multi-factor Ranking
3. Confidence Scoring
4. Dependency Resolution
5. Usage Tracking
6. Caching
7. Proactive Retrieval

TARGET: 9.5/10 Retrieval Quality

USAGE:
    engine = RetrievalEngine(
        meilisearch_client=client,
        redis_client=redis,
    )

    # Simple retrieval
    results = engine.retrieve(
        query="React component architecture",
        file_path="src/features/auth/LoginForm.tsx",
    )

    # With options
    results = engine.retrieve(
        query="API versioning",
        domain_id="ARCH",
        max_results=5,
        token_budget=1500,
        include_dependencies=True,
        min_confidence="MEDIUM",
    )

    # Get context text for AI
    context = engine.get_context(
        file_path="src/components/Button.tsx",
        token_budget=2000,
    )
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import uuid

from .searcher import HybridSearcher, SearchResult, SearchConfig, SearchMode
from .ranker import RelevanceRanker, RankingFactors, RankedResult
from .confidence import ConfidenceScorer, ConfidenceResult, ConfidenceLevel
from .dependencies import DependencyGraph, DependencyResolver
from .tracker import UsageTracker, UsageEventType
from .cache import DecisionCache, CacheConfig
from .quality import QualityScorer, QualityScore
from .suggester import DecisionSuggester, Suggestion


@dataclass
class RetrievalResult:
    """Complete retrieval result for a single decision."""
    decision_id: str
    decision_code: str
    decision: Dict[str, Any]

    # Scores
    search_score: float
    rank_score: float
    confidence: float
    confidence_level: ConfidenceLevel

    # Metadata
    rank: int
    confidence_reason: str
    factors_used: List[str]

    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    is_dependency: bool = False  # True if included due to dependency

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "code": self.decision_code,
            "rank": self.rank,
            "search_score": round(self.search_score, 2),
            "rank_score": round(self.rank_score, 2),
            "confidence": round(self.confidence, 2),
            "confidence_level": self.confidence_level.value,
            "confidence_reason": self.confidence_reason,
            "factors": self.factors_used,
            "dependencies": self.dependencies,
            "is_dependency": self.is_dependency,
        }


@dataclass
class RetrievalResponse:
    """Complete retrieval response."""
    results: List[RetrievalResult]
    total_found: int
    total_returned: int
    token_estimate: int
    query_time_ms: float

    # Metadata
    search_mode: str
    cache_hit: bool
    suggestions: List[Dict] = field(default_factory=list)
    conflicts: List[tuple] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "total_found": self.total_found,
            "total_returned": self.total_returned,
            "token_estimate": self.token_estimate,
            "query_time_ms": round(self.query_time_ms, 1),
            "search_mode": self.search_mode,
            "cache_hit": self.cache_hit,
            "suggestions": self.suggestions,
            "conflicts": self.conflicts,
        }


class RetrievalEngine:
    """
    Main retrieval engine orchestrating all components.

    Provides unified interface for decision retrieval with:
    - Hybrid search (vector + keyword)
    - Multi-factor ranking
    - Confidence scoring
    - Dependency resolution
    - Usage tracking
    - Intelligent caching
    """

    def __init__(
        self,
        decision_repository: Any = None,
        meilisearch_client: Any = None,
        redis_client: Any = None,
        search_config: Optional[SearchConfig] = None,
        ranking_factors: Optional[RankingFactors] = None,
        cache_config: Optional[CacheConfig] = None,
    ):
        """
        Initialize retrieval engine.

        Args:
            decision_repository: Repository for decision data
            meilisearch_client: Meilisearch client for search
            redis_client: Redis client for caching
            search_config: Search configuration
            ranking_factors: Ranking weights
            cache_config: Cache configuration
        """
        self.repository = decision_repository

        # Initialize components
        self.searcher = HybridSearcher(
            meilisearch_client=meilisearch_client,
            config=search_config,
        )

        self.tracker = UsageTracker()

        self.ranker = RelevanceRanker(
            factors=ranking_factors,
            usage_getter=lambda did: self.tracker.get_usage_count(did),
        )

        self.confidence_scorer = ConfidenceScorer()
        self.quality_scorer = QualityScorer()
        self.suggester = DecisionSuggester(
            usage_tracker=self.tracker,
            quality_scorer=self.quality_scorer,
        )

        self.cache = DecisionCache(
            config=cache_config,
            redis_client=redis_client,
        )

        # Dependency graph (built lazily)
        self._dependency_graph: Optional[DependencyGraph] = None
        self._dependency_resolver: Optional[DependencyResolver] = None

        # Decision data cache
        self._decisions: Dict[str, Dict[str, Any]] = {}

    def retrieve(
        self,
        query: str,
        file_path: Optional[str] = None,
        domain_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_results: int = 10,
        token_budget: int = 3000,
        min_confidence: str = "LOW",
        include_dependencies: bool = True,
        search_mode: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> RetrievalResponse:
        """
        Retrieve relevant decisions.

        Args:
            query: Natural language query
            file_path: Current file path for context
            domain_id: Filter by domain
            tags: Filter by tags
            max_results: Maximum results to return
            token_budget: Token budget limit
            min_confidence: Minimum confidence level
            include_dependencies: Include dependency decisions
            search_mode: Override search mode
            session_id: Session for tracking

        Returns:
            RetrievalResponse with ranked, filtered results
        """
        start_time = datetime.utcnow()
        session_id = session_id or str(uuid.uuid4())

        # Check cache
        cache_key = f"retrieve:{hash((query, file_path, domain_id, str(tags)))}"
        cached = self.cache.get(cache_key)
        if cached:
            # Track usage even for cached results
            self.tracker.track_retrieval(
                [r["decision_id"] for r in cached["results"][:5]],
                session_id=session_id,
                context={"query": query, "file_path": file_path},
            )
            cached["cache_hit"] = True
            return self._dict_to_response(cached)

        # Execute search
        mode = SearchMode(search_mode) if search_mode else None
        search_results = self.searcher.search(
            query=query,
            file_path=file_path,
            tags=tags,
            domain_id=domain_id,
            mode=mode,
        )

        # Load decision data
        decisions = self._load_decisions([r.decision_id for r in search_results])

        # Rank results
        context = {
            "query": query,
            "file_path": file_path,
            "domain_id": domain_id,
            "tags": tags,
            "keywords": self.searcher._extract_keywords(query),
        }

        ranked_results = self.ranker.rank(search_results, decisions, context)

        # Calculate confidence
        confidence_results = {}
        for ranked in ranked_results:
            search_scores = {
                "vector_score": ranked.search_score,
                "keyword_score": ranked.search_score * 0.8,  # Approximate
            }
            conf = self.confidence_scorer.score(
                decision_id=ranked.decision_id,
                decision=decisions.get(ranked.decision_id, {}),
                context=context,
                search_scores=search_scores,
            )
            confidence_results[ranked.decision_id] = conf

        # Filter by confidence
        min_level = ConfidenceLevel(min_confidence.upper())
        min_threshold = ConfidenceScorer.THRESHOLDS.get(min_level, 0.0)

        filtered_results = [
            r for r in ranked_results
            if confidence_results[r.decision_id].confidence >= min_threshold
        ]

        # Resolve dependencies
        result_ids = [r.decision_id for r in filtered_results[:max_results]]
        dependency_map = {}

        if include_dependencies:
            self._ensure_dependency_graph(decisions)
            resolved_ids = self._dependency_resolver.resolve(
                result_ids,
                include_dependencies=True,
                max_total=max_results + 5,
            )

            # Track which are dependencies
            for did in resolved_ids:
                if did not in result_ids:
                    dependency_map[did] = True

            # Load any missing decisions
            missing = [did for did in resolved_ids if did not in decisions]
            if missing:
                decisions.update(self._load_decisions(missing))

            # Check for conflicts
            conflicts = self._dependency_resolver.check_conflicts(resolved_ids)
        else:
            resolved_ids = result_ids
            conflicts = []

        # Build final results
        final_results = []
        token_count = 0

        for i, did in enumerate(resolved_ids):
            if token_count >= token_budget:
                break

            decision = decisions.get(did, {})
            conf = confidence_results.get(did)

            # Find ranked result or create minimal
            ranked = next((r for r in ranked_results if r.decision_id == did), None)

            # Estimate tokens for this decision
            decision_tokens = self._estimate_tokens(decision)
            token_count += decision_tokens

            result = RetrievalResult(
                decision_id=did,
                decision_code=decision.get("code", decision.get("decision_code", "")),
                decision=decision,
                search_score=ranked.search_score if ranked else 0.0,
                rank_score=ranked.final_score if ranked else 0.0,
                confidence=conf.confidence if conf else 0.5,
                confidence_level=conf.level if conf else ConfidenceLevel.UNCERTAIN,
                rank=i + 1,
                confidence_reason=conf.primary_reason if conf else "Dependency",
                factors_used=ranked.factors_used if ranked else [],
                dependencies=self._get_dependencies(did, resolved_ids),
                is_dependency=dependency_map.get(did, False),
            )
            final_results.append(result)

        # Track usage
        self.tracker.track_retrieval(
            [r.decision_id for r in final_results[:5]],
            session_id=session_id,
            context={"query": query, "file_path": file_path},
        )

        # Generate suggestions
        suggestions = self.suggester.suggest_for_context(
            context=context,
            existing_decisions=[r.decision for r in final_results],
        )

        # Calculate timing
        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        response = RetrievalResponse(
            results=final_results,
            total_found=len(search_results),
            total_returned=len(final_results),
            token_estimate=token_count,
            query_time_ms=query_time,
            search_mode=self.searcher.config.mode.value,
            cache_hit=False,
            suggestions=[s.to_dict() for s in suggestions[:3]],
            conflicts=conflicts,
        )

        # Cache response
        self.cache.set(cache_key, response.to_dict(), ttl_seconds=300)

        return response

    def get_context(
        self,
        file_path: str,
        token_budget: int = 2000,
        level: str = "standard",
        session_id: Optional[str] = None,
    ) -> str:
        """
        Get context text for AI injection.

        Args:
            file_path: Current file path
            token_budget: Token budget
            level: Detail level (summary, standard, full)
            session_id: Session for tracking

        Returns:
            Formatted context text
        """
        # Use file path to build query
        keywords = self.searcher._extract_from_path(file_path)
        query = " ".join(keywords) if keywords else "general architecture"

        response = self.retrieve(
            query=query,
            file_path=file_path,
            token_budget=token_budget,
            session_id=session_id,
        )

        return self.build_context(
            [r.decision_id for r in response.results],
            level=level,
        )

    def build_context(
        self,
        decision_ids: List[str],
        level: str = "standard",
    ) -> str:
        """
        Build context text from decisions.

        Args:
            decision_ids: Decisions to include
            level: Detail level

        Returns:
            Formatted context text
        """
        decisions = self._load_decisions(decision_ids)
        parts = ["# MANTRA Decisions Context\n"]

        for did in decision_ids:
            decision = decisions.get(did, {})
            if not decision:
                continue

            code = decision.get("code", decision.get("decision_code", ""))
            statement = decision.get("statement", "")
            rationale = decision.get("rationale", "")
            summary = decision.get("summary", "")

            if level == "summary":
                parts.append(f"- [{code}] {summary or statement[:100]}")

            elif level == "standard":
                parts.append(f"\n## {code}")
                parts.append(f"**Statement**: {statement}")
                constraints = decision.get("constraints", [])
                if constraints:
                    constraint_text = "; ".join(
                        c.get("rule", str(c))[:100] for c in constraints[:3]
                    )
                    parts.append(f"**Constraints**: {constraint_text}")

            else:  # full
                parts.append(f"\n## {code}")
                parts.append(f"\n### Statement\n{statement}")
                parts.append(f"\n### Rationale\n{rationale}")

                constraints = decision.get("constraints", [])
                if constraints:
                    parts.append("\n### Constraints")
                    for c in constraints:
                        rule = c.get("rule", str(c)) if isinstance(c, dict) else str(c)
                        parts.append(f"- {rule}")

                invariants = decision.get("invariants", [])
                if invariants:
                    parts.append("\n### Invariants")
                    for inv in invariants:
                        parts.append(f"- {inv}")

            parts.append("\n---")

        return "\n".join(parts)

    def score_quality(self, decision: Dict[str, Any]) -> QualityScore:
        """Score decision quality."""
        return self.quality_scorer.score(decision)

    def get_suggestions(
        self,
        codebase_context: Optional[Dict[str, Any]] = None,
    ) -> List[Suggestion]:
        """Get suggestions for decision improvements."""
        decisions = list(self._decisions.values())
        return self.suggester.analyze(decisions, codebase_context)

    def track_feedback(
        self,
        decision_id: str,
        helpful: bool,
        session_id: Optional[str] = None,
        comment: Optional[str] = None,
    ):
        """Track user feedback on a decision."""
        self.tracker.track_feedback(
            decision_id=decision_id,
            helpful=helpful,
            session_id=session_id,
            comment=comment,
        )

    def invalidate_decision(self, decision_id: str):
        """Invalidate caches for a decision."""
        self.cache.invalidate_decision(decision_id)
        if decision_id in self._decisions:
            del self._decisions[decision_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "cache": self.cache.get_stats(),
            "decisions_loaded": len(self._decisions),
            "dependency_graph_size": len(self._dependency_graph._nodes) if self._dependency_graph else 0,
        }

    def _load_decisions(self, decision_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Load decisions from repository or cache."""
        result = {}
        missing = []

        for did in decision_ids:
            if did in self._decisions:
                result[did] = self._decisions[did]
            else:
                cached = self.cache.get_decision(did)
                if cached:
                    result[did] = cached
                    self._decisions[did] = cached
                else:
                    missing.append(did)

        # Load missing from repository
        if missing and self.repository:
            for did in missing:
                decision = self.repository.get(did)
                if decision:
                    result[did] = decision
                    self._decisions[did] = decision
                    self.cache.set(f"decision:{did}", decision)

        return result

    def _ensure_dependency_graph(self, decisions: Dict[str, Dict[str, Any]]):
        """Ensure dependency graph is built."""
        if self._dependency_graph is None:
            self._dependency_graph = DependencyGraph()
            self._dependency_resolver = DependencyResolver(self._dependency_graph)

        # Add decisions to graph
        self._dependency_graph.build_from_decisions(list(decisions.values()))

    def _get_dependencies(
        self,
        decision_id: str,
        all_ids: List[str],
    ) -> List[str]:
        """Get dependencies for a decision that are in result set."""
        if not self._dependency_resolver:
            return []

        deps = self._dependency_graph.get_dependencies(decision_id, transitive=False)
        return [d for d in deps if d in all_ids]

    def _estimate_tokens(self, decision: Dict[str, Any]) -> int:
        """Estimate token count for a decision."""
        text_length = (
            len(decision.get("statement", "")) +
            len(decision.get("rationale", "")) +
            sum(len(str(c)) for c in decision.get("constraints", []))
        )
        return max(50, text_length // 3)

    def _dict_to_response(self, data: Dict) -> RetrievalResponse:
        """Convert cached dict to RetrievalResponse."""
        results = []
        for r in data.get("results", []):
            results.append(RetrievalResult(
                decision_id=r["decision_id"],
                decision_code=r["code"],
                decision={},
                search_score=r["search_score"],
                rank_score=r["rank_score"],
                confidence=r["confidence"],
                confidence_level=ConfidenceLevel(r["confidence_level"]),
                rank=r["rank"],
                confidence_reason=r["confidence_reason"],
                factors_used=r["factors"],
                dependencies=r.get("dependencies", []),
                is_dependency=r.get("is_dependency", False),
            ))

        return RetrievalResponse(
            results=results,
            total_found=data["total_found"],
            total_returned=data["total_returned"],
            token_estimate=data["token_estimate"],
            query_time_ms=data["query_time_ms"],
            search_mode=data["search_mode"],
            cache_hit=data.get("cache_hit", False),
            suggestions=data.get("suggestions", []),
            conflicts=data.get("conflicts", []),
        )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "RetrievalResult",
    "RetrievalResponse",
    "RetrievalEngine",
]
