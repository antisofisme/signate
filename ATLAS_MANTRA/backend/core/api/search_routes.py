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
    group_id: Optional[str] = Field(None, description="Filter by group (INT, ARCH, CTL, EVO)")
    feature_id: Optional[str] = Field(None, description="Filter by feature (F01-F16)")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    use_cache: bool = Field(True, description="Use cached results if available")


class SearchHitResponse(BaseModel):
    """A single search result hit."""
    decision_id: str
    decision_code: str
    statement: str
    rationale: str
    score: float
    group_id: str
    feature_id: str
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
    group_id: Optional[str] = Field(None, description="Scope check to specific group")
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
    group_id: Optional[str] = Field(None, description="Rebuild specific group only")


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
        "group_id": "INT"
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
        group_id=request.group_id,
        feature_id=request.feature_id,
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
        group_id=request.group_id,
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
        group_id=request.group_id,
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
