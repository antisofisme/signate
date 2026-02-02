"""
Validation Module Contract

Defines the interface for the 3-gate validation pipeline.
Teams implementing validation must conform to this contract.

Owner: Validation Team
Dependencies: Domain models only
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


# =============================================================================
# DATA TRANSFER OBJECTS
# =============================================================================

class GateStatus(str, Enum):
    """Status of a validation gate."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"
    ERROR = "ERROR"


class RuleSeverity(str, Enum):
    """Severity of rule violation."""
    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


@dataclass
class RuleViolation:
    """A single rule violation."""
    rule_id: str
    message: str
    severity: RuleSeverity
    field: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity.value,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "suggestion": self.suggestion,
        }


@dataclass
class GateResult:
    """Result of a single gate validation."""
    gate: int
    status: GateStatus
    violations: List[RuleViolation] = field(default_factory=list)
    warnings: List[RuleViolation] = field(default_factory=list)
    rules_checked: int = 0
    rules_passed: int = 0
    validation_time_ms: float = 0.0

    @property
    def can_proceed(self) -> bool:
        """Can proceed to next gate."""
        return self.status in (GateStatus.PASS, GateStatus.WARN)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "status": self.status.value,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "rules_checked": self.rules_checked,
            "rules_passed": self.rules_passed,
            "validation_time_ms": self.validation_time_ms,
            "can_proceed": self.can_proceed,
        }


@dataclass
class ValidationRequest:
    """Request to validate a decision."""
    decision: Dict[str, Any]
    skip_gates: List[int] = field(default_factory=list)
    user_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class ValidationResponse:
    """Response from validation pipeline."""
    request_id: str
    overall_status: GateStatus
    gate_results: List[GateResult]
    validated_at: datetime
    total_time_ms: float
    can_store: bool
    pending_approval: bool = False
    approval_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "overall_status": self.overall_status.value,
            "gate_results": [g.to_dict() for g in self.gate_results],
            "validated_at": self.validated_at.isoformat(),
            "total_time_ms": self.total_time_ms,
            "can_store": self.can_store,
            "pending_approval": self.pending_approval,
            "approval_id": self.approval_id,
        }


# =============================================================================
# GATE CONTRACTS
# =============================================================================

class Gate1Contract(ABC):
    """
    Gate 1: Deterministic Validation Contract

    Responsibilities:
    - Schema validation (S-rules)
    - Consistency checks (D-rules)
    - No AI involvement

    Output:
    - PASS: All rules passed
    - FAIL: One or more rules failed (blocker or critical)
    - WARN: Only warnings (can proceed)
    """

    @abstractmethod
    def validate(self, record: Dict[str, Any]) -> GateResult:
        """
        Validate decision record against Gate 1 rules.

        Args:
            record: Decision record as dictionary

        Returns:
            GateResult with status and violations
        """
        pass


class Gate2Contract(ABC):
    """
    Gate 2: AI Heuristic Validation Contract

    Responsibilities:
    - Quality scoring (H-rules)
    - Conflict detection (advisory)
    - Duplicate detection (advisory)

    Output:
    - PASS: Quality score >= threshold
    - WARN: Quality score below threshold (can proceed)
    - SKIP: AI not available
    """

    @abstractmethod
    async def validate(
        self,
        record: Dict[str, Any],
        existing_decisions: Optional[List[Dict[str, Any]]] = None,
    ) -> GateResult:
        """
        Validate decision using AI heuristics.

        Args:
            record: Decision record as dictionary
            existing_decisions: Optional list of existing decisions for conflict check

        Returns:
            GateResult with status and warnings
        """
        pass


class Gate3Contract(ABC):
    """
    Gate 3: Human Approval Contract

    Responsibilities:
    - Human approval workflow (A-rules)
    - Per MANTRA-LAW-001 §6: AI has ZERO authority

    Output:
    - PASS: Human approved
    - PENDING: Awaiting human approval
    - FAIL: Human rejected
    """

    @abstractmethod
    async def submit_for_approval(
        self,
        record: Dict[str, Any],
        gate1_result: GateResult,
        gate2_result: GateResult,
        user_id: str,
    ) -> str:
        """
        Submit decision for human approval.

        Args:
            record: Decision record
            gate1_result: Result from Gate 1
            gate2_result: Result from Gate 2
            user_id: User who initiated

        Returns:
            Approval request ID
        """
        pass

    @abstractmethod
    async def approve(
        self,
        approval_id: str,
        approver_id: str,
        comment: Optional[str] = None,
    ) -> GateResult:
        """
        Approve a pending decision.

        Args:
            approval_id: Approval request ID
            approver_id: Human approver ID (MUST be human)
            comment: Optional approval comment

        Returns:
            GateResult with PASS status
        """
        pass

    @abstractmethod
    async def reject(
        self,
        approval_id: str,
        approver_id: str,
        reason: str,
    ) -> GateResult:
        """
        Reject a pending decision.

        Args:
            approval_id: Approval request ID
            approver_id: Human approver ID
            reason: Rejection reason

        Returns:
            GateResult with FAIL status
        """
        pass


# =============================================================================
# VALIDATION PIPELINE CONTRACT
# =============================================================================

class ValidationContract(ABC):
    """
    Validation Pipeline Contract

    Orchestrates the 3-gate validation process.

    Usage:
        validator = ValidationPipeline()
        response = await validator.validate(request)

        if response.can_store:
            # Store the decision
        elif response.pending_approval:
            # Wait for human approval
        else:
            # Show validation errors
    """

    @abstractmethod
    async def validate(self, request: ValidationRequest) -> ValidationResponse:
        """
        Run full validation pipeline.

        Flow:
        1. Gate 1 (Deterministic) - MUST PASS
        2. Gate 2 (AI Heuristic) - Advisory
        3. Gate 3 (Human Approval) - If required

        Args:
            request: ValidationRequest with decision data

        Returns:
            ValidationResponse with all gate results
        """
        pass

    @abstractmethod
    async def validate_gate1_only(
        self,
        record: Dict[str, Any]
    ) -> GateResult:
        """
        Quick validation using Gate 1 only.

        Useful for real-time form validation.

        Args:
            record: Decision record

        Returns:
            GateResult from Gate 1
        """
        pass

    @abstractmethod
    async def get_pending_approvals(
        self,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get pending approval requests.

        Args:
            user_id: Optional filter by user

        Returns:
            List of pending approval records
        """
        pass


__all__ = [
    "GateStatus",
    "RuleSeverity",
    "RuleViolation",
    "GateResult",
    "ValidationRequest",
    "ValidationResponse",
    "Gate1Contract",
    "Gate2Contract",
    "Gate3Contract",
    "ValidationContract",
]
