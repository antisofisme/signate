"""
MANTRA Gate 1: Deterministic Validation

HARD BLOCK - No AI involvement, pure rule-based validation.

Per MANTRA-LAW-001 AMENDMENT-004:
- Gate 1 is the first line of defense
- All rules are deterministic (same input = same output)
- Failure = IMMEDIATE REJECTION

RULES COVERED:
- S-001 to S-022: Schema validation
- D-001 to D-014: Decision consistency
- Structural integrity checks
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any, Set
import re
import uuid

from ..domain.schema_base import DomainId, AspectId, DOMAIN_ASPECT_MATRIX, is_aspect_compatible


# ============================================================================
# ENUMS
# ============================================================================

class Gate1Status(str, Enum):
    """Gate 1 validation status."""
    PASS = "PASS"       # All rules passed
    FAIL = "FAIL"       # One or more rules failed
    ERROR = "ERROR"     # Validation could not complete


class RuleCategory(str, Enum):
    """Category of validation rule."""
    SCHEMA = "SCHEMA"           # S-xxx rules
    CONSISTENCY = "CONSISTENCY" # D-xxx rules
    STRUCTURE = "STRUCTURE"     # Structural integrity


class RuleSeverity(str, Enum):
    """Rule violation severity."""
    BLOCKER = "BLOCKER"   # Must fix, blocks everything
    CRITICAL = "CRITICAL" # Must fix before approval
    WARNING = "WARNING"   # Should fix, advisory


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class RuleViolation:
    """A single rule violation."""
    rule_id: str
    category: RuleCategory
    severity: RuleSeverity
    message: str
    field: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "suggestion": self.suggestion,
        }


@dataclass
class Gate1Result:
    """Result of Gate 1 validation."""
    status: Gate1Status
    violations: List[RuleViolation] = field(default_factory=list)
    warnings: List[RuleViolation] = field(default_factory=list)
    rules_checked: int = 0
    rules_passed: int = 0
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validation_time_ms: float = 0.0

    @property
    def has_blockers(self) -> bool:
        return any(v.severity == RuleSeverity.BLOCKER for v in self.violations)

    @property
    def has_critical(self) -> bool:
        return any(v.severity == RuleSeverity.CRITICAL for v in self.violations)

    @property
    def can_proceed_to_gate2(self) -> bool:
        """Can proceed to Gate 2 only if no blockers."""
        return not self.has_blockers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "rules_checked": self.rules_checked,
            "rules_passed": self.rules_passed,
            "validated_at": self.validated_at.isoformat(),
            "validation_time_ms": round(self.validation_time_ms, 2),
            "can_proceed_to_gate2": self.can_proceed_to_gate2,
        }


# ============================================================================
# VALIDATION RULES
# ============================================================================

# UUID pattern
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE
)

# Version pattern (semantic versioning)
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

# Decision code pattern
CODE_PATTERN = re.compile(r"^[A-Z]+-A[0-9]{2}-[0-9]{3}$")

# Scope path pattern
SCOPE_PATH_PATTERN = re.compile(
    r"^(\*|[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*(\.\*)?|\*)$"
)


class Gate1Validator:
    """
    Gate 1: Deterministic Validation

    Validates decision records against structural and consistency rules.
    No AI involvement - pure deterministic checks.
    """

    def __init__(self):
        self.valid_domains = {d.value for d in DomainId}
        self.valid_aspects = {a.value for a in AspectId}

    def validate(self, record: Dict[str, Any]) -> Gate1Result:
        """
        Validate a decision record.

        Args:
            record: Decision record as dictionary

        Returns:
            Gate1Result with status and violations
        """
        start_time = datetime.now(timezone.utc)
        violations: List[RuleViolation] = []
        warnings: List[RuleViolation] = []
        rules_checked = 0
        rules_passed = 0

        # =====================================================================
        # SCHEMA RULES (S-001 to S-022)
        # =====================================================================

        # S-001: decision_id presence
        rules_checked += 1
        if "decision_id" not in record:
            violations.append(RuleViolation(
                rule_id="S-001",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="decision_id is required",
                field="decision_id",
                suggestion="Add a valid UUID as decision_id"
            ))
        else:
            rules_passed += 1

        # S-002: decision_id format
        rules_checked += 1
        if "decision_id" in record:
            if not UUID_PATTERN.match(str(record.get("decision_id", ""))):
                violations.append(RuleViolation(
                    rule_id="S-002",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.BLOCKER,
                    message="decision_id must be a valid UUID",
                    field="decision_id",
                    actual=str(record.get("decision_id", ""))[:50],
                    expected="UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                ))
            else:
                rules_passed += 1

        # S-003: code presence (MCP schema)
        rules_checked += 1
        code = record.get("code") or record.get("decision_code")
        if not code:
            violations.append(RuleViolation(
                rule_id="S-003",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="code (or decision_code) is required",
                field="code",
                suggestion="Add code in format DOMAIN-ASPECT-SEQ (e.g., ARCH-A06-001)"
            ))
        else:
            rules_passed += 1

        # S-004: code format
        rules_checked += 1
        if code and not CODE_PATTERN.match(str(code)):
            violations.append(RuleViolation(
                rule_id="S-004",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.CRITICAL,
                message="code must match pattern DOMAIN-ASPECT-SEQ",
                field="code",
                actual=str(code),
                expected="Format: XXX-ANN-NNN (e.g., ARCH-A06-001)"
            ))
        elif code:
            rules_passed += 1

        # S-005: domain_id presence
        rules_checked += 1
        if "domain_id" not in record:
            violations.append(RuleViolation(
                rule_id="S-005",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="domain_id is required",
                field="domain_id",
                suggestion=f"Valid domains: {', '.join(sorted(self.valid_domains))}"
            ))
        else:
            rules_passed += 1

        # S-006: domain_id enumeration
        rules_checked += 1
        domain_id = record.get("domain_id")
        if domain_id:
            domain_val = domain_id.value if hasattr(domain_id, 'value') else domain_id
            if domain_val not in self.valid_domains:
                violations.append(RuleViolation(
                    rule_id="S-006",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.BLOCKER,
                    message=f"domain_id must be one of: {sorted(self.valid_domains)}",
                    field="domain_id",
                    actual=str(domain_val)
                ))
            else:
                rules_passed += 1

        # S-007: aspect_id presence
        rules_checked += 1
        if "aspect_id" not in record:
            violations.append(RuleViolation(
                rule_id="S-007",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="aspect_id is required",
                field="aspect_id",
                suggestion=f"Valid aspects: A01-A16"
            ))
        else:
            rules_passed += 1

        # S-008: aspect_id enumeration
        rules_checked += 1
        aspect_id = record.get("aspect_id")
        if aspect_id:
            aspect_val = aspect_id.value if hasattr(aspect_id, 'value') else aspect_id
            if aspect_val not in self.valid_aspects:
                violations.append(RuleViolation(
                    rule_id="S-008",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.BLOCKER,
                    message=f"aspect_id must be one of: A01-A16",
                    field="aspect_id",
                    actual=str(aspect_val)
                ))
            else:
                rules_passed += 1

        # S-009: version presence
        rules_checked += 1
        if "version" not in record:
            violations.append(RuleViolation(
                rule_id="S-009",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="version is required",
                field="version",
                suggestion="Use semantic versioning: X.Y.Z"
            ))
        else:
            rules_passed += 1

        # S-010: version format
        rules_checked += 1
        version = record.get("version")
        if version and not VERSION_PATTERN.match(str(version)):
            violations.append(RuleViolation(
                rule_id="S-010",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.CRITICAL,
                message="version must follow semantic versioning (X.Y.Z)",
                field="version",
                actual=str(version)
            ))
        elif version:
            rules_passed += 1

        # S-011: statement presence
        rules_checked += 1
        if "statement" not in record or not record.get("statement"):
            violations.append(RuleViolation(
                rule_id="S-011",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="statement is required and must not be empty",
                field="statement"
            ))
        else:
            rules_passed += 1

        # S-012: statement type and length
        rules_checked += 1
        statement = record.get("statement", "")
        if statement:
            if not isinstance(statement, str):
                violations.append(RuleViolation(
                    rule_id="S-012",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.BLOCKER,
                    message="statement must be a string",
                    field="statement",
                    actual=type(statement).__name__
                ))
            elif len(statement) < 50:
                warnings.append(RuleViolation(
                    rule_id="S-012",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.WARNING,
                    message="statement should be at least 50 characters for clarity",
                    field="statement",
                    actual=f"{len(statement)} chars"
                ))
                rules_passed += 1
            elif len(statement) > 1500:
                violations.append(RuleViolation(
                    rule_id="S-012",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.CRITICAL,
                    message="statement should not exceed 1500 characters",
                    field="statement",
                    actual=f"{len(statement)} chars"
                ))
            else:
                rules_passed += 1

        # S-013: rationale presence
        rules_checked += 1
        if "rationale" not in record or not record.get("rationale"):
            violations.append(RuleViolation(
                rule_id="S-013",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="rationale is required and must not be empty",
                field="rationale"
            ))
        else:
            rules_passed += 1

        # S-014: rationale type and length
        rules_checked += 1
        rationale = record.get("rationale", "")
        if rationale:
            if not isinstance(rationale, str):
                violations.append(RuleViolation(
                    rule_id="S-014",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.BLOCKER,
                    message="rationale must be a string",
                    field="rationale"
                ))
            elif len(rationale) < 100:
                warnings.append(RuleViolation(
                    rule_id="S-014",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.WARNING,
                    message="rationale should be at least 100 characters",
                    field="rationale",
                    actual=f"{len(rationale)} chars"
                ))
                rules_passed += 1
            else:
                rules_passed += 1

        # S-015: constraints type
        rules_checked += 1
        constraints = record.get("constraints")
        if constraints is not None and not isinstance(constraints, list):
            violations.append(RuleViolation(
                rule_id="S-015",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="constraints must be an array",
                field="constraints",
                actual=type(constraints).__name__
            ))
        else:
            rules_passed += 1

        # S-016: constraint structure
        rules_checked += 1
        if isinstance(constraints, list):
            constraint_errors = self._validate_constraints(constraints)
            if constraint_errors:
                violations.extend(constraint_errors)
            else:
                rules_passed += 1

        # S-017: invariants type
        rules_checked += 1
        invariants = record.get("invariants")
        if invariants is not None and not isinstance(invariants, list):
            violations.append(RuleViolation(
                rule_id="S-017",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.CRITICAL,
                message="invariants must be an array",
                field="invariants"
            ))
        else:
            rules_passed += 1

        # S-018: authored_by presence (per LAW §2.3)
        rules_checked += 1
        authored_by = record.get("authored_by")
        if not authored_by:
            violations.append(RuleViolation(
                rule_id="S-018",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="authored_by is required per LAW §2.3",
                field="authored_by",
                suggestion="Must be a human identifier (not AI)"
            ))
        else:
            rules_passed += 1

        # S-019: authored_by not AI (per LAW §6)
        rules_checked += 1
        if authored_by and str(authored_by).lower().startswith("ai:"):
            violations.append(RuleViolation(
                rule_id="S-019",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.BLOCKER,
                message="authored_by must be human per LAW §6 (AI has ZERO authority)",
                field="authored_by",
                actual=str(authored_by)[:50]
            ))
        elif authored_by:
            rules_passed += 1

        # S-020: summary presence
        rules_checked += 1
        summary = record.get("summary")
        if not summary:
            warnings.append(RuleViolation(
                rule_id="S-020",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.WARNING,
                message="summary is recommended for quick scanning",
                field="summary"
            ))
        else:
            rules_passed += 1

        # S-021: impact presence
        rules_checked += 1
        impact = record.get("impact")
        if impact:
            valid_impacts = {"CRITICAL", "IMPORTANT", "REFERENCE"}
            impact_val = impact.value if hasattr(impact, 'value') else impact
            if impact_val not in valid_impacts:
                violations.append(RuleViolation(
                    rule_id="S-021",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.CRITICAL,
                    message=f"impact must be one of: {valid_impacts}",
                    field="impact",
                    actual=str(impact_val)
                ))
            else:
                rules_passed += 1
        else:
            rules_passed += 1  # impact is optional, defaults to IMPORTANT

        # S-022: scope_path format
        rules_checked += 1
        scope_path = record.get("scope_path", "*")
        if scope_path and not SCOPE_PATH_PATTERN.match(str(scope_path)):
            violations.append(RuleViolation(
                rule_id="S-022",
                category=RuleCategory.SCHEMA,
                severity=RuleSeverity.CRITICAL,
                message="scope_path must match pattern (e.g., 'fe.react.css' or '*')",
                field="scope_path",
                actual=str(scope_path)[:50]
            ))
        else:
            rules_passed += 1

        # =====================================================================
        # CONSISTENCY RULES (D-001 to D-014)
        # =====================================================================

        # D-001: Domain-Aspect compatibility
        rules_checked += 1
        if domain_id and aspect_id:
            domain_val = domain_id.value if hasattr(domain_id, 'value') else domain_id
            aspect_val = aspect_id.value if hasattr(aspect_id, 'value') else aspect_id
            try:
                domain_enum = DomainId(domain_val)
                aspect_enum = AspectId(aspect_val)
                if not is_aspect_compatible(domain_enum, aspect_enum):
                    valid_aspects = [a.value for a in DOMAIN_ASPECT_MATRIX.get(domain_enum, [])]
                    violations.append(RuleViolation(
                        rule_id="D-001",
                        category=RuleCategory.CONSISTENCY,
                        severity=RuleSeverity.BLOCKER,
                        message=f"Aspect {aspect_val} not compatible with domain {domain_val}",
                        field="aspect_id",
                        expected=f"Valid aspects for {domain_val}: {valid_aspects}"
                    ))
                else:
                    rules_passed += 1
            except ValueError:
                pass  # Already caught in schema validation

        # D-002: code matches domain-aspect
        rules_checked += 1
        if code and domain_id and aspect_id:
            domain_val = domain_id.value if hasattr(domain_id, 'value') else domain_id
            aspect_val = aspect_id.value if hasattr(aspect_id, 'value') else aspect_id
            expected_prefix = f"{domain_val}-{aspect_val}"
            if not str(code).startswith(expected_prefix):
                warnings.append(RuleViolation(
                    rule_id="D-002",
                    category=RuleCategory.CONSISTENCY,
                    severity=RuleSeverity.WARNING,
                    message=f"code should start with {expected_prefix}",
                    field="code",
                    actual=str(code),
                    expected=f"{expected_prefix}-NNN"
                ))
            else:
                rules_passed += 1

        # D-003: Constraint IDs unique
        rules_checked += 1
        if isinstance(constraints, list):
            constraint_ids = []
            for c in constraints:
                if isinstance(c, dict):
                    cid = c.get("id") or c.get("constraint_id")
                    if cid:
                        constraint_ids.append(cid)
            if len(constraint_ids) != len(set(constraint_ids)):
                violations.append(RuleViolation(
                    rule_id="D-003",
                    category=RuleCategory.CONSISTENCY,
                    severity=RuleSeverity.CRITICAL,
                    message="Constraint IDs must be unique within decision",
                    field="constraints"
                ))
            else:
                rules_passed += 1

        # D-004: depends_on references valid format
        rules_checked += 1
        depends_on = record.get("depends_on", [])
        if depends_on:
            for dep in depends_on:
                if not CODE_PATTERN.match(str(dep)) and not UUID_PATTERN.match(str(dep)):
                    violations.append(RuleViolation(
                        rule_id="D-004",
                        category=RuleCategory.CONSISTENCY,
                        severity=RuleSeverity.CRITICAL,
                        message="depends_on must contain valid decision codes or UUIDs",
                        field="depends_on",
                        actual=str(dep)[:50]
                    ))
                    break
            else:
                rules_passed += 1
        else:
            rules_passed += 1

        # D-005: supersedes reference valid format
        rules_checked += 1
        supersedes = record.get("supersedes")
        if supersedes:
            if not CODE_PATTERN.match(str(supersedes)) and not UUID_PATTERN.match(str(supersedes)):
                violations.append(RuleViolation(
                    rule_id="D-005",
                    category=RuleCategory.CONSISTENCY,
                    severity=RuleSeverity.CRITICAL,
                    message="supersedes must be a valid decision code or UUID",
                    field="supersedes",
                    actual=str(supersedes)[:50]
                ))
            else:
                rules_passed += 1
        else:
            rules_passed += 1

        # D-006: No self-reference in depends_on
        rules_checked += 1
        decision_id = record.get("decision_id")
        decision_code = record.get("code") or record.get("decision_code")
        if depends_on and (decision_id in depends_on or decision_code in depends_on):
            violations.append(RuleViolation(
                rule_id="D-006",
                category=RuleCategory.CONSISTENCY,
                severity=RuleSeverity.BLOCKER,
                message="Decision cannot depend on itself",
                field="depends_on"
            ))
        else:
            rules_passed += 1

        # D-007: No self-supersede
        rules_checked += 1
        if supersedes and (supersedes == decision_id or supersedes == decision_code):
            violations.append(RuleViolation(
                rule_id="D-007",
                category=RuleCategory.CONSISTENCY,
                severity=RuleSeverity.BLOCKER,
                message="Decision cannot supersede itself",
                field="supersedes"
            ))
        else:
            rules_passed += 1

        # D-008: priority_rank in range
        rules_checked += 1
        priority_rank = record.get("priority_rank")
        if priority_rank is not None:
            if not isinstance(priority_rank, int) or priority_rank < 1 or priority_rank > 100:
                violations.append(RuleViolation(
                    rule_id="D-008",
                    category=RuleCategory.CONSISTENCY,
                    severity=RuleSeverity.CRITICAL,
                    message="priority_rank must be integer 1-100",
                    field="priority_rank",
                    actual=str(priority_rank)
                ))
            else:
                rules_passed += 1
        else:
            rules_passed += 1

        # D-009: tags are strings
        rules_checked += 1
        tags = record.get("tags", [])
        if tags and not all(isinstance(t, str) for t in tags):
            violations.append(RuleViolation(
                rule_id="D-009",
                category=RuleCategory.CONSISTENCY,
                severity=RuleSeverity.CRITICAL,
                message="All tags must be strings",
                field="tags"
            ))
        else:
            rules_passed += 1

        # D-010: applies_to are strings
        rules_checked += 1
        applies_to = record.get("applies_to", [])
        if applies_to and not all(isinstance(a, str) for a in applies_to):
            violations.append(RuleViolation(
                rule_id="D-010",
                category=RuleCategory.CONSISTENCY,
                severity=RuleSeverity.CRITICAL,
                message="All applies_to entries must be strings",
                field="applies_to"
            ))
        else:
            rules_passed += 1

        # =====================================================================
        # BUILD RESULT
        # =====================================================================

        end_time = datetime.now(timezone.utc)
        validation_time_ms = (end_time - start_time).total_seconds() * 1000

        if violations:
            status = Gate1Status.FAIL
        else:
            status = Gate1Status.PASS

        return Gate1Result(
            status=status,
            violations=violations,
            warnings=warnings,
            rules_checked=rules_checked,
            rules_passed=rules_passed,
            validated_at=end_time,
            validation_time_ms=validation_time_ms,
        )

    def _validate_constraints(self, constraints: List) -> List[RuleViolation]:
        """Validate constraint structure."""
        violations = []
        valid_types = {"MUST", "MUST_NOT", "SHOULD", "MAY"}

        for i, constraint in enumerate(constraints):
            if not isinstance(constraint, dict):
                violations.append(RuleViolation(
                    rule_id="S-016",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.CRITICAL,
                    message=f"constraints[{i}] must be an object",
                    field=f"constraints[{i}]"
                ))
                continue

            # Check required fields
            rule = constraint.get("rule") or constraint.get("statement")
            if not rule:
                violations.append(RuleViolation(
                    rule_id="S-016",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.CRITICAL,
                    message=f"constraints[{i}].rule is required",
                    field=f"constraints[{i}].rule"
                ))

            # Check type
            ctype = constraint.get("type")
            if ctype and ctype not in valid_types:
                violations.append(RuleViolation(
                    rule_id="S-016",
                    category=RuleCategory.SCHEMA,
                    severity=RuleSeverity.CRITICAL,
                    message=f"constraints[{i}].type must be one of: {valid_types}",
                    field=f"constraints[{i}].type",
                    actual=str(ctype)
                ))

        return violations


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def validate_gate1(record: Dict[str, Any]) -> Gate1Result:
    """
    Validate a decision record through Gate 1.

    Args:
        record: Decision record as dictionary

    Returns:
        Gate1Result with status and violations
    """
    validator = Gate1Validator()
    return validator.validate(record)


__all__ = [
    "Gate1Status",
    "RuleCategory",
    "RuleSeverity",
    "RuleViolation",
    "Gate1Result",
    "Gate1Validator",
    "validate_gate1",
]
