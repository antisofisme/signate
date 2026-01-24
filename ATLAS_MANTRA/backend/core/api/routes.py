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
    """
    decision_id: str
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
    # Parse authorship metadata if provided
    authorship = None
    if request.authorship_metadata:
        try:
            authorship = AuthorshipMetadata(**request.authorship_metadata)
        except Exception:
            # Invalid metadata format - proceed without it
            pass

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
        advisory_notes=result.advisory_notes,
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

    # Create Decision from request
    # Per MANTRA-SPEC-001-AMENDMENT-001: NO status field
    # Evolution via version + supersedes only
    decision = Decision(
        decision_id=str(uuid.uuid4()),
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
        # STORE_ERROR = technical/IO failure (500 Internal Server Error)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT
            if result.result == StoreResult.ALREADY_EXISTS
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                group_id=d.group_id.value,
                feature_id=d.feature_id.value,
                statement=d.statement,
                rationale=d.rationale,
                constraints=[c.model_dump() for c in d.constraints],
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
        group_id=d.group_id.value,
        feature_id=d.feature_id.value,
        statement=d.statement,
        rationale=d.rationale,
        constraints=[c.model_dump() for c in d.constraints],
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
