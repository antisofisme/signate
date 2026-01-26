"""
Read-Only Endpoints for Phase A+ Visibility
IMPORTANT: These are minimal endpoints for UI visibility only
No business logic, just simple database queries
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from ..repositories.models import (
    DecisionModel,
    WorkflowModel,
    RuleModel
)
# Note: workflow_transitions and event_log tables exist but models not yet created
# Phase A+ workaround: Query directly or skip these features
from .dependencies import get_session

router = APIRouter(prefix="/api", tags=["read-only"])


@router.get("/decisions")
async def list_decisions(
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """
    List all decisions (Phase A+ - no pagination)
    Returns: Recent decisions with basic info
    """
    result = await session.execute(
        select(DecisionModel)
        .order_by(desc(DecisionModel.created_at))
        .limit(limit)
    )
    decisions = result.scalars().all()

    return {
        "decisions": [
            {
                "decision_id": str(d.decision_id),
                "tenant_id": str(d.tenant_id),
                "decision_type": d.decision_type,
                "outcome": d.outcome,
                "outcome_label": _get_outcome_label(d.outcome),
                "rule_matched_id": str(d.rule_matched_id) if d.rule_matched_id else None,
                "approval_workflow_id": str(d.approval_workflow_id) if d.approval_workflow_id else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "context": d.context,
                "latency_ms": d.latency_ms
            }
            for d in decisions
        ],
        "total": len(decisions)
    }


@router.get("/decisions/{decision_id}")
async def get_decision_detail(
    decision_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get decision detail with workflow info
    Returns: Complete decision story
    """
    # Get decision
    result = await session.execute(
        select(DecisionModel).where(DecisionModel.decision_id == decision_id)
    )
    decision = result.scalar_one_or_none()

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Get workflow if exists
    workflow = None
    workflow_actions = []  # Phase A+: Model not created yet, return empty

    if decision.approval_workflow_id:
        workflow_result = await session.execute(
            select(WorkflowModel).where(
                WorkflowModel.workflow_id == decision.approval_workflow_id
            )
        )
        workflow = workflow_result.scalar_one_or_none()

        # TODO Phase B: Add WorkflowTransitionModel to get workflow actions
        # For now, workflow_actions will be empty

    return {
        "decision": {
            "decision_id": str(decision.decision_id),
            "tenant_id": str(decision.tenant_id),
            "decision_type": decision.decision_type,
            "context": decision.context,
            "outcome": decision.outcome,
            "outcome_label": _get_outcome_label(decision.outcome),
            "outcome_description": _get_outcome_description(decision.outcome, decision.context),
            "rule_matched_id": str(decision.rule_matched_id) if decision.rule_matched_id else None,
            "rule_version": decision.rule_version,
            "approval_workflow_id": str(decision.approval_workflow_id) if decision.approval_workflow_id else None,
            "latency_ms": decision.latency_ms,
            "created_at": decision.created_at.isoformat() if decision.created_at else None,
            "metadata_json": decision.metadata_json
        },
        "workflow": {
            "workflow_id": str(workflow.workflow_id),
            "current_state": workflow.current_state,
            "current_state_label": _get_workflow_state_label(workflow.current_state),
            "approver_role": workflow.approver_role,
            "delegated_to_user_id": str(workflow.delegated_to_user_id) if workflow.delegated_to_user_id else None,
            "escalated_to_user_id": str(workflow.escalated_to_user_id) if workflow.escalated_to_user_id else None,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
        } if workflow else None,
        "workflow_actions": [
            {
                "action_id": str(a.action_id),
                "action_type": a.action_type,
                "action_type_label": _get_action_type_label(a.action_type),
                "old_state": a.old_state,
                "new_state": a.new_state,
                "acted_by_role": a.acted_by_role,
                "acted_by_user_id": str(a.acted_by_user_id) if a.acted_by_user_id else None,
                "action_at": a.action_at.isoformat() if a.action_at else None,
                "comment": a.comment,
                "metadata_json": a.metadata_json
            }
            for a in workflow_actions
        ] if workflow_actions else []
    }


@router.get("/workflows")
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status: PENDING_APPROVAL, APPROVED, REJECTED"),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """
    List workflows for approval inbox
    Returns: Workflows with decision info
    """
    query = select(WorkflowModel, DecisionModel).join(
        DecisionModel,
        WorkflowModel.decision_id == DecisionModel.decision_id
    ).order_by(desc(WorkflowModel.created_at))

    if status:
        query = query.where(WorkflowModel.current_state == status)

    query = query.limit(limit)

    result = await session.execute(query)
    rows = result.all()

    return {
        "workflows": [
            {
                "workflow_id": str(workflow.workflow_id),
                "decision_id": str(workflow.decision_id),
                "tenant_id": str(workflow.tenant_id),
                "current_state": workflow.current_state,
                "current_state_label": _get_workflow_state_label(workflow.current_state),
                "approver_role": workflow.approver_role,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                "decision": {
                    "decision_type": decision.decision_type,
                    "context": decision.context,
                    "outcome": decision.outcome
                }
            }
            for workflow, decision in rows
        ],
        "total": len(rows)
    }


@router.get("/rules")
async def list_rules(
    decision_type: Optional[str] = Query(None, description="Filter by decision_type"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, DRAFT, DEPRECATED"),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """
    List rules (configuration visibility)
    Returns: Rules configured in system
    """
    query = select(RuleModel).order_by(
        RuleModel.decision_type,
        RuleModel.evaluation_sequence
    )

    if decision_type:
        query = query.where(RuleModel.decision_type == decision_type)

    if status:
        query = query.where(RuleModel.status == status)

    query = query.limit(limit)

    result = await session.execute(query)
    rules = result.scalars().all()

    return {
        "rules": [
            {
                "rule_id": str(r.rule_id),
                "tenant_id": str(r.tenant_id),
                "decision_type": r.decision_type,
                "rule_name": r.rule_name,
                "description": r.description,
                "conditions": r.conditions,
                "action": r.action,
                "version": r.version,
                "status": r.status,
                "evaluation_sequence": r.evaluation_sequence,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "activated_at": r.activated_at.isoformat() if r.activated_at else None,
                "deactivated_at": r.deactivated_at.isoformat() if r.deactivated_at else None
            }
            for r in rules
        ],
        "total": len(rules)
    }


@router.get("/audit")
async def list_audit_events(
    decision_id: Optional[UUID] = Query(None, description="Filter by decision_id"),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """
    List audit events (read-only timeline)
    Returns: Audit trail events

    Phase A+: EventLog model not created yet, returns empty array
    TODO Phase B: Create EventLogModel and implement actual querying
    """
    # Phase A+ workaround: Return empty events
    # Real implementation will query event_log table when model is created
    return {
        "events": [],
        "total": 0,
        "note": "Phase A+: Audit log model not yet implemented"
    }


# Helper functions for labels (Phase A+ visibility)
def _get_outcome_label(outcome: str) -> str:
    """Human-readable outcome label"""
    labels = {
        "ALLOWED": "Allowed",
        "DENIED": "Denied",
        "REQUIRE_APPROVAL": "Requires Approval"
    }
    return labels.get(outcome, outcome)


def _get_outcome_description(outcome: str, context: dict) -> str:
    """Contextual description of outcome"""
    amount = context.get("amount", 0) if context else 0

    descriptions = {
        "ALLOWED": f"Decision approved automatically (amount: ${amount})",
        "DENIED": f"Decision denied by rule (amount: ${amount})",
        "REQUIRE_APPROVAL": f"Amount ${amount} exceeds threshold, requires approval"
    }
    return descriptions.get(outcome, "No description available")


def _get_workflow_state_label(state: str) -> str:
    """Human-readable workflow state label"""
    labels = {
        "PENDING_APPROVAL": "Pending Approval",
        "APPROVED": "Approved",
        "REJECTED": "Rejected",
        "DELEGATED": "Delegated",
        "ESCALATED": "Escalated"
    }
    return labels.get(state, state)


def _get_action_type_label(action_type: str) -> str:
    """Human-readable action type label"""
    labels = {
        "APPROVE": "Approved",
        "REJECT": "Rejected",
        "DELEGATE": "Delegated",
        "ESCALATE": "Escalated"
    }
    return labels.get(action_type, action_type)
