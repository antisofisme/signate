"""
3-Gate Validation API Routes

Endpoints for the MANTRA 3-gate validation pipeline:
- Gate 1: Deterministic validation
- Gate 2: AI heuristic validation
- Gate 3: Human approval workflow

Per MANTRA LAW §6: AI has ZERO authority for approval.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..validation import (
    # Gate 1
    Gate1Validator,
    Gate1Result,
    validate_gate1,
    # Gate 2
    Gate2AIValidator,
    Gate2AIResult,
    create_gate2_validator,
    # Gate 3
    HumanApprovalManager,
    ApprovalStatus,
    ReviewerRole,
    RejectionReason,
    ApprovalRequest,
    # Pipeline
    ValidationPipeline,
    PipelineResult,
    PipelineOutcome,
    validate_decision_full,
)
from factory.container import Container

logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/validation", tags=["validation"])


def get_pipeline() -> ValidationPipeline:
    """Get validation pipeline from Container (singleton)."""
    return Container.get_validation_pipeline()


def get_approval_manager() -> HumanApprovalManager:
    """Get approval manager from Container (singleton)."""
    return Container.get_approval_manager()


# ============================================================================
# Request/Response Models
# ============================================================================

class ValidationRequest(BaseModel):
    """Request to validate a decision."""
    decision: Dict[str, Any] = Field(..., description="Decision record to validate")
    submitted_by: str = Field(..., description="Human submitter email/ID")
    auto_create_approval: bool = Field(True, description="Auto-create approval request")


class Gate1Response(BaseModel):
    """Gate 1 validation response."""
    status: str
    rules_checked: int
    rules_passed: int
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    can_proceed_to_gate2: bool
    validation_time_ms: float


class Gate2Response(BaseModel):
    """Gate 2 validation response."""
    passed: bool
    quality_score: float
    quality_issues: List[str]
    conflicts: List[Dict[str, Any]]
    duplicates: List[str]


class PipelineResponse(BaseModel):
    """Full pipeline response."""
    outcome: str
    stage: str
    decision_id: str
    decision_code: str
    gate1: Optional[Dict[str, Any]]
    gate2: Optional[Dict[str, Any]]
    gate3: Optional[Dict[str, Any]]
    approval_request_id: Optional[str]
    messages: List[str]
    can_activate: bool


class ApprovalRequestResponse(BaseModel):
    """Approval request response."""
    request_id: str
    decision_id: str
    decision_code: str
    status: str
    submitted_by: str
    submitted_at: str
    assigned_to: Optional[str]
    gate1_passed: bool
    gate2_passed: bool
    comments_count: int


class ApproveRequest(BaseModel):
    """Request to approve a decision."""
    request_id: str = Field(..., description="Approval request ID")
    approver_id: str = Field(..., description="Human approver ID (MUST be human)")
    approver_role: str = Field("PEER", description="Approver role")
    comment: Optional[str] = Field(None, description="Approval comment")


class RejectRequest(BaseModel):
    """Request to reject a decision."""
    request_id: str = Field(..., description="Approval request ID")
    rejector_id: str = Field(..., description="Human rejector ID")
    rejector_role: str = Field("PEER", description="Rejector role")
    reason: str = Field(..., description="Rejection reason")
    comment: str = Field(..., description="Detailed explanation")


class AddCommentRequest(BaseModel):
    """Request to add a review comment."""
    request_id: str = Field(..., description="Approval request ID")
    reviewer_id: str = Field(..., description="Reviewer ID")
    reviewer_role: str = Field("PEER", description="Reviewer role")
    comment: str = Field(..., description="Comment text")
    field_reference: Optional[str] = Field(None, description="Related field")
    is_blocking: bool = Field(False, description="Is this a blocking comment?")


# ============================================================================
# Gate 1 Endpoints (Deterministic)
# ============================================================================

@router.post("/gate1", response_model=Gate1Response)
async def validate_gate1_endpoint(decision: Dict[str, Any]):
    """
    Run Gate 1 (deterministic) validation only.

    Gate 1 performs pure rule-based validation:
    - Schema validation (S-001 to S-022)
    - Consistency checks (D-001 to D-014)

    No AI involvement. Same input = same output.
    """
    result = validate_gate1(decision)

    return Gate1Response(
        status=result.status.value,
        rules_checked=result.rules_checked,
        rules_passed=result.rules_passed,
        violations=[v.to_dict() for v in result.violations],
        warnings=[w.to_dict() for w in result.warnings],
        can_proceed_to_gate2=result.can_proceed_to_gate2,
        validation_time_ms=result.validation_time_ms,
    )


# ============================================================================
# Gate 2 Endpoints (AI Heuristic)
# ============================================================================

@router.post("/gate2", response_model=Gate2Response)
async def validate_gate2_endpoint(decision: Dict[str, Any]):
    """
    Run Gate 2 (AI heuristic) validation only.

    Gate 2 performs AI-assisted checks:
    - Quality scoring
    - Conflict detection
    - Duplicate detection

    This is ADVISORY only - does not block.
    """
    validator = create_gate2_validator()
    result = validator.validate(decision)

    return Gate2Response(
        passed=result.passed,
        quality_score=result.quality_score.overall,
        quality_issues=result.quality_score.issues,
        conflicts=[c.to_dict() if hasattr(c, 'to_dict') else c for c in result.conflicts],
        duplicates=result.duplicates,
    )


# ============================================================================
# Full Pipeline Endpoints
# ============================================================================

@router.post("/pipeline", response_model=PipelineResponse)
async def validate_full_pipeline(request: ValidationRequest):
    """
    Run the full 3-gate validation pipeline.

    1. Gate 1: Deterministic validation (HARD block)
    2. Gate 2: AI heuristic validation (SOFT warn)
    3. Creates approval request for Gate 3 (human approval)

    Returns:
        Pipeline result with status and approval request ID
    """
    # Validate submitter is human
    if request.submitted_by.lower().startswith("ai:"):
        raise HTTPException(
            status_code=403,
            detail="AI cannot submit decisions per MANTRA LAW §6"
        )

    pipeline = get_pipeline()

    try:
        result = pipeline.validate(
            record=request.decision,
            submitted_by=request.submitted_by,
            auto_create_approval=request.auto_create_approval,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Pipeline validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return PipelineResponse(
        outcome=result.outcome.value,
        stage=result.stage.value,
        decision_id=result.decision_id,
        decision_code=result.decision_code,
        gate1=result.gate1.to_dict() if result.gate1 else None,
        gate2=result.gate2.to_dict() if result.gate2 else None,
        gate3=result.gate3.to_dict() if result.gate3 else None,
        approval_request_id=result.approval_request_id,
        messages=result.messages,
        can_activate=result.can_activate,
    )


@router.get("/pipeline/{decision_id}/status", response_model=PipelineResponse)
async def get_pipeline_status(decision_id: str):
    """
    Get current pipeline status for a decision.
    """
    pipeline = get_pipeline()
    result = pipeline.check_approval_status(decision_id)

    return PipelineResponse(
        outcome=result.outcome.value,
        stage=result.stage.value,
        decision_id=result.decision_id,
        decision_code=result.decision_code,
        gate1=result.gate1.to_dict() if result.gate1 else None,
        gate2=result.gate2.to_dict() if result.gate2 else None,
        gate3=result.gate3.to_dict() if result.gate3 else None,
        approval_request_id=result.approval_request_id,
        messages=result.messages,
        can_activate=result.can_activate,
    )


# ============================================================================
# Gate 3 Endpoints (Human Approval)
# ============================================================================

@router.get("/approvals/pending", response_model=List[ApprovalRequestResponse])
async def list_pending_approvals(
    reviewer_id: Optional[str] = Query(None, description="Filter by assigned reviewer"),
):
    """
    List all pending approval requests.

    Returns requests awaiting human review.
    """
    pipeline = get_pipeline()
    pending = pipeline.get_pending_approvals()

    # Filter by reviewer if specified
    if reviewer_id:
        pending = [p for p in pending if p.get("submitted_by") != reviewer_id]  # Can't self-approve

    return [
        ApprovalRequestResponse(
            request_id=p.get("approval_request_id", ""),
            decision_id=p.get("decision_id", ""),
            decision_code=p.get("decision_code", ""),
            status="PENDING_REVIEW",
            submitted_by=p.get("submitted_by", ""),
            submitted_at=p.get("submitted_at", ""),
            assigned_to=None,
            gate1_passed=True,
            gate2_passed=p.get("gate2_quality_score", 0) >= 0.6,
            comments_count=0,
        )
        for p in pending
    ]


@router.post("/approvals/approve")
async def approve_decision(request: ApproveRequest):
    """
    Approve a decision (Gate 3).

    CRITICAL: Only humans can call this endpoint.
    AI has ZERO authority per MANTRA LAW §6.
    """
    # Validate approver is human
    if request.approver_id.lower().startswith("ai:"):
        raise HTTPException(
            status_code=403,
            detail="AI CANNOT approve decisions per MANTRA LAW §6. AI has ZERO authority."
        )

    # Validate role
    try:
        role = ReviewerRole(request.approver_role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {request.approver_role}"
        )

    approval_manager = get_approval_manager()

    try:
        result = approval_manager.approve(
            request_id=request.request_id,
            approver_id=request.approver_id,
            approver_role=role,
            comment=request.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": result.success,
        "status": result.status.value,
        "message": result.message,
        "approved_by": result.approved_by,
        "approved_at": result.approved_at.isoformat() if result.approved_at else None,
    }


@router.post("/approvals/reject")
async def reject_decision(request: RejectRequest):
    """
    Reject a decision (Gate 3).

    Requires a reason and detailed explanation.
    """
    # Validate rejector is human
    if request.rejector_id.lower().startswith("ai:"):
        raise HTTPException(
            status_code=403,
            detail="AI cannot reject decisions per MANTRA LAW §6"
        )

    # Validate role
    try:
        role = ReviewerRole(request.rejector_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.rejector_role}")

    # Validate reason
    try:
        reason = RejectionReason(request.reason)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reason: {request.reason}. Valid: {[r.value for r in RejectionReason]}"
        )

    approval_manager = get_approval_manager()

    try:
        result = approval_manager.reject(
            request_id=request.request_id,
            rejector_id=request.rejector_id,
            rejector_role=role,
            reason=reason,
            comment=request.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": result.success,
        "status": result.status.value,
        "message": result.message,
    }


@router.post("/approvals/comment")
async def add_review_comment(request: AddCommentRequest):
    """
    Add a review comment to an approval request.
    """
    # Validate reviewer is human
    if request.reviewer_id.lower().startswith("ai:"):
        raise HTTPException(
            status_code=403,
            detail="AI cannot add review comments per MANTRA LAW §6"
        )

    # Validate role
    try:
        role = ReviewerRole(request.reviewer_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.reviewer_role}")

    approval_manager = get_approval_manager()

    try:
        comment = approval_manager.add_comment(
            request_id=request.request_id,
            reviewer_id=request.reviewer_id,
            reviewer_role=role,
            comment=request.comment,
            field_reference=request.field_reference,
            is_blocking=request.is_blocking,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "comment_id": comment.comment_id,
        "is_blocking": comment.is_blocking,
    }


@router.get("/summary")
async def get_validation_summary():
    """
    Get validation pipeline summary statistics.
    """
    pipeline = get_pipeline()
    return pipeline.get_summary()


# ============================================================================
# Exports
# ============================================================================

__all__ = ["router"]
