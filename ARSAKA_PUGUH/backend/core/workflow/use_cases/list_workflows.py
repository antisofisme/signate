"""
List Workflows Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IWorkflowRepository
from ..domain import WorkflowStatus


class ListWorkflowsUseCase:
    def __init__(self, repository: IWorkflowRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        assignee_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        wf_status = WorkflowStatus(status) if status else None

        workflows, total = await self._repository.list_workflows(
            tenant_id=tenant_id,
            assignee_id=assignee_id,
            status=wf_status,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                {
                    "id": str(wf.id),
                    "decision_id": str(wf.decision_id),
                    "current_state": wf.current_state.value,
                    "approver_role": wf.approver_role,
                    "is_pending": wf.is_pending(),
                    "is_terminal": wf.is_terminal(),
                    "created_at": wf.created_at.isoformat() if wf.created_at else None,
                    "completed_at": wf.completed_at.isoformat() if wf.completed_at else None,
                }
                for wf in workflows
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0,
        }

    async def get_stats(self, tenant_id: UUID) -> dict:
        """Get workflow statistics for tenant."""
        return await self._repository.get_stats(tenant_id=tenant_id)
