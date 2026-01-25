"""
PostgreSQL Temporal Memory

Stores and retrieves time-based activity summaries.
"""

from typing import Optional, List
from datetime import date, datetime, timedelta
from uuid import uuid4

from ....core.interfaces.memory import TemporalMemory
from ....core.interfaces.storage import VectorStore
from ....core.entities import TimeSummary
from ....infrastructure.database.connection import DatabasePool
from ....shared.logging import get_logger

logger = get_logger(__name__)


class PostgresTemporalMemory(TemporalMemory):
    """
    PostgreSQL implementation of Temporal Memory.

    Time-based summaries stored in PostgreSQL.
    Optional embeddings in Qdrant for semantic search across time.

    Features:
    - Daily, weekly, monthly summaries
    - Topic aggregation
    - Trend tracking
    - Time-range queries
    """

    COLLECTION_PREFIX = "temporal"

    def __init__(
        self,
        db_pool: DatabasePool,
        vector_store: Optional[VectorStore] = None,
        vector_dimensions: int = 1536,
    ):
        self.db_pool = db_pool
        self.vector_store = vector_store
        self.vector_dimensions = vector_dimensions

    def _get_collection_name(self, tenant_id: str) -> str:
        """Get Qdrant collection name for tenant."""
        return f"{self.COLLECTION_PREFIX}_{tenant_id}"

    async def get_summary(
        self,
        tenant_id: str,
        user_id: str,
        period_type: str,
        period_start: date
    ) -> Optional[TimeSummary]:
        """Get summary for a specific time period."""
        pool = await self.db_pool.get_pool()

        row = await pool.fetchrow(
            """
            SELECT
                id, tenant_id, user_id, period_type, period_start, period_end,
                summary_text, topics, session_count, message_count, token_count,
                created_at, updated_at
            FROM memory_timeline
            WHERE tenant_id = $1 AND user_id = $2
              AND period_type = $3 AND period_start = $4
            """,
            tenant_id,
            user_id,
            period_type,
            period_start,
        )

        if not row:
            return None

        return TimeSummary(
            id=str(row["id"]),
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            period_type=row["period_type"],
            period_start=row["period_start"],
            period_end=row["period_end"],
            summary=row["summary_text"],
            topics=row["topics"] or [],
            session_count=row["session_count"] or 0,
            message_count=row["message_count"] or 0,
            token_count=row["token_count"] or 0,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create_summary(
        self,
        summary: TimeSummary,
        embedding: Optional[List[float]] = None
    ) -> str:
        """Create a new time summary."""
        pool = await self.db_pool.get_pool()

        # Generate ID if not set
        if not summary.id:
            summary.id = str(uuid4())

        # Insert or update in PostgreSQL
        await pool.execute(
            """
            INSERT INTO memory_timeline (
                id, tenant_id, user_id, period_type, period_start, period_end,
                summary_text, topics, session_count, message_count, token_count,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (tenant_id, user_id, period_type, period_start)
            DO UPDATE SET
                summary_text = EXCLUDED.summary_text,
                topics = EXCLUDED.topics,
                session_count = EXCLUDED.session_count,
                message_count = EXCLUDED.message_count,
                token_count = EXCLUDED.token_count,
                updated_at = NOW()
            """,
            summary.id,
            summary.tenant_id,
            summary.user_id,
            summary.period_type,
            summary.period_start,
            summary.period_end,
            summary.summary,
            summary.topics,
            summary.session_count,
            summary.message_count,
            summary.token_count,
            summary.created_at or datetime.utcnow(),
        )

        # Store embedding if provided and vector store available
        if embedding and self.vector_store:
            collection = self._get_collection_name(summary.tenant_id)

            await self.vector_store.ensure_collection(
                collection=collection,
                vector_size=self.vector_dimensions,
            )

            await self.vector_store.upsert(
                collection=collection,
                id=f"timeline_{summary.id}",
                vector=embedding,
                payload={
                    "tenant_id": summary.tenant_id,
                    "user_id": summary.user_id,
                    "summary_id": summary.id,
                    "period_type": summary.period_type,
                    "period_start": summary.period_start.isoformat(),
                    "period_end": summary.period_end.isoformat() if summary.period_end else None,
                    "summary": summary.summary,
                    "topics": summary.topics,
                },
            )

        logger.debug(
            f"Created {summary.period_type} summary for user {summary.user_id} "
            f"starting {summary.period_start}"
        )
        return summary.id

    async def get_summaries_range(
        self,
        tenant_id: str,
        user_id: str,
        period_type: str,
        start_date: date,
        end_date: date
    ) -> List[TimeSummary]:
        """Get summaries within date range."""
        pool = await self.db_pool.get_pool()

        rows = await pool.fetch(
            """
            SELECT
                id, tenant_id, user_id, period_type, period_start, period_end,
                summary_text, topics, session_count, message_count, token_count,
                created_at, updated_at
            FROM memory_timeline
            WHERE tenant_id = $1 AND user_id = $2
              AND period_type = $3
              AND period_start >= $4 AND period_start <= $5
            ORDER BY period_start ASC
            """,
            tenant_id,
            user_id,
            period_type,
            start_date,
            end_date,
        )

        return [
            TimeSummary(
                id=str(row["id"]),
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
                period_type=row["period_type"],
                period_start=row["period_start"],
                period_end=row["period_end"],
                summary=row["summary_text"],
                topics=row["topics"] or [],
                session_count=row["session_count"] or 0,
                message_count=row["message_count"] or 0,
                token_count=row["token_count"] or 0,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    async def search_summaries(
        self,
        tenant_id: str,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[TimeSummary]:
        """Search summaries semantically."""
        if not self.vector_store:
            return []

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

            # Fetch full summaries from PostgreSQL
            summary_ids = [
                result.metadata.get("summary_id")
                for result in results
                if result.metadata.get("summary_id")
            ]

            if not summary_ids:
                return []

            pool = await self.db_pool.get_pool()
            rows = await pool.fetch(
                """
                SELECT
                    id, tenant_id, user_id, period_type, period_start, period_end,
                    summary_text, topics, session_count, message_count, token_count,
                    created_at, updated_at
                FROM memory_timeline
                WHERE id = ANY($1::uuid[])
                ORDER BY period_start DESC
                """,
                summary_ids,
            )

            return [
                TimeSummary(
                    id=str(row["id"]),
                    tenant_id=row["tenant_id"],
                    user_id=row["user_id"],
                    period_type=row["period_type"],
                    period_start=row["period_start"],
                    period_end=row["period_end"],
                    summary=row["summary_text"],
                    topics=row["topics"] or [],
                    session_count=row["session_count"] or 0,
                    message_count=row["message_count"] or 0,
                    token_count=row["token_count"] or 0,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

        except Exception as e:
            logger.warning(f"Temporal search failed: {e}")
            return []

    async def get_recent_activity(
        self,
        tenant_id: str,
        user_id: str,
        days: int = 7,
    ) -> dict:
        """Get recent activity statistics."""
        pool = await self.db_pool.get_pool()

        start_date = date.today() - timedelta(days=days)

        row = await pool.fetchrow(
            """
            SELECT
                COUNT(DISTINCT s.id) as session_count,
                COUNT(m.id) as message_count,
                COALESCE(SUM(m.token_count), 0) as token_count
            FROM chat_sessions s
            LEFT JOIN chat_messages m ON m.session_id = s.id
            WHERE s.tenant_id = $1 AND s.user_id = $2
              AND s.started_at >= $3
              AND s.is_deleted = FALSE
            """,
            tenant_id,
            user_id,
            start_date,
        )

        return {
            "period_days": days,
            "session_count": row["session_count"] or 0,
            "message_count": row["message_count"] or 0,
            "token_count": row["token_count"] or 0,
        }

    async def get_topics_for_period(
        self,
        tenant_id: str,
        user_id: str,
        period_type: str,
        period_start: date,
    ) -> List[str]:
        """Get topics discussed in a time period."""
        summary = await self.get_summary(tenant_id, user_id, period_type, period_start)
        if summary:
            return summary.topics
        return []

    @staticmethod
    def get_period_dates(period_type: str, reference_date: date = None) -> tuple[date, date]:
        """Calculate period start and end dates."""
        ref = reference_date or date.today()

        if period_type == "day":
            return ref, ref

        elif period_type == "week":
            # Week starts Monday
            start = ref - timedelta(days=ref.weekday())
            end = start + timedelta(days=6)
            return start, end

        elif period_type == "month":
            start = ref.replace(day=1)
            # Last day of month
            if ref.month == 12:
                end = ref.replace(year=ref.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = ref.replace(month=ref.month + 1, day=1) - timedelta(days=1)
            return start, end

        else:
            raise ValueError(f"Unknown period type: {period_type}")
