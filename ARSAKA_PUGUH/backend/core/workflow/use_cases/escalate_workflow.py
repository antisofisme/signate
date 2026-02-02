"""
Escalate Workflow Use Case
"""

from uuid import UUID

from ..interfaces import IWorkflowRepository


class EscalateWorkflowUseCase:
    def __init__(self, repository: IWorkflowRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
        escalate_to: UUID,
        reason: str,
        idempotency_key: str = None,
    ) -> dict:
        # Check idempotency - return cached result if this key was already processed
        if idempotency_key:
            cached = await self._repository.check_idempotency(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                idempotency_key=idempotency_key,
            )
            if cached:
                return cached

        wf = await self._repository.escalate_workflow(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            user_id=user_id,
            escalate_to=escalate_to,
            reason=reason,
        )

        result = {
            "id": str(wf.id),
            "current_state": wf.current_state.value,
            "escalated_to_user_id": str(wf.escalated_to_user_id),
            "message": "Workflow escalated",
        }

        # Store idempotency result for future deduplication
        if idempotency_key:
            await self._repository.store_idempotency(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                idempotency_key=idempotency_key,
                result=result,
            )

        return result
