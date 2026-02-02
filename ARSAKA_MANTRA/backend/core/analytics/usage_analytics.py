"""
MANTRA Usage Analytics

Track decision access patterns to identify:
- Frequently used decisions (hot)
- Rarely used decisions (cold/stale)
- Usage patterns by context (scope, time, user)
- Effectiveness metrics (was decision helpful?)

USE CASES:
1. Identify stale decisions for review/deprecation
2. Prioritize caching for hot decisions
3. Tune relevance scoring based on usage
4. Feedback loop for search ranking

DATA COLLECTED:
- Access events (who, when, what, context)
- Feedback events (helpful/not helpful)
- Aggregated stats (frequency, recency, etc.)
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class EventType(str, Enum):
    """Type of usage event."""
    VIEW = "VIEW"           # Decision was viewed/retrieved
    APPLY = "APPLY"         # Decision was applied (user confirmed)
    SKIP = "SKIP"           # Decision was skipped/ignored
    FEEDBACK = "FEEDBACK"   # Explicit feedback given


class FeedbackType(str, Enum):
    """Type of feedback."""
    HELPFUL = "HELPFUL"         # Decision was helpful
    NOT_HELPFUL = "NOT_HELPFUL" # Decision was not helpful
    OUTDATED = "OUTDATED"       # Decision seems outdated
    UNCLEAR = "UNCLEAR"         # Decision is unclear
    WRONG_CONTEXT = "WRONG_CONTEXT"  # Wrong decision for context


class DecisionHealth(str, Enum):
    """Health status of a decision based on usage."""
    HEALTHY = "HEALTHY"     # Good usage, positive feedback
    STALE = "STALE"         # No recent usage
    UNDERUSED = "UNDERUSED" # Lower than expected usage
    PROBLEMATIC = "PROBLEMATIC"  # Negative feedback
    NEW = "NEW"             # Too new to evaluate


# ============================================================================
# EVENT MODELS
# ============================================================================

@dataclass
class UsageEvent:
    """A single usage event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.VIEW
    decision_id: str = ""
    decision_code: str = ""

    # Context
    scope_path: Optional[str] = None
    query: Optional[str] = None
    file_path: Optional[str] = None

    # Who & when
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackEvent:
    """Feedback on a decision."""
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    feedback_type: FeedbackType = FeedbackType.HELPFUL

    # Optional details
    comment: Optional[str] = None
    context_scope: Optional[str] = None

    # Who & when
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# AGGREGATED STATS
# ============================================================================

@dataclass
class DecisionStats:
    """Aggregated stats for a decision."""
    decision_id: str
    decision_code: str = ""

    # Counts
    view_count: int = 0
    apply_count: int = 0
    skip_count: int = 0

    # Feedback
    helpful_count: int = 0
    not_helpful_count: int = 0
    outdated_count: int = 0
    unclear_count: int = 0

    # Timing
    first_access: Optional[datetime] = None
    last_access: Optional[datetime] = None
    last_feedback: Optional[datetime] = None

    # Computed
    created_at: Optional[datetime] = None  # When decision was created

    @property
    def total_feedback(self) -> int:
        return (
            self.helpful_count + self.not_helpful_count +
            self.outdated_count + self.unclear_count
        )

    @property
    def helpfulness_ratio(self) -> float:
        """Ratio of helpful feedback (0-1)."""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0.5  # Neutral if no feedback
        return self.helpful_count / total

    @property
    def apply_ratio(self) -> float:
        """Ratio of views that resulted in apply."""
        if self.view_count == 0:
            return 0.0
        return self.apply_count / self.view_count

    @property
    def days_since_last_access(self) -> int:
        """Days since last access."""
        if self.last_access is None:
            return 9999
        delta = datetime.now(timezone.utc) - self.last_access
        return delta.days

    def get_health(self, stale_days: int = 90) -> DecisionHealth:
        """Determine health status."""
        # New decision (less than 7 days old)
        if self.created_at:
            age = datetime.now(timezone.utc) - self.created_at
            if age.days < 7:
                return DecisionHealth.NEW

        # Problematic (many negative feedback)
        if self.not_helpful_count + self.outdated_count > self.helpful_count:
            return DecisionHealth.PROBLEMATIC

        # Stale (no recent access)
        if self.days_since_last_access > stale_days:
            return DecisionHealth.STALE

        # Underused (low apply ratio)
        if self.view_count > 10 and self.apply_ratio < 0.1:
            return DecisionHealth.UNDERUSED

        return DecisionHealth.HEALTHY


# ============================================================================
# ANALYTICS ENGINE
# ============================================================================

class UsageAnalytics:
    """
    Main analytics engine for tracking and querying usage.

    In-memory implementation; extend with DB persistence for production.
    """

    def __init__(
        self,
        stale_threshold_days: int = 90,
        hot_threshold_count: int = 100
    ):
        self.stale_threshold_days = stale_threshold_days
        self.hot_threshold_count = hot_threshold_count

        # Event storage (in production: use database)
        self._events: List[UsageEvent] = []
        self._feedback: List[FeedbackEvent] = []

        # Aggregated stats per decision
        self._stats: Dict[str, DecisionStats] = {}

        # Indexes for fast lookup
        self._by_scope: Dict[str, Set[str]] = defaultdict(set)
        self._by_user: Dict[str, Set[str]] = defaultdict(set)

    # =========================================================================
    # Event Recording
    # =========================================================================

    def record_view(
        self,
        decision_id: str,
        decision_code: str = "",
        scope_path: Optional[str] = None,
        query: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageEvent:
        """Record a view event."""
        event = UsageEvent(
            event_type=EventType.VIEW,
            decision_id=decision_id,
            decision_code=decision_code,
            scope_path=scope_path,
            query=query,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        return self._record_event(event)

    def record_apply(
        self,
        decision_id: str,
        decision_code: str = "",
        scope_path: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> UsageEvent:
        """Record that a decision was applied."""
        event = UsageEvent(
            event_type=EventType.APPLY,
            decision_id=decision_id,
            decision_code=decision_code,
            scope_path=scope_path,
            user_id=user_id
        )
        return self._record_event(event)

    def record_skip(
        self,
        decision_id: str,
        decision_code: str = "",
        reason: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> UsageEvent:
        """Record that a decision was skipped."""
        event = UsageEvent(
            event_type=EventType.SKIP,
            decision_id=decision_id,
            decision_code=decision_code,
            user_id=user_id,
            metadata={"reason": reason} if reason else {}
        )
        return self._record_event(event)

    def record_feedback(
        self,
        decision_id: str,
        feedback_type: FeedbackType,
        comment: Optional[str] = None,
        context_scope: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> FeedbackEvent:
        """Record explicit feedback on a decision."""
        feedback = FeedbackEvent(
            decision_id=decision_id,
            feedback_type=feedback_type,
            comment=comment,
            context_scope=context_scope,
            user_id=user_id
        )

        self._feedback.append(feedback)
        self._update_feedback_stats(feedback)
        return feedback

    def _record_event(self, event: UsageEvent) -> UsageEvent:
        """Internal: record event and update stats."""
        self._events.append(event)
        self._update_stats(event)

        # Update indexes
        if event.scope_path:
            self._by_scope[event.scope_path].add(event.decision_id)
        if event.user_id:
            self._by_user[event.user_id].add(event.decision_id)

        return event

    def _update_stats(self, event: UsageEvent) -> None:
        """Update aggregated stats from event."""
        if event.decision_id not in self._stats:
            self._stats[event.decision_id] = DecisionStats(
                decision_id=event.decision_id,
                decision_code=event.decision_code
            )

        stats = self._stats[event.decision_id]

        # Update counts
        if event.event_type == EventType.VIEW:
            stats.view_count += 1
        elif event.event_type == EventType.APPLY:
            stats.apply_count += 1
        elif event.event_type == EventType.SKIP:
            stats.skip_count += 1

        # Update timing
        if stats.first_access is None:
            stats.first_access = event.timestamp
        stats.last_access = event.timestamp

    def _update_feedback_stats(self, feedback: FeedbackEvent) -> None:
        """Update stats from feedback."""
        if feedback.decision_id not in self._stats:
            self._stats[feedback.decision_id] = DecisionStats(
                decision_id=feedback.decision_id
            )

        stats = self._stats[feedback.decision_id]

        if feedback.feedback_type == FeedbackType.HELPFUL:
            stats.helpful_count += 1
        elif feedback.feedback_type == FeedbackType.NOT_HELPFUL:
            stats.not_helpful_count += 1
        elif feedback.feedback_type == FeedbackType.OUTDATED:
            stats.outdated_count += 1
        elif feedback.feedback_type == FeedbackType.UNCLEAR:
            stats.unclear_count += 1

        stats.last_feedback = feedback.timestamp

    # =========================================================================
    # Querying
    # =========================================================================

    def get_stats(self, decision_id: str) -> Optional[DecisionStats]:
        """Get stats for a specific decision."""
        return self._stats.get(decision_id)

    def get_hot_decisions(self, limit: int = 20) -> List[DecisionStats]:
        """Get most frequently accessed decisions."""
        sorted_stats = sorted(
            self._stats.values(),
            key=lambda s: s.view_count,
            reverse=True
        )
        return sorted_stats[:limit]

    def get_stale_decisions(self, days: Optional[int] = None) -> List[DecisionStats]:
        """Get decisions that haven't been accessed recently."""
        threshold = days or self.stale_threshold_days
        stale = [
            s for s in self._stats.values()
            if s.days_since_last_access > threshold
        ]
        return sorted(stale, key=lambda s: s.days_since_last_access, reverse=True)

    def get_problematic_decisions(self) -> List[DecisionStats]:
        """Get decisions with negative feedback."""
        problematic = [
            s for s in self._stats.values()
            if s.get_health() == DecisionHealth.PROBLEMATIC
        ]
        return sorted(
            problematic,
            key=lambda s: s.not_helpful_count + s.outdated_count,
            reverse=True
        )

    def get_underused_decisions(self, min_views: int = 10) -> List[DecisionStats]:
        """Get decisions with low apply ratio."""
        underused = [
            s for s in self._stats.values()
            if s.view_count >= min_views and s.apply_ratio < 0.1
        ]
        return sorted(underused, key=lambda s: s.apply_ratio)

    def get_usage_by_scope(self, scope_path: str) -> List[DecisionStats]:
        """Get usage stats for decisions accessed in a scope."""
        decision_ids = self._by_scope.get(scope_path, set())
        return [
            self._stats[did] for did in decision_ids
            if did in self._stats
        ]

    def get_health_report(self) -> Dict[DecisionHealth, List[str]]:
        """Get health report grouped by status."""
        report: Dict[DecisionHealth, List[str]] = defaultdict(list)

        for stats in self._stats.values():
            health = stats.get_health(self.stale_threshold_days)
            report[health].append(stats.decision_id)

        return dict(report)

    # =========================================================================
    # Relevance Scoring
    # =========================================================================

    def get_relevance_boost(self, decision_id: str) -> float:
        """
        Get a relevance boost factor based on usage.

        Returns:
            Multiplier (0.5 - 1.5) for search ranking
        """
        stats = self._stats.get(decision_id)
        if not stats:
            return 1.0  # Neutral for unknown

        # Base on multiple factors
        factors = []

        # Recency factor (0.8 - 1.2)
        if stats.days_since_last_access < 7:
            factors.append(1.2)
        elif stats.days_since_last_access < 30:
            factors.append(1.1)
        elif stats.days_since_last_access > 90:
            factors.append(0.8)
        else:
            factors.append(1.0)

        # Helpfulness factor (0.7 - 1.3)
        if stats.total_feedback > 5:
            if stats.helpfulness_ratio > 0.8:
                factors.append(1.3)
            elif stats.helpfulness_ratio > 0.6:
                factors.append(1.1)
            elif stats.helpfulness_ratio < 0.3:
                factors.append(0.7)
            else:
                factors.append(0.9)

        # Apply ratio factor (0.9 - 1.1)
        if stats.view_count > 10:
            if stats.apply_ratio > 0.5:
                factors.append(1.1)
            elif stats.apply_ratio < 0.1:
                factors.append(0.9)

        # Combine factors (geometric mean)
        if not factors:
            return 1.0

        product = 1.0
        for f in factors:
            product *= f
        return product ** (1 / len(factors))

    # =========================================================================
    # Export / Persistence
    # =========================================================================

    def export_stats(self) -> Dict[str, Any]:
        """Export all stats as dict."""
        return {
            "total_events": len(self._events),
            "total_feedback": len(self._feedback),
            "decisions_tracked": len(self._stats),
            "stats": {
                did: {
                    "code": s.decision_code,
                    "view_count": s.view_count,
                    "apply_count": s.apply_count,
                    "skip_count": s.skip_count,
                    "helpful_count": s.helpful_count,
                    "not_helpful_count": s.not_helpful_count,
                    "health": s.get_health().value,
                    "days_since_access": s.days_since_last_access,
                }
                for did, s in self._stats.items()
            }
        }

    def import_stats(self, data: Dict[str, Any]) -> int:
        """Import stats from exported data."""
        imported = 0
        for did, stats_data in data.get("stats", {}).items():
            self._stats[did] = DecisionStats(
                decision_id=did,
                decision_code=stats_data.get("code", ""),
                view_count=stats_data.get("view_count", 0),
                apply_count=stats_data.get("apply_count", 0),
                skip_count=stats_data.get("skip_count", 0),
                helpful_count=stats_data.get("helpful_count", 0),
                not_helpful_count=stats_data.get("not_helpful_count", 0),
            )
            imported += 1
        return imported


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global analytics instance (singleton pattern)
_analytics: Optional[UsageAnalytics] = None


def get_analytics() -> UsageAnalytics:
    """Get global analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = UsageAnalytics()
    return _analytics


def track_view(decision_id: str, **kwargs) -> UsageEvent:
    """Quick helper to track a view."""
    return get_analytics().record_view(decision_id, **kwargs)


def track_feedback(
    decision_id: str,
    helpful: bool,
    comment: Optional[str] = None
) -> FeedbackEvent:
    """Quick helper to track feedback."""
    return get_analytics().record_feedback(
        decision_id=decision_id,
        feedback_type=FeedbackType.HELPFUL if helpful else FeedbackType.NOT_HELPFUL,
        comment=comment
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "EventType",
    "FeedbackType",
    "DecisionHealth",
    # Models
    "UsageEvent",
    "FeedbackEvent",
    "DecisionStats",
    # Engine
    "UsageAnalytics",
    # Convenience
    "get_analytics",
    "track_view",
    "track_feedback",
]
