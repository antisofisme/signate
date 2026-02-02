"""
Get Workflow Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IWorkflowRepository


class GetWorkflowUseCase:
    def __init__(self, repository: IWorkflowRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, workflow_id: UUID) -> Optional[dict]:
        wf = await self._repository.get_workflow(tenant_id, workflow_id)
        if not wf:
            return None

        return {
            "id": str(wf.id),
            "decision_id": str(wf.decision_id),
            "current_state": wf.current_state.value,
            "approver_role": wf.approver_role,
            "delegated_to_user_id": str(wf.delegated_to_user_id) if wf.delegated_to_user_id else None,
            "escalated_to_user_id": str(wf.escalated_to_user_id) if wf.escalated_to_user_id else None,
            "escalation_timeout_at": wf.escalation_timeout_at.isoformat() if wf.escalation_timeout_at else None,
            "is_pending": wf.is_pending(),
            "is_terminal": wf.is_terminal(),
            "can_approve": wf.can_approve(),
            "can_reject": wf.can_reject(),
            "can_delegate": wf.can_delegate(),
            "can_escalate": wf.can_escalate(),
            "created_at": wf.created_at.isoformat() if wf.created_at else None,
            "completed_at": wf.completed_at.isoformat() if wf.completed_at else None,
            "metadata": wf.metadata,
        }

    async def get_transitions(self, tenant_id: UUID, workflow_id: UUID) -> list:
        return await self._repository.get_workflow_transitions(tenant_id, workflow_id)
