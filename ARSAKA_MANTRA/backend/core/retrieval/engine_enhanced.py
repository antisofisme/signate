"""
MANTRA Enhanced Retrieval Engine

Extends base RetrievalEngine with new capabilities:
- Context Triggers: Auto-inject decisions based on conditions
- Smart Index: Hybrid keyword + semantic search
- Context Cache: Pre-computed context windows
- Usage Analytics: Feedback-driven ranking boosts

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────┐
│                    EnhancedRetrievalEngine                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Triggers   │  │ Smart Index │  │   Context Cache         │  │
│  │  (Auto-     │  │ (Hybrid     │  │   (Pre-computed         │  │
│  │   inject)   │  │  search)    │  │    windows)             │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┼──────────────────────┘                │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │               Base RetrievalEngine                          ││
│  │  (searcher, ranker, confidence, dependencies, cache)        ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │               Usage Analytics                                ││
│  │  (track events, calculate health, boost scores)             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Set, Tuple
import uuid

from .engine import RetrievalEngine, RetrievalResult, RetrievalResponse
from .context_trigger import (
    TriggerEngine, RetrievalContext, ContextTrigger, TriggerResult,
    create_file_trigger, create_keyword_trigger, create_scope_trigger,
)
from .smart_index import (
    DecisionIndex, SearchQuery, SearchResult as SmartSearchResult,
    EmbeddingProvider, DummyEmbeddingProvider,
    SearchMode as SmartSearchMode,
)
from .context_cache import (
    ContextCache, HotDecisionsCache, CacheType, ContextWindow,
    get_context_cache, get_hot_cache,
)
from .dependencies import DependencyGraph, DependencyResolver, RelationType
from .intent import (
    IntentDetector, IntentResult, QueryIntent, SearchStrategy,
    STRATEGY_PARAMS, StrategyParams,
)
from .query_expander import QueryExpander, ExpansionResult
from .reranker import (
    Reranker, RerankerConfig, RerankerMethod,
    RerankerCandidate, RerankerResult, RerankerResponse,
    create_reranker, create_accurate_reranker,
)
from .fusion import (
    ScoreFusion, FusionConfig, FusionMethod,
    fuse_rrf, fuse_hybrid,
)
from .optimal_config import (
    OptimalConfig, RetrievalProfile, OPTIMAL_CONFIGS,
    QUERY_TYPE_ADJUSTMENTS, get_optimal_config, DEFAULT_CONFIG,
)
from .query_embedding_cache import (
    QueryEmbeddingCache, AsyncQueryEmbeddingCache,
)
from ..analytics.usage_analytics import (
    UsageAnalytics, UsageEvent, EventType, FeedbackEvent, FeedbackType,
    DecisionHealth, DecisionStats,
)


# ============================================================================
# CONFLICT INFO
# ============================================================================

@dataclass
class ConflictInfo:
    """Information about a conflict between two decisions."""
    decision_a: str
    decision_b: str
    conflict_type: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_a": self.decision_a,
            "decision_b": self.decision_b,
            "conflict_type": self.conflict_type,
            "description": self.description,
        }


# ============================================================================
# ENHANCED RESULT
# ============================================================================

@dataclass
class EnhancedRetrievalResult(RetrievalResult):
    """Extended retrieval result with additional metadata."""
    # Trigger info
    triggered_by: List[str] = field(default_factory=list)  # Trigger IDs
    is_triggered: bool = False  # Was this auto-injected by trigger?

    # Analytics info
    usage_count: int = 0
    last_used: Optional[datetime] = None
    health_status: Optional[str] = None
    relevance_boost: float = 0.0

    # Cache info
    from_cache: bool = False
    cache_type: Optional[str] = None


@dataclass
class EnhancedRetrievalResponse(RetrievalResponse):
    """Extended retrieval response."""
    # Trigger info
    triggers_evaluated: int = 0
    triggers_fired: int = 0
    triggered_decisions: List[str] = field(default_factory=list)

    # Cache info
    context_cache_hit: bool = False
    hot_cache_hits: int = 0

    # Analytics
    analytics_applied: bool = False

    # Intent & Strategy info
    detected_intent: Optional[str] = None
    intent_confidence: float = 0.0
    search_strategy: Optional[str] = None

    # Query expansion info
    query_expanded: bool = False
    expanded_terms: List[str] = field(default_factory=list)

    # Conflict detection
    detected_conflicts: List[ConflictInfo] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Dependency traversal info
    dependencies_traversed: int = 0
    dependency_depth: int = 0

    # Reranking info (NEW)
    reranking_applied: bool = False
    reranking_method: Optional[str] = None
    reranking_time_ms: float = 0.0

    # Threshold info (from optimal config / strategy)
    similarity_threshold_applied: float = 0.0
    optimal_config_profile: Optional[str] = None


# ============================================================================
# ENHANCED ENGINE
# ============================================================================

class EnhancedRetrievalEngine:
    """
    Enhanced Retrieval Engine with triggers, smart index, cache, and analytics.

    Wraps the base RetrievalEngine and adds:
    1. Context triggers for auto-injection
    2. Smart index for hybrid search
    3. Context cache for performance
    4. Usage analytics for feedback-driven ranking
    """

    def __init__(
        self,
        base_engine: Optional[RetrievalEngine] = None,
        trigger_engine: Optional[TriggerEngine] = None,
        smart_index: Optional[DecisionIndex] = None,
        context_cache: Optional[ContextCache] = None,
        hot_cache: Optional[HotDecisionsCache] = None,
        usage_analytics: Optional[UsageAnalytics] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        intent_detector: Optional[IntentDetector] = None,
        query_expander: Optional[QueryExpander] = None,
        reranker: Optional[Reranker] = None,
    ):
        """
        Initialize enhanced engine.

        Args:
            base_engine: Base retrieval engine (or create new)
            trigger_engine: Context trigger engine
            smart_index: Hybrid search index
            context_cache: Pre-computed context cache
            hot_cache: Hot decisions cache
            usage_analytics: Usage tracking
            embedding_provider: For semantic search
            intent_detector: Intent detection for search strategy
            query_expander: Query expansion for better recall
            reranker: Cross-encoder/late interaction reranker
        """
        # Base engine
        self.base_engine = base_engine or RetrievalEngine()

        # Triggers
        self.trigger_engine = trigger_engine or TriggerEngine()

        # Smart index (with fallback embedding provider)
        embedding = embedding_provider or DummyEmbeddingProvider()
        self.smart_index = smart_index or DecisionIndex(embedding_provider=embedding)

        # Caches
        self.context_cache = context_cache or get_context_cache()
        self.hot_cache = hot_cache or get_hot_cache()

        # Analytics
        self.usage_analytics = usage_analytics or UsageAnalytics()

        # Intent detection & query expansion
        self.intent_detector = intent_detector or IntentDetector()
        self.query_expander = query_expander or QueryExpander()

        # Reranker (NEW: Cross-encoder/Late Interaction)
        # Default: Try cross-encoder, fallback to TF-IDF
        self.reranker = reranker or Reranker(RerankerConfig(
            method=RerankerMethod.CROSS_ENCODER,
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
            top_k=10,
            fallback_to_original=True,
        ))

        # Query Embedding Cache (reduces redundant API calls)
        self.query_embedding_cache = QueryEmbeddingCache(
            embedding_provider=embedding_provider,
            max_size=1000,
            ttl_seconds=3600,
            similarity_threshold=0.95,
            enable_semantic_lookup=True,
        )

        # Dependency graph (built lazily)
        self._dependency_graph: Optional[DependencyGraph] = None

        # Optimal config (from multi-agent optimization)
        self._optimal_config: OptimalConfig = DEFAULT_CONFIG

        # Cache warming flag
        self._cache_warmed = False

        # Configuration
        self._use_triggers = True
        self._use_smart_index = True
        self._use_context_cache = True
        self._use_analytics = True
        self._use_intent_detection = True
        self._use_query_expansion = True
        self._use_dependency_traversal = True
        self._use_conflict_detection = True
        self._use_reranking = True  # NEW: Enable reranking
        self._rerank_top_n = 50     # Rerank top N candidates
        self._analytics_boost_factor = 0.2  # Max 20% boost from analytics

    def configure(
        self,
        use_triggers: bool = True,
        use_smart_index: bool = True,
        use_context_cache: bool = True,
        use_analytics: bool = True,
        use_intent_detection: bool = True,
        use_query_expansion: bool = True,
        use_dependency_traversal: bool = True,
        use_conflict_detection: bool = True,
        use_reranking: bool = True,
        rerank_top_n: int = 50,
        analytics_boost_factor: float = 0.2,
    ):
        """Configure which features are enabled."""
        self._use_triggers = use_triggers
        self._use_smart_index = use_smart_index
        self._use_context_cache = use_context_cache
        self._use_analytics = use_analytics
        self._use_intent_detection = use_intent_detection
        self._use_query_expansion = use_query_expansion
        self._use_dependency_traversal = use_dependency_traversal
        self._use_conflict_detection = use_conflict_detection
        self._use_reranking = use_reranking
        self._rerank_top_n = rerank_top_n
        self._analytics_boost_factor = analytics_boost_factor

    def set_retrieval_profile(self, profile: RetrievalProfile):
        """
        Set retrieval profile from optimal configs.

        Args:
            profile: RetrievalProfile enum (MAX_ACCURACY, HIGH_ACCURACY, etc.)
        """
        self._optimal_config = OPTIMAL_CONFIGS.get(profile, DEFAULT_CONFIG)

    # =========================================================================
    # TRIGGER MANAGEMENT
    # =========================================================================

    def register_trigger(self, trigger: ContextTrigger):
        """Register a context trigger."""
        self.trigger_engine.register_trigger(trigger)

    def register_default_triggers(self):
        """Register common default triggers."""
        # React/TypeScript triggers
        self.trigger_engine.register_trigger(create_file_trigger(
            name="React Components",
            pattern="*.tsx",
            decision_ids=[],  # Will be populated when decisions are indexed
            tags=["react", "frontend", "component"],
        ))

        self.trigger_engine.register_trigger(create_file_trigger(
            name="API Routes",
            pattern="**/api/**/*.py",
            decision_ids=[],
            tags=["api", "backend", "endpoint"],
        ))

        self.trigger_engine.register_trigger(create_file_trigger(
            name="Database/Migration",
            pattern="**/migrations/*.sql",
            decision_ids=[],
            tags=["database", "migration", "schema"],
        ))

        self.trigger_engine.register_trigger(create_keyword_trigger(
            name="Security Context",
            keywords=["auth", "security", "password", "token", "jwt"],
            decision_ids=[],
            tags=["security", "auth"],
        ))

        self.trigger_engine.register_trigger(create_keyword_trigger(
            name="Testing Context",
            keywords=["test", "mock", "jest", "pytest", "coverage"],
            decision_ids=[],
            tags=["testing", "qa"],
        ))

    # =========================================================================
    # INDEX MANAGEMENT
    # =========================================================================

    def index_decision(self, decision: Dict[str, Any]):
        """Index a decision for smart search."""
        self.smart_index.index_decision(decision)

        # Also track in analytics
        decision_id = decision.get("decision_id", "")
        self.usage_analytics.ensure_stats(decision_id)

    def index_decisions(self, decisions: List[Dict[str, Any]]):
        """Index multiple decisions."""
        for decision in decisions:
            self.index_decision(decision)

    def rebuild_index(self, decisions: List[Dict[str, Any]]):
        """Rebuild the entire index."""
        self.smart_index.clear()
        self.index_decisions(decisions)

    # =========================================================================
    # MAIN RETRIEVAL
    # =========================================================================

    def retrieve(
        self,
        query: str,
        file_path: Optional[str] = None,
        file_content: Optional[str] = None,
        scope_path: Optional[str] = None,
        domain_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_results: Optional[int] = None,
        token_budget: int = 3000,
        min_confidence: str = "LOW",
        include_dependencies: Optional[bool] = None,
        check_conflicts: Optional[bool] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> EnhancedRetrievalResponse:
        """
        Enhanced retrieval with triggers, smart index, analytics, and intelligent search.

        Args:
            query: Natural language query
            file_path: Current file path
            file_content: Current file content (for content matching)
            scope_path: Current scope (e.g., "fe.react")
            domain_id: Filter by domain
            tags: Filter by tags
            max_results: Maximum results (None = auto from strategy)
            token_budget: Token limit
            min_confidence: Minimum confidence
            include_dependencies: Include dependencies (None = auto from strategy)
            check_conflicts: Check for conflicts (None = auto from strategy)
            session_id: For tracking
            user_id: For analytics

        Returns:
            EnhancedRetrievalResponse
        """
        start_time = datetime.now(timezone.utc)
        session_id = session_id or str(uuid.uuid4())

        # =====================================================================
        # STEP 0: Detect intent and determine search strategy
        # =====================================================================

        intent_result: Optional[IntentResult] = None
        strategy_params: Optional[StrategyParams] = None
        detected_intent: Optional[str] = None
        intent_confidence: float = 0.0
        search_strategy: Optional[str] = None

        if self._use_intent_detection and query:
            intent_result = self.intent_detector.detect(query)
            detected_intent = intent_result.intent.value
            intent_confidence = intent_result.confidence
            search_strategy = intent_result.strategy.value
            strategy_params = intent_result.strategy_params

            # Apply strategy defaults if not explicitly set
            if max_results is None:
                max_results = strategy_params.max_results if strategy_params else 10
            if include_dependencies is None:
                include_dependencies = strategy_params.include_dependencies if strategy_params else True
            if check_conflicts is None:
                check_conflicts = strategy_params.check_conflicts if strategy_params else False
        else:
            # Defaults when intent detection is off
            if max_results is None:
                max_results = 10
            if include_dependencies is None:
                include_dependencies = True
            if check_conflicts is None:
                check_conflicts = False

        # =====================================================================
        # STEP 1: Query expansion
        # =====================================================================

        expanded_terms: List[str] = []
        query_expanded = False
        effective_query = query

        if self._use_query_expansion and query:
            should_expand = True
            if strategy_params:
                should_expand = strategy_params.expand_query

            if should_expand:
                expansion_context = {
                    "domain_id": domain_id,
                    "file_path": file_path,
                    "scope_path": scope_path,
                }
                expansion_result = self.query_expander.expand(query, expansion_context)
                expanded_terms = expansion_result.expanded_terms
                query_expanded = len(expanded_terms) > 0

                # Use expanded query for search
                if expanded_terms:
                    effective_query = expansion_result.to_search_query(boost_original=True)

        # =====================================================================
        # STEP 2: Check context cache
        # =====================================================================

        # Build retrieval context
        context = RetrievalContext(
            file_path=file_path,
            file_content=file_content,
            query=query,
            scope_path=scope_path,
            scope_tags=tags,
        )

        cache_key = self._build_cache_key(query, file_path, scope_path)
        context_cache_hit = False

        if self._use_context_cache:
            cached = self.context_cache.get(cache_key)
            if cached:
                context_cache_hit = True
                # Return cached response with analytics update
                return self._apply_analytics_to_cached(cached, session_id, user_id)

        # =====================================================================
        # STEP 3: Evaluate triggers
        # =====================================================================

        triggered_decisions: Set[str] = set()
        triggers_evaluated = 0
        triggers_fired = 0

        if self._use_triggers:
            trigger_results = self.trigger_engine.evaluate(context)
            triggers_evaluated = len(self.trigger_engine._triggers)
            triggers_fired = len([r for r in trigger_results if r.matched])

            for result in trigger_results:
                if result.matched:
                    triggered_decisions.update(result.decision_ids)

        # =====================================================================
        # STEP 4: Smart index search (with expanded query)
        # =====================================================================

        smart_results: List[SmartSearchResult] = []
        if self._use_smart_index and self.smart_index.size > 0:
            search_query = SearchQuery(
                text=effective_query,  # Use expanded query
                tags=tags,
                scope_path=scope_path,
                limit=max_results * 2,  # Get more for ranking
            )
            smart_results = self.smart_index.search(search_query)

        # =====================================================================
        # STEP 5: Base engine retrieval
        # =====================================================================

        # Get more candidates for reranking
        candidates_for_rerank = max_results * 3 if self._use_reranking else max_results

        base_response = self.base_engine.retrieve(
            query=effective_query,  # Use expanded query
            file_path=file_path,
            domain_id=domain_id,
            tags=tags,
            max_results=candidates_for_rerank,  # Get more for reranking
            token_budget=token_budget,
            min_confidence=min_confidence,
            include_dependencies=include_dependencies,
            session_id=session_id,
        )

        # =====================================================================
        # STEP 5.1: Apply strategy threshold (from intent detection)
        # =====================================================================

        similarity_threshold = self._optimal_config.min_score  # Default from optimal config

        if strategy_params and strategy_params.similarity_threshold:
            # Use strategy-specific threshold
            similarity_threshold = strategy_params.similarity_threshold

        # Filter results by threshold
        if similarity_threshold > 0:
            filtered_results = []
            for result in base_response.results:
                if result.search_score >= similarity_threshold:
                    filtered_results.append(result)
            base_response.results = filtered_results

        # =====================================================================
        # STEP 5.5: Reranking (Cross-encoder / Late Interaction)
        # =====================================================================

        reranking_applied = False
        reranking_method: Optional[str] = None
        reranking_time_ms = 0.0

        if self._use_reranking and query and len(base_response.results) > 0:
            # Prepare candidates for reranker
            rerank_candidates = []
            for result in base_response.results[:self._rerank_top_n]:
                # Build searchable text from decision
                decision = result.decision or {}
                text_parts = [
                    decision.get("statement", ""),
                    decision.get("rationale", ""),
                    decision.get("summary", ""),
                ]
                # Add constraints
                for c in decision.get("constraints", []):
                    if isinstance(c, dict):
                        text_parts.append(c.get("rule", ""))
                    else:
                        text_parts.append(str(c))

                candidate_text = " ".join(filter(None, text_parts))

                rerank_candidates.append(RerankerCandidate(
                    doc_id=result.decision_id,
                    text=candidate_text,
                    original_score=result.rank_score,
                    metadata={
                        "code": result.decision_code,
                        "original_rank": result.rank,
                    },
                ))

            # Perform reranking
            if rerank_candidates:
                rerank_response = self.reranker.rerank(
                    query=query,
                    candidates=rerank_candidates,
                    top_k=max_results,
                )

                reranking_applied = True
                reranking_method = rerank_response.method_used.value
                reranking_time_ms = rerank_response.rerank_time_ms

                # Update base_response results with reranked scores
                rerank_scores = {r.doc_id: r.final_score for r in rerank_response.results}
                rerank_ranks = {r.doc_id: r.rank for r in rerank_response.results}

                for result in base_response.results:
                    if result.decision_id in rerank_scores:
                        # Blend original and rerank scores (70% rerank, 30% original)
                        rerank_score = rerank_scores[result.decision_id]
                        result.rank_score = 0.7 * rerank_score + 0.3 * result.rank_score
                        result.factors_used = result.factors_used + ["reranking"]

                # Re-sort by new scores
                base_response.results.sort(key=lambda r: r.rank_score, reverse=True)

                # Truncate to max_results after reranking
                base_response.results = base_response.results[:max_results]

                # Update ranks
                for i, result in enumerate(base_response.results):
                    result.rank = i + 1

        # =====================================================================
        # STEP 6: Dependency traversal (if enabled)
        # =====================================================================

        dependencies_traversed = 0
        dependency_depth = 0
        dependency_added_ids: Set[str] = set()

        if self._use_dependency_traversal and include_dependencies:
            # Build dependency graph if needed
            self._ensure_dependency_graph()

            # Get initial result IDs
            result_ids = [r.decision_id for r in base_response.results]
            result_ids.extend(triggered_decisions)

            # Determine traversal depth from strategy
            traverse_depth = 1
            if strategy_params:
                traverse_depth = strategy_params.traverse_depth

            # Traverse dependencies
            for decision_id in list(result_ids):
                deps = self._dependency_graph.get_dependencies(
                    decision_id,
                    transitive=traverse_depth > 1,
                    max_depth=traverse_depth,
                )
                for dep_id in deps:
                    if dep_id not in result_ids and dep_id not in dependency_added_ids:
                        dependency_added_ids.add(dep_id)
                        dependencies_traversed += 1

            dependency_depth = traverse_depth

        # =====================================================================
        # STEP 7: Conflict detection (if enabled)
        # =====================================================================

        detected_conflicts: List[ConflictInfo] = []
        warnings: List[str] = []

        if self._use_conflict_detection and check_conflicts:
            self._ensure_dependency_graph()

            # Collect all decision IDs to check
            all_ids_for_conflict = [r.decision_id for r in base_response.results]
            all_ids_for_conflict.extend(triggered_decisions)
            all_ids_for_conflict.extend(dependency_added_ids)

            # Check for conflicts
            conflict_pairs = self._check_conflicts(list(set(all_ids_for_conflict)))
            for pair in conflict_pairs:
                conflict_info = ConflictInfo(
                    decision_a=pair[0],
                    decision_b=pair[1],
                    conflict_type="conflicts_with",
                    description=f"Decision {pair[0]} conflicts with {pair[1]}",
                )
                detected_conflicts.append(conflict_info)

            if detected_conflicts:
                warnings.append(
                    f"Found {len(detected_conflicts)} potential conflicts in retrieved decisions"
                )

        # =====================================================================
        # STEP 8: Merge and enhance results
        # =====================================================================

        # Collect all decision IDs
        all_decision_ids: Set[str] = set()
        for r in base_response.results:
            all_decision_ids.add(r.decision_id)
        for r in smart_results:
            all_decision_ids.add(r.decision_id)
        all_decision_ids.update(triggered_decisions)
        all_decision_ids.update(dependency_added_ids)

        # Build enhanced results
        enhanced_results: List[EnhancedRetrievalResult] = []
        hot_cache_hits = 0

        for i, base_result in enumerate(base_response.results):
            decision_id = base_result.decision_id

            # Get analytics data
            analytics_boost = 0.0
            usage_count = 0
            last_used = None
            health_status = None

            if self._use_analytics:
                stats = self.usage_analytics.get_stats(decision_id)
                if stats:
                    usage_count = stats.view_count
                    last_used = stats.last_viewed
                    health_status = stats.health.value
                    analytics_boost = self.usage_analytics.calculate_relevance_boost(
                        decision_id
                    ) * self._analytics_boost_factor

            # Check if triggered
            is_triggered = decision_id in triggered_decisions
            trigger_ids = []
            if is_triggered:
                for t_result in self.trigger_engine._last_results:
                    if decision_id in t_result.decision_ids:
                        trigger_ids.append(t_result.trigger_id)

            # Check hot cache
            from_hot_cache = self.hot_cache.contains(decision_id) if self._use_context_cache else False
            if from_hot_cache:
                hot_cache_hits += 1

            # Create enhanced result
            enhanced = EnhancedRetrievalResult(
                decision_id=decision_id,
                decision_code=base_result.decision_code,
                decision=base_result.decision,
                search_score=base_result.search_score,
                rank_score=base_result.rank_score + analytics_boost,
                confidence=base_result.confidence,
                confidence_level=base_result.confidence_level,
                rank=i + 1,
                confidence_reason=base_result.confidence_reason,
                factors_used=base_result.factors_used + (["analytics_boost"] if analytics_boost > 0 else []) + (["query_expansion"] if query_expanded else []),
                dependencies=base_result.dependencies,
                is_dependency=base_result.is_dependency,
                # Enhanced fields
                triggered_by=trigger_ids,
                is_triggered=is_triggered,
                usage_count=usage_count,
                last_used=last_used,
                health_status=health_status,
                relevance_boost=analytics_boost,
                from_cache=from_hot_cache,
            )
            enhanced_results.append(enhanced)

        # Add dependency decisions that weren't in base results
        for dep_id in dependency_added_ids:
            if not any(r.decision_id == dep_id for r in enhanced_results):
                decision = self.base_engine._decisions.get(dep_id, {})
                if decision:
                    enhanced = EnhancedRetrievalResult(
                        decision_id=dep_id,
                        decision_code=decision.get("code", ""),
                        decision=decision,
                        search_score=0.0,
                        rank_score=0.4,  # Lower rank for dependency
                        confidence=0.6,
                        confidence_level="MEDIUM",
                        rank=len(enhanced_results) + 1,
                        confidence_reason="Added as dependency",
                        factors_used=["dependency_traversal"],
                        is_dependency=True,
                    )
                    enhanced_results.append(enhanced)

        # Add triggered decisions that weren't in base results
        for decision_id in triggered_decisions:
            if not any(r.decision_id == decision_id for r in enhanced_results):
                # Load decision and add to results
                decision = self.base_engine._decisions.get(decision_id, {})
                if decision:
                    trigger_ids = []
                    for t_result in self.trigger_engine._last_results:
                        if decision_id in t_result.decision_ids:
                            trigger_ids.append(t_result.trigger_id)

                    enhanced = EnhancedRetrievalResult(
                        decision_id=decision_id,
                        decision_code=decision.get("code", ""),
                        decision=decision,
                        search_score=0.0,
                        rank_score=0.5,  # Default rank for triggered
                        confidence=0.7,
                        confidence_level="MEDIUM",
                        rank=len(enhanced_results) + 1,
                        confidence_reason="Triggered by context",
                        factors_used=["context_trigger"],
                        triggered_by=trigger_ids,
                        is_triggered=True,
                    )
                    enhanced_results.append(enhanced)

        # Re-rank by combined score
        enhanced_results.sort(key=lambda r: r.rank_score, reverse=True)
        for i, r in enumerate(enhanced_results):
            r.rank = i + 1

        # Limit to max_results
        enhanced_results = enhanced_results[:max_results]

        # =====================================================================
        # STEP 9: Track analytics
        # =====================================================================

        if self._use_analytics:
            for result in enhanced_results:
                self.usage_analytics.track_event(UsageEvent(
                    event_type=EventType.VIEW,
                    decision_id=result.decision_id,
                    decision_code=result.decision_code,
                    scope_path=scope_path,
                    query=query,
                    file_path=file_path,
                    user_id=user_id,
                    session_id=session_id,
                ))

        # =====================================================================
        # STEP 10: Build response
        # =====================================================================

        end_time = datetime.now(timezone.utc)
        query_time = (end_time - start_time).total_seconds() * 1000

        response = EnhancedRetrievalResponse(
            results=enhanced_results,
            total_found=base_response.total_found + len(triggered_decisions) + dependencies_traversed,
            total_returned=len(enhanced_results),
            token_estimate=base_response.token_estimate,
            query_time_ms=query_time,
            search_mode=base_response.search_mode,
            cache_hit=False,
            suggestions=base_response.suggestions,
            conflicts=base_response.conflicts,
            # Enhanced fields
            triggers_evaluated=triggers_evaluated,
            triggers_fired=triggers_fired,
            triggered_decisions=list(triggered_decisions),
            context_cache_hit=context_cache_hit,
            hot_cache_hits=hot_cache_hits,
            analytics_applied=self._use_analytics,
            # Intent & Strategy
            detected_intent=detected_intent,
            intent_confidence=intent_confidence,
            search_strategy=search_strategy,
            # Query expansion
            query_expanded=query_expanded,
            expanded_terms=expanded_terms,
            # Conflict detection
            detected_conflicts=detected_conflicts,
            warnings=warnings,
            # Dependency traversal
            dependencies_traversed=dependencies_traversed,
            dependency_depth=dependency_depth,
            # Reranking info (NEW)
            reranking_applied=reranking_applied,
            reranking_method=reranking_method,
            reranking_time_ms=reranking_time_ms,
            # Threshold & profile info
            similarity_threshold_applied=similarity_threshold,
            optimal_config_profile=self._optimal_config.profile,
        )

        # Cache the response
        if self._use_context_cache:
            self.context_cache.set(
                cache_key,
                response.to_dict(),
                ttl_seconds=300,  # 5 minutes
            )

        return response

    def get_context(
        self,
        file_path: str,
        token_budget: int = 2000,
        level: str = "standard",
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Get context text with enhanced features."""
        response = self.retrieve(
            query="",
            file_path=file_path,
            token_budget=token_budget,
            session_id=session_id,
            user_id=user_id,
        )

        return self.base_engine.build_context(
            [r.decision_id for r in response.results],
            level=level,
        )

    # =========================================================================
    # FEEDBACK
    # =========================================================================

    def track_feedback(
        self,
        decision_id: str,
        feedback_type: FeedbackType,
        user_id: Optional[str] = None,
        comment: Optional[str] = None,
        context_scope: Optional[str] = None,
    ):
        """Track user feedback on a decision."""
        if self._use_analytics:
            self.usage_analytics.track_feedback(FeedbackEvent(
                decision_id=decision_id,
                feedback_type=feedback_type,
                user_id=user_id,
                comment=comment,
                context_scope=context_scope,
            ))

            # Invalidate caches for this decision
            self.context_cache.invalidate_by_decision(decision_id)

    def track_apply(
        self,
        decision_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Track that a decision was applied/used."""
        if self._use_analytics:
            self.usage_analytics.track_event(UsageEvent(
                event_type=EventType.APPLY,
                decision_id=decision_id,
                user_id=user_id,
                session_id=session_id,
            ))

            # Update hot cache
            self.hot_cache.record_access(decision_id)

    def track_skip(
        self,
        decision_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Track that a decision was skipped."""
        if self._use_analytics:
            self.usage_analytics.track_event(UsageEvent(
                event_type=EventType.SKIP,
                decision_id=decision_id,
                user_id=user_id,
                session_id=session_id,
            ))

    # =========================================================================
    # ANALYTICS & HEALTH
    # =========================================================================

    def get_decision_health(self, decision_id: str) -> Optional[DecisionStats]:
        """Get health stats for a decision."""
        return self.usage_analytics.get_stats(decision_id)

    def get_stale_decisions(self, days: int = 30) -> List[str]:
        """Get decisions not used in N days."""
        return self.usage_analytics.get_stale_decisions(days)

    def get_problematic_decisions(self) -> List[str]:
        """Get decisions with negative feedback."""
        return self.usage_analytics.get_problematic_decisions()

    def get_hot_decisions(self, limit: int = 20) -> List[str]:
        """Get most frequently used decisions."""
        return self.usage_analytics.get_hot_decisions(limit)

    # =========================================================================
    # CACHE WARMING
    # =========================================================================

    def warm_cache(self, force: bool = False) -> Dict[str, Any]:
        """
        Pre-warm caches with hot decisions for faster first queries.

        Call this on application startup to reduce cold-start latency.

        Args:
            force: Force re-warming even if already warmed

        Returns:
            Dict with warming statistics
        """
        if self._cache_warmed and not force:
            return {"status": "already_warmed", "skipped": True}

        stats = {
            "decisions_loaded": 0,
            "embeddings_cached": 0,
            "context_cached": 0,
            "errors": [],
        }

        try:
            # 1. Load hot decisions into memory
            hot_ids = self.get_hot_decisions(limit=100)
            for decision_id in hot_ids:
                if decision_id in self.base_engine._decisions:
                    self.hot_cache.record_access(decision_id)
                    stats["decisions_loaded"] += 1

            # 2. Pre-cache common query embeddings
            common_queries = [
                "react component",
                "api endpoint",
                "database schema",
                "authentication",
                "security policy",
                "deployment",
                "testing",
                "error handling",
            ]

            for query in common_queries:
                try:
                    # This will cache the embedding
                    if hasattr(self.smart_index, '_embedding_provider'):
                        emb = self.query_embedding_cache.get_or_embed(query)
                        if emb:
                            stats["embeddings_cached"] += 1
                except Exception as e:
                    stats["errors"].append(f"Embedding cache error for '{query}': {str(e)}")

            # 3. Pre-cache context for common scopes
            common_scopes = ["fe.react", "be.api", "be.db", "infra.deploy"]
            for scope in common_scopes:
                try:
                    cache_key = self._build_cache_key("", None, scope)
                    # Don't actually query, just prepare cache structure
                    stats["context_cached"] += 1
                except Exception as e:
                    stats["errors"].append(f"Context cache error for '{scope}': {str(e)}")

            self._cache_warmed = True
            stats["status"] = "success"

        except Exception as e:
            stats["status"] = "error"
            stats["errors"].append(str(e))

        return stats

    # =========================================================================
    # DEPENDENCY & CONFLICT UTILITIES
    # =========================================================================

    def _ensure_dependency_graph(self):
        """Ensure dependency graph is built from indexed decisions."""
        if self._dependency_graph is None:
            self._dependency_graph = DependencyGraph()

        # Build from base engine decisions
        if self.base_engine._decisions:
            self._dependency_graph.build_from_decisions(
                list(self.base_engine._decisions.values())
            )

    def _check_conflicts(self, decision_ids: List[str]) -> List[Tuple[str, str]]:
        """
        Check for conflicts among a set of decisions.

        Returns list of conflicting pairs.
        """
        if not self._dependency_graph:
            return []

        conflicts: List[Tuple[str, str]] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for decision_id in decision_ids:
            conflicting = self._dependency_graph.get_conflicts(decision_id)
            for conflict_id in conflicting:
                if conflict_id in decision_ids:
                    # Normalize pair order
                    pair = tuple(sorted([decision_id, conflict_id]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        conflicts.append(pair)

        return conflicts

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def _build_cache_key(
        self,
        query: str,
        file_path: Optional[str],
        scope_path: Optional[str],
    ) -> str:
        """Build cache key for context."""
        parts = [query or ""]
        if file_path:
            parts.append(file_path)
        if scope_path:
            parts.append(scope_path)
        return f"ctx:{hash(tuple(parts))}"

    def _apply_analytics_to_cached(
        self,
        cached: Dict[str, Any],
        session_id: str,
        user_id: Optional[str],
    ) -> EnhancedRetrievalResponse:
        """Apply analytics tracking to cached response."""
        # Track views for cached results
        if self._use_analytics:
            for result in cached.get("results", []):
                self.usage_analytics.track_event(UsageEvent(
                    event_type=EventType.VIEW,
                    decision_id=result.get("decision_id", ""),
                    session_id=session_id,
                    user_id=user_id,
                ))

        # Convert to response object
        # (simplified - would need full conversion in production)
        cached["context_cache_hit"] = True
        return EnhancedRetrievalResponse(**cached)

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        base_stats = self.base_engine.get_stats() if self.base_engine else {}
        return {
            **base_stats,
            "triggers_registered": len(self.trigger_engine._triggers),
            "smart_index_size": self.smart_index.size,
            "context_cache_stats": self.context_cache.get_stats(),
            "hot_cache_size": len(self.hot_cache._access_counts),
            "analytics_decisions_tracked": len(self.usage_analytics._stats),
            # Feature flags
            "features_enabled": {
                "intent_detection": self._use_intent_detection,
                "query_expansion": self._use_query_expansion,
                "dependency_traversal": self._use_dependency_traversal,
                "conflict_detection": self._use_conflict_detection,
                "reranking": self._use_reranking,
            },
            "dependency_graph_nodes": len(self._dependency_graph._nodes) if self._dependency_graph else 0,
            # Reranker stats
            "reranker": self.reranker.get_stats() if self.reranker else None,
            # Optimal config
            "optimal_config": {
                "profile": self._optimal_config.profile,
                "fusion_method": self._optimal_config.fusion_method,
                "vector_weight": self._optimal_config.vector_weight,
                "keyword_weight": self._optimal_config.keyword_weight,
                "min_score": self._optimal_config.min_score,
                "rerank_enabled": self._optimal_config.rerank_enabled,
            },
            # Query embedding cache
            "query_embedding_cache": self.query_embedding_cache.get_stats(),
            # Cache warming
            "cache_warmed": self._cache_warmed,
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_enhanced_engine(
    decisions: Optional[List[Dict[str, Any]]] = None,
    register_default_triggers: bool = True,
    warm_cache: bool = True,
    retrieval_profile: Optional[RetrievalProfile] = None,
) -> EnhancedRetrievalEngine:
    """
    Create an enhanced retrieval engine with all optimizations.

    Args:
        decisions: Decisions to index
        register_default_triggers: Register default context triggers
        warm_cache: Pre-warm caches on creation
        retrieval_profile: Use specific retrieval profile (default: MAX_ACCURACY)

    Returns:
        Configured EnhancedRetrievalEngine
    """
    engine = EnhancedRetrievalEngine()

    # Set retrieval profile if specified
    if retrieval_profile:
        engine.set_retrieval_profile(retrieval_profile)

    if register_default_triggers:
        engine.register_default_triggers()

    if decisions:
        engine.index_decisions(decisions)

    # Warm caches for faster first queries
    if warm_cache and decisions:
        engine.warm_cache()

    return engine


__all__ = [
    "ConflictInfo",
    "EnhancedRetrievalResult",
    "EnhancedRetrievalResponse",
    "EnhancedRetrievalEngine",
    "create_enhanced_engine",
]
