"""
MANTRA Validation Module

Three-Gate Validation System per MANTRA-LAW-001 AMENDMENT-004:

┌─────────────────────────────────────────────────────────────────┐
│  GATE 1: DETERMINISTIC (HARD BLOCK)                             │
│  - Schema validation (S-001 to S-022)                           │
│  - Consistency checks (D-001 to D-014)                          │
│  - Pure rule-based, no AI involvement                           │
│  - PASS → Continue | FAIL → REJECT                              │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  GATE 2: AI HEURISTIC (SOFT WARN)                               │
│  - Quality scoring                                              │
│  - Conflict detection                                           │
│  - Duplicate detection                                          │
│  - PASS → Continue | WARN → Continue with warnings              │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  GATE 3: HUMAN APPROVAL (HARD BLOCK)                            │
│  - Human reviews Gate 1 & 2 results                             │
│  - Human approves/rejects/requests changes                      │
│  - AI has ZERO authority per LAW §6                             │
│  - APPROVED → ACTIVE | NOT APPROVED → PENDING                   │
└─────────────────────────────────────────────────────────────────┘

USAGE:
    from core.validation import validate_decision_full, create_pipeline

    # Quick validation (Gates 1 & 2 + approval request)
    result = validate_decision_full(record, submitted_by="john@example.com")

    if result.outcome == PipelineOutcome.AWAITING_HUMAN:
        print(f"Awaiting approval: {result.approval_request_id}")

    # Full pipeline control
    pipeline = create_pipeline(existing_decisions=existing)
    result = pipeline.validate(record, "john@example.com")

    # Check approval status later
    result = pipeline.check_approval_status(decision_id)
"""

# Gate 1: Deterministic Validation
from .gate1_deterministic import (
    Gate1Status,
    RuleCategory,
    RuleSeverity,
    RuleViolation,
    Gate1Result,
    Gate1Validator,
    validate_gate1,
)

# Gate 2: AI Heuristic Validation
from .gate2_ai_validator import (
    QualityDimension,
    QualityScore,
    ConflictReport,
    Gate2AIResult,
    Gate2AIValidator,
    create_gate2_validator,
)

# Gate 3: Human Approval
from .gate3_human_approval import (
    ApprovalStatus,
    ReviewerRole,
    RejectionReason,
    ReviewComment,
    ApprovalRequest,
    ApprovalResult,
    ApprovalPolicy,
    Gate3Result,
    HumanApprovalManager,
    Gate3Validator,
    DEFAULT_POLICIES,
    create_approval_manager,
    validate_gate3,
)

# Pipeline: Orchestrates all 3 gates
from .pipeline import (
    PipelineStage,
    PipelineOutcome,
    PipelineContext,
    PipelineResult,
    ValidationPipeline,
    create_pipeline,
    validate_decision_full,
)

# Dependency Validation (graph integrity)
from .dependency_validator import (
    DependencyError,
    CyclicDependencyError,
    SelfReferenceError,
    MissingReferenceError,
    ExcessiveDepthError,
    ValidationSeverity,
    DependencyIssue,
    DependencyValidationResult,
    DependencyValidator,
    validate_dependencies,
)

__all__ = [
    # =========================================================================
    # Gate 1: Deterministic
    # =========================================================================
    "Gate1Status",
    "RuleCategory",
    "RuleSeverity",
    "RuleViolation",
    "Gate1Result",
    "Gate1Validator",
    "validate_gate1",

    # =========================================================================
    # Gate 2: AI Heuristic
    # =========================================================================
    "QualityDimension",
    "QualityScore",
    "ConflictReport",
    "Gate2AIResult",
    "Gate2AIValidator",
    "create_gate2_validator",

    # =========================================================================
    # Gate 3: Human Approval
    # =========================================================================
    "ApprovalStatus",
    "ReviewerRole",
    "RejectionReason",
    "ReviewComment",
    "ApprovalRequest",
    "ApprovalResult",
    "ApprovalPolicy",
    "Gate3Result",
    "HumanApprovalManager",
    "Gate3Validator",
    "DEFAULT_POLICIES",
    "create_approval_manager",
    "validate_gate3",

    # =========================================================================
    # Pipeline: Full 3-Gate Orchestration
    # =========================================================================
    "PipelineStage",
    "PipelineOutcome",
    "PipelineContext",
    "PipelineResult",
    "ValidationPipeline",
    "create_pipeline",
    "validate_decision_full",

    # =========================================================================
    # Dependency Validation
    # =========================================================================
    "DependencyError",
    "CyclicDependencyError",
    "SelfReferenceError",
    "MissingReferenceError",
    "ExcessiveDepthError",
    "ValidationSeverity",
    "DependencyIssue",
    "DependencyValidationResult",
    "DependencyValidator",
    "validate_dependencies",
]
