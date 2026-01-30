"""
Confidence Scoring - Match Certainty Assessment

Provides confidence scores and reasons for why a decision was matched.

CONFIDENCE LEVELS:
- HIGH (0.8-1.0):   Direct pattern match, exact keyword, high vector similarity
- MEDIUM (0.5-0.8): Semantic similarity, partial keyword match
- LOW (0.3-0.5):    Weak semantic match, tag-only match
- UNCERTAIN (<0.3): Speculative, should probably not be included

REASONS:
Each confidence score includes human-readable reason explaining the match.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence level classification."""
    HIGH = "HIGH"           # 0.8-1.0
    MEDIUM = "MEDIUM"       # 0.5-0.8
    LOW = "LOW"             # 0.3-0.5
    UNCERTAIN = "UNCERTAIN"  # < 0.3


@dataclass
class ConfidenceReason:
    """Single reason contributing to confidence."""
    factor: str           # e.g., "path_match", "keyword", "semantic"
    description: str      # Human-readable explanation
    contribution: float   # How much this factor contributes (0-1)
    evidence: Optional[str] = None  # Specific evidence (e.g., matched pattern)


@dataclass
class ConfidenceResult:
    """Complete confidence assessment for a match."""
    decision_id: str
    confidence: float                # 0-1 overall confidence
    level: ConfidenceLevel           # Classified level
    reasons: List[ConfidenceReason] = field(default_factory=list)
    primary_reason: str = ""         # Single-line summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "decision_id": self.decision_id,
            "confidence": round(self.confidence, 2),
            "level": self.level.value,
            "reason": self.primary_reason,
            "details": [
                {
                    "factor": r.factor,
                    "description": r.description,
                    "contribution": round(r.contribution, 2),
                    "evidence": r.evidence,
                }
                for r in self.reasons
            ],
        }


class ConfidenceScorer:
    """
    Calculates confidence scores with explanations.

    Analyzes multiple signals to determine how confident we are
    that a decision is relevant to the current context.
    """

    # Thresholds for level classification
    THRESHOLDS = {
        ConfidenceLevel.HIGH: 0.8,
        ConfidenceLevel.MEDIUM: 0.5,
        ConfidenceLevel.LOW: 0.3,
    }

    def __init__(self):
        pass

    def score(
        self,
        decision_id: str,
        decision: Dict[str, Any],
        context: Dict[str, Any],
        search_scores: Dict[str, float],  # vector_score, keyword_score, etc.
    ) -> ConfidenceResult:
        """
        Calculate confidence score with reasons.

        Args:
            decision_id: Decision identifier
            decision: Decision data
            context: Query context (file_path, query, keywords, etc.)
            search_scores: Scores from search/ranking

        Returns:
            ConfidenceResult with score, level, and reasons
        """
        reasons = []
        total_contribution = 0.0

        # Analyze each confidence factor
        path_conf = self._analyze_path_match(decision, context)
        if path_conf:
            reasons.append(path_conf)
            total_contribution += path_conf.contribution

        keyword_conf = self._analyze_keyword_match(decision, context)
        if keyword_conf:
            reasons.append(keyword_conf)
            total_contribution += keyword_conf.contribution

        semantic_conf = self._analyze_semantic_match(search_scores)
        if semantic_conf:
            reasons.append(semantic_conf)
            total_contribution += semantic_conf.contribution

        tag_conf = self._analyze_tag_match(decision, context)
        if tag_conf:
            reasons.append(tag_conf)
            total_contribution += tag_conf.contribution

        domain_conf = self._analyze_domain_match(decision, context)
        if domain_conf:
            reasons.append(domain_conf)
            total_contribution += domain_conf.contribution

        # Calculate overall confidence (max 1.0)
        confidence = min(1.0, total_contribution)

        # Classify level
        level = self._classify_level(confidence)

        # Generate primary reason
        primary_reason = self._generate_primary_reason(reasons, level)

        return ConfidenceResult(
            decision_id=decision_id,
            confidence=confidence,
            level=level,
            reasons=sorted(reasons, key=lambda r: r.contribution, reverse=True),
            primary_reason=primary_reason,
        )

    def _analyze_path_match(
        self,
        decision: Dict,
        context: Dict,
    ) -> Optional[ConfidenceReason]:
        """Analyze file path matching."""
        file_path = context.get("file_path", "")
        if not file_path:
            return None

        applies_to = decision.get("applies_to", [])
        if not applies_to:
            return None

        file_path_lower = file_path.lower()

        for pattern in applies_to:
            pattern_lower = pattern.lower()

            # Exact match - highest confidence
            if pattern_lower == file_path_lower:
                return ConfidenceReason(
                    factor="path_match",
                    description="Exact file path match",
                    contribution=0.5,
                    evidence=f"Pattern '{pattern}' matches exactly",
                )

            # Glob match
            if "*" in pattern_lower:
                if self._glob_matches(pattern_lower, file_path_lower):
                    return ConfidenceReason(
                        factor="path_match",
                        description="File matches glob pattern",
                        contribution=0.4,
                        evidence=f"Pattern '{pattern}' matches file",
                    )

            # Directory match
            if pattern_lower in file_path_lower:
                return ConfidenceReason(
                    factor="path_match",
                    description="File in matching directory",
                    contribution=0.3,
                    evidence=f"Path contains '{pattern}'",
                )

        return None

    def _analyze_keyword_match(
        self,
        decision: Dict,
        context: Dict,
    ) -> Optional[ConfidenceReason]:
        """Analyze keyword matching."""
        query_keywords = context.get("keywords", [])
        if not query_keywords:
            query = context.get("query", "")
            query_keywords = query.lower().split()

        if not query_keywords:
            return None

        # Check tags, applies_to, and statement
        decision_keywords = set()
        decision_keywords.update(t.lower() for t in decision.get("tags", []))
        decision_keywords.update(a.lower() for a in decision.get("applies_to", []))

        statement = decision.get("statement", "").lower()
        decision_keywords.update(statement.split())

        # Find matches
        matches = [kw for kw in query_keywords if kw.lower() in decision_keywords]

        if not matches:
            return None

        # More matches = higher confidence
        match_ratio = len(matches) / len(query_keywords)
        contribution = 0.1 + 0.3 * match_ratio

        return ConfidenceReason(
            factor="keyword",
            description=f"Matched {len(matches)} keyword(s)",
            contribution=contribution,
            evidence=f"Keywords: {', '.join(matches[:5])}",
        )

    def _analyze_semantic_match(
        self,
        search_scores: Dict[str, float],
    ) -> Optional[ConfidenceReason]:
        """Analyze semantic/vector similarity."""
        vector_score = search_scores.get("vector_score", 0)

        if vector_score < 0.3:
            return None

        if vector_score >= 0.8:
            return ConfidenceReason(
                factor="semantic",
                description="High semantic similarity",
                contribution=0.4,
                evidence=f"Vector similarity: {vector_score:.0%}",
            )
        elif vector_score >= 0.5:
            return ConfidenceReason(
                factor="semantic",
                description="Moderate semantic similarity",
                contribution=0.25,
                evidence=f"Vector similarity: {vector_score:.0%}",
            )
        else:
            return ConfidenceReason(
                factor="semantic",
                description="Weak semantic similarity",
                contribution=0.1,
                evidence=f"Vector similarity: {vector_score:.0%}",
            )

    def _analyze_tag_match(
        self,
        decision: Dict,
        context: Dict,
    ) -> Optional[ConfidenceReason]:
        """Analyze tag matching."""
        context_tags = context.get("tags", [])
        if not context_tags:
            return None

        decision_tags = decision.get("tags", [])
        if not decision_tags:
            return None

        context_tags_lower = {t.lower() for t in context_tags}
        decision_tags_lower = {t.lower() for t in decision_tags}

        matches = context_tags_lower & decision_tags_lower

        if not matches:
            return None

        contribution = 0.1 + 0.1 * min(len(matches), 3)  # Max 0.4

        return ConfidenceReason(
            factor="tag",
            description=f"Matched {len(matches)} tag(s)",
            contribution=contribution,
            evidence=f"Tags: {', '.join(matches)}",
        )

    def _analyze_domain_match(
        self,
        decision: Dict,
        context: Dict,
    ) -> Optional[ConfidenceReason]:
        """Analyze domain/aspect matching."""
        context_domain = context.get("domain_id")
        if not context_domain:
            return None

        decision_domain = decision.get("domain_id")
        if hasattr(decision_domain, 'value'):
            decision_domain = decision_domain.value

        if not decision_domain:
            return None

        if str(context_domain).upper() == str(decision_domain).upper():
            return ConfidenceReason(
                factor="domain",
                description="Same domain",
                contribution=0.15,
                evidence=f"Domain: {decision_domain}",
            )

        return None

    def _glob_matches(self, pattern: str, path: str) -> bool:
        """Simple glob matching."""
        if pattern.startswith("*") and pattern.endswith("*"):
            return pattern[1:-1] in path
        elif pattern.startswith("*"):
            return path.endswith(pattern[1:])
        elif pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        elif "*" in pattern:
            parts = pattern.split("*")
            pos = 0
            for part in parts:
                if part:
                    idx = path.find(part, pos)
                    if idx < 0:
                        return False
                    pos = idx + len(part)
            return True
        return pattern == path

    def _classify_level(self, confidence: float) -> ConfidenceLevel:
        """Classify confidence into level."""
        if confidence >= self.THRESHOLDS[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif confidence >= self.THRESHOLDS[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        elif confidence >= self.THRESHOLDS[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN

    def _generate_primary_reason(
        self,
        reasons: List[ConfidenceReason],
        level: ConfidenceLevel,
    ) -> str:
        """Generate single-line summary of confidence."""
        if not reasons:
            return "No strong match signals"

        # Get top reason
        top_reason = max(reasons, key=lambda r: r.contribution)

        level_word = {
            ConfidenceLevel.HIGH: "High confidence",
            ConfidenceLevel.MEDIUM: "Moderate confidence",
            ConfidenceLevel.LOW: "Low confidence",
            ConfidenceLevel.UNCERTAIN: "Uncertain match",
        }[level]

        return f"{level_word}: {top_reason.description}"

    def filter_by_confidence(
        self,
        results: List[ConfidenceResult],
        min_level: ConfidenceLevel = ConfidenceLevel.LOW,
    ) -> List[ConfidenceResult]:
        """Filter results by minimum confidence level."""
        min_threshold = self.THRESHOLDS.get(min_level, 0.0)
        return [r for r in results if r.confidence >= min_threshold]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ConfidenceLevel",
    "ConfidenceReason",
    "ConfidenceResult",
    "ConfidenceScorer",
]
