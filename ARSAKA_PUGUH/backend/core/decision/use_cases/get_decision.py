"""
Get Decision Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IDecisionRepository


class GetDecisionUseCase:
    """Use case for getting a decision with events."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, decision_id: UUID) -> Optional[dict]:
        """Get decision by ID with full details."""
        decision = await self._repository.get_decision(tenant_id, decision_id)
        if not decision:
            return None

        return {
            "id": str(decision.id),
            "decision_type": decision.decision_type,
            "context": decision.context,
            "outcome": decision.outcome.value,
            "rule_matched_id": str(decision.rule_matched_id) if decision.rule_matched_id else None,
            "rule_version": decision.rule_version,
            "approval_workflow_id": str(decision.approval_workflow_id) if decision.approval_workflow_id else None,
            "idempotency_key": decision.idempotency_key,
            "latency_ms": decision.latency_ms,
            "created_at": decision.created_at.isoformat() if decision.created_at else None,
            "metadata": decision.metadata,
            "requires_approval": decision.requires_approval(),
        }

    async def get_events(self, tenant_id: UUID, decision_id: UUID) -> list:
        """Get events for a decision."""
        return await self._repository.get_decision_events(tenant_id, decision_id)
