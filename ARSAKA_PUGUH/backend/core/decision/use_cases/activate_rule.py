"""
Activate Rule Use Case

Note: In a full implementation, this would create an approval workflow.
For now, it directly activates the rule.
"""

from uuid import UUID

from ..interfaces import IDecisionRepository


class ActivateRuleUseCase:
    """Use case for activating a rule (requesting activation)."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        activated_by: UUID,
        idempotency_key: str,
    ) -> dict:
        """
        Activate a rule.

        In production, this would:
        1. Create a decision record (REQUIRE_APPROVAL outcome)
        2. Create an approval workflow
        3. Return workflow info

        For Phase A, we directly activate the rule.
        """
        # For Phase A: Direct activation
        rule = await self._repository.activate_rule(
            tenant_id=tenant_id,
            rule_id=rule_id,
            activated_by=activated_by,
        )

        # TODO: In production, create workflow and return workflow ID
        return {
            "rule_id": str(rule.id),
            "rule_name": rule.rule_name,
            "status": rule.status.value,
            "activated_at": rule.activated_at.isoformat() if rule.activated_at else None,
            "message": "Rule activated successfully",
            # For future: workflow_id, decision_id
        }
