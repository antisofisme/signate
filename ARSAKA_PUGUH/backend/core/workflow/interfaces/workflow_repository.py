"""
Workflow Repository Interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain import Workflow, WorkflowStatus


class IWorkflowRepository(ABC):
    """Workflow repository interface."""

    @abstractmethod
    async def list_workflows(
        self,
        tenant_id: UUID,
        assignee_id: Optional[UUID] = None,
        status: Optional[WorkflowStatus] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[Workflow], int]:
        pass

    @abstractmethod
    async def get_workflow(self, tenant_id: UUID, workflow_id: UUID) -> Optional[Workflow]:
        pass

    @abstractmethod
    async def get_workflow_transitions(self, tenant_id: UUID, workflow_id: UUID) -> List[dict]:
        pass

    @abstractmethod
    async def approve_workflow(
        self, tenant_id: UUID, workflow_id: UUID, user_id: UUID, comment: Optional[str] = None
    ) -> Workflow:
        pass

    @abstractmethod
    async def reject_workflow(
        self, tenant_id: UUID, workflow_id: UUID, user_id: UUID, reason: str
    ) -> Workflow:
        pass

    @abstractmethod
    async def delegate_workflow(
        self, tenant_id: UUID, workflow_id: UUID, user_id: UUID, delegate_to: UUID, reason: str
    ) -> Workflow:
        pass

    @abstractmethod
    async def escalate_workflow(
        self, tenant_id: UUID, workflow_id: UUID, user_id: UUID, escalate_to: UUID, reason: str
    ) -> Workflow:
        pass

    @abstractmethod
    async def get_stats(self, tenant_id: UUID) -> dict:
        pass

    @abstractmethod
    async def check_idempotency(
        self, tenant_id: UUID, workflow_id: UUID, idempotency_key: str
    ) -> Optional[dict]:
        """
        Check if an action with this idempotency_key was already performed.
        Returns the cached result if found, None otherwise.
        """
        pass

    @abstractmethod
    async def store_idempotency(
        self, tenant_id: UUID, workflow_id: UUID, idempotency_key: str, result: dict
    ) -> None:
        """
        Store idempotency result for future deduplication.
        """
        pass
