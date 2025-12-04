"""
Calculate Recurrence Use Case
Business logic for calculating schedule occurrences
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, timedelta
from typing import List

from services.schedule.dtos import (
    CalculateNextOccurrenceResponse,
    NextOccurrence,
    CheckConflictResponse,
    ConflictSchedule
)
from services.schedule.repositories.schedule_repo import ScheduleRepository
from services.schedule.use_cases.get_schedules import is_schedule_active_on_date


def calculate_next_occurrence_use_case(
    schedule_id: int,
    organization_id: int,
    from_date: date = None,
    db: Session = None
) -> CalculateNextOccurrenceResponse:
    """
    Calculate next occurrences for schedule

    Returns:
    - Next occurrence after from_date
    - List of next 10 occurrences
    """
    repo = ScheduleRepository(db)

    # Get schedule
    schedule = repo.get_schedule_by_id(schedule_id, organization_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )

    # Use current date if not provided
    if from_date is None:
        from_date = date.today()

    # Calculate next occurrences
    occurrences = []
    check_date = from_date
    max_iterations = 365  # Prevent infinite loop (check up to 1 year ahead)
    iterations = 0

    while len(occurrences) < 10 and iterations < max_iterations:
        # Check if schedule has ended
        if schedule.end_date and check_date > schedule.end_date:
            break

        # Check if date is in exceptions
        is_exception = False
        if schedule.exceptions:
            date_str = check_date.isoformat()
            if date_str in schedule.exceptions:
                is_exception = True

        # Check if schedule is active on this date
        if is_schedule_active_on_date(schedule, check_date) and check_date >= from_date:
            occurrences.append(NextOccurrence(
                date=check_date,
                start_time=schedule.start_time,
                end_time=schedule.end_time,
                is_exception=is_exception
            ))

        # Move to next day
        check_date += timedelta(days=1)
        iterations += 1

    # Get next non-exception occurrence
    next_occurrence = None
    for occ in occurrences:
        if not occ.is_exception:
            next_occurrence = occ
            break

    return CalculateNextOccurrenceResponse(
        schedule_id=schedule.id,
        schedule_name=schedule.name,
        next_occurrence=next_occurrence,
        occurrences=occurrences
    )


def check_conflicts_use_case(
    organization_id: int,
    playlist_id: int,
    start_date: date,
    end_date: date = None,
    start_time: date = None,
    end_time: date = None,
    exclude_schedule_id: int = None,
    db: Session = None
) -> CheckConflictResponse:
    """
    Check for schedule conflicts

    Returns conflicting schedules that overlap with given parameters
    """
    repo = ScheduleRepository(db)

    conflicts = repo.get_conflicting_schedules(
        organization_id=organization_id,
        playlist_id=playlist_id,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        exclude_schedule_id=exclude_schedule_id
    )

    has_conflicts = len(conflicts) > 0

    conflict_list = [
        ConflictSchedule(
            id=s.id,
            name=s.name,
            color=s.color,
            start_date=s.start_date,
            end_date=s.end_date,
            start_time=s.start_time,
            end_time=s.end_time
        )
        for s in conflicts
    ]

    message = "No conflicts found"
    if has_conflicts:
        message = f"Found {len(conflicts)} conflicting schedule(s). Schedules with 'override' mode will take precedence."

    return CheckConflictResponse(
        has_conflicts=has_conflicts,
        conflicts=conflict_list,
        message=message
    )
