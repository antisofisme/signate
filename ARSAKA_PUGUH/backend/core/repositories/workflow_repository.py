"""
WorkflowRepository Implementation

Persistence adapter for Workflow aggregate.
Source: INFRA-LAY3-002 §3 (Workflow State Machine Standards)
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain import Workflow, WorkflowId, DecisionId, TenantId, WorkflowState, Metadata
from ..use_cases.interfaces import IWorkflowRepository
from .models import WorkflowModel


class WorkflowRepository(IWorkflowRepository):
    """
    Workflow repository implementation
    Maps: Workflow aggregate <-> WorkflowModel
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, workflow: Workflow) -> None:
        """
        Save workflow to database
        Mapping: Workflow aggregate -> WorkflowModel
        """
        stmt = select(WorkflowModel).where(
            WorkflowModel.workflow_id == workflow.workflow_id.value
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        metadata_dict = workflow.metadata.to_dict() if workflow.metadata else {}

        if existing:
            existing.current_state = workflow.current_state.value
            existing.approver_role = workflow.approver_role
            existing.delegated_to_user_id = workflow.delegated_to_user_id
            existing.escalated_to_user_id = workflow.escalated_to_user_id
            existing.completed_at = workflow.completed_at
            existing.metadata = metadata_dict
        else:
            model = WorkflowModel(
                workflow_id=workflow.workflow_id.value,
                decision_id=workflow.decision_id.value,
                tenant_id=workflow.tenant_id.value,
                current_state=workflow.current_state.value,
                approver_role=workflow.approver_role,
                delegated_to_user_id=workflow.delegated_to_user_id,
                escalated_to_user_id=workflow.escalated_to_user_id,
                escalation_timeout_at=None,
                created_at=workflow.created_at,
                completed_at=workflow.completed_at,
                metadata=metadata_dict
            )
            self._session.add(model)

    async def find_by_id(
        self,
        workflow_id: WorkflowId,
        tenant_id: TenantId
    ) -> Optional[Workflow]:
        """
        Find workflow by ID (tenant-scoped)
        Mapping: WorkflowModel -> Workflow aggregate
        """
        stmt = select(WorkflowModel).where(
            WorkflowModel.workflow_id == workflow_id.value,
            WorkflowModel.tenant_id == tenant_id.value
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_aggregate(model)

    def _to_aggregate(self, model: WorkflowModel) -> Workflow:
        """
        Convert database model to domain aggregate
        Mapping: WorkflowModel -> Workflow
        """
        metadata = Metadata(
            trace_id=model.metadata.get('trace_id') if model.metadata else None,
            requester_user_id=model.metadata.get('requester_user_id') if model.metadata else None,
            source=model.metadata.get('source') if model.metadata else None,
            additional_data=model.metadata if model.metadata else None
        )

        return Workflow(
            workflow_id=WorkflowId(model.workflow_id),
            decision_id=DecisionId(model.decision_id),
            tenant_id=TenantId(model.tenant_id),
            current_state=WorkflowState(model.current_state),
            approver_role=model.approver_role,
            created_at=model.created_at,
            delegated_to_user_id=model.delegated_to_user_id,
            escalated_to_user_id=model.escalated_to_user_id,
            escalated_to_role=None,
            completed_at=model.completed_at,
            metadata=metadata
        )
