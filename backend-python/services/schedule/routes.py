"""
Schedule Routes
REST API endpoints for schedule management with RBAC integration
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from datetime import date, time

from shared.database import get_db
from shared.middleware import require_permission
from shared.pagination import PaginationParams
from shared.logging import AuditLogger
from .domain.schedule_executor import get_schedule_executor
from services.schedule.dtos import (
    CreateScheduleRequest,
    UpdateScheduleRequest,
    ScheduleResponse,
    ScheduleListResponse,
    ActiveScheduleRequest,
    ActiveScheduleResponse,
    CalculateNextOccurrenceRequest,
    CalculateNextOccurrenceResponse,
    CheckConflictRequest,
    CheckConflictResponse,
    GetOccurrencesRequest,
    GetOccurrencesResponse
)
from services.schedule.use_cases.create_schedule import create_schedule_use_case
from services.schedule.use_cases.get_schedules import (
    get_schedule_by_id_use_case,
    get_schedules_use_case,
    get_active_schedule_use_case
)
from services.schedule.use_cases.update_schedule import (
    update_schedule_use_case,
    delete_schedule_use_case,
    deactivate_schedule_use_case
)
from services.schedule.use_cases.calculate_recurrence import (
    calculate_next_occurrence_use_case,
    check_conflicts_use_case
)


router = APIRouter()


# ============================================================================
# Dependency Injection
# ============================================================================

def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger()


# ============================================================================
# Schedule CRUD Endpoints
# ============================================================================

@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    request: CreateScheduleRequest,
    http_request: Request,
    current_user: dict = Depends(require_permission("schedules", "create")),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    db: Session = Depends(get_db)
):
    """
    Create new schedule

    Supports recurrence patterns:
    - **once**: Single occurrence
    - **daily**: Every N days (interval)
    - **weekly**: Specific days of week (1=Mon, 7=Sun)
    - **monthly**: Specific days of month (1-31)
    - **yearly**: Specific date each year (month + day_of_month)

    Color:
    - Hex color for calendar display (e.g. #3B82F6)
    - Default: #3B82F6 (blue)
    """
    schedule = create_schedule_use_case(
        organization_id=current_user["organization_id"],
        request=request,
        created_by_id=current_user["user_id"],
        db=db
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="schedule.create",
        resource_type="schedule",
        resource_id=schedule.id,
        details={
            "playlist_id": schedule.playlist_id,
            "recurrence_type": schedule.recurrence_type,
            "start_date": str(schedule.start_date),
            "color": schedule.color,
            "is_active": schedule.is_active
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    return schedule


@router.get("/schedules", response_model=ScheduleListResponse)
def get_schedules(
    playlist_id: Optional[int] = Query(None, description="Filter by playlist ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    recurrence_type: Optional[str] = Query(None, description="Filter by recurrence type"),
    pagination: PaginationParams = Depends(PaginationParams.as_query),
    current_user: dict = Depends(require_permission("schedules", "read")),
    db: Session = Depends(get_db)
):
    """
    Get schedules with filters

    Supports filtering by:
    - playlist_id
    - is_active (true/false)
    - recurrence_type (once, daily, weekly, monthly, yearly)
    - Pagination with skip/limit

    Results ordered by start_date (newest first)
    """
    return get_schedules_use_case(
        organization_id=current_user["organization_id"],
        playlist_id=playlist_id,
        is_active=is_active,
        recurrence_type=recurrence_type,
        skip=pagination.skip,
        limit=pagination.limit,
        db=db
    )


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: int,
    current_user: dict = Depends(require_permission("schedules", "read")),
    db: Session = Depends(get_db)
):
    """Get schedule by ID"""
    return get_schedule_by_id_use_case(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        db=db
    )


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    request: UpdateScheduleRequest,
    http_request: Request,
    current_user: dict = Depends(require_permission("schedules", "edit")),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    db: Session = Depends(get_db)
):
    """Update schedule"""
    schedule = update_schedule_use_case(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        request=request,
        updated_by_id=current_user["user_id"],
        db=db
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="schedule.update",
        resource_type="schedule",
        resource_id=schedule_id,
        details={
            "playlist_id": schedule.playlist_id if hasattr(schedule, 'playlist_id') else None,
            "is_active": schedule.is_active if hasattr(schedule, 'is_active') else None,
            "color": schedule.color if hasattr(schedule, 'color') else None
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    return schedule


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_200_OK)
def delete_schedule(
    schedule_id: int,
    http_request: Request,
    current_user: dict = Depends(require_permission("schedules", "delete")),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    db: Session = Depends(get_db)
):
    """Delete schedule (soft delete with audit tracking)"""
    result = delete_schedule_use_case(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        deleted_by_id=current_user["user_id"],
        db=db
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="schedule.delete",
        resource_type="schedule",
        resource_id=schedule_id,
        details={
            "deleted": True
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    return result


@router.post("/schedules/{schedule_id}/deactivate", response_model=ScheduleResponse)
def deactivate_schedule(
    schedule_id: int,
    current_user: dict = Depends(require_permission("schedules", "edit")),
    db: Session = Depends(get_db)
):
    """Deactivate schedule (soft delete)"""
    return deactivate_schedule_use_case(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        db=db
    )


# ============================================================================
# Active Schedule Endpoints
# ============================================================================

@router.get("/schedules/active/now", response_model=ActiveScheduleResponse)
def get_active_schedule_now(
    current_user: dict = Depends(require_permission("schedules", "read")),
    db: Session = Depends(get_db)
):
    """
    Get currently active schedule

    Returns active schedule that matches current time.
    Uses current date/time to determine active schedule.
    """
    return get_active_schedule_use_case(
        organization_id=current_user["organization_id"],
        check_date=None,  # Will use current date
        check_time=None,  # Will use current time
        db=db
    )


@router.post("/schedules/active/check", response_model=ActiveScheduleResponse)
def get_active_schedule_at(
    request: ActiveScheduleRequest,
    current_user: dict = Depends(require_permission("schedules", "read")),
    db: Session = Depends(get_db)
):
    """
    Get active schedule at specific date/time

    Returns schedule that would be active at the given date/time.
    Useful for previewing schedule behavior.
    """
    return get_active_schedule_use_case(
        organization_id=current_user["organization_id"],
        check_date=request.check_date,
        check_time=request.check_time,
        db=db
    )


# ============================================================================
# Recurrence Calculation Endpoints
# ============================================================================

@router.post("/schedules/{schedule_id}/calculate-next", response_model=CalculateNextOccurrenceResponse)
def calculate_next_occurrence(
    schedule_id: int,
    request: CalculateNextOccurrenceRequest,
    current_user: dict = Depends(require_permission("schedules", "read")),
    db: Session = Depends(get_db)
):
    """
    Calculate next occurrences for schedule

    Returns:
    - Next occurrence (excluding exceptions)
    - List of next 10 occurrences

    Useful for previewing schedule recurrence pattern.
    """
    return calculate_next_occurrence_use_case(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        from_date=request.from_date,
        db=db
    )


# ============================================================================
# Conflict Detection Endpoints
# ============================================================================

@router.post("/schedules/check-conflicts", response_model=CheckConflictResponse)
def check_schedule_conflicts(
    request: CheckConflictRequest,
    current_user: dict = Depends(require_permission("schedules", "read")),
    db: Session = Depends(get_db)
):
    """
    Check for schedule conflicts

    Finds schedules that overlap with given parameters.
    Useful for preventing conflicts before creating/updating schedules.

    Note: Schedules with 'override' mode will take precedence in actual playback.
    """
    return check_conflicts_use_case(
        organization_id=current_user["organization_id"],
        playlist_id=request.playlist_id,
        start_date=request.start_date,
        end_date=request.end_date,
        start_time=request.start_time,
        end_time=request.end_time,
        exclude_schedule_id=request.exclude_schedule_id,
        db=db
    )


# ============================================================================
# Calendar Occurrences Endpoint
# ============================================================================

@router.post("/schedules/occurrences", response_model=GetOccurrencesResponse)
def get_schedule_occurrences(
    request: GetOccurrencesRequest,
    current_user: dict = Depends(require_permission("schedules", "read")),
    db: Session = Depends(get_db)
):
    """
    Get schedule occurrences for calendar view

    Returns all schedule occurrences within the given date range.
    Used to populate the calendar view with schedule events.
    """
    from services.schedule.dtos import ScheduleOccurrence
    from services.schedule.repositories.schedule_repo import ScheduleRepository
    from datetime import datetime, timedelta

    repo = ScheduleRepository(db)
    organization_id = current_user["organization_id"]

    # Get all schedules for this organization
    schedules, _ = repo.get_schedules(organization_id=organization_id)

    occurrences = []
    start_date = request.start_date
    end_date = request.end_date

    for schedule in schedules:
        if not schedule.is_active:
            continue

        # Skip if schedule hasn't started yet or has ended
        if schedule.start_date > end_date:
            continue
        if schedule.end_date and schedule.end_date < start_date:
            continue

        # Filter by playlist if specified
        if request.playlist_id and schedule.playlist_id != request.playlist_id:
            continue

        # Get devices assigned to this schedule's playlist
        device_ids = []
        if schedule.playlist:
            device_ids = [d.id for d in schedule.playlist.devices] if hasattr(schedule.playlist, 'devices') else []

        # Filter by device if specified
        if request.device_id and request.device_id not in device_ids:
            continue

        # Calculate occurrences based on recurrence type
        current_date = max(schedule.start_date, start_date)
        schedule_end = min(schedule.end_date, end_date) if schedule.end_date else end_date

        exception_dates = schedule.exceptions or []

        while current_date <= schedule_end:
            should_occur = False

            if schedule.recurrence_type == 'once':
                should_occur = current_date == schedule.start_date
            elif schedule.recurrence_type == 'daily':
                interval = (schedule.recurrence_pattern or {}).get('interval', 1)
                days_since_start = (current_date - schedule.start_date).days
                should_occur = days_since_start % interval == 0
            elif schedule.recurrence_type == 'weekly':
                days_of_week = (schedule.recurrence_pattern or {}).get('days_of_week', [])
                day_name = current_date.strftime('%A').lower()
                should_occur = day_name in days_of_week
            elif schedule.recurrence_type == 'monthly':
                pattern = schedule.recurrence_pattern or {}
                day_of_month = pattern.get('day_of_month')
                if day_of_month:
                    should_occur = current_date.day == day_of_month
                elif pattern.get('last_day_of_month'):
                    next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
                    last_day = (next_month - timedelta(days=1)).day
                    should_occur = current_date.day == last_day

            # Check if this date is an exception
            if should_occur and str(current_date) not in exception_dates:
                occurrences.append(ScheduleOccurrence(
                    schedule_id=schedule.id,
                    schedule_name=schedule.name,
                    playlist_name=schedule.playlist.name if schedule.playlist else "Unknown",
                    occurrence_date=str(current_date),
                    start_time=str(schedule.start_time) if schedule.start_time else "00:00:00",
                    end_time=str(schedule.end_time) if schedule.end_time else "23:59:59",
                    color=schedule.color or "#3B82F6",
                    devices=device_ids
                ))

            current_date += timedelta(days=1)

    return GetOccurrencesResponse(
        occurrences=occurrences,
        total=len(occurrences)
    )


# ============================================================================
# Schedule Execution Control
# ============================================================================

@router.post("/schedules/refresh", status_code=status.HTTP_200_OK)
async def refresh_schedules(
    current_user: dict = Depends(require_permission("schedules", "edit")),
    organization_id: Optional[int] = Query(None, description="Refresh specific organization (admin only)")
):
    """
    Force immediate schedule refresh

    Manually triggers schedule check without waiting for next interval.
    Useful after creating/updating schedules to see immediate effect.

    - Regular users: Can only refresh their own organization
    - Admins: Can refresh any organization or all organizations
    """
    # Check permissions
    if organization_id and organization_id != current_user["organization_id"]:
        # Only admins can refresh other organizations
        if current_user.get("role") not in ["admin", "super_admin", "ADMIN", "SUPER_ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only refresh schedules for your own organization"
            )

    # Use user's organization if not specified
    target_org_id = organization_id or current_user["organization_id"]

    try:
        executor = get_schedule_executor()
        await executor.force_refresh(target_org_id)

        return {
            "message": f"Schedule refresh triggered for organization {target_org_id}",
            "organization_id": target_org_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh schedules: {str(e)}"
        )
