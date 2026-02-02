"""
Search API Routes - Semantic search endpoints for MANTRA.

This module provides HTTP endpoints for:
- Semantic search for decisions
- Alignment checking for proposals
- Index management (rebuild, stats)

All endpoints use the Clean Architecture use cases and
the dependency injection container for adapters.
"""

import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field

from core.use_cases.search_decisions import (
    SearchDecisionsUseCase,
    SearchDecisionsInput,
)
from core.use_cases.check_alignment import (
    CheckAlignmentUseCase,
    CheckAlignmentInput,
)
from core.use_cases.sync_embeddings import (
    SyncEmbeddingsUseCase,
    SyncEmbeddingsInput,
)
from core.domain.search_result import SearchStatus, AlignmentStatus
from factory.container import Container
from core.api.routes import get_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["search"])


# ==================== Request/Response Models ====================

class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., description="Natural language search query", min_length=3)
    limit: int = Field(10, description="Maximum results", ge=1, le=100)
    min_score: float = Field(0.5, description="Minimum similarity score", ge=0.0, le=1.0)
    domain_id: Optional[str] = Field(None, description="Filter by domain (INT, ARCH, CTL, EVO)")
    aspect_id: Optional[str] = Field(None, description="Filter by aspect (F01-F16)")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    use_cache: bool = Field(True, description="Use cached results if available")


class SearchHitResponse(BaseModel):
    """A single search result hit."""
    decision_id: str
    decision_code: str
    statement: str
    rationale: str
    score: float
    domain_id: str
    aspect_id: str
    version: str
    tags: List[str]
    matched_fields: List[str]


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""
    status: str
    hits: List[SearchHitResponse]
    total_count: int
    query: str
    filters_applied: Dict[str, Any]
    execution_time_ms: float
    cached: bool
    error_message: Optional[str] = None


class CheckAlignmentRequest(BaseModel):
    """Request for alignment check."""
    statement: str = Field(..., description="Proposed decision statement", min_length=10)
    rationale: str = Field("", description="Proposed rationale")
    domain_id: Optional[str] = Field(None, description="Scope check to specific domain")
    min_score: float = Field(0.6, description="Minimum similarity threshold", ge=0.0, le=1.0)


class CheckAlignmentResponse(BaseModel):
    """Response for alignment check."""
    status: str
    aligned_with: List[SearchHitResponse]
    conflicts_with: List[SearchHitResponse]
    related_decisions: List[SearchHitResponse]
    recommendations: List[str]
    execution_time_ms: float
    error_message: Optional[str] = None


class RebuildIndexRequest(BaseModel):
    """Request for index rebuild."""
    force: bool = Field(False, description="Force re-embed all decisions")
    batch_size: int = Field(50, description="Decisions per batch", ge=1, le=200)
    domain_id: Optional[str] = Field(None, description="Rebuild specific domain only")


class RebuildIndexResponse(BaseModel):
    """Response for index rebuild."""
    synced_count: int
    skipped_count: int
    failed_count: int
    total_decisions: int
    execution_time_ms: float
    errors: List[str]


class IndexStatsResponse(BaseModel):
    """Response for index statistics."""
    collection_name: str
    count: int
    vector_size: int
    status: str
    cache_enabled: bool
    embedding_model: str
    embedding_dimensions: int


class HybridSearchRequest(BaseModel):
    """Request for hybrid search (semantic + text)."""
    query: str = Field(..., description="Natural language search query", min_length=3)
    limit: int = Field(20, description="Maximum results", ge=1, le=100)
    min_score: float = Field(0.3, description="Minimum similarity score", ge=0.0, le=1.0)
    domain_id: Optional[str] = Field(None, description="Filter by domain (INT, ARCH, CTL, EVO)")
    aspect_id: Optional[str] = Field(None, description="Filter by aspect")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    use_cache: bool = Field(True, description="Use cached results if available")
    semantic_weight: float = Field(0.6, description="Weight for semantic results (0.0-1.0)", ge=0.0, le=1.0)


class HybridSearchResponse(BaseModel):
    """Response for hybrid search."""
    status: str
    hits: List[SearchHitResponse]
    total_count: int
    query: str
    filters_applied: Dict[str, Any]
    execution_time_ms: float
    cached: bool
    search_modes_used: List[str]
    error_message: Optional[str] = None


class TextSearchRequest(BaseModel):
    """Request for full-text search."""
    query: str = Field(..., description="Text search query", min_length=2)
    limit: int = Field(20, description="Maximum results", ge=1, le=100)
    offset: int = Field(0, description="Results to skip", ge=0)
    domain_id: Optional[str] = Field(None, description="Filter by domain")
    highlight: bool = Field(True, description="Include highlighted snippets")


class TextSearchResponse(BaseModel):
    """Response for full-text search."""
    status: str
    hits: List[Dict[str, Any]]
    total_count: int
    query: str
    execution_time_ms: float
    error_message: Optional[str] = None


# ==================== Endpoints ====================

@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search for decisions using vector similarity.

    Returns decisions ranked by semantic relevance to the query.
    Supports filtering by group, feature, and tags.

    **Example:**
    ```json
    {
        "query": "database technology decision",
        "limit": 10,
        "min_score": 0.5,
        "domain_id": "INT"
    }
    ```
    """
    if not Container.is_semantic_search_enabled():
        raise HTTPException(
            status_code=503,
            detail="Semantic search is disabled"
        )

    use_case = SearchDecisionsUseCase(
        vector_store=Container.get_vector_store(),
        cache=Container.get_cache(),
        embedding_service=Container.get_embedding(),
        repository=get_repository(),
    )

    result = await use_case.execute(SearchDecisionsInput(
        query=request.query,
        limit=request.limit,
        min_score=request.min_score,
        domain_id=request.domain_id,
        aspect_id=request.aspect_id,
        tags=request.tags,
        use_cache=request.use_cache,
    ))

    return SemanticSearchResponse(
        status=result.status.value,
        hits=[SearchHitResponse(**h.to_dict()) for h in result.hits],
        total_count=result.total_count,
        query=result.query,
        filters_applied=result.filters_applied,
        execution_time_ms=result.execution_time_ms,
        cached=result.cached,
        error_message=result.error_message,
    )


@router.post("/check-alignment", response_model=CheckAlignmentResponse)
async def check_alignment(request: CheckAlignmentRequest):
    """
    Check if a proposal aligns with existing decisions.

    Returns conflicts, related decisions, and recommendations.
    Use this before proposing a new decision to ensure alignment.

    **Example:**
    ```json
    {
        "statement": "Use MongoDB for user data storage",
        "rationale": "MongoDB offers schema flexibility"
    }
    ```
    """
    if not Container.is_semantic_search_enabled():
        raise HTTPException(
            status_code=503,
            detail="Semantic search is disabled"
        )

    use_case = CheckAlignmentUseCase(
        vector_store=Container.get_vector_store(),
        cache=Container.get_cache(),
        embedding_service=Container.get_embedding(),
        repository=get_repository(),
    )

    result = await use_case.execute(CheckAlignmentInput(
        statement=request.statement,
        rationale=request.rationale,
        domain_id=request.domain_id,
        min_score=request.min_score,
    ))

    return CheckAlignmentResponse(
        status=result.status.value,
        aligned_with=[SearchHitResponse(**h.to_dict()) for h in result.aligned_with],
        conflicts_with=[SearchHitResponse(**h.to_dict()) for h in result.conflicts_with],
        related_decisions=[SearchHitResponse(**h.to_dict()) for h in result.related_decisions],
        recommendations=result.recommendations,
        execution_time_ms=result.execution_time_ms,
        error_message=result.error_message,
    )


@router.post("/rebuild-index", response_model=RebuildIndexResponse)
async def rebuild_index(request: RebuildIndexRequest = None):
    """
    Rebuild the vector index from all decisions.

    Admin endpoint for maintenance. Use after bulk imports or
    when the index becomes inconsistent.

    **Note:** This may take time for large datasets.
    """
    if not Container.is_semantic_search_enabled():
        raise HTTPException(
            status_code=503,
            detail="Semantic search is disabled"
        )

    request = request or RebuildIndexRequest()

    use_case = SyncEmbeddingsUseCase(
        vector_store=Container.get_vector_store(),
        embedding_service=Container.get_embedding(),
        repository=get_repository(),
    )

    result = await use_case.execute(SyncEmbeddingsInput(
        batch_size=request.batch_size,
        force_rebuild=request.force,
        domain_id=request.domain_id,
    ))

    return RebuildIndexResponse(
        synced_count=result.synced_count,
        skipped_count=result.skipped_count,
        failed_count=result.failed_count,
        total_decisions=result.total_decisions,
        execution_time_ms=result.execution_time_ms,
        errors=result.errors,
    )


@router.get("/stats", response_model=IndexStatsResponse)
async def get_index_stats():
    """
    Get vector index statistics.

    Returns collection info, embedding configuration,
    and cache status.
    """
    from ..runtime.config import get_config

    config = get_config()

    if not Container.is_semantic_search_enabled():
        return IndexStatsResponse(
            collection_name="disabled",
            count=0,
            vector_size=0,
            status="disabled",
            cache_enabled=False,
            embedding_model="none",
            embedding_dimensions=0,
        )

    vector_store = Container.get_vector_store()
    info = await vector_store.get_collection_info()

    return IndexStatsResponse(
        collection_name=info.get("name", "unknown"),
        count=info.get("count", 0),
        vector_size=info.get("vector_size", 0),
        status=info.get("status", "unknown"),
        cache_enabled=config.cache != "none",
        embedding_model=config.embedding_model,
        embedding_dimensions=config.embedding_dimensions,
    )


@router.delete("/cache")
async def clear_search_cache():
    """
    Clear the search cache.

    Use when cached results need to be refreshed.
    """
    if not Container.is_semantic_search_enabled():
        raise HTTPException(
            status_code=503,
            detail="Semantic search is disabled"
        )

    cache = Container.get_cache()
    await cache.delete_pattern("search:*")

    return {"message": "Search cache cleared"}


@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    Hybrid search combining semantic (vector) and full-text search.

    This endpoint merges results from both:
    - **Semantic search** (Qdrant): Understands meaning and context
    - **Text search** (Meilisearch): Fast keyword matching with typo tolerance

    Results are ranked by a weighted combination of both scores.

    **When to use:**
    - General queries that benefit from both approaches
    - When you want the best of both worlds

    **Example:**
    ```json
    {
        "query": "PostgreSQL database scaling",
        "limit": 20,
        "semantic_weight": 0.6
    }
    ```
    """
    import time
    import hashlib
    from core.ports.cache import CacheKeys, CacheTTL
    from core.ports.text_search import TextSearchQuery

    start_time = time.time()
    search_modes = []
    all_hits = {}  # decision_id -> (hit, combined_score)

    # Check cache
    cache = Container.get_cache()
    if request.use_cache:
        cache_key_data = f"hybrid:{request.query}:{request.limit}:{request.min_score}:{request.domain_id}:{request.semantic_weight}"
        cache_key = CacheKeys.search_hybrid(hashlib.sha256(cache_key_data.encode()).hexdigest()[:16])
        cached = await cache.get(cache_key)
        if cached:
            return HybridSearchResponse(
                status="found",
                hits=[SearchHitResponse(**h) for h in cached["hits"]],
                total_count=cached["total_count"],
                query=request.query,
                filters_applied=cached.get("filters_applied", {}),
                execution_time_ms=(time.time() - start_time) * 1000,
                cached=True,
                search_modes_used=cached.get("search_modes_used", []),
            )

    # 1. Semantic search (if enabled)
    if Container.is_semantic_search_enabled():
        try:
            use_case = SearchDecisionsUseCase(
                vector_store=Container.get_vector_store(),
                cache=Container.get_cache(),
                embedding_service=Container.get_embedding(),
                repository=get_repository(),
            )

            semantic_result = await use_case.execute(SearchDecisionsInput(
                query=request.query,
                limit=request.limit,
                min_score=request.min_score,
                domain_id=request.domain_id,
                aspect_id=request.aspect_id,
                tags=request.tags,
                use_cache=False,  # We handle caching at hybrid level
            ))

            search_modes.append("semantic")

            # Add semantic results with weighted score
            for hit in semantic_result.hits:
                weighted_score = hit.score * request.semantic_weight
                all_hits[hit.decision_id] = (hit, weighted_score)

        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")

    # 2. Text search (if enabled)
    text_search = Container.get_text_search()
    if text_search:
        try:
            # Build filters
            filters = {}
            if request.domain_id:
                filters["domain_id"] = request.domain_id
            if request.aspect_id:
                filters["aspect_id"] = request.aspect_id

            text_results = await text_search.search(TextSearchQuery(
                query=request.query,
                filters=filters if filters else None,
                limit=request.limit,
            ))

            search_modes.append("text")
            text_weight = 1.0 - request.semantic_weight

            # Merge text results
            for tr in text_results:
                doc = tr.document
                decision_id = doc.get("id", tr.id)

                if decision_id in all_hits:
                    # Combine scores
                    existing_hit, existing_score = all_hits[decision_id]
                    combined_score = existing_score + (tr.score * text_weight)
                    all_hits[decision_id] = (existing_hit, combined_score)
                else:
                    # Create new hit from text result
                    new_hit = SearchHitResponse(
                        decision_id=decision_id,
                        decision_code=doc.get("decision_code", decision_id),
                        statement=doc.get("statement", ""),
                        rationale=doc.get("rationale", ""),
                        score=tr.score * text_weight,
                        domain_id=doc.get("domain_id", ""),
                        aspect_id=doc.get("aspect_id", ""),
                        version=doc.get("version", "1.0.0"),
                        tags=doc.get("tags", []),
                        matched_fields=list(tr.highlights.keys()),
                    )
                    all_hits[decision_id] = (new_hit, tr.score * text_weight)

        except Exception as e:
            logger.warning(f"Text search failed: {e}")

    # 3. Sort and limit results
    sorted_hits = sorted(all_hits.values(), key=lambda x: x[1], reverse=True)
    final_hits = []
    for hit, combined_score in sorted_hits[:request.limit]:
        # Update hit with combined score
        hit_dict = hit.model_dump() if hasattr(hit, 'model_dump') else hit.__dict__
        hit_dict["score"] = combined_score
        final_hits.append(SearchHitResponse(**hit_dict))

    # Determine status
    status = "found" if final_hits else "not_found"
    if not search_modes:
        status = "error"

    filters_applied = {}
    if request.domain_id:
        filters_applied["domain_id"] = request.domain_id
    if request.aspect_id:
        filters_applied["aspect_id"] = request.aspect_id
    if request.tags:
        filters_applied["tags"] = request.tags

    # Cache results
    if request.use_cache and final_hits:
        cache_data = {
            "hits": [h.model_dump() if hasattr(h, 'model_dump') else h.__dict__ for h in final_hits],
            "total_count": len(final_hits),
            "filters_applied": filters_applied,
            "search_modes_used": search_modes,
        }
        await cache.set(cache_key, cache_data, ttl=CacheTTL.SEARCH_RESULTS)

    return HybridSearchResponse(
        status=status,
        hits=final_hits,
        total_count=len(final_hits),
        query=request.query,
        filters_applied=filters_applied,
        execution_time_ms=(time.time() - start_time) * 1000,
        cached=False,
        search_modes_used=search_modes,
    )


@router.post("/text", response_model=TextSearchResponse)
async def text_search(request: TextSearchRequest):
    """
    Full-text search using Meilisearch.

    Fast keyword-based search with:
    - Typo tolerance
    - Instant results
    - Highlighted matches

    **When to use:**
    - Exact keyword searches
    - When you know specific terms
    - For fast autocomplete-style queries

    **Example:**
    ```json
    {
        "query": "PostgreSQL",
        "limit": 20,
        "highlight": true
    }
    ```
    """
    import time
    from core.ports.text_search import TextSearchQuery

    start_time = time.time()

    text_search_service = Container.get_text_search()
    if not text_search_service:
        raise HTTPException(
            status_code=503,
            detail="Text search is disabled. Enable with FEATURE_MEILISEARCH_ENABLED=true"
        )

    try:
        # Build filters
        filters = {}
        if request.domain_id:
            filters["domain_id"] = request.domain_id

        results = await text_search_service.search(TextSearchQuery(
            query=request.query,
            filters=filters if filters else None,
            limit=request.limit,
            offset=request.offset,
            highlight_fields=["statement", "rationale"] if request.highlight else None,
        ))

        hits = []
        for r in results:
            hit_data = r.document.copy()
            hit_data["score"] = r.score
            if request.highlight and r.highlights:
                hit_data["highlights"] = r.highlights
            hits.append(hit_data)

        return TextSearchResponse(
            status="found" if hits else "not_found",
            hits=hits,
            total_count=len(hits),
            query=request.query,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        logger.error(f"Text search error: {e}")
        return TextSearchResponse(
            status="error",
            hits=[],
            total_count=0,
            query=request.query,
            execution_time_ms=(time.time() - start_time) * 1000,
            error_message=str(e),
        )


@router.get("/services-status")
async def get_search_services_status():
    """
    Get status of all search services.

    Returns health and feature status for:
    - Semantic search (Qdrant)
    - Text search (Meilisearch)
    - Message queue (RabbitMQ)
    - Cache (Redis)
    """
    from ..runtime.config import get_config

    config = get_config()
    status = {
        "semantic_search": {
            "enabled": config.enable_semantic_search,
            "healthy": False,
        },
        "text_search": {
            "enabled": config.feature_meilisearch_enabled,
            "healthy": False,
        },
        "message_queue": {
            "enabled": config.feature_rabbitmq_enabled,
            "healthy": False,
        },
        "cache": {
            "enabled": config.cache != "none",
            "healthy": False,
        },
    }

    # Check semantic search
    if Container.is_semantic_search_enabled():
        try:
            vector_store = Container.get_vector_store()
            status["semantic_search"]["healthy"] = await vector_store.collection_exists()
        except Exception:
            pass

    # Check text search
    text_search = Container.get_text_search()
    if text_search:
        try:
            status["text_search"]["healthy"] = await text_search.health_check()
        except Exception:
            pass

    # Check message queue
    message_queue = Container.get_message_queue()
    if message_queue:
        try:
            status["message_queue"]["healthy"] = await message_queue.health_check()
        except Exception:
            pass

    # Check cache
    try:
        cache = Container.get_cache()
        if hasattr(cache, 'health_check'):
            status["cache"]["healthy"] = await cache.health_check()
        else:
            status["cache"]["healthy"] = True  # Assume healthy if no health check
    except Exception:
        pass

    return status
