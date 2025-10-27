"""
Activity Logs API endpoints
System activity and audit logging management
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException, InternalServerException
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response, paginated_response
from app.models.user import User
from app.models.activity_log import ActivityLog, ActivityAction, EntityType
from app.schemas.activity_log import (
    ActivityLogCreate,
    ActivityLogResponse,
    ActivityLogListResponse,
    ActivityStatsResponse
)
from app.utils.activity_logger import log_activity

# Create structured logger
logger = StructuredLogger(__name__)

router = APIRouter()


def activity_to_response(activity: ActivityLog, db: Session) -> ActivityLogResponse:
    """
    Transform ActivityLog model to ActivityLogResponse with user info

    Args:
        activity: ActivityLog model instance
        db: Database session for querying relationships

    Returns:
        ActivityLogResponse with populated user info
    """
    # Get user info if user_id exists
    user_info = None
    if activity.user_id:
        user = db.query(User).filter(User.id == activity.user_id).first()
        if user:
            user_info = {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }

    return ActivityLogResponse(
        id=activity.id,
        timestamp=activity.timestamp,
        user_id=activity.user_id,
        action_type=activity.action_type,
        entity_type=activity.entity_type,
        entity_id=activity.entity_id,
        entity_name=activity.entity_name,
        details=activity.details,
        ip_address=activity.ip_address,
        user_agent=activity.user_agent,
        created_at=activity.created_at,
        user=user_info
    )


@router.get("/activities", response_model=ActivityLogListResponse)
async def list_activities(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of activity logs with filtering

    Query Parameters:
        - skip: Number of records to skip (pagination)
        - limit: Maximum number of records to return (1-500)
        - action_type: Filter by action type (e.g., DEVICE_APPROVED)
        - entity_type: Filter by entity type (e.g., device, content)
        - entity_id: Filter by specific entity ID
        - user_id: Filter by user who performed the action
        - start_date: Filter activities from this date onwards
        - end_date: Filter activities up to this date

    Returns:
        ActivityLogListResponse with total count and items
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing activity logs",
        request_id=request_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters={
            "action_type": action_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    )

    try:
        # Validate limit
        if limit > 500:
            limit = 500
        if limit < 1:
            limit = 50

        # Build query with filters
        query = db.query(ActivityLog)

        # Apply filters
        if action_type:
            query = query.filter(ActivityLog.action_type == action_type)
        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(ActivityLog.entity_id == entity_id)
        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if start_date:
            query = query.filter(ActivityLog.timestamp >= start_date)
        if end_date:
            query = query.filter(ActivityLog.timestamp <= end_date)

        # Get total count
        total = query.count()

        # Get paginated results, ordered by timestamp descending
        activities = query.order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()

        # Transform to response models
        items = [activity_to_response(activity, db) for activity in activities]

        logger.info(
            "Activity logs retrieved successfully",
            request_id=request_id,
            total=total,
            returned_count=len(items)
        )

        return ActivityLogListResponse(
            total=total,
            items=items
        )

    except Exception as e:
        logger.error(
            "Failed to retrieve activity logs",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to retrieve activity logs",
            details={"error": str(e)}
        )


@router.get("/activities/stats", response_model=ActivityStatsResponse)
async def get_activity_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get activity statistics

    Returns:
        ActivityStatsResponse with counts for today, this week, this month,
        and breakdowns by action type and entity type
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching activity statistics",
        request_id=request_id,
        user_id=current_user.id
    )

    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Count activities for different time periods
        today_count = db.query(func.count(ActivityLog.id)).filter(
            ActivityLog.timestamp >= today_start
        ).scalar()

        week_count = db.query(func.count(ActivityLog.id)).filter(
            ActivityLog.timestamp >= week_start
        ).scalar()

        month_count = db.query(func.count(ActivityLog.id)).filter(
            ActivityLog.timestamp >= month_start
        ).scalar()

        # Group by action type
        action_type_counts = db.query(
            ActivityLog.action_type,
            func.count(ActivityLog.id).label('count')
        ).group_by(ActivityLog.action_type).all()

        by_type = {action: count for action, count in action_type_counts}

        # Group by entity type
        entity_type_counts = db.query(
            ActivityLog.entity_type,
            func.count(ActivityLog.id).label('count')
        ).group_by(ActivityLog.entity_type).all()

        by_entity = {entity: count for entity, count in entity_type_counts}

        logger.info(
            "Activity statistics retrieved successfully",
            request_id=request_id,
            today=today_count,
            this_week=week_count,
            this_month=month_count,
            action_types_count=len(by_type),
            entity_types_count=len(by_entity)
        )

        return ActivityStatsResponse(
            today=today_count,
            this_week=week_count,
            this_month=month_count,
            by_type=by_type,
            by_entity=by_entity
        )

    except Exception as e:
        logger.error(
            "Failed to retrieve activity statistics",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to retrieve activity statistics",
            details={"error": str(e)}
        )


@router.get("/activities/{activity_id}", response_model=ActivityLogResponse)
async def get_activity(
    activity_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a single activity log by ID

    Args:
        activity_id: ID of the activity log to retrieve

    Returns:
        ActivityLogResponse with user info populated
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching activity log",
        request_id=request_id,
        activity_id=activity_id,
        user_id=current_user.id
    )

    try:
        activity = db.query(ActivityLog).filter(ActivityLog.id == activity_id).first()

        if not activity:
            logger.warning(
                "Activity log not found",
                request_id=request_id,
                activity_id=activity_id
            )
            raise NotFoundException(
                message=f"Activity log with ID {activity_id} not found",
                resource_type="ActivityLog",
                resource_id=activity_id
            )

        logger.info(
            "Activity log retrieved successfully",
            request_id=request_id,
            activity_id=activity_id,
            action_type=activity.action_type
        )

        return activity_to_response(activity, db)

    except NotFoundException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve activity log",
            request_id=request_id,
            activity_id=activity_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to retrieve activity log",
            details={"error": str(e)}
        )


@router.post("/activities", response_model=ActivityLogResponse, status_code=status.HTTP_201_CREATED)
async def create_activity_log(
    activity_data: ActivityLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new activity log entry (for manual logging or external integrations)

    Note: Most activity logging should be done automatically via the activity_logger utility.
    This endpoint is primarily for external integrations or manual logging needs.

    Args:
        activity_data: Activity log data to create

    Returns:
        Created ActivityLogResponse
    """
    request_id = get_request_id(request)

    logger.info(
        "Creating activity log",
        request_id=request_id,
        user_id=current_user.id,
        action_type=activity_data.action_type,
        entity_type=activity_data.entity_type
    )

    try:
        # Auto-populate user_id from current user if not provided
        user_id = activity_data.user_id if activity_data.user_id else current_user.id

        # Auto-populate IP address if not provided
        ip_address = activity_data.ip_address
        if not ip_address and request.client:
            ip_address = request.client.host

        # Auto-populate user agent if not provided
        user_agent = activity_data.user_agent
        if not user_agent:
            user_agent = request.headers.get("user-agent")

        # Use the activity_logger utility for consistency
        activity = log_activity(
            db=db,
            action_type=activity_data.action_type,
            entity_type=activity_data.entity_type,
            entity_id=activity_data.entity_id,
            entity_name=activity_data.entity_name,
            details=activity_data.details,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not activity:
            logger.error(
                "Failed to create activity log - log_activity returned None",
                request_id=request_id,
                action_type=activity_data.action_type
            )
            raise InternalServerException(
                message="Failed to create activity log"
            )

        logger.info(
            "Activity log created successfully",
            request_id=request_id,
            activity_id=activity.id,
            action_type=activity.action_type,
            created_by=user_id
        )

        return activity_to_response(activity, db)

    except InternalServerException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create activity log",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to create activity log",
            details={"error": str(e)}
        )


@router.delete("/activities/cleanup")
async def cleanup_old_activities(
    request: Request,
    retention_days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete activity logs older than specified retention period

    Query Parameters:
        - retention_days: Number of days to retain (default: 90)

    Returns:
        Success message with count of deleted records

    Note: This is a maintenance endpoint and should be called periodically
    (e.g., via cron job or scheduled task)
    """
    request_id = get_request_id(request)

    logger.info(
        "Starting activity logs cleanup",
        request_id=request_id,
        user_id=current_user.id,
        retention_days=retention_days
    )

    try:
        # Validate retention days
        if retention_days < 1:
            logger.warning(
                "Invalid retention days parameter",
                request_id=request_id,
                retention_days=retention_days
            )
            raise BadRequestException(
                message="Retention days must be at least 1",
                details={"retention_days": retention_days, "minimum": 1}
            )

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Delete old activities
        deleted_count = db.query(ActivityLog).filter(
            ActivityLog.timestamp < cutoff_date
        ).delete(synchronize_session=False)

        db.commit()

        # Log the cleanup action
        log_activity(
            db=db,
            action_type=ActivityAction.SETTINGS_CHANGED,
            entity_type=EntityType.SYSTEM,
            entity_name="Activity Logs Cleanup",
            details={
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "deleted_count": deleted_count
            },
            user=current_user
        )

        logger.info(
            "Activity logs cleanup completed successfully",
            request_id=request_id,
            deleted_count=deleted_count,
            retention_days=retention_days,
            cutoff_date=cutoff_date.isoformat()
        )

        return success_response(
            data={
                "message": f"Deleted {deleted_count} activity logs older than {retention_days} days",
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat()
            },
            request_id=request_id
        )

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(
            "Failed to cleanup activity logs",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        db.rollback()
        raise InternalServerException(
            message="Failed to cleanup activity logs",
            details={"error": str(e)}
        )
