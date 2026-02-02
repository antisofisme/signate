"""
Request and assembled context entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from .user import User, APIKeyPayload
from .tenant import TenantConfig
from .message import ChatMessage, Message
from .document import SearchResult
from .memory import UserFact


@dataclass
class RequestContext:
    """
    Request context propagated through all layers.

    Contains tenant, user, and request-specific information.
    """
    request_id: str = field(default_factory=lambda: str(uuid4()))
    tenant_id: str = ""
    tenant_config: Optional[TenantConfig] = None

    # Authentication
    user: Optional[User] = None
    api_key: Optional[APIKeyPayload] = None

    # Permissions (computed from user or api_key)
    permissions: List[str] = field(default_factory=list)

    # Request metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def user_id(self) -> str:
        """Get user ID from user or API key context."""
        if self.user:
            return str(self.user.id)
        if self.api_key:
            return f"api_key:{self.api_key.key_id}"
        return "anonymous"

    @property
    def actor_type(self) -> str:
        """Get actor type for audit logging."""
        if self.user:
            return "user"
        if self.api_key:
            return "api_key"
        return "anonymous"

    @property
    def actor_id(self) -> str:
        """Get actor ID for audit logging."""
        return self.user_id

    def has_permission(self, permission: str) -> bool:
        """Check if context has specific permission."""
        if self.user:
            return self.user.has_permission(permission)
        if self.api_key:
            return self.api_key.has_permission(permission)
        return False


@dataclass
class AssembledContext:
    """
    Assembled context ready for LLM.

    Contains all information needed to generate a response.
    """
    # Core context
    tenant_config: TenantConfig = field(default_factory=TenantConfig)
    user_id: str = ""
    session_id: str = ""

    # Messages
    system_message: Message = field(default_factory=lambda: Message(role="system", content=""))
    conversation_messages: List[Message] = field(default_factory=list)
    current_query: str = ""

    # Retrieved context
    retrieved_docs: List[SearchResult] = field(default_factory=list)
    user_facts: List[UserFact] = field(default_factory=list)

    # Token counts
    system_tokens: int = 0
    conversation_tokens: int = 0
    context_tokens: int = 0
    facts_tokens: int = 0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Get total estimated token count."""
        return (
            self.system_tokens +
            self.conversation_tokens +
            self.context_tokens +
            self.facts_tokens
        )

    def get_messages_for_llm(self) -> List[Message]:
        """
        Get all messages formatted for LLM input.

        Order: system -> facts -> context -> conversation -> current query
        """
        messages = []

        # System prompt
        if self.system_message.content:
            messages.append(self.system_message)

        # User facts as system context
        if self.user_facts:
            facts_content = self._format_facts()
            if facts_content:
                messages.append(Message(
                    role="system",
                    content=f"User information:\n{facts_content}"
                ))

        # Retrieved documents as system context
        if self.retrieved_docs:
            context_content = self._format_context()
            if context_content:
                messages.append(Message(
                    role="system",
                    content=f"Relevant context:\n{context_content}"
                ))

        # Conversation history
        messages.extend(self.conversation_messages)

        # Current query (already in conversation_messages as last user message)

        return messages

    def _format_facts(self) -> str:
        """Format user facts as context string."""
        if not self.user_facts:
            return ""

        lines = []
        for fact in self.user_facts:
            if fact.is_active and fact.confidence >= 0.5:
                lines.append(f"- {fact.content}")

        return "\n".join(lines)

    def _format_context(self) -> str:
        """Format retrieved documents as context string."""
        if not self.retrieved_docs:
            return ""

        parts = []
        for i, doc in enumerate(self.retrieved_docs, 1):
            parts.append(f"[{i}] {doc.to_context_string()}")

        return "\n\n".join(parts)

    def is_within_token_limit(self) -> bool:
        """Check if context is within tenant's token limit."""
        return self.total_tokens <= self.tenant_config.max_context_tokens
