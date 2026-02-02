"""
Relevance Ranker - Multi-Factor Ranking System

Ranks search results by multiple factors:
1. Search score (from hybrid search)
2. Quality score (from quality scorer)
3. Usage frequency (from usage tracker)
4. Recency (newer = more relevant)
5. Impact level (CRITICAL > IMPORTANT > REFERENCE)
6. File path match (direct pattern match)

RANKING FORMULA:
    final_score = Σ(factor_weight * factor_score) / Σ(weights)

DEFAULT WEIGHTS:
    search_score:    0.30
    quality_score:   0.20
    usage_frequency: 0.15
    recency:         0.10
    impact:          0.15
    path_match:      0.10
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import math


@dataclass
class RankingFactors:
    """Weights for ranking factors."""
    search_score: float = 0.30
    quality_score: float = 0.20
    usage_frequency: float = 0.15
    recency: float = 0.10
    impact: float = 0.15
    path_match: float = 0.10

    def total(self) -> float:
        return (
            self.search_score +
            self.quality_score +
            self.usage_frequency +
            self.recency +
            self.impact +
            self.path_match
        )

    def normalized(self) -> 'RankingFactors':
        """Return normalized weights (sum to 1.0)."""
        total = self.total()
        if total == 0:
            return RankingFactors()
        return RankingFactors(
            search_score=self.search_score / total,
            quality_score=self.quality_score / total,
            usage_frequency=self.usage_frequency / total,
            recency=self.recency / total,
            impact=self.impact / total,
            path_match=self.path_match / total,
        )


@dataclass
class RankedResult:
    """Ranked search result with factor breakdown."""
    decision_id: str
    decision_code: str
    final_score: float

    # Factor scores (0-1)
    search_score: float = 0.0
    quality_score: float = 0.0
    usage_score: float = 0.0
    recency_score: float = 0.0
    impact_score: float = 0.0
    path_match_score: float = 0.0

    # Metadata
    rank: int = 0
    factors_used: List[str] = field(default_factory=list)

    def explain(self) -> str:
        """Human-readable explanation of ranking."""
        parts = [f"Rank #{self.rank}: {self.decision_code} (score: {self.final_score:.2f})"]
        if self.search_score > 0:
            parts.append(f"  - Search: {self.search_score:.2f}")
        if self.quality_score > 0:
            parts.append(f"  - Quality: {self.quality_score:.2f}")
        if self.usage_score > 0:
            parts.append(f"  - Usage: {self.usage_score:.2f}")
        if self.recency_score > 0:
            parts.append(f"  - Recency: {self.recency_score:.2f}")
        if self.impact_score > 0:
            parts.append(f"  - Impact: {self.impact_score:.2f}")
        if self.path_match_score > 0:
            parts.append(f"  - Path match: {self.path_match_score:.2f}")
        return "\n".join(parts)


class RelevanceRanker:
    """
    Multi-factor relevance ranker.

    Combines multiple signals to produce final ranking.
    """

    # Impact level scores
    IMPACT_SCORES = {
        "CRITICAL": 1.0,
        "IMPORTANT": 0.7,
        "REFERENCE": 0.4,
    }

    def __init__(
        self,
        factors: Optional[RankingFactors] = None,
        quality_getter: Optional[Callable[[str], float]] = None,
        usage_getter: Optional[Callable[[str], int]] = None,
    ):
        """
        Initialize ranker.

        Args:
            factors: Weight configuration
            quality_getter: Function to get quality score by decision_id
            usage_getter: Function to get usage count by decision_id
        """
        self.factors = (factors or RankingFactors()).normalized()
        self.quality_getter = quality_getter
        self.usage_getter = usage_getter

        # Cache for expensive lookups
        self._quality_cache: Dict[str, float] = {}
        self._usage_cache: Dict[str, int] = {}

    def rank(
        self,
        results: List[Any],  # SearchResult from searcher
        decisions: Dict[str, Any],  # decision_id -> decision data
        context: Optional[Dict[str, Any]] = None,
    ) -> List[RankedResult]:
        """
        Rank search results by multiple factors.

        Args:
            results: Search results from HybridSearcher
            decisions: Decision data keyed by decision_id
            context: Additional context (file_path, task_type, etc.)

        Returns:
            Ranked results with scores
        """
        context = context or {}
        file_path = context.get("file_path", "")
        now = datetime.utcnow()

        ranked = []
        for search_result in results:
            decision_id = search_result.decision_id
            decision = decisions.get(decision_id, {})

            # Calculate each factor score
            search_score = search_result.combined_score
            quality_score = self._get_quality_score(decision_id, decision)
            usage_score = self._get_usage_score(decision_id)
            recency_score = self._get_recency_score(decision, now)
            impact_score = self._get_impact_score(decision)
            path_match_score = self._get_path_match_score(decision, file_path)

            # Weighted combination
            final_score = (
                self.factors.search_score * search_score +
                self.factors.quality_score * quality_score +
                self.factors.usage_frequency * usage_score +
                self.factors.recency * recency_score +
                self.factors.impact * impact_score +
                self.factors.path_match * path_match_score
            )

            # Track which factors contributed
            factors_used = []
            if search_score > 0:
                factors_used.append("search")
            if quality_score > 0:
                factors_used.append("quality")
            if usage_score > 0:
                factors_used.append("usage")
            if recency_score > 0:
                factors_used.append("recency")
            if impact_score > 0:
                factors_used.append("impact")
            if path_match_score > 0:
                factors_used.append("path_match")

            ranked.append(RankedResult(
                decision_id=decision_id,
                decision_code=decision.get("code", decision.get("decision_code", "")),
                final_score=final_score,
                search_score=search_score,
                quality_score=quality_score,
                usage_score=usage_score,
                recency_score=recency_score,
                impact_score=impact_score,
                path_match_score=path_match_score,
                factors_used=factors_used,
            ))

        # Sort by final score
        ranked.sort(key=lambda r: r.final_score, reverse=True)

        # Assign ranks
        for i, result in enumerate(ranked):
            result.rank = i + 1

        return ranked

    def _get_quality_score(self, decision_id: str, decision: Dict) -> float:
        """Get quality score (0-1)."""
        # Check cache
        if decision_id in self._quality_cache:
            return self._quality_cache[decision_id]

        # Try getter function
        if self.quality_getter:
            try:
                score = self.quality_getter(decision_id)
                self._quality_cache[decision_id] = score / 100.0  # Normalize to 0-1
                return self._quality_cache[decision_id]
            except Exception:
                pass

        # Try decision data
        quality_meta = decision.get("quality_metadata", {})
        if quality_meta:
            score = quality_meta.get("overall_score", 50) / 100.0
            self._quality_cache[decision_id] = score
            return score

        # Default: neutral quality
        return 0.5

    def _get_usage_score(self, decision_id: str) -> float:
        """Get usage frequency score (0-1)."""
        # Check cache
        if decision_id in self._usage_cache:
            count = self._usage_cache[decision_id]
        elif self.usage_getter:
            try:
                count = self.usage_getter(decision_id)
                self._usage_cache[decision_id] = count
            except Exception:
                count = 0
        else:
            count = 0

        # Logarithmic scaling (diminishing returns)
        # 0 uses = 0, 1 use = 0.3, 10 uses = 0.6, 100 uses = 0.9
        if count <= 0:
            return 0.0
        return min(1.0, math.log10(count + 1) / 2.0)

    def _get_recency_score(self, decision: Dict, now: datetime) -> float:
        """Get recency score (0-1). Newer = higher."""
        created_at = decision.get("created_at") or decision.get("authored_at")

        if not created_at:
            return 0.5  # Unknown = neutral

        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                return 0.5

        # Age in days
        age_days = (now - created_at.replace(tzinfo=None)).days

        # Decay function: half-life of 180 days
        # 0 days = 1.0, 180 days = 0.5, 360 days = 0.25
        half_life = 180
        score = math.pow(0.5, age_days / half_life)

        return max(0.0, min(1.0, score))

    def _get_impact_score(self, decision: Dict) -> float:
        """Get impact level score (0-1)."""
        impact = decision.get("impact", decision.get("blast_radius", "IMPORTANT"))

        if hasattr(impact, 'value'):
            impact = impact.value

        return self.IMPACT_SCORES.get(str(impact).upper(), 0.5)

    def _get_path_match_score(self, decision: Dict, file_path: str) -> float:
        """Get file path match score (0-1)."""
        if not file_path:
            return 0.0

        applies_to = decision.get("applies_to", [])
        if not applies_to:
            return 0.0

        file_path_lower = file_path.lower()
        best_score = 0.0

        for pattern in applies_to:
            pattern_lower = pattern.lower()

            # Exact match
            if pattern_lower == file_path_lower:
                return 1.0

            # Glob-style match
            if "*" in pattern_lower:
                # Simple glob: *.tsx, src/*, etc.
                if pattern_lower.startswith("*"):
                    if file_path_lower.endswith(pattern_lower[1:]):
                        best_score = max(best_score, 0.9)
                elif pattern_lower.endswith("*"):
                    if file_path_lower.startswith(pattern_lower[:-1]):
                        best_score = max(best_score, 0.9)
                elif file_path_lower.find(pattern_lower.replace("*", "")) >= 0:
                    best_score = max(best_score, 0.7)

            # Substring match
            elif pattern_lower in file_path_lower:
                # Longer pattern = better match
                match_ratio = len(pattern_lower) / len(file_path_lower)
                best_score = max(best_score, 0.5 + 0.3 * match_ratio)

            # Directory match
            elif "/" in pattern_lower and pattern_lower in file_path_lower:
                best_score = max(best_score, 0.6)

        return best_score

    def clear_cache(self):
        """Clear internal caches."""
        self._quality_cache.clear()
        self._usage_cache.clear()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "RankingFactors",
    "RankedResult",
    "RelevanceRanker",
]
