"""
EscalateWorkflowUseCase

Orchestrates workflow escalation.
Source: INFRA-LAY3-002 §3.3 (Delegation & Escalation Standards)
"""

from ..domain import TenantId, WorkflowId
from .interfaces import IUnitOfWork, IWorkflowRepository
from .dtos import EscalateWorkflowInput, EscalateWorkflowOutput
from .exceptions import WorkflowNotFoundError, TenantIsolationViolationError


class EscalateWorkflowUseCase:
    """
    Use case: Escalate workflow
    Source: INFRA-LAY3-002 §3.3
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        workflow_repository: IWorkflowRepository
    ):
        self._uow = uow
        self._workflow_repo = workflow_repository

    async def execute(self, input_dto: EscalateWorkflowInput) -> EscalateWorkflowOutput:
        """
        Execute workflow escalation
        """
        tenant_id = TenantId(input_dto.tenant_id)
        workflow_id = WorkflowId(input_dto.workflow_id)

        async with self._uow:
            workflow = await self._workflow_repo.find_by_id(workflow_id, tenant_id)

            if not workflow:
                raise WorkflowNotFoundError(workflow_id.value)

            if workflow.tenant_id.value != tenant_id.value:
                raise TenantIsolationViolationError()

            workflow.escalate(
                escalated_to_role=input_dto.escalated_to_role,
                escalation_reason=input_dto.escalation_reason
            )

            await self._workflow_repo.save(workflow)

            events = workflow.collect_events()

            await self._uow.commit()

        return EscalateWorkflowOutput(
            workflow_id=workflow.workflow_id.value,
            current_state=workflow.current_state.value,
            escalated_to_role=input_dto.escalated_to_role,
            events=events
        )
