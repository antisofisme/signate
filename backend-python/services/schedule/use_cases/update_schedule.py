"""
Update Schedule Use Case
Business logic for updating and deleting schedules
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.schedule.dtos import UpdateScheduleRequest, ScheduleResponse
from services.schedule.repositories.schedule_repo import ScheduleRepository
from services.schedule.use_cases.create_schedule import VALID_RECURRENCE_TYPES


def update_schedule_use_case(
    schedule_id: int,
    organization_id: int,
    request: UpdateScheduleRequest,
    updated_by_id: Optional[int],
    db: Session
) -> ScheduleResponse:
    """
    Update schedule

    Business Rules:
    - Schedule must exist and belong to organization
    - Same validation rules as create apply

    Args:
        schedule_id: Schedule ID
        organization_id: Organization ID
        request: Update request
        updated_by_id: User ID who updates this schedule (for audit trail)
        db: Database session
    """
    repo = ScheduleRepository(db)

    # Get existing schedule
    schedule = repo.get_schedule_by_id(schedule_id, organization_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )

    # Validate recurrence type if updating
    if request.recurrence_type and request.recurrence_type not in VALID_RECURRENCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid recurrence_type. Must be one of: {', '.join(VALID_RECURRENCE_TYPES)}"
        )

    # Validate date range if updating dates
    start_date = request.start_date if request.start_date else schedule.start_date
    end_date = request.end_date if request.end_date is not None else schedule.end_date

    if end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Validate time range if updating times
    start_time = request.start_time if request.start_time is not None else schedule.start_time
    end_time = request.end_time if request.end_time is not None else schedule.end_time

    if start_time and end_time:
        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time must be after start_time"
            )

    # Update schedule (with audit trail - Migration 046)
    updated_schedule = repo.update_schedule(schedule, request, updated_by_id)

    return ScheduleResponse.model_validate(updated_schedule)


def delete_schedule_use_case(
    schedule_id: int,
    organization_id: int,
    db: Session,
    deleted_by_id: Optional[int] = None
) -> dict:
    """
    Delete schedule with audit tracking

    Args:
        schedule_id: Schedule ID to delete
        organization_id: Organization ID for ownership check
        db: Database session
        deleted_by_id: User ID who deleted the schedule (audit trail)
    """
    repo = ScheduleRepository(db)

    # Check if schedule exists
    schedule = repo.get_schedule_by_id(schedule_id, organization_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )

    # Soft delete schedule with audit tracking
    success = repo.delete_schedule(schedule_id, organization_id, deleted_by_id=deleted_by_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule"
        )

    return {"message": f"Schedule {schedule_id} deleted successfully"}


def deactivate_schedule_use_case(
    schedule_id: int,
    organization_id: int,
    db: Session
) -> ScheduleResponse:
    """Deactivate schedule (soft delete)"""
    repo = ScheduleRepository(db)

    # Check if schedule exists
    schedule = repo.get_schedule_by_id(schedule_id, organization_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )

    # Deactivate
    success = repo.deactivate_schedule(schedule_id, organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate schedule"
        )

    # Return updated schedule
    schedule = repo.get_schedule_by_id(schedule_id, organization_id)
    return ScheduleResponse.model_validate(schedule)


def activate_schedule_use_case(
    schedule_id: int,
    organization_id: int,
    db: Session
) -> ScheduleResponse:
    """Activate schedule"""
    repo = ScheduleRepository(db)

    # Check if schedule exists
    schedule = repo.get_schedule_by_id(schedule_id, organization_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )

    # Activate
    success = repo.activate_schedule(schedule_id, organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate schedule"
        )

    # Return updated schedule
    schedule = repo.get_schedule_by_id(schedule_id, organization_id)
    return ScheduleResponse.model_validate(schedule)
