"""
Get Schedules Use Case
Business logic for retrieving schedules
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, time, datetime

from services.schedule.dtos import (
    ScheduleResponse,
    ScheduleListResponse,
    ActiveScheduleResponse
)
from services.schedule.repositories.schedule_repo import ScheduleRepository


def get_schedule_by_id_use_case(
    schedule_id: int,
    organization_id: int,
    db: Session
) -> ScheduleResponse:
    """Get schedule by ID"""
    repo = ScheduleRepository(db)

    schedule = repo.get_schedule_by_id(schedule_id, organization_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )

    return ScheduleResponse.model_validate(schedule)


def get_schedules_use_case(
    organization_id: int,
    playlist_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    recurrence_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = None
) -> ScheduleListResponse:
    """Get schedules with filters"""
    repo = ScheduleRepository(db)

    schedules, total = repo.get_schedules(
        organization_id=organization_id,
        playlist_id=playlist_id,
        is_active=is_active,
        recurrence_type=recurrence_type,
        skip=skip,
        limit=limit
    )

    return ScheduleListResponse(
        schedules=[ScheduleResponse.model_validate(s) for s in schedules],
        total=total
    )


def get_active_schedule_use_case(
    organization_id: int,
    check_date: Optional[date] = None,
    check_time: Optional[time] = None,
    db: Session = None
) -> ActiveScheduleResponse:
    """
    Get active schedule at specific date/time

    Business Rules:
    - Returns highest priority schedule that is active at the given time
    - If no date provided, uses current date
    - If no time provided, uses current time
    - Checks recurrence patterns and exceptions
    """
    repo = ScheduleRepository(db)

    # Use current date/time if not provided
    now = datetime.now()
    if check_date is None:
        check_date = now.date()
    if check_time is None:
        check_time = now.time()

    # Get all potentially active schedules (ordered by priority)
    schedules = repo.get_active_schedules_at(
        organization_id=organization_id,
        check_date=check_date,
        check_time=check_time
    )

    # Find first schedule that matches recurrence pattern
    for schedule in schedules:
        # Check if date is in exceptions
        if schedule.exceptions:
            date_str = check_date.isoformat()
            if date_str in schedule.exceptions:
                continue

        # Check recurrence pattern
        if is_schedule_active_on_date(schedule, check_date):
            return ActiveScheduleResponse(
                schedule=ScheduleResponse.model_validate(schedule),
                playlist_id=schedule.playlist_id,
                schedule_name=schedule.name,
                priority=schedule.priority,
                is_found=True
            )

    # No active schedule found
    return ActiveScheduleResponse(
        schedule=None,
        playlist_id=None,
        schedule_name=None,
        priority=None,
        is_found=False
    )


def is_schedule_active_on_date(schedule, check_date: date) -> bool:
    """
    Check if schedule is active on given date based on recurrence pattern

    Returns True if schedule should be active on this date
    """
    recurrence_type = schedule.recurrence_type or 'once'

    # Once: Only on start_date
    if recurrence_type == 'once':
        return check_date == schedule.start_date

    # Daily: Every N days
    if recurrence_type == 'daily':
        interval = 1
        if schedule.recurrence_pattern and 'interval' in schedule.recurrence_pattern:
            interval = schedule.recurrence_pattern['interval']

        days_diff = (check_date - schedule.start_date).days
        return days_diff >= 0 and days_diff % interval == 0

    # Weekly: Specific days of week
    if recurrence_type == 'weekly':
        if not schedule.recurrence_pattern or 'days' not in schedule.recurrence_pattern:
            return False

        # Python weekday: 0=Mon, 6=Sun
        # Our format: 1=Mon, 7=Sun
        weekday = check_date.weekday() + 1
        return weekday in schedule.recurrence_pattern['days']

    # Monthly: Specific days of month
    if recurrence_type == 'monthly':
        if not schedule.recurrence_pattern or 'days' not in schedule.recurrence_pattern:
            return False

        return check_date.day in schedule.recurrence_pattern['days']

    # Yearly: Specific date each year
    if recurrence_type == 'yearly':
        if not schedule.recurrence_pattern:
            return False

        month = schedule.recurrence_pattern.get('month')
        day_of_month = schedule.recurrence_pattern.get('day_of_month')

        if not month or not day_of_month:
            return False

        return check_date.month == month and check_date.day == day_of_month

    return False
