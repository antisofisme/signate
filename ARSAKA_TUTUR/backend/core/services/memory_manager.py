"""
Memory Manager

Coordinates the 4-layer memory system.
"""

from typing import Optional, List
from datetime import date, datetime

from ..entities import (
    RequestContext,
    ChatMessage,
    ChatSession,
    UserFact,
    TimeSummary,
    SessionSummary,
    ExtractedFact,
    FactType,
)
from ..interfaces.memory import (
    WorkingMemory,
    EpisodicMemory,
    SemanticMemory,
    TemporalMemory,
)
from ..interfaces.extraction import FactExtractor, Summarizer
from ..interfaces.ai_providers import EmbeddingProvider
from ...shared.logging import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """
    Coordinates all 4 memory layers.

    Layers:
    1. Working Memory - Current session context (in-memory)
    2. Episodic Memory - Past session summaries (PostgreSQL + Qdrant)
    3. Semantic Memory - User facts/knowledge (PostgreSQL + Qdrant)
    4. Temporal Memory - Time-based summaries (PostgreSQL)

    Features:
    - Unified context assembly for LLM
    - Automatic fact extraction
    - Session summarization
    - Memory consolidation
    """

    def __init__(
        self,
        working_memory_manager,  # WorkingMemoryManager
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
        temporal_memory: TemporalMemory,
        embedding_provider: EmbeddingProvider,
        fact_extractor: Optional[FactExtractor] = None,
        summarizer: Optional[Summarizer] = None,
    ):
        self.working_memory_manager = working_memory_manager
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        self.temporal_memory = temporal_memory
        self.embedding_provider = embedding_provider
        self.fact_extractor = fact_extractor
        self.summarizer = summarizer

    # =========================================================================
    # Working Memory (Layer 1)
    # =========================================================================

    def get_working_memory(self, session_id: str) -> WorkingMemory:
        """Get working memory for session."""
        return self.working_memory_manager.get_or_create(session_id)

    def add_to_working_memory(self, session_id: str, message: ChatMessage) -> None:
        """Add message to working memory."""
        wm = self.get_working_memory(session_id)
        wm.add(message)

    def get_working_context(
        self,
        session_id: str,
        max_tokens: int = 4000
    ) -> List[ChatMessage]:
        """Get recent messages from working memory."""
        wm = self.get_working_memory(session_id)
        return wm.get_context_for_llm(max_tokens)

    def clear_working_memory(self, session_id: str) -> None:
        """Clear working memory for session."""
        self.working_memory_manager.remove(session_id)

    # =========================================================================
    # Episodic Memory (Layer 2)
    # =========================================================================

    async def save_session_summary(
        self,
        session: ChatSession,
        messages: Optional[List[ChatMessage]] = None,
    ) -> str:
        """
        Summarize and save session to episodic memory.

        Args:
            session: ChatSession to summarize
            messages: Optional messages (fetched if not provided)
        """
        # Generate summary if summarizer available
        if self.summarizer and messages:
            session.summary = await self.summarizer.summarize(messages)

        # Generate embedding for summary
        summary_text = session.summary or session.title or "No summary"
        embedding = await self.embedding_provider.embed(summary_text)

        # Save to episodic memory
        session_id = await self.episodic_memory.save_session_summary(
            session=session,
            embedding=embedding,
        )

        logger.info(f"Saved session summary for {session_id}")
        return session_id

    async def search_past_sessions(
        self,
        ctx: RequestContext,
        query: str,
        top_k: int = 5,
    ) -> List[SessionSummary]:
        """Search for relevant past sessions."""
        # Embed query
        query_embedding = await self.embedding_provider.embed(query)

        # Search episodic memory
        return await self.episodic_memory.search_sessions(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )

    async def get_session_messages(
        self,
        ctx: RequestContext,
        session_id: str,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Get messages from a past session."""
        return await self.episodic_memory.get_session_messages(
            session_id=session_id,
            tenant_id=ctx.tenant_id,
            limit=limit,
        )

    # =========================================================================
    # Semantic Memory (Layer 3)
    # =========================================================================

    async def add_fact(
        self,
        ctx: RequestContext,
        fact: UserFact,
    ) -> str:
        """Add a user fact to semantic memory."""
        # Generate embedding
        embedding = await self.embedding_provider.embed(fact.content)

        # Add to semantic memory
        return await self.semantic_memory.add_fact(fact, embedding)

    async def extract_and_store_facts(
        self,
        ctx: RequestContext,
        messages: List[ChatMessage],
        session_id: Optional[str] = None,
    ) -> List[str]:
        """
        Extract facts from messages and store them.

        Returns list of created fact IDs.
        """
        if not self.fact_extractor:
            return []

        # Get existing facts to avoid duplicates
        existing_facts = await self.semantic_memory.get_all_facts(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            active_only=True,
        )

        # Extract new facts
        extracted = await self.fact_extractor.extract(messages, existing_facts)

        if not extracted:
            return []

        # Store each fact
        fact_ids = []
        for ext_fact in extracted:
            # Check for contradictions
            if existing_facts:
                contradicted = await self.fact_extractor.check_contradiction(
                    ext_fact.content,
                    existing_facts,
                )
                # Deactivate contradicted facts
                for fact_id in contradicted:
                    await self.semantic_memory.deactivate_fact(fact_id, ctx.tenant_id)

            # Create UserFact from ExtractedFact
            fact = UserFact(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                fact_type=ext_fact.fact_type,
                content=ext_fact.content,
                confidence=ext_fact.confidence,
                source_session_id=session_id,
                source_message_id=ext_fact.source_message_id,
            )

            fact_id = await self.add_fact(ctx, fact)
            fact_ids.append(fact_id)

        logger.info(f"Extracted and stored {len(fact_ids)} facts for user {ctx.user_id}")
        return fact_ids

    async def get_relevant_facts(
        self,
        ctx: RequestContext,
        query: str,
        top_k: int = 10,
        min_confidence: float = 0.5,
    ) -> List[UserFact]:
        """Get facts relevant to query."""
        query_embedding = await self.embedding_provider.embed(query)

        return await self.semantic_memory.get_relevant_facts(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            query_embedding=query_embedding,
            top_k=top_k,
            min_confidence=min_confidence,
        )

    async def get_all_user_facts(
        self,
        ctx: RequestContext,
        fact_type: Optional[FactType] = None,
        active_only: bool = True,
    ) -> List[UserFact]:
        """Get all facts for a user."""
        return await self.semantic_memory.get_all_facts(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            fact_type=fact_type.value if fact_type else None,
            active_only=active_only,
        )

    async def deactivate_fact(self, ctx: RequestContext, fact_id: str) -> bool:
        """Deactivate a user fact."""
        return await self.semantic_memory.deactivate_fact(
            fact_id=fact_id,
            tenant_id=ctx.tenant_id,
        )

    # =========================================================================
    # Temporal Memory (Layer 4)
    # =========================================================================

    async def create_temporal_summary(
        self,
        ctx: RequestContext,
        period_type: str,  # 'day', 'week', 'month'
        period_start: date,
        messages: List[ChatMessage],
    ) -> str:
        """Create a temporal summary for a time period."""
        # Generate summary
        summary_text = ""
        topics = []

        if self.summarizer:
            summary_text = await self.summarizer.summarize(messages)
            topics = await self.summarizer.extract_topics(messages)

        # Calculate stats
        session_ids = set(str(m.session_id) for m in messages)
        token_count = sum(m.token_count or 0 for m in messages)

        # Create TimeSummary
        from ..interfaces.memory import TemporalMemory
        period_end = self._calculate_period_end(period_type, period_start)

        summary = TimeSummary(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            summary=summary_text,
            topics=topics,
            session_count=len(session_ids),
            message_count=len(messages),
            token_count=token_count,
        )

        # Generate embedding
        embedding = await self.embedding_provider.embed(summary_text) if summary_text else None

        # Store
        return await self.temporal_memory.create_summary(summary, embedding)

    async def get_temporal_summary(
        self,
        ctx: RequestContext,
        period_type: str,
        period_start: date,
    ) -> Optional[TimeSummary]:
        """Get temporal summary for a period."""
        return await self.temporal_memory.get_summary(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            period_type=period_type,
            period_start=period_start,
        )

    async def get_activity_timeline(
        self,
        ctx: RequestContext,
        period_type: str,
        start_date: date,
        end_date: date,
    ) -> List[TimeSummary]:
        """Get activity timeline for date range."""
        return await self.temporal_memory.get_summaries_range(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
        )

    # =========================================================================
    # Unified Context Assembly
    # =========================================================================

    async def assemble_context(
        self,
        ctx: RequestContext,
        session_id: str,
        query: str,
        max_tokens: int = 6000,
    ) -> dict:
        """
        Assemble unified context from all memory layers.

        Returns:
            {
                "working_messages": List[ChatMessage],
                "relevant_facts": List[UserFact],
                "relevant_sessions": List[SessionSummary],
                "recent_summary": Optional[str],
                "total_tokens": int,
            }
        """
        result = {
            "working_messages": [],
            "relevant_facts": [],
            "relevant_sessions": [],
            "recent_summary": None,
            "total_tokens": 0,
        }

        # 1. Working memory (recent conversation)
        wm = self.get_working_memory(session_id)
        result["working_messages"] = wm.get_context_for_llm(max_tokens // 2)
        result["total_tokens"] += wm.get_token_count()

        # 2. Relevant facts (semantic memory)
        try:
            result["relevant_facts"] = await self.get_relevant_facts(
                ctx=ctx,
                query=query,
                top_k=5,
                min_confidence=0.6,
            )
        except Exception as e:
            logger.warning(f"Failed to get relevant facts: {e}")

        # 3. Relevant past sessions (episodic memory)
        try:
            result["relevant_sessions"] = await self.search_past_sessions(
                ctx=ctx,
                query=query,
                top_k=3,
            )
        except Exception as e:
            logger.warning(f"Failed to search past sessions: {e}")

        # 4. Recent temporal summary
        try:
            today = date.today()
            summary = await self.get_temporal_summary(ctx, "week", today)
            if summary:
                result["recent_summary"] = summary.summary
        except Exception as e:
            logger.warning(f"Failed to get temporal summary: {e}")

        return result

    def format_context_for_llm(self, context: dict) -> str:
        """Format assembled context as text for LLM system prompt."""
        parts = []

        # Facts section
        if context.get("relevant_facts"):
            parts.append("## Known Facts About User")
            for fact in context["relevant_facts"][:5]:
                parts.append(f"- {fact.content}")
            parts.append("")

        # Past sessions section
        if context.get("relevant_sessions"):
            parts.append("## Relevant Past Conversations")
            for session in context["relevant_sessions"][:3]:
                if session.summary:
                    parts.append(f"- {session.summary[:200]}")
            parts.append("")

        # Recent activity
        if context.get("recent_summary"):
            parts.append("## Recent Activity")
            parts.append(context["recent_summary"][:500])
            parts.append("")

        return "\n".join(parts) if parts else ""

    # =========================================================================
    # Helpers
    # =========================================================================

    def _calculate_period_end(self, period_type: str, period_start: date) -> date:
        """Calculate period end date."""
        from datetime import timedelta

        if period_type == "day":
            return period_start
        elif period_type == "week":
            return period_start + timedelta(days=6)
        elif period_type == "month":
            # Last day of month
            if period_start.month == 12:
                return date(period_start.year + 1, 1, 1) - timedelta(days=1)
            return date(period_start.year, period_start.month + 1, 1) - timedelta(days=1)
        else:
            return period_start
