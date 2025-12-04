"""
Schedule Client Routes
Public endpoints for player to fetch schedules (no JWT required)
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import date, time, datetime

from shared.database import get_db
from services.schedule.repositories.schedule_repo import ScheduleRepository


# ============================================================================
# Response Models (simplified for player)
# ============================================================================

class PlayerScheduleResponse(BaseModel):
    """Schedule response for player (simplified)"""
    id: int
    name: str
    playlist_id: int
    organization_id: int

    start_date: date
    end_date: Optional[date]
    start_time: Optional[time]
    end_time: Optional[time]

    recurrence_type: Optional[str]
    recurrence_pattern: Optional[Dict[str, Any]]
    exceptions: Optional[List[str]] = Field(None, description="Exception dates")

    color: str
    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlayerScheduleListResponse(BaseModel):
    """List of schedules for player"""
    schedules: List[PlayerScheduleResponse]
    total: int


# ============================================================================
# Router
# ============================================================================

router = APIRouter()


@router.get("/api/v1/client/schedules", response_model=PlayerScheduleListResponse)
def get_player_schedules(
    organization_id: int = Query(..., description="Organization ID (required)"),
    device_id: Optional[int] = Query(None, description="Device ID for targeting filter"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get active schedules for player (public endpoint - no JWT required)

    This endpoint is designed for player/device use:
    - Filters by organization_id (required)
    - Optionally filters by device_id (for device targeting)
    - Returns only is_active=true schedules by default

    Device targeting logic:
    - If device_id provided, returns schedules that:
      1. Have this device_id in device_ids array, OR
      2. Have applies_to_all=true, OR
      3. Have no targeting (legacy schedules)
    - If device_id not provided, returns all active schedules for org
    """
    repo = ScheduleRepository(db)
    schedules = repo.get_schedules_for_device(
        organization_id=organization_id,
        device_id=device_id,
        is_active=is_active
    )

    # Convert to response format
    schedule_responses = [
        PlayerScheduleResponse(
            id=s.id,
            name=s.name,
            playlist_id=s.playlist_id,
            organization_id=s.organization_id,
            start_date=s.start_date,
            end_date=s.end_date,
            start_time=s.start_time,
            end_time=s.end_time,
            recurrence_type=s.recurrence_type,
            recurrence_pattern=s.recurrence_pattern,
            exceptions=s.exceptions,
            color=s.color,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        for s in schedules
    ]

    return PlayerScheduleListResponse(
        schedules=schedule_responses,
        total=len(schedule_responses)
    )
