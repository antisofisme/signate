"""
RuleRepository Implementation

Persistence adapter for Rule loading.
Source: INFRA-LAY3-002 §1 (Rule Evaluation Engine Standards)
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain import TenantId, RuleId, RuleVersion
from ..use_cases.interfaces import IRuleRepository, Rule
from .models import RuleModel


class RuleRepository(IRuleRepository):
    """
    Rule repository implementation
    Maps: RuleModel -> Rule value object
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_active_rules(
        self,
        tenant_id: TenantId,
        decision_type: str
    ) -> List[Rule]:
        """
        Load ACTIVE rules for tenant and decision type
        Ordered by evaluation_sequence ASC (deterministic)
        Source: INFRA-LAY3-002 §1.4, Phase 1 Clarification 1
        """
        stmt = (
            select(RuleModel)
            .where(
                RuleModel.tenant_id == tenant_id.value,
                RuleModel.decision_type == decision_type,
                RuleModel.status == 'ACTIVE'
            )
            .order_by(RuleModel.evaluation_sequence.asc())
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_value_object(model) for model in models]

    def _to_value_object(self, model: RuleModel) -> Rule:
        """
        Convert database model to Rule value object
        Mapping: RuleModel -> Rule
        """
        return Rule(
            rule_id=RuleId(model.rule_id),
            rule_name=model.rule_name,
            version=RuleVersion(model.version),
            conditions=model.conditions,
            action=model.action,
            evaluation_sequence=model.evaluation_sequence
        )
