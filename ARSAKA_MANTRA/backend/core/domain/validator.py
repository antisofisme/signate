"""
MANTRA Three-Gate Validator - Per LAW AMENDMENT-004

Gate 1: Script/Formula (Deterministic) - HARD block
Gate 2: AI Validator (Heuristic) - SOFT warn
Gate 3: Human Gate - HARD block (final)

No decision passes without Gate 3.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re

from .field_meta import (
    FIELD_REGISTRY,
    get_field_meta,
    get_required_fields,
    validate_length,
    ContentType,
    ValidationLevel,
)


class ValidationResult(str, Enum):
    """Validation outcome"""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


class GateType(str, Enum):
    """Three validation gates"""
    GATE_1_SCRIPT = "GATE_1"    # Deterministic
    GATE_2_AI = "GATE_2"        # Heuristic
    GATE_3_HUMAN = "GATE_3"     # Final


@dataclass
class ValidationIssue:
    """Single validation issue"""
    gate: GateType
    field: str
    rule: str
    message: str
    level: ValidationLevel
    suggestion: Optional[str] = None


@dataclass
class GateResult:
    """Result from one gate"""
    gate: GateType
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ValidationReport:
    """
    Full validation report - IMMUTABLE after creation.

    Per MANTRA-LAW-001: Validation results MUST NOT be modified
    after gates complete to prevent tampering.
    """
    __slots__ = ('_decision_id', '_gate_1', '_gate_2', '_gate_3', '_frozen')

    def __init__(
        self,
        decision_id: str,
        gate_1: Optional[GateResult] = None,
        gate_2: Optional[GateResult] = None,
        gate_3: Optional[GateResult] = None,
    ):
        object.__setattr__(self, '_decision_id', decision_id)
        object.__setattr__(self, '_gate_1', gate_1)
        object.__setattr__(self, '_gate_2', gate_2)
        object.__setattr__(self, '_gate_3', gate_3)
        object.__setattr__(self, '_frozen', False)

    def __setattr__(self, name, value):
        if hasattr(self, '_frozen') and self._frozen:
            raise AttributeError(
                f"ValidationReport is frozen. Cannot modify '{name}'. "
                "Per MANTRA-LAW-001, validation results are immutable."
            )
        object.__setattr__(self, name, value)

    def _freeze(self):
        """Freeze the report after all gates complete."""
        object.__setattr__(self, '_frozen', True)

    @property
    def decision_id(self) -> str:
        return self._decision_id

    @property
    def gate_1(self) -> Optional[GateResult]:
        return self._gate_1

    @property
    def gate_2(self) -> Optional[GateResult]:
        return self._gate_2

    @property
    def gate_3(self) -> Optional[GateResult]:
        return self._gate_3

    @property
    def can_proceed(self) -> bool:
        """Can proceed to next gate?"""
        if self._gate_1 and not self._gate_1.passed:
            return False
        return True

    @property
    def is_approved(self) -> bool:
        """Fully approved by all gates?"""
        return (
            self._gate_1 and self._gate_1.passed and
            self._gate_2 is not None and  # AI gate ran (doesn't need to pass)
            self._gate_3 and self._gate_3.passed
        )

    def with_gate_1(self, result: GateResult) -> 'ValidationReport':
        """Return new report with Gate 1 result."""
        if self._frozen:
            raise AttributeError("Cannot modify frozen ValidationReport")
        return ValidationReport(
            decision_id=self._decision_id,
            gate_1=result,
            gate_2=self._gate_2,
            gate_3=self._gate_3,
        )

    def with_gate_2(self, result: GateResult) -> 'ValidationReport':
        """Return new report with Gate 2 result."""
        if self._frozen:
            raise AttributeError("Cannot modify frozen ValidationReport")
        return ValidationReport(
            decision_id=self._decision_id,
            gate_1=self._gate_1,
            gate_2=result,
            gate_3=self._gate_3,
        )

    def with_gate_3(self, result: GateResult) -> 'ValidationReport':
        """Return new report with Gate 3 result (and freeze)."""
        report = ValidationReport(
            decision_id=self._decision_id,
            gate_1=self._gate_1,
            gate_2=self._gate_2,
            gate_3=result,
        )
        report._freeze()  # Freeze after Gate 3
        return report


# ============================================================================
# GATE 1: SCRIPT/FORMULA (DETERMINISTIC)
# ============================================================================

class Gate1Validator:
    """
    Deterministic validation - HARD block.

    Checks:
    - Required fields present
    - Length limits
    - Format compliance
    - Reference validity
    """

    # Patterns
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    SEMVER_PATTERN = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
    CODE_PATTERN = re.compile(r'^[A-Z]+-A[0-9]{2}-[0-9]{3}$')
    CONSTRAINT_START = re.compile(r'^(MUST|MUST NOT|SHOULD|MAY)\b', re.IGNORECASE)

    def validate(self, decision: Dict[str, Any]) -> GateResult:
        """Run Gate 1 validation."""
        issues = []

        # Check required fields
        issues.extend(self._check_required(decision))

        # Check lengths
        issues.extend(self._check_lengths(decision))

        # Check formats
        issues.extend(self._check_formats(decision))

        # Check constraints format
        issues.extend(self._check_constraints(decision))

        # Check invariants
        issues.extend(self._check_invariants(decision))

        # Check content types per §12
        issues.extend(self._check_content_types(decision))

        # Check supersedes chain (no circular references)
        issues.extend(self._check_supersedes(decision))

        # Determine pass/fail
        hard_failures = [i for i in issues if i.level == ValidationLevel.HARD]
        passed = len(hard_failures) == 0

        return GateResult(
            gate=GateType.GATE_1_SCRIPT,
            passed=passed,
            issues=issues,
        )

    def _check_required(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """Check required fields."""
        issues = []
        for field_name in get_required_fields():
            value = decision.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field=field_name,
                    rule="REQUIRED",
                    message=f"Required field '{field_name}' is missing or empty",
                    level=ValidationLevel.HARD,
                ))
        return issues

    def _check_lengths(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """Check field lengths."""
        issues = []
        for field_name, value in decision.items():
            if isinstance(value, str):
                valid, msg = validate_length(field_name, value)
                if not valid:
                    meta = get_field_meta(field_name)
                    issues.append(ValidationIssue(
                        gate=GateType.GATE_1_SCRIPT,
                        field=field_name,
                        rule="MAX_LENGTH",
                        message=msg,
                        level=meta.validation_level if meta else ValidationLevel.HARD,
                        suggestion=f"Reduce to {meta.max_length} chars" if meta else None,
                    ))
        return issues

    def _check_formats(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """Check format compliance."""
        issues = []

        # UUID format
        if "decision_id" in decision:
            if not self.UUID_PATTERN.match(decision["decision_id"]):
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field="decision_id",
                    rule="UUID_FORMAT",
                    message="decision_id must be valid UUID",
                    level=ValidationLevel.HARD,
                ))

        # Semver format
        if "version" in decision:
            if not self.SEMVER_PATTERN.match(decision["version"]):
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field="version",
                    rule="SEMVER_FORMAT",
                    message="version must be X.Y.Z format",
                    level=ValidationLevel.HARD,
                ))

        # Code format
        if "code" in decision:
            if not self.CODE_PATTERN.match(decision["code"]):
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field="code",
                    rule="CODE_FORMAT",
                    message="code must be DOMAIN-ASPECT-SEQ (e.g., ARCH-A06-001)",
                    level=ValidationLevel.HARD,
                ))

        # Human author check
        if "authored_by" in decision:
            if decision["authored_by"].startswith("ai:"):
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field="authored_by",
                    rule="HUMAN_AUTHOR",
                    message="authored_by must be human, not AI",
                    level=ValidationLevel.HARD,
                ))

        return issues

    def _check_constraints(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """Check constraints format."""
        issues = []
        constraints = decision.get("constraints", [])

        if len(constraints) > 10:
            issues.append(ValidationIssue(
                gate=GateType.GATE_1_SCRIPT,
                field="constraints",
                rule="MAX_ITEMS",
                message=f"Too many constraints: {len(constraints)} (max 10)",
                level=ValidationLevel.HARD,
            ))

        for i, c in enumerate(constraints):
            rule = c.get("rule", "") if isinstance(c, dict) else str(c)
            if not self.CONSTRAINT_START.match(rule):
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field=f"constraints[{i}]",
                    rule="CONSTRAINT_FORMAT",
                    message="Constraint must start with MUST/MUST NOT/SHOULD/MAY",
                    level=ValidationLevel.HARD,
                ))
            if len(rule) > 100:
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field=f"constraints[{i}]",
                    rule="MAX_LENGTH",
                    message=f"Constraint too long: {len(rule)} (max 100)",
                    level=ValidationLevel.HARD,
                ))

        return issues

    def _check_invariants(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """Check invariants."""
        issues = []
        invariants = decision.get("invariants", [])

        if len(invariants) > 10:
            issues.append(ValidationIssue(
                gate=GateType.GATE_1_SCRIPT,
                field="invariants",
                rule="MAX_ITEMS",
                message=f"Too many invariants: {len(invariants)} (max 10)",
                level=ValidationLevel.HARD,
            ))

        for i, inv in enumerate(invariants):
            if len(inv) > 100:
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field=f"invariants[{i}]",
                    rule="MAX_LENGTH",
                    message=f"Invariant too long: {len(inv)} (max 100)",
                    level=ValidationLevel.HARD,
                ))

        return issues

    def _check_content_types(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Check content types per LAW §12 (Normative vs Descriptive).

        RULE fields (statement, constraints, invariants): Must be definitive
        RATIONALE fields: Can be descriptive
        CONTEXT fields: Informational only
        """
        issues = []

        # RULE fields should not contain hedging language
        rule_fields = ["statement"]
        hedging_in_rules = [
            "might", "probably", "perhaps", "maybe", "possibly",
            "consider", "generally", "usually", "sometimes", "often"
        ]

        for field_name in rule_fields:
            value = decision.get(field_name, "")
            if not value:
                continue

            value_lower = value.lower()
            for word in hedging_in_rules:
                if f" {word} " in f" {value_lower} ":
                    issues.append(ValidationIssue(
                        gate=GateType.GATE_1_SCRIPT,
                        field=field_name,
                        rule="CONTENT_TYPE_RULE",
                        message=f"Per §12: RULE field '{field_name}' contains hedging word '{word}'",
                        level=ValidationLevel.SOFT,  # Warn, not block
                        suggestion=f"Remove '{word}' - rules should be definitive",
                    ))

        # Constraints must be enforceable (start with MUST/SHOULD/MAY)
        constraints = decision.get("constraints", [])
        for i, c in enumerate(constraints):
            rule = c.get("rule", "") if isinstance(c, dict) else str(c)
            # Check for vague language
            vague_patterns = ["as needed", "when appropriate", "if possible", "try to"]
            for pattern in vague_patterns:
                if pattern in rule.lower():
                    issues.append(ValidationIssue(
                        gate=GateType.GATE_1_SCRIPT,
                        field=f"constraints[{i}]",
                        rule="CONTENT_TYPE_RULE",
                        message=f"Per §12: Constraint contains vague phrase '{pattern}'",
                        level=ValidationLevel.SOFT,
                        suggestion="Make constraint specific and verifiable",
                    ))

        return issues

    def _check_supersedes(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Check supersedes chain integrity.

        NOTE: Full circular chain detection requires repository access.
        This only checks for obvious self-reference.
        """
        issues = []

        supersedes = decision.get("supersedes")
        decision_id = decision.get("decision_id")

        if supersedes:
            # Check self-reference
            if supersedes == decision_id:
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field="supersedes",
                    rule="NO_SELF_SUPERSEDE",
                    message="Decision cannot supersede itself",
                    level=ValidationLevel.HARD,
                ))

            # Check UUID format
            if not self.UUID_PATTERN.match(supersedes):
                issues.append(ValidationIssue(
                    gate=GateType.GATE_1_SCRIPT,
                    field="supersedes",
                    rule="UUID_FORMAT",
                    message="supersedes must be valid UUID",
                    level=ValidationLevel.HARD,
                ))

        # Check related_decisions for self-reference
        related = decision.get("related_decisions", [])
        if decision_id and decision_id in related:
            issues.append(ValidationIssue(
                gate=GateType.GATE_1_SCRIPT,
                field="related_decisions",
                rule="NO_SELF_REFERENCE",
                message="Decision cannot reference itself in related_decisions",
                level=ValidationLevel.HARD,
            ))

        return issues


# ============================================================================
# GATE 2: AI VALIDATOR (HEURISTIC)
# ============================================================================

class Gate2Validator:
    """
    AI heuristic validation - SOFT warn.

    Checks:
    - Redundancy across fields
    - Ambiguous language
    - Over-verbosity
    - Implicit conflicts

    NOTE: This is a placeholder. Real implementation would call AI.
    """

    # Anti-patterns to detect
    HEDGING_WORDS = [
        "might", "probably", "perhaps", "maybe", "possibly",
        "consider", "could", "generally", "usually", "sometimes"
    ]

    VERBOSE_PHRASES = [
        "in order to", "due to the fact that", "at this point in time",
        "in the event that", "for the purpose of", "with regard to"
    ]

    def validate(self, decision: Dict[str, Any]) -> GateResult:
        """Run Gate 2 validation."""
        issues = []

        # Check for hedging language
        issues.extend(self._check_hedging(decision))

        # Check for verbose phrases
        issues.extend(self._check_verbosity(decision))

        # Check for repetition
        issues.extend(self._check_repetition(decision))

        # Gate 2 always "passes" - it only warns
        return GateResult(
            gate=GateType.GATE_2_AI,
            passed=True,  # Soft gate - doesn't block
            issues=issues,
        )

    def _check_hedging(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """Detect hedging language in rule fields."""
        issues = []
        rule_fields = ["statement", "constraints", "invariants"]

        for field_name in rule_fields:
            value = decision.get(field_name)
            if not value:
                continue

            text = str(value).lower()
            for word in self.HEDGING_WORDS:
                if word in text:
                    issues.append(ValidationIssue(
                        gate=GateType.GATE_2_AI,
                        field=field_name,
                        rule="NO_HEDGING",
                        message=f"Hedging word '{word}' found - rules should be definitive",
                        level=ValidationLevel.SOFT,
                        suggestion=f"Remove '{word}' or make statement more definitive",
                    ))

        return issues

    def _check_verbosity(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """Detect verbose phrases."""
        issues = []

        for field_name, value in decision.items():
            if not isinstance(value, str):
                continue

            text = value.lower()
            for phrase in self.VERBOSE_PHRASES:
                if phrase in text:
                    issues.append(ValidationIssue(
                        gate=GateType.GATE_2_AI,
                        field=field_name,
                        rule="NO_VERBOSE",
                        message=f"Verbose phrase '{phrase}' detected",
                        level=ValidationLevel.ADVISORY,
                        suggestion="Simplify language",
                    ))

        return issues

    def _check_repetition(self, decision: Dict[str, Any]) -> List[ValidationIssue]:
        """Detect repetition across fields."""
        issues = []

        # Extract key phrases from statement
        statement = decision.get("statement", "").lower()
        rationale = decision.get("rationale", "").lower()

        # Check if statement is repeated verbatim in rationale
        if statement and statement in rationale:
            issues.append(ValidationIssue(
                gate=GateType.GATE_2_AI,
                field="rationale",
                rule="NO_REPETITION",
                message="Statement appears verbatim in rationale",
                level=ValidationLevel.SOFT,
                suggestion="Rationale should explain WHY, not repeat WHAT",
            ))

        return issues


# ============================================================================
# GATE 3: HUMAN GATE (FINAL)
# ============================================================================

class HumanDecisionAction(str, Enum):
    """Valid human decision actions."""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REVISE = "REVISE"
    EXCEPTION = "EXCEPTION"


@dataclass(frozen=True)
class HumanDecision:
    """
    Human gate decision - IMMUTABLE.

    Per MANTRA-LAW-001 §6: Decisions require human approval.
    Reviewer field is REQUIRED to enforce accountability.
    """
    action: HumanDecisionAction
    reviewer: str  # REQUIRED - no anonymous approvals
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate required fields."""
        # Validate reviewer is not empty
        if not self.reviewer or not self.reviewer.strip():
            raise ValueError(
                "HumanDecision.reviewer is REQUIRED per MANTRA-LAW-001 §6. "
                "Anonymous approvals are not permitted."
            )
        # Validate reviewer is human (not AI)
        if self.reviewer.lower().startswith("ai:"):
            raise ValueError(
                f"HumanDecision.reviewer must be human, got '{self.reviewer}'. "
                "Per MANTRA-LAW-001 §6, AI cannot approve decisions."
            )
        # Validate reason is provided for non-ACCEPT actions
        if self.action != HumanDecisionAction.ACCEPT and not self.reason:
            raise ValueError(
                f"HumanDecision.reason is REQUIRED for action={self.action.value}. "
                "Rejection/revision/exception must include justification."
            )


@dataclass(frozen=True)
class HumanApprovalAudit:
    """
    Full audit trail for human approval decisions.

    Per MANTRA-LAW-001 §6: All approvals must be auditable.

    This captures:
    - The decision itself (HumanDecision)
    - Context (decision_id, version)
    - Client info (IP, user agent)
    - Session (correlation for multi-step workflows)
    - Integrity (hash of decision content at approval time)

    IMMUTABLE: Once created, cannot be modified.
    """
    # Core approval
    decision_id: str
    decision_version: str
    human_decision: HumanDecision

    # Audit metadata
    audit_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Client context (optional but recommended)
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    # Integrity
    content_hash: Optional[str] = None  # SHA256 of decision content at approval time

    # Workflow context
    gate_1_passed_at: Optional[datetime] = None
    gate_2_completed_at: Optional[datetime] = None
    previous_approval_id: Optional[str] = None  # For revisions

    def __post_init__(self):
        """Validate audit integrity."""
        if not self.decision_id:
            raise ValueError("HumanApprovalAudit requires decision_id")
        if not self.decision_version:
            raise ValueError("HumanApprovalAudit requires decision_version")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API response."""
        return {
            "audit_id": self.audit_id,
            "decision_id": self.decision_id,
            "decision_version": self.decision_version,
            "action": self.human_decision.action.value,
            "reviewer": self.human_decision.reviewer,
            "reason": self.human_decision.reason,
            "approved_at": self.human_decision.timestamp.isoformat(),
            "audit_created_at": self.created_at.isoformat(),
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "content_hash": self.content_hash,
            "gate_1_passed_at": self.gate_1_passed_at.isoformat() if self.gate_1_passed_at else None,
            "gate_2_completed_at": self.gate_2_completed_at.isoformat() if self.gate_2_completed_at else None,
            "previous_approval_id": self.previous_approval_id,
        }

    @classmethod
    def create_from_report(
        cls,
        report: 'ValidationReport',
        human_decision: HumanDecision,
        decision_version: str,
        content_hash: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> 'HumanApprovalAudit':
        """
        Create audit from validation report.

        This is the preferred way to create an audit - it extracts
        gate timestamps from the report automatically.
        """
        return cls(
            decision_id=report.decision_id,
            decision_version=decision_version,
            human_decision=human_decision,
            client_ip=client_ip,
            user_agent=user_agent,
            session_id=session_id,
            content_hash=content_hash,
            gate_1_passed_at=report.gate_1.timestamp if report.gate_1 else None,
            gate_2_completed_at=report.gate_2.timestamp if report.gate_2 else None,
        )


def compute_decision_hash(decision: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of decision content for integrity.

    Only hashes immutable fields per LAW §2.3.
    """
    import hashlib
    import json

    # Fields to hash (immutable per LAW)
    hash_fields = [
        "decision_id", "code", "version",
        "domain_id", "aspect_id",
        "statement", "rationale",
        "constraints", "invariants",
    ]

    content = {k: decision.get(k) for k in hash_fields if k in decision}
    content_str = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(content_str.encode()).hexdigest()


class Gate3Validator:
    """
    Human final gate - HARD block.

    Actions:
    - ACCEPT: Approve as-is
    - REJECT: Block with reason
    - REVISE: Request changes
    - EXCEPTION: Grant exception with justification
    """

    def validate(self, decision: Dict[str, Any], human_decision: HumanDecision) -> GateResult:
        """
        Run Gate 3 validation based on human decision.

        Per MANTRA-LAW-001 §6: This gate is MANDATORY.
        No decision can be stored without human approval.
        """
        issues = []

        # HumanDecision is already validated in __post_init__
        # Here we just map action to result

        if human_decision.action == HumanDecisionAction.REJECT:
            issues.append(ValidationIssue(
                gate=GateType.GATE_3_HUMAN,
                field="_decision",
                rule="HUMAN_REJECT",
                message=f"Rejected by {human_decision.reviewer}: {human_decision.reason}",
                level=ValidationLevel.HARD,
            ))
            passed = False

        elif human_decision.action == HumanDecisionAction.REVISE:
            issues.append(ValidationIssue(
                gate=GateType.GATE_3_HUMAN,
                field="_decision",
                rule="HUMAN_REVISE",
                message=f"Revision requested by {human_decision.reviewer}: {human_decision.reason}",
                level=ValidationLevel.HARD,
            ))
            passed = False

        elif human_decision.action == HumanDecisionAction.EXCEPTION:
            issues.append(ValidationIssue(
                gate=GateType.GATE_3_HUMAN,
                field="_decision",
                rule="HUMAN_EXCEPTION",
                message=f"Exception granted by {human_decision.reviewer}: {human_decision.reason}",
                level=ValidationLevel.ADVISORY,
            ))
            passed = True

        elif human_decision.action == HumanDecisionAction.ACCEPT:
            # Record approval for audit
            issues.append(ValidationIssue(
                gate=GateType.GATE_3_HUMAN,
                field="_decision",
                rule="HUMAN_ACCEPT",
                message=f"Approved by {human_decision.reviewer}",
                level=ValidationLevel.ADVISORY,
            ))
            passed = True

        else:
            # This should never happen due to enum, but defensive
            issues.append(ValidationIssue(
                gate=GateType.GATE_3_HUMAN,
                field="_decision",
                rule="INVALID_ACTION",
                message=f"Unknown action: {human_decision.action}",
                level=ValidationLevel.HARD,
            ))
            passed = False

        return GateResult(
            gate=GateType.GATE_3_HUMAN,
            passed=passed,
            issues=issues,
            timestamp=human_decision.timestamp,
        )


# ============================================================================
# MAIN VALIDATOR
# ============================================================================

class MantraValidator:
    """
    Three-gate validator orchestrator.

    GATE ORDER IS MANDATORY:
    1. Gate 1 (Deterministic) - MUST pass before Gate 2
    2. Gate 2 (AI Heuristic) - MUST run before Gate 3
    3. Gate 3 (Human) - MANDATORY, freezes report

    Per MANTRA-LAW-001: No decision can bypass any gate.

    Usage:
        validator = MantraValidator()

        # Gate 1: Automatic
        report = validator.run_gate_1(decision)
        if not report.can_proceed:
            return report  # Fix issues first

        # Gate 2: AI (automatic)
        report = validator.run_gate_2(decision, report)

        # Gate 3: Human (requires input)
        human_decision = HumanDecision(
            action=HumanDecisionAction.ACCEPT,
            reviewer="john@example.com"
        )
        report = validator.run_gate_3(decision, report, human_decision)

        if report.is_approved:
            save_decision(decision)
    """

    def __init__(self):
        self.gate_1 = Gate1Validator()
        self.gate_2 = Gate2Validator()
        self.gate_3 = Gate3Validator()

    def run_gate_1(self, decision: Dict[str, Any]) -> ValidationReport:
        """Run Gate 1 (deterministic)."""
        result = self.gate_1.validate(decision)
        return ValidationReport(
            decision_id=decision.get("decision_id", "unknown"),
            gate_1=result,
        )

    def run_gate_2(self, decision: Dict[str, Any], report: ValidationReport) -> ValidationReport:
        """
        Run Gate 2 (AI heuristic).

        PREREQUISITE: Gate 1 must have passed.
        """
        # Enforce gate order
        if report.gate_1 is None:
            raise ValueError(
                "Gate 2 cannot run before Gate 1. "
                "Per MANTRA-LAW-001, gates must run in order."
            )
        if not report.can_proceed:
            return report

        result = self.gate_2.validate(decision)
        return report.with_gate_2(result)

    def run_gate_3(
        self,
        decision: Dict[str, Any],
        report: ValidationReport,
        human_decision: HumanDecision
    ) -> ValidationReport:
        """
        Run Gate 3 (human final).

        PREREQUISITE: Gate 1 must have passed, Gate 2 must have run.
        This gate freezes the report.
        """
        # Enforce gate order
        if report.gate_1 is None:
            raise ValueError(
                "Gate 3 cannot run before Gate 1. "
                "Per MANTRA-LAW-001, gates must run in order."
            )
        if report.gate_2 is None:
            raise ValueError(
                "Gate 3 cannot run before Gate 2. "
                "Per MANTRA-LAW-001, gates must run in order."
            )

        result = self.gate_3.validate(decision, human_decision)
        return report.with_gate_3(result)  # This freezes the report

    def validate_all(
        self,
        decision: Dict[str, Any],
        human_decision: HumanDecision
    ) -> ValidationReport:
        """
        Run all gates in sequence.

        Returns frozen ValidationReport.
        """
        report = self.run_gate_1(decision)
        if not report.can_proceed:
            return report

        report = self.run_gate_2(decision, report)
        report = self.run_gate_3(decision, report, human_decision)
        return report


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "ValidationResult",
    "GateType",
    "HumanDecisionAction",
    # Dataclasses
    "ValidationIssue",
    "GateResult",
    "ValidationReport",
    "HumanDecision",
    "HumanApprovalAudit",
    # Functions
    "compute_decision_hash",
    # Validators
    "Gate1Validator",
    "Gate2Validator",
    "Gate3Validator",
    "MantraValidator",
]
