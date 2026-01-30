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
from typing import List, Optional, Dict, Any, Set
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
from ..analytics.usage_analytics import (
    UsageAnalytics, UsageEvent, EventType, FeedbackEvent, FeedbackType,
    DecisionHealth, DecisionStats,
)


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

        # Configuration
        self._use_triggers = True
        self._use_smart_index = True
        self._use_context_cache = True
        self._use_analytics = True
        self._analytics_boost_factor = 0.2  # Max 20% boost from analytics

    def configure(
        self,
        use_triggers: bool = True,
        use_smart_index: bool = True,
        use_context_cache: bool = True,
        use_analytics: bool = True,
        analytics_boost_factor: float = 0.2,
    ):
        """Configure which features are enabled."""
        self._use_triggers = use_triggers
        self._use_smart_index = use_smart_index
        self._use_context_cache = use_context_cache
        self._use_analytics = use_analytics
        self._analytics_boost_factor = analytics_boost_factor

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
        max_results: int = 10,
        token_budget: int = 3000,
        min_confidence: str = "LOW",
        include_dependencies: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> EnhancedRetrievalResponse:
        """
        Enhanced retrieval with triggers, smart index, and analytics.

        Args:
            query: Natural language query
            file_path: Current file path
            file_content: Current file content (for content matching)
            scope_path: Current scope (e.g., "fe.react")
            domain_id: Filter by domain
            tags: Filter by tags
            max_results: Maximum results
            token_budget: Token limit
            min_confidence: Minimum confidence
            include_dependencies: Include dependencies
            session_id: For tracking
            user_id: For analytics

        Returns:
            EnhancedRetrievalResponse
        """
        start_time = datetime.now(timezone.utc)
        session_id = session_id or str(uuid.uuid4())

        # Build retrieval context
        context = RetrievalContext(
            file_path=file_path,
            file_content=file_content,
            query=query,
            scope_path=scope_path,
            scope_tags=tags,
        )

        triggered_decisions: Set[str] = set()
        triggers_evaluated = 0
        triggers_fired = 0

        # =====================================================================
        # STEP 1: Check context cache
        # =====================================================================

        cache_key = self._build_cache_key(query, file_path, scope_path)
        context_cache_hit = False

        if self._use_context_cache:
            cached = self.context_cache.get(cache_key)
            if cached:
                context_cache_hit = True
                # Return cached response with analytics update
                return self._apply_analytics_to_cached(cached, session_id, user_id)

        # =====================================================================
        # STEP 2: Evaluate triggers
        # =====================================================================

        if self._use_triggers:
            trigger_results = self.trigger_engine.evaluate(context)
            triggers_evaluated = len(self.trigger_engine._triggers)
            triggers_fired = len([r for r in trigger_results if r.matched])

            for result in trigger_results:
                if result.matched:
                    triggered_decisions.update(result.decision_ids)

        # =====================================================================
        # STEP 3: Smart index search
        # =====================================================================

        smart_results: List[SmartSearchResult] = []
        if self._use_smart_index and self.smart_index.size > 0:
            search_query = SearchQuery(
                text=query,
                tags=tags,
                scope_path=scope_path,
                limit=max_results * 2,  # Get more for ranking
            )
            smart_results = self.smart_index.search(search_query)

        # =====================================================================
        # STEP 4: Base engine retrieval
        # =====================================================================

        base_response = self.base_engine.retrieve(
            query=query,
            file_path=file_path,
            domain_id=domain_id,
            tags=tags,
            max_results=max_results,
            token_budget=token_budget,
            min_confidence=min_confidence,
            include_dependencies=include_dependencies,
            session_id=session_id,
        )

        # =====================================================================
        # STEP 5: Merge and enhance results
        # =====================================================================

        # Collect all decision IDs
        all_decision_ids: Set[str] = set()
        for r in base_response.results:
            all_decision_ids.add(r.decision_id)
        for r in smart_results:
            all_decision_ids.add(r.decision_id)
        all_decision_ids.update(triggered_decisions)

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
                factors_used=base_result.factors_used + (["analytics_boost"] if analytics_boost > 0 else []),
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
        # STEP 6: Track analytics
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
        # STEP 7: Build response
        # =====================================================================

        end_time = datetime.now(timezone.utc)
        query_time = (end_time - start_time).total_seconds() * 1000

        response = EnhancedRetrievalResponse(
            results=enhanced_results,
            total_found=base_response.total_found + len(triggered_decisions),
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
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_enhanced_engine(
    decisions: Optional[List[Dict[str, Any]]] = None,
    register_default_triggers: bool = True,
) -> EnhancedRetrievalEngine:
    """
    Create an enhanced retrieval engine.

    Args:
        decisions: Decisions to index
        register_default_triggers: Register default context triggers

    Returns:
        Configured EnhancedRetrievalEngine
    """
    engine = EnhancedRetrievalEngine()

    if register_default_triggers:
        engine.register_default_triggers()

    if decisions:
        engine.index_decisions(decisions)

    return engine


__all__ = [
    "EnhancedRetrievalResult",
    "EnhancedRetrievalResponse",
    "EnhancedRetrievalEngine",
    "create_enhanced_engine",
]
