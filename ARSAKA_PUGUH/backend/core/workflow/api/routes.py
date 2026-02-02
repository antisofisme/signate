"""
Workflow API Routes

Source: PUGUH UI_API_MAPPING.md - Workflow Domain
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status

from .schemas import (
    ApproveWorkflowRequest,
    RejectWorkflowRequest,
    DelegateWorkflowRequest,
    EscalateWorkflowRequest,
    ListWorkflowsResponse,
    SuccessResponse,
)
from .dependencies import (
    get_current_user_id,
    get_current_tenant_id,
    get_list_workflows_use_case,
    get_get_workflow_use_case,
    get_approve_workflow_use_case,
    get_reject_workflow_use_case,
    get_delegate_workflow_use_case,
    get_escalate_workflow_use_case,
)
from ..use_cases import *


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=ListWorkflowsResponse)
async def list_workflows(
    assignee: Optional[str] = Query(None, description="Filter by assignee ('me' for current user)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: ListWorkflowsUseCase = Depends(get_list_workflows_use_case),
):
    """List workflows. Use assignee=me&status=pending for my pending queue."""
    assignee_id = user_id if assignee == "me" else None
    result = await use_case.execute(
        tenant_id=tenant_id,
        assignee_id=assignee_id,
        status=status,
        page=page,
        limit=limit,
    )
    return {"success": True, "data": result}


@router.get("/pending", response_model=SuccessResponse)
async def list_pending_workflows(
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: ListWorkflowsUseCase = Depends(get_list_workflows_use_case),
):
    """Get pending workflows for current user."""
    result = await use_case.execute(
        tenant_id=tenant_id,
        assignee_id=user_id,
        status="PENDING_APPROVAL",
        page=1,
        limit=100,
    )
    return {"success": True, "data": result.get("items", [])}


@router.get("/stats", response_model=SuccessResponse)
async def get_workflow_stats(
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListWorkflowsUseCase = Depends(get_list_workflows_use_case),
):
    """Get workflow statistics."""
    stats = await use_case.get_stats(tenant_id=tenant_id)
    return {"success": True, "data": stats}


@router.get("/{workflow_id}", response_model=SuccessResponse)
async def get_workflow(
    workflow_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetWorkflowUseCase = Depends(get_get_workflow_use_case),
):
    """Get workflow detail."""
    result = await use_case.execute(tenant_id=tenant_id, workflow_id=workflow_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND"})
    return {"success": True, "data": result}


@router.get("/{workflow_id}/transitions", response_model=SuccessResponse)
async def get_workflow_transitions(
    workflow_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetWorkflowUseCase = Depends(get_get_workflow_use_case),
):
    """Get workflow transition history."""
    transitions = await use_case.get_transitions(tenant_id=tenant_id, workflow_id=workflow_id)
    return {"success": True, "data": {"transitions": transitions}}


@router.post("/{workflow_id}/approve", response_model=SuccessResponse)
async def approve_workflow(
    workflow_id: UUID,
    request: ApproveWorkflowRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: ApproveWorkflowUseCase = Depends(get_approve_workflow_use_case),
):
    """Approve a workflow. This action CANNOT be undone."""
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            user_id=user_id,
            comment=request.comment,
            idempotency_key=request.idempotency_key,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "INVALID_STATE", "message": str(e)})


@router.post("/{workflow_id}/reject", response_model=SuccessResponse)
async def reject_workflow(
    workflow_id: UUID,
    request: RejectWorkflowRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: RejectWorkflowUseCase = Depends(get_reject_workflow_use_case),
):
    """Reject a workflow. This action CANNOT be undone."""
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            user_id=user_id,
            reason=request.reason,
            idempotency_key=request.idempotency_key,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "INVALID_STATE", "message": str(e)})


@router.post("/{workflow_id}/delegate", response_model=SuccessResponse)
async def delegate_workflow(
    workflow_id: UUID,
    request: DelegateWorkflowRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: DelegateWorkflowUseCase = Depends(get_delegate_workflow_use_case),
):
    """Delegate a workflow to another user."""
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            user_id=user_id,
            delegate_to=request.delegate_to_user_id,
            reason=request.reason,
            idempotency_key=request.idempotency_key,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "INVALID_STATE", "message": str(e)})


@router.post("/{workflow_id}/escalate", response_model=SuccessResponse)
async def escalate_workflow(
    workflow_id: UUID,
    request: EscalateWorkflowRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: EscalateWorkflowUseCase = Depends(get_escalate_workflow_use_case),
):
    """Escalate a workflow to a higher authority."""
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            user_id=user_id,
            escalate_to=request.escalate_to_user_id,
            reason=request.reason,
            idempotency_key=request.idempotency_key,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "INVALID_STATE", "message": str(e)})
