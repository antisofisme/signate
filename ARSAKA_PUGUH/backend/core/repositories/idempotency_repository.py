"""
IdempotencyRepository Implementation

Persistence adapter for idempotency cache.
Source: INFRA-LAY3-002 §2.2, Phase 1 Clarification 2
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain import TenantId, DecisionId, IdempotencyKey
from ..use_cases.interfaces import IIdempotencyRepository
from .models import IdempotencyCacheModel


class IdempotencyRepository(IIdempotencyRepository):
    """
    Idempotency cache repository implementation
    Maps: IdempotencyCacheModel <-> idempotency cache operations
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find(
        self,
        tenant_id: TenantId,
        idempotency_key: IdempotencyKey
    ) -> Optional[DecisionId]:
        """
        Find cached decision ID by idempotency key
        """
        stmt = select(IdempotencyCacheModel).where(
            IdempotencyCacheModel.tenant_id == tenant_id.value,
            IdempotencyCacheModel.idempotency_key == str(idempotency_key)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return DecisionId(model.decision_id)

    async def save(
        self,
        tenant_id: TenantId,
        idempotency_key: IdempotencyKey,
        decision_id: DecisionId,
        context_hash: str
    ) -> None:
        """
        Save idempotency cache entry
        context_hash: SHA-256 hash of canonicalized context (Architecture Layer 2.6)
        """
        model = IdempotencyCacheModel(
            tenant_id=tenant_id.value,
            idempotency_key=str(idempotency_key),
            decision_id=decision_id.value,
            context_hash=context_hash,
            ttl=None
        )
        self._session.add(model)

    async def get_context_hash(
        self,
        tenant_id: TenantId,
        idempotency_key: IdempotencyKey
    ) -> Optional[str]:
        """
        Get context hash for conflict detection
        """
        stmt = select(IdempotencyCacheModel).where(
            IdempotencyCacheModel.tenant_id == tenant_id.value,
            IdempotencyCacheModel.idempotency_key == str(idempotency_key)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return model.context_hash
