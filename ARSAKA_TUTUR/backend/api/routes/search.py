"""
Search API Routes.

Semantic search endpoints for knowledge retrieval.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query

from ..schemas.requests import SearchRequest
from ..schemas.responses import SearchResponse, SearchResultItem
from ..dependencies.context import get_request_context
from ...core.entities import RequestContext
from ...container import get_container
from ...shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Search the knowledge base using semantic similarity.

    Returns documents ranked by relevance to the query.
    """
    container = await get_container()

    # Use RAG orchestrator for search
    result = await container.rag_orchestrator.search(
        ctx=ctx,
        query=request.query,
        top_k=request.top_k,
        filters=request.filters,
        score_threshold=request.score_threshold,
    )

    # Convert to response format
    items = [
        SearchResultItem(
            id=r.id,
            content=r.content,
            score=r.score,
            document_id=r.document_id,
            metadata=r.metadata,
        )
        for r in result.results
    ]

    return SearchResponse(
        success=True,
        data={
            "results": items,
            "query": request.query,
            "strategy": result.strategy_used,
        },
        meta={
            "total": len(items),
            "retrieval_time_ms": result.retrieval_time_ms,
            "was_reranked": result.was_reranked,
        }
    )


@router.get("/similar")
async def find_similar(
    document_id: str = Query(..., description="Document ID to find similar to"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results"),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Find documents similar to a given document.

    Uses the document's embedding to find semantically similar content.
    """
    container = await get_container()

    # Get document's embedding from vector store
    collection = f"knowledge_{ctx.tenant_id}"

    # Retrieve the document first
    doc_point = await container.vector_store.get_by_id(collection, document_id)
    if not doc_point:
        return SearchResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Document {document_id} not found"
            }
        )

    # Search using document's vector
    results = await container.vector_store.search(
        collection=collection,
        query_vector=doc_point["vector"],
        top_k=top_k + 1,  # +1 to exclude self
        filters={"tenant_id": ctx.tenant_id},
    )

    # Filter out the source document
    items = [
        SearchResultItem(
            id=r.id,
            content=r.content,
            score=r.score,
            document_id=r.document_id,
            metadata=r.metadata,
        )
        for r in results
        if r.id != document_id
    ][:top_k]

    return SearchResponse(
        success=True,
        data={"results": items, "source_document": document_id},
        meta={"total": len(items)}
    )


@router.get("/stats")
async def get_search_stats(
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Get statistics about the knowledge base for this tenant.
    """
    container = await get_container()

    stats = await container.rag_orchestrator.get_collection_stats(ctx.tenant_id)

    return {
        "success": True,
        "data": stats
    }
