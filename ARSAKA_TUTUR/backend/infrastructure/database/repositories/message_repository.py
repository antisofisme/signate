"""
Message repository.

Messages are APPEND-ONLY per CHAT-LAW-006.
"""

from typing import Optional, List
from uuid import UUID
import json

from .base_repository import BaseRepository
from ....core.entities import ChatMessage, Role
from ....shared.logging import get_logger

logger = get_logger(__name__)


class MessageRepository(BaseRepository[ChatMessage]):
    """
    Repository for chat message operations.

    IMPORTANT: Messages are APPEND-ONLY per CHAT-LAW-006.
    Only redaction is allowed (setting is_redacted = TRUE).
    """

    def __init__(self, pool):
        super().__init__(pool, "chat_messages")

    def _row_to_entity(self, row) -> ChatMessage:
        """Convert database row to ChatMessage."""
        # Parse retrieved_doc_ids - might be JSON string from JSONB column
        retrieved_doc_ids = row["retrieved_doc_ids"]
        if isinstance(retrieved_doc_ids, str):
            retrieved_doc_ids = json.loads(retrieved_doc_ids) if retrieved_doc_ids else []
        elif retrieved_doc_ids is None:
            retrieved_doc_ids = []

        return ChatMessage(
            id=row["id"],
            session_id=row["session_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            role=Role(row["role"]),
            content=row["content"],
            page_context=row["page_context"],
            retrieved_doc_ids=retrieved_doc_ids,
            token_count=row["token_count"],
            prompt_tokens=row["prompt_tokens"],
            completion_tokens=row["completion_tokens"],
            provider=row["provider"],
            model=row["model"],
            temperature=row["temperature"],
            is_redacted=row["is_redacted"],
            redacted_at=row["redacted_at"],
            redacted_by=row["redacted_by"],
            redaction_reason=row["redaction_reason"],
            created_at=row["created_at"],
        )

    async def create(self, message: ChatMessage) -> str:
        """
        Create a new message (APPEND-ONLY).

        Args:
            message: ChatMessage to save

        Returns:
            Message ID
        """
        query = """
            INSERT INTO chat_messages (
                id, session_id, tenant_id, user_id,
                role, content, page_context, retrieved_doc_ids,
                token_count, prompt_tokens, completion_tokens,
                provider, model, temperature
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
            )
            RETURNING id
        """

        # Serialize list to JSON string for JSONB column
        retrieved_doc_ids_json = json.dumps(message.retrieved_doc_ids or [])

        result = await self._fetchval(
            query,
            message.id, message.session_id, message.tenant_id, message.user_id,
            message.role.value, message.content, message.page_context,
            retrieved_doc_ids_json,
            message.token_count, message.prompt_tokens, message.completion_tokens,
            message.provider, message.model, message.temperature
        )

        logger.debug(f"Created message: {result}")
        return str(result)

    async def get_by_session(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50,
        before_id: Optional[str] = None
    ) -> List[ChatMessage]:
        """
        Get messages for a session.

        Args:
            session_id: Session ID
            tenant_id: Tenant ID
            limit: Max messages
            before_id: Cursor for pagination (messages before this ID)

        Returns:
            List of ChatMessage ordered by created_at ASC
        """
        if before_id:
            query = """
                SELECT * FROM chat_messages
                WHERE session_id = $1 AND tenant_id = $2
                  AND created_at < (
                      SELECT created_at FROM chat_messages WHERE id = $4
                  )
                ORDER BY created_at DESC
                LIMIT $3
            """
            rows = await self._fetch(query, session_id, tenant_id, limit, before_id)
        else:
            # Get most recent messages
            query = """
                SELECT * FROM (
                    SELECT * FROM chat_messages
                    WHERE session_id = $1 AND tenant_id = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                ) sub
                ORDER BY created_at ASC
            """
            rows = await self._fetch(query, session_id, tenant_id, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_recent_by_user(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 100
    ) -> List[ChatMessage]:
        """Get recent messages for a user across all sessions."""
        query = """
            SELECT * FROM chat_messages
            WHERE tenant_id = $1 AND user_id = $2
            ORDER BY created_at DESC
            LIMIT $3
        """

        rows = await self._fetch(query, tenant_id, user_id, limit)
        return [self._row_to_entity(row) for row in rows]

    async def count_by_session(
        self,
        session_id: str,
        tenant_id: str
    ) -> int:
        """Count messages in session."""
        query = """
            SELECT COUNT(*) FROM chat_messages
            WHERE session_id = $1 AND tenant_id = $2
        """
        return await self._fetchval(query, session_id, tenant_id)

    async def redact(
        self,
        message_id: str,
        tenant_id: str,
        redacted_by: str,
        reason: str
    ) -> bool:
        """
        Redact a message (compliance action per CHAT-LAW-006).

        This replaces content with [REDACTED] but preserves the record.

        Args:
            message_id: Message ID
            tenant_id: Tenant ID
            redacted_by: Who performed redaction
            reason: Reason for redaction

        Returns:
            True if redacted
        """
        query = """
            UPDATE chat_messages SET
                content = '[REDACTED]',
                is_redacted = TRUE,
                redacted_at = NOW(),
                redacted_by = $3,
                redaction_reason = $4
            WHERE id = $1 AND tenant_id = $2 AND is_redacted = FALSE
        """

        result = await self._execute(query, message_id, tenant_id, redacted_by, reason)
        return "UPDATE 1" in result

    async def get_token_usage(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> dict:
        """Get token usage statistics."""
        if user_id:
            query = """
                SELECT
                    SUM(prompt_tokens) as total_prompt,
                    SUM(completion_tokens) as total_completion,
                    COUNT(*) as message_count
                FROM chat_messages
                WHERE tenant_id = $1 AND user_id = $2
                  AND role = 'assistant'
                  AND created_at >= NOW() - INTERVAL '%s days'
            """ % days
            row = await self._fetchrow(query, tenant_id, user_id)
        else:
            query = """
                SELECT
                    SUM(prompt_tokens) as total_prompt,
                    SUM(completion_tokens) as total_completion,
                    COUNT(*) as message_count
                FROM chat_messages
                WHERE tenant_id = $1
                  AND role = 'assistant'
                  AND created_at >= NOW() - INTERVAL '%s days'
            """ % days
            row = await self._fetchrow(query, tenant_id)

        return {
            "prompt_tokens": row["total_prompt"] or 0,
            "completion_tokens": row["total_completion"] or 0,
            "message_count": row["message_count"] or 0,
        }
