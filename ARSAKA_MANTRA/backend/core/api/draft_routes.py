"""
Draft Review API Routes

Endpoints for per-field decision review workflow:
1. POST /drafts - AI creates draft
2. GET /drafts - List user's pending drafts
3. GET /drafts/{id} - Get draft for review
4. POST /drafts/{id}/review/{field} - Review single field (OK/NO)
5. POST /drafts/{id}/finalize - Finalize after all reviewed
6. DELETE /drafts/{id} - Cancel draft

MANTRA Compliance:
- AI creates drafts, but CANNOT approve
- Each field needs human OK/NO
- Finalize requires human approved_by
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# These will be injected
from adapters.repositories.draft_repository import InMemoryDraftRepository
from core.domain.review_schema import AIDecisionDrafter, format_for_ui


router = APIRouter(prefix="/drafts", tags=["drafts"])

# In-memory repository (replace with real DB in production)
_repository = InMemoryDraftRepository()


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateDraftRequest(BaseModel):
    """Request to create a new draft."""
    request: str = Field(..., description="User's request for decision", min_length=5)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context (files, trigger, etc)")

    class Config:
        json_schema_extra = {
            "example": {
                "request": "implement rate limiting for API endpoints",
                "context": {
                    "files": ["src/api/routes.py"],
                    "trigger": "Security audit recommendation"
                }
            }
        }


class ReviewFieldRequest(BaseModel):
    """Request to review a single field."""
    approved: bool = Field(..., description="True = OK, False = NO")
    new_value: Optional[Any] = Field(default=None, description="New value if editing")
    rejection_reason: Optional[str] = Field(default=None, description="Reason for rejection")

    class Config:
        json_schema_extra = {
            "example": {
                "approved": False,
                "new_value": "Rate limiting is critical for API security",
                "rejection_reason": "Original was too generic"
            }
        }


class FinalizeRequest(BaseModel):
    """Request to finalize draft."""
    approved_by: str = Field(..., description="Human user ID who approves")

    class Config:
        json_schema_extra = {
            "example": {
                "approved_by": "human:john@example.com"
            }
        }


class DraftSummary(BaseModel):
    """Summary of a draft for list view."""
    draft_id: str
    original_request: str
    created_at: datetime
    created_by_ai: str
    review_progress: Dict[str, Any]
    needs_review: bool
    finalized: bool


class FieldForReview(BaseModel):
    """Field data for review UI."""
    name: str
    label: str
    value: Any
    display_value: str
    source: str
    source_label: str
    source_explanation: Optional[str]
    status: str
    status_label: str
    is_reviewed: bool
    can_edit: bool
    edited_value: Optional[Any]
    final_value: Any


class DraftDetailResponse(BaseModel):
    """Full draft detail for review."""
    draft_id: str
    created_at: datetime
    created_by_ai: str
    original_request: str
    review_progress: Dict[str, Any]
    needs_review: bool
    can_finalize: bool
    fields: List[FieldForReview]
    pending_fields: List[str]
    rejected_fields: List[str]


class APIResponse(BaseModel):
    """Standard API response."""
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, str]] = None


# ============================================================================
# Helper: Get current user (simplified - replace with real auth)
# ============================================================================

def get_current_user() -> str:
    """Get current authenticated user. Replace with real auth."""
    return "human:current_user@example.com"


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=APIResponse)
async def create_draft(
    request: CreateDraftRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Create a new decision draft.

    AI fills all fields based on the request.
    Draft is saved with needs_review=true.
    User will review each field in UI.
    """
    try:
        # AI creates draft
        drafter = AIDecisionDrafter(
            user_id=user_id,
            ai_model="claude-opus-4-5"
        )

        draft = drafter.create_draft(
            request=request.request,
            context=request.context or {}
        )

        # Save draft
        await _repository.save_draft(draft)

        # Return draft info
        return APIResponse(
            success=True,
            data={
                "draft_id": draft.draft_id,
                "message": "Draft created. Please review each field.",
                "fields_count": len(draft.fields),
                "review_url": f"/drafts/{draft.draft_id}",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse)
async def list_drafts(
    include_finalized: bool = Query(False, description="Include finalized drafts"),
    user_id: str = Depends(get_current_user),
):
    """
    List user's drafts.

    By default only shows drafts needing review.
    """
    try:
        drafts = await _repository.get_user_drafts(user_id, include_finalized)

        summaries = [
            DraftSummary(
                draft_id=d.draft_id,
                original_request=d.original_request,
                created_at=d.created_at,
                created_by_ai=d.created_by_ai,
                review_progress=d.review_progress,
                needs_review=d.needs_review,
                finalized=d.finalized,
            ).model_dump()
            for d in drafts
        ]

        return APIResponse(
            success=True,
            data={
                "drafts": summaries,
                "total": len(summaries),
                "pending_count": sum(1 for d in drafts if d.needs_review),
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=APIResponse)
async def list_pending_drafts(
    user_id: str = Depends(get_current_user),
):
    """Get drafts that need review (shortcut)."""
    try:
        drafts = await _repository.get_pending_drafts(user_id)

        return APIResponse(
            success=True,
            data={
                "drafts": [
                    {
                        "draft_id": d.draft_id,
                        "original_request": d.original_request[:100],
                        "fields_pending": len(d.pending_fields),
                        "fields_total": len(d.fields),
                        "created_at": d.created_at.isoformat(),
                    }
                    for d in drafts
                ],
                "total": len(drafts),
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Field Specs Endpoints (MUST be before /{draft_id} routes)
# ============================================================================

@router.get("/field-specs", response_model=APIResponse)
async def get_field_specs():
    """
    Get field specifications for UI.

    Returns guidelines, validation rules, examples for each field.
    Use this to display help text in the review form.
    """
    try:
        import os
        import importlib.util

        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        spec = importlib.util.spec_from_file_location(
            "field_specs",
            os.path.join(backend_dir, "core", "domain", "field_specs.py")
        )
        field_specs_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(field_specs_module)

        all_specs = field_specs_module.get_all_specs()

        return APIResponse(
            success=True,
            data={
                "field_specs": all_specs,
                "total_fields": len(all_specs),
            }
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "SPEC_LOAD_ERROR", "message": str(e)}
        )


@router.get("/field-specs/{field_name}", response_model=APIResponse)
async def get_field_spec(field_name: str):
    """
    Get specification for a single field.

    Includes:
    - Description and purpose
    - Guidelines and writing tips
    - Good and bad examples
    - Validation rules
    """
    try:
        import os
        import importlib.util

        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        spec = importlib.util.spec_from_file_location(
            "field_specs",
            os.path.join(backend_dir, "core", "domain", "field_specs.py")
        )
        field_specs_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(field_specs_module)

        field_spec = field_specs_module.get_field_spec(field_name)

        if not field_spec:
            return APIResponse(
                success=False,
                error={"code": "FIELD_NOT_FOUND", "message": f"No spec for field: {field_name}"}
            )

        return APIResponse(
            success=True,
            data={
                "field_name": field_name,
                "spec": field_spec.to_dict(),
                "display_text": field_specs_module.format_spec_for_display(field_name),
            }
        )

    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "SPEC_LOAD_ERROR", "message": str(e)}
        )


@router.get("/{draft_id}", response_model=APIResponse)
async def get_draft(
    draft_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Get draft detail for review UI.

    Returns all fields with their review status.
    UI should show OK/NO buttons for each field.
    """
    try:
        draft = await _repository.get_draft(draft_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your draft")

        # Format for UI
        ui_data = format_for_ui(draft)

        return APIResponse(
            success=True,
            data=ui_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{draft_id}/review/{field_name}", response_model=APIResponse)
async def review_field(
    draft_id: str,
    field_name: str,
    request: ReviewFieldRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Review a single field (OK or NO).

    - approved=true → Field status becomes APPROVED
    - approved=false → Field status becomes REJECTED
    - If new_value provided → Field is EDITED (approved after edit)

    After all fields reviewed, draft can be finalized.
    """
    try:
        draft = await _repository.get_draft(draft_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your draft")

        if draft.finalized:
            raise HTTPException(status_code=400, detail="Draft already finalized")

        if field_name not in draft.fields:
            raise HTTPException(status_code=404, detail=f"Field '{field_name}' not found")

        # Update field review
        updated_draft = await _repository.update_field_review(
            draft_id=draft_id,
            field_name=field_name,
            approved=request.approved,
            new_value=request.new_value,
            rejection_reason=request.rejection_reason,
        )

        field = updated_draft.fields[field_name]

        return APIResponse(
            success=True,
            data={
                "field_name": field_name,
                "status": field.status.value,
                "is_reviewed": field.is_reviewed,
                "final_value": field.final_value,
                "review_progress": updated_draft.review_progress,
                "can_finalize": updated_draft.all_reviewed and not updated_draft.rejected_fields,
                "pending_fields": updated_draft.pending_fields,
                "rejected_fields": updated_draft.rejected_fields,
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{draft_id}/review-bulk", response_model=APIResponse)
async def review_fields_bulk(
    draft_id: str,
    reviews: Dict[str, ReviewFieldRequest] = Body(...),
    user_id: str = Depends(get_current_user),
):
    """
    Review multiple fields at once.

    Body format:
    {
        "title": {"approved": true},
        "statement": {"approved": true},
        "rationale": {"approved": false, "new_value": "New rationale..."}
    }
    """
    try:
        draft = await _repository.get_draft(draft_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your draft")

        results = {}
        for field_name, review in reviews.items():
            if field_name in draft.fields:
                await _repository.update_field_review(
                    draft_id=draft_id,
                    field_name=field_name,
                    approved=review.approved,
                    new_value=review.new_value,
                    rejection_reason=review.rejection_reason,
                )
                results[field_name] = "reviewed"

        # Get updated draft
        updated_draft = await _repository.get_draft(draft_id)

        return APIResponse(
            success=True,
            data={
                "reviewed_fields": results,
                "review_progress": updated_draft.review_progress,
                "can_finalize": updated_draft.all_reviewed and not updated_draft.rejected_fields,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{draft_id}/approve-all", response_model=APIResponse)
async def approve_all_fields(
    draft_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Quick action: Approve all pending fields.

    Use when AI suggestions are all acceptable.
    Still requires finalize step with human approval.
    """
    try:
        draft = await _repository.get_draft(draft_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your draft")

        # Approve all pending fields
        approved_count = 0
        for field_name in list(draft.pending_fields):
            await _repository.update_field_review(
                draft_id=draft_id,
                field_name=field_name,
                approved=True,
            )
            approved_count += 1

        updated_draft = await _repository.get_draft(draft_id)

        return APIResponse(
            success=True,
            data={
                "approved_count": approved_count,
                "review_progress": updated_draft.review_progress,
                "can_finalize": True,
                "message": "All fields approved. Ready to finalize.",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{draft_id}/finalize", response_model=APIResponse)
async def finalize_draft(
    draft_id: str,
    request: FinalizeRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Finalize draft and create decision.

    Requirements:
    - All fields must be reviewed (approved or edited)
    - No rejected fields without edit
    - approved_by MUST be human (MANTRA §6)

    Returns the final decision.
    """
    try:
        draft = await _repository.get_draft(draft_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your draft")

        if draft.finalized:
            raise HTTPException(status_code=400, detail="Draft already finalized")

        # Validate approved_by is human (MANTRA §6)
        if request.approved_by.startswith("ai:"):
            raise HTTPException(
                status_code=400,
                detail="MANTRA §6 VIOLATION: approved_by CANNOT be AI"
            )

        # Finalize
        decision = await _repository.finalize_draft(
            draft_id=draft_id,
            approved_by=request.approved_by,
        )

        return APIResponse(
            success=True,
            data={
                "decision": decision,
                "message": "Decision created successfully",
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{draft_id}", response_model=APIResponse)
async def delete_draft(
    draft_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Delete/cancel a draft.

    Cannot delete finalized drafts.
    """
    try:
        draft = await _repository.get_draft(draft_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your draft")

        if draft.finalized:
            raise HTTPException(status_code=400, detail="Cannot delete finalized draft")

        deleted = await _repository.delete_draft(draft_id)

        return APIResponse(
            success=True,
            data={
                "deleted": deleted,
                "draft_id": draft_id,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export router
# ============================================================================

__all__ = ["router"]
