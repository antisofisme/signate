"""
Activity Logger Utility
Helper function for logging system activities
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.activity_log import ActivityLog, ActivityAction, EntityType
from app.models.user import User
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


def log_activity(
    db: Session,
    action_type: ActivityAction,
    entity_type: EntityType,
    entity_id: Optional[int] = None,
    entity_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    user: Optional[User] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[ActivityLog]:
    """
    Log an activity to the database

    Args:
        db: Database session
        action_type: Type of action performed
        entity_type: Type of entity affected
        entity_id: ID of the entity (optional)
        entity_name: Name of the entity (optional)
        details: Additional details as JSON (optional)
        user_id: ID of user who performed action (optional)
        user: User object who performed action (optional)
        ip_address: IP address of the request (optional)
        user_agent: User agent of the request (optional)

    Returns:
        ActivityLog object if successful, None otherwise
    """
    try:
        # Get user_id from user object if provided
        if user and not user_id:
            user_id = user.id

        # Create activity log entry
        activity = ActivityLog(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details or {},
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )

        db.add(activity)
        db.commit()
        db.refresh(activity)

        logger.info(
            f"Activity logged: {action_type.value} on {entity_type.value}",
            action_type=action_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            user_id=user_id
        )

        return activity

    except Exception as e:
        logger.error(
            f"Failed to log activity: {e}",
            action_type=action_type.value if action_type else None,
            entity_type=entity_type.value if entity_type else None,
            error=str(e)
        )
        db.rollback()
        return None
