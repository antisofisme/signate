"""
Control API Routes

Source: PUGUH UI_API_MAPPING.md - Control Domain
All endpoints are READ-ONLY.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel

from .dependencies import (
    get_current_tenant_id,
    get_list_audit_use_case,
    get_get_audit_use_case,
    get_list_events_use_case,
    get_get_event_use_case,
    get_get_metrics_use_case,
    get_retry_dlq_use_case,
)
from ..use_cases import *


class SuccessResponse(BaseModel):
    success: bool = True
    data: dict


router = APIRouter(prefix="/control", tags=["control"])


# =============================================================================
# Audit Endpoints
# =============================================================================

@router.get("/audit", response_model=SuccessResponse)
async def list_audit(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    action: Optional[str] = Query(None, description="Filter by operation type"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListAuditUseCase = Depends(get_list_audit_use_case),
):
    """List audit records. READ-ONLY."""
    result = await use_case.execute(
        tenant_id=tenant_id,
        resource_type=resource_type,
        action=action,
        page=page,
        limit=limit,
    )
    return {"success": True, "data": result}


@router.get("/audit/{audit_id}", response_model=SuccessResponse)
async def get_audit(
    audit_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetAuditUseCase = Depends(get_get_audit_use_case),
):
    """Get audit record detail. READ-ONLY."""
    result = await use_case.execute(tenant_id=tenant_id, audit_id=audit_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND"})
    return {"success": True, "data": result}


# =============================================================================
# Event Endpoints
# =============================================================================

@router.get("/events", response_model=SuccessResponse)
async def list_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    aggregate_id: Optional[UUID] = Query(None, description="Filter by aggregate ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListEventsUseCase = Depends(get_list_events_use_case),
):
    """List system events. READ-ONLY."""
    result = await use_case.execute(
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_id=aggregate_id,
        page=page,
        limit=limit,
    )
    return {"success": True, "data": result}


@router.get("/events/dlq", response_model=SuccessResponse)
async def list_dlq_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListEventsUseCase = Depends(get_list_events_use_case),
):
    """List Dead Letter Queue events. READ-ONLY."""
    result = await use_case.list_dlq(tenant_id=tenant_id, page=page, limit=limit)
    return {"success": True, "data": result}


@router.get("/events/{event_id}", response_model=SuccessResponse)
async def get_event(
    event_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetEventUseCase = Depends(get_get_event_use_case),
):
    """Get event detail. READ-ONLY."""
    result = await use_case.execute(tenant_id=tenant_id, event_id=event_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND"})
    return {"success": True, "data": result}


# =============================================================================
# Metrics Endpoints
# =============================================================================

@router.get("/metrics", response_model=SuccessResponse)
async def get_metrics(
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetMetricsUseCase = Depends(get_get_metrics_use_case),
):
    """Get system metrics overview. READ-ONLY."""
    result = await use_case.execute(tenant_id=tenant_id)
    return {"success": True, "data": result}


@router.get("/metrics/decisions", response_model=SuccessResponse)
async def get_decision_metrics(
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetMetricsUseCase = Depends(get_get_metrics_use_case),
):
    """Get decision metrics. READ-ONLY."""
    result = await use_case.get_decision_metrics(tenant_id=tenant_id)
    return {"success": True, "data": result}


@router.get("/metrics/workflows", response_model=SuccessResponse)
async def get_workflow_metrics(
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetMetricsUseCase = Depends(get_get_metrics_use_case),
):
    """Get workflow metrics. READ-ONLY."""
    result = await use_case.get_workflow_metrics(tenant_id=tenant_id)
    return {"success": True, "data": result}


@router.get("/metrics/trends", response_model=SuccessResponse)
async def get_metrics_trends(
    period: str = Query("7d", description="Time period (7d, 30d, 90d)"),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetMetricsUseCase = Depends(get_get_metrics_use_case),
):
    """Get metrics trends over time. READ-ONLY."""
    result = await use_case.get_trends(tenant_id=tenant_id, period=period)
    return {"success": True, "data": result}


# =============================================================================
# DLQ Endpoint (Direct access without /events prefix)
# =============================================================================

@router.get("/dlq", response_model=SuccessResponse)
async def list_dlq(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListEventsUseCase = Depends(get_list_events_use_case),
):
    """List Dead Letter Queue events. READ-ONLY."""
    result = await use_case.list_dlq(tenant_id=tenant_id, page=page, limit=limit)
    return {"success": True, "data": result}


@router.get("/dlq/{dlq_entry_id}", response_model=SuccessResponse)
async def get_dlq_event(
    dlq_entry_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: RetryDLQUseCase = Depends(get_retry_dlq_use_case),
):
    """Get a single DLQ event. READ-ONLY."""
    try:
        result = await use_case.get_dlq_event(tenant_id=tenant_id, dlq_entry_id=dlq_entry_id)
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)}
        )


@router.post("/dlq/{dlq_entry_id}/retry", response_model=SuccessResponse)
async def retry_dlq_event(
    dlq_entry_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: RetryDLQUseCase = Depends(get_retry_dlq_use_case),
):
    """
    Retry a DLQ event.

    Resets the event for reprocessing by the event poller.
    The event will be picked up and published again.
    """
    try:
        result = await use_case.execute(tenant_id=tenant_id, dlq_entry_id=dlq_entry_id)
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATE", "message": str(e)}
        )
