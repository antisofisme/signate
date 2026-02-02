"""
Update Rule Use Case

Updates a rule that is in DRAFT status.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from ..interfaces import IDecisionRepository


class UpdateRuleUseCase:
    """Use case for updating a draft rule."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        updated_by: UUID,
        rule_name: Optional[str] = None,
        description: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        action: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Update a rule in DRAFT status.

        Only rules in DRAFT status can be updated.
        At least one field must be provided for update.

        Raises:
            ValueError: If rule not found, not in DRAFT status, or no fields provided.
        """
        # Validate at least one field is provided
        if all(f is None for f in [rule_name, description, conditions, action]):
            raise ValueError("At least one field must be provided for update")

        rule = await self._repository.update_rule(
            tenant_id=tenant_id,
            rule_id=rule_id,
            updated_by=updated_by,
            rule_name=rule_name,
            description=description,
            conditions=conditions,
            action=action,
        )

        return {
            "id": str(rule.id),
            "rule_name": rule.rule_name,
            "decision_type": rule.decision_type,
            "description": rule.description,
            "conditions": rule.conditions,
            "action": rule.action,
            "status": rule.status.value,
            "version": rule.version,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
            "message": "Rule updated successfully",
        }
