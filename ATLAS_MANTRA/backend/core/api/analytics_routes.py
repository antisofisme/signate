"""
Usage Analytics API Routes

Endpoints for tracking and querying decision usage analytics:
- Track usage events (view, apply, skip)
- Record feedback
- Query analytics (hot, stale, problematic decisions)
- Get decision health metrics

These endpoints help improve retrieval relevance over time.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..analytics.usage_analytics import (
    UsageAnalytics,
    UsageEvent,
    FeedbackEvent,
    EventType,
    FeedbackType,
    DecisionHealth,
    DecisionStats,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Global analytics instance (should be managed by Container in production)
_analytics: Optional[UsageAnalytics] = None


def get_analytics() -> UsageAnalytics:
    """Get or create analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = UsageAnalytics()
    return _analytics


# ============================================================================
# Request/Response Models
# ============================================================================

class TrackEventRequest(BaseModel):
    """Request to track a usage event."""
    event_type: str = Field(..., description="Event type: VIEW, APPLY, SKIP")
    decision_id: str = Field(..., description="Decision ID")
    decision_code: Optional[str] = Field(None, description="Decision code")
    scope_path: Optional[str] = Field(None, description="Context scope")
    query: Optional[str] = Field(None, description="Search query")
    file_path: Optional[str] = Field(None, description="Current file")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")


class TrackFeedbackRequest(BaseModel):
    """Request to record feedback."""
    decision_id: str = Field(..., description="Decision ID")
    feedback_type: str = Field(..., description="HELPFUL, NOT_HELPFUL, OUTDATED, UNCLEAR, WRONG_CONTEXT")
    comment: Optional[str] = Field(None, description="Feedback comment")
    context_scope: Optional[str] = Field(None, description="Context scope")
    user_id: Optional[str] = Field(None, description="User ID")


class DecisionStatsResponse(BaseModel):
    """Decision statistics response."""
    decision_id: str
    view_count: int
    apply_count: int
    skip_count: int
    feedback_count: int
    helpful_count: int
    not_helpful_count: int
    health: str
    last_viewed: Optional[str]
    last_applied: Optional[str]
    relevance_boost: float


class AnalyticsSummaryResponse(BaseModel):
    """Analytics summary response."""
    total_decisions_tracked: int
    total_events: int
    total_feedback: int
    hot_decisions_count: int
    stale_decisions_count: int
    problematic_decisions_count: int


class DecisionListResponse(BaseModel):
    """List of decisions."""
    decisions: List[str]
    count: int


# ============================================================================
# Tracking Endpoints
# ============================================================================

@router.post("/track/event")
async def track_event(request: TrackEventRequest):
    """
    Track a usage event.

    Event types:
    - VIEW: Decision was retrieved/viewed
    - APPLY: Decision was applied by user
    - SKIP: Decision was skipped/ignored
    """
    # Validate event type
    try:
        event_type = EventType(request.event_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event type: {request.event_type}. Valid: {[e.value for e in EventType]}"
        )

    analytics = get_analytics()

    event = UsageEvent(
        event_type=event_type,
        decision_id=request.decision_id,
        decision_code=request.decision_code or "",
        scope_path=request.scope_path,
        query=request.query,
        file_path=request.file_path,
        user_id=request.user_id,
        session_id=request.session_id,
    )

    analytics.track_event(event)

    return {
        "success": True,
        "event_id": event.event_id,
        "event_type": event_type.value,
    }


@router.post("/track/feedback")
async def track_feedback(request: TrackFeedbackRequest):
    """
    Record feedback on a decision.

    Feedback types:
    - HELPFUL: Decision was useful
    - NOT_HELPFUL: Decision was not useful
    - OUTDATED: Decision seems outdated
    - UNCLEAR: Decision is unclear
    - WRONG_CONTEXT: Wrong decision for the context
    """
    # Validate feedback type
    try:
        feedback_type = FeedbackType(request.feedback_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid feedback type: {request.feedback_type}. Valid: {[f.value for f in FeedbackType]}"
        )

    analytics = get_analytics()

    feedback = FeedbackEvent(
        decision_id=request.decision_id,
        feedback_type=feedback_type,
        comment=request.comment,
        context_scope=request.context_scope,
        user_id=request.user_id,
    )

    analytics.track_feedback(feedback)

    return {
        "success": True,
        "feedback_id": feedback.feedback_id,
        "feedback_type": feedback_type.value,
    }


# ============================================================================
# Query Endpoints
# ============================================================================

@router.get("/decision/{decision_id}", response_model=DecisionStatsResponse)
async def get_decision_stats(decision_id: str):
    """
    Get usage statistics for a specific decision.
    """
    analytics = get_analytics()
    stats = analytics.get_stats(decision_id)

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"No analytics found for decision: {decision_id}"
        )

    return DecisionStatsResponse(
        decision_id=stats.decision_id,
        view_count=stats.view_count,
        apply_count=stats.apply_count,
        skip_count=stats.skip_count,
        feedback_count=stats.feedback_count,
        helpful_count=stats.helpful_count,
        not_helpful_count=stats.not_helpful_count,
        health=stats.health.value,
        last_viewed=stats.last_viewed.isoformat() if stats.last_viewed else None,
        last_applied=stats.last_applied.isoformat() if stats.last_applied else None,
        relevance_boost=analytics.calculate_relevance_boost(decision_id),
    )


@router.get("/hot", response_model=DecisionListResponse)
async def get_hot_decisions(
    limit: int = Query(20, ge=1, le=100, description="Max decisions to return"),
):
    """
    Get frequently accessed (hot) decisions.

    Hot decisions have high view/apply counts.
    These should be prioritized in caching.
    """
    analytics = get_analytics()
    hot = analytics.get_hot_decisions(limit)

    return DecisionListResponse(
        decisions=hot,
        count=len(hot),
    )


@router.get("/stale", response_model=DecisionListResponse)
async def get_stale_decisions(
    days: int = Query(30, ge=1, le=365, description="Days without access"),
):
    """
    Get decisions not accessed in N days.

    Stale decisions may need:
    - Review for relevance
    - Deprecation consideration
    - Content update
    """
    analytics = get_analytics()
    stale = analytics.get_stale_decisions(days)

    return DecisionListResponse(
        decisions=stale,
        count=len(stale),
    )


@router.get("/problematic", response_model=DecisionListResponse)
async def get_problematic_decisions():
    """
    Get decisions with negative feedback.

    Problematic decisions have:
    - More NOT_HELPFUL than HELPFUL feedback
    - Multiple OUTDATED/UNCLEAR/WRONG_CONTEXT reports

    These need immediate attention.
    """
    analytics = get_analytics()
    problematic = analytics.get_problematic_decisions()

    return DecisionListResponse(
        decisions=problematic,
        count=len(problematic),
    )


@router.get("/underused", response_model=DecisionListResponse)
async def get_underused_decisions(
    min_expected_views: int = Query(10, ge=1, description="Minimum expected views"),
):
    """
    Get decisions with lower than expected usage.

    May indicate:
    - Poor discoverability
    - Irrelevant decisions
    - Need for better tagging/scope
    """
    analytics = get_analytics()

    underused = []
    for decision_id, stats in analytics._stats.items():
        if stats.view_count < min_expected_views and stats.health != DecisionHealth.NEW:
            underused.append(decision_id)

    return DecisionListResponse(
        decisions=underused,
        count=len(underused),
    )


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary():
    """
    Get overall analytics summary.
    """
    analytics = get_analytics()

    total_events = sum(
        s.view_count + s.apply_count + s.skip_count
        for s in analytics._stats.values()
    )
    total_feedback = sum(s.feedback_count for s in analytics._stats.values())

    hot = analytics.get_hot_decisions(100)
    stale = analytics.get_stale_decisions(30)
    problematic = analytics.get_problematic_decisions()

    return AnalyticsSummaryResponse(
        total_decisions_tracked=len(analytics._stats),
        total_events=total_events,
        total_feedback=total_feedback,
        hot_decisions_count=len(hot),
        stale_decisions_count=len(stale),
        problematic_decisions_count=len(problematic),
    )


@router.get("/health-distribution")
async def get_health_distribution():
    """
    Get distribution of decision health statuses.
    """
    analytics = get_analytics()

    distribution = {h.value: 0 for h in DecisionHealth}

    for stats in analytics._stats.values():
        distribution[stats.health.value] += 1

    return {
        "distribution": distribution,
        "total": len(analytics._stats),
    }


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.post("/recalculate")
async def recalculate_health():
    """
    Recalculate health status for all tracked decisions.

    This should be run periodically to update health statuses
    based on new events and time-based criteria.
    """
    analytics = get_analytics()

    updated = 0
    for stats in analytics._stats.values():
        old_health = stats.health
        analytics._calculate_health(stats)
        if stats.health != old_health:
            updated += 1

    return {
        "success": True,
        "decisions_checked": len(analytics._stats),
        "health_updated": updated,
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = ["router"]
