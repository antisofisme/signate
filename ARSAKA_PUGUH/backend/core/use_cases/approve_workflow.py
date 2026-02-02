"""
ApproveWorkflowUseCase

Orchestrates workflow approval.
Source: INFRA-LAY3-002 §3.2 (Workflow Approval Action Standards)
"""

from ..domain import TenantId, WorkflowId
from .interfaces import IUnitOfWork, IWorkflowRepository
from .dtos import ApproveWorkflowInput, ApproveWorkflowOutput
from .exceptions import WorkflowNotFoundError, TenantIsolationViolationError


class ApproveWorkflowUseCase:
    """
    Use case: Approve workflow
    Source: INFRA-LAY3-002 §3.2
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        workflow_repository: IWorkflowRepository
    ):
        self._uow = uow
        self._workflow_repo = workflow_repository

    async def execute(self, input_dto: ApproveWorkflowInput) -> ApproveWorkflowOutput:
        """
        Execute workflow approval
        """
        tenant_id = TenantId(input_dto.tenant_id)
        workflow_id = WorkflowId(input_dto.workflow_id)

        async with self._uow:
            workflow = await self._workflow_repo.find_by_id(workflow_id, tenant_id)

            if not workflow:
                raise WorkflowNotFoundError(workflow_id.value)

            if workflow.tenant_id.value != tenant_id.value:
                raise TenantIsolationViolationError()

            workflow.approve(
                approver_role=input_dto.approver_role,
                acted_by_user_id=input_dto.acted_by_user_id,
                comment=input_dto.comment
            )

            await self._workflow_repo.save(workflow)

            events = workflow.collect_events()

            await self._uow.commit()

        return ApproveWorkflowOutput(
            workflow_id=workflow.workflow_id.value,
            current_state=workflow.current_state.value,
            completed_at=workflow.completed_at,
            events=events
        )
