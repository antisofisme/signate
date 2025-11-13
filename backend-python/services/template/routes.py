"""
Template Routes
FastAPI endpoints for template management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser

from services.template.dtos import (
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateResponse,
    TemplateListResponse,
    RenderTemplateRequest,
    RenderTemplateResponse,
    ValidateTemplateRequest,
    ValidateTemplateResponse,
    ExtractVariablesRequest,
    ExtractVariablesResponse
)
from services.template.use_cases.create_template import create_template_use_case
from services.template.use_cases.get_templates import (
    get_template_by_id_use_case,
    get_templates_use_case
)
from services.template.use_cases.update_template import (
    update_template_use_case,
    delete_template_use_case
)
from services.template.use_cases.render_template import (
    render_template_use_case,
    validate_template_use_case,
    extract_variables_use_case
)

router = APIRouter(prefix="/templates", tags=["templates"])


# ============================================================================
# Template CRUD Endpoints
# ============================================================================

@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(
    request: CreateTemplateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new template

    Permissions: All authenticated users
    """
    return create_template_use_case(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        request=request,
        db=db
    )


@router.get("", response_model=TemplateListResponse)
def get_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all templates for current organization

    Filters:
    - template_type: text, image, video, html, greeting
    - is_active: true/false
    """
    return get_templates_use_case(
        organization_id=current_user.organization_id,
        template_type=template_type,
        is_active=is_active,
        skip=skip,
        limit=limit,
        db=db
    )


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int = Path(..., description="Template ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get template by ID"""
    return get_template_by_id_use_case(
        template_id=template_id,
        organization_id=current_user.organization_id,
        db=db
    )


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: int = Path(..., description="Template ID"),
    request: UpdateTemplateRequest = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update template

    Permissions: All authenticated users
    """
    return update_template_use_case(
        template_id=template_id,
        organization_id=current_user.organization_id,
        request=request,
        db=db
    )


@router.delete("/{template_id}")
def delete_template(
    template_id: int = Path(..., description="Template ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete template

    Permissions: All authenticated users
    """
    return delete_template_use_case(
        template_id=template_id,
        organization_id=current_user.organization_id,
        db=db
    )


# ============================================================================
# Template Rendering Endpoints
# ============================================================================

@router.post("/{template_id}/render", response_model=RenderTemplateResponse)
def render_template(
    template_id: int = Path(..., description="Template ID"),
    request: RenderTemplateRequest = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Render template with provided data

    Returns rendered content with all variables substituted
    """
    return render_template_use_case(
        template_id=template_id,
        organization_id=current_user.organization_id,
        request=request,
        db=db
    )


@router.post("/validate", response_model=ValidateTemplateResponse)
def validate_template(
    request: ValidateTemplateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate template syntax and optionally render with sample data

    Returns validation result with extracted variables
    """
    return validate_template_use_case(
        request=request,
        db=db
    )


@router.post("/extract-variables", response_model=ExtractVariablesResponse)
def extract_variables(
    request: ExtractVariablesRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract variable names from template content

    Returns list of unique variables found in template
    """
    return extract_variables_use_case(
        request=request,
        db=db
    )
