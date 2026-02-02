"""
Decision Suggester - AI-Powered Gap Detection

Analyzes codebase and existing decisions to suggest:
1. Missing decisions (gaps in coverage)
2. Outdated decisions (tech stack changed)
3. Conflicting decisions (contradictions)
4. Overly broad decisions (should be split)

SUGGESTION TYPES:
- NEW:      Decision needed for uncovered area
- UPDATE:   Existing decision needs refresh
- SPLIT:    Decision too broad, split into specifics
- MERGE:    Multiple decisions overlap, consolidate
- RETIRE:   Decision no longer relevant
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from enum import Enum
from datetime import datetime, timedelta


class SuggestionType(str, Enum):
    """Types of suggestions."""
    NEW = "NEW"           # Create new decision
    UPDATE = "UPDATE"     # Update existing
    SPLIT = "SPLIT"       # Split into multiple
    MERGE = "MERGE"       # Merge overlapping
    RETIRE = "RETIRE"     # Mark as retired


class SuggestionPriority(str, Enum):
    """Suggestion priority levels."""
    CRITICAL = "CRITICAL"  # Blocking issue
    HIGH = "HIGH"          # Should address soon
    MEDIUM = "MEDIUM"      # Nice to have
    LOW = "LOW"            # Minor improvement


@dataclass
class Suggestion:
    """Single suggestion for decision improvement."""
    suggestion_id: str
    suggestion_type: SuggestionType
    priority: SuggestionPriority
    title: str
    description: str
    rationale: str

    # For NEW suggestions
    suggested_domain: Optional[str] = None
    suggested_aspect: Optional[str] = None
    suggested_statement: Optional[str] = None

    # For UPDATE/SPLIT/MERGE/RETIRE
    affected_decision_ids: List[str] = field(default_factory=list)

    # Evidence
    evidence: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.5  # 0-1 how confident in suggestion

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "type": self.suggestion_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "suggested_domain": self.suggested_domain,
            "suggested_aspect": self.suggested_aspect,
            "suggested_statement": self.suggested_statement,
            "affected_decisions": self.affected_decision_ids,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


class DecisionSuggester:
    """
    Analyzes decisions and suggests improvements.

    Uses heuristics and patterns to identify gaps and issues.
    Can be extended with AI model for smarter suggestions.
    """

    # Common tech patterns that should have decisions
    COMMON_PATTERNS = {
        "react": {
            "domain": "ARCH",
            "aspect": "A06",
            "topics": ["component structure", "state management", "styling"],
        },
        "api": {
            "domain": "ARCH",
            "aspect": "A08",
            "topics": ["endpoint naming", "versioning", "error handling"],
        },
        "auth": {
            "domain": "CTL",
            "aspect": "A11",
            "topics": ["authentication method", "session handling", "permissions"],
        },
        "database": {
            "domain": "ARCH",
            "aspect": "A07",
            "topics": ["schema design", "migrations", "naming conventions"],
        },
        "testing": {
            "domain": "EVO",
            "aspect": "A16",
            "topics": ["test coverage", "test patterns", "CI integration"],
        },
    }

    def __init__(
        self,
        usage_tracker: Optional[Any] = None,
        quality_scorer: Optional[Any] = None,
    ):
        """
        Initialize suggester.

        Args:
            usage_tracker: For detecting unused decisions
            quality_scorer: For detecting low quality decisions
        """
        self.usage_tracker = usage_tracker
        self.quality_scorer = quality_scorer
        self._suggestion_counter = 0

    def analyze(
        self,
        decisions: List[Dict[str, Any]],
        codebase_context: Optional[Dict[str, Any]] = None,
    ) -> List[Suggestion]:
        """
        Analyze decisions and generate suggestions.

        Args:
            decisions: Existing decisions
            codebase_context: Info about codebase (tech stack, file patterns)

        Returns:
            List of suggestions
        """
        suggestions = []

        # Detect coverage gaps
        suggestions.extend(self._detect_gaps(decisions, codebase_context))

        # Detect outdated decisions
        suggestions.extend(self._detect_outdated(decisions))

        # Detect overlapping decisions
        suggestions.extend(self._detect_overlaps(decisions))

        # Detect low quality decisions
        suggestions.extend(self._detect_low_quality(decisions))

        # Detect unused decisions
        suggestions.extend(self._detect_unused(decisions))

        # Sort by priority
        priority_order = {
            SuggestionPriority.CRITICAL: 0,
            SuggestionPriority.HIGH: 1,
            SuggestionPriority.MEDIUM: 2,
            SuggestionPriority.LOW: 3,
        }
        suggestions.sort(key=lambda s: priority_order[s.priority])

        return suggestions

    def suggest_for_context(
        self,
        context: Dict[str, Any],
        existing_decisions: List[Dict[str, Any]],
    ) -> List[Suggestion]:
        """
        Suggest decisions for a specific context (file, task).

        Args:
            context: Current context (file_path, task_type, etc.)
            existing_decisions: Already matched decisions

        Returns:
            Suggestions for what's missing
        """
        suggestions = []
        file_path = context.get("file_path", "").lower()
        query = context.get("query", "").lower()

        # Detect tech from context
        detected_tech = set()
        for tech, info in self.COMMON_PATTERNS.items():
            if tech in file_path or tech in query:
                detected_tech.add(tech)

        # Check extension patterns
        if file_path.endswith(('.tsx', '.jsx')):
            detected_tech.add('react')
        if '/api/' in file_path or '/routes/' in file_path:
            detected_tech.add('api')
        if '/auth/' in file_path:
            detected_tech.add('auth')
        if file_path.endswith('.sql') or 'migration' in file_path:
            detected_tech.add('database')
        if 'test' in file_path or 'spec' in file_path:
            detected_tech.add('testing')

        # Check which detected tech has decisions
        existing_domains = set()
        existing_tags = set()
        for d in existing_decisions:
            existing_domains.add(d.get("domain_id"))
            existing_tags.update(t.lower() for t in d.get("tags", []))

        # Suggest for uncovered tech
        for tech in detected_tech:
            if tech not in existing_tags:
                pattern_info = self.COMMON_PATTERNS.get(tech, {})
                for topic in pattern_info.get("topics", []):
                    self._suggestion_counter += 1
                    suggestions.append(Suggestion(
                        suggestion_id=f"sug_{self._suggestion_counter}",
                        suggestion_type=SuggestionType.NEW,
                        priority=SuggestionPriority.MEDIUM,
                        title=f"Decision needed: {tech} {topic}",
                        description=f"Working with {tech} code but no decision for {topic}",
                        rationale=f"File {file_path} involves {tech} but no relevant decision exists",
                        suggested_domain=pattern_info.get("domain"),
                        suggested_aspect=pattern_info.get("aspect"),
                        suggested_statement=f"Define standards for {tech} {topic}",
                        evidence=[file_path],
                        confidence=0.6,
                    ))

        return suggestions

    def _detect_gaps(
        self,
        decisions: List[Dict[str, Any]],
        codebase_context: Optional[Dict[str, Any]],
    ) -> List[Suggestion]:
        """Detect coverage gaps based on codebase."""
        suggestions = []

        if not codebase_context:
            return suggestions

        tech_stack = codebase_context.get("tech_stack", [])
        file_patterns = codebase_context.get("file_patterns", [])

        # Check which tech stack items have decisions
        covered_tech = set()
        for d in decisions:
            covered_tech.update(t.lower() for t in d.get("tags", []))
            covered_tech.update(t.lower() for t in d.get("tech_stack", []))

        for tech in tech_stack:
            tech_lower = tech.lower()
            if tech_lower not in covered_tech:
                pattern_info = self.COMMON_PATTERNS.get(tech_lower, {})
                self._suggestion_counter += 1
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{self._suggestion_counter}",
                    suggestion_type=SuggestionType.NEW,
                    priority=SuggestionPriority.HIGH,
                    title=f"No decision for {tech}",
                    description=f"Tech stack includes {tech} but no decisions cover it",
                    rationale="Team should document standards for this technology",
                    suggested_domain=pattern_info.get("domain", "ARCH"),
                    suggested_aspect=pattern_info.get("aspect", "A06"),
                    evidence=[f"Tech stack: {tech}"],
                    confidence=0.8,
                ))

        return suggestions

    def _detect_outdated(
        self,
        decisions: List[Dict[str, Any]],
    ) -> List[Suggestion]:
        """Detect potentially outdated decisions."""
        suggestions = []
        now = datetime.utcnow()
        stale_threshold = timedelta(days=365)  # 1 year

        for d in decisions:
            created_at = d.get("created_at")
            if not created_at:
                continue

            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    continue

            created_at = created_at.replace(tzinfo=None)
            age = now - created_at

            if age > stale_threshold:
                decision_id = d.get("decision_id", "unknown")
                code = d.get("code", d.get("decision_code", ""))

                self._suggestion_counter += 1
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{self._suggestion_counter}",
                    suggestion_type=SuggestionType.UPDATE,
                    priority=SuggestionPriority.MEDIUM,
                    title=f"Review {code}: over 1 year old",
                    description=f"Decision was created {age.days} days ago",
                    rationale="Technology and practices may have changed",
                    affected_decision_ids=[decision_id],
                    evidence=[f"Created: {created_at.date()}"],
                    confidence=0.5,
                ))

        return suggestions

    def _detect_overlaps(
        self,
        decisions: List[Dict[str, Any]],
    ) -> List[Suggestion]:
        """Detect overlapping decisions that might need merging."""
        suggestions = []

        # Group by domain+aspect
        by_category = {}
        for d in decisions:
            key = (d.get("domain_id"), d.get("aspect_id"))
            if key not in by_category:
                by_category[key] = []
            by_category[key].append(d)

        # Check for potential overlaps within category
        for (domain, aspect), group in by_category.items():
            if len(group) > 5:  # Too many in same category
                decision_ids = [d.get("decision_id") for d in group]
                codes = [d.get("code", d.get("decision_code", "")) for d in group]

                self._suggestion_counter += 1
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{self._suggestion_counter}",
                    suggestion_type=SuggestionType.MERGE,
                    priority=SuggestionPriority.LOW,
                    title=f"Consider merging {domain}/{aspect} decisions",
                    description=f"{len(group)} decisions in same category",
                    rationale="Multiple similar decisions may cause confusion",
                    affected_decision_ids=decision_ids[:10],
                    evidence=[f"Decisions: {', '.join(codes[:5])}"],
                    confidence=0.4,
                ))

        return suggestions

    def _detect_low_quality(
        self,
        decisions: List[Dict[str, Any]],
    ) -> List[Suggestion]:
        """Detect low quality decisions."""
        suggestions = []

        if not self.quality_scorer:
            return suggestions

        for d in decisions:
            score = self.quality_scorer.score(d)
            if score.overall_score < 50:
                decision_id = d.get("decision_id", "unknown")
                code = d.get("code", d.get("decision_code", ""))

                self._suggestion_counter += 1
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{self._suggestion_counter}",
                    suggestion_type=SuggestionType.UPDATE,
                    priority=SuggestionPriority.HIGH,
                    title=f"Improve {code}: quality score {score.overall_score}/100",
                    description=f"Decision rated as {score.grade.value}",
                    rationale="; ".join(score.top_suggestions[:2]),
                    affected_decision_ids=[decision_id],
                    evidence=score.top_suggestions[:3],
                    confidence=0.8,
                ))

        return suggestions

    def _detect_unused(
        self,
        decisions: List[Dict[str, Any]],
    ) -> List[Suggestion]:
        """Detect unused decisions."""
        suggestions = []

        if not self.usage_tracker:
            return suggestions

        for d in decisions:
            decision_id = d.get("decision_id")
            if not decision_id:
                continue

            stats = self.usage_tracker.get_stats(decision_id)
            if stats.total_retrievals == 0:
                code = d.get("code", d.get("decision_code", ""))

                self._suggestion_counter += 1
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{self._suggestion_counter}",
                    suggestion_type=SuggestionType.RETIRE,
                    priority=SuggestionPriority.LOW,
                    title=f"Consider retiring {code}: never used",
                    description="Decision has never been retrieved",
                    rationale="May be obsolete or too specific",
                    affected_decision_ids=[decision_id],
                    evidence=["0 retrievals since tracking began"],
                    confidence=0.5,
                ))

        return suggestions


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SuggestionType",
    "SuggestionPriority",
    "Suggestion",
    "DecisionSuggester",
]
