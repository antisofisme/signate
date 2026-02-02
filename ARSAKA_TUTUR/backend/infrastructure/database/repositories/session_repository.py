"""
Session repository.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from .base_repository import BaseRepository
from ....core.entities import ChatSession
from ....shared.logging import get_logger

logger = get_logger(__name__)


class SessionRepository(BaseRepository[ChatSession]):
    """
    Repository for chat session operations.

    Also provides message operations via delegation to MessageRepository
    to satisfy the MemoryStore interface.
    """

    def __init__(self, pool, message_repository=None):
        super().__init__(pool, "chat_sessions")
        self._message_repository = message_repository

    def set_message_repository(self, message_repository):
        """Set message repository for delegation."""
        self._message_repository = message_repository

    def _row_to_entity(self, row) -> ChatSession:
        """Convert database row to ChatSession."""
        return ChatSession(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            title=row["title"],
            started_at=row["started_at"],
            last_message_at=row["last_message_at"],
            message_count=row["message_count"],
            summary=row["summary"],
            summary_embedding=None,  # Not loaded by default
            summary_updated_at=row["summary_updated_at"],
            topics=row["topics"] or [],
            is_active=row["is_active"],
            is_deleted=row["is_deleted"],
            deleted_at=row["deleted_at"],
            deleted_by=row["deleted_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create(self, session: ChatSession) -> str:
        """Create a new session."""
        query = """
            INSERT INTO chat_sessions (
                id, tenant_id, user_id, title, started_at
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """

        result = await self._fetchval(
            query,
            session.id, session.tenant_id, session.user_id,
            session.title, session.started_at
        )

        logger.debug(f"Created session: {result}")
        return str(result)

    async def get_by_id(
        self,
        session_id: str,
        tenant_id: str
    ) -> Optional[ChatSession]:
        """Get session by ID."""
        query = """
            SELECT * FROM chat_sessions
            WHERE id = $1 AND tenant_id = $2
        """
        row = await self._fetchrow(query, session_id, tenant_id)
        return self._row_to_entity(row) if row else None

    async def get_active(
        self,
        session_id: str,
        tenant_id: str
    ) -> Optional[ChatSession]:
        """Get active (non-deleted) session."""
        query = """
            SELECT * FROM chat_sessions
            WHERE id = $1 AND tenant_id = $2
              AND is_active = TRUE AND is_deleted = FALSE
        """
        row = await self._fetchrow(query, session_id, tenant_id)
        return self._row_to_entity(row) if row else None

    async def list_by_user(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[ChatSession]:
        """List sessions for a user."""
        if include_deleted:
            query = """
                SELECT * FROM chat_sessions
                WHERE tenant_id = $1 AND user_id = $2
                ORDER BY last_message_at DESC NULLS LAST, created_at DESC
                LIMIT $3 OFFSET $4
            """
        else:
            query = """
                SELECT * FROM chat_sessions
                WHERE tenant_id = $1 AND user_id = $2
                  AND is_active = TRUE AND is_deleted = FALSE
                ORDER BY last_message_at DESC NULLS LAST, created_at DESC
                LIMIT $3 OFFSET $4
            """

        rows = await self._fetch(query, tenant_id, user_id, limit, offset)
        return [self._row_to_entity(row) for row in rows]

    async def update(self, session: ChatSession) -> bool:
        """Update session metadata."""
        query = """
            UPDATE chat_sessions SET
                title = $3,
                summary = $4,
                summary_updated_at = $5,
                topics = $6,
                is_active = $7,
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2
        """

        result = await self._execute(
            query,
            str(session.id), session.tenant_id,
            session.title, session.summary, session.summary_updated_at,
            session.topics, session.is_active
        )

        return "UPDATE 1" in result

    async def soft_delete(
        self,
        session_id: str,
        tenant_id: str,
        deleted_by: str
    ) -> bool:
        """Soft delete a session."""
        query = """
            UPDATE chat_sessions SET
                is_deleted = TRUE,
                is_active = FALSE,
                deleted_at = NOW(),
                deleted_by = $3,
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2 AND is_deleted = FALSE
        """

        result = await self._execute(query, session_id, tenant_id, deleted_by)
        return "UPDATE 1" in result

    async def count_by_user(
        self,
        tenant_id: str,
        user_id: str
    ) -> int:
        """Count active sessions for user."""
        query = """
            SELECT COUNT(*) FROM chat_sessions
            WHERE tenant_id = $1 AND user_id = $2
              AND is_active = TRUE AND is_deleted = FALSE
        """
        return await self._fetchval(query, tenant_id, user_id)

    # =========================================================================
    # Aliases for MemoryStore interface
    # =========================================================================

    async def count_sessions(self, tenant_id: str, user_id: str) -> int:
        """Alias for count_by_user - MemoryStore interface."""
        return await self.count_by_user(tenant_id, user_id)

    async def create_session(self, session: ChatSession) -> str:
        """Alias for create - MemoryStore interface."""
        return await self.create(session)

    async def get_session(self, session_id: str, tenant_id: str) -> Optional[ChatSession]:
        """Alias for get_active - MemoryStore interface."""
        return await self.get_active(session_id, tenant_id)

    async def list_sessions(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[ChatSession]:
        """Alias for list_by_user - MemoryStore interface."""
        return await self.list_by_user(tenant_id, user_id, limit, offset)

    async def delete_session(
        self,
        session_id: str,
        tenant_id: str,
        deleted_by: str
    ) -> bool:
        """Alias for soft_delete - MemoryStore interface."""
        return await self.soft_delete(session_id, tenant_id, deleted_by)

    async def update_session(self, session: ChatSession) -> bool:
        """Alias for update - MemoryStore interface."""
        return await self.update(session)

    # =========================================================================
    # Message Methods (delegated to MessageRepository)
    # =========================================================================

    async def save_message(self, message) -> str:
        """Save a message - MemoryStore interface (delegated)."""
        if not self._message_repository:
            raise RuntimeError("MessageRepository not set on SessionRepository")
        return await self._message_repository.create(message)

    async def get_messages(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50,
        before_id: Optional[str] = None
    ) -> List:
        """Get messages for session - MemoryStore interface (delegated)."""
        if not self._message_repository:
            raise RuntimeError("MessageRepository not set on SessionRepository")
        return await self._message_repository.get_by_session(
            session_id, tenant_id, limit, before_id
        )

    async def get_recent_for_user(
        self,
        tenant_id: str,
        user_id: str,
        days: int = 7,
        limit: int = 10
    ) -> List[ChatSession]:
        """Get recent sessions for user within N days."""
        query = """
            SELECT * FROM chat_sessions
            WHERE tenant_id = $1 AND user_id = $2
              AND is_active = TRUE AND is_deleted = FALSE
              AND created_at >= NOW() - INTERVAL '%s days'
            ORDER BY last_message_at DESC NULLS LAST
            LIMIT $3
        """ % days

        rows = await self._fetch(query, tenant_id, user_id, limit)
        return [self._row_to_entity(row) for row in rows]

    async def update_summary(
        self,
        session_id: str,
        tenant_id: str,
        summary: str,
        topics: List[dict]
    ) -> bool:
        """Update session summary and topics."""
        query = """
            UPDATE chat_sessions SET
                summary = $3,
                topics = $4,
                summary_updated_at = NOW(),
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2
        """

        result = await self._execute(
            query,
            session_id, tenant_id, summary, topics
        )

        return "UPDATE 1" in result
