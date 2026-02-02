"""
Create Rule Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IDecisionRepository


class CreateRuleUseCase:
    """Use case for creating a new rule draft."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        rule_name: str,
        decision_type: str,
        conditions: dict,
        action: dict,
        created_by: UUID,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """Create a new rule in DRAFT status."""
        rule = await self._repository.create_rule(
            tenant_id=tenant_id,
            rule_name=rule_name,
            decision_type=decision_type,
            conditions=conditions,
            action=action,
            created_by=created_by,
            description=description,
            idempotency_key=idempotency_key,
        )

        return {
            "id": str(rule.id),
            "rule_name": rule.rule_name,
            "decision_type": rule.decision_type,
            "description": rule.description,
            "status": rule.status.value,
            "version": rule.version,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
        }
