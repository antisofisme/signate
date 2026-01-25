"""
Audit logging interfaces.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any

from ..entities import AuditEntry, AuditLog


class IAuditService(ABC):
    """
    Interface for audit logging service.

    Audit logs are APPEND-ONLY (no updates or deletes).

    Implementations: PostgresAuditService
    """

    @abstractmethod
    async def log(self, entry: AuditEntry) -> str:
        """
        Log an audit entry.

        Args:
            entry: AuditEntry to log

        Returns:
            Entry ID
        """
        pass

    @abstractmethod
    async def log_action(
        self,
        tenant_id: str,
        actor_type: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> str:
        """
        Convenience method to log an action.

        Args:
            tenant_id: Tenant ID
            actor_type: Type of actor (user, api_key, system)
            actor_id: Actor identifier
            action: Action performed
            resource_type: Type of resource affected
            resource_id: Resource identifier
            request_id: Request ID for tracing
            ip_address: Client IP
            details: Additional details
            status: Action status

        Returns:
            Entry ID
        """
        pass

    @abstractmethod
    async def get_logs(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AuditLog:
        """
        Query audit logs.

        Args:
            tenant_id: Tenant ID
            filters: Optional filters (actor_id, action, resource_type, etc.)
            limit: Max entries
            offset: Pagination offset
            start_date: Filter by date range start
            end_date: Filter by date range end

        Returns:
            AuditLog with entries and metadata
        """
        pass

    @abstractmethod
    async def get_user_activity(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[AuditEntry]:
        """
        Get recent activity for a user.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            limit: Max entries

        Returns:
            List of AuditEntry
        """
        pass
