"""
PostgreSQL + Qdrant Episodic Memory

Stores and retrieves past session summaries.
"""

from typing import Optional, List
from datetime import datetime

from ....core.interfaces.memory import EpisodicMemory
from ....core.interfaces.storage import VectorStore
from ....core.entities import ChatMessage, ChatSession, SessionSummary
from ....infrastructure.database.connection import DatabasePool
from ....shared.logging import get_logger

logger = get_logger(__name__)


class PostgresEpisodicMemory(EpisodicMemory):
    """
    PostgreSQL + Qdrant implementation of Episodic Memory.

    Session summaries stored in PostgreSQL.
    Summary embeddings stored in Qdrant for semantic search.

    Features:
    - Session summary storage
    - Semantic session search
    - Message retrieval from past sessions
    """

    COLLECTION_PREFIX = "episodic"

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

    async def save_session_summary(
        self,
        session: ChatSession,
        embedding: List[float]
    ) -> str:
        """Save session summary with embedding."""
        pool = await self.db_pool.get_pool()

        # Update session with summary in PostgreSQL
        await pool.execute(
            """
            UPDATE chat_sessions
            SET summary = $1, summary_updated_at = NOW()
            WHERE id = $2 AND tenant_id = $3
            """,
            session.summary,
            str(session.id),
            session.tenant_id,
        )

        # Store embedding in Qdrant
        collection = self._get_collection_name(session.tenant_id)

        # Ensure collection exists
        await self.vector_store.ensure_collection(
            collection=collection,
            vector_size=self.vector_dimensions,
        )

        # Upsert embedding
        await self.vector_store.upsert(
            collection=collection,
            id=f"session_{session.id}",
            vector=embedding,
            payload={
                "tenant_id": session.tenant_id,
                "user_id": session.user_id,
                "session_id": str(session.id),
                "title": session.title,
                "summary": session.summary,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "message_count": session.message_count,
            },
        )

        logger.debug(f"Saved session summary for {session.id}")
        return str(session.id)

    async def search_sessions(
        self,
        tenant_id: str,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SessionSummary]:
        """Search for similar past sessions."""
        collection = self._get_collection_name(tenant_id)

        try:
            results = await self.vector_store.search(
                collection=collection,
                query_vector=query_embedding,
                top_k=top_k,
                filters={
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                },
                score_threshold=0.3,
            )

            summaries = []
            for result in results:
                summaries.append(SessionSummary(
                    session_id=result.metadata.get("session_id", result.id),
                    title=result.metadata.get("title"),
                    summary=result.metadata.get("summary", result.content),
                    message_count=result.metadata.get("message_count", 0),
                    started_at=datetime.fromisoformat(result.metadata["started_at"])
                        if result.metadata.get("started_at") else None,
                    relevance_score=result.score,
                ))

            logger.debug(f"Found {len(summaries)} relevant sessions for user {user_id}")
            return summaries

        except Exception as e:
            logger.warning(f"Session search failed: {e}")
            return []

    async def get_session_messages(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get messages from a specific session."""
        pool = await self.db_pool.get_pool()

        rows = await pool.fetch(
            """
            SELECT
                id, session_id, tenant_id, user_id, role, content,
                page_context, retrieved_doc_ids, token_count,
                prompt_tokens, completion_tokens, provider, model,
                temperature, is_redacted, created_at
            FROM chat_messages
            WHERE session_id = $1 AND tenant_id = $2
            ORDER BY created_at ASC
            LIMIT $3
            """,
            session_id,
            tenant_id,
            limit,
        )

        messages = []
        for row in rows:
            from ....core.entities import Role
            messages.append(ChatMessage(
                id=row["id"],
                session_id=row["session_id"],
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
                role=Role(row["role"]),
                content=row["content"],
                page_context=row["page_context"],
                retrieved_doc_ids=row["retrieved_doc_ids"] or [],
                token_count=row["token_count"],
                prompt_tokens=row["prompt_tokens"],
                completion_tokens=row["completion_tokens"],
                provider=row["provider"],
                model=row["model"],
                temperature=row["temperature"],
                is_redacted=row["is_redacted"],
                created_at=row["created_at"],
            ))

        return messages

    async def get_recent_sessions(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 10,
    ) -> List[SessionSummary]:
        """Get recent sessions for user (non-semantic)."""
        pool = await self.db_pool.get_pool()

        rows = await pool.fetch(
            """
            SELECT
                id, tenant_id, user_id, title, summary,
                message_count, started_at, last_message_at
            FROM chat_sessions
            WHERE tenant_id = $1 AND user_id = $2
              AND is_deleted = FALSE
            ORDER BY last_message_at DESC NULLS LAST
            LIMIT $3
            """,
            tenant_id,
            user_id,
            limit,
        )

        return [
            SessionSummary(
                session_id=str(row["id"]),
                title=row["title"],
                summary=row["summary"],
                message_count=row["message_count"] or 0,
                started_at=row["started_at"],
            )
            for row in rows
        ]

    async def ensure_collection(self, tenant_id: str) -> bool:
        """Ensure Qdrant collection exists for tenant."""
        collection = self._get_collection_name(tenant_id)
        return await self.vector_store.ensure_collection(
            collection=collection,
            vector_size=self.vector_dimensions,
        )
