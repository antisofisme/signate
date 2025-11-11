"""
Get Templates Use Case
Business logic for retrieving templates
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.template.dtos import TemplateResponse, TemplateListResponse
from services.template.repositories.template_repo import TemplateRepository


def get_template_by_id_use_case(
    template_id: int,
    organization_id: int,
    db: Session
) -> TemplateResponse:
    """Get template by ID"""
    repo = TemplateRepository(db)

    template = repo.get_template_by_id(template_id, organization_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found"
        )

    return TemplateResponse.model_validate(template)


def get_templates_use_case(
    organization_id: int,
    template_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = None
) -> TemplateListResponse:
    """Get templates with optional filters"""
    repo = TemplateRepository(db)

    templates, total = repo.get_templates(
        organization_id=organization_id,
        template_type=template_type,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

    return TemplateListResponse(
        templates=[TemplateResponse.model_validate(t) for t in templates],
        total=total
    )
