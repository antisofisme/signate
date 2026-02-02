"""
Quality Scoring - AI-Powered Decision Quality Assessment

Rates decision quality to ensure rich, useful data.

QUALITY DIMENSIONS:
1. Clarity (30%):     Is the statement clear and unambiguous?
2. Actionability (25%): Can someone act on this decision?
3. Completeness (20%): Are required fields filled properly?
4. Specificity (15%): Is it specific enough to be useful?
5. Consistency (10%): Does rationale support statement?

SCORING:
- 90-100: EXCELLENT - Exemplary decision, use as template
- 70-89:  GOOD      - Solid decision, minor improvements possible
- 50-69:  FAIR      - Acceptable but needs improvement
- 30-49:  POOR      - Significant issues, should be revised
- 0-29:   REJECT    - Not suitable, needs rewrite

ANTI-PATTERNS DETECTED:
- Vague language ("consider", "maybe", "if possible")
- Missing rationale ("we decided" without why)
- Too broad ("all code should be good")
- Too narrow (applies to one edge case)
- Contradictory (statement vs constraints conflict)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import re


class QualityGrade(str, Enum):
    """Quality grade classification."""
    EXCELLENT = "EXCELLENT"  # 90-100
    GOOD = "GOOD"            # 70-89
    FAIR = "FAIR"            # 50-69
    POOR = "POOR"            # 30-49
    REJECT = "REJECT"        # 0-29


@dataclass
class QualityIssue:
    """Single quality issue found."""
    dimension: str           # clarity, actionability, etc.
    severity: str            # CRITICAL, HIGH, MEDIUM, LOW
    message: str             # What's wrong
    suggestion: str          # How to fix
    field: Optional[str] = None  # Which field has the issue
    evidence: Optional[str] = None  # Specific text that caused issue


@dataclass
class QualityScore:
    """Complete quality assessment."""
    overall_score: int       # 0-100
    grade: QualityGrade

    # Dimension scores (0-100)
    clarity_score: int = 0
    actionability_score: int = 0
    completeness_score: int = 0
    specificity_score: int = 0
    consistency_score: int = 0

    # Issues found
    issues: List[QualityIssue] = field(default_factory=list)

    # Suggestions for improvement
    top_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "overall_score": self.overall_score,
            "grade": self.grade.value,
            "clarity_score": self.clarity_score,
            "actionability_score": self.actionability_score,
            "completeness_score": self.completeness_score,
            "specificity_score": self.specificity_score,
            "consistency_score": self.consistency_score,
            "issue_count": len(self.issues),
            "top_suggestions": self.top_suggestions[:3],
        }


class QualityScorer:
    """
    AI-powered quality scorer for decisions.

    Uses heuristic rules and pattern matching to assess quality.
    Can be extended with actual AI model calls.
    """

    # Dimension weights
    WEIGHTS = {
        "clarity": 0.30,
        "actionability": 0.25,
        "completeness": 0.20,
        "specificity": 0.15,
        "consistency": 0.10,
    }

    # Anti-patterns
    VAGUE_WORDS = [
        "consider", "maybe", "might", "perhaps", "possibly",
        "if possible", "when appropriate", "as needed",
        "generally", "usually", "sometimes", "often",
        "try to", "attempt to", "should probably",
    ]

    ACTION_VERBS = [
        "must", "shall", "will", "use", "implement", "create",
        "define", "establish", "require", "ensure", "maintain",
        "follow", "apply", "adopt", "enforce", "validate",
    ]

    def __init__(self, ai_scorer: Optional[Any] = None):
        """
        Initialize scorer.

        Args:
            ai_scorer: Optional AI model for advanced scoring
        """
        self.ai_scorer = ai_scorer

    def score(self, decision: Dict[str, Any]) -> QualityScore:
        """
        Score decision quality.

        Args:
            decision: Decision data

        Returns:
            QualityScore with breakdown and issues
        """
        issues = []

        # Score each dimension
        clarity = self._score_clarity(decision, issues)
        actionability = self._score_actionability(decision, issues)
        completeness = self._score_completeness(decision, issues)
        specificity = self._score_specificity(decision, issues)
        consistency = self._score_consistency(decision, issues)

        # Calculate weighted overall score
        overall = int(
            self.WEIGHTS["clarity"] * clarity +
            self.WEIGHTS["actionability"] * actionability +
            self.WEIGHTS["completeness"] * completeness +
            self.WEIGHTS["specificity"] * specificity +
            self.WEIGHTS["consistency"] * consistency
        )

        # Classify grade
        grade = self._classify_grade(overall)

        # Generate top suggestions
        suggestions = self._generate_suggestions(issues)

        return QualityScore(
            overall_score=overall,
            grade=grade,
            clarity_score=clarity,
            actionability_score=actionability,
            completeness_score=completeness,
            specificity_score=specificity,
            consistency_score=consistency,
            issues=issues,
            top_suggestions=suggestions,
        )

    def _score_clarity(
        self,
        decision: Dict,
        issues: List[QualityIssue],
    ) -> int:
        """Score statement clarity (0-100)."""
        statement = decision.get("statement", "")
        score = 100

        # Check for vague language
        statement_lower = statement.lower()
        vague_found = []
        for word in self.VAGUE_WORDS:
            if word in statement_lower:
                vague_found.append(word)
                score -= 10

        if vague_found:
            issues.append(QualityIssue(
                dimension="clarity",
                severity="HIGH",
                message="Statement contains vague language",
                suggestion="Replace vague terms with specific requirements",
                field="statement",
                evidence=f"Found: {', '.join(vague_found[:3])}",
            ))

        # Check sentence structure
        sentences = [s.strip() for s in re.split(r'[.!?]', statement) if s.strip()]
        if len(sentences) > 5:
            score -= 15
            issues.append(QualityIssue(
                dimension="clarity",
                severity="MEDIUM",
                message="Statement too long",
                suggestion="Limit to 1-3 sentences",
                field="statement",
            ))

        # Check for passive voice indicators
        passive_indicators = ["is used", "are used", "be used", "been used", "was decided", "were decided"]
        for indicator in passive_indicators:
            if indicator in statement_lower:
                score -= 5
                issues.append(QualityIssue(
                    dimension="clarity",
                    severity="LOW",
                    message="Passive voice detected",
                    suggestion="Use active voice: 'We use X' instead of 'X is used'",
                    field="statement",
                    evidence=indicator,
                ))
                break

        return max(0, score)

    def _score_actionability(
        self,
        decision: Dict,
        issues: List[QualityIssue],
    ) -> int:
        """Score actionability (0-100)."""
        statement = decision.get("statement", "").lower()
        constraints = decision.get("constraints", [])
        score = 70  # Start at 70, adjust up/down

        # Check for action verbs
        has_action = any(verb in statement for verb in self.ACTION_VERBS)
        if has_action:
            score += 20
        else:
            issues.append(QualityIssue(
                dimension="actionability",
                severity="HIGH",
                message="No clear action verb in statement",
                suggestion="Start with MUST, SHALL, or specific action verb",
                field="statement",
            ))
            score -= 20

        # Check for constraints
        if constraints:
            score += 10
            # Check constraint quality
            good_constraints = 0
            for c in constraints:
                rule = c.get("rule", "") if isinstance(c, dict) else str(c)
                if any(rule.upper().startswith(kw) for kw in ["MUST", "SHALL", "SHOULD"]):
                    good_constraints += 1

            if good_constraints < len(constraints) * 0.5:
                issues.append(QualityIssue(
                    dimension="actionability",
                    severity="MEDIUM",
                    message="Some constraints lack clear action verbs",
                    suggestion="Start each constraint with MUST/SHALL/SHOULD",
                    field="constraints",
                ))
                score -= 10
        else:
            issues.append(QualityIssue(
                dimension="actionability",
                severity="MEDIUM",
                message="No constraints defined",
                suggestion="Add MUST/SHOULD constraints for enforceability",
                field="constraints",
            ))
            score -= 10

        return max(0, min(100, score))

    def _score_completeness(
        self,
        decision: Dict,
        issues: List[QualityIssue],
    ) -> int:
        """Score field completeness (0-100)."""
        score = 0

        # Required fields (60 points)
        required = {
            "statement": 20,
            "rationale": 20,
            "domain_id": 10,
            "aspect_id": 10,
        }

        for field_name, points in required.items():
            value = decision.get(field_name)
            if value and (not isinstance(value, str) or len(value.strip()) > 10):
                score += points
            else:
                issues.append(QualityIssue(
                    dimension="completeness",
                    severity="CRITICAL" if points >= 20 else "HIGH",
                    message=f"Required field '{field_name}' is missing or too short",
                    suggestion=f"Provide meaningful content for {field_name}",
                    field=field_name,
                ))

        # Important fields (40 points)
        important = {
            "constraints": 15,
            "applies_to": 10,
            "tags": 10,
            "version": 5,
        }

        for field_name, points in important.items():
            value = decision.get(field_name)
            if value and (isinstance(value, list) and len(value) > 0 or isinstance(value, str) and len(value) > 0):
                score += points
            else:
                issues.append(QualityIssue(
                    dimension="completeness",
                    severity="MEDIUM",
                    message=f"Important field '{field_name}' is empty",
                    suggestion=f"Add {field_name} for better retrieval",
                    field=field_name,
                ))

        return score

    def _score_specificity(
        self,
        decision: Dict,
        issues: List[QualityIssue],
    ) -> int:
        """Score specificity (0-100)."""
        statement = decision.get("statement", "")
        applies_to = decision.get("applies_to", [])
        tags = decision.get("tags", [])
        score = 50  # Neutral start

        # Check for specific patterns
        has_specific_pattern = any("*" in a or "/" in a for a in applies_to)
        if has_specific_pattern:
            score += 20
        elif applies_to:
            score += 10

        # Check for tech stack specificity
        tech_patterns = [
            r'\b(react|vue|angular|python|go|java|typescript)\b',
            r'\b(v\d+|version \d+)\b',
            r'\b(/\w+/|src/|lib/)\b',
        ]

        specific_count = 0
        for pattern in tech_patterns:
            if re.search(pattern, statement, re.IGNORECASE):
                specific_count += 1

        score += specific_count * 10

        # Check for overly broad statements
        broad_indicators = [
            "all code", "everything", "always", "never",
            "any file", "all files", "entire codebase",
        ]

        statement_lower = statement.lower()
        for indicator in broad_indicators:
            if indicator in statement_lower and len(applies_to) == 0:
                score -= 20
                issues.append(QualityIssue(
                    dimension="specificity",
                    severity="HIGH",
                    message="Statement is too broad",
                    suggestion="Add specific applies_to patterns or narrow scope",
                    field="statement",
                    evidence=indicator,
                ))
                break

        # Penalize if no tags
        if not tags:
            score -= 10
            issues.append(QualityIssue(
                dimension="specificity",
                severity="LOW",
                message="No tags defined",
                suggestion="Add tags for better categorization",
                field="tags",
            ))

        return max(0, min(100, score))

    def _score_consistency(
        self,
        decision: Dict,
        issues: List[QualityIssue],
    ) -> int:
        """Score internal consistency (0-100)."""
        statement = decision.get("statement", "").lower()
        rationale = decision.get("rationale", "").lower()
        constraints = decision.get("constraints", [])
        score = 80  # Start high, deduct for issues

        # Check if rationale supports statement
        # Simple heuristic: statement keywords should appear in rationale
        statement_words = set(re.findall(r'\b\w{4,}\b', statement))
        rationale_words = set(re.findall(r'\b\w{4,}\b', rationale))

        overlap = statement_words & rationale_words
        overlap_ratio = len(overlap) / max(len(statement_words), 1)

        if overlap_ratio < 0.2:
            score -= 30
            issues.append(QualityIssue(
                dimension="consistency",
                severity="HIGH",
                message="Rationale doesn't clearly support statement",
                suggestion="Explain WHY this specific decision was made",
                field="rationale",
            ))
        elif overlap_ratio < 0.4:
            score -= 10
            issues.append(QualityIssue(
                dimension="consistency",
                severity="MEDIUM",
                message="Weak connection between statement and rationale",
                suggestion="Reference statement concepts in rationale",
                field="rationale",
            ))

        # Check for contradictory constraints
        constraint_texts = [
            c.get("rule", "").lower() if isinstance(c, dict) else str(c).lower()
            for c in constraints
        ]

        # Simple contradiction check: MUST vs MUST NOT for same subject
        must_subjects = set()
        must_not_subjects = set()

        for ct in constraint_texts:
            if ct.startswith("must not"):
                words = ct[8:].split()[:3]
                must_not_subjects.update(words)
            elif ct.startswith("must"):
                words = ct[4:].split()[:3]
                must_subjects.update(words)

        contradictions = must_subjects & must_not_subjects
        if contradictions:
            score -= 20
            issues.append(QualityIssue(
                dimension="consistency",
                severity="CRITICAL",
                message="Potentially contradictory constraints",
                suggestion="Review MUST and MUST NOT constraints for conflicts",
                field="constraints",
                evidence=f"Conflict on: {', '.join(contradictions)}",
            ))

        return max(0, score)

    def _classify_grade(self, score: int) -> QualityGrade:
        """Classify score into grade."""
        if score >= 90:
            return QualityGrade.EXCELLENT
        elif score >= 70:
            return QualityGrade.GOOD
        elif score >= 50:
            return QualityGrade.FAIR
        elif score >= 30:
            return QualityGrade.POOR
        else:
            return QualityGrade.REJECT

    def _generate_suggestions(
        self,
        issues: List[QualityIssue],
    ) -> List[str]:
        """Generate top improvement suggestions."""
        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_issues = sorted(issues, key=lambda i: severity_order.get(i.severity, 4))

        suggestions = []
        seen = set()

        for issue in sorted_issues:
            if issue.suggestion not in seen:
                suggestions.append(issue.suggestion)
                seen.add(issue.suggestion)

            if len(suggestions) >= 5:
                break

        return suggestions


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "QualityGrade",
    "QualityIssue",
    "QualityScore",
    "QualityScorer",
]
