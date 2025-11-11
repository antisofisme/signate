"""
Update Widget Use Case
Business logic for updating widgets
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.widget.dtos import UpdateWidgetRequest, WidgetResponse
from services.widget.repositories.widget_repo import WidgetRepository


def update_widget_use_case(
    widget_id: int,
    organization_id: int,
    request: UpdateWidgetRequest,
    db: Session
) -> WidgetResponse:
    """
    Update widget

    Business Rules:
    - Widget must exist and belong to organization
    - If name is changed, new name must be unique
    """
    repo = WidgetRepository(db)

    # Check if widget exists
    existing_widget = repo.get_widget_by_id(widget_id, organization_id)
    if not existing_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Widget with id {widget_id} not found"
        )

    # If name is being changed, check uniqueness
    if request.name and request.name != existing_widget.name:
        if repo.check_widget_name_exists(organization_id, request.name, exclude_id=widget_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Widget with name '{request.name}' already exists"
            )

    # Update widget
    updated_widget = repo.update_widget(widget_id, organization_id, request)

    return WidgetResponse.model_validate(updated_widget)


def delete_widget_use_case(
    widget_id: int,
    organization_id: int,
    db: Session
) -> dict:
    """
    Delete widget

    Business Rules:
    - Widget must exist and belong to organization
    - Cascade delete will remove playlist_widgets assignments
    """
    repo = WidgetRepository(db)

    # Check if widget exists
    widget = repo.get_widget_by_id(widget_id, organization_id)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Widget with id {widget_id} not found"
        )

    # Delete widget
    success = repo.delete_widget(widget_id, organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete widget"
        )

    return {"message": f"Widget {widget_id} deleted successfully"}
