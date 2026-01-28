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
import uuid
import logging
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.schema import (
    Decision,
    DecisionCreate,
    DomainId,
    AspectId,
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
    group_decisions_by_domain_aspect,
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
from ..repositories.decision_repository import DecisionRepository
from ..runtime.config import get_config
from ..ports.cache import CacheKeys, CacheTTL
from ..ports.message_queue import Message, MantraEvents
from factory.container import Container

# Setup logger
logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["decisions"])


def get_repository() -> DecisionRepository:
    """
    Get repository instance from Container (singleton).

    The repository is initialized during application startup via Container.initialize().
    """
    return Container.get_decision_repository()


def set_repository(repo: DecisionRepository) -> None:
    """
    Set repository instance (for testing purposes).

    Note: This directly sets the Container's internal repository.
    Use Container.reset() to clear and reinitialize.
    """
    Container._decision_repository = repo
    Container._repository_initialized = True


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

    MICS Two-Layer Content Model:
    - Layer A: statement, rationale (summary/executive)
    - Layer B: detailed_content, sections (full specification)
    """
    decision_id: str
    decision_code: Optional[str] = None
    domain_id: str
    aspect_id: str
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
    # MICS Layer B Content
    detailed_content: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    content_summary: Optional[str] = None


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
    common_domain: bool = False
    common_aspect: bool = False
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

# In-memory proposal storage (Redis-backed with fallback)
_pending_proposals: TypingDict[str, PendingProposal] = {}

# Proposal storage helpers (Redis-backed)
PROPOSAL_TTL = 1800  # 30 minutes

async def _store_proposal(proposal_id: str, proposal: PendingProposal) -> None:
    """Store proposal in Redis (or fallback to memory)."""
    cache = Container.get_cache()
    if cache:
        try:
            # Serialize proposal to dict
            proposal_data = {
                'proposal_id': proposal.proposal_id,
                'decision_id': proposal.decision_id,
                'record': proposal.record,
                'validation_result': proposal.validation_result,
                'can_store': proposal.can_store,
                'requires_acknowledgment': proposal.requires_acknowledgment,
                'warnings': proposal.warnings,
                'validated_at': proposal.validated_at.isoformat(),
                'expires_at': proposal.expires_at,
            }
            await cache.set(
                f"mantra:proposal:{proposal_id}",
                proposal_data,
                ttl=PROPOSAL_TTL
            )
            return
        except Exception:
            # Silently fallback to memory on Redis errors
            pass
    # Fallback to memory
    _pending_proposals[proposal_id] = proposal

async def _get_proposal(proposal_id: str) -> Optional[PendingProposal]:
    """Get proposal from Redis (or fallback to memory)."""
    cache = Container.get_cache()
    if cache:
        try:
            cached = await cache.get(f"mantra:proposal:{proposal_id}")
            if cached:
                # Deserialize from dict to PendingProposal
                return PendingProposal(
                    proposal_id=cached['proposal_id'],
                    decision_id=cached['decision_id'],
                    record=cached['record'],
                    validation_result=cached['validation_result'],
                    can_store=cached['can_store'],
                    requires_acknowledgment=cached['requires_acknowledgment'],
                    warnings=cached['warnings'],
                    validated_at=datetime.fromisoformat(cached['validated_at']),
                    expires_at=cached['expires_at'],
                )
        except Exception:
            # Silently fallback to memory on Redis errors
            pass
    # Fallback to memory
    return _pending_proposals.get(proposal_id)

async def _delete_proposal(proposal_id: str) -> None:
    """Delete proposal from Redis (or memory)."""
    cache = Container.get_cache()
    if cache:
        try:
            await cache.delete(f"mantra:proposal:{proposal_id}")
        except Exception:
            # Silently ignore Redis errors
            pass
    # Also remove from memory fallback
    _pending_proposals.pop(proposal_id, None)


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

    # AI Classification - Auto-detect group/feature (when missing)
    classification_required: bool = False  # True if domain_id/aspect_id missing
    classification_context: Optional[Dict[str, Any]] = None  # For delegated AI

    # Auto-Supersedes Detection - Suggest if this updates existing decision
    supersedes_suggestion: Optional[Dict[str, Any]] = None

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

    # =========================================================================
    # AI CLASSIFICATION: Check if domain_id/aspect_id need classification
    # =========================================================================
    classification_required = False
    classification_context = None
    supersedes_suggestion = None

    domain_id = request.record.get('domain_id')
    aspect_id = request.record.get('aspect_id')
    statement = request.record.get('statement', '')
    rationale = request.record.get('rationale', '')
    constraints = request.record.get('constraints', [])

    # If domain_id or aspect_id missing, provide classification context
    if not domain_id or not aspect_id:
        from ..use_cases.ai_arbiter import get_classification_context
        classification_required = True
        classification_context = get_classification_context(statement, rationale, constraints)

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
    # AUTO-SUPERSEDES: Check if this should supersede existing decision
    # =========================================================================
    # Only check if we have valid domain/aspect and statement
    if domain_id and aspect_id and statement:
        supersedes_suggestion = await _check_supersedes_suggestion(
            statement=statement,
            rationale=rationale,
            domain_id=domain_id,
            aspect_id=aspect_id,
            repository=repository
        )

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
    await _store_proposal(serialized['proposal_id'], proposal)

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
        # AI Classification (when domain_id/aspect_id missing)
        classification_required=classification_required,
        classification_context=classification_context,
        # Auto-Supersedes Detection
        supersedes_suggestion=supersedes_suggestion,
        # User Approval Flow
        requires_user_approval=True,
        approval_summary=serialized.get('approval_summary'),
    )


async def _cleanup_expired_proposals():
    """
    Remove expired proposals from memory storage.

    Note: Redis entries are automatically expired via TTL,
    so we only clean up the in-memory fallback here.
    """
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
# AI Classification Endpoint
# ============================================================================

class ClassifyRequest(BaseModel):
    """Request body for decision classification."""
    statement: str = Field(..., min_length=10, description="Decision statement to classify")
    rationale: str = Field(..., min_length=10, description="Decision rationale")
    constraints: Optional[List[Dict[str, Any]]] = Field(None, description="Decision constraints")
    # Mode: SERVER = MANTRA's AI classifies, DELEGATED = return context for client AI
    classification_mode: ArbitrationModeInput = Field(
        ArbitrationModeInput.DELEGATED,
        description="DELEGATED returns prompt for client AI, SERVER uses MANTRA's AI"
    )
    # If client AI already classified (delegated mode follow-up)
    classification_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Client AI's classification result: {domain_id: str, aspect_id: str, confidence: float}"
    )


class ClassifyResponse(BaseModel):
    """Response body for decision classification."""
    # Classification result (if available)
    domain_id: Optional[str] = None
    aspect_id: Optional[str] = None
    domain_label: Optional[str] = None
    aspect_label: Optional[str] = None
    confidence: Optional[float] = None

    # For delegated mode: context for client AI to classify
    classification_required: bool = False
    classification_context: Optional[Dict[str, Any]] = None

    # Supersedes detection (auto-detect if this updates existing decision)
    supersedes_suggestion: Optional[Dict[str, Any]] = None

    # Status
    is_valid: bool
    message: str


@router.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Auto-classify decision into Group and Feature",
    description="""
    AI-powered decision classification.

    **Purpose:**
    - Remove human error in categorizing decisions
    - AI determines the correct Group (INT/ARCH/CTL/EVO) and Feature (F01-F16)
    - Also detects if this decision should supersede an existing one

    **Modes:**
    - DELEGATED (default): Returns prompt/context for your AI to classify
    - SERVER: MANTRA's AI classifies directly (costs MANTRA)

    **Flow:**
    1. POST /classify with statement + rationale → Get classification_context
    2. Your AI classifies using the context
    3. POST /classify again with classification_result
    4. Receive domain_id, aspect_id, and supersedes_suggestion

    **Taxonomy:**
    - INT: Intent & Direction (WHY/WHAT) → F01-F04
    - ARCH: Architecture & Boundaries (HOW/WHERE) → F05-F08
    - CTL: Control, Policy & Risk (CAN/MUST NOT) → F09-F12
    - EVO: Execution & Evolution (CHANGE SAFELY) → F13-F16
    """
)
async def classify_endpoint(
    request: ClassifyRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> ClassifyResponse:
    """Classify decision into correct Group and Feature."""
    from ..use_cases.ai_arbiter import (
        DecisionClassifier,
        get_classification_context,
        validate_classification_result,
        get_ai_client,
    )
    from ..domain.schema import DOMAIN_LABELS, ASPECT_LABELS

    classifier = DecisionClassifier()

    # If client provided classification result (delegated mode follow-up)
    if request.classification_result:
        domain_id = request.classification_result.get('domain_id', '').upper()
        aspect_id = request.classification_result.get('aspect_id', '').upper()
        confidence = float(request.classification_result.get('confidence', 0.8))

        # Validate the classification
        is_valid, error = validate_classification_result(domain_id, aspect_id)

        if not is_valid:
            return ClassifyResponse(
                is_valid=False,
                message=error or "Invalid classification",
                classification_required=True,
                classification_context=get_classification_context(
                    request.statement,
                    request.rationale,
                    request.constraints
                )
            )

        # Check for supersedes (similar existing decision)
        supersedes_suggestion = await _check_supersedes_suggestion(
            request.statement,
            request.rationale,
            domain_id,
            aspect_id,
            repository
        )

        return ClassifyResponse(
            domain_id=domain_id,
            aspect_id=aspect_id,
            domain_label=DOMAIN_LABELS.get(domain_id, domain_id),
            aspect_label=ASPECT_LABELS.get(aspect_id, aspect_id),
            confidence=confidence,
            supersedes_suggestion=supersedes_suggestion,
            is_valid=True,
            message=f"Classified as {domain_id}/{aspect_id}" + (
                f" (suggests supersedes {supersedes_suggestion['existing_code']})"
                if supersedes_suggestion else ""
            )
        )

    # DELEGATED mode: Return context for client AI
    if request.classification_mode == ArbitrationModeInput.DELEGATED:
        ctx = get_classification_context(
            request.statement,
            request.rationale,
            request.constraints
        )
        return ClassifyResponse(
            classification_required=True,
            classification_context=ctx,
            is_valid=True,
            message="Classification context provided. Use your AI to classify, then submit classification_result."
        )

    # SERVER mode: Use MANTRA's AI (requires configured AI client)
    ai_client = get_ai_client()

    if not ai_client.is_configured:
        # Fallback to delegated mode if AI not configured
        ctx = get_classification_context(
            request.statement,
            request.rationale,
            request.constraints
        )
        return ClassifyResponse(
            classification_required=True,
            classification_context=ctx,
            is_valid=True,
            message="Server-side AI not configured. Please use delegated mode or provide classification_result."
        )

    # Build classifier and perform server-side classification
    classifier = DecisionClassifier()
    prompt = classifier.build_prompt(
        request.statement,
        request.rationale,
        request.constraints
    )

    try:
        # Call AI for classification
        response_text = await ai_client.complete(prompt)
        result = classifier._parse_response(response_text)

        if result.requires_ai or not result.domain_id:
            # AI response couldn't be parsed - return delegated context
            ctx = get_classification_context(
                request.statement,
                request.rationale,
                request.constraints
            )
            return ClassifyResponse(
                classification_required=True,
                classification_context=ctx,
                is_valid=True,
                message="AI classification failed to produce valid result. Please use delegated mode."
            )

        # Successful classification - check for supersedes
        supersedes_suggestion = await _check_supersedes_suggestion(
            request.statement,
            request.rationale,
            result.domain_id,
            result.aspect_id,
            repository
        )

        return ClassifyResponse(
            classification_required=False,
            domain_id=result.domain_id,
            aspect_id=result.aspect_id,
            confidence=result.confidence,
            supersedes_suggestion=supersedes_suggestion,
            is_valid=True,
            message=f"AI classified as {result.domain_id}/{result.aspect_id} (confidence: {result.confidence:.0%})" + (
                f" - suggests supersedes {supersedes_suggestion['existing_code']}"
                if supersedes_suggestion else ""
            )
        )

    except Exception as e:
        # AI call failed - fallback to delegated mode
        ctx = get_classification_context(
            request.statement,
            request.rationale,
            request.constraints
        )
        return ClassifyResponse(
            classification_required=True,
            classification_context=ctx,
            is_valid=True,
            message=f"Server-side AI error: {str(e)}. Please use delegated mode."
        )


async def _check_supersedes_suggestion(
    statement: str,
    rationale: str,
    domain_id: str,
    aspect_id: str,
    repository: DecisionRepository
) -> Optional[Dict[str, Any]]:
    """
    Check if this decision should supersede an existing one.

    TIERED APPROACH (minimize AI cost):
    - >80% similarity: AUTO (auto-set supersedes, no AI needed)
    - 60-80% similarity: AI_REVIEW (delegated AI decides)
    - 40-60% similarity: MANUAL_REVIEW (human decides)
    - <40% similarity: NOT_RELATED (no suggestion)

    This approach uses simple word-overlap first, only invoking AI for ambiguous cases.
    """
    try:
        # Convert string to enum for repository call
        from ..domain.schema import DomainId, AspectId
        domain_enum = DomainId(domain_id)

        # Get existing decisions in same domain, then filter by aspect
        all_in_domain = await repository.find_by_domain_async(
            domain_id=domain_enum,
            limit=50  # Get more to filter
        )

        # Filter by aspect_id (compare enum values or strings)
        existing = [
            d for d in all_in_domain
            if (d.decision.aspect_id.value if hasattr(d.decision.aspect_id, 'value') else d.decision.aspect_id) == aspect_id
        ][:10]

        if not existing:
            return None

        # Simple similarity check (Jaccard index on words)
        statement_lower = statement.lower()
        rationale_lower = rationale.lower()

        best_match = None
        best_score = 0.0

        for stored in existing:
            # Calculate word overlap similarity (Jaccard index)
            # stored is StoredDecision, access .decision for the actual Decision
            existing_statement = (stored.decision.statement or '').lower()
            existing_rationale = (stored.decision.rationale or '').lower()

            # Statement similarity
            statement_words = set(statement_lower.split())
            existing_words = set(existing_statement.split())

            if not statement_words or not existing_words:
                continue

            overlap = len(statement_words & existing_words)
            union = len(statement_words | existing_words)
            stmt_similarity = overlap / union if union > 0 else 0

            # Rationale similarity (if available)
            rat_similarity = 0.0
            rationale_words = set(rationale_lower.split())
            existing_rat_words = set(existing_rationale.split())
            if rationale_words and existing_rat_words:
                rat_overlap = len(rationale_words & existing_rat_words)
                rat_union = len(rationale_words | existing_rat_words)
                rat_similarity = rat_overlap / rat_union if rat_union > 0 else 0

            # Combined similarity (weighted: statement 60%, rationale 40%)
            similarity = (stmt_similarity * 0.6) + (rat_similarity * 0.4)

            if similarity > best_score and similarity >= 0.4:
                best_score = similarity
                best_match = stored  # StoredDecision object

        if not best_match or best_score < 0.4:
            return None

        # TIERED DECISION:
        # >80%: AUTO - definitely an update, auto-supersedes
        # 60-80%: AI_REVIEW - likely an update, AI decides
        # 40-60%: MANUAL_REVIEW - possibly related, human decides

        # best_match is StoredDecision, access .decision for attributes
        match_decision = best_match.decision

        if best_score >= 0.8:
            # HIGH confidence - AUTO supersedes
            recommendation = 'AUTO'
            message = (
                f"SIMILARITY {int(best_score * 100)}%: This is clearly an update to "
                f"{match_decision.decision_code or match_decision.decision_id[:8]}. "
                f"Supersedes will be auto-set."
            )
            auto_populate = {'supersedes': match_decision.decision_id}
            ai_context = None

        elif best_score >= 0.6:
            # MEDIUM confidence - AI decides
            recommendation = 'AI_REVIEW'
            message = (
                f"SIMILARITY {int(best_score * 100)}%: This might be an update to "
                f"{match_decision.decision_code or match_decision.decision_id[:8]}. "
                f"AI will determine if this should supersede."
            )
            auto_populate = None
            # Provide context for delegated AI
            ai_context = {
                'prompt': (
                    f"Decide if the NEW decision supersedes the EXISTING decision.\n\n"
                    f"NEW:\n  Statement: \"{statement[:200]}...\"\n\n"
                    f"EXISTING ({match_decision.decision_code or match_decision.decision_id[:8]}):\n"
                    f"  Statement: \"{match_decision.statement[:200]}...\"\n\n"
                    f"Respond JSON only: {{\"is_supersedes\": true|false, \"confidence\": 0.0-1.0}}"
                ),
                'existing_id': match_decision.decision_id,
                'existing_code': match_decision.decision_code,
            }

        else:
            # LOW confidence - manual review
            recommendation = 'MANUAL_REVIEW'
            message = (
                f"SIMILARITY {int(best_score * 100)}%: This might be related to "
                f"{match_decision.decision_code or match_decision.decision_id[:8]}. "
                f"Please review if this should supersede or be a separate decision."
            )
            auto_populate = None
            ai_context = None

        return {
            'existing_id': match_decision.decision_id,
            'existing_code': match_decision.decision_code or f"{domain_id}-{aspect_id}",
            'existing_statement': (
                match_decision.statement[:100] + '...'
                if len(match_decision.statement) > 100
                else match_decision.statement
            ),
            'similarity': round(best_score, 2),
            'recommendation': recommendation,
            'message': message,
            'auto_populate': auto_populate,
            'ai_context': ai_context,
        }

    except Exception:
        # Silently fail - supersedes suggestion is optional
        return None


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
    config = get_config()

    # Clean up expired proposals
    await _cleanup_expired_proposals()

    # Find the proposal
    proposal = await _get_proposal(request.proposal_id)
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
            domain_id=DomainId(record['domain_id']),
            aspect_id=AspectId(record['aspect_id']),
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
        await _delete_proposal(request.proposal_id)

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

        # Publish decision approved event
        queue = Container.get_message_queue()
        if queue:
            try:
                await queue.publish(config.rabbitmq_queue_sync, Message(
                    id=str(uuid.uuid4()),
                    event_type=MantraEvents.DECISION_APPROVED,
                    payload={
                        "decision_id": result.decision_id,
                        "approved_by": request.approved_by,
                        "approved_at": datetime.utcnow().isoformat()
                    },
                    timestamp=datetime.utcnow().isoformat()
                ))
            except Exception as e:
                logger.warning(f"Failed to queue approval event: {e}")

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
    config = get_config()

    # Use provided decision_id from propose, or generate new one
    # This preserves ID continuity between propose and store operations
    final_decision_id = request.decision_id or str(uuid.uuid4())

    # Create Decision from request
    # Per MANTRA-SPEC-001-AMENDMENT-001: NO status field
    # Evolution via version + supersedes only
    decision = Decision(
        decision_id=final_decision_id,
        domain_id=request.decision.domain_id,
        aspect_id=request.decision.aspect_id,
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
        # Layer B Content (MICS Long Content Strategy)
        detailed_content=request.decision.detailed_content,
        sections=request.decision.sections,
    )

    # Store decision - use async version to ensure persistence completes
    result = await store_decision_async(decision, request.stored_by, repository)

    if result.result == StoreResult.STORED:
        # Publish embedding sync event
        queue = Container.get_message_queue()
        if queue:
            try:
                await queue.publish(config.rabbitmq_queue_sync, Message(
                    id=str(uuid.uuid4()),
                    event_type=MantraEvents.EMBEDDING_SYNC_REQUESTED,
                    payload={"decision_ids": [result.decision_id], "force_rebuild": False},
                    timestamp=datetime.utcnow().isoformat()
                ))
            except Exception as e:
                logger.warning(f"Failed to queue embedding sync: {e}")

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
    - Structural filtering only (domain_id)
    """
)
async def list_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    domain_id: Optional[DomainId] = Query(default=None),
    repository: DecisionRepository = Depends(get_repository)
) -> ListDecisionsResponse:
    """List ALL decisions - PURE DATA ACCESS."""
    # Check cache first
    cache = Container.get_cache()

    # Build cache key from parameters
    domain_key = domain_id.value if domain_id else "all"
    cache_key = f"mantra:decisions:list:{limit}:{offset}:{domain_key}"

    if cache:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return ListDecisionsResponse(**cached)
        except Exception:
            pass  # Cache miss or error, continue to DB

    try:
        # Use async version of find_all for proper database access
        stored_decisions = await repository.find_all_async(limit=limit, offset=offset)
        decisions = [sd.decision for sd in stored_decisions]

        # Structural filter only - by domain_id
        if domain_id:
            decisions = [d for d in decisions if d.domain_id == domain_id]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    result = ListDecisionsResponse(
        decisions=[
            DecisionResponse(
                decision_id=d.decision_id,
                decision_code=d.decision_code,
                domain_id=d.domain_id.value,
                aspect_id=d.aspect_id.value,
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
                # MICS Layer B Content
                detailed_content=getattr(d, 'detailed_content', None),
                sections=[
                    {
                        "section_id": s.section_id,
                        "title": s.title,
                        "section_type": s.section_type.value if hasattr(s.section_type, 'value') else s.section_type,
                        "content": s.content,
                        "order": s.order
                    }
                    for s in getattr(d, 'sections', []) or []
                ] if getattr(d, 'sections', None) else None,
                content_summary=getattr(d, 'content_summary', None),
            )
            for d in decisions
        ],
        total_count=len(decisions),
        limit=limit,
        offset=offset,
    )

    # Cache the result
    if cache:
        try:
            await cache.set(cache_key, result.model_dump(), ttl=CacheTTL.DECISION_LIST)
        except Exception:
            pass

    return result


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
    # Check cache first
    cache = Container.get_cache()
    cache_key = CacheKeys.decision(decision_id)

    if cache:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return DecisionResponse(**cached)
        except Exception:
            pass  # Cache miss or error, continue to DB

    # Use async version for proper database access
    stored = await repository.find_by_id_async(decision_id)

    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found"
        )

    d = stored.decision
    response = DecisionResponse(
        decision_id=d.decision_id,
        decision_code=d.decision_code,
        domain_id=d.domain_id.value,
        aspect_id=d.aspect_id.value,
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
        # MICS Layer B Content
        detailed_content=getattr(d, 'detailed_content', None),
        sections=[
            {
                "section_id": s.section_id,
                "title": s.title,
                "section_type": s.section_type.value if hasattr(s.section_type, 'value') else s.section_type,
                "content": s.content,
                "order": s.order
            }
            for s in getattr(d, 'sections', []) or []
        ] if getattr(d, 'sections', None) else None,
        content_summary=getattr(d, 'content_summary', None),
    )

    # Cache the result (decisions are immutable)
    if cache:
        try:
            await cache.set(cache_key, response.model_dump(), ttl=CacheTTL.DECISION)
        except Exception:
            pass

    return response


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
    # Check cache first
    cache = Container.get_cache()
    cache_key = "mantra:decisions:grouped"

    if cache:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return GroupedDecisionsResponse(**cached)
        except Exception:
            pass  # Cache miss or error, continue to DB

    # Build grouped structure using async methods
    grouped = {}

    for domain in DomainId:
        grouped[domain.value] = {}
        stored_decisions = await repository.find_by_domain_async(domain)

        for sd in stored_decisions:
            aspect_key = sd.decision.aspect_id.value
            if aspect_key not in grouped[domain.value]:
                grouped[domain.value][aspect_key] = []

            # Return ALL decisions, no filtering
            grouped[domain.value][aspect_key].append({
                "decision_id": sd.decision.decision_id,
                "statement": sd.decision.statement,
                "scope": sd.decision.scope.value,
                "blast_radius": sd.decision.blast_radius.value,
                "version": sd.decision.version,
                "supersedes": sd.decision.supersedes,
                "created_at": sd.decision.created_at.isoformat() if sd.decision.created_at else None
            })

    result = GroupedDecisionsResponse(
        grouped=grouped,
        generated_at=datetime.utcnow()
    )

    # Cache the result
    if cache:
        try:
            await cache.set(cache_key, result.model_dump(), ttl=CacheTTL.DECISION_LIST)
        except Exception:
            pass

    return result


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
# MICS Context Assembly Endpoints
# ============================================================================

class ContextRequest(BaseModel):
    """Request body for context assembly endpoint."""
    task_description: str = Field(..., description="What you're trying to accomplish")
    code_context: Optional[str] = Field(None, description="Current code or file path for context")
    token_budget: int = Field(default=2000, ge=100, le=10000, description="Max tokens for context")
    include_groups: Optional[List[str]] = Field(None, description="Only include these groups")
    exclude_groups: Optional[List[str]] = Field(None, description="Exclude these groups")
    detail_level: Optional[str] = Field(
        default="standard",
        description="micro|standard|detailed|sections - controls content depth"
    )


class ContextResponse(BaseModel):
    """Response body for context assembly endpoint."""
    decisions: List[Dict[str, Any]]
    total_tokens: int
    token_budget: int
    context_summary: str
    task_analysis: Dict[str, Any]
    priority_breakdown: Dict[str, int]


@router.post(
    "/context",
    response_model=ContextResponse,
    summary="Get relevant context for a task (MICS)",
    description="""
    MICS Smart Context Injection - Get relevant decisions for your current task.

    **Pipeline:**
    1. Analyze task description to extract intent and keywords
    2. Select relevant decisions from the knowledge base
    3. Rank by relevance to your task
    4. Allocate token budget across decisions
    5. Return context with appropriate detail levels

    **Token Budget Strategy:**
    - Critical decisions (60%): Full detailed content (Layer B)
    - High priority (30%): Standard content (Layer A)
    - Medium priority (10%): Micro summaries only

    **Detail Levels:**
    - micro: ~100 tokens - content_summary only
    - standard: ~500 tokens - statement + rationale
    - detailed: ~2000+ tokens - full content including Layer B
    - sections: variable - specific sections only

    Use this to inject relevant MANTRA context into your AI workflow.
    """
)
async def get_context_endpoint(
    request: ContextRequest,
    repository: DecisionRepository = Depends(get_repository)
) -> ContextResponse:
    """Get relevant context for a task using MICS pipeline."""
    try:
        from context.pipeline import ContextPipeline

        pipeline = ContextPipeline(repository)
        result = await pipeline.assemble(
            task=request.task_description,
            code=request.code_context,
            budget=request.token_budget,
            include_groups=request.include_groups,
            exclude_groups=request.exclude_groups
        )

        return ContextResponse(
            decisions=result.get("decisions", []),
            total_tokens=result.get("total_tokens", 0),
            token_budget=request.token_budget,
            context_summary=result.get("context_summary", ""),
            task_analysis=result.get("task_analysis", {}),
            priority_breakdown=result.get("priority_breakdown", {})
        )
    except ImportError:
        # Fallback if context module not available
        return ContextResponse(
            decisions=[],
            total_tokens=0,
            token_budget=request.token_budget,
            context_summary="Context pipeline not available",
            task_analysis={"task": request.task_description, "error": "Module not loaded"},
            priority_breakdown={}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context assembly failed: {str(e)}"
        )


class SummaryRequest(BaseModel):
    """Request body for content summary generation."""
    record: Dict[str, Any] = Field(..., description="Decision record to summarize")


class SummaryResponse(BaseModel):
    """Response body for content summary generation."""
    summary: str
    word_count: int
    estimated_tokens: int
    key_terms: List[str]
    compression_ratio: float


@router.post(
    "/summarize",
    response_model=SummaryResponse,
    summary="Generate content summary for a decision (MICS)",
    description="""
    Generate a token-efficient summary for a decision record.

    Used for:
    - Auto-populating content_summary field (Layer A)
    - Micro-level context injection (~100 tokens)
    - Quick reference in AI prompts

    The summary preserves:
    - Key decision intent
    - Technical terminology
    - Actionable clarity

    Compresses to ~50-100 words while maintaining meaning.
    """
)
async def generate_summary_endpoint(request: SummaryRequest) -> SummaryResponse:
    """Generate content summary for a decision."""
    try:
        from context.summarizer import ContentSummarizer

        summarizer = ContentSummarizer()
        result = summarizer.summarize(request.record)

        return SummaryResponse(
            summary=result.summary,
            word_count=result.word_count,
            estimated_tokens=result.estimated_tokens,
            key_terms=result.key_terms,
            compression_ratio=result.compression_ratio
        )
    except ImportError:
        # Fallback - simple truncation
        statement = request.record.get("statement", "")
        return SummaryResponse(
            summary=statement[:200] + "..." if len(statement) > 200 else statement,
            word_count=len(statement.split()),
            estimated_tokens=len(statement) // 4,
            key_terms=[],
            compression_ratio=1.0
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
    config = get_config()

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
            "domain_id": result.decision.domain_id.value,
            "aspect_id": result.decision.aspect_id.value,
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
            "domain_id": result.decision.domain_id.value,
            "aspect_id": result.decision.aspect_id.value,
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

    # Publish decision proposed event for async validation
    queue = Container.get_message_queue()
    if queue and result.proposal_id:
        try:
            await queue.publish(config.rabbitmq_queue_validation, Message(
                id=str(uuid.uuid4()),
                event_type=MantraEvents.DECISION_PROPOSED,
                payload={
                    "proposal_id": result.proposal_id,
                    "decision_id": result.decision_id,
                    "statement": request.decision.statement,
                    "rationale": request.decision.rationale,
                    "domain_id": request.decision.domain_id.value,
                    "aspect_id": request.decision.aspect_id.value
                },
                timestamp=datetime.utcnow().isoformat()
            ))
        except Exception as e:
            logger.warning(f"Failed to queue validation: {e}")

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
    config = get_config()

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
        domain_id=request.proposed_replacement.domain_id,
        aspect_id=request.proposed_replacement.aspect_id,
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

        # Publish challenge event
        queue = Container.get_message_queue()
        if queue:
            try:
                await queue.publish(config.rabbitmq_queue_sync, Message(
                    id=str(uuid.uuid4()),
                    event_type=MantraEvents.DECISION_APPROVED,
                    payload={
                        "decision_id": result.decision_id,
                        "challenged_id": decision_id,
                        "reason": "challenge"
                    },
                    timestamp=datetime.utcnow().isoformat()
                ))
            except Exception as e:
                logger.warning(f"Failed to queue challenge event: {e}")

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
            "domain_id": d.domain_id.value,
            "aspect_id": d.aspect_id.value,
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
        common_domain=result.common_domain,
        common_aspect=result.common_aspect,
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
            "domain_id": d.domain_id.value,
            "aspect_id": d.aspect_id.value,
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


# ============================================================================
# MCP Tool Routes (HTTP Bridge)
# ============================================================================
# These routes expose MCP tools via HTTP for testing and alternative integration.
# IMPORTANT: Write operations require human_confirmed=true

class MCPClassifyRequest(BaseModel):
    """Request for AI decision classification."""
    statement: str = Field(..., description="Decision statement to classify")
    rationale: str = Field(..., description="Decision rationale")
    constraints: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional constraints")


class MCPClassifyResponse(BaseModel):
    """Response with delegated classification context."""
    classification_type: str
    prompt: str
    taxonomy: str
    expected_response: Dict[str, Any]


@router.post(
    "/mcp/classify",
    response_model=MCPClassifyResponse,
    summary="Get AI classification context (delegated)",
    description="""
    Returns classification context for delegated AI mode.
    The calling AI performs the actual classification using the returned prompt.
    MANTRA does NOT call AI - the cost is on the user's AI.
    """
)
async def mcp_classify(
    request: MCPClassifyRequest,
) -> MCPClassifyResponse:
    """Get classification context for delegated AI."""
    from ..use_cases.ai_arbiter.decision_classifier import get_classification_context

    result = get_classification_context(
        statement=request.statement,
        rationale=request.rationale,
        constraints=request.constraints,
    )

    return MCPClassifyResponse(
        classification_type=result.get("classification_type", "DECISION_CLASSIFICATION"),
        prompt=result.get("prompt", ""),
        taxonomy=result.get("taxonomy", ""),
        expected_response=result.get("expected_response", {}),
    )


class MCPProposeRequest(BaseModel):
    """Request to propose a new decision."""
    decision: Dict[str, Any] = Field(..., description="Decision record to propose")
    proposed_by: str = Field(default="ai_assistant", description="Who is proposing")
    classification_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Classification result from AI (domain_id, aspect_id, confidence)"
    )


class MCPProposeResponse(BaseModel):
    """Response from propose operation."""
    result: str
    proposal_id: Optional[str] = None
    decision_id: Optional[str] = None
    validation_status: Optional[str] = None
    advisory_notes: Optional[List[str]] = None
    blocking_reasons: Optional[List[str]] = None
    error: Optional[str] = None


@router.post(
    "/mcp/propose",
    response_model=MCPProposeResponse,
    summary="Propose a new decision (validate without storing)",
    description="""
    Validates a decision and creates a proposal for human review.
    Does NOT store the decision - human must approve via /mcp/store.
    """
)
async def mcp_propose(
    request: MCPProposeRequest,
    repository: DecisionRepository = Depends(get_repository),
) -> MCPProposeResponse:
    """Propose a decision for human review."""
    import uuid
    from datetime import datetime
    from ..use_cases.validate_decision import DecisionValidator
    from ..use_cases.quality_scoring import assess_quality

    decision = request.decision.copy()

    # Apply classification result if provided
    if request.classification_result:
        if "domain_id" in request.classification_result:
            decision["domain_id"] = request.classification_result["domain_id"]
        if "aspect_id" in request.classification_result:
            decision["aspect_id"] = request.classification_result["aspect_id"]

    # Generate IDs if not present
    if "decision_id" not in decision:
        decision["decision_id"] = str(uuid.uuid4())

    # Validate
    try:
        from ..use_cases.validate_decision import ValidationStatus
        validator = DecisionValidator()
        result = validator.validate(decision)

        if result.status != ValidationStatus.VALID:
            # Extract error messages from violations
            error_messages = [v.message for v in result.violations] if result.violations else []
            return MCPProposeResponse(
                result="INVALID",
                blocking_reasons=error_messages,
                error=error_messages[0] if error_messages else "Validation failed",
            )

        # Quality assessment
        quality = assess_quality(decision)

        # Generate proposal
        proposal_id = str(uuid.uuid4())

        return MCPProposeResponse(
            result="READY",
            proposal_id=proposal_id,
            decision_id=decision["decision_id"],
            validation_status="VALID",
            advisory_notes=[
                f"Quality score: {quality.overall_score}/100",
                "Decision is valid and ready to store.",
                "Call POST /mcp/store with human_confirmed=true to store.",
            ],
        )
    except Exception as e:
        return MCPProposeResponse(
            result="ERROR",
            error=str(e),
        )


class MCPStoreRequest(BaseModel):
    """Request to store a decision."""
    decision: Dict[str, Any] = Field(..., description="Decision record to store")
    human_confirmed: bool = Field(..., description="MUST be true - human has reviewed and approved")
    stored_by: str = Field(default="human_user", description="Who is storing (should be human)")


class MCPStoreResponse(BaseModel):
    """Response from store operation."""
    action: str
    reason: Optional[str] = None
    message: Optional[str] = None
    decision_id: Optional[str] = None
    decision_code: Optional[str] = None
    stored_at: Optional[str] = None


@router.post(
    "/mcp/store",
    response_model=MCPStoreResponse,
    summary="Store a decision (requires human confirmation)",
    description="""
    Stores a decision in MANTRA.

    IMPORTANT: human_confirmed MUST be true.
    This ensures a human has reviewed and approved the decision.
    AI assistants should NOT set human_confirmed=true automatically.
    """
)
async def mcp_store(
    request: MCPStoreRequest,
    repository: DecisionRepository = Depends(get_repository),
) -> MCPStoreResponse:
    """Store a decision with human confirmation."""
    if not request.human_confirmed:
        return MCPStoreResponse(
            action="REJECTED",
            reason="HUMAN_CONFIRMATION_REQUIRED",
            message=(
                "Cannot store decision without human confirmation. "
                "Set human_confirmed=true ONLY after the human user has reviewed "
                "and explicitly approved this decision. AI assistants must NOT "
                "set this flag automatically."
            ),
        )

    try:
        import uuid
        from ..domain.schema import Decision, DomainId, AspectId, Scope, BlastRadius

        dec = request.decision

        # Create Decision object (not DecisionCreate)
        decision_obj = Decision(
            decision_id=dec.get("decision_id") or str(uuid.uuid4()),
            domain_id=DomainId(dec.get("domain_id", "INT")),
            aspect_id=AspectId(dec.get("aspect_id", "F01")),
            statement=dec.get("statement", ""),
            rationale=dec.get("rationale", ""),
            version=dec.get("version", "1.0.0"),
            constraints=dec.get("constraints", []),
            invariants=dec.get("invariants", []),
            scope=Scope(dec.get("scope", "APPLICATION")),
            blast_radius=BlastRadius(dec.get("blast_radius", "LOW")),
            created_by=request.stored_by,
            created_at=datetime.utcnow(),
            related_decisions=dec.get("related_decisions", []),
            tags=dec.get("tags", []),
            tech_stack=dec.get("tech_stack", []),
            supersedes=dec.get("supersedes"),
        )

        # Store using repository
        result = await store_decision_async(
            decision_obj,
            request.stored_by,
            repository,
        )

        if result.result == StoreResult.STORED:
            return MCPStoreResponse(
                action="STORED",
                decision_id=result.decision_id,
                stored_at=result.stored_at.isoformat() if result.stored_at else datetime.utcnow().isoformat(),
            )
        else:
            return MCPStoreResponse(
                action="FAILED",
                reason=result.result.value,
                message=result.error_message,
            )
    except Exception as e:
        return MCPStoreResponse(
            action="ERROR",
            reason="EXCEPTION",
            message=str(e),
        )


class MCPTaskContextRequest(BaseModel):
    """Request for MICS task context."""
    intent: str = Field(..., description="What the user wants to do (e.g., 'deploy to production')")
    target: Optional[str] = Field(default=None, description="Target component/service")
    environment: Optional[str] = Field(default=None, description="Environment (dev/staging/production)")
    code_context: Optional[str] = Field(default=None, description="Current code context")
    token_budget: int = Field(default=4000, description="Max tokens for context")


class MCPTaskContextResponse(BaseModel):
    """Response with MICS task context."""
    agent: Optional[Dict[str, Any]] = None
    relevant_decisions: Optional[List[Dict[str, Any]]] = None
    checklist: Optional[List[str]] = None
    critical_rules: Optional[List[str]] = None
    context_prompt: Optional[str] = None
    token_count: Optional[int] = None
    error: Optional[str] = None


@router.post(
    "/mcp/task-context",
    response_model=MCPTaskContextResponse,
    summary="Get intelligent task context (MICS)",
    description="""
    Returns context-aware guidance for a specific task.

    MICS (MANTRA Intelligent Context System) analyzes the intent
    and returns:
    - Relevant agent profile (deployment, database, frontend, etc.)
    - Applicable decisions from MANTRA
    - Pre-flight checklist
    - Critical rules that must be followed

    This uses the 7-stage Context Assembly Pipeline:
    1. Intent Recognition - Identify task type
    2. Agent Loading - Load from YAML definitions
    3. Decision Retrieval - Get relevant decisions
    4. Constraint Extraction - Extract rules
    5. Codebase Context - Add file info
    6. Template Rendering - Build prompt
    7. Platform Adaptation - Format for target
    """
)
async def mcp_task_context(
    request: MCPTaskContextRequest,
    repository: DecisionRepository = Depends(get_repository),
) -> MCPTaskContextResponse:
    """
    Get MICS task context using 7-stage Context Assembly Pipeline.

    Uses MICSToolProvider with AgentLoader for:
    - YAML-based agent definitions (Universal Agent Format)
    - Actual decision retrieval from repository
    - Constraint extraction from both agents and decisions
    - Template rendering with context variables
    """
    import os

    try:
        # Import MICSToolProvider
        import sys
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from mcp.tools import MICSToolProvider

        # Initialize with repository and agents directory
        agents_dir = os.path.join(backend_dir, "agents")

        mics_provider = MICSToolProvider(
            repository=repository,
            agents_dir=agents_dir
        )

        # Call the full 7-stage pipeline
        result = await mics_provider.get_task_context(
            intent=request.intent,
            target=request.target,
            environment=request.environment,
            code_context=request.code_context,
            token_budget=request.token_budget,
            platform="claude-code"
        )

        # Extract task_context from result
        task_ctx = result.get("task_context", {})
        meta = result.get("meta", {})

        # Build response in expected format
        agent_info = task_ctx.get("agent", {})
        decisions = task_ctx.get("decisions", [])
        constraints = task_ctx.get("constraints", {})
        checklist_items = task_ctx.get("checklist", [])

        # Convert checklist to list of strings
        checklist_strings = []
        for item in checklist_items:
            if isinstance(item, dict):
                step = item.get("step", "")
                cmd = item.get("command", "")
                if cmd:
                    checklist_strings.append(f"{step} (`{cmd}`)")
                else:
                    checklist_strings.append(step)
            else:
                checklist_strings.append(str(item))

        # Extract critical rules (blocking constraints/prohibitions)
        critical_rules = constraints.get("prohibitions", [])
        critical_rules.extend(constraints.get("requirements", [])[:3])  # Add top 3 requirements

        return MCPTaskContextResponse(
            agent={
                "id": agent_info.get("id", "backend-agent"),
                "name": agent_info.get("name", "Backend Agent"),
                "version": agent_info.get("version", "1.0.0"),
                "category": agent_info.get("category", "general"),
                "confidence": agent_info.get("confidence", 0.5),
            },
            relevant_decisions=decisions if decisions else None,
            checklist=checklist_strings if checklist_strings else None,
            critical_rules=critical_rules if critical_rules else None,
            context_prompt=task_ctx.get("prompt"),
            token_count=meta.get("token_estimate", 0),
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"MICS task context error: {e}")

        # Fallback to simple response on error
        return MCPTaskContextResponse(
            agent={"name": "Backend Agent", "id": "backend-agent"},
            error=f"MICS pipeline error: {str(e)}",
        )


# =============================================================================
# MICS Additional MCP Endpoints
# =============================================================================

class MCPListAgentsRequest(BaseModel):
    """Request to list available agents."""
    category: Optional[str] = Field(
        default=None,
        description="Filter by category: infrastructure, development, quality, workflow, all"
    )


class MCPListAgentsResponse(BaseModel):
    """Response with list of agents."""
    agents: List[Dict[str, Any]]
    total: int
    category_filter: str


@router.post(
    "/mcp/list-agents",
    response_model=MCPListAgentsResponse,
    summary="List all available task agents (MICS)",
    description="""
    List all available task agents for MICS context assembly.

    Use this to discover what specialized agents are available
    for different task types (deployment, database, backend, frontend, security).
    """
)
async def mcp_list_agents(
    request: MCPListAgentsRequest,
    repository: DecisionRepository = Depends(get_repository),
) -> MCPListAgentsResponse:
    """List available MICS agents."""
    import os

    try:
        import sys
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from mcp.tools import MICSToolProvider

        agents_dir = os.path.join(backend_dir, "agents")

        provider = MICSToolProvider(repository=repository, agents_dir=agents_dir)
        result = await provider.list_agents(category=request.category)

        return MCPListAgentsResponse(
            agents=result.get("agents", []),
            total=result.get("total", 0),
            category_filter=result.get("category_filter", "all"),
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"MICS list agents error: {e}")
        return MCPListAgentsResponse(agents=[], total=0, category_filter="all")


class MCPChecklistRequest(BaseModel):
    """Request for task checklist."""
    task_type: str = Field(..., description="Type of task (deployment, database, backend, frontend, security)")
    target: Optional[str] = Field(default=None, description="Target system")
    phase: str = Field(default="all", description="Phase: pre_deploy, deploy, post_deploy, all")


class MCPChecklistResponse(BaseModel):
    """Response with task checklist."""
    task_type: str
    agent: Dict[str, Any]
    target: Optional[str]
    phase: str
    checklist: Dict[str, List[Dict[str, Any]]]
    critical_rules: List[str]
    total_steps: int
    error: Optional[str] = None


@router.post(
    "/mcp/checklist",
    response_model=MCPChecklistResponse,
    summary="Get checklist for a task type (MICS)",
    description="""
    Get the step-by-step checklist for a specific task type.

    Returns commands that should be executed for:
    - pre_deploy: Steps before deployment
    - deploy: Deployment steps
    - post_deploy: Verification steps after deployment
    """
)
async def mcp_get_checklist(
    request: MCPChecklistRequest,
    repository: DecisionRepository = Depends(get_repository),
) -> MCPChecklistResponse:
    """Get MICS task checklist."""
    import os

    try:
        import sys
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from mcp.tools import MICSToolProvider

        agents_dir = os.path.join(backend_dir, "agents")

        provider = MICSToolProvider(repository=repository, agents_dir=agents_dir)
        result = await provider.get_checklist_for_task(
            task_type=request.task_type,
            target=request.target,
            phase=request.phase
        )

        if "error" in result:
            return MCPChecklistResponse(
                task_type=request.task_type,
                agent={},
                target=request.target,
                phase=request.phase,
                checklist={},
                critical_rules=[],
                total_steps=0,
                error=result["error"]
            )

        return MCPChecklistResponse(
            task_type=result.get("task_type", request.task_type),
            agent=result.get("agent", {}),
            target=result.get("target"),
            phase=result.get("phase", "all"),
            checklist=result.get("checklist", {}),
            critical_rules=result.get("critical_rules", []),
            total_steps=result.get("total_steps", 0),
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"MICS checklist error: {e}")
        return MCPChecklistResponse(
            task_type=request.task_type,
            agent={},
            target=request.target,
            phase=request.phase,
            checklist={},
            critical_rules=[],
            total_steps=0,
            error=str(e)
        )


class MCPValidateActionsRequest(BaseModel):
    """Request to validate proposed actions."""
    task_type: str = Field(..., description="Type of task (DEPLOYMENT, DEVELOPMENT, DATABASE, etc.)")
    proposed_actions: List[str] = Field(..., description="List of actions to validate")


class MCPValidateActionsResponse(BaseModel):
    """Response with validation result."""
    valid: bool
    task_type: str
    actions_checked: int
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    suggestions: List[str]
    error: Optional[str] = None


@router.post(
    "/mcp/validate-actions",
    response_model=MCPValidateActionsResponse,
    summary="Validate proposed actions against MANTRA decisions (MICS)",
    description="""
    Validate proposed actions against MANTRA decisions and constraints.

    Before executing significant actions, use this to check if they
    comply with established decisions and constraints.

    Returns:
    - valid: Whether the actions are allowed
    - violations: BLOCKING issues that must be fixed
    - warnings: Advisory notes
    - suggestions: How to make actions compliant
    """
)
async def mcp_validate_actions(
    request: MCPValidateActionsRequest,
    repository: DecisionRepository = Depends(get_repository),
) -> MCPValidateActionsResponse:
    """Validate actions against MICS rules."""
    import os
    import sys

    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from mcp.tools import MICSToolProvider

        agents_dir = os.path.join(backend_dir, "agents")

        provider = MICSToolProvider(repository=repository, agents_dir=agents_dir)
        result = await provider.validate_actions(
            task_type=request.task_type,
            proposed_actions=request.proposed_actions
        )

        return MCPValidateActionsResponse(
            valid=result.get("valid", True),
            task_type=result.get("task_type", request.task_type),
            actions_checked=result.get("actions_checked", len(request.proposed_actions)),
            violations=result.get("violations", []),
            warnings=result.get("warnings", []),
            suggestions=result.get("suggestions", []),
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"MICS validate actions error: {e}")
        return MCPValidateActionsResponse(
            valid=True,
            task_type=request.task_type,
            actions_checked=0,
            violations=[],
            warnings=[],
            suggestions=[],
            error=str(e)
        )


class MCPTaskContextWithBudgetRequest(BaseModel):
    """Request for task context with token budget management."""
    intent: str = Field(..., description="What the user wants to do")
    target: Optional[str] = Field(default=None, description="Target component/service")
    environment: Optional[str] = Field(default=None, description="Environment")
    code_context: Optional[str] = Field(default=None, description="Current code context")
    token_budget: int = Field(default=4000, description="Max tokens for context")
    platform: str = Field(default="claude-code", description="Target platform")


class MCPTaskContextWithBudgetResponse(BaseModel):
    """Response with position-optimized task context."""
    task_context: Dict[str, Any]
    meta: Dict[str, Any]
    budget_summary: Dict[str, Any]
    hints: Dict[str, Any]
    error: Optional[str] = None


@router.post(
    "/mcp/task-context-v2",
    response_model=MCPTaskContextWithBudgetResponse,
    summary="Get task context with token budget management (MICS v2)",
    description="""
    Enhanced version of task-context with proper token budget management.

    Features:
    - TIER 1 (CRITICAL): Agent identity, Layer 0, PROHIBITIONS -> START position
    - TIER 2 (IMPORTANT): Decisions, Requirements, Checklist -> NEAR_START position
    - TIER 3 (SUPPLEMENTARY): Codebase context, Hints -> END position
    - TIER 4 (REFERENCE): On-demand details

    Position optimization avoids "lost in the middle" problem.
    """
)
async def mcp_task_context_v2(
    request: MCPTaskContextWithBudgetRequest,
    repository: DecisionRepository = Depends(get_repository),
) -> MCPTaskContextWithBudgetResponse:
    """Get MICS task context with token budget management."""
    import os
    import sys

    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from mcp.tools import MICSToolProvider

        agents_dir = os.path.join(backend_dir, "agents")

        provider = MICSToolProvider(repository=repository, agents_dir=agents_dir)
        result = await provider.get_task_context_with_budget(
            intent=request.intent,
            target=request.target,
            environment=request.environment,
            code_context=request.code_context,
            token_budget=request.token_budget,
            platform=request.platform
        )

        if "error" in result:
            return MCPTaskContextWithBudgetResponse(
                task_context={},
                meta={},
                budget_summary={},
                hints={},
                error=result["error"]
            )

        return MCPTaskContextWithBudgetResponse(
            task_context=result.get("task_context", {}),
            meta=result.get("meta", {}),
            budget_summary=result.get("budget_summary", {}),
            hints=result.get("hints", {}),
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"MICS task context v2 error: {e}")
        return MCPTaskContextWithBudgetResponse(
            task_context={},
            meta={},
            budget_summary={},
            hints={},
            error=str(e)
        )
