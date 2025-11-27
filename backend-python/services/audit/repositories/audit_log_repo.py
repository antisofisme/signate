"""
AuditLog Repository Implementation
Implements IAuditLogRepository using SQLAlchemy
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ..domain.audit_log import AuditLog
from ..domain.interfaces import IAuditLogRepository
from services.auth.repositories.models import AuditLogModel


class AuditLogRepository(IAuditLogRepository):
    """AuditLog repository implementation using SQLAlchemy"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, audit_log: AuditLog) -> AuditLog:
        """Create new audit log entry"""
        audit_log_model = AuditLogModel(
            user_id=audit_log.user_id,
            organization_id=audit_log.organization_id,
            action=audit_log.action,
            resource_type=audit_log.resource_type,
            resource_id=audit_log.resource_id,
            details=audit_log.details,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent
        )

        self.db.add(audit_log_model)
        self.db.commit()
        self.db.refresh(audit_log_model)

        return self._to_entity(audit_log_model)

    def find_by_id(self, log_id: int) -> Optional[AuditLog]:
        """Find audit log by ID"""
        audit_log_model = self.db.query(AuditLogModel).filter(
            AuditLogModel.id == log_id
        ).first()

        return self._to_entity(audit_log_model) if audit_log_model else None

    def get_all(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get all audit logs with filters"""
        query = self.db.query(AuditLogModel)

        # Apply filters
        filters = []

        if user_id is not None:
            filters.append(AuditLogModel.user_id == user_id)

        if organization_id is not None:
            filters.append(AuditLogModel.organization_id == organization_id)

        if action is not None:
            filters.append(AuditLogModel.action == action)

        if resource_type is not None:
            filters.append(AuditLogModel.resource_type == resource_type)

        if resource_id is not None:
            filters.append(AuditLogModel.resource_id == resource_id)

        if start_date is not None:
            filters.append(AuditLogModel.created_at >= start_date)

        if end_date is not None:
            filters.append(AuditLogModel.created_at <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # Order by created_at descending (newest first)
        query = query.order_by(desc(AuditLogModel.created_at))

        # Apply pagination
        query = query.limit(limit).offset(offset)

        audit_logs = query.all()
        return [self._to_entity(log) for log in audit_logs]

    def count(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count audit logs with filters"""
        query = self.db.query(AuditLogModel)

        # Apply filters
        filters = []

        if user_id is not None:
            filters.append(AuditLogModel.user_id == user_id)

        if organization_id is not None:
            filters.append(AuditLogModel.organization_id == organization_id)

        if action is not None:
            filters.append(AuditLogModel.action == action)

        if resource_type is not None:
            filters.append(AuditLogModel.resource_type == resource_type)

        if resource_id is not None:
            filters.append(AuditLogModel.resource_id == resource_id)

        if start_date is not None:
            filters.append(AuditLogModel.created_at >= start_date)

        if end_date is not None:
            filters.append(AuditLogModel.created_at <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        return query.count()

    def get_recent_by_user(self, user_id: int, limit: int = 10) -> List[AuditLog]:
        """Get recent audit logs for a specific user"""
        audit_logs = self.db.query(AuditLogModel).filter(
            AuditLogModel.user_id == user_id
        ).order_by(desc(AuditLogModel.created_at)).limit(limit).all()

        return [self._to_entity(log) for log in audit_logs]

    def get_recent_by_organization(self, organization_id: int, limit: int = 10) -> List[AuditLog]:
        """Get recent audit logs for a specific organization"""
        audit_logs = self.db.query(AuditLogModel).filter(
            AuditLogModel.organization_id == organization_id
        ).order_by(desc(AuditLogModel.created_at)).limit(limit).all()

        return [self._to_entity(log) for log in audit_logs]

    def _to_entity(self, model: AuditLogModel) -> AuditLog:
        """Convert SQLAlchemy model to domain entity"""
        return AuditLog(
            id=model.id,
            user_id=model.user_id,
            organization_id=model.organization_id,
            action=model.action,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            details=model.details,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            created_at=model.created_at
        )
