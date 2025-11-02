"""
Activity Repository - Database Access untuk Activity Logging
===========================================================

CENTRALIZED QUERIES untuk activity_logs table
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.repositories.base import BaseRepository
from app.models.activity_log import ActivityLog, ActivityAction, EntityType


class ActivityRepository(BaseRepository):
    """
    Activity Repository untuk activity logging

    Handles:
    - Activity log creation
    - Activity queries by user/organization/entity
    - Activity statistics
    - Audit trails
    """

    def __init__(self, db: Session):
        super().__init__(ActivityLog, db)
        self.db = db

    # =========================================================================
    # ACTIVITY-SPECIFIC QUERIES
    # =========================================================================

    def log_activity(
        self,
        user_id: int,
        organization_id: int,
        action: ActivityAction,
        entity_type: EntityType,
        entity_id: int,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """
        Log an activity

        Example:
            activity_repo.log_activity(
                user_id=1,
                organization_id=1,
                action=ActivityAction.CREATE,
                entity_type=EntityType.DEVICE,
                entity_id=123,
                details={"device_name": "TV-001"}
            )
        """
        activity = ActivityLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            timestamp=datetime.utcnow()
        )

        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)

        return activity

    def get_user_activities(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[ActivityLog]:
        """
        Get recent activities by a user

        Example:
            activities = activity_repo.get_user_activities(user_id=1, limit=50)
        """
        return self.db.query(self.model).filter(
            self.model.user_id == user_id
        ).order_by(desc(self.model.timestamp)).limit(limit).all()

    def get_organization_activities(
        self,
        organization_id: int,
        limit: int = 100
    ) -> List[ActivityLog]:
        """
        Get recent activities in an organization

        Example:
            activities = activity_repo.get_organization_activities(org_id=1)
        """
        return self.db.query(self.model).filter(
            self.model.organization_id == organization_id
        ).order_by(desc(self.model.timestamp)).limit(limit).all()

    def get_entity_activities(
        self,
        entity_type: EntityType,
        entity_id: int,
        limit: int = 50
    ) -> List[ActivityLog]:
        """
        Get activities related to a specific entity

        Example:
            # Get all activities for device 123
            activities = activity_repo.get_entity_activities(
                entity_type=EntityType.DEVICE,
                entity_id=123
            )
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.entity_type == entity_type,
                self.model.entity_id == entity_id
            )
        ).order_by(desc(self.model.timestamp)).limit(limit).all()

    def get_recent_activities(
        self,
        organization_id: int,
        hours: int = 24,
        limit: int = 100
    ) -> List[ActivityLog]:
        """
        Get activities from the last N hours

        Example:
            # Get activities from last 24 hours
            activities = activity_repo.get_recent_activities(org_id=1, hours=24)
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        return self.db.query(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.timestamp >= since
            )
        ).order_by(desc(self.model.timestamp)).limit(limit).all()

    def get_activity_stats(
        self,
        organization_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get activity statistics for the last N days

        Returns:
            {
                "total_activities": 150,
                "by_action": {"CREATE": 50, "UPDATE": 70, "DELETE": 30},
                "by_entity_type": {"DEVICE": 80, "CONTENT": 70},
                "top_users": [(user_id, count), ...]
            }
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Total activities
        total = self.db.query(func.count(self.model.id)).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.timestamp >= since
            )
        ).scalar() or 0

        # By action
        by_action = {}
        action_counts = self.db.query(
            self.model.action,
            func.count(self.model.id)
        ).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.timestamp >= since
            )
        ).group_by(self.model.action).all()

        for action, count in action_counts:
            by_action[action.value if hasattr(action, 'value') else str(action)] = count

        # By entity type
        by_entity = {}
        entity_counts = self.db.query(
            self.model.entity_type,
            func.count(self.model.id)
        ).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.timestamp >= since
            )
        ).group_by(self.model.entity_type).all()

        for entity_type, count in entity_counts:
            by_entity[entity_type.value if hasattr(entity_type, 'value') else str(entity_type)] = count

        # Top users
        top_users = self.db.query(
            self.model.user_id,
            func.count(self.model.id)
        ).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.timestamp >= since
            )
        ).group_by(self.model.user_id).order_by(
            desc(func.count(self.model.id))
        ).limit(10).all()

        return {
            "total_activities": total,
            "by_action": by_action,
            "by_entity_type": by_entity,
            "top_users": [(user_id, count) for user_id, count in top_users]
        }
