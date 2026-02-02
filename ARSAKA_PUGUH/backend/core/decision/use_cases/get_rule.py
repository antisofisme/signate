"""
Get Rule Use Case
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IDecisionRepository


class GetRuleUseCase:
    """Use case for getting a rule with versions."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, rule_id: UUID) -> Optional[dict]:
        """Get rule by ID."""
        rule = await self._repository.get_rule(tenant_id, rule_id)
        if not rule:
            return None

        return {
            "id": str(rule.id),
            "rule_name": rule.rule_name,
            "decision_type": rule.decision_type,
            "description": rule.description,
            "conditions": rule.conditions,
            "action": rule.action,
            "extension_hooks": rule.extension_hooks,
            "status": rule.status.value,
            "version": rule.version,
            "evaluation_sequence": rule.evaluation_sequence,
            "can_edit": rule.can_edit(),
            "can_delete": rule.can_delete(),
            "can_activate": rule.can_activate(),
            "created_by_user_id": str(rule.created_by_user_id) if rule.created_by_user_id else None,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
            "activated_at": rule.activated_at.isoformat() if rule.activated_at else None,
            "deactivated_at": rule.deactivated_at.isoformat() if rule.deactivated_at else None,
            "deactivation_reason": rule.deactivation_reason,
        }

    async def get_versions(self, tenant_id: UUID, rule_id: UUID) -> list:
        """Get version history for a rule."""
        return await self._repository.get_rule_versions(tenant_id, rule_id)
