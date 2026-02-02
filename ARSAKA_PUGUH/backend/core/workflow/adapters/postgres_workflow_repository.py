"""
PostgreSQL Workflow Repository Implementation
"""

from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..interfaces import IWorkflowRepository
from ..domain import Workflow, WorkflowStatus


class PostgresWorkflowRepository(IWorkflowRepository):
    """PostgreSQL implementation of Workflow repository."""

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def list_workflows(
        self,
        tenant_id: UUID,
        assignee_id: Optional[UUID] = None,
        status: Optional[WorkflowStatus] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[Workflow], int]:
        async with self._session_factory() as session:
            base_query = """
                SELECT
                    workflow_id, decision_id, tenant_id, current_state, approver_role,
                    delegated_to_user_id, escalated_to_user_id, escalation_timeout_at,
                    created_at, completed_at, metadata
                FROM workflows
                WHERE tenant_id = :tenant_id
            """
            params = {"tenant_id": str(tenant_id)}

            if status:
                base_query += " AND current_state = :status"
                params["status"] = status.value

            # "assignee=me" logic: check if workflow is assigned to user
            # For now, we don't have a direct assignee field, so we use approver_role
            # In production, you'd check user roles against approver_role

            count_query = f"SELECT COUNT(*) FROM ({base_query}) sub"
            result = await session.execute(text(count_query), params)
            total = result.scalar() or 0

            offset = (page - 1) * limit
            paginated_query = f"{base_query} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await session.execute(text(paginated_query), params)
            rows = result.fetchall()

            workflows = [
                Workflow(
                    id=row.workflow_id,
                    decision_id=row.decision_id,
                    tenant_id=row.tenant_id,
                    current_state=WorkflowStatus(row.current_state),
                    approver_role=row.approver_role,
                    delegated_to_user_id=row.delegated_to_user_id,
                    escalated_to_user_id=row.escalated_to_user_id,
                    escalation_timeout_at=row.escalation_timeout_at,
                    created_at=row.created_at,
                    completed_at=row.completed_at,
                    metadata=row.metadata,
                )
                for row in rows
            ]

            return workflows, total

    async def get_workflow(self, tenant_id: UUID, workflow_id: UUID) -> Optional[Workflow]:
        async with self._session_factory() as session:
            query = """
                SELECT
                    workflow_id, decision_id, tenant_id, current_state, approver_role,
                    delegated_to_user_id, escalated_to_user_id, escalation_timeout_at,
                    created_at, completed_at, metadata
                FROM workflows
                WHERE workflow_id = :workflow_id AND tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"workflow_id": str(workflow_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return Workflow(
                id=row.workflow_id,
                decision_id=row.decision_id,
                tenant_id=row.tenant_id,
                current_state=WorkflowStatus(row.current_state),
                approver_role=row.approver_role,
                delegated_to_user_id=row.delegated_to_user_id,
                escalated_to_user_id=row.escalated_to_user_id,
                escalation_timeout_at=row.escalation_timeout_at,
                created_at=row.created_at,
                completed_at=row.completed_at,
                metadata=row.metadata,
            )

    async def get_workflow_transitions(self, tenant_id: UUID, workflow_id: UUID) -> List[dict]:
        async with self._session_factory() as session:
            query = """
                SELECT
                    transition_id, workflow_id, from_state, to_state, action,
                    acted_by_user_id, approver_role, comment, created_at
                FROM workflow_transitions
                WHERE workflow_id = :workflow_id AND tenant_id = :tenant_id
                ORDER BY created_at ASC
            """
            result = await session.execute(
                text(query),
                {"workflow_id": str(workflow_id), "tenant_id": str(tenant_id)}
            )
            rows = result.fetchall()

            return [
                {
                    "id": str(row.transition_id),
                    "from_state": row.from_state,
                    "to_state": row.to_state,
                    "action": row.action,
                    "acted_by_user_id": str(row.acted_by_user_id) if row.acted_by_user_id else None,
                    "approver_role": row.approver_role,
                    "comment": row.comment,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]

    async def _update_workflow_state(
        self,
        session,
        tenant_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
        new_state: WorkflowStatus,
        action: str,
        comment: Optional[str] = None,
        extra_updates: Optional[dict] = None,
    ) -> Workflow:
        """Helper to update workflow state and create transition."""
        # Get current workflow
        workflow = await self.get_workflow(tenant_id, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        old_state = workflow.current_state.value

        # Update workflow
        update_sql = "UPDATE workflows SET current_state = :new_state"
        params = {
            "workflow_id": str(workflow_id),
            "tenant_id": str(tenant_id),
            "new_state": new_state.value,
        }

        if new_state in (WorkflowStatus.APPROVED, WorkflowStatus.REJECTED):
            update_sql += ", completed_at = NOW()"

        if extra_updates:
            for key, value in extra_updates.items():
                update_sql += f", {key} = :{key}"
                params[key] = str(value) if isinstance(value, UUID) else value

        update_sql += " WHERE workflow_id = :workflow_id AND tenant_id = :tenant_id"
        await session.execute(text(update_sql), params)

        # Create transition
        transition_id = uuid4()
        transition_sql = """
            INSERT INTO workflow_transitions (
                transition_id, workflow_id, tenant_id, from_state, to_state,
                action, acted_by_user_id, comment
            )
            VALUES (
                :transition_id, :workflow_id, :tenant_id, :from_state, :to_state,
                :action, :acted_by_user_id, :comment
            )
        """
        await session.execute(
            text(transition_sql),
            {
                "transition_id": str(transition_id),
                "workflow_id": str(workflow_id),
                "tenant_id": str(tenant_id),
                "from_state": old_state,
                "to_state": new_state.value,
                "action": action,
                "acted_by_user_id": str(user_id),
                "comment": comment,
            }
        )

        await session.commit()

        # Return updated workflow
        return await self.get_workflow(tenant_id, workflow_id)

    async def approve_workflow(
        self, tenant_id: UUID, workflow_id: UUID, user_id: UUID, comment: Optional[str] = None
    ) -> Workflow:
        async with self._session_factory() as session:
            return await self._update_workflow_state(
                session, tenant_id, workflow_id, user_id,
                WorkflowStatus.APPROVED, "APPROVED", comment
            )

    async def reject_workflow(
        self, tenant_id: UUID, workflow_id: UUID, user_id: UUID, reason: str
    ) -> Workflow:
        async with self._session_factory() as session:
            return await self._update_workflow_state(
                session, tenant_id, workflow_id, user_id,
                WorkflowStatus.REJECTED, "REJECTED", reason
            )

    async def delegate_workflow(
        self, tenant_id: UUID, workflow_id: UUID, user_id: UUID, delegate_to: UUID, reason: str
    ) -> Workflow:
        async with self._session_factory() as session:
            return await self._update_workflow_state(
                session, tenant_id, workflow_id, user_id,
                WorkflowStatus.DELEGATED, "DELEGATED", reason,
                extra_updates={"delegated_to_user_id": delegate_to}
            )

    async def escalate_workflow(
        self, tenant_id: UUID, workflow_id: UUID, user_id: UUID, escalate_to: UUID, reason: str
    ) -> Workflow:
        async with self._session_factory() as session:
            return await self._update_workflow_state(
                session, tenant_id, workflow_id, user_id,
                WorkflowStatus.ESCALATED, "ESCALATED", reason,
                extra_updates={"escalated_to_user_id": escalate_to}
            )

    async def get_stats(self, tenant_id: UUID) -> dict:
        """Get workflow statistics for tenant."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN current_state = 'PENDING_APPROVAL' THEN 1 END) as pending,
                    COUNT(CASE WHEN current_state = 'APPROVED' THEN 1 END) as approved,
                    COUNT(CASE WHEN current_state = 'REJECTED' THEN 1 END) as rejected,
                    COUNT(CASE WHEN current_state = 'ESCALATED' THEN 1 END) as escalated,
                    COUNT(CASE WHEN current_state = 'DELEGATED' THEN 1 END) as delegated
                FROM workflows
                WHERE tenant_id = :tenant_id
            """
            result = await session.execute(text(query), {"tenant_id": str(tenant_id)})
            row = result.fetchone()

            return {
                "total": row.total or 0,
                "pending": row.pending or 0,
                "approved": row.approved or 0,
                "rejected": row.rejected or 0,
                "escalated": row.escalated or 0,
                "delegated": row.delegated or 0,
            }

    async def check_idempotency(
        self, tenant_id: UUID, workflow_id: UUID, idempotency_key: str
    ) -> Optional[dict]:
        """
        Check if an action with this idempotency_key was already performed.
        Returns the cached result if found, None otherwise.
        Uses the workflow's metadata JSONB column to store idempotency info.
        """
        async with self._session_factory() as session:
            query = """
                SELECT metadata->'idempotency'->:idempotency_key as cached_result
                FROM workflows
                WHERE workflow_id = :workflow_id AND tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {
                    "workflow_id": str(workflow_id),
                    "tenant_id": str(tenant_id),
                    "idempotency_key": idempotency_key,
                }
            )
            row = result.fetchone()

            if row and row.cached_result:
                return row.cached_result

            return None

    async def store_idempotency(
        self, tenant_id: UUID, workflow_id: UUID, idempotency_key: str, result: dict
    ) -> None:
        """
        Store idempotency result for future deduplication.
        Stores in workflow metadata JSONB: {"idempotency": {"key": {result}}}
        """
        import json
        async with self._session_factory() as session:
            query = """
                UPDATE workflows
                SET metadata = COALESCE(metadata, '{}'::jsonb) ||
                    jsonb_build_object('idempotency',
                        COALESCE(metadata->'idempotency', '{}'::jsonb) ||
                        jsonb_build_object(:idempotency_key, :result::jsonb)
                    )
                WHERE workflow_id = :workflow_id AND tenant_id = :tenant_id
            """
            await session.execute(
                text(query),
                {
                    "workflow_id": str(workflow_id),
                    "tenant_id": str(tenant_id),
                    "idempotency_key": idempotency_key,
                    "result": json.dumps(result),
                }
            )
            await session.commit()
