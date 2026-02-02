"""
PostgreSQL + Qdrant Semantic Memory

Stores and retrieves persistent user facts.
"""

from typing import Optional, List
from datetime import datetime
from uuid import uuid4

from ....core.interfaces.memory import SemanticMemory
from ....core.interfaces.storage import VectorStore
from ....core.entities import UserFact, FactType
from ....infrastructure.database.connection import DatabasePool
from ....shared.logging import get_logger

logger = get_logger(__name__)


class PostgresSemanticMemory(SemanticMemory):
    """
    PostgreSQL + Qdrant implementation of Semantic Memory.

    User facts stored in PostgreSQL with metadata.
    Fact embeddings stored in Qdrant for semantic search.

    Features:
    - Persistent user fact storage
    - Semantic fact retrieval
    - Confidence tracking and decay
    - Fact deactivation (soft delete)
    """

    COLLECTION_PREFIX = "semantic"

    def __init__(
        self,
        db_pool: DatabasePool,
        vector_store: VectorStore,
        vector_dimensions: int = 1536,
    ):
        self.db_pool = db_pool
        self.vector_store = vector_store
        self.vector_dimensions = vector_dimensions

    def _get_collection_name(self, tenant_id: str) -> str:
        """Get Qdrant collection name for tenant."""
        return f"{self.COLLECTION_PREFIX}_{tenant_id}"

    async def add_fact(
        self,
        fact: UserFact,
        embedding: List[float]
    ) -> str:
        """Add a new user fact with embedding."""
        pool = await self.db_pool.get_pool()

        # Generate ID if not set
        if not fact.id:
            fact.id = str(uuid4())

        # Insert into PostgreSQL
        await pool.execute(
            """
            INSERT INTO user_facts (
                id, tenant_id, user_id, fact_type, content,
                source_session_id, source_message_id,
                confidence, is_active, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                confidence = EXCLUDED.confidence,
                updated_at = NOW()
            """,
            fact.id,
            fact.tenant_id,
            fact.user_id,
            fact.fact_type.value if isinstance(fact.fact_type, FactType) else fact.fact_type,
            fact.content,
            fact.source_session_id,
            fact.source_message_id,
            fact.confidence,
            fact.is_active,
            fact.created_at or datetime.utcnow(),
        )

        # Store embedding in Qdrant
        collection = self._get_collection_name(fact.tenant_id)

        await self.vector_store.ensure_collection(
            collection=collection,
            vector_size=self.vector_dimensions,
        )

        await self.vector_store.upsert(
            collection=collection,
            id=f"fact_{fact.id}",
            vector=embedding,
            payload={
                "tenant_id": fact.tenant_id,
                "user_id": fact.user_id,
                "fact_id": fact.id,
                "fact_type": fact.fact_type.value if isinstance(fact.fact_type, FactType) else fact.fact_type,
                "content": fact.content,
                "confidence": fact.confidence,
                "is_active": fact.is_active,
                "created_at": fact.created_at.isoformat() if fact.created_at else None,
            },
        )

        logger.debug(f"Added fact {fact.id} for user {fact.user_id}")
        return fact.id

    async def get_relevant_facts(
        self,
        tenant_id: str,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 10,
        min_confidence: float = 0.5
    ) -> List[UserFact]:
        """Get facts relevant to query."""
        collection = self._get_collection_name(tenant_id)

        try:
            results = await self.vector_store.search(
                collection=collection,
                query_vector=query_embedding,
                top_k=top_k * 2,  # Get more to filter by confidence
                filters={
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "is_active": True,
                },
                score_threshold=0.3,
            )

            facts = []
            for result in results:
                confidence = result.metadata.get("confidence", 1.0)
                if confidence >= min_confidence:
                    facts.append(UserFact(
                        id=result.metadata.get("fact_id", result.id),
                        tenant_id=tenant_id,
                        user_id=user_id,
                        fact_type=FactType(result.metadata.get("fact_type", "general")),
                        content=result.metadata.get("content", result.content),
                        confidence=confidence,
                        is_active=result.metadata.get("is_active", True),
                        relevance_score=result.score,
                    ))

                if len(facts) >= top_k:
                    break

            logger.debug(f"Found {len(facts)} relevant facts for user {user_id}")
            return facts

        except Exception as e:
            logger.warning(f"Fact search failed: {e}")
            return []

    async def get_all_facts(
        self,
        tenant_id: str,
        user_id: str,
        fact_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[UserFact]:
        """Get all user facts from PostgreSQL."""
        pool = await self.db_pool.get_pool()

        query = """
            SELECT
                id, tenant_id, user_id, fact_type, content,
                source_session_id, source_message_id,
                confidence, is_active, created_at, updated_at
            FROM user_facts
            WHERE tenant_id = $1 AND user_id = $2
        """
        params = [tenant_id, user_id]

        if active_only:
            query += " AND is_active = TRUE"

        if fact_type:
            query += f" AND fact_type = ${len(params) + 1}"
            params.append(fact_type)

        query += " ORDER BY confidence DESC, created_at DESC"

        rows = await pool.fetch(query, *params)

        return [
            UserFact(
                id=str(row["id"]),
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
                fact_type=FactType(row["fact_type"]),
                content=row["content"],
                source_session_id=row["source_session_id"],
                source_message_id=row["source_message_id"],
                confidence=row["confidence"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    async def update_fact_confidence(
        self,
        fact_id: str,
        tenant_id: str,
        new_confidence: float
    ) -> bool:
        """Update fact confidence score."""
        pool = await self.db_pool.get_pool()

        # Clamp confidence to valid range
        new_confidence = max(0.0, min(1.0, new_confidence))

        result = await pool.execute(
            """
            UPDATE user_facts
            SET confidence = $1, updated_at = NOW()
            WHERE id = $2 AND tenant_id = $3
            """,
            new_confidence,
            fact_id,
            tenant_id,
        )

        # Also update in Qdrant
        collection = self._get_collection_name(tenant_id)
        try:
            # Get existing point to update payload
            point = await self.vector_store.get_by_id(collection, f"fact_{fact_id}")
            if point:
                payload = point.get("payload", {})
                payload["confidence"] = new_confidence
                await self.vector_store.upsert(
                    collection=collection,
                    id=f"fact_{fact_id}",
                    vector=point["vector"],
                    payload=payload,
                )
        except Exception as e:
            logger.warning(f"Failed to update fact confidence in Qdrant: {e}")

        updated = "UPDATE 1" in str(result)
        if updated:
            logger.debug(f"Updated confidence for fact {fact_id} to {new_confidence}")
        return updated

    async def deactivate_fact(
        self,
        fact_id: str,
        tenant_id: str
    ) -> bool:
        """Deactivate a fact (soft delete)."""
        pool = await self.db_pool.get_pool()

        result = await pool.execute(
            """
            UPDATE user_facts
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2
            """,
            fact_id,
            tenant_id,
        )

        # Update in Qdrant
        collection = self._get_collection_name(tenant_id)
        try:
            point = await self.vector_store.get_by_id(collection, f"fact_{fact_id}")
            if point:
                payload = point.get("payload", {})
                payload["is_active"] = False
                await self.vector_store.upsert(
                    collection=collection,
                    id=f"fact_{fact_id}",
                    vector=point["vector"],
                    payload=payload,
                )
        except Exception as e:
            logger.warning(f"Failed to deactivate fact in Qdrant: {e}")

        deactivated = "UPDATE 1" in str(result)
        if deactivated:
            logger.debug(f"Deactivated fact {fact_id}")
        return deactivated

    async def merge_facts(
        self,
        tenant_id: str,
        user_id: str,
        fact_ids: List[str],
        merged_content: str,
        merged_embedding: List[float],
    ) -> str:
        """
        Merge multiple facts into one.

        Deactivates old facts and creates a new merged fact.
        """
        pool = await self.db_pool.get_pool()

        # Create merged fact
        merged_fact = UserFact(
            id=str(uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            fact_type=FactType.GENERAL,
            content=merged_content,
            confidence=1.0,
            is_active=True,
        )

        # Add merged fact
        merged_id = await self.add_fact(merged_fact, merged_embedding)

        # Deactivate original facts
        for fact_id in fact_ids:
            await self.deactivate_fact(fact_id, tenant_id)

        logger.info(f"Merged {len(fact_ids)} facts into {merged_id}")
        return merged_id

    async def ensure_collection(self, tenant_id: str) -> bool:
        """Ensure Qdrant collection exists for tenant."""
        collection = self._get_collection_name(tenant_id)
        return await self.vector_store.ensure_collection(
            collection=collection,
            vector_size=self.vector_dimensions,
        )
