"""
MANTRA Validation Rules Registry

Single source of truth for all validation rules across the 3-Gate pipeline.

Rule Naming Convention:
- S-XXX: Schema rules (Gate 1) - Structural validation
- D-XXX: Decision rules (Gate 1) - Consistency validation
- H-XXX: Heuristic rules (Gate 2) - AI quality scoring
- A-XXX: Approval rules (Gate 3) - Human review requirements

Rule Severities:
- BLOCKER: Must fix, blocks everything (immediate rejection)
- CRITICAL: Must fix before approval
- WARNING: Should fix, advisory only
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
import re


# =============================================================================
# ENUMS
# =============================================================================

class RuleGate(int, Enum):
    """Which gate the rule belongs to."""
    GATE_1 = 1  # Deterministic validation
    GATE_2 = 2  # AI heuristic validation
    GATE_3 = 3  # Human approval


class RuleCategory(str, Enum):
    """Category of validation rule."""
    SCHEMA = "SCHEMA"           # S-xxx: Structural validation
    CONSISTENCY = "CONSISTENCY" # D-xxx: Decision consistency
    HEURISTIC = "HEURISTIC"     # H-xxx: AI quality scoring
    APPROVAL = "APPROVAL"       # A-xxx: Human approval requirements


class RuleSeverity(str, Enum):
    """Rule violation severity."""
    BLOCKER = "BLOCKER"   # Must fix, blocks everything
    CRITICAL = "CRITICAL" # Must fix before approval
    WARNING = "WARNING"   # Should fix, advisory


# =============================================================================
# RULE DATACLASS
# =============================================================================

@dataclass
class Rule:
    """
    Definition of a validation rule.

    Attributes:
        rule_id: Unique identifier (e.g., "S-001", "D-005", "H-003")
        name: Human-readable name
        description: Detailed description of what the rule checks
        gate: Which gate this rule belongs to
        category: Rule category
        severity: Default severity when violated
        field: Which field this rule applies to (None for multi-field rules)
        pattern: Regex pattern for validation (if applicable)
        min_value: Minimum value (for length/range checks)
        max_value: Maximum value (for length/range checks)
        allowed_values: Set of allowed values (for enum checks)
        required: Whether the field is required
        suggestion: Default suggestion when violated
        law_reference: Reference to MANTRA-LAW section (if applicable)
    """
    rule_id: str
    name: str
    description: str
    gate: RuleGate
    category: RuleCategory
    severity: RuleSeverity
    field: Optional[str] = None
    pattern: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    allowed_values: Optional[Set[str]] = None
    required: bool = False
    suggestion: Optional[str] = None
    law_reference: Optional[str] = None

    def __post_init__(self):
        # Compile pattern if provided
        if self.pattern:
            self._compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
        else:
            self._compiled_pattern = None

    def matches_pattern(self, value: str) -> bool:
        """Check if value matches the rule's pattern."""
        if not self._compiled_pattern:
            return True
        return bool(self._compiled_pattern.match(str(value)))

    def in_range(self, value: int) -> bool:
        """Check if value is within allowed range."""
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def is_allowed(self, value: str) -> bool:
        """Check if value is in allowed values set."""
        if not self.allowed_values:
            return True
        return str(value) in self.allowed_values

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "gate": self.gate.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "field": self.field,
            "pattern": self.pattern,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "allowed_values": list(self.allowed_values) if self.allowed_values else None,
            "required": self.required,
            "suggestion": self.suggestion,
            "law_reference": self.law_reference,
        }


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

# Common patterns
UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
VERSION_PATTERN = r"^[0-9]+\.[0-9]+\.[0-9]+$"
CODE_PATTERN = r"^[A-Z]+-A[0-9]{2}-[0-9]{3}$"
SCOPE_PATH_PATTERN = r"^(\*|[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*(\.\*)?|\*)$"

# Valid domain IDs
VALID_DOMAINS = {"INT", "ARCH", "CTL", "EVO"}

# Valid aspect IDs
VALID_ASPECTS = {f"A{i:02d}" for i in range(1, 17)}  # A01-A16

# Valid impact levels
VALID_IMPACTS = {"CRITICAL", "IMPORTANT", "REFERENCE"}

# Valid constraint types
VALID_CONSTRAINT_TYPES = {"MUST", "MUST_NOT", "SHOULD", "MAY"}


# -----------------------------------------------------------------------------
# SCHEMA RULES (S-001 to S-022)
# -----------------------------------------------------------------------------

SCHEMA_RULES: List[Rule] = [
    Rule(
        rule_id="S-001",
        name="decision_id_presence",
        description="decision_id is required",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="decision_id",
        required=True,
        suggestion="Add a valid UUID as decision_id",
    ),
    Rule(
        rule_id="S-002",
        name="decision_id_format",
        description="decision_id must be a valid UUID",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="decision_id",
        pattern=UUID_PATTERN,
        suggestion="Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    ),
    Rule(
        rule_id="S-003",
        name="code_presence",
        description="code (or decision_code) is required",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="code",
        required=True,
        suggestion="Add code in format DOMAIN-ASPECT-SEQ (e.g., ARCH-A06-001)",
    ),
    Rule(
        rule_id="S-004",
        name="code_format",
        description="code must match pattern DOMAIN-ASPECT-SEQ",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.CRITICAL,
        field="code",
        pattern=CODE_PATTERN,
        suggestion="Format: XXX-ANN-NNN (e.g., ARCH-A06-001)",
    ),
    Rule(
        rule_id="S-005",
        name="domain_id_presence",
        description="domain_id is required",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="domain_id",
        required=True,
        suggestion=f"Valid domains: {', '.join(sorted(VALID_DOMAINS))}",
    ),
    Rule(
        rule_id="S-006",
        name="domain_id_enumeration",
        description="domain_id must be a valid domain",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="domain_id",
        allowed_values=VALID_DOMAINS,
    ),
    Rule(
        rule_id="S-007",
        name="aspect_id_presence",
        description="aspect_id is required",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="aspect_id",
        required=True,
        suggestion="Valid aspects: A01-A16",
    ),
    Rule(
        rule_id="S-008",
        name="aspect_id_enumeration",
        description="aspect_id must be a valid aspect",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="aspect_id",
        allowed_values=VALID_ASPECTS,
    ),
    Rule(
        rule_id="S-009",
        name="version_presence",
        description="version is required",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="version",
        required=True,
        suggestion="Use semantic versioning: X.Y.Z",
    ),
    Rule(
        rule_id="S-010",
        name="version_format",
        description="version must follow semantic versioning (X.Y.Z)",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.CRITICAL,
        field="version",
        pattern=VERSION_PATTERN,
    ),
    Rule(
        rule_id="S-011",
        name="statement_presence",
        description="statement is required and must not be empty",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="statement",
        required=True,
    ),
    Rule(
        rule_id="S-012",
        name="statement_length",
        description="statement must be 50-1500 characters",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.WARNING,  # WARNING for min, CRITICAL for max
        field="statement",
        min_value=50,
        max_value=1500,
    ),
    Rule(
        rule_id="S-013",
        name="rationale_presence",
        description="rationale is required and must not be empty",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="rationale",
        required=True,
    ),
    Rule(
        rule_id="S-014",
        name="rationale_length",
        description="rationale should be at least 100 characters",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.WARNING,
        field="rationale",
        min_value=100,
    ),
    Rule(
        rule_id="S-015",
        name="constraints_type",
        description="constraints must be an array",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="constraints",
    ),
    Rule(
        rule_id="S-016",
        name="constraint_structure",
        description="Each constraint must have rule/statement and valid type",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.CRITICAL,
        field="constraints",
        allowed_values=VALID_CONSTRAINT_TYPES,
    ),
    Rule(
        rule_id="S-017",
        name="invariants_type",
        description="invariants must be an array",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.CRITICAL,
        field="invariants",
    ),
    Rule(
        rule_id="S-018",
        name="authored_by_presence",
        description="authored_by is required per LAW §2.3",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="authored_by",
        required=True,
        law_reference="MANTRA-LAW-001 §2.3",
        suggestion="Must be a human identifier (not AI)",
    ),
    Rule(
        rule_id="S-019",
        name="authored_by_not_ai",
        description="authored_by must be human per LAW §6 (AI has ZERO authority)",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.BLOCKER,
        field="authored_by",
        law_reference="MANTRA-LAW-001 §6",
    ),
    Rule(
        rule_id="S-020",
        name="summary_presence",
        description="summary is recommended for quick scanning",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.WARNING,
        field="summary",
    ),
    Rule(
        rule_id="S-021",
        name="impact_enumeration",
        description="impact must be CRITICAL, IMPORTANT, or REFERENCE",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.CRITICAL,
        field="impact",
        allowed_values=VALID_IMPACTS,
    ),
    Rule(
        rule_id="S-022",
        name="scope_path_format",
        description="scope_path must match pattern (e.g., 'fe.react.css' or '*')",
        gate=RuleGate.GATE_1,
        category=RuleCategory.SCHEMA,
        severity=RuleSeverity.CRITICAL,
        field="scope_path",
        pattern=SCOPE_PATH_PATTERN,
    ),
]


# -----------------------------------------------------------------------------
# CONSISTENCY RULES (D-001 to D-014)
# -----------------------------------------------------------------------------

CONSISTENCY_RULES: List[Rule] = [
    Rule(
        rule_id="D-001",
        name="domain_aspect_compatibility",
        description="Aspect must be compatible with domain per DOMAIN_ASPECT_MATRIX",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.BLOCKER,
        field="aspect_id",
    ),
    Rule(
        rule_id="D-002",
        name="code_matches_domain_aspect",
        description="code should start with domain-aspect prefix",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.WARNING,
        field="code",
    ),
    Rule(
        rule_id="D-003",
        name="constraint_ids_unique",
        description="Constraint IDs must be unique within decision",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.CRITICAL,
        field="constraints",
    ),
    Rule(
        rule_id="D-004",
        name="depends_on_valid_format",
        description="depends_on must contain valid decision codes or UUIDs",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.CRITICAL,
        field="depends_on",
    ),
    Rule(
        rule_id="D-005",
        name="supersedes_valid_format",
        description="supersedes must be a valid decision code or UUID",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.CRITICAL,
        field="supersedes",
    ),
    Rule(
        rule_id="D-006",
        name="no_self_dependency",
        description="Decision cannot depend on itself",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.BLOCKER,
        field="depends_on",
    ),
    Rule(
        rule_id="D-007",
        name="no_self_supersede",
        description="Decision cannot supersede itself",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.BLOCKER,
        field="supersedes",
    ),
    Rule(
        rule_id="D-008",
        name="priority_rank_range",
        description="priority_rank must be integer 1-100",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.CRITICAL,
        field="priority_rank",
        min_value=1,
        max_value=100,
    ),
    Rule(
        rule_id="D-009",
        name="tags_are_strings",
        description="All tags must be strings",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.CRITICAL,
        field="tags",
    ),
    Rule(
        rule_id="D-010",
        name="applies_to_are_strings",
        description="All applies_to entries must be strings",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.CRITICAL,
        field="applies_to",
    ),
    Rule(
        rule_id="D-011",
        name="circular_dependency",
        description="Decision graph must not have circular dependencies",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.BLOCKER,
        field="depends_on",
    ),
    Rule(
        rule_id="D-012",
        name="supersedes_exists",
        description="Superseded decision must exist in system",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.CRITICAL,
        field="supersedes",
    ),
    Rule(
        rule_id="D-013",
        name="depends_on_exists",
        description="Dependency decisions must exist in system",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.WARNING,
        field="depends_on",
    ),
    Rule(
        rule_id="D-014",
        name="code_sequence_gap",
        description="Decision code sequence should not have large gaps",
        gate=RuleGate.GATE_1,
        category=RuleCategory.CONSISTENCY,
        severity=RuleSeverity.WARNING,
        field="code",
    ),
]


# -----------------------------------------------------------------------------
# HEURISTIC RULES (H-001 to H-010) - Gate 2 AI Validation
# -----------------------------------------------------------------------------

HEURISTIC_RULES: List[Rule] = [
    Rule(
        rule_id="H-001",
        name="statement_clarity",
        description="Statement should be clear and unambiguous",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.WARNING,
        field="statement",
        suggestion="Use specific language, avoid ambiguity",
    ),
    Rule(
        rule_id="H-002",
        name="rationale_completeness",
        description="Rationale should explain WHY, not just WHAT",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.WARNING,
        field="rationale",
        suggestion="Include reasoning, trade-offs, and context",
    ),
    Rule(
        rule_id="H-003",
        name="constraint_specificity",
        description="Constraints should be specific and actionable",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.WARNING,
        field="constraints",
    ),
    Rule(
        rule_id="H-004",
        name="summary_accuracy",
        description="Summary should accurately reflect the decision",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.WARNING,
        field="summary",
    ),
    Rule(
        rule_id="H-005",
        name="scope_appropriateness",
        description="Scope path should match decision's actual applicability",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.WARNING,
        field="scope_path",
    ),
    Rule(
        rule_id="H-006",
        name="impact_justification",
        description="Impact level should be justified by content",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.WARNING,
        field="impact",
    ),
    Rule(
        rule_id="H-007",
        name="dependency_completeness",
        description="All relevant dependencies should be declared",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.WARNING,
        field="depends_on",
    ),
    Rule(
        rule_id="H-008",
        name="conflict_detection",
        description="Decision should not conflict with existing decisions",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.CRITICAL,
    ),
    Rule(
        rule_id="H-009",
        name="duplicate_detection",
        description="Decision should not duplicate existing decisions",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.CRITICAL,
    ),
    Rule(
        rule_id="H-010",
        name="readability_score",
        description="Content should meet minimum readability standards",
        gate=RuleGate.GATE_2,
        category=RuleCategory.HEURISTIC,
        severity=RuleSeverity.WARNING,
        min_value=60,  # Flesch Reading Ease score
    ),
]


# -----------------------------------------------------------------------------
# APPROVAL RULES (A-001 to A-005) - Gate 3 Human Approval
# -----------------------------------------------------------------------------

APPROVAL_RULES: List[Rule] = [
    Rule(
        rule_id="A-001",
        name="human_approver_required",
        description="Decision must be approved by a human (not AI)",
        gate=RuleGate.GATE_3,
        category=RuleCategory.APPROVAL,
        severity=RuleSeverity.BLOCKER,
        field="approved_by",
        law_reference="MANTRA-LAW-001 §6",
    ),
    Rule(
        rule_id="A-002",
        name="gate1_passed",
        description="Gate 1 validation must pass before approval",
        gate=RuleGate.GATE_3,
        category=RuleCategory.APPROVAL,
        severity=RuleSeverity.BLOCKER,
    ),
    Rule(
        rule_id="A-003",
        name="gate2_reviewed",
        description="Gate 2 warnings must be reviewed (not necessarily fixed)",
        gate=RuleGate.GATE_3,
        category=RuleCategory.APPROVAL,
        severity=RuleSeverity.CRITICAL,
    ),
    Rule(
        rule_id="A-004",
        name="conflict_acknowledged",
        description="Any detected conflicts must be acknowledged",
        gate=RuleGate.GATE_3,
        category=RuleCategory.APPROVAL,
        severity=RuleSeverity.CRITICAL,
    ),
    Rule(
        rule_id="A-005",
        name="author_different_from_approver",
        description="Approver should ideally be different from author",
        gate=RuleGate.GATE_3,
        category=RuleCategory.APPROVAL,
        severity=RuleSeverity.WARNING,
    ),
]


# =============================================================================
# RULE REGISTRY
# =============================================================================

class RuleRegistry:
    """
    Central registry for all validation rules.

    Provides lookup by:
    - Rule ID
    - Gate number
    - Category
    - Field name
    """

    _instance = None
    _rules: Dict[str, Rule] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Load all rules into registry."""
        all_rules = SCHEMA_RULES + CONSISTENCY_RULES + HEURISTIC_RULES + APPROVAL_RULES

        for rule in all_rules:
            self._rules[rule.rule_id] = rule

    def get(self, rule_id: str) -> Optional[Rule]:
        """Get rule by ID."""
        return self._rules.get(rule_id)

    def get_by_gate(self, gate: RuleGate) -> List[Rule]:
        """Get all rules for a specific gate."""
        return [r for r in self._rules.values() if r.gate == gate]

    def get_by_category(self, category: RuleCategory) -> List[Rule]:
        """Get all rules for a specific category."""
        return [r for r in self._rules.values() if r.category == category]

    def get_by_field(self, field: str) -> List[Rule]:
        """Get all rules for a specific field."""
        return [r for r in self._rules.values() if r.field == field]

    def get_all(self) -> List[Rule]:
        """Get all rules."""
        return list(self._rules.values())

    def get_blockers(self) -> List[Rule]:
        """Get all blocker rules."""
        return [r for r in self._rules.values() if r.severity == RuleSeverity.BLOCKER]

    def count(self) -> int:
        """Get total number of rules."""
        return len(self._rules)

    def summary(self) -> Dict[str, Any]:
        """Get registry summary."""
        return {
            "total_rules": self.count(),
            "by_gate": {
                "gate_1": len(self.get_by_gate(RuleGate.GATE_1)),
                "gate_2": len(self.get_by_gate(RuleGate.GATE_2)),
                "gate_3": len(self.get_by_gate(RuleGate.GATE_3)),
            },
            "by_category": {
                "schema": len(self.get_by_category(RuleCategory.SCHEMA)),
                "consistency": len(self.get_by_category(RuleCategory.CONSISTENCY)),
                "heuristic": len(self.get_by_category(RuleCategory.HEURISTIC)),
                "approval": len(self.get_by_category(RuleCategory.APPROVAL)),
            },
            "by_severity": {
                "blocker": len(self.get_blockers()),
                "critical": len([r for r in self._rules.values() if r.severity == RuleSeverity.CRITICAL]),
                "warning": len([r for r in self._rules.values() if r.severity == RuleSeverity.WARNING]),
            },
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_rule(rule_id: str) -> Optional[Rule]:
    """Get rule by ID."""
    return RuleRegistry().get(rule_id)


def get_rules_by_gate(gate: int) -> List[Rule]:
    """Get all rules for a specific gate number."""
    return RuleRegistry().get_by_gate(RuleGate(gate))


def get_rules_by_category(category: str) -> List[Rule]:
    """Get all rules for a specific category."""
    return RuleRegistry().get_by_category(RuleCategory(category))


def get_all_rules() -> List[Rule]:
    """Get all rules."""
    return RuleRegistry().get_all()


def get_registry_summary() -> Dict[str, Any]:
    """Get registry summary."""
    return RuleRegistry().summary()


__all__ = [
    "Rule",
    "RuleRegistry",
    "RuleGate",
    "RuleCategory",
    "RuleSeverity",
    "get_rule",
    "get_rules_by_gate",
    "get_rules_by_category",
    "get_all_rules",
    "get_registry_summary",
    # Constants
    "VALID_DOMAINS",
    "VALID_ASPECTS",
    "VALID_IMPACTS",
    "VALID_CONSTRAINT_TYPES",
    "UUID_PATTERN",
    "VERSION_PATTERN",
    "CODE_PATTERN",
    "SCOPE_PATH_PATTERN",
]
