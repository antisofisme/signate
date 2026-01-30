"""
Proactive Retrieval - Pre-fetch and Prediction

Proactively retrieves decisions before AI asks:
1. Pre-fetch on file open
2. Watch mode for file changes
3. Predictive loading based on git diff
4. Session warm-up based on recent patterns

TRIGGERS:
- FILE_OPEN:   User opens a file
- FILE_SAVE:   User saves a file
- GIT_DIFF:    Git status changes
- SESSION_START: New session begins
- IDLE:        Periodic refresh during idle
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import re
from pathlib import Path


class TriggerType(str, Enum):
    """Types of proactive triggers."""
    FILE_OPEN = "FILE_OPEN"
    FILE_SAVE = "FILE_SAVE"
    GIT_DIFF = "GIT_DIFF"
    SESSION_START = "SESSION_START"
    IDLE = "IDLE"
    MANUAL = "MANUAL"


@dataclass
class ProactiveContext:
    """Context for proactive retrieval."""
    trigger_type: TriggerType
    file_paths: List[str] = field(default_factory=list)
    git_diff_files: List[str] = field(default_factory=list)
    recent_queries: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProactiveResult:
    """Result of proactive retrieval."""
    trigger_type: TriggerType
    decision_ids: List[str]
    decision_codes: List[str]
    context_text: str
    token_count: int
    patterns_matched: List[str]
    cached: bool = False
    fetch_time_ms: float = 0.0


class ProactiveRetrieval:
    """
    Proactively retrieves decisions based on context signals.

    Pre-fetches relevant decisions before the AI assistant asks,
    reducing latency and improving response quality.
    """

    def __init__(
        self,
        retrieval_engine: Any = None,
        cache: Any = None,
        max_prefetch: int = 10,
    ):
        """
        Initialize proactive retrieval.

        Args:
            retrieval_engine: Main retrieval engine
            cache: Decision cache
            max_prefetch: Maximum decisions to pre-fetch
        """
        self.engine = retrieval_engine
        self.cache = cache
        self.max_prefetch = max_prefetch

        # Pattern registry: file pattern → relevant queries
        self._pattern_queries: Dict[str, List[str]] = {
            r".*\.tsx$": ["react component", "typescript"],
            r".*\.jsx$": ["react component", "javascript"],
            r".*\.vue$": ["vue component"],
            r".*/api/.*": ["api endpoint", "rest api"],
            r".*/routes/.*": ["routing", "api endpoint"],
            r".*/auth/.*": ["authentication", "security"],
            r".*/components/.*": ["component architecture"],
            r".*/features/.*": ["feature structure"],
            r".*/hooks/.*": ["react hooks"],
            r".*/utils/.*": ["utility functions"],
            r".*/services/.*": ["service layer"],
            r".*/models/.*": ["data model"],
            r".*\.sql$": ["database", "sql"],
            r".*/migrations/.*": ["database migration"],
            r".*test.*": ["testing"],
            r".*spec.*": ["testing"],
            r".*\.py$": ["python"],
            r".*\.go$": ["golang"],
        }

        # Session history for pattern learning
        self._session_history: Dict[str, List[Dict]] = {}

    def on_file_open(
        self,
        file_path: str,
        session_id: Optional[str] = None,
    ) -> ProactiveResult:
        """
        Handle file open event.

        Pre-fetches decisions relevant to the opened file.
        """
        context = ProactiveContext(
            trigger_type=TriggerType.FILE_OPEN,
            file_paths=[file_path],
            session_id=session_id,
        )
        return self._execute(context)

    def on_file_save(
        self,
        file_path: str,
        session_id: Optional[str] = None,
    ) -> ProactiveResult:
        """
        Handle file save event.

        Re-evaluates relevance after file change.
        """
        context = ProactiveContext(
            trigger_type=TriggerType.FILE_SAVE,
            file_paths=[file_path],
            session_id=session_id,
        )
        return self._execute(context)

    def on_git_diff(
        self,
        diff_files: List[str],
        session_id: Optional[str] = None,
    ) -> ProactiveResult:
        """
        Handle git diff event.

        Pre-fetches decisions for all changed files.
        """
        context = ProactiveContext(
            trigger_type=TriggerType.GIT_DIFF,
            git_diff_files=diff_files,
            file_paths=diff_files,
            session_id=session_id,
        )
        return self._execute(context)

    def on_session_start(
        self,
        session_id: str,
        working_directory: Optional[str] = None,
    ) -> ProactiveResult:
        """
        Handle session start.

        Warms up cache with commonly used decisions.
        """
        # Get session history if available
        recent_queries = []
        if session_id in self._session_history:
            history = self._session_history[session_id]
            recent_queries = [h.get("query", "") for h in history[-10:]]

        context = ProactiveContext(
            trigger_type=TriggerType.SESSION_START,
            recent_queries=recent_queries,
            session_id=session_id,
        )
        return self._execute(context)

    def predict_from_git(
        self,
        git_status: Dict[str, List[str]],
        session_id: Optional[str] = None,
    ) -> ProactiveResult:
        """
        Predict needed decisions from git status.

        Args:
            git_status: {"modified": [...], "added": [...], "deleted": [...]}
        """
        all_files = []
        all_files.extend(git_status.get("modified", []))
        all_files.extend(git_status.get("added", []))

        return self.on_git_diff(all_files, session_id)

    def _execute(self, context: ProactiveContext) -> ProactiveResult:
        """Execute proactive retrieval."""
        start_time = datetime.utcnow()

        # Check cache first
        cache_key = self._build_cache_key(context)
        if self.cache:
            cached = self.cache.get_bundle(cache_key)
            if cached:
                return ProactiveResult(
                    trigger_type=context.trigger_type,
                    decision_ids=cached.decision_ids,
                    decision_codes=cached.decision_codes,
                    context_text=cached.context_text,
                    token_count=cached.token_count,
                    patterns_matched=[],
                    cached=True,
                    fetch_time_ms=0,
                )

        # Build queries from context
        queries = self._build_queries(context)
        patterns_matched = queries.copy()

        # Execute retrieval
        decision_ids = []
        decision_codes = []
        context_text = ""
        token_count = 0

        if self.engine:
            for query in queries[:3]:  # Limit queries
                results = self.engine.retrieve(
                    query=query,
                    file_path=context.file_paths[0] if context.file_paths else None,
                    max_results=self.max_prefetch // len(queries) or 3,
                )

                for r in results:
                    if r.decision_id not in decision_ids:
                        decision_ids.append(r.decision_id)
                        decision_codes.append(r.decision_code)

        # Build context text
        if self.engine and decision_ids:
            context_text = self.engine.build_context(
                decision_ids[:self.max_prefetch],
                level="standard",
            )
            token_count = len(context_text) // 4  # Rough estimate

        # Calculate fetch time
        fetch_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Cache result
        if self.cache and decision_ids:
            self.cache.set_bundle(
                pattern=cache_key,
                decision_ids=decision_ids[:self.max_prefetch],
                decision_codes=decision_codes[:self.max_prefetch],
                context_text=context_text,
                token_count=token_count,
            )

        # Record in session history
        if context.session_id:
            self._record_history(context, decision_ids)

        return ProactiveResult(
            trigger_type=context.trigger_type,
            decision_ids=decision_ids[:self.max_prefetch],
            decision_codes=decision_codes[:self.max_prefetch],
            context_text=context_text,
            token_count=token_count,
            patterns_matched=patterns_matched,
            cached=False,
            fetch_time_ms=fetch_time,
        )

    def _build_queries(self, context: ProactiveContext) -> List[str]:
        """Build search queries from context."""
        queries = []

        # From file patterns
        for file_path in context.file_paths:
            file_path_normalized = file_path.replace("\\", "/")
            for pattern, pattern_queries in self._pattern_queries.items():
                if re.match(pattern, file_path_normalized, re.IGNORECASE):
                    queries.extend(pattern_queries)

        # From git diff (aggregate patterns)
        if context.git_diff_files:
            tech_set = set()
            for file_path in context.git_diff_files:
                if file_path.endswith(('.tsx', '.jsx')):
                    tech_set.add("react")
                elif file_path.endswith('.vue'):
                    tech_set.add("vue")
                elif file_path.endswith('.py'):
                    tech_set.add("python")
                if '/api/' in file_path:
                    tech_set.add("api")
                if '/auth/' in file_path:
                    tech_set.add("auth")
            queries.extend(list(tech_set))

        # From recent queries
        queries.extend(context.recent_queries)

        # Deduplicate while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)

        return unique_queries

    def _build_cache_key(self, context: ProactiveContext) -> str:
        """Build cache key from context."""
        parts = [context.trigger_type.value]

        if context.file_paths:
            # Use directory pattern, not full path
            for fp in context.file_paths[:3]:
                fp_normalized = fp.replace("\\", "/")
                # Extract pattern: e.g., "src/features/*.tsx"
                path = Path(fp_normalized)
                pattern = f"{path.parent}/*{path.suffix}"
                parts.append(pattern)

        return "|".join(parts)

    def _record_history(
        self,
        context: ProactiveContext,
        decision_ids: List[str],
    ):
        """Record retrieval in session history."""
        session_id = context.session_id
        if not session_id:
            return

        if session_id not in self._session_history:
            self._session_history[session_id] = []

        self._session_history[session_id].append({
            "timestamp": context.timestamp,
            "trigger": context.trigger_type.value,
            "files": context.file_paths[:5],
            "decisions": decision_ids[:10],
        })

        # Limit history size
        if len(self._session_history[session_id]) > 100:
            self._session_history[session_id] = self._session_history[session_id][-100:]

    def get_session_patterns(
        self,
        session_id: str,
    ) -> Dict[str, int]:
        """Get most common patterns from session history."""
        history = self._session_history.get(session_id, [])

        pattern_counts = {}
        for entry in history:
            for file_path in entry.get("files", []):
                for pattern in self._pattern_queries.keys():
                    if re.match(pattern, file_path, re.IGNORECASE):
                        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        return dict(sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True))

    def clear_session(self, session_id: str):
        """Clear session history."""
        if session_id in self._session_history:
            del self._session_history[session_id]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "TriggerType",
    "ProactiveContext",
    "ProactiveResult",
    "ProactiveRetrieval",
]
