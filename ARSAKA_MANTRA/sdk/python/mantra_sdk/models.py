"""
MANTRA SDK Data Models

Pydantic models for MANTRA API requests and responses.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Enums
# ============================================================================


class DomainId(str, Enum):
    """Decision domain identifiers - the 4 domains of MANTRA taxonomy."""
    INT = "INT"   # Intent & Direction
    ARCH = "ARCH"  # Architecture
    CTL = "CTL"   # Control & Policy
    EVO = "EVO"   # Evolution


class AspectId(str, Enum):
    """Decision aspect identifiers - the 16 aspects across domains."""
    A01 = "A01"  # Vision & Strategy
    A02 = "A02"  # Objectives & Goals
    A03 = "A03"  # Scope Definition
    A04 = "A04"  # Priority Framework
    A05 = "A05"  # System Design
    A06 = "A06"  # Integration Patterns
    A07 = "A07"  # Technology Choices
    A08 = "A08"  # Data Architecture
    A09 = "A09"  # Process Rules
    A10 = "A10"  # Quality Standards
    A11 = "A11"  # Security Policies
    A12 = "A12"  # Compliance Rules
    A13 = "A13"  # Change Management
    A14 = "A14"  # Versioning Strategy
    A15 = "A15"  # Migration Paths
    A16 = "A16"  # Deprecation Rules


class ValidationStatus(str, Enum):
    """Validation result status."""
    VALID = "VALID"
    INVALID = "INVALID"
    ADVISORY = "ADVISORY"


class HealthStatus(str, Enum):
    """Decision health status."""
    HEALTHY = "HEALTHY"
    GOOD = "GOOD"
    WARNING = "WARNING"
    POOR = "POOR"
    CRITICAL = "CRITICAL"
    NEW = "NEW"


# ============================================================================
# Decision Models
# ============================================================================


class AuthorshipMetadata(BaseModel):
    """Metadata about decision authorship (required for LAW compliance)."""
    authored_by: str = Field(..., description="Human author identifier")
    authored_at: datetime = Field(default_factory=datetime.utcnow)
    organization: Optional[str] = None
    role: Optional[str] = None


class DecisionCreate(BaseModel):
    """Model for creating a new decision (proposal)."""
    code: str = Field(..., description="Decision code (e.g., MANTRA-INT-001)")
    domain_id: DomainId
    aspect_id: AspectId
    statement: str = Field(..., description="The decision statement")
    rationale: str = Field(..., description="Why this decision was made")
    scope: list[str] = Field(default_factory=list, description="Scope paths")
    tags: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list, description="Decision IDs this depends on")
    conflicts_with: list[str] = Field(default_factory=list, description="Decision IDs this conflicts with")
    supersedes: Optional[str] = Field(None, description="Decision ID this supersedes")
    metadata: dict[str, Any] = Field(default_factory=dict)
    authorship: AuthorshipMetadata


class Decision(BaseModel):
    """Full decision model as returned from the API."""
    id: str
    code: str
    domain_id: DomainId
    aspect_id: AspectId
    statement: str
    rationale: str
    scope: list[str]
    tags: list[str]
    depends_on: list[str]
    conflicts_with: list[str]
    supersedes: Optional[str]
    superseded_by: Optional[str]
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    authorship: AuthorshipMetadata
    metadata: dict[str, Any]
    approval_status: str
    health_status: Optional[HealthStatus] = None


# ============================================================================
# Validation Models
# ============================================================================


class ValidationViolation(BaseModel):
    """A validation rule violation."""
    rule_id: str
    severity: str  # HARD or SOFT
    message: str
    field: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of decision validation."""
    status: ValidationStatus
    violations: list[ValidationViolation]
    skipped_rules: list[str]
    advisory_notes: list[str]
    validated_at: datetime
    schema_version: str


class Gate1Result(BaseModel):
    """Gate 1 (Deterministic) validation result."""
    passed: bool
    violations: list[ValidationViolation]
    rule_count: int


class Gate2Result(BaseModel):
    """Gate 2 (AI Heuristic) validation result."""
    passed: bool
    suggestions: list[str]
    confidence: float
    model_used: str


class Gate3Result(BaseModel):
    """Gate 3 (Human Approval) status."""
    required: bool
    pending: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class FullValidationResult(BaseModel):
    """Complete 3-Gate validation result."""
    gate1: Gate1Result
    gate2: Gate2Result
    gate3: Gate3Result
    overall_status: str
    can_proceed: bool


# ============================================================================
# Retrieval Models
# ============================================================================


class RetrievalMatch(BaseModel):
    """A single retrieval result."""
    decision_id: str
    decision_code: str
    statement: str
    confidence: float
    source: str  # keyword, semantic, trigger
    matched_by: list[str]


class RetrievalResult(BaseModel):
    """Context-aware retrieval result."""
    results: list[RetrievalMatch]
    total_count: int
    token_count: int
    execution_time_ms: float
    from_cache: bool
    triggered_by: list[str]
    suggestions: list[str]


class TriggerMatch(BaseModel):
    """A matched trigger."""
    trigger_id: str
    name: str
    type: str
    priority: int
    matched_patterns: list[str]
    decision_ids: list[str]


class TriggerCheckResult(BaseModel):
    """Trigger check result."""
    triggered: bool
    triggers: list[TriggerMatch]
    decision_ids: list[str]


# ============================================================================
# Document Generation Models
# ============================================================================


class DocumentType(BaseModel):
    """Available document type."""
    type: str
    name: str
    description: str
    phase: str
    primary_audience: str


class DocumentGenerateRequest(BaseModel):
    """Request to generate a document."""
    doc_type: str
    title: Optional[str] = None
    company_name: Optional[str] = None
    domain_filter: Optional[str] = None
    scope_filter: Optional[str] = None
    max_decisions: int = 100
    include_toc: bool = True
    include_metadata: bool = True


class GeneratedDocument(BaseModel):
    """Generated document."""
    title: str
    content: str
    doc_type: str
    word_count: int
    section_count: int
    decision_count: int
    source_decisions: list[str]
    generated_at: datetime


# ============================================================================
# Analytics Models
# ============================================================================


class AnalyticsSummary(BaseModel):
    """Usage analytics summary."""
    total_decisions_tracked: int
    total_events: int
    total_feedback: int
    hot_decisions_count: int
    stale_decisions_count: int
    problematic_decisions_count: int


class HealthDistribution(BaseModel):
    """Health status distribution."""
    distribution: dict[str, int]
    total: int


class DecisionStats(BaseModel):
    """Statistics for a single decision."""
    decision_id: str
    view_count: int
    apply_count: int
    positive_feedback: int
    negative_feedback: int
    last_accessed: Optional[datetime]
    health_status: HealthStatus
