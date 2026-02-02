"""
DelegateWorkflowUseCase

Orchestrates workflow delegation.
Source: INFRA-LAY3-002 §3.3 (Delegation & Escalation Standards)
"""

from ..domain import TenantId, WorkflowId
from .interfaces import IUnitOfWork, IWorkflowRepository
from .dtos import DelegateWorkflowInput, DelegateWorkflowOutput
from .exceptions import WorkflowNotFoundError, TenantIsolationViolationError


class DelegateWorkflowUseCase:
    """
    Use case: Delegate workflow
    Source: INFRA-LAY3-002 §3.3
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        workflow_repository: IWorkflowRepository
    ):
        self._uow = uow
        self._workflow_repo = workflow_repository

    async def execute(self, input_dto: DelegateWorkflowInput) -> DelegateWorkflowOutput:
        """
        Execute workflow delegation
        """
        tenant_id = TenantId(input_dto.tenant_id)
        workflow_id = WorkflowId(input_dto.workflow_id)

        async with self._uow:
            workflow = await self._workflow_repo.find_by_id(workflow_id, tenant_id)

            if not workflow:
                raise WorkflowNotFoundError(workflow_id.value)

            if workflow.tenant_id.value != tenant_id.value:
                raise TenantIsolationViolationError()

            workflow.delegate(
                approver_role=input_dto.approver_role,
                delegated_to_user_id=input_dto.delegated_to_user_id,
                acted_by_user_id=input_dto.acted_by_user_id,
                reason=input_dto.reason
            )

            await self._workflow_repo.save(workflow)

            events = workflow.collect_events()

            await self._uow.commit()

        return DelegateWorkflowOutput(
            workflow_id=workflow.workflow_id.value,
            current_state=workflow.current_state.value,
            delegated_to_user_id=input_dto.delegated_to_user_id,
            events=events
        )
