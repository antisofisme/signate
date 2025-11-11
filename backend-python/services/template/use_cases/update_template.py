"""
Update Template Use Case
Business logic for updating templates
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.template.dtos import UpdateTemplateRequest, TemplateResponse
from services.template.repositories.template_repo import TemplateRepository


def update_template_use_case(
    template_id: int,
    organization_id: int,
    request: UpdateTemplateRequest,
    db: Session
) -> TemplateResponse:
    """
    Update template

    Business Rules:
    - Template must exist and belong to organization
    - If name is changed, new name must be unique
    """
    repo = TemplateRepository(db)

    # Check if template exists
    existing_template = repo.get_template_by_id(template_id, organization_id)
    if not existing_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found"
        )

    # If name is being changed, check uniqueness
    if request.name and request.name != existing_template.name:
        if repo.check_template_name_exists(organization_id, request.name, exclude_id=template_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Template with name '{request.name}' already exists"
            )

    # Update template
    updated_template = repo.update_template(template_id, organization_id, request)

    return TemplateResponse.model_validate(updated_template)


def delete_template_use_case(
    template_id: int,
    organization_id: int,
    db: Session
) -> dict:
    """
    Delete template

    Business Rules:
    - Template must exist and belong to organization
    """
    repo = TemplateRepository(db)

    # Check if template exists
    template = repo.get_template_by_id(template_id, organization_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found"
        )

    # Delete template
    success = repo.delete_template(template_id, organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )

    return {"message": f"Template {template_id} deleted successfully"}
