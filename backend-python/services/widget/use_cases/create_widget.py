"""
Create Widget Use Case
Business logic for creating new widgets
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.widget.dtos import CreateWidgetRequest, WidgetResponse
from services.widget.repositories.widget_repo import WidgetRepository


def create_widget_use_case(
    organization_id: int,
    user_id: int,
    request: CreateWidgetRequest,
    db: Session
) -> WidgetResponse:
    """
    Create a new widget

    Business Rules:
    - Widget name must be unique within organization
    - Widget type must be valid
    - Config must match widget type schema (basic validation)
    """
    repo = WidgetRepository(db)

    # Check if widget name already exists
    if repo.check_widget_name_exists(organization_id, request.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Widget with name '{request.name}' already exists"
        )

    # Validate widget type
    valid_types = ['clock', 'weather', 'news', 'hotel_info', 'custom']
    if request.widget_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid widget_type. Must be one of: {', '.join(valid_types)}"
        )

    # Create widget
    widget = repo.create_widget(organization_id, user_id, request)

    return WidgetResponse.model_validate(widget)
