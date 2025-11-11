"""
Create Schedule Use Case
Business logic for creating schedules
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.schedule.dtos import CreateScheduleRequest, ScheduleResponse
from services.schedule.repositories.schedule_repo import ScheduleRepository


# Valid recurrence types
VALID_RECURRENCE_TYPES = ['once', 'daily', 'weekly', 'monthly', 'yearly']


def create_schedule_use_case(
    organization_id: int,
    request: CreateScheduleRequest,
    created_by: int,
    db: Session
) -> ScheduleResponse:
    """
    Create new schedule

    Business Rules:
    - Recurrence type must be valid
    - End date must be after start date (if provided)
    - End time must be after start time (if both provided)
    - Playlist must exist (validated at API layer)
    - Priority range: 0-100
    """
    repo = ScheduleRepository(db)

    # Validate recurrence type
    if request.recurrence_type and request.recurrence_type not in VALID_RECURRENCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid recurrence_type. Must be one of: {', '.join(VALID_RECURRENCE_TYPES)}"
        )

    # Validate date range
    if request.end_date and request.end_date < request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Validate time range
    if request.start_time and request.end_time:
        if request.end_time <= request.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time must be after start_time"
            )

    # Validate recurrence pattern for weekly
    if request.recurrence_type == 'weekly':
        if not request.recurrence_pattern or not request.recurrence_pattern.days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weekly recurrence requires 'days' in recurrence_pattern (1=Mon, 7=Sun)"
            )
        # Validate days are 1-7
        for day in request.recurrence_pattern.days:
            if day < 1 or day > 7:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Days must be between 1 (Monday) and 7 (Sunday)"
                )

    # Validate recurrence pattern for monthly
    if request.recurrence_type == 'monthly':
        if not request.recurrence_pattern or not request.recurrence_pattern.days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monthly recurrence requires 'days' in recurrence_pattern (1-31)"
            )
        # Validate days are 1-31
        for day in request.recurrence_pattern.days:
            if day < 1 or day > 31:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Days must be between 1 and 31 for monthly recurrence"
                )

    # Validate recurrence pattern for yearly
    if request.recurrence_type == 'yearly':
        if not request.recurrence_pattern or not request.recurrence_pattern.month or not request.recurrence_pattern.day_of_month:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Yearly recurrence requires 'month' and 'day_of_month' in recurrence_pattern"
            )

    # Create schedule
    schedule = repo.create_schedule(
        organization_id=organization_id,
        request=request,
        created_by=created_by
    )

    return ScheduleResponse.model_validate(schedule)
