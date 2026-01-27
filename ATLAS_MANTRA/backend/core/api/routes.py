"""
API Routes

Implements the HTTP endpoints for ATLAS_MANTRA services:
- Validator Service (POST /validate)
- Decision Store (POST /decisions)
- Public Read API (GET /decisions)

Per MANTRA-L2-IMPL-INTEGRATION-BOUNDARIES-001:
- All external clients have ZERO authority
- AI clients are treated as external
- All responses are authoritative from the system only
"""

import time
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.schema import (
    Decision,
    DecisionCreate,
    GroupId,
    FeatureId,
    AuthorshipMetadata,
)
from ..use_cases.validate_decision import (
    validate_decision,
    ValidationResult,
    ValidationStatus,
    validate_related_decisions_integrity_async,
    RelationshipValidationResult,
)
from ..use_cases.enhanced_validation import (
    validate_enhanced_async,
    EnhancedValidationResponse,
    EnhancedValidationStatus,
    serialize_enhanced_response,
)
from ..use_cases.impact_analysis import (
    analyze_impact_async,
    serialize_impact_result,
    ImpactLevel,
)
from ..use_cases.store_decision import store_decision, store_decision_async, StoreResult
from ..use_cases.read_decision import (
    get_decision,
    list_decisions,
    group_decisions_by_group_feature,
    ReadResult,
)
from ..use_cases.propose_decision import (
    propose_decision,
    ProposeResult,
    ProposeDecisionResult,
)
# ProposeResult imported for relationship validation override
from ..use_cases.compare_decisions import (
    compare_decisions,
    get_decision_history,
    CompareResult,
    DecisionComparison,
    VersionChainResult,
)
from ..use_cases.audit_log import (
    list_audit_entries,
    record_audit,
    AuditResult,
    ListAuditResult,
)
from ..domain.decision import AuditEventType, ChallengeMetadata
from ..repositories.decision_repository import DecisionRepository, InMemoryDecisionRepository
from ..runtime.config import get_config


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["decisions"])

# Dependency injection for repository
_repository: Optional[DecisionRepository] = None
_repository_initialized: bool = False


def get_repository() -> DecisionRepository:
    """Get repository instance (singleton)."""
    global _repository
    if _repository is None:
        # Fallback to in-memory if not set
        # Production should call set_repository() with PostgresDecisionRepository
        _repository = InMemoryDecisionRepository()
    return _repository


def set_repository(repo: DecisionRepository) -> None:
    """Set repository instance (for testing/production switch)."""
    global _repository, _repository_initialized
    _repository = repo
    _repository_initialized = True


async def initialize_repository() -> None:
    """Initialize the repository (call on app startup)."""
    global _repository, _repository_initialized

    if _repository_initialized:
        return

    config = get_config()

    if config.database_url:
        try:
            from adapters.repositories.postgres_decision_repository import PostgresDecisionRepository
            repo = PostgresDecisionRepository(config.database_url)
            await repo.initialize()
            _repository = repo
            _repository_initialized = True
            print(f"  - Repository: PostgreSQL")
        except Exception as e:
            print(f"  - Repository: PostgreSQL FAILED ({e}), using InMemory")
            _repository = InMemoryDecisionRepository()
            _repository_initialized = True
    else:
        print(f"  - Repository: InMemory (no DATABASE_URL)")
        _repository = InMemoryDecisionRepository()
        _repository_initialized = True


# ============================================================================
# Request/Response Models
# ============================================================================

class ValidateRequest(BaseModel):
    """Request body for validation endpoint."""
    record: Dict[str, Any] = Field(..., description="Decision record to validate")
    authorship_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional authorship metadata for L-001 through L-008 rules"
    )


class ValidateResponse(BaseModel):
    """Response body for validation endpoint."""
    status: str
    violations: List[Dict[str, Any]]
    skipped_rules: List[str]
    advisory_notes: List[str]
    validated_at: datetime
    schema_version: str
    specification_version: str


class StoreRequest(BaseModel):
    """Request body for store endpoint."""
    decision: DecisionCreate
    stored_by: str = Field(..., description="Human identifier storing the decision")
    decision_id: Optional[str] = Field(
        None,
        description="Optional decision_id from propose. If provided, preserves ID continuity."
    )


class StoreResponse(BaseModel):
    """Response body for store endpoint."""
    result: str
    decision_id: Optional[str] = None
    stored_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DecisionResponse(BaseModel):
    """Response body for single decision.

    Per MANTRA-SPEC-001-AMENDMENT-001:
    - NO status field (lifecycle is NOT encoded in domain)
    - Evolution expressed via version + supersedes only

    UX Enhancement (Phase 5):
    - decision_code provides human-readable identifier
    - Format: {group}-{feature}-{seq}-v{version}
    """
    decision_id: str
    decision_code: Optional[str] = None
    group_id: str
    feature_id: str
    statement: str
    rationale: str
    constraints: List[Dict[str, Any]]
    invariants: List[str]
    scope: str
    blast_radius: str
    version: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    supersedes: Optional[str] = None
    related_decisions: List[str] = []
    # Projection fields
    tags: List[str] = []
    tech_stack: List[str] = []


class ListDecisionsResponse(BaseModel):
    """Response body for list decisions."""
    decisions: List[DecisionResponse]
    total_count: int
    limit: int
    offset: int


class GroupedDecisionsResponse(BaseModel):
    """Response body for grouped decisions - PURE DATA ACCESS."""
    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]]
    generated_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: datetime


# ============================================================================
# Command-Style API Request/Response Models
# ============================================================================

class ProposeRequest(BaseModel):
    """Request body for propose endpoint."""
    decision: DecisionCreate
    proposed_by: str = Field(..., description="Human identifier proposing the decision")
    authorship_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional authorship metadata for L-rules validation"
    )


class ProposeResponse(BaseModel):
    """Response body for propose endpoint."""
    result: str  # READY or INVALID
    proposal_id: str
    decision_id: str
    decision: Optional[Dict[str, Any]] = None
    validation_status: str
    violations: List[Dict[str, Any]] = []
    advisory_notes: List[str] = []
    warnings: List[str] = []  # Explicit warnings (e.g., invalid authorship_metadata)
    skipped_rules: List[str] = []  # Rules skipped due to missing metadata
    proposed_at: datetime


class ChallengeRequest(BaseModel):
    """Request body for challenge endpoint."""
    challenger: str = Field(..., description="Human identifier challenging the decision")
    challenge_rationale: str = Field(..., description="Reason for challenging")
    proposed_replacement: DecisionCreate = Field(..., description="New decision to supersede")


class ChallengeResponse(BaseModel):
    """Response body for challenge endpoint."""
    result: str  # STORED or error
    challenged_decision_id: str
    new_decision_id: Optional[str] = None
    stored_at: Optional[datetime] = None
    error_message: Optional[str] = None


class CompareResponse(BaseModel):
    """Response body for compare endpoint."""
    result: str  # COMPARABLE, NOT_FOUND_A, NOT_FOUND_B, NOT_FOUND_BOTH
    decision_a: Optional[Dict[str, Any]] = None
    decision_b: Optional[Dict[str, Any]] = None
    differences: List[Dict[str, Any]] = []
    is_supersedes_chain: bool = False
    supersedes_direction: Optional[str] = None
    common_group: bool = False
    common_feature: bool = False
    error_message: Optional[str] = None


class HistoryResponse(BaseModel):
    """Response body for history endpoint."""
    result: str
    decision_id: str
    chain: List[Dict[str, Any]] = []
    total_versions: int = 0
    error_message: Optional[str] = None


class AuditEntryResponse(BaseModel):
    """Single audit entry response."""
    event_id: str
    event_type: str
    actor: str
    actor_type: str
    decision_id: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class AuditListResponse(BaseModel):
    """Response body for audit list endpoint."""
    result: str
    entries: List[AuditEntryResponse] = []
    total_count: int = 0
    limit: int = 100
    offset: int = 0
    error_message: Optional[str] = None


class RelationshipViolationResponse(BaseModel):
    """Single relationship violation."""
    rule_id: str
    message: str
    is_error: bool
    related_id: Optional[str] = None
    source_group: Optional[str] = None
    target_group: Optional[str] = None


class RelationshipValidationResponse(BaseModel):
    """Response for relationship validation endpoint."""
    is_valid: bool
    violations: List[RelationshipViolationResponse] = []
    advisory_notes: List[str] = []
    cross_group_references: List[Dict[str, str]] = []


class ArbitrationVerdictInput(BaseModel):
    """Client AI's verdict for delegated arbitration."""
    arbitration_type: str = Field(..., description="QUALITY, DUPLICATE, or CONFLICT")
    verdict: str = Field(..., description="The AI's judgment (e.g., APPROVE, REJECT)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence 0.0-1.0")
    reason: str = Field(..., description="Brief explanation")
    suggestions: Optional[List[str]] = Field(None, description="Optional suggestions")


# ============================================================================
# User Approval Flow Models
# ============================================================================

class ApproveRequest(BaseModel):
    """Request body for decision approval endpoint."""
    proposal_id: str = Field(..., description="The proposal_id from validate/enhanced response")
    approved_by: str = Field(..., description="Human identifier approving the decision")
    acknowledgments: Optional[List[str]] = Field(
        None,
        description="Optional list of acknowledged warnings (required if decision has warnings)"
    )


class ApproveResponse(BaseModel):
    """Response body for decision approval endpoint."""
    result: str  # STORED, BLOCKED, NOT_FOUND, ERROR
    decision_id: Optional[str] = None
    decision_code: Optional[str] = None
    stored_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ============================================================================
# Proposal Storage (In-Memory for now - tracks pending approvals)
# ============================================================================

from dataclasses import dataclass, field as dc_field
from typing import Dict as TypingDict

@dataclass
class PendingProposal:
    """Tracks a validated proposal awaiting user approval."""
    proposal_id: str
    decision_id: str
    record: Dict[str, Any]
    validation_result: str  # READY, INVALID, BLOCKED
    can_store: bool
    requires_acknowledgment: bool
    warnings: List[str]
    validated_at: datetime
    expires_at: float  # Unix timestamp for expiration (30 min default)

# In-memory proposal storage (replace with Redis/PostgreSQL in production)
_pending_proposals: TypingDict[str, PendingProposal] = {}


class ArbitrationModeInput(str, Enum):
    """Arbitration mode for validation."""
    SERVER = "SERVER"       # MANTRA's AI does arbitration (costs $)
    DELEGATED = "DELEGATED" # Client AI does arbitration (returns context)
    SKIP = "SKIP"           # No AI arbitration


class EnhancedValidateRequest(BaseModel):
    """Request body for enhanced validation endpoint."""
    record: Dict[str, Any] = Field(..., description="Decision record to validate")
    authorship_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional authorship metadata for L-rules"
    )
    # AI Arbitration configuration
    arbitration_mode: ArbitrationModeInput = Field(
        ArbitrationModeInput.DELEGATED,
        description="DELEGATED=returns context for client AI, SERVER=MANTRA's AI arbitrates, SKIP=no AI"
    )
    # Delegated arbitration: Client AI can submit verdicts
    arbitration_verdicts: Optional[List[ArbitrationVerdictInput]] = Field(
        None,
        description="Client AI's verdicts for delegated arbitration. Submit after receiving arbitration_contexts."
    )


class EnhancedValidateResponse(BaseModel):
    """Response body for enhanced validation endpoint."""
    result: str  # READY, INVALID, or BLOCKED
    proposal_id: str
    decision_id: str

    # Quality assessment
    quality: Dict[str, Any]

    # Consistency assessment
    duplicates: Dict[str, Any]
    conflicts: Dict[str, Any]

    # Impact analysis
    impact: Dict[str, Any]

    # Violations and feedback
    violations: List[Dict[str, Any]]
    warnings: List[str]
    advisory_notes: List[str]
    skipped_rules: List[str]

    # Status
    validated_at: datetime
    can_store: bool
    requires_acknowledgment: bool
    blocking_reasons: List[str]

    # AI Arbiter (Phase 9) - Delegated arbitration for borderline cases
    arbitration_required: bool = False
    arbitration_contexts: Optional[List[Dict[str, Any]]] = None
    ai_verdicts: Optional[Dict[str, Any]] = None

    # Metadata Inference (Phase 7) - Auto-suggested metadata
    metadata_suggestions: Optional[Dict[str, Any]] = None

    # User Approval Flow - User must explicitly approve before storing
    requires_user_approval: bool = True  # Always true - user must approve
    approval_summary: Optional[Dict[str, Any]] = None  # Summary for user review


# ============================================================================
# Helper Functions
# ============================================================================

def serialize_constraint(constraint) -> Dict[str, Any]:
    """
    Serialize a Constraint to consistent dict format.

    Ensures constraint.type is always serialized as string value,
    fixing inconsistency between endpoints.

    Args:
        constraint: Constraint object (may be Pydantic model or dict)

    Returns:
        Dict with consistent format: {"constraint_id": str, "statement": str, "type": str}
    """
    if hasattr(constraint, 'model_dump'):
        # Pydantic model
        c_dict = constraint.model_dump()
        # Ensure type is string value, not enum
        if hasattr(c_dict.get('type'), 'value'):
            c_dict['type'] = c_dict['type'].value
        elif hasattr(constraint.type, 'value'):
            c_dict['type'] = constraint.type.value
        return c_dict
    elif isinstance(constraint, dict):
        # Already a dict
        c_type = constraint.get('type')
        if hasattr(c_type, 'value'):
            constraint['type'] = c_type.value
        return constraint
    else:
        # Fallback
        return {
            "constraint_id": getattr(constraint, 'constraint_id', ''),
            "statement": getattr(constraint, 'statement', ''),
            "type": getattr(constraint.type, 'value', str(constraint.type)) if hasattr(constraint, 'type') else ''
        }


# ============================================================================
# Validator Service Endpoint
# ============================================================================

@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate a decision record",
    description="""
    Validates a decision record against MANTRA-SCHEMA-001 and MANTRA-SPEC-001.

    Per MANTRA-L1-IMPL-VALIDATOR-001, the validator:
    - Applies 47 validation rules across 3 levels
    - Produces VALID, INVALID, or REJECTED status
    - Has NO authority to modify or approve decisions

    When authorship_metadata is not provided, rules L-001 through L-008
    are skipped per MANTRA-SPEC-001 §4.3.2.
    """
)
async def validate_endpoint(request: ValidateRequest) -> ValidateResponse:
    """Validate a decision record."""
    # Parse authorship metadata if provided (with explicit handling)
    authorship = None
    additional_advisory_notes = []

    if request.authorship_metadata:
        try:
            authorship = AuthorshipMetadata(**request.authorship_metadata)
        except Exception as e:
            # Note the parsing failure in advisory notes
            additional_advisory_notes.append(
                f"Warning: authorship_metadata parsing failed ({str(e)}). "
                "L-rules (L-001 through L-008) were skipped."
            )

    # Perform validation
    result = validate_decision(request.record, authorship)

    return ValidateResponse(
        status=result.status.value,
        violations=[
            {
                "rule_id": v.rule_id,
                "level": v.level.value,
                "message": v.message,
                "field": v.field,
                "failure_result": v.failure_result.value,
                "governing_reference": v.governing_reference,
            }
            for v in result.violations
        ],
        skipped_rules=result.skipped_rules,
        advisory_notes=result.advisory_notes + additional_advisory_notes,
        validated_at=result.validated_at,
        schema_version=result.schema_version,
        specification_version=result.specification_version,
    )


@router.post(
    "/validate/enhanced",
    response_model=EnhancedValidateResponse,
    summary="Enhanced validation with quality, duplicate, conflict, and impact analysis",
    description="""
    Comprehensive 6-phase validation:

    1. Schema Validation (S-001 to S-022)
    2. Quality Scoring (Q-001 to Q-025)
       - Statement quality (0-25)
       - Rationale quality (0-25)
       - Constraint quality (0-25)
       - Metadata quality (0-25)
       - Advanced: Readability, Coherence (SBERT), Objectivity
       - Grade: EXCELLENT/GOOD/FAIR/POOR/REJECT

    3. Duplicate Detection
       - EXACT (100%): Block storage
       - NEAR (85-99%): Require acknowledgment
       - SEMANTIC (70-84%): Warning
       - RELATED (50-69%): Suggest relation

    4. Conflict Detection
       - Technology conflicts (postgresql vs mongodb)
       - Architecture conflicts (microservice vs monolith)
       - Direct contradictions (must X vs must not X)

    5. Law Compliance (L-001 to L-011)

    6. Impact Analysis
       - Dependency chain analysis
       - Breaking change detection
       - Risk scoring (0-100)
       - Risk level: MINIMAL/LOW/MODERATE/HIGH/CRITICAL

    Returns:
    - READY: Can be stored
    - INVALID: Has issues, can store with acknowledgment
    - BLOCKED: Cannot be stored
    """
)
async def validate_enhanced_endpoint(
    request: EnhancedValidateRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> EnhancedValidateResponse:
    """Enhanced validation with quality, duplicate, and conflict detection."""
    # Parse authorship metadata if provided
    authorship = None
    if request.authorship_metadata:
        try:
            authorship = AuthorshipMetadata(**request.authorship_metadata)
        except Exception:
            pass  # Will be handled in validation

    # Parse client AI verdicts if provided (delegated arbitration)
    client_verdicts = None
    if request.arbitration_verdicts:
        client_verdicts = [
            {
                'arbitration_type': v.arbitration_type,
                'verdict': v.verdict,
                'confidence': v.confidence,
                'reason': v.reason,
                'suggestions': v.suggestions or [],
            }
            for v in request.arbitration_verdicts
        ]

    # Run enhanced validation
    result = await validate_enhanced_async(
        record=request.record,
        repository=repository,
        authorship_metadata=authorship,
        client_verdicts=client_verdicts,
        arbitration_mode=request.arbitration_mode.value,  # SERVER, DELEGATED, or SKIP
    )

    # Serialize to response
    serialized = serialize_enhanced_response(result)

    # =========================================================================
    # USER APPROVAL FLOW: Store proposal for later approval
    # =========================================================================
    # Clean up expired proposals first
    _cleanup_expired_proposals()

    # Store the proposal (30 minute expiration)
    proposal = PendingProposal(
        proposal_id=serialized['proposal_id'],
        decision_id=serialized['decision_id'],
        record=request.record,
        validation_result=serialized['result'],
        can_store=serialized['can_store'],
        requires_acknowledgment=serialized['requires_acknowledgment'],
        warnings=serialized['warnings'],
        validated_at=result.validated_at,
        expires_at=time.time() + (30 * 60),  # 30 minutes
    )
    _pending_proposals[serialized['proposal_id']] = proposal

    return EnhancedValidateResponse(
        result=serialized['result'],
        proposal_id=serialized['proposal_id'],
        decision_id=serialized['decision_id'],
        quality=serialized['quality'],
        duplicates=serialized['duplicates'],
        conflicts=serialized['conflicts'],
        impact=serialized['impact'],
        violations=serialized['violations'],
        warnings=serialized['warnings'],
        advisory_notes=serialized['advisory_notes'],
        skipped_rules=serialized['skipped_rules'],
        validated_at=result.validated_at,
        can_store=serialized['can_store'],
        requires_acknowledgment=serialized['requires_acknowledgment'],
        blocking_reasons=serialized['blocking_reasons'],
        # AI Arbiter fields
        arbitration_required=serialized.get('arbitration_required', False),
        arbitration_contexts=serialized.get('arbitration_contexts'),
        ai_verdicts=serialized.get('ai_verdicts'),
        # Metadata inference
        metadata_suggestions=serialized.get('metadata_suggestions'),
        # User Approval Flow
        requires_user_approval=True,
        approval_summary=serialized.get('approval_summary'),
    )


def _cleanup_expired_proposals():
    """Remove expired proposals from storage."""
    now = time.time()
    expired = [k for k, v in _pending_proposals.items() if v.expires_at < now]
    for k in expired:
        del _pending_proposals[k]


@router.post(
    "/validate/relationships",
    response_model=RelationshipValidationResponse,
    summary="Validate related_decisions integrity",
    description="""
    Validates referential integrity for related_decisions field.

    Rules checked:
    - D-015: All IDs in related_decisions MUST exist
    - D-016: No circular reference (self or chain)
    - D-017: Cross-group references generate advisory note (not error)

    Use this to check relationships before storing a decision.
    """
)
async def validate_relationships_endpoint(
    request: ValidateRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> RelationshipValidationResponse:
    """Validate related_decisions referential integrity."""
    result = await validate_related_decisions_integrity_async(
        record=request.record,
        repository=repository
    )

    return RelationshipValidationResponse(
        is_valid=result.is_valid,
        violations=[
            RelationshipViolationResponse(
                rule_id=v.rule_id,
                message=v.message,
                is_error=v.is_error,
                related_id=v.related_id,
                source_group=v.source_group,
                target_group=v.target_group,
            )
            for v in result.violations
        ],
        advisory_notes=result.advisory_notes,
        cross_group_references=result.cross_group_references,
    )


class ImpactAnalysisResponse(BaseModel):
    """Response body for impact analysis endpoint."""
    overall_risk: str  # MINIMAL, LOW, MODERATE, HIGH, CRITICAL
    risk_score: int  # 0-100
    affected_decisions: List[Dict[str, Any]]
    affected_count: int
    dependency_chains: List[Dict[str, Any]]
    reverse_dependencies: List[Dict[str, Any]]
    max_dependency_depth: int
    breaking_changes: List[Dict[str, Any]]
    has_breaking_changes: bool
    affected_areas: List[str]
    affected_tech_stack: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    summary: str


@router.post(
    "/validate/impact",
    response_model=ImpactAnalysisResponse,
    summary="Analyze impact of a proposed decision",
    description="""
    Comprehensive impact analysis for a proposed decision:

    1. **Dependency Analysis**
       - Finds decisions that depend on this decision
       - Traces dependency chains up to 5 levels deep
       - Detects circular dependencies

    2. **Reverse Dependencies**
       - Identifies what this decision depends on

    3. **Breaking Change Detection**
       - If superseding, identifies affected dependents
       - Calculates risk level for breaking changes

    4. **Area/Tech Impact**
       - Tags (FE, BE, DB, INFRA, etc.)
       - Tech stack overlap

    5. **Risk Scoring**
       - Score: 0-100
       - Level: MINIMAL, LOW, MODERATE, HIGH, CRITICAL
       - Based on: blast_radius, scope, dependencies, breaking changes

    Use this before storing a decision to understand its system-wide impact.
    """
)
async def validate_impact_endpoint(
    request: ValidateRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> ImpactAnalysisResponse:
    """Analyze impact of a proposed decision."""
    result = await analyze_impact_async(
        record=request.record,
        repository=repository
    )

    serialized = serialize_impact_result(result)

    return ImpactAnalysisResponse(
        overall_risk=serialized['overall_risk'],
        risk_score=serialized['risk_score'],
        affected_decisions=serialized['affected_decisions'],
        affected_count=serialized['affected_count'],
        dependency_chains=serialized['dependency_chains'],
        reverse_dependencies=serialized['reverse_dependencies'],
        max_dependency_depth=serialized['max_dependency_depth'],
        breaking_changes=serialized['breaking_changes'],
        has_breaking_changes=serialized['has_breaking_changes'],
        affected_areas=serialized['affected_areas'],
        affected_tech_stack=serialized['affected_tech_stack'],
        risk_factors=serialized['risk_factors'],
        recommendations=serialized['recommendations'],
        summary=serialized['summary'],
    )


# ============================================================================
# User Approval Flow Endpoint
# ============================================================================

@router.post(
    "/decisions/approve",
    response_model=ApproveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Approve and store a validated decision",
    description="""
    User Approval Flow - Final step to store a decision.

    **Flow:**
    1. POST /validate/enhanced → Get proposal_id + approval_summary
    2. User reviews approval_summary
    3. POST /decisions/approve → Store decision permanently

    **Why approval is required:**
    - Decisions are IMMUTABLE once stored (MANTRA-LAW-001)
    - User must consciously approve before storage
    - Prevents accidental storage of decisions

    **Requirements:**
    - proposal_id: Must be from a recent /validate/enhanced call (< 30 min)
    - approved_by: Human identifier taking responsibility
    - acknowledgments: Required if decision has warnings

    **Returns:**
    - STORED: Decision stored successfully
    - BLOCKED: Decision cannot be stored (check blocking_reasons)
    - NOT_FOUND: Proposal expired or invalid
    - ERROR: Storage failed
    """
)
async def approve_decision_endpoint(
    request: ApproveRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> ApproveResponse:
    """Approve and store a validated decision."""
    import uuid

    # Clean up expired proposals
    _cleanup_expired_proposals()

    # Find the proposal
    proposal = _pending_proposals.get(request.proposal_id)
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {request.proposal_id} not found or expired. "
                   "Please run /validate/enhanced again to get a new proposal."
        )

    # Check if proposal can be stored
    if not proposal.can_store:
        return ApproveResponse(
            result="BLOCKED",
            decision_id=proposal.decision_id,
            error_message=f"Decision cannot be stored. Validation result: {proposal.validation_result}"
        )

    # Check acknowledgments if required
    if proposal.requires_acknowledgment:
        if not request.acknowledgments:
            return ApproveResponse(
                result="BLOCKED",
                decision_id=proposal.decision_id,
                error_message="This decision has warnings that must be acknowledged. "
                              f"Please provide acknowledgments for: {proposal.warnings[:3]}"
            )

    # Build the decision from the proposal record
    record = proposal.record
    try:
        decision = Decision(
            decision_id=proposal.decision_id,
            group_id=GroupId(record['group_id']),
            feature_id=FeatureId(record['feature_id']),
            statement=record['statement'],
            rationale=record['rationale'],
            constraints=record.get('constraints', []),
            invariants=record.get('invariants', []),
            scope=record.get('scope', 'APPLICATION'),
            blast_radius=record.get('blast_radius', 'LOW'),
            version=record.get('version', '1.0.0'),
            created_by=record.get('created_by'),
            created_at=datetime.utcnow(),
            approved_by=request.approved_by,
            approved_at=datetime.utcnow(),
            supersedes=record.get('supersedes'),
            related_decisions=record.get('related_decisions', []),
            tags=record.get('tags', []),
            tech_stack=record.get('tech_stack', []),
        )
    except Exception as e:
        return ApproveResponse(
            result="ERROR",
            decision_id=proposal.decision_id,
            error_message=f"Failed to build decision: {str(e)}"
        )

    # Store the decision
    result = await store_decision_async(decision, request.approved_by, repository)

    if result.result == StoreResult.STORED:
        # Remove from pending proposals
        del _pending_proposals[request.proposal_id]

        # Record audit event
        record_audit(
            event_type=AuditEventType.DECISION_STORED,
            actor=request.approved_by,
            actor_type="human",
            decision_id=proposal.decision_id,
            repository=repository,
            metadata={
                "proposal_id": request.proposal_id,
                "acknowledged_warnings": request.acknowledgments or [],
                "approval_flow": "user_approval",
            },
        )

        return ApproveResponse(
            result="STORED",
            decision_id=result.decision_id,
            decision_code=decision.decision_code,
            stored_at=result.stored_at,
        )
    else:
        return ApproveResponse(
            result="ERROR",
            decision_id=proposal.decision_id,
            error_message=result.error_message,
        )


# ============================================================================
# Decision Store Endpoints
# ============================================================================

@router.post(
    "/decisions",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store a validated decision",
    description="""
    Stores a validated decision immutably.

    Per MANTRA-L1-IMPL-DECISION-STORE-001:
    - Enforces write-once semantics
    - Provides append-only storage
    - Maintains audit trail

    Per MANTRA-LAW-001 §10:
    - Stored decisions MUST NOT be modified
    - Stored decisions MUST NOT be deleted
    """
)
async def store_endpoint(
    request: StoreRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> StoreResponse:
    """Store a validated decision."""
    import uuid

    # Use provided decision_id from propose, or generate new one
    # This preserves ID continuity between propose and store operations
    final_decision_id = request.decision_id or str(uuid.uuid4())

    # Create Decision from request
    # Per MANTRA-SPEC-001-AMENDMENT-001: NO status field
    # Evolution via version + supersedes only
    decision = Decision(
        decision_id=final_decision_id,
        group_id=request.decision.group_id,
        feature_id=request.decision.feature_id,
        statement=request.decision.statement,
        rationale=request.decision.rationale,
        constraints=request.decision.constraints,
        invariants=request.decision.invariants,
        scope=request.decision.scope,
        blast_radius=request.decision.blast_radius,
        version=request.decision.version,
        created_by=request.decision.created_by,
        created_at=datetime.utcnow(),
        supersedes=request.decision.supersedes,
        related_decisions=request.decision.related_decisions,
        tags=request.decision.tags,
        tech_stack=request.decision.tech_stack,
    )

    # Store decision - use async version to ensure persistence completes
    result = await store_decision_async(decision, request.stored_by, repository)

    if result.result == StoreResult.STORED:
        return StoreResponse(
            result=result.result.value,
            decision_id=result.decision_id,
            stored_at=result.stored_at,
        )
    else:
        # Per Human Decision (Phase 2): Store returns TECHNICAL errors only
        # ALREADY_EXISTS = immutability constraint (409 Conflict)
        # INVALID_SUPERSEDES = data integrity error (400 Bad Request)
        # STORE_ERROR = technical/IO failure (500 Internal Server Error)
        if result.result == StoreResult.ALREADY_EXISTS:
            status_code = status.HTTP_409_CONFLICT
        elif result.result == StoreResult.INVALID_SUPERSEDES:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        raise HTTPException(
            status_code=status_code,
            detail=result.error_message
        )


# ============================================================================
# Public Read API Endpoints
# ============================================================================

@router.get(
    "/decisions",
    response_model=ListDecisionsResponse,
    summary="List all decisions",
    description="""
    Lists ALL stored decisions with pagination - PURE DATA ACCESS.

    Per Human Decision (Phase 3):
    - Returns ALL decisions (no semantic filtering)
    - Consumer interprets which is current/active/valid
    - Structural filtering only (group_id)
    """
)
async def list_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    group_id: Optional[GroupId] = Query(default=None),
    repository: DecisionRepository = Depends(get_repository)
) -> ListDecisionsResponse:
    """List ALL decisions - PURE DATA ACCESS."""
    try:
        # Use async version of find_all for proper database access
        stored_decisions = await repository.find_all_async(limit=limit, offset=offset)
        decisions = [sd.decision for sd in stored_decisions]

        # Structural filter only - by group_id
        if group_id:
            decisions = [d for d in decisions if d.group_id == group_id]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return ListDecisionsResponse(
        decisions=[
            DecisionResponse(
                decision_id=d.decision_id,
                decision_code=d.decision_code,
                group_id=d.group_id.value,
                feature_id=d.feature_id.value,
                statement=d.statement,
                rationale=d.rationale,
                constraints=[serialize_constraint(c) for c in d.constraints],
                invariants=d.invariants,
                scope=d.scope.value,
                blast_radius=d.blast_radius.value,
                version=d.version,
                created_by=d.created_by,
                created_at=d.created_at,
                approved_by=d.approved_by,
                approved_at=d.approved_at,
                supersedes=d.supersedes,
                related_decisions=d.related_decisions,
                tags=d.tags,
                tech_stack=d.tech_stack,
            )
            for d in decisions
        ],
        total_count=len(decisions),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/decisions/{decision_id}",
    response_model=DecisionResponse,
    summary="Get a decision by ID",
    description="Retrieves a single decision by its ID."
)
async def get_endpoint(
    decision_id: str,
    repository: DecisionRepository = Depends(get_repository)
) -> DecisionResponse:
    """Get a decision by ID."""
    # Use async version for proper database access
    stored = await repository.find_by_id_async(decision_id)

    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found"
        )

    d = stored.decision
    return DecisionResponse(
        decision_id=d.decision_id,
        decision_code=d.decision_code,
        group_id=d.group_id.value,
        feature_id=d.feature_id.value,
        statement=d.statement,
        rationale=d.rationale,
        constraints=[serialize_constraint(c) for c in d.constraints],
        invariants=d.invariants,
        scope=d.scope.value,
        blast_radius=d.blast_radius.value,
        version=d.version,
        created_by=d.created_by,
        created_at=d.created_at,
        approved_by=d.approved_by,
        approved_at=d.approved_at,
        supersedes=d.supersedes,
        related_decisions=d.related_decisions,
        tags=d.tags,
        tech_stack=d.tech_stack,
    )


@router.get(
    "/grouped",
    response_model=GroupedDecisionsResponse,
    summary="Get decisions grouped by group/feature",
    description="""
    Returns ALL decisions grouped by group/feature - PURE DATA ACCESS.

    Per Human Decision (Phase 3):
    - Returns ALL decisions for each group/feature combination
    - NO filtering by status, active, valid, or any semantic criteria
    - Consumer interprets which decision is current/active/valid
    """
)
async def grouped_endpoint(
    repository: DecisionRepository = Depends(get_repository)
) -> GroupedDecisionsResponse:
    """Get ALL decisions grouped by group/feature - PURE DATA ACCESS."""
    # Build grouped structure using async methods
    grouped = {}

    for group in GroupId:
        grouped[group.value] = {}
        stored_decisions = await repository.find_by_group_async(group)

        for sd in stored_decisions:
            feature_key = sd.decision.feature_id.value
            if feature_key not in grouped[group.value]:
                grouped[group.value][feature_key] = []

            # Return ALL decisions, no filtering
            grouped[group.value][feature_key].append({
                "decision_id": sd.decision.decision_id,
                "statement": sd.decision.statement,
                "scope": sd.decision.scope.value,
                "blast_radius": sd.decision.blast_radius.value,
                "version": sd.decision.version,
                "supersedes": sd.decision.supersedes,
                "created_at": sd.decision.created_at.isoformat() if sd.decision.created_at else None
            })

    return GroupedDecisionsResponse(
        grouped=grouped,
        generated_at=datetime.utcnow()
    )


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service health status."
)
async def health_endpoint() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="ATLAS_MANTRA",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


# ============================================================================
# AI Provider Configuration Endpoints
# ============================================================================

class AIProviderInfo(BaseModel):
    """Information about an AI provider."""
    id: str
    name: str
    default_model: str
    env_key: str
    models: List[str]


class AIProvidersResponse(BaseModel):
    """Response listing available AI providers."""
    providers: List[AIProviderInfo]
    current_provider: Optional[str] = None
    is_configured: bool = False


@router.get(
    "/ai/providers",
    response_model=AIProvidersResponse,
    summary="List available AI providers",
    description="""
    Returns list of supported AI providers for server-side arbitration.

    Supported providers:
    - Anthropic (Claude) - Default, recommended
    - OpenAI (GPT-4, GPT-3.5)
    - DeepSeek
    - Groq (fast inference)
    - xAI (Grok)
    - OpenRouter (multi-model aggregator)

    Use these in arbitration_mode=SERVER requests.
    Set the provider via AI_PROVIDER environment variable.
    """
)
async def list_ai_providers_endpoint() -> AIProvidersResponse:
    """List available AI providers."""
    from ..use_cases.ai_arbiter import get_available_providers, get_ai_client

    providers_data = get_available_providers()
    client = get_ai_client()

    return AIProvidersResponse(
        providers=[
            AIProviderInfo(
                id=p['id'],
                name=p['name'],
                default_model=p['default_model'] or '',
                env_key=p['env_key'] or '',
                models=p['models'] or [],
            )
            for p in providers_data
        ],
        current_provider=client.config.provider.value if client.is_configured else None,
        is_configured=client.is_configured,
    )


# ============================================================================
# Command-Style API Endpoints
# ============================================================================

@router.post(
    "/decisions/propose",
    response_model=ProposeResponse,
    summary="Propose a decision",
    description="""
    Validates a decision and prepares it for storage WITHOUT storing.

    Key Principle:
    - Propose is PREPARATION, not storage
    - Returns a proposal_id and pre-generated decision_id
    - Consumer must call POST /decisions to actually store

    Validation includes:
    - Schema validation (S-001 to S-022)
    - Decision consistency (D-001 to D-014)
    - Relationship integrity (D-015 to D-017) - NEW
    - Law compliance (L-001 to L-011)

    Returns:
    - READY: Decision is valid, ready to store
    - INVALID: Validation failed, see violations
    """
)
async def propose_endpoint(
    request: ProposeRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> ProposeResponse:
    """Propose a decision for storage."""
    # Parse authorship metadata if provided (with explicit error handling)
    authorship = None
    validation_warnings = []
    skipped_rules = []

    if request.authorship_metadata:
        try:
            authorship = AuthorshipMetadata(**request.authorship_metadata)
        except Exception as e:
            # Explicit warning instead of silent fail
            validation_warnings.append(
                f"Invalid authorship_metadata format: {str(e)}. "
                "L-rules (L-001 through L-008) will be skipped."
            )
            skipped_rules = ["L-001", "L-002", "L-003", "L-004", "L-005", "L-006", "L-007", "L-008"]
    else:
        # No authorship metadata provided - L-rules will be skipped
        skipped_rules = ["L-001", "L-002", "L-003", "L-004", "L-005", "L-006", "L-007", "L-008"]

    result = propose_decision(
        decision_create=request.decision,
        proposed_by=request.proposed_by,
        repository=repository,
        authorship_metadata=authorship,
    )

    # Additional: Validate relationship integrity (D-015 to D-017)
    relationship_violations = []
    relationship_advisory = []

    if result.decision and result.decision.related_decisions:
        # Build record dict for validation
        record_dict = {
            "decision_id": result.decision.decision_id,
            "group_id": result.decision.group_id.value,
            "feature_id": result.decision.feature_id.value,
            "related_decisions": result.decision.related_decisions,
        }
        rel_result = await validate_related_decisions_integrity_async(record_dict, repository)

        # Add relationship violations (errors only)
        for v in rel_result.violations:
            if v.is_error:
                relationship_violations.append({
                    "rule_id": v.rule_id,
                    "level": "LEVEL_2",
                    "message": v.message,
                    "field": "related_decisions",
                    "failure_result": "INVALID",
                    "governing_reference": "MANTRA-SCHEMA-001",
                })

        # Add relationship advisory notes
        relationship_advisory = rel_result.advisory_notes

        # If relationship errors, change result to INVALID
        if relationship_violations and result.result.value == "READY":
            # We need to modify the result
            result.result = ProposeResult.INVALID

    # Convert decision to dict for response
    decision_dict = None
    if result.decision:
        decision_dict = {
            "decision_id": result.decision.decision_id,
            "decision_code": result.decision.decision_code,
            "group_id": result.decision.group_id.value,
            "feature_id": result.decision.feature_id.value,
            "statement": result.decision.statement,
            "rationale": result.decision.rationale,
            "constraints": [serialize_constraint(c) for c in result.decision.constraints],
            "invariants": result.decision.invariants,
            "scope": result.decision.scope.value,
            "blast_radius": result.decision.blast_radius.value,
            "version": result.decision.version,
            "created_by": result.decision.created_by,
            "created_at": result.decision.created_at.isoformat() if result.decision.created_at else None,
            "supersedes": result.decision.supersedes,
            "related_decisions": result.decision.related_decisions,
            "tags": result.decision.tags,
            "tech_stack": result.decision.tech_stack,
        }

    # Convert violations
    violations = []
    if result.validation_result:
        violations = [
            {
                "rule_id": v.rule_id,
                "level": v.level.value,
                "message": v.message,
                "field": v.field,
                "failure_result": v.failure_result.value,
                "governing_reference": v.governing_reference,
            }
            for v in result.validation_result.violations
        ]

    # Add relationship violations (D-015, D-016, D-017)
    violations.extend(relationship_violations)

    # Merge skipped_rules from validation result
    if result.validation_result:
        skipped_rules = list(set(skipped_rules + result.validation_result.skipped_rules))

    # Merge advisory notes
    all_advisory_notes = result.advisory_notes + relationship_advisory

    # Determine final result status
    final_result = result.result.value
    if relationship_violations:
        final_result = "INVALID"

    return ProposeResponse(
        result=final_result,
        proposal_id=result.proposal_id,
        decision_id=result.decision_id,
        decision=decision_dict,
        validation_status=result.validation_result.status.value if result.validation_result else "UNKNOWN",
        violations=violations,
        advisory_notes=all_advisory_notes,
        warnings=validation_warnings,
        skipped_rules=skipped_rules,
        proposed_at=result.proposed_at,
    )


@router.post(
    "/decisions/{decision_id}/challenge",
    response_model=ChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Challenge a decision",
    description="""
    Creates a NEW decision that supersedes the challenged one.

    Challenge != Status change:
    - Old decision stays immutable
    - New decision is created with supersedes = challenged decision_id
    - Maintains append-only semantics

    Per MANTRA-LAW-001:
    - Human authority required to challenge
    - Both decisions remain immutable
    """
)
async def challenge_endpoint(
    decision_id: str,
    request: ChallengeRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> ChallengeResponse:
    """Challenge a decision by creating a superseding decision."""
    import uuid

    # Verify challenged decision exists - use async version
    challenged = await repository.find_by_id_async(decision_id)
    if not challenged:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision to challenge not found: {decision_id}"
        )

    # Create the new decision with supersedes set
    new_decision = Decision(
        decision_id=str(uuid.uuid4()),
        group_id=request.proposed_replacement.group_id,
        feature_id=request.proposed_replacement.feature_id,
        statement=request.proposed_replacement.statement,
        rationale=request.proposed_replacement.rationale,
        constraints=request.proposed_replacement.constraints,
        invariants=request.proposed_replacement.invariants,
        scope=request.proposed_replacement.scope,
        blast_radius=request.proposed_replacement.blast_radius,
        version=request.proposed_replacement.version,
        created_by=request.proposed_replacement.created_by or request.challenger,
        created_at=datetime.utcnow(),
        supersedes=decision_id,  # KEY: Link to challenged decision
        related_decisions=request.proposed_replacement.related_decisions + [decision_id],
        tags=request.proposed_replacement.tags,
        tech_stack=request.proposed_replacement.tech_stack,
    )

    # Store the new decision - use async version
    result = await store_decision_async(new_decision, request.challenger, repository)

    if result.result == StoreResult.STORED:
        # Record challenge audit event using typed metadata
        challenge_metadata = ChallengeMetadata(
            challenged_decision_id=decision_id,
            challenge_rationale=request.challenge_rationale,
            new_decision_id=result.decision_id,
        )
        record_audit(
            event_type=AuditEventType.CHALLENGE_CREATED,
            actor=request.challenger,
            actor_type="human",
            decision_id=new_decision.decision_id,
            repository=repository,
            metadata=challenge_metadata.to_dict(),
        )

        return ChallengeResponse(
            result="STORED",
            challenged_decision_id=decision_id,
            new_decision_id=result.decision_id,
            stored_at=result.stored_at,
        )
    else:
        return ChallengeResponse(
            result="ERROR",
            challenged_decision_id=decision_id,
            error_message=result.error_message,
        )


@router.get(
    "/decisions/{decision_id}/compare/{other_decision_id}",
    response_model=CompareResponse,
    summary="Compare two decisions",
    description="""
    Compares two decisions side-by-side.

    Returns:
    - Field-by-field differences
    - Whether they're in a supersedes chain
    - Common group/feature information
    """
)
async def compare_endpoint(
    decision_id: str,
    other_decision_id: str,
    actor: str = Query(..., description="Human identifier performing comparison"),
    repository: DecisionRepository = Depends(get_repository)
) -> CompareResponse:
    """Compare two decisions."""
    result = compare_decisions(decision_id, other_decision_id, actor, repository)

    # Convert decisions to dicts
    def decision_to_dict(d):
        if not d:
            return None
        return {
            "decision_id": d.decision_id,
            "decision_code": d.decision_code,
            "group_id": d.group_id.value,
            "feature_id": d.feature_id.value,
            "statement": d.statement,
            "rationale": d.rationale,
            "constraints": [serialize_constraint(c) for c in d.constraints],
            "invariants": d.invariants,
            "scope": d.scope.value,
            "blast_radius": d.blast_radius.value,
            "version": d.version,
            "created_by": d.created_by,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "supersedes": d.supersedes,
            "tags": d.tags,
            "tech_stack": d.tech_stack,
        }

    return CompareResponse(
        result=result.result.value,
        decision_a=decision_to_dict(result.decision_a),
        decision_b=decision_to_dict(result.decision_b),
        differences=[
            {
                "field_name": diff.field_name,
                "value_a": diff.value_a,
                "value_b": diff.value_b,
                "change_type": diff.change_type,
            }
            for diff in result.differences
        ],
        is_supersedes_chain=result.is_supersedes_chain,
        supersedes_direction=result.supersedes_direction,
        common_group=result.common_group,
        common_feature=result.common_feature,
        error_message=result.error_message,
    )


@router.get(
    "/decisions/{decision_id}/history",
    response_model=HistoryResponse,
    summary="Get decision version history",
    description="""
    Gets the complete version chain for a decision.

    Returns all decisions in the supersedes chain:
    - Older versions (decisions this one supersedes)
    - Newer versions (decisions that supersede this one)

    Chain is ordered from oldest to newest.
    """
)
async def history_endpoint(
    decision_id: str,
    actor: str = Query(..., description="Human identifier requesting history"),
    repository: DecisionRepository = Depends(get_repository)
) -> HistoryResponse:
    """Get version chain for a decision."""
    result = get_decision_history(decision_id, actor, repository)

    def decision_to_dict(d):
        return {
            "decision_id": d.decision_id,
            "decision_code": d.decision_code,
            "group_id": d.group_id.value,
            "feature_id": d.feature_id.value,
            "statement": d.statement,
            "version": d.version,
            "created_by": d.created_by,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "supersedes": d.supersedes,
        }

    return HistoryResponse(
        result=result.result.value,
        decision_id=decision_id,
        chain=[decision_to_dict(d) for d in result.chain],
        total_versions=result.total_versions,
        error_message=result.error_message,
    )


@router.get(
    "/audit",
    response_model=AuditListResponse,
    summary="List audit entries",
    description="""
    Lists audit trail entries with optional filtering.

    Filter by:
    - decision_id: Filter by specific decision
    - event_type: Filter by event type (DECISION_PROPOSED, DECISION_STORED, etc.)
    - actor: Filter by actor identifier

    Returns entries ordered by timestamp descending (most recent first).
    """
)
async def audit_list_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    decision_id: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    actor: Optional[str] = Query(default=None),
    repository: DecisionRepository = Depends(get_repository)
) -> AuditListResponse:
    """List audit entries."""
    # Parse event_type if provided
    parsed_event_type = None
    if event_type:
        try:
            parsed_event_type = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event_type: {event_type}. Valid values: {[e.value for e in AuditEventType]}"
            )

    result = list_audit_entries(
        repository=repository,
        limit=limit,
        offset=offset,
        decision_id=decision_id,
        event_type=parsed_event_type,
        actor=actor,
    )

    if result.result == AuditResult.ERROR:
        return AuditListResponse(
            result="ERROR",
            error_message=result.error_message,
        )

    return AuditListResponse(
        result=result.result.value,
        entries=[
            AuditEntryResponse(
                event_id=e.event_id,
                event_type=e.event_type.value,
                actor=e.actor,
                actor_type=e.actor_type,
                decision_id=e.decision_id,
                timestamp=e.timestamp,
                metadata=e.metadata,
            )
            for e in result.entries
        ],
        total_count=result.total_count,
        limit=limit,
        offset=offset,
    )
