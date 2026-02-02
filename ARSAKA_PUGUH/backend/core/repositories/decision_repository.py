"""
DecisionRepository Implementation

Persistence adapter for Decision aggregate.
Source: INFRA-LAY3-002 §2 (Decision Creation Transaction Standards)
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain import Decision, DecisionId, TenantId, Outcome, Context, IdempotencyKey, RuleId, RuleVersion, Metadata
from ..use_cases.interfaces import IDecisionRepository
from .models import DecisionModel


class DecisionRepository(IDecisionRepository):
    """
    Decision repository implementation
    Maps: Decision aggregate <-> DecisionModel
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, decision: Decision) -> None:
        """
        Save decision to database
        Mapping: Decision aggregate -> DecisionModel
        """
        metadata_dict = decision.metadata.to_dict() if decision.metadata else {}

        model = DecisionModel(
            decision_id=decision.decision_id.value,
            tenant_id=decision.tenant_id.value,
            decision_type=decision.decision_type,
            context=decision.context.to_dict(),
            outcome=decision.outcome.value,
            rule_matched_id=decision.rule_matched_id.value if decision.rule_matched_id else None,
            rule_version=str(decision.rule_version) if decision.rule_version else None,
            approval_workflow_id=None,
            idempotency_key=str(decision.idempotency_key) if decision.idempotency_key else None,
            latency_ms=decision.latency_ms,
            created_at=decision.created_at,
            metadata=metadata_dict
        )

        self._session.add(model)

    async def find_by_id(
        self,
        decision_id: DecisionId,
        tenant_id: TenantId
    ) -> Optional[Decision]:
        """
        Find decision by ID (tenant-scoped)
        Mapping: DecisionModel -> Decision aggregate
        """
        stmt = select(DecisionModel).where(
            DecisionModel.decision_id == decision_id.value,
            DecisionModel.tenant_id == tenant_id.value
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_aggregate(model)

    async def find_by_idempotency_key(
        self,
        tenant_id: TenantId,
        idempotency_key: IdempotencyKey
    ) -> Optional[Decision]:
        """
        Find decision by idempotency key
        Source: INFRA-LAY3-002 §2.2
        """
        stmt = select(DecisionModel).where(
            DecisionModel.tenant_id == tenant_id.value,
            DecisionModel.idempotency_key == str(idempotency_key)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_aggregate(model)

    def _to_aggregate(self, model: DecisionModel) -> Decision:
        """
        Convert database model to domain aggregate
        Mapping: DecisionModel -> Decision
        """
        metadata = Metadata(
            trace_id=model.metadata.get('trace_id') if model.metadata else None,
            requester_user_id=model.metadata.get('requester_user_id') if model.metadata else None,
            source=model.metadata.get('source') if model.metadata else None,
            additional_data=model.metadata if model.metadata else None
        )

        return Decision(
            decision_id=DecisionId(model.decision_id),
            tenant_id=TenantId(model.tenant_id),
            decision_type=model.decision_type,
            context=Context(model.context),
            outcome=Outcome(model.outcome),
            rule_matched_id=RuleId(model.rule_matched_id) if model.rule_matched_id else None,
            rule_version=RuleVersion(model.rule_version) if model.rule_version else None,
            idempotency_key=IdempotencyKey(model.idempotency_key) if model.idempotency_key else None,
            metadata=metadata,
            created_at=model.created_at,
            latency_ms=model.latency_ms
        )
