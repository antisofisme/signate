"""
In-Memory Working Memory

Holds the current conversation context for active sessions.
"""

from typing import List, Optional
from collections import deque
from threading import Lock

from ....core.interfaces.memory import WorkingMemory
from ....core.entities import ChatMessage
from ....shared.logging import get_logger
from ....shared.tokens import count_tokens

logger = get_logger(__name__)


class InMemoryWorkingMemory(WorkingMemory):
    """
    In-memory implementation of Working Memory.

    Features:
    - Fast O(1) append and O(n) retrieval
    - Thread-safe with locks
    - Automatic token tracking
    - LRU-style truncation

    Typically one instance per active session.
    """

    def __init__(
        self,
        session_id: str,
        max_messages: int = 100,
        max_tokens: int = 8000,
    ):
        self.session_id = session_id
        self.max_messages = max_messages
        self.max_tokens = max_tokens

        self._messages: deque[ChatMessage] = deque(maxlen=max_messages)
        self._token_count: int = 0
        self._lock = Lock()

    def add(self, message: ChatMessage) -> None:
        """Add message to working memory."""
        with self._lock:
            # Calculate tokens for this message
            message_tokens = count_tokens(message.content)
            if message.token_count is None:
                message.token_count = message_tokens

            self._messages.append(message)
            self._token_count += message_tokens

            # Auto-truncate if over token limit
            if self._token_count > self.max_tokens:
                self._truncate_oldest()

            logger.debug(
                f"Working memory: added message, total={len(self._messages)}, "
                f"tokens={self._token_count}"
            )

    def get_recent(self, limit: int = 10) -> List[ChatMessage]:
        """Get recent messages."""
        with self._lock:
            if limit >= len(self._messages):
                return list(self._messages)
            return list(self._messages)[-limit:]

    def get_all(self) -> List[ChatMessage]:
        """Get all messages in working memory."""
        with self._lock:
            return list(self._messages)

    def get_token_count(self) -> int:
        """Get total token count."""
        with self._lock:
            return self._token_count

    def clear(self) -> None:
        """Clear working memory."""
        with self._lock:
            self._messages.clear()
            self._token_count = 0
            logger.debug(f"Working memory cleared for session {self.session_id}")

    def truncate_to_tokens(self, max_tokens: int) -> None:
        """Truncate to fit within token limit."""
        with self._lock:
            while self._token_count > max_tokens and self._messages:
                removed = self._messages.popleft()
                self._token_count -= (removed.token_count or count_tokens(removed.content))

            logger.debug(
                f"Working memory truncated to {len(self._messages)} messages, "
                f"{self._token_count} tokens"
            )

    def _truncate_oldest(self) -> None:
        """Remove oldest messages to fit within token limit."""
        while self._token_count > self.max_tokens and self._messages:
            removed = self._messages.popleft()
            self._token_count -= (removed.token_count or count_tokens(removed.content))

    def get_context_for_llm(self, max_tokens: Optional[int] = None) -> List[ChatMessage]:
        """
        Get messages formatted for LLM context.

        Ensures total tokens don't exceed limit.
        """
        limit = max_tokens or self.max_tokens

        with self._lock:
            if self._token_count <= limit:
                return list(self._messages)

            # Build from most recent, staying under limit
            result = []
            token_sum = 0

            for msg in reversed(self._messages):
                msg_tokens = msg.token_count or count_tokens(msg.content)
                if token_sum + msg_tokens > limit:
                    break
                result.insert(0, msg)
                token_sum += msg_tokens

            return result

    @property
    def message_count(self) -> int:
        """Get number of messages."""
        return len(self._messages)

    @property
    def is_empty(self) -> bool:
        """Check if working memory is empty."""
        return len(self._messages) == 0


class WorkingMemoryManager:
    """
    Manages working memory instances for multiple sessions.

    Thread-safe session registry with automatic cleanup.
    """

    def __init__(
        self,
        max_messages: int = 100,
        max_tokens: int = 8000,
        max_sessions: int = 1000,
    ):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.max_sessions = max_sessions

        self._sessions: dict[str, InMemoryWorkingMemory] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str) -> InMemoryWorkingMemory:
        """Get or create working memory for session."""
        with self._lock:
            if session_id not in self._sessions:
                # Check if we need to evict old sessions
                if len(self._sessions) >= self.max_sessions:
                    self._evict_oldest()

                self._sessions[session_id] = InMemoryWorkingMemory(
                    session_id=session_id,
                    max_messages=self.max_messages,
                    max_tokens=self.max_tokens,
                )
                logger.debug(f"Created working memory for session {session_id}")

            return self._sessions[session_id]

    def remove(self, session_id: str) -> bool:
        """Remove working memory for session."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.debug(f"Removed working memory for session {session_id}")
                return True
            return False

    def clear_all(self) -> int:
        """Clear all working memory sessions."""
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            logger.info(f"Cleared {count} working memory sessions")
            return count

    def _evict_oldest(self) -> None:
        """Evict oldest session (simple LRU approximation)."""
        if self._sessions:
            oldest_key = next(iter(self._sessions))
            del self._sessions[oldest_key]
            logger.debug(f"Evicted working memory for session {oldest_key}")

    @property
    def active_sessions(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)
