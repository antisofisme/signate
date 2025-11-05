"""
AuditLog Repository Interface
Defines contract for audit log data access
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from .audit_log import AuditLog


class IAuditLogRepository(ABC):
    """AuditLog repository interface"""

    @abstractmethod
    def create(self, audit_log: AuditLog) -> AuditLog:
        """Create new audit log entry"""
        pass

    @abstractmethod
    def find_by_id(self, log_id: int) -> Optional[AuditLog]:
        """Find audit log by ID"""
        pass

    @abstractmethod
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
        """
        Get all audit logs with filters

        Args:
            user_id: Filter by user who performed action
            organization_id: Filter by organization
            action: Filter by specific action (e.g., 'user.create')
            resource_type: Filter by resource type (e.g., 'user', 'organization')
            resource_id: Filter by specific resource ID
            start_date: Filter logs from this date onwards
            end_date: Filter logs up to this date
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (for pagination)

        Returns:
            List of AuditLog entities
        """
        pass

    @abstractmethod
    def count(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count audit logs with filters

        Returns:
            Total number of logs matching filters
        """
        pass

    @abstractmethod
    def get_recent_by_user(self, user_id: int, limit: int = 10) -> List[AuditLog]:
        """Get recent audit logs for a specific user"""
        pass

    @abstractmethod
    def get_recent_by_organization(self, organization_id: int, limit: int = 10) -> List[AuditLog]:
        """Get recent audit logs for a specific organization"""
        pass
