"""
User facts repository (semantic memory).
"""

from typing import Optional, List
from uuid import UUID

from .base_repository import BaseRepository
from ....core.entities import UserFact, FactType
from ....shared.logging import get_logger

logger = get_logger(__name__)


class FactRepository(BaseRepository[UserFact]):
    """Repository for user facts (semantic memory)."""

    def __init__(self, pool):
        super().__init__(pool, "user_facts")

    def _row_to_entity(self, row) -> UserFact:
        """Convert database row to UserFact."""
        return UserFact(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            fact_type=FactType(row["fact_type"]),
            content=row["content"],
            content_embedding=None,  # Not loaded by default
            confidence=row["confidence"],
            source_session_id=row["source_session_id"],
            source_message_id=row["source_message_id"],
            extracted_at=row["extracted_at"],
            is_active=row["is_active"],
            superseded_by=row["superseded_by"],
            last_confirmed_at=row["last_confirmed_at"],
            confirmation_count=row["confirmation_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create(self, fact: UserFact) -> str:
        """Create a new user fact."""
        query = """
            INSERT INTO user_facts (
                id, tenant_id, user_id,
                fact_type, content, confidence,
                source_session_id, source_message_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """

        result = await self._fetchval(
            query,
            fact.id, fact.tenant_id, fact.user_id,
            fact.fact_type.value, fact.content, fact.confidence,
            fact.source_session_id, fact.source_message_id
        )

        logger.debug(f"Created fact: {result}")
        return str(result)

    async def get_by_user(
        self,
        tenant_id: str,
        user_id: str,
        fact_type: Optional[str] = None,
        active_only: bool = True,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[UserFact]:
        """Get facts for a user."""
        conditions = ["tenant_id = $1", "user_id = $2"]
        args = [tenant_id, user_id]
        arg_idx = 3

        if active_only:
            conditions.append("is_active = TRUE")

        if fact_type:
            conditions.append(f"fact_type = ${arg_idx}")
            args.append(fact_type)
            arg_idx += 1

        if min_confidence > 0:
            conditions.append(f"confidence >= ${arg_idx}")
            args.append(min_confidence)
            arg_idx += 1

        conditions.append(f"LIMIT ${arg_idx}")
        args.append(limit)

        query = f"""
            SELECT * FROM user_facts
            WHERE {' AND '.join(conditions[:-1])}
            ORDER BY confidence DESC, created_at DESC
            {conditions[-1]}
        """

        rows = await self._fetch(query, *args)
        return [self._row_to_entity(row) for row in rows]

    async def update_confidence(
        self,
        fact_id: str,
        tenant_id: str,
        new_confidence: float
    ) -> bool:
        """Update fact confidence."""
        query = """
            UPDATE user_facts SET
                confidence = $3,
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2
        """

        result = await self._execute(query, fact_id, tenant_id, new_confidence)
        return "UPDATE 1" in result

    async def confirm(
        self,
        fact_id: str,
        tenant_id: str
    ) -> bool:
        """Confirm a fact (increases confidence)."""
        query = """
            UPDATE user_facts SET
                last_confirmed_at = NOW(),
                confirmation_count = confirmation_count + 1,
                confidence = LEAST(1.0, confidence + 0.05),
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2 AND is_active = TRUE
        """

        result = await self._execute(query, fact_id, tenant_id)
        return "UPDATE 1" in result

    async def deactivate(
        self,
        fact_id: str,
        tenant_id: str
    ) -> bool:
        """Deactivate a fact (soft delete)."""
        query = """
            UPDATE user_facts SET
                is_active = FALSE,
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2 AND is_active = TRUE
        """

        result = await self._execute(query, fact_id, tenant_id)
        return "UPDATE 1" in result

    async def supersede(
        self,
        old_fact_id: str,
        new_fact_id: str,
        tenant_id: str
    ) -> bool:
        """Mark fact as superseded by a newer fact."""
        query = """
            UPDATE user_facts SET
                is_active = FALSE,
                superseded_by = $2,
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $3 AND is_active = TRUE
        """

        result = await self._execute(query, old_fact_id, new_fact_id, tenant_id)
        return "UPDATE 1" in result

    async def count_by_user(
        self,
        tenant_id: str,
        user_id: str,
        active_only: bool = True
    ) -> int:
        """Count facts for user."""
        if active_only:
            query = """
                SELECT COUNT(*) FROM user_facts
                WHERE tenant_id = $1 AND user_id = $2 AND is_active = TRUE
            """
        else:
            query = """
                SELECT COUNT(*) FROM user_facts
                WHERE tenant_id = $1 AND user_id = $2
            """

        return await self._fetchval(query, tenant_id, user_id)

    async def get_by_type_stats(
        self,
        tenant_id: str,
        user_id: str
    ) -> dict:
        """Get fact count by type."""
        query = """
            SELECT fact_type, COUNT(*) as count
            FROM user_facts
            WHERE tenant_id = $1 AND user_id = $2 AND is_active = TRUE
            GROUP BY fact_type
        """

        rows = await self._fetch(query, tenant_id, user_id)
        return {row["fact_type"]: row["count"] for row in rows}
