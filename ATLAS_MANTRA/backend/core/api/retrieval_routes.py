"""
Enhanced Retrieval API Routes

Endpoints for context-aware decision retrieval:
- Retrieve decisions based on coding context
- Get triggered decisions for file patterns
- Query smart index with hybrid search
- Access context cache and hot decisions

These endpoints power AI assistant integrations.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..retrieval import (
    EnhancedRetrievalEngine,
    EnhancedRetrievalResponse,
    create_enhanced_engine,
    RetrievalContext,
    TriggerResult,
    TriggerType,
    get_context_cache,
    get_hot_cache,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])

# Global engine instance (should be managed by Container in production)
_engine: Optional[EnhancedRetrievalEngine] = None


def get_engine() -> EnhancedRetrievalEngine:
    """Get or create enhanced retrieval engine."""
    global _engine
    if _engine is None:
        _engine = create_enhanced_engine()
    return _engine


# ============================================================================
# Request/Response Models
# ============================================================================

class RetrievalRequest(BaseModel):
    """Request for context-aware retrieval."""
    query: str = Field(..., description="Natural language query or code context")
    file_path: Optional[str] = Field(None, description="Current file path for context")
    file_content: Optional[str] = Field(None, description="Current file content (first 2000 chars)")
    scope_path: Optional[str] = Field(None, description="Scope path for filtering")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results")
    token_budget: int = Field(2000, ge=100, le=10000, description="Token budget for response")
    use_cache: bool = Field(True, description="Use context cache")
    track_usage: bool = Field(True, description="Track usage analytics")


class RetrievalResultItem(BaseModel):
    """Single retrieval result."""
    decision_id: str
    decision_code: str
    statement: str
    rationale: Optional[str]
    confidence: float
    relevance_score: float
    source: str  # "cache", "trigger", "search", "base"
    matched_by: List[str]  # keywords, file_pattern, etc.


class RetrievalResponse(BaseModel):
    """Response with retrieved decisions."""
    results: List[RetrievalResultItem]
    total_count: int
    from_cache: bool
    triggered_by: List[str]
    execution_time_ms: float
    token_count: int
    suggestions: List[str]


class TriggerCheckRequest(BaseModel):
    """Request to check which triggers match a context."""
    file_path: Optional[str] = Field(None, description="File path to check")
    file_content: Optional[str] = Field(None, description="File content")
    scope_path: Optional[str] = Field(None, description="Scope path")
    keywords: Optional[List[str]] = Field(None, description="Additional keywords")


class TriggerCheckResponse(BaseModel):
    """Response with matching triggers."""
    triggered: bool
    triggers: List[Dict[str, Any]]
    decision_ids: List[str]


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    context_cache: Dict[str, Any]
    hot_cache: Dict[str, Any]


# ============================================================================
# Retrieval Endpoints
# ============================================================================

@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_decisions(request: RetrievalRequest):
    """
    Retrieve decisions based on coding context.

    This endpoint provides context-aware decision retrieval:
    1. Checks context cache for recent queries
    2. Evaluates context triggers (file patterns, keywords)
    3. Performs hybrid search (vector + keyword)
    4. Ranks and filters by relevance
    5. Tracks usage for analytics

    Returns decisions most relevant to the current context.
    """
    engine = get_engine()

    start_time = datetime.utcnow()

    try:
        response = engine.retrieve(
            query=request.query,
            file_path=request.file_path,
            file_content=request.file_content,
            scope_path=request.scope_path,
            max_results=request.max_results,
            token_budget=request.token_budget,
            use_cache=request.use_cache,
            track_usage=request.track_usage,
        )
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    end_time = datetime.utcnow()
    execution_time_ms = (end_time - start_time).total_seconds() * 1000

    # Convert response to API format
    results = []
    for r in response.results:
        results.append(RetrievalResultItem(
            decision_id=r.decision_id,
            decision_code=r.decision_code,
            statement=r.statement,
            rationale=r.rationale,
            confidence=r.confidence,
            relevance_score=r.relevance_score,
            source=r.source,
            matched_by=r.matched_by,
        ))

    return RetrievalResponse(
        results=results,
        total_count=len(results),
        from_cache=response.from_cache,
        triggered_by=response.triggered_by,
        execution_time_ms=execution_time_ms,
        token_count=response.token_count,
        suggestions=response.suggestions,
    )


@router.post("/check-triggers", response_model=TriggerCheckResponse)
async def check_triggers(request: TriggerCheckRequest):
    """
    Check which triggers match the given context.

    Useful for debugging trigger configurations and
    understanding which decisions would be retrieved.
    """
    engine = get_engine()

    # Build context
    context = RetrievalContext(
        file_path=request.file_path,
        file_content=request.file_content,
        scope_path=request.scope_path,
        keywords=request.keywords or [],
    )

    # Evaluate triggers
    results = engine.trigger_engine.evaluate_all(context)

    triggered = len(results) > 0
    triggers = []
    decision_ids = set()

    for r in results:
        triggers.append({
            "trigger_id": r.trigger.trigger_id,
            "name": r.trigger.name,
            "type": r.trigger.trigger_type.value,
            "priority": r.trigger.priority.value,
            "matched_patterns": r.matched_patterns,
            "decision_ids": r.trigger.decision_ids,
        })
        decision_ids.update(r.trigger.decision_ids)

    return TriggerCheckResponse(
        triggered=triggered,
        triggers=triggers,
        decision_ids=list(decision_ids),
    )


@router.get("/hot-decisions")
async def get_hot_decisions(
    limit: int = Query(20, ge=1, le=100, description="Maximum decisions"),
):
    """
    Get frequently accessed (hot) decisions.

    Hot decisions are pre-cached for fast retrieval.
    """
    cache = get_hot_cache()
    hot = cache.get_hot_decisions(limit)

    return {
        "decisions": hot,
        "count": len(hot),
        "cache_size": cache.current_size,
        "max_size": cache.max_size,
    }


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    Get cache statistics for context and hot caches.
    """
    context_cache = get_context_cache()
    hot_cache = get_hot_cache()

    context_stats = context_cache.get_stats()
    hot_stats = hot_cache.get_stats()

    return CacheStatsResponse(
        context_cache={
            "total_entries": context_stats.total_entries,
            "hit_rate": context_stats.hit_rate,
            "avg_age_seconds": context_stats.avg_age_seconds,
            "memory_bytes": context_stats.memory_bytes,
            "hits": context_stats.hits,
            "misses": context_stats.misses,
        },
        hot_cache={
            "total_entries": hot_stats.get("total_entries", 0),
            "hit_rate": hot_stats.get("hit_rate", 0.0),
            "memory_bytes": hot_stats.get("memory_bytes", 0),
        },
    )


@router.post("/cache/invalidate")
async def invalidate_cache(
    scope_path: Optional[str] = Query(None, description="Invalidate by scope"),
    decision_id: Optional[str] = Query(None, description="Invalidate by decision"),
):
    """
    Invalidate cache entries.

    Use this after decision updates to ensure fresh data.
    """
    context_cache = get_context_cache()

    if scope_path:
        invalidated = context_cache.invalidate_by_scope(scope_path)
    elif decision_id:
        invalidated = context_cache.invalidate_by_decision(decision_id)
    else:
        invalidated = context_cache.clear_all()

    return {
        "success": True,
        "invalidated_count": invalidated,
    }


@router.get("/context-window")
async def get_context_window(
    scope_path: str = Query(..., description="Scope path for context"),
    max_decisions: int = Query(10, ge=1, le=50),
    token_budget: int = Query(2000, ge=100, le=10000),
):
    """
    Get a pre-built context window for a scope.

    Returns decisions optimized for inclusion in AI context.
    """
    engine = get_engine()

    # Retrieve for scope
    response = engine.retrieve(
        query=f"scope:{scope_path}",
        scope_path=scope_path,
        max_results=max_decisions,
        token_budget=token_budget,
        use_cache=True,
    )

    # Format as context window
    context_lines = [
        f"# MANTRA Decisions for {scope_path}",
        f"# {len(response.results)} decisions, ~{response.token_count} tokens",
        "",
    ]

    for r in response.results:
        context_lines.append(f"## {r.decision_code}")
        context_lines.append(r.statement)
        if r.rationale:
            context_lines.append(f"> {r.rationale[:200]}")
        context_lines.append("")

    return {
        "scope_path": scope_path,
        "decision_count": len(response.results),
        "token_count": response.token_count,
        "context": "\n".join(context_lines),
        "decision_ids": [r.decision_id for r in response.results],
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = ["router"]
