"""
Schedules API Endpoints
Content scheduling management with Quick Wins standards

MIGRATED TO QUICK WINS STANDARDS:
- Structured logging with StructuredLogger
- Custom exceptions (NotFoundException, BadRequestException)
- Standardized success_response wrapper
- Request ID tracking
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.core.cache import invalidate_by_prefix, CACHE_KEY_PREFIXES
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response
from app.models.user import User
from app.models.schedule import Schedule
from app.models.device import Device
from app.models.content import Content
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleListResponse,
    ScheduleDeleteResponse
)

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/schedules", tags=["schedules"])


# =============================================================================
# SCHEDULE CRUD ENDPOINTS
# =============================================================================

@router.get("")
def list_schedules(
    request: Request,
    device_id: Optional[int] = None,
    content_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all schedules with optional filters

    Query Parameters:
        device_id: Filter by device ID
        content_id: Filter by content ID
        is_active: Filter by active status

    Returns:
        List of schedules matching the filters
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing schedules",
        request_id=request_id,
        filters={
            "device_id": device_id,
            "content_id": content_id,
            "is_active": is_active
        }
    )

    # Build query
    query = db.query(Schedule)

    if device_id is not None:
        query = query.filter(Schedule.device_id == device_id)

    if content_id is not None:
        query = query.filter(Schedule.content_id == content_id)

    if is_active is not None:
        query = query.filter(Schedule.is_active == is_active)

    schedules = query.order_by(Schedule.priority.desc(), Schedule.created_at.desc()).all()

    # Convert to response models
    schedule_responses = [ScheduleResponse(**schedule.to_dict()) for schedule in schedules]

    logger.info(
        "Schedules listed successfully",
        request_id=request_id,
        total_schedules=len(schedule_responses)
    )

    return success_response(
        data={
            "total": len(schedule_responses),
            "items": [s.model_dump() for s in schedule_responses]
        },
        request_id=request_id
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_schedule(
    schedule_data: ScheduleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Create a new schedule

    Request body:
        {
            "schedule_name": "Morning News",
            "device_id": 123,
            "content_id": 456,
            "day_of_week": "0,1,2,3,4",
            "start_time": "08:00:00",
            "end_time": "17:00:00",
            "start_date": "2025-01-01T00:00:00Z",
            "end_date": null,
            "is_active": true,
            "priority": 100,
            "notes": "Display during business hours"
        }
    """
    request_id = get_request_id(request)

    logger.info(
        "Creating new schedule",
        request_id=request_id,
        schedule_name=schedule_data.schedule_name,
        device_id=schedule_data.device_id,
        content_id=schedule_data.content_id
    )

    # Validate device exists (if specified)
    if schedule_data.device_id:
        device = db.query(Device).filter(Device.id == schedule_data.device_id).first()
        if not device:
            raise NotFoundException(
                message=f"Device with ID {schedule_data.device_id} not found",
                resource_type="Device",
                resource_id=schedule_data.device_id
            )

    # Validate content exists
    content = db.query(Content).filter(Content.id == schedule_data.content_id).first()
    if not content:
        raise NotFoundException(
            message=f"Content with ID {schedule_data.content_id} not found",
            resource_type="Content",
            resource_id=schedule_data.content_id
        )

    # Create schedule
    schedule = Schedule(
        schedule_name=schedule_data.schedule_name,
        device_id=schedule_data.device_id,
        content_id=schedule_data.content_id,
        day_of_week=schedule_data.day_of_week,
        start_time=schedule_data.start_time,
        end_time=schedule_data.end_time,
        start_date=schedule_data.start_date,
        end_date=schedule_data.end_date,
        is_active=schedule_data.is_active,
        priority=schedule_data.priority,
        notes=schedule_data.notes
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    # Invalidate schedule cache
    invalidate_by_prefix("schedule_list")

    logger.info(
        "Schedule created successfully",
        request_id=request_id,
        schedule_id=schedule.id,
        schedule_name=schedule.schedule_name
    )

    return success_response(
        data=schedule.to_dict(),
        request_id=request_id
    )


@router.get("/{schedule_id}")
def get_schedule(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a single schedule by ID

    Returns:
        Schedule details including timestamps
    """
    request_id = get_request_id(request)

    logger.info(
        "Retrieving schedule",
        request_id=request_id,
        schedule_id=schedule_id
    )

    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        logger.warning(
            "Schedule not found",
            request_id=request_id,
            schedule_id=schedule_id
        )
        raise NotFoundException(
            message=f"Schedule with ID {schedule_id} not found",
            resource_type="Schedule",
            resource_id=schedule_id
        )

    logger.info(
        "Schedule retrieved successfully",
        request_id=request_id,
        schedule_id=schedule.id,
        schedule_name=schedule.schedule_name
    )

    return success_response(
        data=schedule.to_dict(),
        request_id=request_id
    )


@router.put("/{schedule_id}")
def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update an existing schedule

    Request body (all fields optional):
        {
            "schedule_name": "Updated Name",
            "is_active": false,
            "priority": 150
        }
    """
    request_id = get_request_id(request)

    logger.info(
        "Updating schedule",
        request_id=request_id,
        schedule_id=schedule_id,
        update_fields=list(schedule_data.model_dump(exclude_unset=True).keys())
    )

    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        logger.warning(
            "Schedule not found for update",
            request_id=request_id,
            schedule_id=schedule_id
        )
        raise NotFoundException(
            message=f"Schedule with ID {schedule_id} not found",
            resource_type="Schedule",
            resource_id=schedule_id
        )

    # Update fields
    update_data = schedule_data.model_dump(exclude_unset=True)

    # Validate device_id if being updated
    if 'device_id' in update_data and update_data['device_id'] is not None:
        device = db.query(Device).filter(Device.id == update_data['device_id']).first()
        if not device:
            raise NotFoundException(
                message=f"Device with ID {update_data['device_id']} not found",
                resource_type="Device",
                resource_id=update_data['device_id']
            )

    # Validate content_id if being updated
    if 'content_id' in update_data:
        content = db.query(Content).filter(Content.id == update_data['content_id']).first()
        if not content:
            raise NotFoundException(
                message=f"Content with ID {update_data['content_id']} not found",
                resource_type="Content",
                resource_id=update_data['content_id']
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)

    # Invalidate cache
    invalidate_by_prefix("schedule_list")

    logger.info(
        "Schedule updated successfully",
        request_id=request_id,
        schedule_id=schedule.id,
        schedule_name=schedule.schedule_name
    )

    return success_response(
        data=schedule.to_dict(),
        request_id=request_id
    )


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete a schedule

    Returns:
        Confirmation message with deleted schedule ID
    """
    request_id = get_request_id(request)

    logger.info(
        "Deleting schedule",
        request_id=request_id,
        schedule_id=schedule_id
    )

    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        logger.warning(
            "Schedule not found for deletion",
            request_id=request_id,
            schedule_id=schedule_id
        )
        raise NotFoundException(
            message=f"Schedule with ID {schedule_id} not found",
            resource_type="Schedule",
            resource_id=schedule_id
        )

    schedule_name = schedule.schedule_name
    db.delete(schedule)
    db.commit()

    # Invalidate cache
    invalidate_by_prefix("schedule_list")

    logger.info(
        "Schedule deleted successfully",
        request_id=request_id,
        schedule_id=schedule_id,
        schedule_name=schedule_name
    )

    return success_response(
        data={
            "message": f"Schedule '{schedule_name}' deleted successfully",
            "deleted_id": schedule_id
        },
        request_id=request_id
    )
