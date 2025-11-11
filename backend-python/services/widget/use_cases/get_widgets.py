"""
Get Widgets Use Case
Business logic for retrieving widgets
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.widget.dtos import WidgetResponse, WidgetListResponse
from services.widget.repositories.widget_repo import WidgetRepository


def get_widget_by_id_use_case(
    widget_id: int,
    organization_id: int,
    db: Session
) -> WidgetResponse:
    """Get widget by ID"""
    repo = WidgetRepository(db)

    widget = repo.get_widget_by_id(widget_id, organization_id)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Widget with id {widget_id} not found"
        )

    return WidgetResponse.model_validate(widget)


def get_widgets_use_case(
    organization_id: int,
    widget_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = None
) -> WidgetListResponse:
    """Get widgets with optional filters"""
    repo = WidgetRepository(db)

    widgets, total = repo.get_widgets(
        organization_id=organization_id,
        widget_type=widget_type,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

    return WidgetListResponse(
        widgets=[WidgetResponse.model_validate(w) for w in widgets],
        total=total
    )
