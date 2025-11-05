"""Create AuditLog Use Case"""

from typing import Optional, Dict, Any
from ..domain.audit_log import AuditLog
from ..domain.interfaces import IAuditLogRepository


class CreateAuditLogUseCase:
    """Use case for creating audit log entry"""

    def __init__(self, audit_log_repo: IAuditLogRepository):
        self.audit_log_repo = audit_log_repo

    def execute(
        self,
        user_id: Optional[int],
        organization_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Create audit log entry

        Args:
            user_id: ID of user who performed action (None for system actions)
            organization_id: ID of organization (None for cross-org actions)
            action: Action performed (e.g., 'user.create', 'org.update')
            resource_type: Type of resource ('user', 'organization', 'device', etc.)
            resource_id: ID of specific resource affected
            details: Additional context as dictionary
            ip_address: IP address of requester
            user_agent: User agent string from request

        Returns:
            Created AuditLog entity

        Raises:
            ValueError: If validation fails
        """

        # Create audit log entity (validates in __post_init__)
        audit_log = AuditLog(
            id=None,
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Save via repository
        return self.audit_log_repo.create(audit_log)
