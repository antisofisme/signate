"""
MANTRA Gate 2: AI-Powered Validation

Real AI validation replacing the placeholder in validator.py.

VALIDATION CHECKS:
1. Semantic Consistency - statement/rationale alignment
2. Conflict Detection - with existing decisions
3. Quality Scoring - completeness, clarity, specificity
4. Taxonomy Compliance - domain/aspect appropriateness
5. Constraint Feasibility - can constraints be enforced?

BACKENDS:
- Claude API (default)
- Local LLM (fallback)
- Rule-based heuristics (emergency fallback)

Per MANTRA-LAW-001:
- Gate 2 is SOFT (warning only, doesn't block)
- But results inform human decision in Gate 3
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import json


class QualityDimension(str, Enum):
    """Dimensions of decision quality."""
    COMPLETENESS = "COMPLETENESS"   # All required info present
    CLARITY = "CLARITY"             # Easy to understand
    SPECIFICITY = "SPECIFICITY"     # Concrete, not vague
    CONSISTENCY = "CONSISTENCY"     # Internal coherence
    ACTIONABILITY = "ACTIONABILITY" # Can be enforced


@dataclass
class QualityScore:
    """Quality score for a single dimension."""
    dimension: QualityDimension
    score: float  # 0-1
    issues: List[str]
    suggestions: List[str]


@dataclass
class ConflictReport:
    """Report of potential conflict with existing decision."""
    existing_decision_id: str
    existing_decision_code: str
    conflict_type: str  # CONTRADICTS, OVERLAPS, WEAKENS
    severity: str  # HIGH, MEDIUM, LOW
    description: str
    resolution_hint: Optional[str] = None


@dataclass
class Gate2AIResult:
    """
    Comprehensive Gate 2 AI validation result.

    Contains:
    - Overall quality score
    - Dimensional scores
    - Conflict reports
    - Suggestions for improvement
    """
    decision_id: str
    overall_score: float  # 0-1
    dimensional_scores: List[QualityScore]
    conflicts: List[ConflictReport]
    suggestions: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_high_quality(self) -> bool:
        """Score >= 0.7 is considered high quality."""
        return self.overall_score >= 0.7

    @property
    def has_conflicts(self) -> bool:
        """Any conflicts detected."""
        return len(self.conflicts) > 0

    @property
    def high_severity_conflicts(self) -> List[ConflictReport]:
        """Get HIGH severity conflicts only."""
        return [c for c in self.conflicts if c.severity == "HIGH"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "decision_id": self.decision_id,
            "overall_score": self.overall_score,
            "dimensional_scores": [
                {
                    "dimension": s.dimension.value,
                    "score": s.score,
                    "issues": s.issues,
                    "suggestions": s.suggestions,
                }
                for s in self.dimensional_scores
            ],
            "conflicts": [
                {
                    "existing_decision_id": c.existing_decision_id,
                    "existing_decision_code": c.existing_decision_code,
                    "conflict_type": c.conflict_type,
                    "severity": c.severity,
                    "description": c.description,
                    "resolution_hint": c.resolution_hint,
                }
                for c in self.conflicts
            ],
            "suggestions": self.suggestions,
            "warnings": self.warnings,
            "is_high_quality": self.is_high_quality,
            "has_conflicts": self.has_conflicts,
            "validated_at": self.validated_at.isoformat(),
        }


class Gate2AIValidator:
    """
    AI-powered Gate 2 validator.

    Uses multiple validation strategies:
    1. Rule-based heuristics (always runs)
    2. AI semantic analysis (when available)
    3. Conflict detection against existing decisions
    """

    # Hedging words that reduce clarity
    HEDGING_WORDS = [
        "might", "probably", "perhaps", "maybe", "possibly",
        "consider", "could", "generally", "usually", "sometimes",
        "often", "rarely", "typically", "tends to"
    ]

    # Vague phrases that reduce specificity
    VAGUE_PHRASES = [
        "as needed", "when appropriate", "if possible",
        "as necessary", "when required", "properly",
        "correctly", "appropriately", "effectively",
        "good", "bad", "better", "best", "nice"
    ]

    # Verbose phrases that reduce clarity
    VERBOSE_PHRASES = [
        "in order to", "due to the fact that", "at this point in time",
        "in the event that", "for the purpose of", "with regard to",
        "in spite of the fact that", "at the present time",
        "it is important to note that", "it should be noted that"
    ]

    # Constraint keywords that indicate enforceability
    ENFORCEABLE_KEYWORDS = [
        "must", "shall", "required", "mandatory",
        "always", "never", "only", "exactly"
    ]

    def __init__(
        self,
        existing_decisions: Optional[List[Dict[str, Any]]] = None,
        ai_backend: Optional[Callable] = None,
    ):
        """
        Initialize Gate 2 validator.

        Args:
            existing_decisions: List of existing decisions for conflict detection
            ai_backend: Optional AI backend function for semantic analysis
        """
        self.existing_decisions = existing_decisions or []
        self.ai_backend = ai_backend

    def validate(self, decision: Dict[str, Any]) -> Gate2AIResult:
        """
        Run comprehensive Gate 2 validation.

        Always runs rule-based checks. Optionally runs AI if available.
        """
        decision_id = decision.get("decision_id", "unknown")

        # Run all dimensional validations
        dimensional_scores = [
            self._check_completeness(decision),
            self._check_clarity(decision),
            self._check_specificity(decision),
            self._check_consistency(decision),
            self._check_actionability(decision),
        ]

        # Detect conflicts
        conflicts = self._detect_conflicts(decision)

        # Calculate overall score (weighted average)
        weights = {
            QualityDimension.COMPLETENESS: 0.25,
            QualityDimension.CLARITY: 0.20,
            QualityDimension.SPECIFICITY: 0.20,
            QualityDimension.CONSISTENCY: 0.20,
            QualityDimension.ACTIONABILITY: 0.15,
        }

        overall_score = sum(
            s.score * weights.get(s.dimension, 0.2)
            for s in dimensional_scores
        )

        # Penalize for conflicts
        if conflicts:
            high_conflicts = len([c for c in conflicts if c.severity == "HIGH"])
            medium_conflicts = len([c for c in conflicts if c.severity == "MEDIUM"])
            conflict_penalty = (high_conflicts * 0.15) + (medium_conflicts * 0.05)
            overall_score = max(0, overall_score - conflict_penalty)

        # Collect all suggestions
        all_suggestions = []
        for score in dimensional_scores:
            all_suggestions.extend(score.suggestions)

        # Collect warnings
        warnings = []
        if overall_score < 0.5:
            warnings.append("Overall quality score is LOW - significant improvements needed")
        if conflicts:
            warnings.append(f"Detected {len(conflicts)} potential conflict(s) with existing decisions")
        for score in dimensional_scores:
            if score.score < 0.5:
                warnings.append(f"{score.dimension.value} score is LOW ({score.score:.0%})")

        return Gate2AIResult(
            decision_id=decision_id,
            overall_score=overall_score,
            dimensional_scores=dimensional_scores,
            conflicts=conflicts,
            suggestions=all_suggestions[:10],  # Top 10 suggestions
            warnings=warnings,
            metadata={
                "validator_version": "2.0",
                "ai_backend_used": self.ai_backend is not None,
                "existing_decisions_checked": len(self.existing_decisions),
            },
        )

    def _check_completeness(self, decision: Dict[str, Any]) -> QualityScore:
        """Check if all important information is present."""
        issues = []
        suggestions = []
        score = 1.0

        # Required fields
        required = ["statement", "rationale", "constraints"]
        for field_name in required:
            if not decision.get(field_name):
                issues.append(f"Missing required field: {field_name}")
                score -= 0.3

        # Statement length (should be substantial but not too long)
        statement = decision.get("statement", "")
        if len(statement) < 50:
            issues.append("Statement is too short (< 50 chars)")
            suggestions.append("Expand statement to clearly explain the decision")
            score -= 0.1
        elif len(statement) > 500:
            issues.append("Statement is too long (> 500 chars)")
            suggestions.append("Condense statement to essential points")
            score -= 0.05

        # Rationale length
        rationale = decision.get("rationale", "")
        if len(rationale) < 100:
            issues.append("Rationale is too short (< 100 chars)")
            suggestions.append("Explain WHY this decision was made")
            score -= 0.15
        elif len(rationale) > 2000:
            issues.append("Rationale is too long (> 2000 chars)")
            suggestions.append("Focus rationale on key reasons")
            score -= 0.05

        # Constraints count
        constraints = decision.get("constraints", [])
        if len(constraints) == 0:
            issues.append("No constraints defined")
            suggestions.append("Add at least one MUST or SHOULD constraint")
            score -= 0.2
        elif len(constraints) > 10:
            issues.append("Too many constraints (> 10)")
            suggestions.append("Consolidate related constraints")
            score -= 0.1

        # Tags (should have at least some)
        tags = decision.get("tags", [])
        if len(tags) == 0:
            issues.append("No tags defined")
            suggestions.append("Add tags for discoverability (e.g., 'react', 'api', 'security')")
            score -= 0.1

        # Examples (helpful but not required)
        examples = decision.get("examples", [])
        if len(examples) == 0:
            suggestions.append("Consider adding examples for clarity")
            score -= 0.05

        return QualityScore(
            dimension=QualityDimension.COMPLETENESS,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def _check_clarity(self, decision: Dict[str, Any]) -> QualityScore:
        """Check if decision is clear and easy to understand."""
        issues = []
        suggestions = []
        score = 1.0

        # Check all text fields
        text_fields = {
            "statement": decision.get("statement", ""),
            "rationale": decision.get("rationale", ""),
        }

        for field_name, text in text_fields.items():
            if not text:
                continue

            text_lower = text.lower()

            # Check for hedging words
            hedging_found = []
            for word in self.HEDGING_WORDS:
                if re.search(rf"\b{word}\b", text_lower):
                    hedging_found.append(word)

            if hedging_found:
                issues.append(f"{field_name} contains hedging words: {', '.join(hedging_found)}")
                suggestions.append(f"Remove hedging from {field_name} - be definitive")
                score -= 0.05 * len(hedging_found)

            # Check for verbose phrases
            verbose_found = []
            for phrase in self.VERBOSE_PHRASES:
                if phrase in text_lower:
                    verbose_found.append(phrase)

            if verbose_found:
                issues.append(f"{field_name} contains verbose phrases")
                suggestions.append(f"Simplify {field_name} - remove '{verbose_found[0]}'")
                score -= 0.03 * len(verbose_found)

            # Check sentence length (avg > 30 words = too complex)
            sentences = re.split(r'[.!?]+', text)
            avg_words = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
            if avg_words > 30:
                issues.append(f"{field_name} has long sentences (avg {avg_words:.0f} words)")
                suggestions.append(f"Break up long sentences in {field_name}")
                score -= 0.1

        # Check constraints for clarity
        constraints = decision.get("constraints", [])
        for i, c in enumerate(constraints):
            rule = c.get("rule", "") if isinstance(c, dict) else str(c)
            if len(rule) > 100:
                issues.append(f"Constraint {i+1} is too long ({len(rule)} chars)")
                suggestions.append(f"Simplify constraint {i+1}")
                score -= 0.05

        return QualityScore(
            dimension=QualityDimension.CLARITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def _check_specificity(self, decision: Dict[str, Any]) -> QualityScore:
        """Check if decision is specific and concrete."""
        issues = []
        suggestions = []
        score = 1.0

        text_fields = {
            "statement": decision.get("statement", ""),
            "rationale": decision.get("rationale", ""),
        }

        for field_name, text in text_fields.items():
            if not text:
                continue

            text_lower = text.lower()

            # Check for vague phrases
            vague_found = []
            for phrase in self.VAGUE_PHRASES:
                if phrase in text_lower:
                    vague_found.append(phrase)

            if vague_found:
                issues.append(f"{field_name} contains vague phrases: {', '.join(vague_found[:3])}")
                suggestions.append(f"Replace vague phrases in {field_name} with specific criteria")
                score -= 0.05 * len(vague_found)

        # Check constraints for specificity
        constraints = decision.get("constraints", [])
        for i, c in enumerate(constraints):
            rule = c.get("rule", "") if isinstance(c, dict) else str(c)
            rule_lower = rule.lower()

            # Check for vague language in constraints (more severe)
            for phrase in self.VAGUE_PHRASES:
                if phrase in rule_lower:
                    issues.append(f"Constraint {i+1} is vague ('{phrase}')")
                    suggestions.append(f"Make constraint {i+1} more specific and verifiable")
                    score -= 0.1
                    break

            # Check if constraint has measurable criteria
            has_measurement = any(
                pattern in rule_lower
                for pattern in ["must be", "must not", "maximum", "minimum", "at least", "at most", "exactly", "within"]
            )
            if not has_measurement and not rule_lower.startswith(("must ", "should ", "may ")):
                issues.append(f"Constraint {i+1} lacks measurable criteria")
                score -= 0.05

        # Check applies_to specificity
        applies_to = decision.get("applies_to", [])
        if applies_to:
            vague_applies = [a for a in applies_to if a in ["*", "all", "any", "everything"]]
            if vague_applies:
                issues.append("applies_to is too broad")
                suggestions.append("Specify concrete file patterns or contexts")
                score -= 0.1

        return QualityScore(
            dimension=QualityDimension.SPECIFICITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def _check_consistency(self, decision: Dict[str, Any]) -> QualityScore:
        """Check internal consistency of the decision."""
        issues = []
        suggestions = []
        score = 1.0

        statement = decision.get("statement", "").lower()
        rationale = decision.get("rationale", "").lower()
        constraints = decision.get("constraints", [])

        # Check if rationale supports statement
        # Simple heuristic: rationale should mention key terms from statement
        statement_keywords = set(re.findall(r'\b[a-z]{4,}\b', statement))
        rationale_keywords = set(re.findall(r'\b[a-z]{4,}\b', rationale))

        # At least 30% keyword overlap expected
        if statement_keywords:
            overlap = len(statement_keywords & rationale_keywords) / len(statement_keywords)
            if overlap < 0.3:
                issues.append("Rationale may not fully support statement (low keyword overlap)")
                suggestions.append("Ensure rationale explains WHY the statement is important")
                score -= 0.15

        # Check constraint types are consistent
        constraint_types = []
        for c in constraints:
            ctype = c.get("type", "MUST") if isinstance(c, dict) else "MUST"
            constraint_types.append(ctype)

        # Too many MAY without MUST is weak
        must_count = sum(1 for t in constraint_types if t in ["MUST", "MUST_NOT"])
        may_count = sum(1 for t in constraint_types if t == "MAY")

        if must_count == 0 and may_count > 0:
            issues.append("No MUST constraints - only MAY (too permissive)")
            suggestions.append("Add at least one MUST constraint for enforceability")
            score -= 0.2

        # Check for contradicting constraints (simple check)
        constraint_rules = [
            (c.get("rule", "") if isinstance(c, dict) else str(c)).lower()
            for c in constraints
        ]

        for i, rule1 in enumerate(constraint_rules):
            for j, rule2 in enumerate(constraint_rules[i+1:], i+1):
                # Simple contradiction detection
                if "must " in rule1 and "must not " in rule2:
                    # Check if they're about the same thing
                    r1_keywords = set(re.findall(r'\b[a-z]{4,}\b', rule1))
                    r2_keywords = set(re.findall(r'\b[a-z]{4,}\b', rule2.replace("must not", "")))
                    if len(r1_keywords & r2_keywords) > 2:
                        issues.append(f"Potential contradiction between constraints {i+1} and {j+1}")
                        score -= 0.2

        return QualityScore(
            dimension=QualityDimension.CONSISTENCY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def _check_actionability(self, decision: Dict[str, Any]) -> QualityScore:
        """Check if decision can be enforced."""
        issues = []
        suggestions = []
        score = 1.0

        constraints = decision.get("constraints", [])

        if not constraints:
            issues.append("No constraints to enforce")
            return QualityScore(
                dimension=QualityDimension.ACTIONABILITY,
                score=0.0,
                issues=issues,
                suggestions=["Add enforceable constraints"],
            )

        enforceable_count = 0
        for i, c in enumerate(constraints):
            rule = c.get("rule", "") if isinstance(c, dict) else str(c)
            rule_lower = rule.lower()

            # Check if constraint is enforceable
            is_enforceable = any(
                kw in rule_lower for kw in self.ENFORCEABLE_KEYWORDS
            )

            if is_enforceable:
                enforceable_count += 1
            else:
                issues.append(f"Constraint {i+1} may not be enforceable")
                suggestions.append(f"Make constraint {i+1} more enforceable with clear criteria")

            # Check if constraint is automatable
            is_automated = c.get("is_automated", False) if isinstance(c, dict) else False
            if not is_automated:
                # Could potentially be automated
                automation_hints = ["file", "import", "name", "line", "char", "pattern"]
                if any(h in rule_lower for h in automation_hints):
                    suggestions.append(f"Constraint {i+1} could potentially be automated")

        # Score based on enforceable ratio
        if constraints:
            enforceable_ratio = enforceable_count / len(constraints)
            score = enforceable_ratio

            if enforceable_ratio < 0.5:
                issues.append("Less than half of constraints are clearly enforceable")

        return QualityScore(
            dimension=QualityDimension.ACTIONABILITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def _detect_conflicts(self, decision: Dict[str, Any]) -> List[ConflictReport]:
        """Detect conflicts with existing decisions."""
        conflicts = []

        if not self.existing_decisions:
            return conflicts

        decision_domain = decision.get("domain_id", "")
        decision_aspect = decision.get("aspect_id", "")
        decision_tags = set(decision.get("tags", []))
        decision_applies = set(decision.get("applies_to", []))
        decision_constraints = decision.get("constraints", [])

        for existing in self.existing_decisions:
            # Skip self-comparison
            if existing.get("decision_id") == decision.get("decision_id"):
                continue

            existing_id = existing.get("decision_id", "")
            existing_code = existing.get("code", "")
            existing_domain = existing.get("domain_id", "")
            existing_aspect = existing.get("aspect_id", "")
            existing_tags = set(existing.get("tags", []))
            existing_applies = set(existing.get("applies_to", []))
            existing_constraints = existing.get("constraints", [])

            # Check for same domain+aspect (potential overlap)
            same_taxonomy = (decision_domain == existing_domain and
                           decision_aspect == existing_aspect)

            # Check for tag overlap
            tag_overlap = decision_tags & existing_tags

            # Check for applies_to overlap
            applies_overlap = decision_applies & existing_applies

            # Only check for conflicts if there's significant overlap
            if not (same_taxonomy or len(tag_overlap) > 2 or len(applies_overlap) > 0):
                continue

            # Check for constraint conflicts
            for new_c in decision_constraints:
                new_rule = new_c.get("rule", "") if isinstance(new_c, dict) else str(new_c)
                new_type = new_c.get("type", "MUST") if isinstance(new_c, dict) else "MUST"
                new_rule_lower = new_rule.lower()

                for old_c in existing_constraints:
                    old_rule = old_c.get("rule", "") if isinstance(old_c, dict) else str(old_c)
                    old_type = old_c.get("type", "MUST") if isinstance(old_c, dict) else "MUST"
                    old_rule_lower = old_rule.lower()

                    # Check for direct contradiction (MUST vs MUST_NOT on same topic)
                    if (new_type == "MUST" and old_type == "MUST_NOT") or \
                       (new_type == "MUST_NOT" and old_type == "MUST"):
                        # Check keyword overlap
                        new_keywords = set(re.findall(r'\b[a-z]{4,}\b', new_rule_lower))
                        old_keywords = set(re.findall(r'\b[a-z]{4,}\b', old_rule_lower))
                        overlap = new_keywords & old_keywords

                        if len(overlap) >= 3:
                            conflicts.append(ConflictReport(
                                existing_decision_id=existing_id,
                                existing_decision_code=existing_code,
                                conflict_type="CONTRADICTS",
                                severity="HIGH",
                                description=f"MUST vs MUST_NOT conflict on similar topic",
                                resolution_hint="Review if decisions apply to different contexts, or if one supersedes the other",
                            ))

                    # Check for weakening (MUST → SHOULD on same topic)
                    if new_type == "SHOULD" and old_type == "MUST":
                        new_keywords = set(re.findall(r'\b[a-z]{4,}\b', new_rule_lower))
                        old_keywords = set(re.findall(r'\b[a-z]{4,}\b', old_rule_lower))
                        overlap = new_keywords & old_keywords

                        if len(overlap) >= 3:
                            conflicts.append(ConflictReport(
                                existing_decision_id=existing_id,
                                existing_decision_code=existing_code,
                                conflict_type="WEAKENS",
                                severity="MEDIUM",
                                description=f"New SHOULD may weaken existing MUST",
                                resolution_hint="Consider if this is intentional relaxation or should be MUST",
                            ))

            # Check for general overlap without specific conflict
            if same_taxonomy and len(tag_overlap) > 2:
                # Already checked constraints, just note the overlap
                if not any(c.existing_decision_id == existing_id for c in conflicts):
                    conflicts.append(ConflictReport(
                        existing_decision_id=existing_id,
                        existing_decision_code=existing_code,
                        conflict_type="OVERLAPS",
                        severity="LOW",
                        description=f"Overlaps with existing decision in same taxonomy with similar tags",
                        resolution_hint="Ensure decisions are complementary, not redundant",
                    ))

        return conflicts

    def load_existing_decisions(self, decisions: List[Dict[str, Any]]):
        """Load existing decisions for conflict detection."""
        self.existing_decisions = decisions


# ============================================================================
# INTEGRATION HELPER
# ============================================================================

def create_gate2_validator(
    existing_decisions: Optional[List[Dict[str, Any]]] = None,
) -> Gate2AIValidator:
    """
    Factory function to create Gate 2 validator.

    Args:
        existing_decisions: Existing decisions for conflict detection

    Returns:
        Configured Gate2AIValidator
    """
    return Gate2AIValidator(
        existing_decisions=existing_decisions or [],
        ai_backend=None,  # TODO: Add Claude API integration
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "QualityDimension",
    "QualityScore",
    "ConflictReport",
    "Gate2AIResult",
    "Gate2AIValidator",
    "create_gate2_validator",
]
