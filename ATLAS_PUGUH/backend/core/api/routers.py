"""
API Routers

HTTP endpoints for Core Service use cases.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status

from ..use_cases import (
    CreateDecisionUseCase,
    CreateDecisionInput,
    ApproveWorkflowUseCase,
    ApproveWorkflowInput,
    RejectWorkflowUseCase,
    RejectWorkflowInput,
    DelegateWorkflowUseCase,
    DelegateWorkflowInput,
    EscalateWorkflowUseCase,
    EscalateWorkflowInput
)
from .schemas import (
    CreateDecisionRequest,
    CreateDecisionResponse,
    ApproveWorkflowRequest,
    ApproveWorkflowResponse,
    RejectWorkflowRequest,
    RejectWorkflowResponse,
    DelegateWorkflowRequest,
    DelegateWorkflowResponse,
    EscalateWorkflowRequest,
    EscalateWorkflowResponse
)
from .dependencies import (
    get_create_decision_use_case,
    get_approve_workflow_use_case,
    get_reject_workflow_use_case,
    get_delegate_workflow_use_case,
    get_escalate_workflow_use_case
)


router = APIRouter(prefix="/api/v1", tags=["decisions"])


@router.post(
    "/decisions",
    response_model=CreateDecisionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_decision(
    request: CreateDecisionRequest,
    use_case: CreateDecisionUseCase = Depends(get_create_decision_use_case)
):
    """
    Create decision with rule evaluation
    Source: INFRA-LAY3-002 §2.3
    """
    input_dto = CreateDecisionInput(
        tenant_id=request.tenant_id,
        decision_type=request.decision_type,
        context=request.context,
        idempotency_key=request.idempotency_key,
        trace_id=request.trace_id,
        requester_user_id=request.requester_user_id
    )

    output = await use_case.execute(input_dto)

    return CreateDecisionResponse(
        decision_id=output.decision_id,
        outcome=output.outcome,
        rule_matched_id=output.rule_matched_id,
        rule_version=output.rule_version,
        workflow_id=output.workflow_id,
        created_at=output.created_at
    )


@router.post(
    "/workflows/{workflow_id}/approve",
    response_model=ApproveWorkflowResponse,
    status_code=status.HTTP_200_OK
)
async def approve_workflow(
    workflow_id: UUID,
    request: ApproveWorkflowRequest,
    use_case: ApproveWorkflowUseCase = Depends(get_approve_workflow_use_case)
):
    """
    Approve workflow
    Source: INFRA-LAY3-002 §3.2
    """
    input_dto = ApproveWorkflowInput(
        workflow_id=workflow_id,
        tenant_id=request.tenant_id,
        approver_role=request.approver_role,
        acted_by_user_id=request.acted_by_user_id,
        comment=request.comment
    )

    output = await use_case.execute(input_dto)

    return ApproveWorkflowResponse(
        workflow_id=output.workflow_id,
        current_state=output.current_state,
        completed_at=output.completed_at
    )


@router.post(
    "/workflows/{workflow_id}/reject",
    response_model=RejectWorkflowResponse,
    status_code=status.HTTP_200_OK
)
async def reject_workflow(
    workflow_id: UUID,
    request: RejectWorkflowRequest,
    use_case: RejectWorkflowUseCase = Depends(get_reject_workflow_use_case)
):
    """
    Reject workflow
    Source: INFRA-LAY3-002 §3.2
    """
    input_dto = RejectWorkflowInput(
        workflow_id=workflow_id,
        tenant_id=request.tenant_id,
        approver_role=request.approver_role,
        acted_by_user_id=request.acted_by_user_id,
        reason=request.reason
    )

    output = await use_case.execute(input_dto)

    return RejectWorkflowResponse(
        workflow_id=output.workflow_id,
        current_state=output.current_state,
        completed_at=output.completed_at
    )


@router.post(
    "/workflows/{workflow_id}/delegate",
    response_model=DelegateWorkflowResponse,
    status_code=status.HTTP_200_OK
)
async def delegate_workflow(
    workflow_id: UUID,
    request: DelegateWorkflowRequest,
    use_case: DelegateWorkflowUseCase = Depends(get_delegate_workflow_use_case)
):
    """
    Delegate workflow
    Source: INFRA-LAY3-002 §3.3
    """
    input_dto = DelegateWorkflowInput(
        workflow_id=workflow_id,
        tenant_id=request.tenant_id,
        approver_role=request.approver_role,
        delegated_to_user_id=request.delegated_to_user_id,
        acted_by_user_id=request.acted_by_user_id,
        reason=request.reason
    )

    output = await use_case.execute(input_dto)

    return DelegateWorkflowResponse(
        workflow_id=output.workflow_id,
        current_state=output.current_state,
        delegated_to_user_id=output.delegated_to_user_id
    )


@router.post(
    "/workflows/{workflow_id}/escalate",
    response_model=EscalateWorkflowResponse,
    status_code=status.HTTP_200_OK
)
async def escalate_workflow(
    workflow_id: UUID,
    request: EscalateWorkflowRequest,
    use_case: EscalateWorkflowUseCase = Depends(get_escalate_workflow_use_case)
):
    """
    Escalate workflow
    Source: INFRA-LAY3-002 §3.3
    """
    input_dto = EscalateWorkflowInput(
        workflow_id=workflow_id,
        tenant_id=request.tenant_id,
        escalated_to_role=request.escalated_to_role,
        escalation_reason=request.escalation_reason
    )

    output = await use_case.execute(input_dto)

    return EscalateWorkflowResponse(
        workflow_id=output.workflow_id,
        current_state=output.current_state,
        escalated_to_role=output.escalated_to_role
    )
