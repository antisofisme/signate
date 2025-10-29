"""
Schedule Schemas
Pydantic models for content scheduling validation and serialization
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime, time
from typing import Optional, List


class ScheduleBase(BaseModel):
    """Base schedule schema with common fields"""
    schedule_name: str = Field(..., min_length=1, max_length=100, description="Name of the schedule")
    device_id: Optional[int] = Field(None, description="Device ID (optional, can be tag-based)")
    content_id: int = Field(..., description="Content ID to schedule")
    day_of_week: Optional[str] = Field(None, description="Days of week (0=Mon, 6=Sun, comma-separated, e.g. '0,1,2,3,4')")
    start_time: Optional[time] = Field(None, description="Time to start showing content")
    end_time: Optional[time] = Field(None, description="Time to stop showing content")
    start_date: Optional[datetime] = Field(None, description="Date to start this schedule")
    end_date: Optional[datetime] = Field(None, description="Date to end this schedule (optional)")
    is_active: bool = Field(True, description="Whether this schedule is active")
    priority: int = Field(100, ge=1, le=1000, description="Schedule priority (1-1000)")
    notes: Optional[str] = Field(None, max_length=1000, description="Admin notes about schedule")

    @field_validator('day_of_week')
    @classmethod
    def validate_day_of_week(cls, v):
        """Validate day_of_week format"""
        if v is None:
            return v

        # Check format: comma-separated numbers 0-6
        try:
            days = [int(d.strip()) for d in v.split(',')]
            if not all(0 <= day <= 6 for day in days):
                raise ValueError("Days must be between 0 (Monday) and 6 (Sunday)")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid day_of_week format: {str(e)}")

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        """Validate end_time is after start_time"""
        start_time = info.data.get('start_time')
        if v and start_time and v <= start_time:
            raise ValueError("end_time must be after start_time")
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Validate end_date is after start_date"""
        start_date = info.data.get('start_date')
        if v and start_date and v <= start_date:
            raise ValueError("end_date must be after start_date")
        return v


class ScheduleCreate(ScheduleBase):
    """Schema for creating a new schedule"""
    pass


class ScheduleUpdate(BaseModel):
    """Schema for updating an existing schedule (all fields optional)"""
    schedule_name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_id: Optional[int] = None
    content_id: Optional[int] = None
    day_of_week: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('day_of_week')
    @classmethod
    def validate_day_of_week(cls, v):
        """Validate day_of_week format"""
        if v is None:
            return v

        try:
            days = [int(d.strip()) for d in v.split(',')]
            if not all(0 <= day <= 6 for day in days):
                raise ValueError("Days must be between 0 (Monday) and 6 (Sunday)")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid day_of_week format: {str(e)}")


class ScheduleResponse(ScheduleBase):
    """Schema for schedule responses"""
    id: int = Field(..., description="Schedule ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    """Schema for paginated schedule list"""
    total: int = Field(..., description="Total number of schedules")
    items: List[ScheduleResponse] = Field(..., description="List of schedules")


class ScheduleDeleteResponse(BaseModel):
    """Schema for schedule deletion response"""
    message: str = Field(..., description="Deletion confirmation message")
    deleted_id: int = Field(..., description="ID of deleted schedule")
