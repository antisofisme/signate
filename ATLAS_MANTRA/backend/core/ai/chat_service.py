"""
Chat Service

Handles AI chat interactions with persistent history.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .providers import get_ai_provider
from .providers.base import ChatMessage, ChatResponse
from .system_prompt import get_system_prompt, format_decisions_for_context


@dataclass
class StoredMessage:
    """Message stored in database."""
    id: str
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    context: Dict[str, Any]
    provider: Optional[str]
    created_at: datetime


@dataclass
class ChatSession:
    """Chat session for a user."""
    id: str
    user_id: str
    messages: List[StoredMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ChatService:
    """
    Service for managing AI chat interactions.

    Handles:
    - Chat history storage (in-memory for now, can be extended to DB)
    - Context management (page, decision context)
    - AI provider interaction
    """

    def __init__(self):
        # In-memory storage (replace with DB in production)
        self._sessions: Dict[str, ChatSession] = {}
        self._messages: Dict[str, List[StoredMessage]] = {}

    def get_or_create_session(self, user_id: str) -> ChatSession:
        """Get existing session or create new one for user."""
        # Find existing session for user
        for session in self._sessions.values():
            if session.user_id == user_id:
                return session

        # Create new session
        session_id = str(uuid.uuid4())
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._sessions[session_id] = session
        self._messages[session_id] = []
        return session

    def get_session_messages(self, session_id: str) -> List[StoredMessage]:
        """Get all messages for a session."""
        return self._messages.get(session_id, [])

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        context: Dict[str, Any] = None,
        provider: str = None,
    ) -> StoredMessage:
        """Add message to session."""
        message = StoredMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            context=context or {},
            provider=provider,
            created_at=datetime.utcnow(),
        )

        if session_id not in self._messages:
            self._messages[session_id] = []
        self._messages[session_id].append(message)

        # Update session timestamp
        if session_id in self._sessions:
            self._sessions[session_id].updated_at = datetime.utcnow()

        return message

    async def chat(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any] = None,
        existing_decisions: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Process chat message and get AI response.

        Args:
            user_id: User identifier
            message: User's message
            context: Page/decision context
            existing_decisions: List of existing decisions for context

        Returns:
            Dict with response and metadata
        """
        # Get or create session
        session = self.get_or_create_session(user_id)

        # Store user message
        self.add_message(
            session_id=session.id,
            role="user",
            content=message,
            context=context,
        )

        # Prepare chat history for AI
        history = self.get_session_messages(session.id)
        chat_messages = [
            ChatMessage(role=m.role, content=m.content)
            for m in history[-20:]  # Last 20 messages for context
        ]

        # Build system prompt with decisions context
        decisions_summary = format_decisions_for_context(existing_decisions or [])
        system_prompt = get_system_prompt(decisions_summary)

        # Get AI provider and send request
        try:
            provider = get_ai_provider()
            response = await provider.chat(chat_messages, system_prompt)

            # Store assistant response
            self.add_message(
                session_id=session.id,
                role="assistant",
                content=response.content,
                context=context,
                provider=response.provider,
            )

            return {
                "success": True,
                "response": response.content,
                "session_id": session.id,
                "provider": response.provider,
                "model": response.model,
                "usage": response.usage,
            }

        except Exception as e:
            error_msg = f"AI service error: {str(e)}"
            return {
                "success": False,
                "error": error_msg,
                "session_id": session.id,
            }

    def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get chat history for user."""
        session = self.get_or_create_session(user_id)
        messages = self.get_session_messages(session.id)

        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "context": m.context,
                "provider": m.provider,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]

    def clear_history(self, user_id: str) -> bool:
        """Clear chat history for user."""
        session = self.get_or_create_session(user_id)
        if session.id in self._messages:
            self._messages[session.id] = []
            return True
        return False


# Singleton instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get chat service singleton."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
