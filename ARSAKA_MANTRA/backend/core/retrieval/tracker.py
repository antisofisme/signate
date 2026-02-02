"""
Usage Tracking - Decision Retrieval Analytics

Tracks which decisions are retrieved and used, enabling:
1. Popularity-based ranking (frequently used = more relevant)
2. Stale decision detection (never used = maybe remove)
3. Feedback loop (helpful/not helpful)
4. Analytics dashboard

EVENTS TRACKED:
- RETRIEVED: Decision was included in context
- VIEWED:    User explicitly viewed decision details
- APPLIED:   User confirmed they applied decision
- HELPFUL:   Explicit positive feedback
- UNHELPFUL: Explicit negative feedback
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import json


class UsageEventType(str, Enum):
    """Types of usage events."""
    RETRIEVED = "RETRIEVED"   # Included in AI context
    VIEWED = "VIEWED"         # User clicked to view details
    APPLIED = "APPLIED"       # User confirmed application
    HELPFUL = "HELPFUL"       # Positive feedback
    UNHELPFUL = "UNHELPFUL"   # Negative feedback


@dataclass
class UsageEvent:
    """Single usage event record."""
    event_id: str
    decision_id: str
    event_type: UsageEventType
    timestamp: datetime
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # file_path, query, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "decision_id": self.decision_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "context": self.context,
        }


@dataclass
class UsageStats:
    """Aggregated usage statistics for a decision."""
    decision_id: str
    total_retrievals: int = 0
    total_views: int = 0
    total_applied: int = 0
    helpful_count: int = 0
    unhelpful_count: int = 0
    last_retrieved: Optional[datetime] = None
    last_applied: Optional[datetime] = None

    @property
    def helpfulness_ratio(self) -> float:
        """Calculate helpfulness ratio (0-1)."""
        total_feedback = self.helpful_count + self.unhelpful_count
        if total_feedback == 0:
            return 0.5  # Neutral if no feedback
        return self.helpful_count / total_feedback

    @property
    def application_rate(self) -> float:
        """Calculate application rate (applied / retrieved)."""
        if self.total_retrievals == 0:
            return 0.0
        return self.total_applied / self.total_retrievals

    @property
    def engagement_score(self) -> float:
        """Calculate overall engagement score (0-1)."""
        if self.total_retrievals == 0:
            return 0.0

        # Weighted factors
        view_rate = min(1.0, self.total_views / self.total_retrievals)
        apply_rate = self.application_rate
        helpfulness = self.helpfulness_ratio

        return (0.2 * view_rate + 0.4 * apply_rate + 0.4 * helpfulness)


class UsageTracker:
    """
    Tracks and analyzes decision usage.

    Can use in-memory storage for development or external storage
    (Redis, PostgreSQL) for production.
    """

    def __init__(
        self,
        storage: Optional[Any] = None,
        max_events_memory: int = 10000,
    ):
        """
        Initialize tracker.

        Args:
            storage: External storage adapter (Redis/DB)
            max_events_memory: Max events to keep in memory
        """
        self.storage = storage
        self.max_events_memory = max_events_memory

        # In-memory storage (for dev/testing)
        self._events: List[UsageEvent] = []
        self._stats: Dict[str, UsageStats] = defaultdict(
            lambda: UsageStats(decision_id="")
        )
        self._event_counter = 0

    def track(
        self,
        decision_id: str,
        event_type: UsageEventType,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> UsageEvent:
        """
        Track a usage event.

        Args:
            decision_id: Decision that was used
            event_type: Type of usage
            session_id: Session identifier
            user_id: User identifier
            context: Additional context

        Returns:
            Created UsageEvent
        """
        self._event_counter += 1
        event = UsageEvent(
            event_id=f"evt_{self._event_counter}",
            decision_id=decision_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            session_id=session_id,
            user_id=user_id,
            context=context,
        )

        # Store event
        if self.storage:
            self._store_external(event)
        else:
            self._store_memory(event)

        # Update stats
        self._update_stats(event)

        return event

    def track_retrieval(
        self,
        decision_ids: List[str],
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[UsageEvent]:
        """
        Track multiple decisions retrieved in one query.

        Args:
            decision_ids: Decisions included in context
            session_id: Session identifier
            context: Query context

        Returns:
            List of created events
        """
        events = []
        for decision_id in decision_ids:
            event = self.track(
                decision_id=decision_id,
                event_type=UsageEventType.RETRIEVED,
                session_id=session_id,
                context=context,
            )
            events.append(event)
        return events

    def track_feedback(
        self,
        decision_id: str,
        helpful: bool,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> UsageEvent:
        """
        Track user feedback on a decision.

        Args:
            decision_id: Decision being rated
            helpful: True if helpful, False if not
            session_id: Session identifier
            user_id: User identifier
            comment: Optional feedback comment

        Returns:
            Created UsageEvent
        """
        return self.track(
            decision_id=decision_id,
            event_type=UsageEventType.HELPFUL if helpful else UsageEventType.UNHELPFUL,
            session_id=session_id,
            user_id=user_id,
            context={"comment": comment} if comment else None,
        )

    def get_stats(self, decision_id: str) -> UsageStats:
        """Get usage statistics for a decision."""
        if self.storage:
            return self._load_stats_external(decision_id)

        stats = self._stats.get(decision_id)
        if stats:
            stats.decision_id = decision_id
            return stats

        return UsageStats(decision_id=decision_id)

    def get_usage_count(self, decision_id: str) -> int:
        """Get total retrieval count for a decision."""
        return self.get_stats(decision_id).total_retrievals

    def get_top_used(
        self,
        limit: int = 20,
        since: Optional[datetime] = None,
    ) -> List[UsageStats]:
        """Get most frequently used decisions."""
        if since:
            # Filter events by time
            recent_events = [
                e for e in self._events
                if e.timestamp >= since and e.event_type == UsageEventType.RETRIEVED
            ]
            # Count by decision
            counts = defaultdict(int)
            for e in recent_events:
                counts[e.decision_id] += 1

            # Build stats
            stats_list = []
            for decision_id, count in counts.items():
                stats = self.get_stats(decision_id)
                stats_list.append(stats)

            stats_list.sort(key=lambda s: s.total_retrievals, reverse=True)
            return stats_list[:limit]

        # All time
        all_stats = [
            self.get_stats(decision_id)
            for decision_id in self._stats.keys()
        ]
        all_stats.sort(key=lambda s: s.total_retrievals, reverse=True)
        return all_stats[:limit]

    def get_stale_decisions(
        self,
        days_threshold: int = 30,
    ) -> List[str]:
        """Get decisions not retrieved in N days."""
        threshold = datetime.utcnow() - timedelta(days=days_threshold)
        stale = []

        for decision_id, stats in self._stats.items():
            if stats.last_retrieved is None or stats.last_retrieved < threshold:
                stale.append(decision_id)

        return stale

    def get_unhelpful_decisions(
        self,
        min_feedback: int = 3,
        max_ratio: float = 0.3,
    ) -> List[str]:
        """Get decisions with low helpfulness ratio."""
        unhelpful = []

        for decision_id, stats in self._stats.items():
            total_feedback = stats.helpful_count + stats.unhelpful_count
            if total_feedback >= min_feedback and stats.helpfulness_ratio < max_ratio:
                unhelpful.append(decision_id)

        return unhelpful

    def _store_memory(self, event: UsageEvent):
        """Store event in memory."""
        self._events.append(event)

        # Trim if over limit
        if len(self._events) > self.max_events_memory:
            self._events = self._events[-self.max_events_memory:]

    def _store_external(self, event: UsageEvent):
        """Store event in external storage."""
        if hasattr(self.storage, 'store_event'):
            self.storage.store_event(event.to_dict())

    def _load_stats_external(self, decision_id: str) -> UsageStats:
        """Load stats from external storage."""
        if hasattr(self.storage, 'get_stats'):
            data = self.storage.get_stats(decision_id)
            if data:
                return UsageStats(
                    decision_id=decision_id,
                    total_retrievals=data.get("total_retrievals", 0),
                    total_views=data.get("total_views", 0),
                    total_applied=data.get("total_applied", 0),
                    helpful_count=data.get("helpful_count", 0),
                    unhelpful_count=data.get("unhelpful_count", 0),
                )
        return UsageStats(decision_id=decision_id)

    def _update_stats(self, event: UsageEvent):
        """Update aggregated stats."""
        decision_id = event.decision_id
        if decision_id not in self._stats:
            self._stats[decision_id] = UsageStats(decision_id=decision_id)

        stats = self._stats[decision_id]

        if event.event_type == UsageEventType.RETRIEVED:
            stats.total_retrievals += 1
            stats.last_retrieved = event.timestamp
        elif event.event_type == UsageEventType.VIEWED:
            stats.total_views += 1
        elif event.event_type == UsageEventType.APPLIED:
            stats.total_applied += 1
            stats.last_applied = event.timestamp
        elif event.event_type == UsageEventType.HELPFUL:
            stats.helpful_count += 1
        elif event.event_type == UsageEventType.UNHELPFUL:
            stats.unhelpful_count += 1


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "UsageEventType",
    "UsageEvent",
    "UsageStats",
    "UsageTracker",
]
