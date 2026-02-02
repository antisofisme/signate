"""
Delete Rule Use Case

Soft deletes a rule (sets deleted_at timestamp).
"""

from uuid import UUID

from ..interfaces import IDecisionRepository


class DeleteRuleUseCase:
    """Use case for soft deleting a rule."""

    def __init__(self, repository: IDecisionRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        deleted_by: UUID,
    ) -> dict:
        """
        Soft delete a rule.

        Only rules in DRAFT or DEPRECATED status can be deleted.
        ACTIVE rules must first be deprecated before deletion.

        Raises:
            ValueError: If rule not found or cannot be deleted.
        """
        await self._repository.delete_rule(
            tenant_id=tenant_id,
            rule_id=rule_id,
            deleted_by=deleted_by,
        )

        return {
            "rule_id": str(rule_id),
            "deleted": True,
            "message": "Rule deleted successfully",
        }
