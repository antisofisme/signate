"""
Memory API Routes

Endpoints for managing user memory (facts, timeline, summaries).
"""

from typing import Optional, List
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from ..dependencies.context import get_request_context
from ...core.entities import RequestContext, UserFact, FactType, TimeSummary, SessionSummary
from ...container import get_container
from ...shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =========================================================================
# Request/Response Schemas
# =========================================================================

class FactData(BaseModel):
    """User fact data."""
    id: str
    fact_type: str
    content: str
    confidence: float
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateFactRequest(BaseModel):
    """Request to create a fact."""
    fact_type: str = Field(..., description="Fact type: PREFERENCE, BEHAVIOR, CONTEXT, RELATIONSHIP, GENERAL")
    content: str = Field(..., min_length=1, max_length=1000)
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class UpdateFactRequest(BaseModel):
    """Request to update fact confidence."""
    confidence: float = Field(..., ge=0.0, le=1.0)


class TimelineData(BaseModel):
    """Timeline summary data."""
    id: str
    period_type: str
    period_start: date
    period_end: Optional[date] = None
    summary: Optional[str] = None
    topics: List[str] = []
    session_count: int = 0
    message_count: int = 0


class SessionSearchResult(BaseModel):
    """Session search result."""
    session_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    relevance_score: float = 0.0
    started_at: Optional[datetime] = None


# =========================================================================
# Facts Endpoints
# =========================================================================

@router.get("/facts")
async def list_facts(
    fact_type: Optional[str] = Query(None, description="Filter by type"),
    active_only: bool = Query(True, description="Only active facts"),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    List all user facts.

    Returns facts extracted from conversations.
    """
    container = await get_container()

    # Convert fact_type string to enum if provided
    ft = None
    if fact_type:
        try:
            ft = FactType(fact_type.upper())
        except ValueError:
            raise HTTPException(400, f"Invalid fact_type: {fact_type}")

    facts = await container.memory_manager.get_all_user_facts(
        ctx=ctx,
        fact_type=ft,
        active_only=active_only,
    )

    return {
        "success": True,
        "data": [
            FactData(
                id=str(f.id),
                fact_type=f.fact_type.value if isinstance(f.fact_type, FactType) else f.fact_type,
                content=f.content,
                confidence=f.confidence,
                is_active=f.is_active,
                created_at=f.created_at,
            )
            for f in facts
        ],
        "meta": {"total": len(facts)}
    }


@router.post("/facts")
async def create_fact(
    request: CreateFactRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Manually create a user fact.

    Facts can also be auto-extracted from conversations.
    """
    container = await get_container()

    try:
        fact_type = FactType(request.fact_type.upper())
    except ValueError:
        raise HTTPException(400, f"Invalid fact_type: {request.fact_type}")

    fact = UserFact(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        fact_type=fact_type,
        content=request.content,
        confidence=request.confidence,
        is_active=True,
    )

    fact_id = await container.memory_manager.add_fact(ctx, fact)

    return {
        "success": True,
        "data": {"fact_id": fact_id}
    }


@router.get("/facts/relevant")
async def get_relevant_facts(
    query: str = Query(..., min_length=1, description="Query to find relevant facts"),
    top_k: int = Query(10, ge=1, le=50),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Get facts relevant to a query.

    Uses semantic search to find facts related to the query.
    """
    container = await get_container()

    facts = await container.memory_manager.get_relevant_facts(
        ctx=ctx,
        query=query,
        top_k=top_k,
        min_confidence=min_confidence,
    )

    return {
        "success": True,
        "data": [
            FactData(
                id=str(f.id),
                fact_type=f.fact_type.value if isinstance(f.fact_type, FactType) else f.fact_type,
                content=f.content,
                confidence=f.confidence,
                is_active=f.is_active,
                created_at=f.created_at,
            )
            for f in facts
        ]
    }


@router.patch("/facts/{fact_id}")
async def update_fact(
    fact_id: str,
    request: UpdateFactRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """Update fact confidence."""
    container = await get_container()

    success = await container.semantic_memory.update_fact_confidence(
        fact_id=fact_id,
        tenant_id=ctx.tenant_id,
        new_confidence=request.confidence,
    )

    if not success:
        raise HTTPException(404, f"Fact not found: {fact_id}")

    return {"success": True, "data": {"updated": True}}


@router.delete("/facts/{fact_id}")
async def delete_fact(
    fact_id: str,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Deactivate a fact (soft delete).

    The fact is marked as inactive but not permanently deleted.
    """
    container = await get_container()

    success = await container.memory_manager.deactivate_fact(ctx, fact_id)

    if not success:
        raise HTTPException(404, f"Fact not found: {fact_id}")

    return {"success": True, "data": {"deleted": True}}


# =========================================================================
# Session Search Endpoints
# =========================================================================

@router.get("/sessions/search")
async def search_past_sessions(
    query: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(5, ge=1, le=20),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Search past conversation sessions.

    Uses semantic search on session summaries.
    """
    container = await get_container()

    sessions = await container.memory_manager.search_past_sessions(
        ctx=ctx,
        query=query,
        top_k=top_k,
    )

    return {
        "success": True,
        "data": [
            SessionSearchResult(
                session_id=s.session_id,
                title=s.title,
                summary=s.summary,
                relevance_score=s.relevance_score or 0.0,
                started_at=s.started_at,
            )
            for s in sessions
        ]
    }


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Get messages from a past session.
    """
    container = await get_container()

    messages = await container.memory_manager.get_session_messages(
        ctx=ctx,
        session_id=session_id,
        limit=limit,
    )

    return {
        "success": True,
        "data": [
            {
                "id": str(m.id),
                "role": m.role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "meta": {"total": len(messages)}
    }


# =========================================================================
# Timeline Endpoints
# =========================================================================

@router.get("/timeline")
async def get_timeline(
    period_type: str = Query("week", description="Period type: day, week, month"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Get activity timeline summaries.

    Returns summaries aggregated by time period.
    """
    container = await get_container()

    # Default to last 4 periods
    from datetime import timedelta

    if not end_date:
        end_date = date.today()
    if not start_date:
        if period_type == "day":
            start_date = end_date - timedelta(days=7)
        elif period_type == "week":
            start_date = end_date - timedelta(weeks=4)
        else:  # month
            start_date = end_date - timedelta(days=120)

    summaries = await container.memory_manager.get_activity_timeline(
        ctx=ctx,
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "success": True,
        "data": [
            TimelineData(
                id=str(s.id),
                period_type=s.period_type,
                period_start=s.period_start,
                period_end=s.period_end,
                summary=s.summary,
                topics=s.topics or [],
                session_count=s.session_count,
                message_count=s.message_count,
            )
            for s in summaries
        ]
    }


@router.get("/timeline/{period_type}/{period_start}")
async def get_period_summary(
    period_type: str,
    period_start: date,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Get summary for a specific time period.
    """
    container = await get_container()

    if period_type not in ["day", "week", "month"]:
        raise HTTPException(400, f"Invalid period_type: {period_type}")

    summary = await container.memory_manager.get_temporal_summary(
        ctx=ctx,
        period_type=period_type,
        period_start=period_start,
    )

    if not summary:
        raise HTTPException(404, f"No summary found for {period_type} starting {period_start}")

    return {
        "success": True,
        "data": TimelineData(
            id=str(summary.id),
            period_type=summary.period_type,
            period_start=summary.period_start,
            period_end=summary.period_end,
            summary=summary.summary,
            topics=summary.topics or [],
            session_count=summary.session_count,
            message_count=summary.message_count,
        )
    }


# =========================================================================
# Context Assembly Endpoint
# =========================================================================

@router.get("/context")
async def get_assembled_context(
    session_id: str = Query(..., description="Current session ID"),
    query: str = Query(..., description="Current query/message"),
    max_tokens: int = Query(6000, ge=1000, le=16000),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Get assembled context from all memory layers.

    Returns unified context for LLM generation.
    """
    container = await get_container()

    context = await container.memory_manager.assemble_context(
        ctx=ctx,
        session_id=session_id,
        query=query,
        max_tokens=max_tokens,
    )

    # Format for response
    return {
        "success": True,
        "data": {
            "working_messages": len(context.get("working_messages", [])),
            "relevant_facts": [
                {"content": f.content, "confidence": f.confidence}
                for f in context.get("relevant_facts", [])
            ],
            "relevant_sessions": [
                {"session_id": s.session_id, "summary": s.summary[:200] if s.summary else None}
                for s in context.get("relevant_sessions", [])
            ],
            "recent_summary": context.get("recent_summary"),
            "total_tokens": context.get("total_tokens", 0),
            "formatted_context": container.memory_manager.format_context_for_llm(context),
        }
    }
