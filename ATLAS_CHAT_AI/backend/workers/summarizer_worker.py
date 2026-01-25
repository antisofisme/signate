"""
Summarizer Worker

Background worker that summarizes completed sessions.
"""

from typing import List, Optional
from datetime import datetime, timedelta

from .base_worker import ScheduledWorker
from ..core.entities import ChatSession, RequestContext
from ..core.services.memory_manager import MemoryManager
from ..infrastructure.database.repositories import SessionRepository, MessageRepository
from ..shared.logging import get_logger

logger = get_logger(__name__)


class SummarizerWorker(ScheduledWorker):
    """
    Summarizes completed conversation sessions.

    Schedule: Every 30 minutes
    Process:
    1. Find sessions that ended recently (idle > 1 hour)
    2. Generate summary from messages
    3. Store in episodic memory with embedding
    4. Mark session as summarized
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
        schedule_seconds: int = 1800,  # 30 minutes
        idle_threshold_minutes: int = 60,
        batch_size: int = 10,
    ):
        super().__init__(
            name="summarizer",
            schedule_seconds=schedule_seconds,
        )
        self.memory_manager = memory_manager
        self.session_repository = session_repository
        self.message_repository = message_repository
        self.idle_threshold_minutes = idle_threshold_minutes
        self.batch_size = batch_size

    async def process(self) -> None:
        """Find and summarize idle sessions."""
        logger.info("Starting session summarization run...")

        # Find idle sessions that haven't been summarized
        idle_threshold = datetime.utcnow() - timedelta(minutes=self.idle_threshold_minutes)

        sessions = await self._get_unsummarized_sessions(idle_threshold)

        if not sessions:
            logger.debug("No sessions to summarize")
            return

        logger.info(f"Summarizing {len(sessions)} sessions")

        processed = 0
        for session_data in sessions[:self.batch_size]:
            try:
                await self._summarize_session(session_data)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to summarize session {session_data['id']}: {e}")

        logger.info(f"Summarization complete: {processed}/{len(sessions)} sessions processed")

    async def _get_unsummarized_sessions(self, idle_threshold: datetime) -> List[dict]:
        """Get sessions that need summarization."""
        query = """
            SELECT s.id, s.tenant_id, s.user_id, s.title,
                   s.started_at, s.updated_at, s.message_count
            FROM chat_sessions s
            WHERE s.updated_at < $1
              AND s.summary IS NULL
              AND s.message_count >= 2
              AND s.is_deleted = FALSE
            ORDER BY s.updated_at DESC
            LIMIT $2
        """

        pool = self.session_repository._db_pool.pool
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, idle_threshold, self.batch_size * 2)
            return [dict(row) for row in rows]

    async def _summarize_session(self, session_data: dict) -> None:
        """Summarize a single session."""
        session_id = str(session_data["id"])
        tenant_id = session_data["tenant_id"]
        user_id = session_data["user_id"]

        logger.debug(f"Summarizing session {session_id}")

        # Get session messages
        messages = await self.message_repository.get_by_session(
            session_id=session_id,
            tenant_id=tenant_id,
            limit=200,  # More messages for summarization
        )

        if not messages:
            logger.debug(f"No messages in session {session_id}")
            return

        # Create ChatSession object
        session = ChatSession(
            id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=session_data.get("title"),
            started_at=session_data.get("started_at"),
            message_count=session_data.get("message_count", len(messages)),
        )

        # Save session summary (generates summary and embedding)
        await self.memory_manager.save_session_summary(
            session=session,
            messages=messages,
        )

        # Update session record with summary
        await self._update_session_summary(session_id, session.summary)

        logger.info(f"Summarized session {session_id}: {len(session.summary or '')} chars")

    async def _update_session_summary(self, session_id: str, summary: Optional[str]) -> None:
        """Update session with generated summary."""
        query = """
            UPDATE chat_sessions
            SET summary = $2,
                summarized_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
        """

        pool = self.session_repository._db_pool.pool
        async with pool.acquire() as conn:
            await conn.execute(query, session_id, summary)


class IncrementalSummarizer:
    """
    Incremental summarization during active sessions.

    Updates session summary as conversation progresses.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        update_every_n: int = 10,
    ):
        self.memory_manager = memory_manager
        self.update_every_n = update_every_n
        self._message_counts: dict = {}
        self._summaries: dict = {}

    async def on_message(
        self,
        ctx: RequestContext,
        session_id: str,
        messages: List,
        current_summary: Optional[str] = None,
    ) -> Optional[str]:
        """
        Called after each message to potentially update summary.

        Returns new summary if updated, None otherwise.
        """
        count = self._message_counts.get(session_id, 0) + 1
        self._message_counts[session_id] = count

        # Only update periodically
        if count < self.update_every_n:
            return None

        if count % self.update_every_n != 0:
            return None

        # Get or create summarizer
        summarizer = self.memory_manager.summarizer
        if not summarizer:
            return None

        try:
            # Use previous summary if available
            prev_summary = self._summaries.get(session_id) or current_summary

            if prev_summary:
                # Incremental update
                new_summary = await summarizer.summarize_incremental(
                    previous_summary=prev_summary,
                    new_messages=messages[-self.update_every_n:],
                    max_length=500,
                )
            else:
                # Full summarization
                new_summary = await summarizer.summarize(
                    messages=messages,
                    max_length=500,
                )

            self._summaries[session_id] = new_summary
            logger.debug(f"Incremental summary for session {session_id}: {len(new_summary)} chars")
            return new_summary

        except Exception as e:
            logger.warning(f"Incremental summarization failed: {e}")
            return None

    def get_summary(self, session_id: str) -> Optional[str]:
        """Get current summary for session."""
        return self._summaries.get(session_id)

    def clear_session(self, session_id: str) -> None:
        """Clear tracking for a session."""
        self._message_counts.pop(session_id, None)
        self._summaries.pop(session_id, None)
