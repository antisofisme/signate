"""
Session entities for chat sessions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


@dataclass
class ChatSession:
    """
    Chat session entity (episodic memory container).

    Sessions group related messages and can have summaries for retrieval.
    """
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = ""
    user_id: str = ""

    # Session metadata
    title: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None
    message_count: int = 0

    # Summary for long sessions
    summary: Optional[str] = None
    summary_embedding: Optional[List[float]] = None
    summary_updated_at: Optional[datetime] = None

    # Topics extracted from conversation
    topics: List[Dict[str, Any]] = field(default_factory=list)

    # Soft delete (CHAT-LAW-006 compliant)
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def soft_delete(self, deleted_by: str) -> None:
        """Mark session as soft-deleted."""
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
        self.updated_at = datetime.utcnow()

    def update_on_message(self) -> None:
        """Update stats when a new message is added."""
        self.message_count += 1
        self.last_message_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def needs_summary_update(self, summary_interval: int = 10) -> bool:
        """Check if summary should be regenerated."""
        if self.summary is None and self.message_count >= 5:
            return True
        if self.summary is not None:
            messages_since_summary = self.message_count - (
                0 if self.summary_updated_at is None else
                # Approximate: count messages since last summary
                self.message_count // 2
            )
            return messages_since_summary >= summary_interval
        return False


@dataclass
class SessionSummary:
    """Lightweight session info for search results."""
    session_id: UUID
    title: Optional[str]
    summary: Optional[str]
    topics: List[str]
    message_count: int
    last_message_at: Optional[datetime]
    score: float = 0.0  # Similarity score when searching
