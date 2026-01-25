"""
Fact Extractor Worker

Background worker that extracts facts from conversations.
"""

from typing import List, Optional
from datetime import datetime, timedelta

from .base_worker import ScheduledWorker
from ..core.entities import RequestContext, ChatMessage
from ..core.services.memory_manager import MemoryManager
from ..infrastructure.database.repositories import SessionRepository, MessageRepository
from ..shared.logging import get_logger

logger = get_logger(__name__)


class FactExtractorWorker(ScheduledWorker):
    """
    Extracts user facts from completed conversations.

    Schedule: Every 15 minutes
    Process:
    1. Find sessions that ended recently (idle > 30 min)
    2. Extract facts from session messages
    3. Store facts in semantic memory
    4. Mark session as processed
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
        schedule_seconds: int = 900,  # 15 minutes
        idle_threshold_minutes: int = 30,
        batch_size: int = 10,
    ):
        super().__init__(
            name="fact_extractor",
            schedule_seconds=schedule_seconds,
        )
        self.memory_manager = memory_manager
        self.session_repository = session_repository
        self.message_repository = message_repository
        self.idle_threshold_minutes = idle_threshold_minutes
        self.batch_size = batch_size

    async def process(self) -> None:
        """Find and process idle sessions for fact extraction."""
        logger.info("Starting fact extraction run...")

        # Find idle sessions that haven't been processed
        idle_threshold = datetime.utcnow() - timedelta(minutes=self.idle_threshold_minutes)

        sessions = await self._get_unprocessed_sessions(idle_threshold)

        if not sessions:
            logger.debug("No sessions to process for fact extraction")
            return

        logger.info(f"Processing {len(sessions)} sessions for fact extraction")

        processed = 0
        for session in sessions[:self.batch_size]:
            try:
                await self._process_session(session)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to extract facts from session {session['id']}: {e}")

        logger.info(f"Fact extraction complete: {processed}/{len(sessions)} sessions processed")

    async def _get_unprocessed_sessions(self, idle_threshold: datetime) -> List[dict]:
        """Get sessions that need fact extraction."""
        # Sessions that:
        # 1. Last activity before idle_threshold
        # 2. Have not been processed for facts (facts_extracted_at IS NULL)
        # 3. Have at least some messages

        query = """
            SELECT s.id, s.tenant_id, s.user_id, s.title,
                   s.updated_at, s.message_count
            FROM chat_sessions s
            WHERE s.updated_at < $1
              AND s.facts_extracted_at IS NULL
              AND s.message_count >= 3
              AND s.is_deleted = FALSE
            ORDER BY s.updated_at DESC
            LIMIT $2
        """

        pool = self.session_repository._db_pool.pool
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, idle_threshold, self.batch_size * 2)
            return [dict(row) for row in rows]

    async def _process_session(self, session: dict) -> None:
        """Extract facts from a single session."""
        session_id = str(session["id"])
        tenant_id = session["tenant_id"]
        user_id = session["user_id"]

        logger.debug(f"Extracting facts from session {session_id}")

        # Get session messages
        messages = await self.message_repository.get_by_session(
            session_id=session_id,
            tenant_id=tenant_id,
            limit=100,
        )

        if not messages:
            logger.debug(f"No messages in session {session_id}")
            await self._mark_session_processed(session_id)
            return

        # Create request context
        ctx = RequestContext(
            request_id=f"worker-fact-{session_id}",
            tenant_id=tenant_id,
            user_id=user_id,
            tenant_config=None,  # Worker doesn't need full config
        )

        # Extract and store facts
        fact_ids = await self.memory_manager.extract_and_store_facts(
            ctx=ctx,
            messages=messages,
            session_id=session_id,
        )

        logger.info(f"Extracted {len(fact_ids)} facts from session {session_id}")

        # Mark session as processed
        await self._mark_session_processed(session_id)

    async def _mark_session_processed(self, session_id: str) -> None:
        """Mark session as processed for fact extraction."""
        query = """
            UPDATE chat_sessions
            SET facts_extracted_at = NOW()
            WHERE id = $1
        """

        pool = self.session_repository._db_pool.pool
        async with pool.acquire() as conn:
            await conn.execute(query, session_id)


class RealtimeFactExtractor:
    """
    Real-time fact extraction triggered after each message.

    Alternative to scheduled extraction for immediate processing.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        min_messages: int = 5,
        extract_every_n: int = 10,
    ):
        self.memory_manager = memory_manager
        self.min_messages = min_messages
        self.extract_every_n = extract_every_n
        self._message_counts: dict = {}

    async def on_message(
        self,
        ctx: RequestContext,
        session_id: str,
        messages: List[ChatMessage],
    ) -> Optional[List[str]]:
        """
        Called after each message.

        Extracts facts if threshold reached.
        """
        # Track message count per session
        count = self._message_counts.get(session_id, 0) + 1
        self._message_counts[session_id] = count

        # Check if we should extract
        if count < self.min_messages:
            return None

        if count % self.extract_every_n != 0:
            return None

        # Extract from recent messages only
        recent = messages[-self.extract_every_n:]

        try:
            fact_ids = await self.memory_manager.extract_and_store_facts(
                ctx=ctx,
                messages=recent,
                session_id=session_id,
            )
            logger.debug(f"Real-time extraction: {len(fact_ids)} facts from session {session_id}")
            return fact_ids
        except Exception as e:
            logger.warning(f"Real-time fact extraction failed: {e}")
            return None

    def clear_session(self, session_id: str) -> None:
        """Clear tracking for a session."""
        self._message_counts.pop(session_id, None)
