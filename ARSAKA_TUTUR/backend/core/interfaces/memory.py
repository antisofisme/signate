"""
Memory interfaces for the 4-layer memory system.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List

from ..entities import (
    ChatMessage,
    ChatSession,
    UserFact,
    TimeSummary,
    SessionSummary
)


class WorkingMemory(ABC):
    """
    Interface for current session memory (in-memory).

    Holds the active conversation context for the current session.
    """

    @abstractmethod
    def add(self, message: ChatMessage) -> None:
        """
        Add message to working memory.

        Args:
            message: ChatMessage to add
        """
        pass

    @abstractmethod
    def get_recent(self, limit: int = 10) -> List[ChatMessage]:
        """
        Get recent messages.

        Args:
            limit: Max messages to return

        Returns:
            List of recent ChatMessage
        """
        pass

    @abstractmethod
    def get_all(self) -> List[ChatMessage]:
        """
        Get all messages in working memory.

        Returns:
            All ChatMessage in order
        """
        pass

    @abstractmethod
    def get_token_count(self) -> int:
        """
        Get total token count of working memory.

        Returns:
            Token count
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear working memory."""
        pass

    @abstractmethod
    def truncate_to_tokens(self, max_tokens: int) -> None:
        """
        Truncate memory to fit within token limit.

        Removes oldest messages first.

        Args:
            max_tokens: Maximum tokens to keep
        """
        pass


class EpisodicMemory(ABC):
    """
    Interface for session-based memory (PostgreSQL + Qdrant).

    Stores and retrieves past session information.
    """

    @abstractmethod
    async def save_session_summary(
        self,
        session: ChatSession,
        embedding: List[float]
    ) -> str:
        """
        Save session with embedding for retrieval.

        Args:
            session: ChatSession with summary
            embedding: Session summary embedding

        Returns:
            Session ID
        """
        pass

    @abstractmethod
    async def search_sessions(
        self,
        tenant_id: str,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SessionSummary]:
        """
        Search for similar past sessions.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            query_embedding: Query embedding vector
            top_k: Number of results

        Returns:
            List of SessionSummary with scores
        """
        pass

    @abstractmethod
    async def get_session_messages(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Get messages from a specific session.

        Args:
            session_id: Session UUID
            tenant_id: Tenant ID
            limit: Max messages

        Returns:
            List of ChatMessage
        """
        pass


class SemanticMemory(ABC):
    """
    Interface for user facts/knowledge (PostgreSQL + Qdrant).

    Stores and retrieves persistent user information.
    """

    @abstractmethod
    async def add_fact(
        self,
        fact: UserFact,
        embedding: List[float]
    ) -> str:
        """
        Add a new user fact.

        Args:
            fact: UserFact entity
            embedding: Fact content embedding

        Returns:
            Fact ID
        """
        pass

    @abstractmethod
    async def get_relevant_facts(
        self,
        tenant_id: str,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 10,
        min_confidence: float = 0.5
    ) -> List[UserFact]:
        """
        Get facts relevant to query.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            query_embedding: Query embedding
            top_k: Max results
            min_confidence: Minimum confidence threshold

        Returns:
            List of relevant UserFact
        """
        pass

    @abstractmethod
    async def get_all_facts(
        self,
        tenant_id: str,
        user_id: str,
        fact_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[UserFact]:
        """
        Get all user facts.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            fact_type: Filter by type
            active_only: Only active facts

        Returns:
            List of UserFact
        """
        pass

    @abstractmethod
    async def update_fact_confidence(
        self,
        fact_id: str,
        tenant_id: str,
        new_confidence: float
    ) -> bool:
        """
        Update fact confidence score.

        Args:
            fact_id: Fact UUID
            tenant_id: Tenant ID
            new_confidence: New confidence (0.0-1.0)

        Returns:
            True if updated
        """
        pass

    @abstractmethod
    async def deactivate_fact(
        self,
        fact_id: str,
        tenant_id: str
    ) -> bool:
        """
        Deactivate a fact (soft delete).

        Args:
            fact_id: Fact UUID
            tenant_id: Tenant ID

        Returns:
            True if deactivated
        """
        pass


class TemporalMemory(ABC):
    """
    Interface for time-based summaries.

    Aggregates user activity over time periods.
    """

    @abstractmethod
    async def get_summary(
        self,
        tenant_id: str,
        user_id: str,
        period_type: str,
        period_start: date
    ) -> Optional[TimeSummary]:
        """
        Get summary for time period.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            period_type: 'day', 'week', 'month'
            period_start: Start date of period

        Returns:
            TimeSummary or None
        """
        pass

    @abstractmethod
    async def create_summary(
        self,
        summary: TimeSummary,
        embedding: List[float]
    ) -> str:
        """
        Create a new time summary.

        Args:
            summary: TimeSummary entity
            embedding: Summary embedding

        Returns:
            Summary ID
        """
        pass

    @abstractmethod
    async def get_summaries_range(
        self,
        tenant_id: str,
        user_id: str,
        period_type: str,
        start_date: date,
        end_date: date
    ) -> List[TimeSummary]:
        """
        Get summaries within date range.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            period_type: 'day', 'week', 'month'
            start_date: Range start
            end_date: Range end

        Returns:
            List of TimeSummary
        """
        pass
