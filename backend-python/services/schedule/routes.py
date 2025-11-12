"""
Schedule Routes
REST API endpoints for schedule management
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, time

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser
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
    CheckConflictResponse
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
# Schedule CRUD Endpoints
# ============================================================================

@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    request: CreateScheduleRequest,
    current_user: CurrentUser = Depends(get_current_user),
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

    Priority:
    - Higher priority (0-100) wins when schedules overlap
    - Default: 0
    """
    return create_schedule_use_case(
        organization_id=current_user["organization_id"],
        request=request,
        created_by=current_user["user_id"],
        db=db
    )


@router.get("/schedules", response_model=ScheduleListResponse)
def get_schedules(
    playlist_id: Optional[int] = Query(None, description="Filter by playlist ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    recurrence_type: Optional[str] = Query(None, description="Filter by recurrence type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get schedules with filters

    Supports filtering by:
    - playlist_id
    - is_active (true/false)
    - recurrence_type (once, daily, weekly, monthly, yearly)
    - Pagination with skip/limit

    Results ordered by priority (highest first), then start_date (newest first)
    """
    return get_schedules_use_case(
        organization_id=current_user["organization_id"],
        playlist_id=playlist_id,
        is_active=is_active,
        recurrence_type=recurrence_type,
        skip=skip,
        limit=limit,
        db=db
    )


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: int,
    current_user: CurrentUser = Depends(get_current_user),
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update schedule"""
    return update_schedule_use_case(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        request=request,
        db=db
    )


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_200_OK)
def delete_schedule(
    schedule_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete schedule (hard delete)"""
    return delete_schedule_use_case(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        db=db
    )


@router.post("/schedules/{schedule_id}/deactivate", response_model=ScheduleResponse)
def deactivate_schedule(
    schedule_id: int,
    current_user: CurrentUser = Depends(get_current_user),
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get currently active schedule

    Returns highest priority schedule that is active right now.
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get active schedule at specific date/time

    Returns highest priority schedule that would be active at the given date/time.
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
    current_user: CurrentUser = Depends(get_current_user),
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check for schedule conflicts

    Finds schedules that overlap with given parameters.
    Useful for preventing conflicts before creating/updating schedules.

    Note: Higher priority schedules will take precedence in actual playback.
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
# Schedule Execution Control
# ============================================================================

@router.post("/schedules/refresh", status_code=status.HTTP_200_OK)
async def refresh_schedules(
    current_user: dict = Depends(get_current_user),
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
        if current_user["role"] not in ["admin", "super_admin"]:
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
