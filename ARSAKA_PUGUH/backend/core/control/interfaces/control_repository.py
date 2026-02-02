"""
Control Repository Interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain import AuditRecord, SystemEvent


class IControlRepository(ABC):
    """Control repository interface."""

    @abstractmethod
    async def list_audit(
        self,
        tenant_id: UUID,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[AuditRecord], int]:
        pass

    @abstractmethod
    async def get_audit(self, tenant_id: UUID, audit_id: UUID) -> Optional[AuditRecord]:
        pass

    @abstractmethod
    async def list_events(
        self,
        tenant_id: UUID,
        event_type: Optional[str] = None,
        aggregate_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[SystemEvent], int]:
        pass

    @abstractmethod
    async def get_event(self, tenant_id: UUID, event_id: UUID) -> Optional[SystemEvent]:
        pass

    @abstractmethod
    async def list_dlq_events(
        self, tenant_id: UUID, page: int = 1, limit: int = 20
    ) -> tuple[List[dict], int]:
        pass

    @abstractmethod
    async def get_metrics(self, tenant_id: UUID) -> dict:
        pass

    @abstractmethod
    async def get_decision_metrics(self, tenant_id: UUID) -> dict:
        pass

    @abstractmethod
    async def get_workflow_metrics(self, tenant_id: UUID) -> dict:
        pass

    @abstractmethod
    async def get_metrics_trends(self, tenant_id: UUID, period: str = "7d") -> List[dict]:
        pass

    @abstractmethod
    async def get_dlq_event(
        self, tenant_id: UUID, dlq_entry_id: UUID
    ) -> Optional[dict]:
        """Get a single DLQ event by its entry ID."""
        pass

    @abstractmethod
    async def retry_dlq_event(
        self, tenant_id: UUID, dlq_entry_id: UUID
    ) -> dict:
        """
        Retry a DLQ event by resetting it for reprocessing.
        Marks the event for republishing and updates reprocessed_at.
        """
        pass
