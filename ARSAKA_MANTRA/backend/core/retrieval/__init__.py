"""
MANTRA Retrieval System - State-of-the-Art 2025-2026 Implementation

This module provides intelligent retrieval of decisions for AI assistants.

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: SEARCH (hybrid: vector + keyword with RRF fusion)  │
│ Layer 2: RERANKING (cross-encoder / late interaction)       │
│ Layer 3: RANKING (multi-factor: quality + usage + impact)   │
│ Layer 4: OUTPUT (adaptive, token-aware, cached)             │
└─────────────────────────────────────────────────────────────┘

COMPONENTS:
- searcher.py       : Hybrid search (vector + keyword)
- fusion.py         : RRF, CombMNZ, CombSUM-Normalized, Weighted, Borda fusion
- reranker.py       : Cross-encoder, ColBERT-style, Cohere reranking
- ranker.py         : Multi-factor ranking
- cache.py          : Hot cache + pre-computed bundles
- tracker.py        : Usage tracking + feedback
- confidence.py     : Match confidence scoring
- dependencies.py   : Decision dependency graph
- proactive.py      : Pre-fetch + predictive loading
- quality.py        : Decision quality scoring
- suggester.py      : Auto-suggest missing decisions
- intent.py         : Query intent detection
- query_expander.py : Query expansion with synonyms

KEY FEATURES (2025-2026):
1. RRF (Reciprocal Rank Fusion) - Industry standard score fusion
2. Cross-Encoder Reranking - +20-35% accuracy improvement
3. Late Interaction (ColBERT-style) - Fast + accurate reranking
4. Hybrid Search - Vector + keyword combined
5. Query Expansion - Domain-specific synonyms

USAGE:
    from core.retrieval import EnhancedRetrievalEngine

    engine = EnhancedRetrievalEngine()

    # Smart retrieval with all features
    response = engine.retrieve(
        query="React component architecture",
        file_path="src/features/auth/LoginForm.tsx",
        max_results=5,
        token_budget=1500
    )

    # Results include confidence, dependencies, and reranking info
    for r in response.results:
        print(f"{r.decision_code} (score={r.rank_score:.2f})")

    # Check reranking applied
    print(f"Reranking: {response.reranking_method}")
"""

from .engine import RetrievalEngine
from .searcher import HybridSearcher, SearchResult, SearchMode, SearchConfig, FusionMode
from .ranker import RelevanceRanker, RankingFactors

# Score Fusion (RRF, Weighted, CombMNZ, CombSUM-Normalized, Borda)
from .fusion import (
    FusionMethod, FusionConfig, FusedResult, FusionResponse,
    ScoreFuser, RRFusion, WeightedLinearFusion, CombMNZFusion,
    CombSUMNormalizedFusion, BordaCountFusion,
    ScoreFusion, create_rrf_fusion, create_weighted_fusion,
    fuse_rrf, fuse_hybrid,
)

# Reranking (Cross-encoder, Late Interaction, Cohere)
from .reranker import (
    RerankerMethod, RerankerConfig, RerankerCandidate, RerankerResult, RerankerResponse,
    RerankerBackend, CrossEncoderBackend, LateInteractionBackend, CohereRerankerBackend,
    Reranker, create_reranker, create_fast_reranker, create_accurate_reranker,
)
from .cache import DecisionCache, CacheConfig
from .tracker import UsageTracker, UsageEvent
from .confidence import ConfidenceScorer, ConfidenceResult
from .dependencies import DependencyGraph, DependencyResolver
from .quality import QualityScorer, QualityScore
from .suggester import DecisionSuggester, Suggestion
from .intent import (
    QueryIntent, IntentResult, IntentDetector, AdaptiveFieldSelector,
    SearchStrategy, StrategyParams,
    INTENT_FIELDS, INTENT_TOKENS, INTENT_SEARCH_STRATEGY, STRATEGY_PARAMS,
)
from .query_expander import QueryExpander, ExpansionResult
from .prd_export import (
    ExportFormat, SectionStyle, ExportConfig,
    PRDSection, PRDDocument, PRDExporter,
    PRD_EXPORT_FIELDS, PRD_EXPORT_TOKEN_ESTIMATE,
)

# New features: Context Triggers, Smart Index, Context Cache
from .context_trigger import (
    TriggerType, CompositeOperator, TriggerPriority,
    RetrievalContext, ContextTrigger, TriggerEngine, TriggerResult,
    create_file_trigger, create_keyword_trigger, create_scope_trigger,
)
from .smart_index import (
    SearchMode as SmartSearchMode, EmbeddingModel,
    IndexedDecision, SearchResult as SmartSearchResult, SearchQuery,
    EmbeddingProvider, DummyEmbeddingProvider, LocalEmbeddingProvider,
    DecisionIndex, create_index_from_decisions,
)
from .context_cache import (
    CacheType, CacheStatus, CacheEntry, CacheStats, ContextWindow,
    ContextCache, HotDecisionsCache, get_context_cache, get_hot_cache,
)

# Optimal Configuration (Multi-Agent Optimized)
from .optimal_config import (
    RetrievalProfile,
    OptimalConfig,
    OPTIMAL_CONFIGS,
    QUERY_TYPE_ADJUSTMENTS,
    DATASET_SIZE_ADJUSTMENTS,
    get_optimal_config,
    get_config_summary,
    DEFAULT_CONFIG,
)

# Query Embedding Cache (reduces redundant API calls)
from .query_embedding_cache import (
    CachedEmbedding,
    QueryEmbeddingCache,
    AsyncQueryEmbeddingCache,
)

# Enhanced Engine (integrates all components)
from .engine_enhanced import (
    ConflictInfo,
    EnhancedRetrievalResult,
    EnhancedRetrievalResponse,
    EnhancedRetrievalEngine,
    create_enhanced_engine,
)

# Embedding Bridge (connects retrieval to embedding services)
from .embedding_bridge import (
    EmbeddingServiceBridge,
    AsyncEmbeddingProvider,
    create_embedding_provider,
    create_async_embedding_provider,
)

# Scope Resolver (DAG-based scope-aware retrieval)
from .scope_resolver import (
    ScopeMatch,
    ScopeContext,
    DecisionScopeInfo,
    MATCH_WEIGHTS,
    ScopeResolver,
    get_scope_resolver,
    resolve_query_scopes,
    get_scope_context_for_ai,
    filter_decisions_by_scope,
)

__all__ = [
    # Main engine
    "RetrievalEngine",

    # Search
    "HybridSearcher",
    "SearchResult",
    "SearchMode",
    "SearchConfig",
    "FusionMode",

    # Score Fusion (RRF, Weighted, CombMNZ, CombSUM-Normalized, Borda)
    "FusionMethod",
    "FusionConfig",
    "FusedResult",
    "FusionResponse",
    "ScoreFuser",
    "RRFusion",
    "WeightedLinearFusion",
    "CombMNZFusion",
    "CombSUMNormalizedFusion",
    "BordaCountFusion",
    "ScoreFusion",
    "create_rrf_fusion",
    "create_weighted_fusion",
    "fuse_rrf",
    "fuse_hybrid",

    # Optimal Configuration (Multi-Agent Optimized)
    "RetrievalProfile",
    "OptimalConfig",
    "OPTIMAL_CONFIGS",
    "QUERY_TYPE_ADJUSTMENTS",
    "DATASET_SIZE_ADJUSTMENTS",
    "get_optimal_config",
    "get_config_summary",
    "DEFAULT_CONFIG",

    # Query Embedding Cache
    "CachedEmbedding",
    "QueryEmbeddingCache",
    "AsyncQueryEmbeddingCache",

    # Reranking (Cross-encoder, Late Interaction, Cohere)
    "RerankerMethod",
    "RerankerConfig",
    "RerankerCandidate",
    "RerankerResult",
    "RerankerResponse",
    "RerankerBackend",
    "CrossEncoderBackend",
    "LateInteractionBackend",
    "CohereRerankerBackend",
    "Reranker",
    "create_reranker",
    "create_fast_reranker",
    "create_accurate_reranker",

    # Ranking
    "RelevanceRanker",
    "RankingFactors",

    # Cache
    "DecisionCache",
    "CacheConfig",

    # Tracking
    "UsageTracker",
    "UsageEvent",

    # Confidence
    "ConfidenceScorer",
    "ConfidenceResult",

    # Dependencies
    "DependencyGraph",
    "DependencyResolver",

    # Quality
    "QualityScorer",
    "QualityScore",

    # Suggestions
    "DecisionSuggester",
    "Suggestion",

    # Intent Detection & Adaptive Fields
    "QueryIntent",
    "IntentResult",
    "IntentDetector",
    "AdaptiveFieldSelector",
    "SearchStrategy",
    "StrategyParams",
    "INTENT_FIELDS",
    "INTENT_TOKENS",
    "INTENT_SEARCH_STRATEGY",
    "STRATEGY_PARAMS",

    # Query Expansion
    "QueryExpander",
    "ExpansionResult",

    # PRD Export
    "ExportFormat",
    "SectionStyle",
    "ExportConfig",
    "PRDSection",
    "PRDDocument",
    "PRDExporter",
    "PRD_EXPORT_FIELDS",
    "PRD_EXPORT_TOKEN_ESTIMATE",

    # Context Triggers
    "TriggerType",
    "CompositeOperator",
    "TriggerPriority",
    "RetrievalContext",
    "ContextTrigger",
    "TriggerEngine",
    "TriggerResult",
    "create_file_trigger",
    "create_keyword_trigger",
    "create_scope_trigger",

    # Smart Index
    "SmartSearchMode",
    "EmbeddingModel",
    "IndexedDecision",
    "SmartSearchResult",
    "SearchQuery",
    "EmbeddingProvider",
    "DummyEmbeddingProvider",
    "LocalEmbeddingProvider",
    "DecisionIndex",
    "create_index_from_decisions",

    # Context Cache
    "CacheType",
    "CacheStatus",
    "CacheEntry",
    "CacheStats",
    "ContextWindow",
    "ContextCache",
    "HotDecisionsCache",
    "get_context_cache",
    "get_hot_cache",

    # Enhanced Engine (integrated)
    "ConflictInfo",
    "EnhancedRetrievalResult",
    "EnhancedRetrievalResponse",
    "EnhancedRetrievalEngine",
    "create_enhanced_engine",

    # Embedding Bridge
    "EmbeddingServiceBridge",
    "AsyncEmbeddingProvider",
    "create_embedding_provider",
    "create_async_embedding_provider",

    # Scope Resolver (DAG-based)
    "ScopeMatch",
    "ScopeContext",
    "DecisionScopeInfo",
    "MATCH_WEIGHTS",
    "ScopeResolver",
    "get_scope_resolver",
    "resolve_query_scopes",
    "get_scope_context_for_ai",
    "filter_decisions_by_scope",
]
