"""
Get Schedules Use Case
Business logic for retrieving schedules
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, time, datetime, timezone

from services.schedule.dtos import (
    ScheduleResponse,
    ScheduleListResponse,
    ActiveScheduleResponse,
    TargetDeviceInfo,
    TargetTagInfo
)
from services.schedule.repositories.schedule_repo import ScheduleRepository
from services.schedule.repositories.models import Schedule


def _schedule_to_response(schedule: Schedule) -> ScheduleResponse:
    """
    Convert Schedule model to ScheduleResponse with targeting data.
    Maps junction table relationships to target_devices and target_tags.
    """
    # Get target devices from junction table
    target_devices = None
    if schedule.device_targets:
        target_devices = [
            TargetDeviceInfo(
                id=dt.device.id,
                device_name=dt.device.device_name
            )
            for dt in schedule.device_targets
            if dt.device is not None
        ]

    # Get target tags from junction table
    target_tags = None
    if schedule.tag_targets:
        target_tags = [
            TargetTagInfo(
                id=tt.tag.id,
                name=tt.tag.name
            )
            for tt in schedule.tag_targets
            if tt.tag is not None
        ]

    return ScheduleResponse(
        id=schedule.id,
        organization_id=schedule.organization_id,
        name=schedule.name,
        description=schedule.description,
        playlist_id=schedule.playlist_id,
        # Legacy fields for backward compatibility
        device_ids=schedule.device_ids,
        tag_ids=schedule.tag_ids,
        # New normalized targeting
        target_devices=target_devices,
        target_tags=target_tags,
        applies_to_all=schedule.applies_to_all or False,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        recurrence_type=schedule.recurrence_type,
        recurrence_pattern=schedule.recurrence_pattern,
        exception_dates=schedule.exceptions,
        color=schedule.color or "#3B82F6",
        mode=schedule.mode or "rotate",
        is_active=schedule.is_active,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        created_by_id=schedule.created_by_id,
        updated_by_id=schedule.updated_by_id
    )


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

    return _schedule_to_response(schedule)


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
        schedules=[_schedule_to_response(s) for s in schedules],
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
    - Returns active schedule that matches the given time
    - If no date provided, uses current date
    - If no time provided, uses current time
    - Checks recurrence patterns and exceptions
    """
    repo = ScheduleRepository(db)

    # Use current date/time if not provided
    now = datetime.now(timezone.utc)
    if check_date is None:
        check_date = now.date()
    if check_time is None:
        check_time = now.time()

    # Get all potentially active schedules (ordered by start_date)
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
                schedule=_schedule_to_response(schedule),
                playlist_id=schedule.playlist_id,
                schedule_name=schedule.name,
                color=schedule.color,
                is_found=True
            )

    # No active schedule found
    return ActiveScheduleResponse(
        schedule=None,
        playlist_id=None,
        schedule_name=None,
        color=None,
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
