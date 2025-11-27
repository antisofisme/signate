"""
Schedule DTOs
Request and Response models for schedule endpoints
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date, time


# ============================================================================
# Recurrence Pattern Models
# ============================================================================

class RecurrencePattern(BaseModel):
    """Recurrence pattern configuration"""
    interval: Optional[int] = Field(1, description="Interval for recurrence (e.g., every 2 days)")
    days: Optional[List[int]] = Field(None, description="Days for weekly (1=Mon, 7=Sun) or monthly (1-31)")
    month: Optional[int] = Field(None, description="Month for yearly recurrence (1-12)")
    day_of_month: Optional[int] = Field(None, description="Day of month for yearly recurrence (1-31)")

    class Config:
        json_schema_extra = {
            "example": {
                "interval": 2,
                "days": [1, 3, 5]  # Monday, Wednesday, Friday
            }
        }


# ============================================================================
# Schedule CRUD DTOs
# ============================================================================

class CreateScheduleRequest(BaseModel):
    """Request to create schedule"""
    name: str = Field(..., min_length=1, max_length=255, description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    playlist_id: int = Field(..., description="Playlist ID to schedule")
    device_ids: Optional[List[int]] = Field(None, description="Target device IDs for this schedule")

    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="End date (optional for ongoing)")
    start_time: Optional[time] = Field(None, description="Start time (HH:MM:SS)")
    end_time: Optional[time] = Field(None, description="End time (HH:MM:SS)")

    recurrence_type: Optional[str] = Field("once", description="once, daily, weekly, monthly, yearly")
    recurrence_pattern: Optional[RecurrencePattern] = Field(None, description="Recurrence configuration")
    exception_dates: Optional[List[str]] = Field(None, description="Exception dates (YYYY-MM-DD)")

    priority: int = Field(0, ge=0, le=100, description="Priority (0-100, higher wins)")
    is_active: bool = Field(True, description="Active status")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Weekday Morning Schedule",
                "description": "Play breakfast menu 7-10am on weekdays",
                "playlist_id": 1,
                "device_ids": [1, 2, 3],
                "start_date": "2025-01-13",
                "end_date": "2025-12-31",
                "start_time": "07:00:00",
                "end_time": "10:00:00",
                "recurrence_type": "weekly",
                "recurrence_pattern": {
                    "interval": 1,
                    "days": [1, 2, 3, 4, 5]  # Mon-Fri
                },
                "exception_dates": ["2025-01-15", "2025-02-20"],
                "priority": 10,
                "is_active": True
            }
        }


class UpdateScheduleRequest(BaseModel):
    """Request to update schedule"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    playlist_id: Optional[int] = None
    device_ids: Optional[List[int]] = Field(None, description="Target device IDs for this schedule")

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    recurrence_type: Optional[str] = None
    recurrence_pattern: Optional[RecurrencePattern] = None
    exception_dates: Optional[List[str]] = None

    priority: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    """Schedule response model"""
    id: int
    organization_id: int
    name: str
    description: Optional[str]
    playlist_id: int
    device_ids: Optional[List[int]] = Field(None, description="Target device IDs")

    start_date: date
    end_date: Optional[date]
    start_time: Optional[time]
    end_time: Optional[time]

    recurrence_type: Optional[str]
    recurrence_pattern: Optional[Dict[str, Any]]
    exception_dates: Optional[List[str]] = Field(None, validation_alias="exceptions")  # Map from DB column

    priority: int
    is_active: bool

    created_at: datetime
    updated_at: datetime

    # Audit trail fields (Migration 046)
    created_by_id: Optional[int] = Field(None, description="User who created this schedule")
    updated_by_id: Optional[int] = Field(None, description="User who last updated this schedule")

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow both field name and alias


class ScheduleListResponse(BaseModel):
    """List of schedules response"""
    schedules: List[ScheduleResponse]
    total: int


# ============================================================================
# Schedule Query DTOs
# ============================================================================

class ActiveScheduleRequest(BaseModel):
    """Request to get active schedule at specific time"""
    check_date: Optional[date] = Field(None, description="Date to check (default: today)")
    check_time: Optional[time] = Field(None, description="Time to check (default: now)")

    class Config:
        json_schema_extra = {
            "example": {
                "check_date": "2025-01-13",
                "check_time": "09:30:00"
            }
        }


class ActiveScheduleResponse(BaseModel):
    """Active schedule response"""
    schedule: Optional[ScheduleResponse]
    playlist_id: Optional[int]
    schedule_name: Optional[str]
    priority: Optional[int]
    is_found: bool

    class Config:
        json_schema_extra = {
            "example": {
                "schedule": {"id": 1, "name": "Morning Schedule"},
                "playlist_id": 5,
                "schedule_name": "Weekday Morning",
                "priority": 10,
                "is_found": True
            }
        }


# ============================================================================
# Recurrence Calculation DTOs
# ============================================================================

class CalculateNextOccurrenceRequest(BaseModel):
    """Request to calculate next occurrence"""
    from_date: Optional[date] = Field(None, description="Calculate from date (default: today)")

    class Config:
        json_schema_extra = {
            "example": {
                "from_date": "2025-01-13"
            }
        }


class NextOccurrence(BaseModel):
    """Next occurrence info"""
    date: date
    start_time: Optional[time]
    end_time: Optional[time]
    is_exception: bool


class CalculateNextOccurrenceResponse(BaseModel):
    """Next occurrence response"""
    schedule_id: int
    schedule_name: str
    next_occurrence: Optional[NextOccurrence]
    occurrences: List[NextOccurrence] = Field(default_factory=list, description="Next 10 occurrences")

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": 1,
                "schedule_name": "Weekday Morning",
                "next_occurrence": {
                    "date": "2025-01-13",
                    "start_time": "07:00:00",
                    "end_time": "10:00:00",
                    "is_exception": False
                },
                "occurrences": []
            }
        }


# ============================================================================
# Schedule Validation DTOs
# ============================================================================

class ValidateScheduleRequest(BaseModel):
    """Request to validate schedule configuration"""
    start_date: date
    end_date: Optional[date]
    start_time: Optional[time]
    end_time: Optional[time]
    recurrence_type: str
    recurrence_pattern: Optional[RecurrencePattern]


class ValidateScheduleResponse(BaseModel):
    """Schedule validation response"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ============================================================================
# Schedule Conflict DTOs
# ============================================================================

class CheckConflictRequest(BaseModel):
    """Request to check schedule conflicts"""
    playlist_id: int
    start_date: date
    end_date: Optional[date]
    start_time: Optional[time]
    end_time: Optional[time]
    recurrence_type: str
    exclude_schedule_id: Optional[int] = Field(None, description="Exclude this schedule from check")


class ConflictSchedule(BaseModel):
    """Conflicting schedule info"""
    id: int
    name: str
    priority: int
    start_date: date
    end_date: Optional[date]
    start_time: Optional[time]
    end_time: Optional[time]


class CheckConflictResponse(BaseModel):
    """Schedule conflict response"""
    has_conflicts: bool
    conflicts: List[ConflictSchedule] = Field(default_factory=list)
    message: str
