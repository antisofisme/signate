"""
MANTRA-SCHEMA-003: Enhanced Decision Schema v3 (Fully Integrated)

This module provides the comprehensive enhanced JSON Schema for the Decision Matrix.
Per MANTRA-LAW-001, this schema is constitutional and immutable once stored.

DESIGN GOALS:
1. Score 9.0+/10 for Knowledge, Guidance, Search, and Governance dimensions
2. Address ALL gaps identified in multi-perspective analysis
3. Remain implementable and backward compatible
4. Support auto-inference for new fields

KEY ENHANCEMENTS over v2:
- Phase 1: Knowledge Consumption, Context Triggers, Code Artifacts, Enhanced Search/RAG
- Phase 2: Exception Model, Causality Context, Implementation Status, Stability
- Phase 3: Persisted Impact Analysis, Usage Analytics

CROSS-AGENT IMPROVEMENTS (from schema_v3_enhanced.py):
- Phase A: Amendment Model (immutability resolution), Constraint Relations (conflict detection),
           Stale Reference Detection, Graph Integrity Hooks
- Phase B: Structured Implementation Steps, Structured Blockers, Rollback Records,
           Embedding Lifecycle, Team Adoption Tracking, Notification Infrastructure
- Phase C: Disambiguation Support, Query Processing Hints, Expected Coverage Registry,
           Learning Paths, Enhanced Implementation Guidance, Enhanced Stability

MIGRATION PATH:
- All v2 fields remain with same semantics
- New fields have sensible defaults or are Optional
- Auto-inference functions populate fields from existing content
- Database migration adds columns with NULL defaults
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
from datetime import datetime, date
import uuid
import re
import hashlib

# Import all v2 types for backward compatibility
from .schema_base import (
    # Enums
    DomainId, AspectId, Scope, BlastRadius, ConstraintType, RelationType,
    SectionType, ChangeType, StakeholderRole, ComplianceFramework, ApprovalStatus,
    AreaTag,
    # Matrix
    DOMAIN_ASPECT_MATRIX, DOMAIN_LABELS, ASPECT_LABELS, is_aspect_compatible,
    # Sub-models
    Relation, ContentSection, Stakeholder, ApprovalRecord, ComplianceReference,
    TemporalValidity, QualityMetadata, ImplementationGuidance,
    # Migration helpers
    DATABASE_INDEXES, VALIDATION_RULES,
)

# Import all enhanced models from schema_v3_enhanced.py (Cross-Agent Improvements)
from .schema_v3_enhanced import (
    # Phase A - Enums (LAW-compliant - EnrichmentType replaces AmendmentType)
    EnrichmentType, ConflictStatus, ConflictRelationType, NotificationChannel,
    NotificationTrigger, BlockerCategory, BlockerSeverity, EmbeddingStatus,
    AdoptionStatus, CoverageImportance,
    # Phase A - Metadata Enrichment (LAW §10.7 compliant - replaces DecisionAmendment)
    MetadataEnrichment, ENRICHABLE_FIELDS, IMMUTABLE_FIELDS,
    # Backward compatibility alias
    DecisionAmendment,  # Alias for MetadataEnrichment (deprecated)
    # Phase A - Constraint Relations
    ConstraintRelation, ConflictSummary,
    # Phase A - Stale Reference Detection
    StaleReferenceWarning,
    # Phase B - Structured Implementation
    ImplementationStep, Blocker, RollbackStep, RollbackRecord,
    # Phase B - Embedding Lifecycle
    EmbeddingMetadata,
    # Phase B - Team Adoption
    TeamAdoption, AdoptionTarget, AdoptionSnapshot,
    # Phase B - Notification Infrastructure
    NotificationSubscription, EscalationLevel, EscalationPath, NotificationRecord,
    # Phase C - Disambiguation (with AI Safeguards per §6.5)
    DisambiguationSupport, QueryProcessingHints,
    # Phase C - Coverage Registry
    ExpectedCoverage, CoverageGap,
    # Phase C - Learning Path
    LearningPathCheckpoint, LearningPath, LearnerProgress,
    # Phase C - Enhanced Models
    EnhancedImplementationGuidance, EnhancedStabilityMetadata, FullyEnhancedConstraint,
    # Phase C - Structured Summary
    SummaryLevel, StructuredSummary,
    # Utility functions
    generate_content_hash, create_metadata_enrichment, create_blocker, create_team_adoption,
    create_amendment,  # Deprecated - use create_metadata_enrichment
    # Section 17 - Content Length & Writing Guidelines (Verbosity Control)
    ContentLengthConfig, WritingStyle, WritingGuideline, WRITING_GUIDELINES,
    validate_content_length, check_anti_patterns, get_writing_tips,
    # Section 18 - Content Validators
    validate_statement, validate_rationale, validate_constraint_statement, validate_invariant,
    # Section 19 - Validation Classification System
    ValidationType, FieldSource, ValidationRule, FieldSpec,
    VALIDATION_RULES, FIELD_PROMPTS,
    get_validation_rules, get_rules_by_type, count_rules_by_type, get_field_prompt,
)


# ============================================================================
# SECTION 1: Phase 1 - New Enumerations
# ============================================================================

class AudienceLevel(str, Enum):
    """Target audience skill level."""
    BEGINNER = "BEGINNER"       # New to the concept
    INTERMEDIATE = "INTERMEDIATE"  # Familiar with basics
    ADVANCED = "ADVANCED"       # Deep understanding required
    EXPERT = "EXPERT"           # Subject matter expert level


class TriggerEventType(str, Enum):
    """Types of events that can trigger a decision."""
    INCIDENT = "incident"               # Production incident
    AUDIT = "audit"                     # Audit finding
    SECURITY_FINDING = "security_finding"  # Security vulnerability
    PERFORMANCE_ISSUE = "performance_issue"  # Performance problem
    TECH_DEBT = "tech_debt"             # Technical debt cleanup
    COMPLIANCE = "compliance"           # Compliance requirement
    MARKET_CHANGE = "market_change"     # External market/tech change
    STRATEGIC = "strategic"             # Strategic initiative
    USER_FEEDBACK = "user_feedback"     # User/customer feedback
    TEAM_REQUEST = "team_request"       # Internal team request


class StabilityStatus(str, Enum):
    """Stability/maturity status of a decision."""
    EXPERIMENTAL = "experimental"   # New, untested
    ALPHA = "alpha"                 # Early adopter stage
    BETA = "beta"                   # Wider testing
    STABLE = "stable"               # Production ready
    DEPRECATED = "deprecated"       # Will be removed
    ARCHIVED = "archived"           # Historical only


class ImplementationStatusType(str, Enum):
    """Implementation progress status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETED = "completed"
    VERIFIED = "verified"
    REVERTED = "reverted"


class ExceptionScope(str, Enum):
    """Scope of an exception request."""
    THIS_PR = "this_pr"             # Single PR only
    THIS_SERVICE = "this_service"   # Single service
    THIS_SPRINT = "this_sprint"     # Current sprint
    PERMANENT = "permanent"         # Permanent exception


class ExceptionStatus(str, Enum):
    """Status of a granted exception."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class CodeArtifactType(str, Enum):
    """Types of code artifacts."""
    PR = "pr"
    COMMIT = "commit"
    ISSUE = "issue"
    BRANCH = "branch"
    FILE = "file"
    DIRECTORY = "directory"


class RiskLevel(str, Enum):
    """Impact analysis risk levels."""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# SECTION 2: Phase 1 - Knowledge Consumption & Context
# ============================================================================

class KnowledgeConsumption(BaseModel):
    """
    v3: Knowledge consumption metadata.

    Defines WHO should read this decision and HOW to consume it.
    Enables better knowledge base functionality.
    """
    # Target audience
    target_roles: List[str] = Field(
        default_factory=list,
        description="Roles that should follow: ['backend_dev', 'frontend_dev', 'devops', 'architect', 'tech_lead']"
    )
    audience_level: Optional[AudienceLevel] = Field(
        default=None,
        description="Required skill level to understand"
    )

    # Learning context
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="What will be learned after reading this decision"
    )
    prerequisites_knowledge: List[str] = Field(
        default_factory=list,
        description="Knowledge assumed to be already known"
    )
    prerequisite_decisions: List[str] = Field(
        default_factory=list,
        description="Decision IDs that should be read first"
    )

    # Consumption hints
    reading_time_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description="Estimated reading time (auto-calculated from token count)"
    )

    class Config:
        extra = "forbid"


class ContextTrigger(BaseModel):
    """
    v3: Context trigger for when a decision applies.

    Enables auto-detection of applicable decisions based on context.
    """
    trigger_id: str = Field(..., description="Unique ID: CTX-001")
    condition: str = Field(..., description="Human-readable condition")
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that trigger applicability"
    )
    file_patterns: List[str] = Field(
        default_factory=list,
        description="Glob patterns: ['*.tsx', 'src/components/**']"
    )

    class Config:
        extra = "forbid"


class ApplicabilityContext(BaseModel):
    """
    v3: Context for when decision applies or doesn't apply.

    Transforms passive decisions into active guidance.
    """
    applies_when: List[ContextTrigger] = Field(
        default_factory=list,
        description="Conditions when this decision applies"
    )
    does_not_apply_when: List[str] = Field(
        default_factory=list,
        description="Explicit exclusions"
    )
    auto_detect: bool = Field(
        default=False,
        description="Whether to auto-detect from file context"
    )

    class Config:
        extra = "forbid"


class CodeArtifact(BaseModel):
    """
    v3: Link to implementation artifact.

    Enables traceability between decisions and code.
    """
    artifact_type: CodeArtifactType = Field(..., description="Type of artifact")
    repository: str = Field(..., description="Repository: 'org/repo' or 'internal'")
    reference: str = Field(..., description="PR #123, commit SHA, issue #456, etc.")
    url: Optional[str] = Field(default=None, description="Full URL if external")
    status: Optional[str] = Field(
        default=None,
        description="open | merged | closed | active"
    )
    linked_at: datetime = Field(default_factory=datetime.utcnow)
    linked_by: Optional[str] = Field(default=None, description="Who linked this")

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 3: Phase 1 - Enhanced Search & RAG Metadata
# ============================================================================

class SemanticExpansion(BaseModel):
    """
    v3: Conceptual expansion for better retrieval.

    Enables finding decisions via related concepts.
    """
    related_concepts: List[str] = Field(
        default_factory=list,
        description="Related concepts: microservices -> ['distributed systems', 'service mesh']"
    )
    parent_concepts: List[str] = Field(
        default_factory=list,
        description="Parent concepts: ['software architecture', 'system design']"
    )
    child_concepts: List[str] = Field(
        default_factory=list,
        description="Child concepts: ['API gateway', 'service discovery']"
    )
    synonyms: List[str] = Field(
        default_factory=list,
        description="Synonyms: feature folder -> feature-based, feature-sliced"
    )

    class Config:
        extra = "forbid"


class IntentBasedQuestions(BaseModel):
    """
    v3: Questions categorized by intent for better RAG matching.

    Replaces flat question_variants with structured intent types.
    """
    how_questions: List[str] = Field(
        default_factory=list,
        description="Procedural: 'How do I...?'"
    )
    why_questions: List[str] = Field(
        default_factory=list,
        description="Reasoning: 'Why do we...?'"
    )
    what_questions: List[str] = Field(
        default_factory=list,
        description="Definitional: 'What is...?'"
    )
    when_questions: List[str] = Field(
        default_factory=list,
        description="Conditional: 'When should I...?'"
    )
    negative_questions: List[str] = Field(
        default_factory=list,
        description="What this decision does NOT answer"
    )

    class Config:
        extra = "forbid"


class EnhancedSearchMetadata(BaseModel):
    """
    v3: Enhanced search metadata with semantic expansion.

    Improves discoverability and retrieval precision.
    """
    # Existing v2 fields
    aliases: List[str] = Field(
        default_factory=list,
        description="Alternative names/abbreviations"
    )
    search_keywords: List[str] = Field(
        default_factory=list,
        description="Additional search keywords not in content"
    )

    # v3: Intent-based questions (replaces flat question_variants)
    questions: Optional[IntentBasedQuestions] = Field(
        default=None,
        description="Questions categorized by intent"
    )

    # v3: Semantic expansion
    semantic_expansion: Optional[SemanticExpansion] = Field(
        default=None,
        description="Conceptual expansion for better retrieval"
    )

    # v3: Negative keywords for precision
    negative_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that should NOT match this decision"
    )

    # v3: Retrieval boost
    retrieval_boost: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Priority multiplier for frequently used decisions"
    )

    # Legacy field for backward compatibility
    question_variants: List[str] = Field(
        default_factory=list,
        description="DEPRECATED: Use 'questions' instead"
    )

    class Config:
        extra = "forbid"


class RAGOptimization(BaseModel):
    """
    v3: RAG-specific optimization metadata.

    Improves retrieval quality for AI-assisted workflows.
    """
    # Context summary (~100-150 words, longer than micro_summary)
    context_summary: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="RAG-optimized summary ~100-150 words"
    )

    # Standalone answer
    standalone_answer: Optional[str] = Field(
        default=None,
        description="Answer that can be returned directly without context"
    )

    # Citation format
    citation_format: Optional[str] = Field(
        default=None,
        description="Citation format: '[ARCH-A06-001] Feature-Based Structure'"
    )

    # Chunking guidance
    semantic_boundaries: List[int] = Field(
        default_factory=list,
        description="Line numbers for natural chunk breaks"
    )
    recommended_chunk_size: int = Field(
        default=512,
        description="Recommended tokens per chunk"
    )

    # Multi-vector hints
    separate_embeddings: bool = Field(
        default=False,
        description="Whether to create separate embeddings per aspect"
    )

    class Config:
        extra = "forbid"


class EnhancedLLMOptimization(BaseModel):
    """
    v3: Enhanced LLM optimization with RAG support.

    Pre-computed data for efficient AI context injection.
    """
    # Existing v2 fields
    embedding_text: Optional[str] = Field(
        default=None,
        description="Text used for vector embedding (optimized for search)"
    )
    total_token_count: Optional[int] = Field(
        default=None,
        description="Total token count for all content"
    )
    micro_summary: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Ultra-short summary (~20 words) for token-limited contexts"
    )
    prompt_hints: List[str] = Field(
        default_factory=list,
        description="Hints for LLM on how to apply this decision"
    )
    keywords_for_rag: List[str] = Field(
        default_factory=list,
        description="Keywords optimized for RAG retrieval"
    )

    # v3: Embedding versioning
    embedding_model: Optional[str] = Field(
        default=None,
        description="Model used: 'text-embedding-3-large'"
    )
    embedding_generated_at: Optional[datetime] = Field(
        default=None,
        description="When embedding was generated"
    )

    # v3: RAG optimization
    rag: Optional[RAGOptimization] = Field(
        default=None,
        description="RAG-specific optimization"
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 4: Phase 2 - Exception Model & Enforcement
# ============================================================================

class ExceptionRequest(BaseModel):
    """
    v3: Structured exception request.

    Enables formal exception process for constraints.
    """
    request_id: str = Field(..., description="Unique ID: EXC-001")
    constraint_id: str = Field(..., description="Constraint requesting exception for")
    requestor: str = Field(..., description="Who is requesting")
    requestor_email: Optional[str] = Field(default=None)

    # Justification
    justification: str = Field(..., description="Why exception is needed")
    scope: ExceptionScope = Field(..., description="Scope of exception")
    duration_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Duration in days (null = permanent)"
    )

    # Analysis
    alternatives_considered: List[str] = Field(default_factory=list)
    risk_assessment: Optional[str] = Field(default=None)
    mitigation_plan: Optional[str] = Field(default=None)

    requested_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        extra = "forbid"


class GrantedException(BaseModel):
    """
    v3: Granted exception with tracking.

    Tracks approved exceptions and their validity.
    """
    exception_id: str = Field(..., description="Unique ID")
    request: ExceptionRequest = Field(..., description="Original request")

    # Approval
    approved_by: str = Field(..., description="Who approved")
    approved_at: datetime = Field(default_factory=datetime.utcnow)
    approval_notes: Optional[str] = Field(default=None)

    # Validity
    expires_at: Optional[datetime] = Field(default=None)
    conditions: List[str] = Field(
        default_factory=list,
        description="Conditions that must be met"
    )

    # Status tracking
    status: ExceptionStatus = Field(default=ExceptionStatus.ACTIVE)
    revoked_at: Optional[datetime] = Field(default=None)
    revoked_by: Optional[str] = Field(default=None)
    revoke_reason: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"


class EnforcementStatus(BaseModel):
    """
    v3: Track actual enforcement status of a constraint.

    Bridges gap between defined rules and actual enforcement.
    """
    is_active_in_ci: bool = Field(default=False, description="Is this checked in CI?")
    ci_job_url: Optional[str] = Field(default=None, description="CI job URL")
    last_check_at: Optional[datetime] = Field(default=None)
    last_check_result: Optional[str] = Field(
        default=None,
        description="PASS | FAIL | ERROR"
    )
    violation_count_7d: int = Field(default=0)
    violation_count_30d: int = Field(default=0)
    exception_count_active: int = Field(default=0)

    class Config:
        extra = "forbid"


class EnhancedConstraint(BaseModel):
    """
    v3: Enhanced constraint with exception tracking and enforcement status.

    Extends v2 Constraint with governance features.
    """
    # Existing v2 fields
    constraint_id: str = Field(..., min_length=1, description="Unique ID like C-001")
    statement: str = Field(..., min_length=1, description="The constraint statement")
    type: ConstraintType = Field(..., description="Type of constraint")
    enforcement_level: Optional[str] = Field(
        default="STRICT",
        description="STRICT | ADVISORY | AUDIT"
    )
    automated_check: bool = Field(default=False)
    check_command: Optional[str] = Field(default=None)

    # v3: Enhanced exception handling
    exception_process: Optional[str] = Field(
        default=None,
        description="Text description (backward compat)"
    )
    exception_template: Optional[str] = Field(
        default=None,
        description="Template for exception request"
    )
    granted_exceptions: List[GrantedException] = Field(
        default_factory=list,
        description="Active exceptions for this constraint"
    )

    # v3: Enforcement tracking
    enforcement_status: Optional[EnforcementStatus] = Field(
        default=None,
        description="Actual enforcement status"
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 5: Phase 2 - Causality & Implementation Tracking
# ============================================================================

class TriggerEvent(BaseModel):
    """
    v3: Event that triggered this decision.

    Enables causality tracking - "why does this decision exist?"
    """
    event_type: TriggerEventType = Field(..., description="Type of trigger")
    event_id: Optional[str] = Field(
        default=None,
        description="External ID: JIRA-123, INCIDENT-456"
    )
    event_date: Optional[date] = Field(default=None)
    description: str = Field(..., description="What happened")
    severity: Optional[str] = Field(
        default=None,
        description="low | medium | high | critical"
    )

    # Links
    event_url: Optional[str] = Field(default=None)
    related_decisions: List[str] = Field(
        default_factory=list,
        description="Other decisions triggered by same event"
    )

    class Config:
        extra = "forbid"


class ImplementationStatus(BaseModel):
    """
    v3: Track implementation progress of a decision.

    Bridges gap between decision and actual implementation.
    """
    status: ImplementationStatusType = Field(
        default=ImplementationStatusType.NOT_STARTED
    )
    progress_percentage: int = Field(default=0, ge=0, le=100)
    completion_notes: Optional[str] = Field(default=None)

    # Tracking
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    verified_at: Optional[datetime] = Field(default=None)

    updated_by: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Verification
    verification_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from check_command or manual verification"
    )

    # Blockers
    blockers: List[str] = Field(
        default_factory=list,
        description="What is blocking implementation"
    )

    class Config:
        extra = "forbid"


class StabilityMetadata(BaseModel):
    """
    v3: Stability and maturity indicator.

    Helps users understand decision reliability.
    """
    stability_status: StabilityStatus = Field(default=StabilityStatus.STABLE)
    maturity_score: int = Field(default=50, ge=0, le=100)

    # Deprecation info
    deprecation_date: Optional[date] = Field(default=None)
    deprecation_reason: Optional[str] = Field(default=None)
    successor_id: Optional[str] = Field(
        default=None,
        description="Decision ID that replaces this one"
    )

    # Adoption metrics
    adoption_count: int = Field(
        default=0,
        description="Number of projects/teams adopting"
    )
    feedback_score: Optional[float] = Field(
        default=None,
        ge=1.0,
        le=5.0,
        description="Average feedback rating 1-5"
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 6: Phase 3 - Impact Analysis & Usage Analytics
# ============================================================================

class PersistedImpactAnalysis(BaseModel):
    """
    v3: Persisted impact analysis results.

    Caches expensive impact analysis for fast queries.
    """
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    analyzer_version: str = Field(default="1.0.0")

    # Risk assessment
    risk_score: int = Field(default=0, ge=0, le=100)
    risk_level: RiskLevel = Field(default=RiskLevel.MINIMAL)

    # Affected decisions
    affected_decision_ids: List[str] = Field(default_factory=list)
    affected_count: int = Field(default=0)

    # Dependency info
    dependency_depth: int = Field(default=0)
    breaking_change_count: int = Field(default=0)

    # Recommendations
    risk_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"


class UsageAnalytics(BaseModel):
    """
    v3: Usage analytics for optimization.

    Tracks how decision is used for future optimization.
    """
    # Retrieval stats
    retrieval_count: int = Field(default=0)
    successful_retrievals: int = Field(default=0)

    # Query patterns
    common_queries: List[str] = Field(
        default_factory=list,
        description="Queries that successfully find this"
    )
    failed_queries: List[str] = Field(
        default_factory=list,
        description="Queries that lead here but shouldn't"
    )

    # Last access
    last_accessed_at: Optional[datetime] = Field(default=None)
    last_accessed_by: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 7: Main Decision Model v3
# ============================================================================

class DecisionV3(BaseModel):
    """
    Decision record per MANTRA-SCHEMA-003 (v3)

    This is the enhanced core aggregate of ATLAS_MANTRA.
    Per MANTRA-LAW-001, stored decisions are ABSOLUTELY IMMUTABLE.

    v3 DESIGN PRINCIPLES:
    1. All v2 fields preserved with same semantics
    2. New fields are Optional with sensible defaults
    3. Auto-inference functions populate fields from content
    4. Full backward compatibility with v2

    NEW FIELD CATEGORIES (v3):
    - Knowledge: knowledge_consumption
    - Applicability: applicability
    - Traceability: code_artifacts
    - Causality: trigger_event
    - Progress: implementation_status
    - Stability: stability
    - Search: search_metadata (enhanced)
    - AI/LLM: llm_optimization (enhanced)
    - Impact: impact_analysis
    - Analytics: usage_analytics
    """

    # =========================================================================
    # Identity Fields (unchanged from v2)
    # =========================================================================

    decision_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Immutable UUID, primary key"
    )
    decision_code: Optional[str] = Field(
        default=None,
        description="Human-readable code (e.g., ARCH-A06-001-v1.0.0)"
    )

    # =========================================================================
    # Classification Fields (unchanged from v2)
    # =========================================================================

    domain_id: DomainId = Field(..., description="Domain classification")
    aspect_id: AspectId = Field(..., description="Aspect within domain")

    # =========================================================================
    # Content Fields - Layer A (unchanged from v2)
    # =========================================================================

    statement: str = Field(
        ...,
        min_length=1,
        description="What: The decision statement (10-200 words)"
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Why: The reasoning behind the decision (20-500 words)"
    )
    constraints: List[EnhancedConstraint] = Field(
        default_factory=list,
        description="Enforceable rules/requirements (v3 enhanced)"
    )
    invariants: List[str] = Field(
        default_factory=list,
        description="Things that must always be true"
    )

    # =========================================================================
    # Content Fields - Layer B (unchanged from v2)
    # =========================================================================

    detailed_content: Optional[str] = Field(
        default=None,
        description="Full specification in Markdown (unlimited length)"
    )
    sections: List[ContentSection] = Field(
        default_factory=list,
        description="Structured sections for detailed content"
    )
    content_summary: Optional[str] = Field(
        default=None,
        description="Auto-generated summary (~50-100 words)"
    )

    # =========================================================================
    # Core Metadata Fields (unchanged from v2)
    # =========================================================================

    scope: Scope = Field(..., description="Applicability scope")
    blast_radius: BlastRadius = Field(..., description="Impact level")
    version: str = Field(
        ...,
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
        description="Semantic version (X.Y.Z)"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Area tags: FE, BE, DB, INFRA, etc."
    )
    tech_stack: List[str] = Field(
        default_factory=list,
        description="Technologies: React, FastAPI, PostgreSQL, etc."
    )

    # =========================================================================
    # Authorship Fields (unchanged from v2)
    # =========================================================================

    created_by: Optional[str] = Field(
        default=None,
        description="Author identifier (human only per MANTRA-LAW-001)"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Creation timestamp"
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="Primary approver identifier"
    )
    approved_at: Optional[datetime] = Field(
        default=None,
        description="Approval timestamp"
    )

    # =========================================================================
    # Relation Fields (unchanged from v2)
    # =========================================================================

    supersedes: Optional[str] = Field(
        default=None,
        description="UUID of decision this one supersedes"
    )
    related_decisions: List[str] = Field(
        default_factory=list,
        description="DEPRECATED: Use 'relations' instead"
    )
    relations: List[Relation] = Field(
        default_factory=list,
        description="Typed relations with context"
    )

    # =========================================================================
    # v2: Temporal Validity (unchanged)
    # =========================================================================

    temporal_validity: Optional[TemporalValidity] = Field(
        default=None,
        description="Time-bounded validity and review schedule"
    )

    # =========================================================================
    # v2: Multi-Stakeholder Governance (unchanged)
    # =========================================================================

    stakeholders: List[Stakeholder] = Field(
        default_factory=list,
        description="People/teams involved in this decision"
    )
    approvals: List[ApprovalRecord] = Field(
        default_factory=list,
        description="Multi-approver workflow history"
    )
    approval_workflow: Optional[str] = Field(
        default=None,
        description="Workflow type: SINGLE, QUORUM, UNANIMOUS, HIERARCHICAL"
    )

    # =========================================================================
    # v2: Compliance Tracking (unchanged)
    # =========================================================================

    compliance_references: List[ComplianceReference] = Field(
        default_factory=list,
        description="Links to compliance requirements"
    )
    audit_trail_id: Optional[str] = Field(
        default=None,
        description="External audit trail reference"
    )

    # =========================================================================
    # v2: Versioning Enhancements (unchanged)
    # =========================================================================

    change_type: Optional[ChangeType] = Field(
        default=ChangeType.INITIAL,
        description="Type of change from previous version"
    )
    change_summary: Optional[str] = Field(
        default=None,
        description="Brief description of what changed"
    )
    migration_guide: Optional[str] = Field(
        default=None,
        description="How to migrate from superseded version"
    )
    breaking_changes: List[str] = Field(
        default_factory=list,
        description="List of breaking changes from previous version"
    )

    # =========================================================================
    # v2: Quality Metadata (unchanged)
    # =========================================================================

    quality_metadata: Optional[QualityMetadata] = Field(
        default=None,
        description="Quality scoring results (denormalized for queries)"
    )

    # =========================================================================
    # v2: Implementation Guidance (unchanged)
    # =========================================================================

    implementation_guidance: Optional[ImplementationGuidance] = Field(
        default=None,
        description="Guidance for adopting this decision"
    )
    anti_patterns: List[str] = Field(
        default_factory=list,
        description="What NOT to do (common mistakes)"
    )

    # =========================================================================
    # v2: Lineage Tracking (unchanged)
    # =========================================================================

    derived_from: List[str] = Field(
        default_factory=list,
        description="External sources this decision is based on (URLs, doc refs)"
    )
    influenced_decisions: List[str] = Field(
        default_factory=list,
        description="Decision IDs that cite this decision (denormalized)"
    )

    # =========================================================================
    # v3 Phase 1: Knowledge Consumption
    # =========================================================================

    knowledge_consumption: Optional[KnowledgeConsumption] = Field(
        default=None,
        description="Who should read and how to consume"
    )

    # =========================================================================
    # v3 Phase 1: Applicability Context
    # =========================================================================

    applicability: Optional[ApplicabilityContext] = Field(
        default=None,
        description="When this decision applies"
    )

    # =========================================================================
    # v3 Phase 1: Code Traceability
    # =========================================================================

    code_artifacts: List[CodeArtifact] = Field(
        default_factory=list,
        description="Links to implementation artifacts (PRs, commits, etc.)"
    )

    # =========================================================================
    # v3 Phase 1: Enhanced Search (replaces v2 search_metadata)
    # =========================================================================

    search_metadata: Optional[EnhancedSearchMetadata] = Field(
        default=None,
        description="Enhanced search optimization data"
    )

    # =========================================================================
    # v3 Phase 1: Enhanced LLM (replaces v2 llm_optimization)
    # =========================================================================

    llm_optimization: Optional[EnhancedLLMOptimization] = Field(
        default=None,
        description="Enhanced AI/LLM optimization data"
    )

    # =========================================================================
    # v3 Phase 2: Causality Context
    # =========================================================================

    trigger_event: Optional[TriggerEvent] = Field(
        default=None,
        description="Event that triggered this decision"
    )

    # =========================================================================
    # v3 Phase 2: Implementation Status
    # =========================================================================

    implementation_status: Optional[ImplementationStatus] = Field(
        default=None,
        description="Implementation progress tracking"
    )

    # =========================================================================
    # v3 Phase 2: Stability Metadata
    # =========================================================================

    stability: Optional[StabilityMetadata] = Field(
        default=None,
        description="Stability and maturity indicator"
    )

    # =========================================================================
    # v3 Phase 3: Persisted Impact Analysis
    # =========================================================================

    impact_analysis: Optional[PersistedImpactAnalysis] = Field(
        default=None,
        description="Cached impact analysis results"
    )

    # =========================================================================
    # v3 Phase 3: Usage Analytics
    # =========================================================================

    usage_analytics: Optional[UsageAnalytics] = Field(
        default=None,
        description="Usage tracking for optimization"
    )

    # =========================================================================
    # Cross-Agent Phase A: Metadata Enrichment & Conflict Tracking
    # NOTE: Per LAW §10.7, enrichments are stored in SEPARATE table (metadata_enrichments)
    # This field is DEPRECATED - use metadata_enrichments table instead
    # =========================================================================

    # DEPRECATED: Per LAW §4.5 & §10.7, enrichments stored separately for audit trail
    # Keep for backward compatibility during migration period
    amendments: List[MetadataEnrichment] = Field(
        default_factory=list,
        description="DEPRECATED: Use metadata_enrichments table. Per LAW §10.7, enrichments are separate."
    )

    stale_reference_warnings: List[StaleReferenceWarning] = Field(
        default_factory=list,
        description="Warnings about references to deprecated decisions"
    )

    # =========================================================================
    # v3 Enhanced: Structured Summary (Multi-Level Document Summarization)
    # =========================================================================

    structured_summary: Optional[StructuredSummary] = Field(
        default=None,
        description="Multi-level summary: headline, abstract, executive, role-based, Q&A"
    )

    # =========================================================================
    # Cross-Agent Phase B: Embedding & Adoption Tracking
    # NOTE: Per LAW §4.5, team_adoptions and blockers are stored in SEPARATE tables
    # =========================================================================

    embedding_metadata: Optional[EmbeddingMetadata] = Field(
        default=None,
        description="Complete embedding lifecycle metadata (LAW §6.5 compliant)"
    )

    # DEPRECATED: Per LAW §4.5.3, implementation tracking stored separately
    # Use decision_team_adoptions table instead
    team_adoptions: List[TeamAdoption] = Field(
        default_factory=list,
        description="DEPRECATED: Use decision_team_adoptions table. Per LAW §4.5, stored separately."
    )

    adoption_target: Optional[AdoptionTarget] = Field(
        default=None,
        description="Adoption goals and targets"
    )

    # adoption_timeline is OK - it's read-only snapshots, not mutable state
    adoption_timeline: List[AdoptionSnapshot] = Field(
        default_factory=list,
        description="Historical adoption snapshots (read-only)"
    )

    notification_subscriptions: List[NotificationSubscription] = Field(
        default_factory=list,
        description="Notification subscriptions for this decision"
    )

    # =========================================================================
    # Cross-Agent Phase B: Structured Blockers
    # NOTE: Per LAW §4.5.3, blockers are stored in SEPARATE table
    # =========================================================================

    # DEPRECATED: Per LAW §4.5.3, blockers stored separately
    # Use decision_blockers table instead
    structured_blockers: List[Blocker] = Field(
        default_factory=list,
        description="DEPRECATED: Use decision_blockers table. Per LAW §4.5, stored separately."
    )

    # =========================================================================
    # Cross-Agent Phase C: Disambiguation & Query Support
    # NOTE: LAW §6.5 compliant - includes AI safeguards
    # =========================================================================

    disambiguation: Optional[DisambiguationSupport] = Field(
        default=None,
        description="Query disambiguation with AI safeguards (LAW §6.5 compliant)"
    )

    query_hints: Optional[QueryProcessingHints] = Field(
        default=None,
        description="Query processing hints with AI safeguards (LAW §6.5 compliant)"
    )

    # =========================================================================
    # Cross-Agent Phase C: Enhanced Implementation Guidance
    # =========================================================================

    enhanced_implementation: Optional[EnhancedImplementationGuidance] = Field(
        default=None,
        description="Enhanced implementation guidance with structured steps"
    )

    rollback_history: List[RollbackRecord] = Field(
        default_factory=list,
        description="History of rollback events"
    )

    # =========================================================================
    # Cross-Agent Phase C: Enhanced Stability (integrates team adoption)
    # =========================================================================

    enhanced_stability: Optional[EnhancedStabilityMetadata] = Field(
        default=None,
        description="Enhanced stability with per-team tracking"
    )

    # =========================================================================
    # Computed Properties
    # =========================================================================

    @computed_field
    @property
    def has_detailed_content(self) -> bool:
        """Whether Layer B content exists."""
        return bool(self.detailed_content) or len(self.sections) > 0

    @computed_field
    @property
    def constraint_count(self) -> int:
        """Number of constraints."""
        return len(self.constraints)

    @computed_field
    @property
    def is_time_bounded(self) -> bool:
        """Whether decision has temporal limits."""
        if self.temporal_validity:
            return bool(self.temporal_validity.sunset_date or
                       self.temporal_validity.review_by)
        return False

    @computed_field
    @property
    def content_hash(self) -> str:
        """Hash of core content for change detection."""
        content = f"{self.statement}|{self.rationale}|{self.version}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @computed_field
    @property
    def is_stable(self) -> bool:
        """Whether decision is considered stable."""
        if self.stability:
            return self.stability.stability_status == StabilityStatus.STABLE
        return True  # Default to stable if not specified

    @computed_field
    @property
    def is_deprecated(self) -> bool:
        """Whether decision is deprecated."""
        if self.stability:
            return self.stability.stability_status in [
                StabilityStatus.DEPRECATED,
                StabilityStatus.ARCHIVED
            ]
        return False

    @computed_field
    @property
    def implementation_progress(self) -> int:
        """Implementation progress percentage."""
        if self.implementation_status:
            return self.implementation_status.progress_percentage
        return 0

    @computed_field
    @property
    def has_amendments(self) -> bool:
        """Whether this decision has active amendments."""
        return len([a for a in self.amendments if a.is_active]) > 0

    @computed_field
    @property
    def amendment_count(self) -> int:
        """Number of active amendments."""
        return len([a for a in self.amendments if a.is_active])

    @computed_field
    @property
    def has_stale_references(self) -> bool:
        """Whether this decision has unresolved stale references."""
        return len([w for w in self.stale_reference_warnings if not w.acknowledged]) > 0

    @computed_field
    @property
    def active_blocker_count(self) -> int:
        """Number of unresolved blockers."""
        return len([b for b in self.structured_blockers if not b.resolved_at])

    @computed_field
    @property
    def critical_blocker_count(self) -> int:
        """Number of critical unresolved blockers."""
        return len([
            b for b in self.structured_blockers
            if not b.resolved_at and b.severity == BlockerSeverity.CRITICAL
        ])

    @computed_field
    @property
    def team_adoption_percentage(self) -> float:
        """Percentage of teams that have adopted."""
        if not self.team_adoptions:
            return 0.0
        completed = len([t for t in self.team_adoptions if t.status == AdoptionStatus.COMPLETED])
        return round(completed / len(self.team_adoptions) * 100, 1)

    @computed_field
    @property
    def needs_embedding_update(self) -> bool:
        """Whether embedding needs regeneration."""
        if not self.embedding_metadata:
            return True
        return self.embedding_metadata.status in [EmbeddingStatus.STALE, EmbeddingStatus.PENDING]

    @computed_field
    @property
    def has_conflict_warnings(self) -> bool:
        """Whether any constraints have conflict warnings."""
        for constraint in self.constraints:
            if hasattr(constraint, 'conflict_summary') and constraint.conflict_summary:
                if constraint.conflict_summary.unresolved_count > 0:
                    return True
        return False

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("aspect_id")
    @classmethod
    def validate_domain_aspect_compatibility(cls, v, info):
        """Validate aspect is compatible with domain"""
        domain_id = info.data.get("domain_id")
        if domain_id and not is_aspect_compatible(domain_id, v):
            raise ValueError(
                f"Aspect {v} is not compatible with domain {domain_id}. "
                f"Valid aspects for {domain_id}: {DOMAIN_ASPECT_MATRIX[domain_id]}"
            )
        return v

    @field_validator("statement")
    @classmethod
    def validate_statement_length(cls, v):
        """
        Validate statement field for verbosity control.

        - Minimum: 50 chars (~10 words)
        - Maximum: 1500 chars (~200 words)

        Anti-patterns detected trigger warnings.
        """
        return validate_statement(v)

    @field_validator("rationale")
    @classmethod
    def validate_rationale_length(cls, v):
        """
        Validate rationale field for verbosity control.

        - Minimum: 100 chars (~20 words)
        - Maximum: 4000 chars (~500 words)

        Anti-patterns detected trigger warnings.
        """
        return validate_rationale(v)

    @field_validator("invariants")
    @classmethod
    def validate_invariants(cls, v):
        """
        Ensure invariants are non-empty strings with length limits.

        Per WRITING_GUIDELINES['invariant']:
        - Each invariant: 10-300 chars max
        - Total invariants: 20 max
        """
        if len(v) > ContentLengthConfig.INVARIANTS_MAX:
            raise ValueError(
                f"Too many invariants: {len(v)} "
                f"(max: {ContentLengthConfig.INVARIANTS_MAX}). "
                f"Consider consolidating related invariants."
            )
        for i, inv in enumerate(v):
            if not inv or len(inv.strip()) == 0:
                raise ValueError(f"Invariant at index {i} must not be empty")
            # Validate length
            validate_invariant(inv)
        return v

    @field_validator("constraints")
    @classmethod
    def validate_constraint_uniqueness(cls, v):
        """
        Ensure constraint_ids are unique and statements are concise.

        Per WRITING_GUIDELINES['constraint']:
        - Each constraint statement: 20-500 chars max
        - Total constraints: 30 max
        """
        if len(v) > ContentLengthConfig.CONSTRAINTS_MAX:
            raise ValueError(
                f"Too many constraints: {len(v)} "
                f"(max: {ContentLengthConfig.CONSTRAINTS_MAX}). "
                f"Consider grouping related constraints."
            )
        ids = [c.constraint_id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("constraint_id must be unique within decision")
        # Validate each constraint statement length
        for c in v:
            validate_constraint_statement(c.statement)
        return v

    @field_validator("sections")
    @classmethod
    def validate_section_uniqueness(cls, v):
        """Ensure section_ids are unique within decision"""
        if not v:
            return v
        ids = [s.section_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("section_id must be unique within decision")
        return sorted(v, key=lambda s: s.order)

    @model_validator(mode='after')
    def validate_supersedes_not_self(self):
        """Ensure decision doesn't supersede itself"""
        if self.supersedes and self.supersedes == self.decision_id:
            raise ValueError("Decision cannot supersede itself")
        return self

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_all_tags(self) -> List[str]:
        """Get all tags including inferred from tech_stack."""
        all_tags = set(self.tags)
        return list(all_tags)

    def get_total_token_estimate(self) -> int:
        """Estimate total tokens for LLM context."""
        if self.llm_optimization and self.llm_optimization.total_token_count:
            return self.llm_optimization.total_token_count
        char_count = len(self.statement) + len(self.rationale)
        if self.detailed_content:
            char_count += len(self.detailed_content)
        return int(char_count * 0.75)

    def is_active(self, as_of: Optional[date] = None) -> bool:
        """Check if decision is active as of a date."""
        check_date = as_of or date.today()
        if self.temporal_validity:
            if self.temporal_validity.effective_date:
                if check_date < self.temporal_validity.effective_date:
                    return False
            if self.temporal_validity.sunset_date:
                if check_date > self.temporal_validity.sunset_date:
                    return False
        return True

    def needs_review(self) -> bool:
        """Check if decision is due for review."""
        if not self.temporal_validity or not self.temporal_validity.review_by:
            return False
        return date.today() >= self.temporal_validity.review_by

    def get_embedding_text(self) -> str:
        """Get optimized text for vector embedding."""
        if self.llm_optimization and self.llm_optimization.embedding_text:
            return self.llm_optimization.embedding_text
        # Default: combine key content with structure markers
        parts = [
            f"[DECISION] {self.statement}",
            f"[RATIONALE] {self.rationale}",
        ]
        if self.invariants:
            parts.append(f"[INVARIANTS] {' '.join(self.invariants)}")
        if self.constraints:
            parts.append(f"[CONSTRAINTS] {' '.join(c.statement for c in self.constraints)}")
        return " ".join(parts)

    def get_target_roles(self) -> List[str]:
        """Get target roles for this decision."""
        if self.knowledge_consumption and self.knowledge_consumption.target_roles:
            return self.knowledge_consumption.target_roles
        return ["developer"]  # Default

    def get_citation(self) -> str:
        """Get citation format for this decision."""
        if self.llm_optimization and self.llm_optimization.rag and self.llm_optimization.rag.citation_format:
            return self.llm_optimization.rag.citation_format
        return f"[{self.decision_code or self.decision_id[:8]}]"

    def matches_context(self, keywords: List[str] = None, file_path: str = None) -> bool:
        """Check if this decision matches given context."""
        if not self.applicability:
            return True  # No applicability defined = always applicable

        for trigger in self.applicability.applies_when:
            # Check keywords
            if keywords and trigger.keywords:
                if any(k.lower() in [kw.lower() for kw in keywords] for k in trigger.keywords):
                    return True

            # Check file patterns (simplified - would use fnmatch in real impl)
            if file_path and trigger.file_patterns:
                for pattern in trigger.file_patterns:
                    if pattern.replace("*", "") in file_path:
                        return True

        return False

    # =========================================================================
    # Cross-Agent Utility Methods
    # =========================================================================

    def add_amendment(
        self,
        field_path: str,
        new_value: Any,
        reason: str,
        amended_by: str,
        amendment_type: EnrichmentType = EnrichmentType.OPERATIONAL_TAG,
        requires_approval: bool = False
    ) -> DecisionAmendment:
        """Create and add an amendment to this decision."""
        # Get previous value if exists
        previous_value = None
        try:
            # Navigate to field path
            parts = field_path.split(".")
            obj = self
            for part in parts:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    obj = None
                    break
            previous_value = obj
        except Exception:
            pass

        amendment = create_amendment(
            decision_id=self.decision_id,
            field_path=field_path,
            new_value=new_value,
            reason=reason,
            amended_by=amended_by,
            amendment_type=amendment_type,
            previous_value=previous_value,
            requires_approval=requires_approval
        )
        self.amendments.append(amendment)
        return amendment

    def add_blocker(
        self,
        description: str,
        category: BlockerCategory,
        severity: BlockerSeverity,
        created_by: str,
        affected_teams: List[str] = None
    ) -> Blocker:
        """Add a blocker to this decision."""
        blocker = create_blocker(
            description=description,
            category=category,
            severity=severity,
            created_by=created_by,
            affected_teams=affected_teams
        )
        self.structured_blockers.append(blocker)
        return blocker

    def resolve_blocker(self, blocker_id: str, resolution: str, resolved_by: str) -> bool:
        """Resolve a blocker by ID."""
        for blocker in self.structured_blockers:
            if blocker.blocker_id == blocker_id and not blocker.resolved_at:
                blocker.resolved_at = datetime.utcnow()
                blocker.resolved_by = resolved_by
                blocker.resolution = resolution
                return True
        return False

    def add_team_adoption(
        self,
        team_id: str,
        team_name: str,
        contact_person: str = None,
        target_date: date = None
    ) -> TeamAdoption:
        """Add a team to adoption tracking."""
        adoption = create_team_adoption(
            team_id=team_id,
            team_name=team_name,
            contact_person=contact_person,
            target_date=target_date
        )
        self.team_adoptions.append(adoption)
        return adoption

    def update_team_adoption_status(
        self,
        team_id: str,
        status: AdoptionStatus,
        progress: int = None,
        updated_by: str = None
    ) -> bool:
        """Update adoption status for a team."""
        for adoption in self.team_adoptions:
            if adoption.team_id == team_id:
                adoption.status = status
                if progress is not None:
                    adoption.progress_percentage = progress
                adoption.last_updated_by = updated_by
                adoption.last_updated_at = datetime.utcnow()
                if status == AdoptionStatus.COMPLETED and not adoption.completed_at:
                    adoption.completed_at = datetime.utcnow()
                elif status == AdoptionStatus.IN_PROGRESS and not adoption.started_at:
                    adoption.started_at = datetime.utcnow()
                return True
        return False

    def get_unresolved_blockers(self) -> List[Blocker]:
        """Get all unresolved blockers."""
        return [b for b in self.structured_blockers if not b.resolved_at]

    def get_critical_blockers(self) -> List[Blocker]:
        """Get all critical blockers."""
        return [
            b for b in self.structured_blockers
            if not b.resolved_at and b.severity == BlockerSeverity.CRITICAL
        ]

    def get_active_amendments(self) -> List[DecisionAmendment]:
        """Get all active amendments."""
        return [a for a in self.amendments if a.is_active]

    def get_pending_approval_amendments(self) -> List[DecisionAmendment]:
        """Get amendments requiring approval."""
        return [
            a for a in self.amendments
            if a.is_active and a.requires_approval and not a.approved_at
        ]

    def acknowledge_stale_reference(
        self,
        warning_id: str,
        acknowledged_by: str,
        resolution_action: str = None
    ) -> bool:
        """Acknowledge a stale reference warning."""
        for warning in self.stale_reference_warnings:
            if warning.warning_id == warning_id and not warning.acknowledged:
                warning.acknowledged = True
                warning.acknowledged_by = acknowledged_by
                warning.acknowledged_at = datetime.utcnow()
                if resolution_action:
                    warning.resolution_action = resolution_action
                    warning.resolved_at = datetime.utcnow()
                return True
        return False

    def get_constraint_conflicts(self) -> List[Dict[str, Any]]:
        """Get all constraint conflicts across constraints."""
        conflicts = []
        for constraint in self.constraints:
            if hasattr(constraint, 'constraint_relations'):
                for relation in constraint.constraint_relations:
                    if relation.conflict_status in [ConflictStatus.POTENTIAL, ConflictStatus.CONFIRMED]:
                        conflicts.append({
                            'constraint_id': constraint.constraint_id,
                            'related_decision_id': relation.related_decision_id,
                            'related_constraint_id': relation.related_constraint_id,
                            'relation_type': relation.relation_type,
                            'conflict_status': relation.conflict_status,
                            'context': relation.context
                        })
        return conflicts

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "550e8400-e29b-41d4-a716-446655440000",
                "decision_code": "ARCH-A06-001-v1.0.0",
                "domain_id": "ARCH",
                "aspect_id": "A06",
                "statement": "All frontend projects must follow feature-based folder structure.",
                "rationale": "Feature-based structure improves discoverability and enables lazy loading.",
                "scope": "ORGANIZATION",
                "blast_radius": "HIGH",
                "version": "1.0.0",
                "tags": ["FE", "ARCH"],
                "tech_stack": ["TypeScript", "React"],
                "knowledge_consumption": {
                    "target_roles": ["frontend_dev", "tech_lead"],
                    "audience_level": "INTERMEDIATE",
                    "learning_objectives": ["Understand feature-based structure benefits"],
                    "reading_time_minutes": 5
                },
                "applicability": {
                    "applies_when": [{
                        "trigger_id": "CTX-001",
                        "condition": "Creating new React component",
                        "keywords": ["react", "component"],
                        "file_patterns": ["src/features/**/*.tsx"]
                    }],
                    "auto_detect": True
                },
                "stability": {
                    "stability_status": "stable",
                    "maturity_score": 85,
                    "adoption_count": 12
                }
            }
        }


# ============================================================================
# SECTION 8: Input/Output DTOs
# ============================================================================

class DecisionCreateV3(BaseModel):
    """
    Input DTO for creating a new v3 decision.

    Only required fields are mandatory; v3 enhancements are optional.
    Auto-inference will populate many fields from content.
    """
    # Required fields
    domain_id: DomainId
    aspect_id: AspectId
    statement: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    scope: Scope
    blast_radius: BlastRadius
    version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    created_by: str

    # Optional v1/v2 fields
    constraints: List[EnhancedConstraint] = Field(default_factory=list)
    invariants: List[str] = Field(default_factory=list)
    supersedes: Optional[str] = None
    relations: List[Relation] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)

    # Optional Layer B content
    detailed_content: Optional[str] = None
    sections: List[ContentSection] = Field(default_factory=list)

    # Optional v2 fields
    temporal_validity: Optional[TemporalValidity] = None
    stakeholders: List[Stakeholder] = Field(default_factory=list)
    compliance_references: List[ComplianceReference] = Field(default_factory=list)
    change_type: Optional[ChangeType] = None
    implementation_guidance: Optional[ImplementationGuidance] = None
    anti_patterns: List[str] = Field(default_factory=list)
    derived_from: List[str] = Field(default_factory=list)

    # Optional v3 fields (will be auto-inferred if not provided)
    knowledge_consumption: Optional[KnowledgeConsumption] = None
    applicability: Optional[ApplicabilityContext] = None
    code_artifacts: List[CodeArtifact] = Field(default_factory=list)
    trigger_event: Optional[TriggerEvent] = None
    stability: Optional[StabilityMetadata] = None
    search_metadata: Optional[EnhancedSearchMetadata] = None
    llm_optimization: Optional[EnhancedLLMOptimization] = None

    # Optional Cross-Agent enhanced fields
    disambiguation: Optional[DisambiguationSupport] = None
    query_hints: Optional[QueryProcessingHints] = None
    enhanced_implementation: Optional[EnhancedImplementationGuidance] = None
    enhanced_stability: Optional[EnhancedStabilityMetadata] = None


# ============================================================================
# SECTION 9: Migration Helpers
# ============================================================================

def migrate_v2_to_v3(v2_decision: dict) -> DecisionV3:
    """
    Migrate a v2 decision dictionary to v3 DecisionV3 model.

    All v2 fields map directly; v3 fields get sensible defaults or auto-inferred.
    """
    # Copy all v2 fields
    v3_data = dict(v2_decision)

    # Migrate constraints to EnhancedConstraint
    if "constraints" in v3_data:
        v3_data["constraints"] = [
            EnhancedConstraint(**c) if isinstance(c, dict) else c
            for c in v3_data["constraints"]
        ]

    # Migrate search_metadata to EnhancedSearchMetadata
    if "search_metadata" in v3_data and v3_data["search_metadata"]:
        sm = v3_data["search_metadata"]
        if isinstance(sm, dict):
            # Convert question_variants to questions if exists
            if "question_variants" in sm and sm["question_variants"]:
                sm["questions"] = IntentBasedQuestions(
                    how_questions=[q for q in sm["question_variants"] if "how" in q.lower()],
                    why_questions=[q for q in sm["question_variants"] if "why" in q.lower()],
                    what_questions=[q for q in sm["question_variants"] if "what" in q.lower()],
                    when_questions=[q for q in sm["question_variants"] if "when" in q.lower()],
                )
            v3_data["search_metadata"] = EnhancedSearchMetadata(**sm)

    # Migrate llm_optimization to EnhancedLLMOptimization
    if "llm_optimization" in v3_data and v3_data["llm_optimization"]:
        llm = v3_data["llm_optimization"]
        if isinstance(llm, dict):
            v3_data["llm_optimization"] = EnhancedLLMOptimization(**llm)

    # Set v3 defaults
    if "stability" not in v3_data or not v3_data["stability"]:
        v3_data["stability"] = StabilityMetadata()

    if "implementation_status" not in v3_data or not v3_data["implementation_status"]:
        v3_data["implementation_status"] = ImplementationStatus()

    return DecisionV3(**v3_data)


# ============================================================================
# SECTION 10: v3 Database Indexing Strategy
# ============================================================================

DATABASE_INDEXES_V3 = """
-- v3 indexes for knowledge consumption queries
CREATE INDEX IF NOT EXISTS idx_decisions_target_roles
    ON decisions USING gin((knowledge_consumption->'target_roles') jsonb_path_ops)
    WHERE knowledge_consumption IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_audience_level
    ON decisions((knowledge_consumption->>'audience_level'))
    WHERE knowledge_consumption IS NOT NULL;

-- v3 indexes for applicability queries
CREATE INDEX IF NOT EXISTS idx_decisions_auto_detect
    ON decisions((applicability->>'auto_detect')::boolean)
    WHERE applicability IS NOT NULL;

-- v3 indexes for code artifact queries
CREATE INDEX IF NOT EXISTS idx_decisions_code_artifacts
    ON decisions USING gin(code_artifacts jsonb_path_ops)
    WHERE code_artifacts IS NOT NULL AND jsonb_array_length(code_artifacts) > 0;

-- v3 indexes for stability queries
CREATE INDEX IF NOT EXISTS idx_decisions_stability_status
    ON decisions((stability->>'stability_status'))
    WHERE stability IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_maturity_score
    ON decisions((stability->>'maturity_score')::int)
    WHERE stability IS NOT NULL;

-- v3 indexes for implementation status queries
CREATE INDEX IF NOT EXISTS idx_decisions_impl_status
    ON decisions((implementation_status->>'status'))
    WHERE implementation_status IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_impl_progress
    ON decisions((implementation_status->>'progress_percentage')::int)
    WHERE implementation_status IS NOT NULL;

-- v3 indexes for trigger event queries
CREATE INDEX IF NOT EXISTS idx_decisions_trigger_type
    ON decisions((trigger_event->>'event_type'))
    WHERE trigger_event IS NOT NULL;

-- v3 indexes for impact analysis queries
CREATE INDEX IF NOT EXISTS idx_decisions_risk_level
    ON decisions((impact_analysis->>'risk_level'))
    WHERE impact_analysis IS NOT NULL;

-- v3 indexes for usage analytics queries
CREATE INDEX IF NOT EXISTS idx_decisions_retrieval_count
    ON decisions((usage_analytics->>'retrieval_count')::int DESC)
    WHERE usage_analytics IS NOT NULL;

-- v3 composite indexes for common v3 query patterns
CREATE INDEX IF NOT EXISTS idx_decisions_stable_by_domain
    ON decisions(domain_id, created_at DESC)
    WHERE (stability->>'stability_status') = 'stable';

CREATE INDEX IF NOT EXISTS idx_decisions_implemented
    ON decisions(domain_id)
    WHERE (implementation_status->>'status') = 'completed';
"""

# ============================================================================
# SECTION 11: Cross-Agent Enhanced Database Indexes
# ============================================================================

DATABASE_INDEXES_V3_ENHANCED = """
-- Cross-Agent Phase A: Amendment indexes
CREATE INDEX IF NOT EXISTS idx_decisions_amendments_active
    ON decisions USING gin(amendments jsonb_path_ops)
    WHERE amendments IS NOT NULL AND jsonb_array_length(amendments) > 0;

-- Cross-Agent Phase A: Stale reference indexes
CREATE INDEX IF NOT EXISTS idx_decisions_stale_refs_unacked
    ON decisions(decision_id)
    WHERE stale_reference_warnings IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM jsonb_array_elements(stale_reference_warnings) elem
          WHERE (elem->>'acknowledged')::boolean = false
      );

-- Cross-Agent Phase B: Team adoption indexes
CREATE INDEX IF NOT EXISTS idx_decisions_team_adoptions
    ON decisions USING gin(team_adoptions jsonb_path_ops)
    WHERE team_adoptions IS NOT NULL AND jsonb_array_length(team_adoptions) > 0;

CREATE INDEX IF NOT EXISTS idx_decisions_adoption_progress
    ON decisions((enhanced_stability->>'adoption_count')::int DESC)
    WHERE enhanced_stability IS NOT NULL;

-- Cross-Agent Phase B: Blocker indexes
CREATE INDEX IF NOT EXISTS idx_decisions_blockers
    ON decisions USING gin(structured_blockers jsonb_path_ops)
    WHERE structured_blockers IS NOT NULL AND jsonb_array_length(structured_blockers) > 0;

CREATE INDEX IF NOT EXISTS idx_decisions_critical_blockers
    ON decisions(decision_id)
    WHERE structured_blockers IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM jsonb_array_elements(structured_blockers) elem
          WHERE (elem->>'severity') = 'critical'
            AND (elem->>'resolved_at') IS NULL
      );

-- Cross-Agent Phase B: Embedding metadata indexes
CREATE INDEX IF NOT EXISTS idx_decisions_embedding_status
    ON decisions((embedding_metadata->>'status'))
    WHERE embedding_metadata IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_decisions_embedding_stale
    ON decisions(decision_id)
    WHERE embedding_metadata IS NOT NULL
      AND (embedding_metadata->>'status') IN ('stale', 'pending');

-- Cross-Agent Phase C: Disambiguation indexes
CREATE INDEX IF NOT EXISTS idx_decisions_disambiguation_group
    ON decisions((disambiguation->>'disambiguation_group'))
    WHERE disambiguation IS NOT NULL
      AND (disambiguation->>'disambiguation_group') IS NOT NULL;

-- Cross-Agent Phase C: Rollback history
CREATE INDEX IF NOT EXISTS idx_decisions_rollback_history
    ON decisions USING gin(rollback_history jsonb_path_ops)
    WHERE rollback_history IS NOT NULL AND jsonb_array_length(rollback_history) > 0;

-- Composite: Decisions needing attention (multiple criteria)
CREATE INDEX IF NOT EXISTS idx_decisions_needs_attention_enhanced
    ON decisions(created_at DESC)
    WHERE (embedding_metadata IS NOT NULL AND (embedding_metadata->>'status') = 'stale')
       OR (structured_blockers IS NOT NULL AND jsonb_array_length(structured_blockers) > 0)
       OR (stale_reference_warnings IS NOT NULL AND jsonb_array_length(stale_reference_warnings) > 0)
       OR (amendments IS NOT NULL AND EXISTS (
           SELECT 1 FROM jsonb_array_elements(amendments) elem
           WHERE (elem->>'requires_approval')::boolean = true
             AND (elem->>'approved_at') IS NULL
       ));
"""


# ============================================================================
# SECTION 12: Module Exports
# ============================================================================

__all__ = [
    # v2 re-exports (backward compatibility)
    "DomainId", "AspectId", "Scope", "BlastRadius", "ConstraintType", "RelationType",
    "SectionType", "ChangeType", "StakeholderRole", "ComplianceFramework", "ApprovalStatus",
    "AreaTag", "DOMAIN_ASPECT_MATRIX", "DOMAIN_LABELS", "ASPECT_LABELS", "is_aspect_compatible",
    "Relation", "ContentSection", "Stakeholder", "ApprovalRecord", "ComplianceReference",
    "TemporalValidity", "QualityMetadata", "ImplementationGuidance",

    # v3 Enums
    "AudienceLevel", "TriggerEventType", "StabilityStatus", "ImplementationStatusType",
    "ExceptionScope", "ExceptionStatus", "CodeArtifactType", "RiskLevel",

    # v3 Phase 1 Models
    "KnowledgeConsumption", "ContextTrigger", "ApplicabilityContext", "CodeArtifact",
    "SemanticExpansion", "IntentBasedQuestions", "EnhancedSearchMetadata",
    "RAGOptimization", "EnhancedLLMOptimization",

    # v3 Phase 2 Models
    "ExceptionRequest", "GrantedException", "EnforcementStatus", "EnhancedConstraint",
    "TriggerEvent", "ImplementationStatus", "StabilityMetadata",

    # v3 Phase 3 Models
    "PersistedImpactAnalysis", "UsageAnalytics",

    # Cross-Agent Phase A Enums (LAW-compliant)
    "EnrichmentType",  # Replaces AmendmentType
    "ConflictStatus", "ConflictRelationType", "NotificationChannel",
    "NotificationTrigger", "BlockerCategory", "BlockerSeverity", "EmbeddingStatus",
    "AdoptionStatus", "CoverageImportance",

    # Cross-Agent Phase A Models (LAW §10.7 compliant)
    "MetadataEnrichment",  # NEW: LAW §10.7 compliant enrichment
    "ENRICHABLE_FIELDS", "IMMUTABLE_FIELDS",  # NEW: Field validation constants
    "DecisionAmendment",  # Deprecated alias for MetadataEnrichment
    "ConstraintRelation", "ConflictSummary", "StaleReferenceWarning",

    # Cross-Agent Phase B Models
    "ImplementationStep", "Blocker", "RollbackStep", "RollbackRecord",
    "EmbeddingMetadata", "TeamAdoption", "AdoptionTarget", "AdoptionSnapshot",
    "NotificationSubscription", "EscalationLevel", "EscalationPath", "NotificationRecord",

    # Cross-Agent Phase C Models (with AI Safeguards per LAW §6.5)
    "DisambiguationSupport", "QueryProcessingHints", "ExpectedCoverage", "CoverageGap",
    "LearningPathCheckpoint", "LearningPath", "LearnerProgress",
    "EnhancedImplementationGuidance", "EnhancedStabilityMetadata", "FullyEnhancedConstraint",

    # Cross-Agent Phase C: Structured Summary
    "SummaryLevel", "StructuredSummary",

    # Main Models
    "DecisionV3", "DecisionCreateV3",

    # Migration & Utilities
    "migrate_v2_to_v3", "generate_content_hash",
    "create_metadata_enrichment",  # NEW: LAW §10.7 compliant factory
    "create_amendment",  # Deprecated - use create_metadata_enrichment
    "create_blocker", "create_team_adoption",

    # Database Constants
    "DATABASE_INDEXES_V3", "DATABASE_INDEXES_V3_ENHANCED",
]
