"""
MANTRA Retrieval System - 9.5/10 Implementation

This module provides intelligent retrieval of decisions for AI assistants.

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: SEARCH (vector + keyword hybrid)                   │
│ Layer 2: RANKING (relevance + quality + usage)              │
│ Layer 3: OUTPUT (adaptive, token-aware, cached)             │
└─────────────────────────────────────────────────────────────┘

COMPONENTS:
- searcher.py      : Hybrid search (vector + keyword)
- ranker.py        : Multi-factor ranking
- cache.py         : Hot cache + pre-computed bundles
- tracker.py       : Usage tracking + feedback
- confidence.py    : Match confidence scoring
- dependencies.py  : Decision dependency graph
- proactive.py     : Pre-fetch + predictive loading
- quality.py       : Decision quality scoring
- suggester.py     : Auto-suggest missing decisions

USAGE:
    from core.retrieval import RetrievalEngine

    engine = RetrievalEngine()

    # Simple retrieval
    results = engine.retrieve(
        query="React component architecture",
        file_path="src/features/auth/LoginForm.tsx",
        max_results=5,
        token_budget=1500
    )

    # Results include confidence and dependencies
    for r in results:
        print(f"{r.decision.code} ({r.confidence:.0%})")
"""

from .engine import RetrievalEngine
from .searcher import HybridSearcher, SearchResult, SearchMode, SearchConfig
from .ranker import RelevanceRanker, RankingFactors
from .cache import DecisionCache, CacheConfig
from .tracker import UsageTracker, UsageEvent
from .confidence import ConfidenceScorer, ConfidenceResult
from .dependencies import DependencyGraph, DependencyResolver
from .quality import QualityScorer, QualityScore
from .suggester import DecisionSuggester, Suggestion
from .intent import (
    QueryIntent, IntentResult, IntentDetector, AdaptiveFieldSelector,
    INTENT_FIELDS, INTENT_TOKENS,
)
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

# Enhanced Engine (integrates all components)
from .engine_enhanced import (
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

__all__ = [
    # Main engine
    "RetrievalEngine",

    # Search
    "HybridSearcher",
    "SearchResult",
    "SearchMode",
    "SearchConfig",

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
    "INTENT_FIELDS",
    "INTENT_TOKENS",

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
    "EnhancedRetrievalResult",
    "EnhancedRetrievalResponse",
    "EnhancedRetrievalEngine",
    "create_enhanced_engine",

    # Embedding Bridge
    "EmbeddingServiceBridge",
    "AsyncEmbeddingProvider",
    "create_embedding_provider",
    "create_async_embedding_provider",
]
