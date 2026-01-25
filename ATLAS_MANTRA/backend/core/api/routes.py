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
)
from ..use_cases.store_decision import store_decision, StoreResult
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


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["decisions"])

# Dependency injection for repository
_repository: Optional[DecisionRepository] = None


def get_repository() -> DecisionRepository:
    """Get repository instance (singleton for now)."""
    global _repository
    if _repository is None:
        _repository = InMemoryDecisionRepository()
    return _repository


def set_repository(repo: DecisionRepository) -> None:
    """Set repository instance (for testing/production switch)."""
    global _repository
    _repository = repo


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
    - Format: DEC-G{group}-{feature}-{seq}-v{version}
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
    )

    # Store decision
    result = store_decision(decision, request.stored_by, repository)

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
    result = list_decisions(repository, limit=limit, offset=offset)

    if result.result == ReadResult.ERROR:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message
        )

    # Structural filter only - by group_id
    decisions = result.decisions
    if group_id:
        decisions = [d for d in decisions if d.group_id == group_id]

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
    result = get_decision(decision_id, repository)

    if result.result == ReadResult.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found"
        )
    elif result.result == ReadResult.ERROR:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message
        )

    d = result.decision
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
    grouped = group_decisions_by_group_feature(repository)
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

    # Merge skipped_rules from validation result
    if result.validation_result:
        skipped_rules = list(set(skipped_rules + result.validation_result.skipped_rules))

    return ProposeResponse(
        result=result.result.value,
        proposal_id=result.proposal_id,
        decision_id=result.decision_id,
        decision=decision_dict,
        validation_status=result.validation_result.status.value if result.validation_result else "UNKNOWN",
        violations=violations,
        advisory_notes=result.advisory_notes,
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

    # Verify challenged decision exists
    challenged = repository.find_by_id(decision_id)
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
    )

    # Store the new decision
    result = store_decision(new_decision, request.challenger, repository)

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
