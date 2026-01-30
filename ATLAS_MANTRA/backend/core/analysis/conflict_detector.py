"""
MANTRA Conflict Detection

Automated detection of field-level conflicts between decisions.

CONFLICT TYPES DETECTED:
1. MUST vs MUST_NOT - Direct contradiction
2. STRENGTHENS - SHOULD → MUST on same topic
3. WEAKENS - MUST → SHOULD on same topic
4. OVERLAP - Same applies_to with different rules

DETECTION METHODS:
1. Rule-based heuristics (keyword matching)
2. Semantic similarity (embedding comparison)
3. Pattern matching (file patterns, tags)
4. Scope-aware filtering (hierarchical scope paths)

SCOPE-AWARE DETECTION:
- Decisions in different scope branches (e.g., fe.react vs fe.vue) cannot conflict
- Parent scopes with inheritance can conflict with child scopes
- Global scope (*) can conflict with any scope
"""

from typing import List, Dict, Any, Optional, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import re

from ..domain.field_relation import (
    FieldRelation,
    RelationType,
    RelationConfidence,
    RelationSource,
    RelationGraph,
    FieldPath,
)

from ..domain.scope import scopes_can_conflict


class ConflictSeverity(str, Enum):
    """Severity of detected conflict."""
    CRITICAL = "CRITICAL"   # Must be resolved before approval
    HIGH = "HIGH"           # Strong conflict, needs review
    MEDIUM = "MEDIUM"       # Potential conflict
    LOW = "LOW"             # Minor overlap, informational


@dataclass
class DetectedConflict:
    """A detected conflict between fields."""
    source_decision_id: str
    source_decision_code: str
    source_field_path: str
    source_content: str

    target_decision_id: str
    target_decision_code: str
    target_field_path: str
    target_content: str

    conflict_type: RelationType
    severity: ConflictSeverity
    confidence: RelationConfidence

    description: str
    resolution_hints: List[str]

    # Scoring
    keyword_overlap: float  # 0-1
    semantic_similarity: Optional[float] = None  # 0-1, if available

    def to_field_relation(self, detected_by: str = "system") -> FieldRelation:
        """Convert to FieldRelation for storage."""
        return FieldRelation(
            relation_id="",  # Will be generated
            source_decision_id=self.source_decision_id,
            source_field_path=self.source_field_path,
            target_decision_id=self.target_decision_id,
            target_field_path=self.target_field_path,
            relation_type=self.conflict_type,
            confidence=self.confidence,
            source=RelationSource.RULE_BASED,
            description=self.description,
            rationale="; ".join(self.resolution_hints[:2]),
            created_by=detected_by,
            similarity_score=self.semantic_similarity or self.keyword_overlap,
        )


@dataclass
class ConflictDetectionResult:
    """Result of conflict detection."""
    decision_id: str
    conflicts: List[DetectedConflict]
    strengthens: List[DetectedConflict]
    weakens: List[DetectedConflict]
    overlaps: List[DetectedConflict]

    # Stats
    decisions_checked: int
    constraints_checked: int
    detection_time_ms: float = 0

    # Scope stats
    scope_filtered_out: int = 0  # Decisions skipped due to incompatible scope
    scope_path: str = "*"        # Scope path of the decision being checked

    @property
    def total_issues(self) -> int:
        return len(self.conflicts) + len(self.strengthens) + len(self.weakens)

    @property
    def has_critical(self) -> bool:
        return any(c.severity == ConflictSeverity.CRITICAL for c in self.conflicts)

    def all_relations(self) -> List[DetectedConflict]:
        """Get all detected relations."""
        return self.conflicts + self.strengthens + self.weakens + self.overlaps


class FieldConflictDetector:
    """
    Detects field-level conflicts between decisions.

    Analyzes constraints, statements, and invariants for:
    - Direct contradictions (MUST vs MUST_NOT)
    - Strengthening (SHOULD → MUST)
    - Weakening (MUST → SHOULD)
    - Overlapping rules on same topic
    """

    # Constraint type strength order (for strengthens/weakens)
    CONSTRAINT_STRENGTH = {
        "MUST": 4,
        "MUST_NOT": 4,
        "SHOULD": 3,
        "SHOULD_NOT": 3,
        "MAY": 2,
        "MAY_NOT": 2,
    }

    # Keywords that indicate topic
    TOPIC_KEYWORDS = [
        # Architecture
        "component", "module", "service", "api", "endpoint",
        "database", "cache", "queue", "event",
        # Frontend
        "react", "vue", "angular", "component", "hook", "state",
        "form", "validation", "ui", "ux",
        # Backend
        "controller", "service", "repository", "model",
        "auth", "security", "encryption", "token",
        # Data
        "schema", "migration", "index", "query",
        # Testing
        "test", "mock", "fixture", "coverage",
        # Deployment
        "deploy", "staging", "production", "docker", "kubernetes",
    ]

    # Stop words to ignore
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after",
        "all", "each", "every", "both", "few", "more", "most",
        "other", "some", "such", "no", "not", "only", "same",
        "and", "but", "or", "nor", "so", "yet", "if", "then",
        "use", "using", "used", "uses",
    }

    def __init__(
        self,
        existing_decisions: Optional[List[Dict[str, Any]]] = None,
        min_keyword_overlap: float = 0.3,
        min_confidence: RelationConfidence = RelationConfidence.LOW,
        scope_aware: bool = True,
    ):
        """
        Initialize detector.

        Args:
            existing_decisions: List of existing decisions to check against
            min_keyword_overlap: Minimum keyword overlap to consider (0-1)
            min_confidence: Minimum confidence to report
            scope_aware: If True, filter candidates by scope compatibility
        """
        self.existing_decisions = existing_decisions or []
        self.min_keyword_overlap = min_keyword_overlap
        self.min_confidence = min_confidence
        self.scope_aware = scope_aware

        # Build index for faster lookup
        self._decision_index: Dict[str, Dict[str, Any]] = {}
        self._tag_index: Dict[str, List[str]] = {}  # tag → decision_ids
        self._applies_to_index: Dict[str, List[str]] = {}  # pattern → decision_ids
        self._scope_index: Dict[str, Tuple[str, bool]] = {}  # decision_id → (scope_path, inheritance)

        self._build_indexes()

    def _build_indexes(self):
        """Build lookup indexes."""
        for decision in self.existing_decisions:
            dec_id = decision.get("decision_id", "")
            if not dec_id:
                continue

            self._decision_index[dec_id] = decision

            # Index by tags
            for tag in decision.get("tags", []):
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                self._tag_index[tag].append(dec_id)

            # Index by applies_to
            for pattern in decision.get("applies_to", []):
                if pattern not in self._applies_to_index:
                    self._applies_to_index[pattern] = []
                self._applies_to_index[pattern].append(dec_id)

            # Index by scope
            scope_path = decision.get("scope_path", "*")
            scope_inheritance = decision.get("scope_inheritance", True)
            self._scope_index[dec_id] = (scope_path, scope_inheritance)

    def detect_conflicts(
        self,
        new_decision: Dict[str, Any],
    ) -> ConflictDetectionResult:
        """
        Detect conflicts between new decision and existing decisions.

        Args:
            new_decision: The decision to check

        Returns:
            ConflictDetectionResult with all detected issues
        """
        import time
        start_time = time.time()

        decision_id = new_decision.get("decision_id", "unknown")
        decision_code = new_decision.get("code", "UNKNOWN")
        scope_path = new_decision.get("scope_path", "*")
        scope_inheritance = new_decision.get("scope_inheritance", True)

        conflicts = []
        strengthens = []
        weakens = []
        overlaps = []

        constraints_checked = 0
        decisions_checked = 0
        scope_filtered_out = 0

        # Get candidates (decisions that might conflict)
        all_candidates = self._get_candidates(new_decision)

        # Filter by scope if enabled
        if self.scope_aware:
            candidates = []
            for existing in all_candidates:
                existing_scope = existing.get("scope_path", "*")
                existing_inheritance = existing.get("scope_inheritance", True)

                can_conflict, reason = scopes_can_conflict(
                    scope_path, existing_scope,
                    scope_inheritance, existing_inheritance
                )

                if can_conflict:
                    candidates.append(existing)
                else:
                    scope_filtered_out += 1
        else:
            candidates = all_candidates

        decisions_checked = len(candidates)

        # Check each candidate
        for existing in candidates:
            existing_id = existing.get("decision_id", "")
            existing_code = existing.get("code", "")

            # Skip self
            if existing_id == decision_id:
                continue

            # Compare constraints
            new_constraints = new_decision.get("constraints", [])
            existing_constraints = existing.get("constraints", [])

            for i, new_c in enumerate(new_constraints):
                new_rule = self._get_rule_text(new_c)
                new_type = self._get_constraint_type(new_c)
                new_keywords = self._extract_keywords(new_rule)

                for j, existing_c in enumerate(existing_constraints):
                    existing_rule = self._get_rule_text(existing_c)
                    existing_type = self._get_constraint_type(existing_c)
                    existing_keywords = self._extract_keywords(existing_rule)

                    constraints_checked += 1

                    # Calculate keyword overlap
                    overlap = self._calculate_overlap(new_keywords, existing_keywords)

                    if overlap < self.min_keyword_overlap:
                        continue

                    # Determine conflict type and severity
                    conflict = self._analyze_constraint_pair(
                        source_id=decision_id,
                        source_code=decision_code,
                        source_idx=i,
                        source_rule=new_rule,
                        source_type=new_type,
                        source_keywords=new_keywords,
                        target_id=existing_id,
                        target_code=existing_code,
                        target_idx=j,
                        target_rule=existing_rule,
                        target_type=existing_type,
                        target_keywords=existing_keywords,
                        overlap=overlap,
                    )

                    if conflict:
                        if conflict.conflict_type == RelationType.CONFLICTS_WITH:
                            conflicts.append(conflict)
                        elif conflict.conflict_type == RelationType.STRENGTHENS:
                            strengthens.append(conflict)
                        elif conflict.conflict_type == RelationType.WEAKENS:
                            weakens.append(conflict)
                        else:
                            overlaps.append(conflict)

        elapsed_ms = (time.time() - start_time) * 1000

        return ConflictDetectionResult(
            decision_id=decision_id,
            conflicts=conflicts,
            strengthens=strengthens,
            weakens=weakens,
            overlaps=overlaps,
            decisions_checked=decisions_checked,
            constraints_checked=constraints_checked,
            detection_time_ms=elapsed_ms,
            scope_filtered_out=scope_filtered_out,
            scope_path=scope_path,
        )

    def _get_candidates(self, decision: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get candidate decisions that might conflict."""
        candidate_ids: Set[str] = set()

        # Same domain + aspect = high priority
        domain = decision.get("domain_id", "")
        aspect = decision.get("aspect_id", "")

        for existing in self.existing_decisions:
            if (existing.get("domain_id") == domain and
                existing.get("aspect_id") == aspect):
                candidate_ids.add(existing.get("decision_id", ""))

        # Same tags
        for tag in decision.get("tags", []):
            for dec_id in self._tag_index.get(tag, []):
                candidate_ids.add(dec_id)

        # Overlapping applies_to
        for pattern in decision.get("applies_to", []):
            for dec_id in self._applies_to_index.get(pattern, []):
                candidate_ids.add(dec_id)

        # Return candidate decisions
        return [
            self._decision_index[dec_id]
            for dec_id in candidate_ids
            if dec_id in self._decision_index
        ]

    def _get_rule_text(self, constraint: Any) -> str:
        """Extract rule text from constraint."""
        if isinstance(constraint, dict):
            return constraint.get("rule", "")
        return str(constraint)

    def _get_constraint_type(self, constraint: Any) -> str:
        """Extract constraint type."""
        if isinstance(constraint, dict):
            return constraint.get("type", "MUST")

        # Detect from text
        text = str(constraint).upper()
        if text.startswith("MUST NOT"):
            return "MUST_NOT"
        elif text.startswith("MUST"):
            return "MUST"
        elif text.startswith("SHOULD NOT"):
            return "SHOULD_NOT"
        elif text.startswith("SHOULD"):
            return "SHOULD"
        elif text.startswith("MAY NOT"):
            return "MAY_NOT"
        elif text.startswith("MAY"):
            return "MAY"
        return "MUST"

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        # Normalize
        text = text.lower()
        # Remove special chars
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Split into words
        words = text.split()
        # Filter
        keywords = {
            w for w in words
            if len(w) > 2 and w not in self.STOP_WORDS
        }
        return keywords

    def _calculate_overlap(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard-like overlap between keyword sets."""
        if not set1 or not set2:
            return 0.0

        intersection = set1 & set2
        union = set1 | set2

        if not union:
            return 0.0

        # Weighted by topic keywords
        topic_intersection = intersection & set(self.TOPIC_KEYWORDS)
        if topic_intersection:
            # Boost if topic keywords match
            return min(1.0, (len(intersection) / len(union)) + 0.2 * len(topic_intersection))

        return len(intersection) / len(union)

    def _analyze_constraint_pair(
        self,
        source_id: str,
        source_code: str,
        source_idx: int,
        source_rule: str,
        source_type: str,
        source_keywords: Set[str],
        target_id: str,
        target_code: str,
        target_idx: int,
        target_rule: str,
        target_type: str,
        target_keywords: Set[str],
        overlap: float,
    ) -> Optional[DetectedConflict]:
        """Analyze a pair of constraints for conflicts."""

        # Determine conflict type
        conflict_type = None
        severity = ConflictSeverity.LOW
        confidence = RelationConfidence.LOW
        description = ""
        hints = []

        source_strength = self.CONSTRAINT_STRENGTH.get(source_type, 2)
        target_strength = self.CONSTRAINT_STRENGTH.get(target_type, 2)

        # Case 1: Direct contradiction (MUST vs MUST_NOT on same topic)
        if (source_type == "MUST" and target_type == "MUST_NOT") or \
           (source_type == "MUST_NOT" and target_type == "MUST"):
            conflict_type = RelationType.CONFLICTS_WITH
            severity = ConflictSeverity.CRITICAL if overlap > 0.5 else ConflictSeverity.HIGH
            confidence = RelationConfidence.HIGH if overlap > 0.5 else RelationConfidence.MEDIUM
            description = f"MUST vs MUST_NOT conflict: '{source_rule[:50]}...' contradicts '{target_rule[:50]}...'"
            hints = [
                "Determine if these apply to different contexts",
                "Consider if one should supersede the other",
                f"Review overlap keywords: {', '.join(source_keywords & target_keywords)}"
            ]

        # Case 2: STRENGTHENS (SHOULD → MUST on same topic)
        elif source_type == "MUST" and target_type == "SHOULD":
            conflict_type = RelationType.STRENGTHENS
            severity = ConflictSeverity.MEDIUM
            confidence = RelationConfidence.MEDIUM if overlap > 0.4 else RelationConfidence.LOW
            description = f"Strengthening: New MUST may tighten existing SHOULD"
            hints = [
                "Verify this is intentional tightening",
                "Update or deprecate the SHOULD if MUST is correct"
            ]

        # Case 3: WEAKENS (MUST → SHOULD on same topic)
        elif source_type == "SHOULD" and target_type == "MUST":
            conflict_type = RelationType.WEAKENS
            severity = ConflictSeverity.HIGH
            confidence = RelationConfidence.MEDIUM if overlap > 0.4 else RelationConfidence.LOW
            description = f"Weakening: New SHOULD may weaken existing MUST"
            hints = [
                "Verify this is intentional relaxation",
                "Keep the MUST if the rule should remain strict"
            ]

        # Case 4: Same type, overlapping topic (potential redundancy)
        elif source_type == target_type and overlap > 0.5:
            conflict_type = RelationType.REFERENCES
            severity = ConflictSeverity.LOW
            confidence = RelationConfidence.LOW
            description = f"Potential overlap: similar {source_type} rules"
            hints = [
                "Check if rules are redundant",
                "Consider consolidating into one decision"
            ]

        if not conflict_type:
            return None

        # Filter by minimum confidence
        if self._confidence_value(confidence) < self._confidence_value(self.min_confidence):
            return None

        return DetectedConflict(
            source_decision_id=source_id,
            source_decision_code=source_code,
            source_field_path=f"constraints[{source_idx}].rule",
            source_content=source_rule,
            target_decision_id=target_id,
            target_decision_code=target_code,
            target_field_path=f"constraints[{target_idx}].rule",
            target_content=target_rule,
            conflict_type=conflict_type,
            severity=severity,
            confidence=confidence,
            description=description,
            resolution_hints=hints,
            keyword_overlap=overlap,
        )

    def _confidence_value(self, confidence: RelationConfidence) -> int:
        """Convert confidence to numeric value for comparison."""
        return {
            RelationConfidence.CERTAIN: 4,
            RelationConfidence.HIGH: 3,
            RelationConfidence.MEDIUM: 2,
            RelationConfidence.LOW: 1,
        }.get(confidence, 0)

    def load_decisions(self, decisions: List[Dict[str, Any]]):
        """Load or reload existing decisions."""
        self.existing_decisions = decisions
        self._decision_index = {}
        self._tag_index = {}
        self._applies_to_index = {}
        self._scope_index = {}
        self._build_indexes()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def detect_conflicts_for_decision(
    decision: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]],
    min_overlap: float = 0.3,
    scope_aware: bool = True,
) -> ConflictDetectionResult:
    """
    Simple interface to detect conflicts.

    Args:
        decision: New decision to check
        existing_decisions: Existing decisions to check against
        min_overlap: Minimum keyword overlap threshold
        scope_aware: If True, filter candidates by scope compatibility
                     (fe.react vs fe.vue decisions cannot conflict)

    Returns:
        ConflictDetectionResult
    """
    detector = FieldConflictDetector(
        existing_decisions=existing_decisions,
        min_keyword_overlap=min_overlap,
        scope_aware=scope_aware,
    )
    return detector.detect_conflicts(decision)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ConflictSeverity",
    "DetectedConflict",
    "ConflictDetectionResult",
    "FieldConflictDetector",
    "detect_conflicts_for_decision",
]
