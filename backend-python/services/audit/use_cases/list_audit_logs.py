"""List AuditLogs Use Case"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..domain.audit_log import AuditLog
from ..domain.interfaces import IAuditLogRepository


class ListAuditLogsUseCase:
    """Use case for listing audit logs with filters"""

    def __init__(self, audit_log_repo: IAuditLogRepository):
        self.audit_log_repo = audit_log_repo

    def execute(
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
    ) -> Dict[str, Any]:
        """
        List audit logs with filters and pagination

        Args:
            user_id: Filter by user who performed action
            organization_id: Filter by organization
            action: Filter by specific action
            resource_type: Filter by resource type
            resource_id: Filter by specific resource ID
            start_date: Filter from this date
            end_date: Filter until this date
            limit: Maximum results per page (default 100, max 1000)
            offset: Number of results to skip

        Returns:
            Dictionary with:
                - logs: List of AuditLog entities
                - total: Total count matching filters
                - limit: Applied limit
                - offset: Applied offset
        """

        # Validate and cap limit
        if limit > 1000:
            limit = 1000
        if limit < 1:
            limit = 10

        # Get logs from repository
        logs = self.audit_log_repo.get_all(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        # Get total count
        total = self.audit_log_repo.count(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }
