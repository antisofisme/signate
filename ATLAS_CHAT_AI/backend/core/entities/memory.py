"""
Memory entities for semantic and temporal memory.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


class FactType(str, Enum):
    """Types of user facts that can be extracted."""
    PREFERENCE = "preference"    # User preferences (e.g., "prefers TypeScript")
    KNOWLEDGE = "knowledge"      # User's domain knowledge
    RELATIONSHIP = "relationship"  # Relationships to other entities
    CONTEXT = "context"          # Contextual information (e.g., "works at X")
    GOAL = "goal"                # User's goals or objectives


@dataclass
class UserFact:
    """
    User fact entity (semantic memory).

    Facts are extracted from conversations and represent durable user knowledge.
    """
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = ""
    user_id: str = ""

    # Fact content
    fact_type: FactType = FactType.CONTEXT
    content: str = ""
    content_embedding: Optional[List[float]] = None
    confidence: float = 1.0  # 0.0 to 1.0

    # Source tracking
    source_session_id: Optional[UUID] = None
    source_message_id: Optional[UUID] = None
    extracted_at: datetime = field(default_factory=datetime.utcnow)

    # Lifecycle
    is_active: bool = True
    superseded_by: Optional[UUID] = None
    last_confirmed_at: Optional[datetime] = None
    confirmation_count: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def confirm(self) -> None:
        """Confirm fact is still valid, increase confidence."""
        self.last_confirmed_at = datetime.utcnow()
        self.confirmation_count += 1
        # Increase confidence slightly, max 1.0
        self.confidence = min(1.0, self.confidence + 0.05)
        self.updated_at = datetime.utcnow()

    def contradict(self, amount: float = 0.2) -> None:
        """Decrease confidence when contradicted."""
        self.confidence = max(0.0, self.confidence - amount)
        self.updated_at = datetime.utcnow()

        # Deactivate if confidence drops too low
        if self.confidence < 0.3:
            self.is_active = False

    def supersede(self, new_fact_id: UUID) -> None:
        """Mark this fact as superseded by a newer fact."""
        self.superseded_by = new_fact_id
        self.is_active = False
        self.updated_at = datetime.utcnow()


@dataclass
class ExtractedFact:
    """Fact extracted from conversation, pending storage."""
    fact_type: FactType
    content: str
    confidence: float
    source_message_id: Optional[UUID] = None
    contradicts_fact_ids: List[UUID] = field(default_factory=list)


@dataclass
class TimeSummary:
    """
    Time-based memory summary (temporal memory).

    Aggregates user activity over a time period (day/week/month).
    """
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = ""
    user_id: str = ""

    # Time period
    period_type: str = "day"  # 'day', 'week', 'month'
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Aggregated content
    summary: str = ""
    summary_embedding: Optional[List[float]] = None
    topics: List[Dict[str, Any]] = field(default_factory=list)  # [{"topic": "...", "count": N}]
    session_count: int = 0
    message_count: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)

    def get_top_topics(self, limit: int = 5) -> List[str]:
        """Get top N topics by count."""
        sorted_topics = sorted(
            self.topics,
            key=lambda t: t.get("count", 0),
            reverse=True
        )
        return [t.get("topic", "") for t in sorted_topics[:limit]]
