"""
Deactivate Rule Use Case

Transitions a rule from ACTIVE to DEPRECATED status.
"""

from typing import Optional
from uuid import UUID

from ..interfaces import IDecisionRepository


class DeactivateRuleUseCase:
    """Use case for deactivating (deprecating) an active rule."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        deactivated_by: UUID,
        reason: Optional[str] = None,
    ) -> dict:
        """
        Deactivate a rule.

        Transitions rule from ACTIVE to DEPRECATED status.
        DEPRECATED rules can then be deleted if needed.

        Args:
            tenant_id: Tenant ID for isolation
            rule_id: Rule to deactivate
            deactivated_by: User performing the action
            reason: Optional reason for deactivation

        Returns:
            Dict with rule info and status

        Raises:
            ValueError: If rule is not in ACTIVE status
        """
        rule = await self._repository.deactivate_rule(
            tenant_id=tenant_id,
            rule_id=rule_id,
            deactivated_by=deactivated_by,
            reason=reason,
        )

        return {
            "rule_id": str(rule.id),
            "rule_name": rule.rule_name,
            "status": rule.status.value,
            "deactivated_at": rule.deactivated_at.isoformat() if rule.deactivated_at else None,
            "deactivation_reason": rule.deactivation_reason,
            "message": "Rule deactivated successfully",
        }
