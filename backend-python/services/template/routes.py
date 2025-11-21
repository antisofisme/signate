"""
Template Routes
FastAPI endpoints for template management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, Request
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser
from shared.logging import AuditLogger
from shared.pagination import PaginationParams

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

# Initialize audit logger
audit_logger = AuditLogger()


# ============================================================================
# Template CRUD Endpoints
# ============================================================================

@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(
    request: CreateTemplateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Create a new template

    Permissions: All authenticated users
    """
    result = create_template_use_case(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        request=request,
        db=db
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="template.create",
        resource_type="template",
        resource_id=result.id,
        details={"name": result.name, "template_type": result.template_type},
        ip_address=http_request.client.host if http_request else None,
        organization_id=current_user.organization_id
    )

    return result


@router.get("", response_model=TemplateListResponse)
def get_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    pagination: PaginationParams = Depends(PaginationParams.as_query),
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
        skip=pagination.skip,
        limit=pagination.limit,
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
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Update template

    Permissions: All authenticated users
    """
    result = update_template_use_case(
        template_id=template_id,
        organization_id=current_user.organization_id,
        request=request,
        db=db
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="template.update",
        resource_type="template",
        resource_id=result.id,
        details={"name": result.name, "is_active": result.is_active},
        ip_address=http_request.client.host if http_request else None,
        organization_id=current_user.organization_id
    )

    return result


@router.delete("/{template_id}")
def delete_template(
    template_id: int = Path(..., description="Template ID"),
    current_user: CurrentUser = Depends(get_current_user),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Delete template

    Permissions: All authenticated users
    """
    # Get template name before deletion for audit log
    from services.template.repositories.template_repo import TemplateRepository
    repo = TemplateRepository(db)
    template = repo.get_template_by_id(template_id, current_user.organization_id)
    template_name = template.name if template else f"ID:{template_id}"

    result = delete_template_use_case(
        template_id=template_id,
        organization_id=current_user.organization_id,
        db=db
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="template.delete",
        resource_type="template",
        resource_id=template_id,
        details={"name": template_name},
        ip_address=http_request.client.host if http_request else None,
        organization_id=current_user.organization_id
    )

    return result


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
