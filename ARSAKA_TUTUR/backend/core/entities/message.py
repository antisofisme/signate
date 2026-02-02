"""
Message entities for chat conversations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


class Role(str, Enum):
    """Message role in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Simple message structure for LLM input."""
    role: str
    content: str


@dataclass
class ChatMessage:
    """
    Chat message entity (APPEND-ONLY per CHAT-LAW-006).

    Messages are immutable once created. Only redaction is allowed.
    """
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default_factory=uuid4)
    tenant_id: str = ""
    user_id: str = ""

    # Message content
    role: Role = Role.USER
    content: str = ""

    # Context information
    page_context: Optional[str] = None
    retrieved_doc_ids: List[str] = field(default_factory=list)

    # Token tracking
    token_count: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

    # AI metadata
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None

    # Redaction only (CHAT-LAW-006 - no delete, only redact)
    is_redacted: bool = False
    redacted_at: Optional[datetime] = None
    redacted_by: Optional[str] = None
    redaction_reason: Optional[str] = None

    # Timestamp (NO updated_at - immutable!)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_message(self) -> Message:
        """Convert to simple Message for LLM input."""
        return Message(role=self.role.value, content=self.content)

    def is_user_message(self) -> bool:
        return self.role == Role.USER

    def is_assistant_message(self) -> bool:
        return self.role == Role.ASSISTANT


@dataclass
class GenerationResult:
    """Result from LLM generation."""
    content: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
