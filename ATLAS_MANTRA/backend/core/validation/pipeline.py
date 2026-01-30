"""
MANTRA 3-Gate Validation Pipeline

Orchestrates the complete validation flow:

    ┌─────────────────────────────────────────────────────────────┐
    │                    DECISION SUBMITTED                        │
    └─────────────────────┬───────────────────────────────────────┘
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  GATE 1: DETERMINISTIC (HARD BLOCK)                         │
    │  - Schema validation (S-001 to S-022)                       │
    │  - Consistency checks (D-001 to D-014)                      │
    │  - PASS → Continue | FAIL → REJECT                          │
    └─────────────────────┬───────────────────────────────────────┘
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  GATE 2: AI HEURISTIC (SOFT WARN)                           │
    │  - Quality scoring                                          │
    │  - Conflict detection                                       │
    │  - Duplicate detection                                      │
    │  - PASS → Continue | WARN → Continue with warnings          │
    └─────────────────────┬───────────────────────────────────────┘
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  GATE 3: HUMAN APPROVAL (HARD BLOCK)                        │
    │  - Human reviews Gate 1 & 2 results                         │
    │  - Human approves/rejects/requests changes                  │
    │  - APPROVED → ACTIVE | NOT APPROVED → PENDING               │
    └─────────────────────┬───────────────────────────────────────┘
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    DECISION ACTIVE                           │
    └─────────────────────────────────────────────────────────────┘

Per MANTRA-LAW-001:
- Gate 1 & 3 are HARD blocks (must pass)
- Gate 2 is SOFT (advisory only)
- AI has ZERO authority in Gate 3
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any, Callable

from .gate1_deterministic import Gate1Validator, Gate1Result, Gate1Status
from .gate2_ai_validator import Gate2AIValidator, Gate2AIResult, create_gate2_validator
from .gate3_human_approval import (
    HumanApprovalManager, Gate3Validator, Gate3Result,
    ApprovalStatus, ApprovalRequest, create_approval_manager,
)


# ============================================================================
# ENUMS
# ============================================================================

class PipelineStage(str, Enum):
    """Current stage in the pipeline."""
    NOT_STARTED = "NOT_STARTED"
    GATE1_VALIDATING = "GATE1_VALIDATING"
    GATE1_FAILED = "GATE1_FAILED"
    GATE2_VALIDATING = "GATE2_VALIDATING"
    GATE2_COMPLETE = "GATE2_COMPLETE"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"


class PipelineOutcome(str, Enum):
    """Final outcome of pipeline."""
    PENDING = "PENDING"           # Still in progress
    PASSED = "PASSED"             # All gates passed
    FAILED_GATE1 = "FAILED_GATE1" # Failed deterministic validation
    FAILED_GATE2 = "FAILED_GATE2" # Failed AI validation (if required)
    FAILED_GATE3 = "FAILED_GATE3" # Human rejected
    AWAITING_HUMAN = "AWAITING_HUMAN"  # Waiting for human approval


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class PipelineContext:
    """Context passed through pipeline stages."""
    decision_id: str
    decision_code: str
    decision_record: Dict[str, Any]
    impact_level: str = "IMPORTANT"
    submitted_by: str = ""

    # Stage results
    gate1_result: Optional[Gate1Result] = None
    gate2_result: Optional[Gate2AIResult] = None
    gate3_result: Optional[Gate3Result] = None

    # Approval tracking
    approval_request: Optional[ApprovalRequest] = None


@dataclass
class PipelineResult:
    """Complete result of pipeline execution."""
    outcome: PipelineOutcome
    stage: PipelineStage
    decision_id: str
    decision_code: str

    # Gate results
    gate1: Optional[Gate1Result] = None
    gate2: Optional[Gate2AIResult] = None
    gate3: Optional[Gate3Result] = None

    # Approval
    approval_request_id: Optional[str] = None

    # Timing
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    total_time_ms: float = 0.0

    # Messages
    messages: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Pipeline is complete (passed or failed)."""
        return self.outcome in [
            PipelineOutcome.PASSED,
            PipelineOutcome.FAILED_GATE1,
            PipelineOutcome.FAILED_GATE2,
            PipelineOutcome.FAILED_GATE3,
        ]

    @property
    def can_activate(self) -> bool:
        """Decision can be activated."""
        return self.outcome == PipelineOutcome.PASSED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "stage": self.stage.value,
            "decision_id": self.decision_id,
            "decision_code": self.decision_code,
            "gate1": self.gate1.to_dict() if self.gate1 else None,
            "gate2": self.gate2.to_dict() if self.gate2 else None,
            "gate3": self.gate3.to_dict() if self.gate3 else None,
            "approval_request_id": self.approval_request_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_time_ms": round(self.total_time_ms, 2),
            "messages": self.messages,
            "is_complete": self.is_complete,
            "can_activate": self.can_activate,
        }


# ============================================================================
# VALIDATION PIPELINE
# ============================================================================

class ValidationPipeline:
    """
    3-Gate Validation Pipeline.

    Orchestrates Gate 1, Gate 2, and Gate 3 validation.
    """

    def __init__(
        self,
        gate1_validator: Optional[Gate1Validator] = None,
        gate2_validator: Optional[Gate2AIValidator] = None,
        approval_manager: Optional[HumanApprovalManager] = None,
        existing_decisions: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize pipeline.

        Args:
            gate1_validator: Gate 1 validator (or create default)
            gate2_validator: Gate 2 validator (or create default)
            approval_manager: Human approval manager (or create default)
            existing_decisions: Existing decisions for conflict/duplicate check
        """
        self.gate1 = gate1_validator or Gate1Validator()
        self.gate2 = gate2_validator or create_gate2_validator(
            existing_decisions=existing_decisions or []
        )
        self.approval_manager = approval_manager or create_approval_manager()
        self.gate3 = Gate3Validator(self.approval_manager)

        # Pipeline state
        self._contexts: Dict[str, PipelineContext] = {}
        self._results: Dict[str, PipelineResult] = {}

    def validate(
        self,
        record: Dict[str, Any],
        submitted_by: str,
        auto_create_approval: bool = True,
    ) -> PipelineResult:
        """
        Run validation pipeline for a decision.

        This runs Gates 1 and 2 synchronously.
        Gate 3 (human approval) is asynchronous by nature.

        Args:
            record: Decision record
            submitted_by: Human who submitted
            auto_create_approval: Auto-create approval request if Gates 1&2 pass

        Returns:
            PipelineResult with current status
        """
        start_time = datetime.now(timezone.utc)

        decision_id = record.get("decision_id", "")
        decision_code = record.get("code") or record.get("decision_code", "")
        impact_level = record.get("impact", "IMPORTANT")
        if hasattr(impact_level, 'value'):
            impact_level = impact_level.value

        # Validate submitter is human
        if submitted_by.lower().startswith("ai:"):
            return PipelineResult(
                outcome=PipelineOutcome.FAILED_GATE1,
                stage=PipelineStage.GATE1_FAILED,
                decision_id=decision_id,
                decision_code=decision_code,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                messages=["AI cannot submit decisions per LAW §6"],
            )

        # Create context
        context = PipelineContext(
            decision_id=decision_id,
            decision_code=decision_code,
            decision_record=record,
            impact_level=impact_level,
            submitted_by=submitted_by,
        )

        messages = []

        # =====================================================================
        # GATE 1: DETERMINISTIC VALIDATION
        # =====================================================================

        messages.append("Starting Gate 1: Deterministic Validation")
        gate1_result = self.gate1.validate(record)
        context.gate1_result = gate1_result

        if gate1_result.status == Gate1Status.FAIL:
            # Gate 1 is HARD block - stop here
            end_time = datetime.now(timezone.utc)
            messages.append(f"Gate 1 FAILED: {len(gate1_result.violations)} violations")

            result = PipelineResult(
                outcome=PipelineOutcome.FAILED_GATE1,
                stage=PipelineStage.GATE1_FAILED,
                decision_id=decision_id,
                decision_code=decision_code,
                gate1=gate1_result,
                started_at=start_time,
                completed_at=end_time,
                total_time_ms=(end_time - start_time).total_seconds() * 1000,
                messages=messages,
            )
            self._results[decision_id] = result
            return result

        messages.append(f"Gate 1 PASSED: {gate1_result.rules_passed}/{gate1_result.rules_checked} rules")
        if gate1_result.warnings:
            messages.append(f"Gate 1 warnings: {len(gate1_result.warnings)}")

        # =====================================================================
        # GATE 2: AI HEURISTIC VALIDATION
        # =====================================================================

        messages.append("Starting Gate 2: AI Heuristic Validation")
        gate2_result = self.gate2.validate(record)
        context.gate2_result = gate2_result

        # Gate 2 is SOFT - always continue, but record warnings
        if gate2_result.passed:
            messages.append(f"Gate 2 PASSED: Quality score {gate2_result.quality_score.overall:.2f}")
        else:
            messages.append(f"Gate 2 WARNINGS: {len(gate2_result.quality_score.issues)} issues")

        if gate2_result.conflicts:
            messages.append(f"Gate 2 detected {len(gate2_result.conflicts)} potential conflicts")

        if gate2_result.duplicates:
            messages.append(f"Gate 2 detected {len(gate2_result.duplicates)} potential duplicates")

        # =====================================================================
        # CREATE APPROVAL REQUEST (GATE 3 PREP)
        # =====================================================================

        if auto_create_approval:
            messages.append("Creating approval request for Gate 3")

            approval_request = self.approval_manager.create_request(
                decision_id=decision_id,
                decision_code=decision_code,
                submitted_by=submitted_by,
                impact_level=impact_level,
                gate1_passed=True,
                gate2_passed=gate2_result.passed,
                gate1_warnings=len(gate1_result.warnings),
                gate2_warnings=len(gate2_result.quality_score.issues),
            )
            context.approval_request = approval_request
            messages.append(f"Approval request created: {approval_request.request_id}")

        # Store context
        self._contexts[decision_id] = context

        # Build result - awaiting human approval
        end_time = datetime.now(timezone.utc)

        result = PipelineResult(
            outcome=PipelineOutcome.AWAITING_HUMAN,
            stage=PipelineStage.AWAITING_APPROVAL,
            decision_id=decision_id,
            decision_code=decision_code,
            gate1=gate1_result,
            gate2=gate2_result,
            approval_request_id=approval_request.request_id if auto_create_approval else None,
            started_at=start_time,
            completed_at=end_time,
            total_time_ms=(end_time - start_time).total_seconds() * 1000,
            messages=messages,
        )

        self._results[decision_id] = result
        return result

    def check_approval_status(self, decision_id: str) -> PipelineResult:
        """
        Check current approval status for a decision.

        Args:
            decision_id: The decision to check

        Returns:
            Updated PipelineResult
        """
        if decision_id not in self._results:
            return PipelineResult(
                outcome=PipelineOutcome.PENDING,
                stage=PipelineStage.NOT_STARTED,
                decision_id=decision_id,
                decision_code="",
                messages=["Decision not found in pipeline"],
            )

        result = self._results[decision_id]

        # If already complete, return as-is
        if result.is_complete:
            return result

        # Check Gate 3
        gate3_result = self.gate3.validate(decision_id)

        if gate3_result.can_activate:
            # Human approved!
            result.outcome = PipelineOutcome.PASSED
            result.stage = PipelineStage.APPROVED
            result.gate3 = gate3_result
            result.completed_at = datetime.now(timezone.utc)
            result.messages.append(f"Gate 3 PASSED: Approved by {gate3_result.approved_by}")

        elif gate3_result.status == ApprovalStatus.REJECTED:
            # Human rejected
            result.outcome = PipelineOutcome.FAILED_GATE3
            result.stage = PipelineStage.REJECTED
            result.gate3 = gate3_result
            result.completed_at = datetime.now(timezone.utc)
            result.messages.append("Gate 3 FAILED: Human rejected")

        else:
            # Still waiting
            result.messages.append(f"Gate 3 status: {gate3_result.status.value}")

        return result

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all decisions awaiting human approval."""
        pending = []
        for decision_id, result in self._results.items():
            if result.outcome == PipelineOutcome.AWAITING_HUMAN:
                context = self._contexts.get(decision_id)
                pending.append({
                    "decision_id": decision_id,
                    "decision_code": result.decision_code,
                    "approval_request_id": result.approval_request_id,
                    "gate1_warnings": len(result.gate1.warnings) if result.gate1 else 0,
                    "gate2_warnings": len(result.gate2.quality_score.issues) if result.gate2 else 0,
                    "gate2_quality_score": result.gate2.quality_score.overall if result.gate2 else None,
                    "impact_level": context.impact_level if context else "IMPORTANT",
                    "submitted_by": context.submitted_by if context else "",
                    "submitted_at": result.started_at.isoformat(),
                })
        return pending

    def get_summary(self) -> Dict[str, Any]:
        """Get pipeline summary statistics."""
        total = len(self._results)
        passed = sum(1 for r in self._results.values() if r.outcome == PipelineOutcome.PASSED)
        failed_g1 = sum(1 for r in self._results.values() if r.outcome == PipelineOutcome.FAILED_GATE1)
        failed_g3 = sum(1 for r in self._results.values() if r.outcome == PipelineOutcome.FAILED_GATE3)
        awaiting = sum(1 for r in self._results.values() if r.outcome == PipelineOutcome.AWAITING_HUMAN)

        return {
            "total_processed": total,
            "passed": passed,
            "failed_gate1": failed_g1,
            "failed_gate3": failed_g3,
            "awaiting_approval": awaiting,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_pipeline(
    existing_decisions: Optional[List[Dict[str, Any]]] = None,
) -> ValidationPipeline:
    """
    Create a new validation pipeline.

    Args:
        existing_decisions: Existing decisions for conflict/duplicate detection

    Returns:
        Configured ValidationPipeline
    """
    return ValidationPipeline(existing_decisions=existing_decisions)


def validate_decision_full(
    record: Dict[str, Any],
    submitted_by: str,
    existing_decisions: Optional[List[Dict[str, Any]]] = None,
) -> PipelineResult:
    """
    Validate a decision through the full 3-gate pipeline.

    Args:
        record: Decision record
        submitted_by: Human submitter
        existing_decisions: Existing decisions for context

    Returns:
        PipelineResult with status
    """
    pipeline = create_pipeline(existing_decisions)
    return pipeline.validate(record, submitted_by)


__all__ = [
    # Enums
    "PipelineStage",
    "PipelineOutcome",
    # Data structures
    "PipelineContext",
    "PipelineResult",
    # Pipeline
    "ValidationPipeline",
    # Functions
    "create_pipeline",
    "validate_decision_full",
]
