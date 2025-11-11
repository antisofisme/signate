"""
Create Template Use Case
Business logic for creating new templates
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.template.dtos import CreateTemplateRequest, TemplateResponse
from services.template.repositories.template_repo import TemplateRepository


def create_template_use_case(
    organization_id: int,
    user_id: int,
    request: CreateTemplateRequest,
    db: Session
) -> TemplateResponse:
    """
    Create a new template

    Business Rules:
    - Template name must be unique within organization
    - Template type must be valid
    - Content must not be empty
    """
    repo = TemplateRepository(db)

    # Check if template name already exists
    if repo.check_template_name_exists(organization_id, request.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template with name '{request.name}' already exists"
        )

    # Validate template type
    valid_types = ['text', 'image', 'video', 'html', 'greeting']
    if request.template_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template_type. Must be one of: {', '.join(valid_types)}"
        )

    # Create template
    template = repo.create_template(organization_id, user_id, request)

    return TemplateResponse.model_validate(template)
