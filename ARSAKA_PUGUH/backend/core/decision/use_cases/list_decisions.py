"""
List Decisions Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IDecisionRepository


class ListDecisionsUseCase:
    """Use case for listing decisions in a tenant."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        decision_type: Optional[str] = None,
        outcome: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List decisions with optional filters."""
        decisions, total = await self._repository.list_decisions(
            tenant_id=tenant_id,
            decision_type=decision_type,
            outcome=outcome,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                {
                    "id": str(dec.id),
                    "decision_type": dec.decision_type,
                    "outcome": dec.outcome.value,
                    "rule_matched_id": str(dec.rule_matched_id) if dec.rule_matched_id else None,
                    "rule_version": dec.rule_version,
                    "approval_workflow_id": str(dec.approval_workflow_id) if dec.approval_workflow_id else None,
                    "latency_ms": dec.latency_ms,
                    "created_at": dec.created_at.isoformat() if dec.created_at else None,
                }
                for dec in decisions
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
