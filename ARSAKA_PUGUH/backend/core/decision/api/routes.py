"""
Decision API Routes

FastAPI router for rules and decisions endpoints.

Source: PUGUH UI_API_MAPPING.md - Decision Domain
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status

from .schemas import (
    CreateRuleRequest,
    UpdateRuleRequest,
    ActivateRuleRequest,
    DeactivateRuleRequest,
    ListRulesResponse,
    ListDecisionsResponse,
    SuccessResponse,
    CreateResponse,
)
from .dependencies import (
    get_current_user_id,
    get_current_tenant_id,
    get_list_rules_use_case,
    get_get_rule_use_case,
    get_create_rule_use_case,
    get_update_rule_use_case,
    get_delete_rule_use_case,
    get_activate_rule_use_case,
    get_deactivate_rule_use_case,
    get_list_decisions_use_case,
    get_get_decision_use_case,
)
from ..use_cases import (
    ListRulesUseCase,
    GetRuleUseCase,
    CreateRuleUseCase,
    UpdateRuleUseCase,
    DeleteRuleUseCase,
    ActivateRuleUseCase,
    DeactivateRuleUseCase,
    ListDecisionsUseCase,
    GetDecisionUseCase,
)


router = APIRouter(prefix="/decision", tags=["decision"])


# =============================================================================
# Rule Endpoints
# =============================================================================

@router.get("/rules", response_model=ListRulesResponse)
async def list_rules(
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, ACTIVE, DEPRECATED)"),
    decision_type: Optional[str] = Query(None, description="Filter by decision type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListRulesUseCase = Depends(get_list_rules_use_case),
):
    """
    List rules in tenant.

    Returns paginated list of rules.
    Optionally filter by status or decision type.
    """
    result = await use_case.execute(
        tenant_id=tenant_id,
        status=status,
        decision_type=decision_type,
        page=page,
        limit=limit,
    )
    return {"success": True, "data": result}


@router.post("/rules", response_model=CreateResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: CreateRuleRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: CreateRuleUseCase = Depends(get_create_rule_use_case),
):
    """
    Create a new rule draft.

    Creates rule in DRAFT status. Requires idempotency_key.
    """
    result = await use_case.execute(
        tenant_id=tenant_id,
        rule_name=request.rule_name,
        decision_type=request.decision_type,
        conditions=request.conditions,
        action=request.action,
        created_by=user_id,
        description=request.description,
        idempotency_key=request.idempotency_key,
    )
    return {
        "success": True,
        "data": result,
        "message": "Rule draft created successfully",
    }


@router.get("/rules/{rule_id}", response_model=SuccessResponse)
async def get_rule(
    rule_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetRuleUseCase = Depends(get_get_rule_use_case),
):
    """
    Get rule detail.

    Returns rule with conditions and action.
    """
    result = await use_case.execute(tenant_id=tenant_id, rule_id=rule_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"Rule {rule_id} not found"}
        )
    return {"success": True, "data": result}


@router.put("/rules/{rule_id}", response_model=SuccessResponse)
async def update_rule(
    rule_id: UUID,
    request: UpdateRuleRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: UpdateRuleUseCase = Depends(get_update_rule_use_case),
):
    """
    Update a rule draft.

    Only rules in DRAFT status can be updated.
    At least one field must be provided for update.
    """
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            rule_id=rule_id,
            updated_by=user_id,
            rule_name=request.rule_name,
            description=request.description,
            conditions=request.conditions,
            action=request.action,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATE", "message": str(e)}
        )


@router.delete("/rules/{rule_id}", response_model=SuccessResponse)
async def delete_rule(
    rule_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: DeleteRuleUseCase = Depends(get_delete_rule_use_case),
):
    """
    Delete a rule (soft delete).

    Only rules in DRAFT or DEPRECATED status can be deleted.
    ACTIVE rules must first be deprecated before deletion.
    """
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            rule_id=rule_id,
            deleted_by=user_id,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATE", "message": str(e)}
        )


@router.get("/rules/{rule_id}/versions", response_model=SuccessResponse)
async def get_rule_versions(
    rule_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetRuleUseCase = Depends(get_get_rule_use_case),
):
    """
    Get rule version history.

    Returns list of versions and related events.
    """
    versions = await use_case.get_versions(tenant_id=tenant_id, rule_id=rule_id)
    return {"success": True, "data": {"versions": versions}}


@router.post("/rules/{rule_id}/activate", response_model=SuccessResponse)
async def activate_rule(
    rule_id: UUID,
    request: ActivateRuleRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: ActivateRuleUseCase = Depends(get_activate_rule_use_case),
):
    """
    Request rule activation.

    In production, this creates an approval workflow.
    For Phase A, directly activates the rule.
    """
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            rule_id=rule_id,
            activated_by=user_id,
            idempotency_key=request.idempotency_key,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATE", "message": str(e)}
        )


@router.post("/rules/{rule_id}/deactivate", response_model=SuccessResponse)
async def deactivate_rule(
    rule_id: UUID,
    request: DeactivateRuleRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: DeactivateRuleUseCase = Depends(get_deactivate_rule_use_case),
):
    """
    Deactivate an active rule.

    Transitions rule from ACTIVE to DEPRECATED status.
    DEPRECATED rules can then be deleted if needed.
    """
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            rule_id=rule_id,
            deactivated_by=user_id,
            reason=request.reason,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATE", "message": str(e)}
        )


# =============================================================================
# Decision Endpoints
# =============================================================================

@router.get("/history", response_model=ListDecisionsResponse)
async def list_decisions(
    type: Optional[str] = Query(None, alias="type", description="Filter by decision type"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (ALLOWED, DENIED, REQUIRE_APPROVAL)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListDecisionsUseCase = Depends(get_list_decisions_use_case),
):
    """
    List decisions (history).

    Returns paginated list of decision records.
    Optionally filter by type or outcome.
    """
    result = await use_case.execute(
        tenant_id=tenant_id,
        decision_type=type,
        outcome=outcome,
        page=page,
        limit=limit,
    )
    return {"success": True, "data": result}


@router.get("/types", response_model=SuccessResponse)
async def list_decision_types(
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListRulesUseCase = Depends(get_list_rules_use_case),
):
    """
    List decision types.

    Returns distinct decision types available.
    """
    types = await use_case.get_decision_types(tenant_id=tenant_id)
    return {"success": True, "data": types}


@router.get("/history/{decision_id}", response_model=SuccessResponse)
async def get_decision(
    decision_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetDecisionUseCase = Depends(get_get_decision_use_case),
):
    """
    Get decision detail.

    Returns decision with context and metadata.
    """
    result = await use_case.execute(tenant_id=tenant_id, decision_id=decision_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"Decision {decision_id} not found"}
        )
    return {"success": True, "data": result}


@router.get("/history/{decision_id}/events", response_model=SuccessResponse)
async def get_decision_events(
    decision_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetDecisionUseCase = Depends(get_get_decision_use_case),
):
    """
    Get decision events.

    Returns event timeline for the decision.
    """
    events = await use_case.get_events(tenant_id=tenant_id, decision_id=decision_id)
    return {"success": True, "data": {"events": events}}
