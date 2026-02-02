"""
List Rules Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IDecisionRepository
from ..domain import RuleStatus


class ListRulesUseCase:
    """Use case for listing rules in a tenant."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        decision_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List rules with optional filters."""
        rule_status = RuleStatus(status) if status else None

        rules, total = await self._repository.list_rules(
            tenant_id=tenant_id,
            status=rule_status,
            decision_type=decision_type,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                {
                    "id": str(rule.id),
                    "rule_name": rule.rule_name,
                    "decision_type": rule.decision_type,
                    "description": rule.description,
                    "status": rule.status.value,
                    "version": rule.version,
                    "evaluation_sequence": rule.evaluation_sequence,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "activated_at": rule.activated_at.isoformat() if rule.activated_at else None,
                }
                for rule in rules
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0,
        }

    async def get_decision_types(self, tenant_id: UUID) -> list[str]:
        """Get distinct decision types available in tenant."""
        return await self._repository.get_decision_types(tenant_id=tenant_id)
