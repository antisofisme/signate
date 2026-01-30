"""
MANTRA-SCHEMA-003-ENHANCED: Production-Ready Decision Schema v3

This module provides ALL improvements identified from cross-agent analysis:
- Phase A: Critical Fixes (Amendment, Conflict, Graph Integrity)
- Phase B: Structural Improvements (Steps, Blockers, Embedding, Team)
- Phase C: Operational Excellence (Disambiguation, Query, Coverage, Learning)

Target: Raise maturity score from 6.2/10 to 9.0/10

CRITICAL FIXES:
1. DecisionAmendment - Resolve immutability vs retroactive changes conflict
2. ConstraintRelation - Cross-decision conflict detection
3. Cycle detection hooks - Graph integrity validation
4. Supersede auto-sync - Automatic successor_id updates

STRUCTURAL IMPROVEMENTS:
1. ImplementationStep - Structured steps with code and verification
2. Blocker - Structured blockers with category and severity
3. RollbackRecord - Trackable rollback with post-mortem
4. EmbeddingMetadata - Complete embedding lifecycle management
5. TeamAdoption - Per-team adoption tracking
6. NotificationConfig - Escalation and notification infrastructure

OPERATIONAL EXCELLENCE:
1. DisambiguationSupport - Active query disambiguation
2. QueryProcessingHints - Query-side processing support
3. ExpectedCoverage - Gap analysis registry
4. LearningPath - Curriculum-level learning aggregation
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Literal, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, date
import uuid
import hashlib


# ============================================================================
# SECTION 1: Phase A - New Enumerations for Critical Fixes
# ============================================================================

class EnrichmentType(str, Enum):
    """
    Types of metadata enrichment (compliant with MANTRA-LAW-001 §10.7).

    NOTE: These are ADDITIVE ONLY - they do not modify core content.
    Per §10.7, only operational metadata can be enriched, NOT:
    - statement, rationale, constraints, invariants (require supersedes)
    """
    TRIGGER_EVENT = "trigger_event"           # Add causality context
    CODE_ARTIFACT = "code_artifact"           # Link implementation PR/commit
    EMBEDDING_UPDATE = "embedding_update"     # Update AI embeddings
    OPERATIONAL_TAG = "operational_tag"       # Add operational metadata
    SEARCH_OPTIMIZATION = "search_optimization"  # Improve search keywords


class ConflictStatus(str, Enum):
    """Status of constraint conflicts."""
    NONE = "none"               # No conflict detected
    POTENTIAL = "potential"     # Semantic similarity detected
    CONFIRMED = "confirmed"     # Admin confirmed conflict
    RESOLVED = "resolved"       # Exception granted or constraint modified
    ACCEPTED = "accepted"       # Intentional conflict (different scopes)


class ConflictRelationType(str, Enum):
    """Types of relations between constraints."""
    CONFLICTS_WITH = "conflicts_with"   # Direct contradiction
    SUPERSEDES = "supersedes"           # This constraint overrides target
    COMPLEMENTS = "complements"         # Works together with target
    NARROWS = "narrows"                 # More specific version of target
    EXTENDS = "extends"                 # Broader version of target
    EXCEPTION_TO = "exception_to"       # Explicit exception to target


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationTrigger(str, Enum):
    """Events that trigger notifications."""
    DECISION_CREATED = "decision_created"
    DECISION_SUPERSEDED = "decision_superseded"
    DECISION_DEPRECATED = "decision_deprecated"
    EXCEPTION_EXPIRING = "exception_expiring"
    EXCEPTION_EXPIRED = "exception_expired"
    CONSTRAINT_VIOLATED = "constraint_violated"
    STALE_REFERENCE = "stale_reference"
    REVIEW_DUE = "review_due"


class BlockerCategory(str, Enum):
    """Categories of implementation blockers."""
    TECHNICAL = "technical"         # Technical limitation
    RESOURCE = "resource"           # Lack of resources/time
    DEPENDENCY = "dependency"       # Waiting on another decision/system
    PROCESS = "process"             # Process/approval blocker
    KNOWLEDGE = "knowledge"         # Lack of knowledge/skills
    PRIORITY = "priority"           # Deprioritized
    OTHER = "other"


class BlockerSeverity(str, Enum):
    """Severity of blockers."""
    LOW = "low"           # Minor inconvenience
    MEDIUM = "medium"     # Slows progress
    HIGH = "high"         # Significantly blocks progress
    CRITICAL = "critical" # Complete blocker


class EmbeddingStatus(str, Enum):
    """Status of embedding generation."""
    PENDING = "pending"       # Not yet generated
    GENERATING = "generating" # In progress
    CURRENT = "current"       # Up to date
    STALE = "stale"           # Needs regeneration
    FAILED = "failed"         # Generation failed


class AdoptionStatus(str, Enum):
    """Team adoption status."""
    NOT_STARTED = "not_started"
    EVALUATING = "evaluating"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETED = "completed"
    OPTED_OUT = "opted_out"   # Explicit opt-out with reason


class CoverageImportance(str, Enum):
    """Importance level for expected coverage."""
    CRITICAL = "critical"     # Must have
    IMPORTANT = "important"   # Should have
    NICE_TO_HAVE = "nice_to_have"


# ============================================================================
# SECTION 2: Phase A - Metadata Enrichment Model (LAW §10.7 Compliant)
# ============================================================================

# Allowed fields for enrichment (per LAW §10.7.1)
ENRICHABLE_FIELDS = frozenset([
    "trigger_event",
    "code_artifacts",
    "embedding_metadata",
    "search_metadata.search_keywords",
    "search_metadata.aliases",
    "llm_optimization.embedding_text",
    "llm_optimization.keywords_for_rag",
    "knowledge_consumption.reading_time_minutes",
])

# Forbidden fields that REQUIRE supersedes (per LAW §10.7.3)
IMMUTABLE_FIELDS = frozenset([
    "statement",
    "rationale",
    "constraints",
    "invariants",
    "domain_id",
    "aspect_id",
    "scope",
    "blast_radius",
])


class MetadataEnrichment(BaseModel):
    """
    IMMUTABLE metadata enrichment record - compliant with MANTRA-LAW-001 §10.7.

    This replaces the non-compliant DecisionAmendment model.

    KEY DIFFERENCES FROM PREVIOUS DecisionAmendment:
    1. NO mutable state (no is_active, no reverted_at)
    2. Once created, enrichment is PERMANENT (append-only log)
    3. Only ENRICHABLE_FIELDS can be enriched (not core content)
    4. Human approval is ALWAYS required (no auto-enrichment)

    Use cases (per §10.7.1):
    - Adding trigger_event to old decision
    - Adding code_artifacts (PR links, commits)
    - Updating embedding metadata
    - Adding operational tags

    NOT allowed (per §10.7.3):
    - Changing statement, rationale, constraints, invariants
    - These REQUIRE supersedes mechanism
    """
    enrichment_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique enrichment identifier (immutable)"
    )
    decision_id: str = Field(..., description="Reference to enriched decision")

    # Enrichment details
    enrichment_type: EnrichmentType = Field(..., description="Type of enrichment")
    field_path: str = Field(
        ...,
        description="Field being enriched (must be in ENRICHABLE_FIELDS)"
    )
    enrichment_value: Any = Field(..., description="Value to add/set")

    # Justification (required per §10.7.2)
    reason: str = Field(
        ...,
        min_length=10,
        description="Why this enrichment is needed"
    )
    supporting_evidence: Optional[str] = Field(
        default=None,
        description="Links or references supporting this enrichment"
    )

    # Audit trail (required per §10.7.2)
    # Per amended §10.7.2: enriched_by MAY be AI (ai:*) or human
    enriched_by: str = Field(
        ...,
        description="Creator identifier. AI format: 'ai:model-name'. Human: any other string."
    )
    enriched_at: datetime = Field(default_factory=datetime.utcnow)

    # Approval (ALWAYS required - MUST be human per §6.3 and §10.7.2)
    approved_by: str = Field(
        ...,
        description="Human approver (MUST NOT start with 'ai:')"
    )
    approved_at: datetime = Field(default_factory=datetime.utcnow)
    approval_notes: Optional[str] = Field(default=None)

    # NO mutable state - once created, enrichment is permanent
    # If enrichment was wrong, create SUPERSEDING decision instead

    class Config:
        extra = "forbid"

    @field_validator("approved_by")
    @classmethod
    def validate_human_approver(cls, v):
        """Validate approver is human (not AI) per §6.3 and §10.7.2."""
        if v.startswith("ai:"):
            raise ValueError(
                f"approved_by cannot be AI ('{v}'). "
                f"Per MANTRA-LAW-001 §6.3, AI cannot approve decisions or enrichments. "
                f"Human approval is REQUIRED."
            )
        return v

    @field_validator("field_path")
    @classmethod
    def validate_enrichable_field(cls, v):
        """Validate field is in ENRICHABLE_FIELDS (per LAW §10.7.1)."""
        # Check exact match or prefix match for nested fields
        if v not in ENRICHABLE_FIELDS:
            # Check if it's a valid sub-path of an enrichable field
            is_valid_subpath = any(
                v.startswith(f"{allowed}.") or v == allowed
                for allowed in ENRICHABLE_FIELDS
            )
            if not is_valid_subpath:
                raise ValueError(
                    f"Field '{v}' is not enrichable per MANTRA-LAW-001 §10.7.1. "
                    f"Enrichable fields: {', '.join(sorted(ENRICHABLE_FIELDS))}. "
                    f"Changes to statement, rationale, constraints, or invariants "
                    f"REQUIRE supersedes mechanism per §10.7.3."
                )
        return v


# Backward compatibility alias (deprecated)
DecisionAmendment = MetadataEnrichment


# ============================================================================
# SECTION 3: Phase A - Constraint Relation Model (Conflict Detection)
# ============================================================================

class ConstraintRelation(BaseModel):
    """
    Track relationships between constraints across decisions.

    Enables:
    - Conflict detection: "MUST use X" vs "MUST NOT use X"
    - Precedence tracking: Which constraint takes priority
    - Exception mapping: Explicit carve-outs
    """
    relation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique relation identifier"
    )

    # Related constraint reference
    related_decision_id: str = Field(..., description="Decision containing related constraint")
    related_constraint_id: str = Field(..., description="Constraint ID in related decision")

    # Relation type and status
    relation_type: ConflictRelationType = Field(..., description="Type of relation")
    conflict_status: ConflictStatus = Field(
        default=ConflictStatus.NONE,
        description="Current conflict status"
    )

    # Context and resolution
    context: Optional[str] = Field(
        default=None,
        description="Why this relation exists"
    )
    resolution_notes: Optional[str] = Field(
        default=None,
        description="How conflict was resolved (if applicable)"
    )

    # Scope intersection
    scope_overlap: Optional[str] = Field(
        default=None,
        description="Description of scope overlap: 'Both apply to React components'"
    )
    precedence_reason: Optional[str] = Field(
        default=None,
        description="Why this constraint takes precedence (if SUPERSEDES)"
    )

    # Detection metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: Literal["automated", "manual"] = Field(default="manual")
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence of automated detection"
    )

    # Acknowledgment
    acknowledged_by: Optional[str] = Field(default=None)
    acknowledged_at: Optional[datetime] = Field(default=None)

    class Config:
        extra = "forbid"


class ConflictSummary(BaseModel):
    """
    Summary of conflicts for a decision.

    Provides quick overview without traversing all constraint relations.
    """
    total_relations: int = Field(default=0)
    potential_conflicts: int = Field(default=0)
    confirmed_conflicts: int = Field(default=0)
    resolved_conflicts: int = Field(default=0)
    unresolved_count: int = Field(default=0)
    last_checked_at: Optional[datetime] = Field(default=None)
    needs_review: bool = Field(default=False)

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 4: Phase A - Stale Reference Detection
# ============================================================================

class StaleReferenceWarning(BaseModel):
    """
    Warning about references to deprecated/superseded decisions.

    Auto-populated when a referenced decision is deprecated.
    """
    warning_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Reference details
    referenced_decision_id: str = Field(..., description="ID of deprecated decision")
    referenced_decision_code: Optional[str] = Field(default=None)
    reference_type: str = Field(
        ...,
        description="Type of reference: 'relation', 'prerequisite', 'derived_from'"
    )

    # Replacement info
    successor_id: Optional[str] = Field(
        default=None,
        description="ID of replacement decision"
    )
    successor_code: Optional[str] = Field(default=None)
    migration_available: bool = Field(default=False)

    # Status
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = Field(default=False)
    acknowledged_by: Optional[str] = Field(default=None)
    acknowledged_at: Optional[datetime] = Field(default=None)

    # Resolution
    resolution_action: Optional[str] = Field(
        default=None,
        description="What was done: 'updated_reference', 'exception_granted', 'accepted_as_is'"
    )
    resolved_at: Optional[datetime] = Field(default=None)

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 5: Phase B - Structured Implementation Models
# ============================================================================

class ImplementationStep(BaseModel):
    """
    Structured implementation step with code and verification.

    Replaces unstructured List[str] in implementation_guidance.steps.
    """
    step_number: int = Field(..., ge=1, description="Step order (1-based)")
    title: str = Field(..., min_length=1, description="Short title")
    description: str = Field(..., description="Detailed description")

    # Code support
    code_snippet: Optional[str] = Field(
        default=None,
        description="Example code for this step"
    )
    code_language: Optional[str] = Field(
        default=None,
        description="Language: 'typescript', 'python', 'bash'"
    )
    file_to_modify: Optional[str] = Field(
        default=None,
        description="Target file path"
    )

    # Dependencies
    depends_on_steps: List[int] = Field(
        default_factory=list,
        description="Step numbers that must complete first"
    )

    # Timing
    estimated_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description="Estimated time to complete"
    )

    # Verification
    verification_command: Optional[str] = Field(
        default=None,
        description="Command to verify step completion"
    )
    verification_criteria: Optional[str] = Field(
        default=None,
        description="How to know step is done"
    )

    # Tracking
    is_optional: bool = Field(default=False)
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = Field(default=None)
    completed_by: Optional[str] = Field(default=None)
    completion_notes: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"


class Blocker(BaseModel):
    """
    Structured blocker with category and severity.

    Enables aggregation and tracking of blockers across decisions.
    """
    blocker_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique blocker identifier"
    )

    # Classification
    category: BlockerCategory = Field(..., description="Type of blocker")
    severity: BlockerSeverity = Field(..., description="Impact level")

    # Details
    description: str = Field(..., min_length=10, description="What is blocking")
    root_cause: Optional[str] = Field(
        default=None,
        description="Underlying cause if known"
    )

    # Scope
    affected_teams: List[str] = Field(
        default_factory=list,
        description="Teams affected by this blocker"
    )
    affected_areas: List[str] = Field(
        default_factory=list,
        description="Areas affected: 'frontend', 'api', 'database'"
    )

    # Dependencies
    depends_on_decision_id: Optional[str] = Field(
        default=None,
        description="Decision ID that must be resolved first"
    )
    depends_on_external: Optional[str] = Field(
        default=None,
        description="External dependency: 'vendor_api', 'infrastructure_upgrade'"
    )

    # Timeline
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Who reported this blocker")
    expected_resolution_date: Optional[date] = Field(default=None)

    # Resolution
    resolved_at: Optional[datetime] = Field(default=None)
    resolved_by: Optional[str] = Field(default=None)
    resolution: Optional[str] = Field(
        default=None,
        description="How it was resolved"
    )

    class Config:
        extra = "forbid"


class RollbackStep(BaseModel):
    """
    Structured rollback step with verification.
    """
    step_number: int = Field(..., ge=1)
    description: str = Field(...)
    command: Optional[str] = Field(default=None, description="Command to execute")
    verification: Optional[str] = Field(default=None, description="How to verify")
    is_reversible: bool = Field(default=True, description="Can this step be undone")

    # Tracking
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = Field(default=None)
    completed_by: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"


class RollbackRecord(BaseModel):
    """
    Complete rollback record with post-mortem.

    Tracks rollback execution and captures lessons learned.
    """
    rollback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Trigger
    trigger_event_id: Optional[str] = Field(
        default=None,
        description="Link to incident that triggered rollback"
    )
    reason: str = Field(..., description="Why rollback was needed")

    # Execution
    initiated_by: str = Field(...)
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Steps
    steps: List[RollbackStep] = Field(default_factory=list)

    # Verification
    verification_status: Literal["pending", "verified", "failed", "partial"] = Field(
        default="pending"
    )
    verification_notes: Optional[str] = Field(default=None)
    verified_by: Optional[str] = Field(default=None)
    verified_at: Optional[datetime] = Field(default=None)

    # Post-mortem
    lessons_learned: List[str] = Field(
        default_factory=list,
        description="What we learned from this rollback"
    )
    prevention_measures: List[str] = Field(
        default_factory=list,
        description="How to prevent similar issues"
    )
    postmortem_url: Optional[str] = Field(
        default=None,
        description="Link to detailed post-mortem document"
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 6: Phase B - Embedding Lifecycle Management
# ============================================================================

class EmbeddingMetadata(BaseModel):
    """
    Complete embedding metadata for lifecycle management.

    Tracks embedding generation, versioning, and staleness.
    """
    # Model info
    model: str = Field(..., description="Model name: 'text-embedding-3-large'")
    model_version: Optional[str] = Field(default=None, description="Model version: 'v1.2.0'")
    dimensions: int = Field(..., description="Vector dimensions: 3072")

    # Generation
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_duration_ms: Optional[int] = Field(default=None)

    # Content tracking
    content_hash: str = Field(
        ...,
        description="Hash of embedding_text when generated"
    )
    source_fields: List[str] = Field(
        default_factory=lambda: ["statement", "rationale"],
        description="Fields used to generate embedding"
    )

    # Quality metrics
    cosine_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for retrieval"
    )
    retrieval_quality_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Based on user feedback"
    )

    # Status
    status: EmbeddingStatus = Field(default=EmbeddingStatus.CURRENT)
    stale_reason: Optional[str] = Field(
        default=None,
        description="Why embedding is stale: 'model_upgraded', 'content_changed'"
    )

    # Re-embedding queue
    reembedding_priority: int = Field(
        default=0,
        ge=0,
        le=10,
        description="0=low, 10=urgent"
    )
    reembedding_requested_at: Optional[datetime] = Field(default=None)
    reembedding_requested_by: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"

    def is_stale(self, current_content_hash: str, current_model: str) -> bool:
        """Check if embedding needs regeneration."""
        if self.status == EmbeddingStatus.STALE:
            return True
        if self.content_hash != current_content_hash:
            return True
        if self.model != current_model:
            return True
        return False


# ============================================================================
# SECTION 7: Phase B - Team Adoption Tracking
# ============================================================================

class TeamAdoption(BaseModel):
    """
    Per-team adoption tracking.

    Enables visibility into which teams have adopted, are in progress,
    or have blockers.
    """
    team_id: str = Field(..., description="Unique team identifier")
    team_name: str = Field(..., description="Human-readable team name")

    # Status
    status: AdoptionStatus = Field(default=AdoptionStatus.NOT_STARTED)
    progress_percentage: int = Field(default=0, ge=0, le=100)

    # Timeline
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    target_date: Optional[date] = Field(default=None)

    # Contacts
    contact_person: Optional[str] = Field(default=None)
    contact_email: Optional[str] = Field(default=None)

    # Blockers (references to Blocker objects)
    blocker_ids: List[str] = Field(
        default_factory=list,
        description="IDs of blockers affecting this team"
    )

    # Opt-out
    opted_out_reason: Optional[str] = Field(
        default=None,
        description="Why team opted out (if status=OPTED_OUT)"
    )
    opted_out_approved_by: Optional[str] = Field(default=None)

    # Notes
    notes: Optional[str] = Field(default=None)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_by: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"


class AdoptionTarget(BaseModel):
    """
    Adoption target for tracking against goals.
    """
    target_date: date = Field(..., description="Target completion date")
    target_percentage: int = Field(
        ...,
        ge=0,
        le=100,
        description="Target adoption percentage"
    )
    target_team_count: Optional[int] = Field(
        default=None,
        description="Target number of teams"
    )
    target_teams: List[str] = Field(
        default_factory=list,
        description="Specific teams that must adopt"
    )

    class Config:
        extra = "forbid"


class AdoptionSnapshot(BaseModel):
    """
    Point-in-time adoption snapshot for trend analysis.
    """
    snapshot_date: date = Field(...)
    total_teams: int = Field(...)
    adopted_teams: int = Field(...)
    in_progress_teams: int = Field(default=0)
    opted_out_teams: int = Field(default=0)
    adoption_percentage: float = Field(...)
    active_blockers: int = Field(default=0)

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 8: Phase B - Notification Infrastructure
# ============================================================================

class NotificationSubscription(BaseModel):
    """
    Subscription to decision-related notifications.
    """
    subscription_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Subscriber
    subscriber_type: Literal["user", "team", "channel"] = Field(...)
    subscriber_id: str = Field(..., description="Email, team ID, or channel ID")

    # What to notify
    triggers: List[NotificationTrigger] = Field(
        default_factory=list,
        description="Events that trigger notification"
    )

    # How to notify
    channels: List[NotificationChannel] = Field(
        default_factory=list,
        description="Delivery channels"
    )

    # Filters
    filter_domains: List[str] = Field(
        default_factory=list,
        description="Only notify for these domains (empty=all)"
    )
    filter_tags: List[str] = Field(
        default_factory=list,
        description="Only notify for these tags (empty=all)"
    )
    filter_blast_radius: List[str] = Field(
        default_factory=list,
        description="Only notify for these blast radius levels"
    )

    # Status
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        extra = "forbid"


class EscalationLevel(BaseModel):
    """
    Single level in escalation path.
    """
    level: int = Field(..., ge=1, le=5)
    notify_after_hours: int = Field(
        ...,
        ge=0,
        description="Hours after trigger before escalating to this level"
    )
    recipients: List[str] = Field(..., description="Email addresses or team IDs")
    channels: List[NotificationChannel] = Field(default_factory=list)

    class Config:
        extra = "forbid"


class EscalationPath(BaseModel):
    """
    Complete escalation path for critical notifications.
    """
    path_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., description="Escalation path name")

    # Triggers
    applicable_triggers: List[NotificationTrigger] = Field(
        default_factory=list,
        description="Which triggers use this escalation"
    )

    # Levels
    levels: List[EscalationLevel] = Field(
        default_factory=list,
        description="Escalation levels (1 to N)"
    )

    # Settings
    auto_resolve_after_hours: Optional[int] = Field(
        default=None,
        description="Auto-close if not acknowledged after N hours"
    )
    require_acknowledgment: bool = Field(default=True)

    class Config:
        extra = "forbid"


class NotificationRecord(BaseModel):
    """
    Record of a sent notification.
    """
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Context
    decision_id: str = Field(...)
    trigger: NotificationTrigger = Field(...)

    # Delivery
    channel: NotificationChannel = Field(...)
    recipient: str = Field(...)
    sent_at: datetime = Field(default_factory=datetime.utcnow)

    # Status
    delivered: bool = Field(default=False)
    delivery_error: Optional[str] = Field(default=None)

    # Acknowledgment
    acknowledged: bool = Field(default=False)
    acknowledged_at: Optional[datetime] = Field(default=None)
    acknowledged_by: Optional[str] = Field(default=None)

    # Escalation
    escalation_level: int = Field(default=1)
    escalated_at: Optional[datetime] = Field(default=None)

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 9: Phase C - Disambiguation Support (with AI Safeguards per §6.2)
# ============================================================================

class DisambiguationSupport(BaseModel):
    """
    Support for query disambiguation - WITH AI SAFEGUARDS.

    Per MANTRA-LAW-001 §6.2, AI MAY detect conflicts and produce analysis.
    Per §6.3, AI MUST NOT assign decisions or auto-select.

    SAFEGUARDS IMPLEMENTED:
    1. human_confirmation_required: AI cannot auto-select default
    2. ai_selection_prohibited: Explicit flag preventing auto-selection
    3. present_all_options: AI must show all disambiguation options
    """
    # Grouping
    disambiguation_group: Optional[str] = Field(
        default=None,
        description="Group ID for related-but-distinct decisions: 'api-types'"
    )
    disambiguation_group_name: Optional[str] = Field(
        default=None,
        description="Human-readable group name: 'API Types'"
    )

    # Distinguishing features
    distinguishing_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that distinguish this from group siblings"
    )
    distinguishing_summary: Optional[str] = Field(
        default=None,
        description="Brief description of what makes this unique"
    )

    # Clarifying questions
    clarifying_questions: List[str] = Field(
        default_factory=list,
        description="Questions to ask user for disambiguation"
    )

    # Ranking within group (for DISPLAY ORDER ONLY, not auto-selection)
    popularity_rank: int = Field(
        default=0,
        ge=0,
        description="Rank within disambiguation group (0 = most common) - FOR DISPLAY ORDER ONLY"
    )

    # CHANGED: default_in_group now requires human confirmation
    suggested_default: bool = Field(
        default=False,
        description="SUGGESTED default (requires human confirmation, NOT auto-selected)"
    )

    # === AI SAFEGUARDS (per MANTRA-LAW-001 §6.3) ===

    human_confirmation_required: bool = Field(
        default=True,
        description="SAFEGUARD: Human MUST confirm selection. AI cannot auto-select. Per §6.3."
    )

    ai_auto_selection_prohibited: bool = Field(
        default=True,
        description="SAFEGUARD: Explicit prohibition of AI auto-selection. Per §6.3."
    )

    present_all_options: bool = Field(
        default=True,
        description="SAFEGUARD: AI must present ALL options in group, not just suggested default."
    )

    class Config:
        extra = "forbid"


class QueryProcessingHints(BaseModel):
    """
    Hints for query-side processing - WITH AI SAFEGUARDS.

    Per MANTRA-LAW-001 §6.2, AI MAY read and analyze.
    Per §6.3, AI MUST NOT assign or finalize.

    SAFEGUARDS IMPLEMENTED:
    1. triggers are SUGGESTIONS, not automatic selections
    2. human_must_confirm_trigger: Explicit confirmation requirement
    3. ai_suggestion_only: Results are suggestions for human review
    """
    # Intent signals
    intent_signals: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping: {'how': ['structure', 'organize'], 'why': ['reason', 'because']}"
    )

    # Query expansions
    query_expansions: List[str] = Field(
        default_factory=list,
        description="Alternative query phrasings that should match"
    )

    # Trigger phrases (SUGGESTIONS, not auto-selections)
    trigger_phrases: List[str] = Field(
        default_factory=list,
        description="Phrases that SUGGEST this decision (human confirms final selection)"
    )

    # Context requirements
    required_context: List[str] = Field(
        default_factory=list,
        description="Context keywords required for match"
    )
    exclude_context: List[str] = Field(
        default_factory=list,
        description="Context keywords that should exclude match"
    )

    # === AI SAFEGUARDS (per MANTRA-LAW-001 §6.3) ===

    human_must_confirm_trigger: bool = Field(
        default=True,
        description="SAFEGUARD: Trigger match is SUGGESTION only. Human must confirm. Per §6.3."
    )

    ai_suggestion_only: bool = Field(
        default=True,
        description="SAFEGUARD: AI outputs are suggestions for human review, not final answers."
    )

    max_auto_suggestions: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum decisions AI can suggest (prevents overwhelming user)"
    )

    require_confidence_display: bool = Field(
        default=True,
        description="SAFEGUARD: AI must display confidence score with suggestions."
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 10: Phase C - Expected Coverage Registry
# ============================================================================

class ExpectedCoverage(BaseModel):
    """
    Expected coverage for gap analysis.

    Defines what decisions SHOULD exist, enabling gap identification.
    """
    coverage_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Classification
    domain_id: str = Field(..., description="Domain: ARCH, INT, CTL, EVO")
    aspect_id: str = Field(..., description="Aspect: A01-A16")

    # Expectations
    expected_count: int = Field(
        default=1,
        ge=1,
        description="Expected number of decisions"
    )
    importance: CoverageImportance = Field(
        default=CoverageImportance.IMPORTANT,
        description="How important is this coverage"
    )

    # Context
    topic_description: str = Field(
        ...,
        description="What this coverage area should address"
    )
    example_decisions: List[str] = Field(
        default_factory=list,
        description="Example decision titles that would satisfy"
    )

    # Responsibility
    responsible_team: Optional[str] = Field(default=None)
    responsible_person: Optional[str] = Field(default=None)

    # Timeline
    target_date: Optional[date] = Field(default=None)

    # Status
    current_count: int = Field(default=0)
    is_satisfied: bool = Field(default=False)
    matching_decision_ids: List[str] = Field(
        default_factory=list,
        description="Decision IDs that satisfy this coverage"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(...)
    notes: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"


class CoverageGap(BaseModel):
    """
    Identified coverage gap.
    """
    gap_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Reference
    expected_coverage_id: str = Field(...)
    domain_id: str = Field(...)
    aspect_id: str = Field(...)

    # Gap details
    gap_description: str = Field(...)
    priority: CoverageImportance = Field(...)

    # Status
    identified_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(default=None)
    resolved_by_decision_id: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 11: Phase C - Learning Path
# ============================================================================

class LearningPathCheckpoint(BaseModel):
    """
    Checkpoint in a learning path.
    """
    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., description="Checkpoint name: 'Fundamentals Complete'")
    description: Optional[str] = Field(default=None)

    # Position
    after_decision_ids: List[str] = Field(
        ...,
        description="Decision IDs that must be completed before checkpoint"
    )

    # Assessment
    has_quiz: bool = Field(default=False)
    quiz_url: Optional[str] = Field(default=None)

    class Config:
        extra = "forbid"


class LearningPath(BaseModel):
    """
    Curated learning path for onboarding.

    Aggregates prerequisite_decisions into structured curriculum.
    """
    path_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Identity
    name: str = Field(..., description="Path name: 'Backend Developer Onboarding'")
    description: Optional[str] = Field(default=None)

    # Target audience
    target_role: str = Field(..., description="Primary role: 'backend_dev'")
    target_level: str = Field(
        default="INTERMEDIATE",
        description="Entry level: BEGINNER, INTERMEDIATE, ADVANCED"
    )

    # Content
    ordered_decision_ids: List[str] = Field(
        ...,
        description="Decision IDs in learning order"
    )
    optional_decision_ids: List[str] = Field(
        default_factory=list,
        description="Optional/bonus decisions"
    )

    # Checkpoints
    checkpoints: List[LearningPathCheckpoint] = Field(
        default_factory=list,
        description="Milestones in the path"
    )

    # Timing
    estimated_total_hours: Optional[float] = Field(default=None)
    recommended_pace: Optional[str] = Field(
        default=None,
        description="e.g., '2-3 decisions per day'"
    )

    # Status
    is_active: bool = Field(default=True)
    version: str = Field(default="1.0.0")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(...)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        extra = "forbid"


class LearnerProgress(BaseModel):
    """
    Track individual learner progress through a path.
    """
    progress_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # References
    learner_id: str = Field(..., description="User ID")
    path_id: str = Field(..., description="Learning path ID")

    # Progress
    completed_decision_ids: List[str] = Field(default_factory=list)
    current_decision_id: Optional[str] = Field(default=None)
    progress_percentage: int = Field(default=0, ge=0, le=100)

    # Checkpoints
    completed_checkpoints: List[str] = Field(default_factory=list)

    # Timeline
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Engagement
    time_spent_minutes: int = Field(default=0)

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 12: Phase C - Enhanced Implementation Guidance
# ============================================================================

class EnhancedImplementationGuidance(BaseModel):
    """
    Enhanced implementation guidance with structured steps and rollback.

    Replaces the simpler ImplementationGuidance from v2.
    """
    # Effort estimation
    estimated_effort: Optional[str] = Field(
        default=None,
        description="SMALL/MEDIUM/LARGE/XLARGE"
    )
    estimated_hours: Optional[float] = Field(
        default=None,
        description="Estimated implementation hours"
    )

    # Prerequisites (structured)
    prerequisites: List[str] = Field(
        default_factory=list,
        description="What must be in place (for backward compat)"
    )
    prerequisite_decisions: List[str] = Field(
        default_factory=list,
        description="Decision IDs that must be implemented first"
    )
    prerequisite_tools: List[str] = Field(
        default_factory=list,
        description="Tools that must be installed"
    )

    # Steps (structured)
    steps_text: List[str] = Field(
        default_factory=list,
        description="Simple text steps (backward compat)"
    )
    structured_steps: List[ImplementationStep] = Field(
        default_factory=list,
        description="Full structured steps with code and verification"
    )

    # Pitfalls
    common_pitfalls: List[str] = Field(default_factory=list)

    # Success criteria
    success_criteria: List[str] = Field(default_factory=list)
    verification_commands: List[str] = Field(
        default_factory=list,
        description="Commands to verify implementation"
    )

    # Rollback (structured)
    rollback_procedure: Optional[str] = Field(
        default=None,
        description="Simple text rollback (backward compat)"
    )
    structured_rollback: List[RollbackStep] = Field(
        default_factory=list,
        description="Full structured rollback steps"
    )

    # History
    rollback_records: List[RollbackRecord] = Field(
        default_factory=list,
        description="Past rollback events"
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 13: Phase C - Enhanced Stability Metadata
# ============================================================================

class EnhancedStabilityMetadata(BaseModel):
    """
    Enhanced stability with per-team tracking and targets.
    """
    # Core stability (from v3)
    stability_status: str = Field(default="stable")
    maturity_score: int = Field(default=50, ge=0, le=100)

    # Deprecation
    deprecation_date: Optional[date] = Field(default=None)
    deprecation_reason: Optional[str] = Field(default=None)
    successor_id: Optional[str] = Field(default=None)

    # Team adoptions (NEW)
    team_adoptions: List[TeamAdoption] = Field(
        default_factory=list,
        description="Per-team adoption tracking"
    )

    # Adoption targets (NEW)
    adoption_target: Optional[AdoptionTarget] = Field(
        default=None,
        description="Target for tracking"
    )

    # Adoption timeline (NEW)
    adoption_timeline: List[AdoptionSnapshot] = Field(
        default_factory=list,
        description="Historical snapshots"
    )

    # Blockers (NEW - structured)
    blockers: List[Blocker] = Field(
        default_factory=list,
        description="Current blockers"
    )

    # Aggregate metrics
    adoption_count: int = Field(default=0)
    feedback_score: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    total_teams: int = Field(default=0)
    adopted_teams_count: int = Field(default=0)
    in_progress_teams_count: int = Field(default=0)
    blocked_teams_count: int = Field(default=0)

    class Config:
        extra = "forbid"

    def update_aggregates(self):
        """Recalculate aggregate metrics from team_adoptions."""
        self.total_teams = len(self.team_adoptions)
        self.adopted_teams_count = sum(
            1 for t in self.team_adoptions
            if t.status == AdoptionStatus.COMPLETED
        )
        self.in_progress_teams_count = sum(
            1 for t in self.team_adoptions
            if t.status in [AdoptionStatus.IN_PROGRESS, AdoptionStatus.PARTIAL]
        )
        self.blocked_teams_count = sum(
            1 for t in self.team_adoptions
            if len(t.blocker_ids) > 0
        )
        self.adoption_count = self.adopted_teams_count


# ============================================================================
# SECTION 14: Enhanced Constraint with Relations
# ============================================================================

class FullyEnhancedConstraint(BaseModel):
    """
    Fully enhanced constraint with conflict tracking.

    Extends EnhancedConstraint from schema_v3.py with ConstraintRelation.
    """
    # Core fields (from v2/v3)
    constraint_id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    type: str = Field(...)  # ConstraintType enum value
    enforcement_level: Optional[str] = Field(default="STRICT")
    automated_check: bool = Field(default=False)
    check_command: Optional[str] = Field(default=None)

    # Exception handling (from v3)
    exception_process: Optional[str] = Field(default=None)
    exception_template: Optional[str] = Field(default=None)
    granted_exceptions: List[Any] = Field(default_factory=list)  # GrantedException

    # Enforcement status (from v3)
    enforcement_status: Optional[Any] = Field(default=None)  # EnforcementStatus

    # NEW: Constraint relations for conflict detection
    constraint_relations: List[ConstraintRelation] = Field(
        default_factory=list,
        description="Relations to constraints in other decisions"
    )

    # NEW: Conflict summary
    conflict_summary: Optional[ConflictSummary] = Field(
        default=None,
        description="Summary of conflict status"
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 15: Structured Summary Model (Multi-Level Document Summarization)
# ============================================================================

class SummaryLevel(str, Enum):
    """Levels of summary detail."""
    HEADLINE = "headline"       # 1 sentence, <20 words
    ABSTRACT = "abstract"       # 2-3 sentences, 50-80 words
    EXECUTIVE = "executive"     # 1 paragraph, 100-200 words
    DETAILED = "detailed"       # Multiple paragraphs, 300-500 words


class StructuredSummary(BaseModel):
    """
    Multi-level structured summary for long decision documents.

    Enables:
    - Quick scanning (headline)
    - Context understanding (abstract)
    - Stakeholder briefing (executive)
    - Role-specific views (for_developers, for_architects, for_managers)
    - Q&A access (quick_answers)

    Use when detailed_content exceeds 1000 words.
    """

    # === Hierarchical Summaries ===

    headline: str = Field(
        ...,
        max_length=150,
        description="One-liner (~15-20 words): 'We use feature folders for React components'"
    )

    abstract: str = Field(
        ...,
        max_length=500,
        description="2-3 sentences (~50-80 words) covering WHAT and WHY"
    )

    executive_summary: str = Field(
        ...,
        max_length=1500,
        description="Full paragraph (~100-200 words) for management/stakeholders"
    )

    # === Structured Breakdown ===

    key_points: List[str] = Field(
        default_factory=list,
        description="3-7 bullet points of main takeaways"
    )

    constraints_summary: List[str] = Field(
        default_factory=list,
        description="One-line summary per constraint: 'C-001: MUST use /v{n}/ prefix'"
    )

    invariants_summary: List[str] = Field(
        default_factory=list,
        description="One-line summary per invariant"
    )

    # === Role-Based Summaries ===

    for_developers: Optional[str] = Field(
        default=None,
        max_length=800,
        description="Technical implementation focus: how to implement"
    )

    for_architects: Optional[str] = Field(
        default=None,
        max_length=800,
        description="System design focus: architectural implications"
    )

    for_managers: Optional[str] = Field(
        default=None,
        max_length=800,
        description="Business impact focus: timeline, resources, risk"
    )

    for_security: Optional[str] = Field(
        default=None,
        max_length=800,
        description="Security focus: compliance, risks, controls"
    )

    # === Question-Based Access ===

    quick_answers: Dict[str, str] = Field(
        default_factory=dict,
        description="Q&A pairs: {'What is this?': '...', 'When to use?': '...'}"
    )

    common_questions: List[str] = Field(
        default_factory=list,
        description="Frequently asked questions about this decision"
    )

    # === Navigation Aids ===

    related_topics: List[str] = Field(
        default_factory=list,
        description="Related concepts for further reading"
    )

    see_also_decision_ids: List[str] = Field(
        default_factory=list,
        description="Related decisions to explore"
    )

    # === Generation Metadata ===

    generated_by: Literal["human", "ai_assisted", "ai_generated"] = Field(
        default="human",
        description="Who created this summary"
    )

    verified_by: Optional[str] = Field(
        default=None,
        description="Human who verified AI-generated summary (required if ai_generated)"
    )

    generated_at: datetime = Field(default_factory=datetime.utcnow)

    last_synced_at: Optional[datetime] = Field(
        default=None,
        description="When summary was last synced with source content"
    )

    source_content_hash: Optional[str] = Field(
        default=None,
        description="Hash of source content for staleness detection"
    )

    class Config:
        extra = "forbid"

    @model_validator(mode='after')
    def validate_verification(self):
        """AI-generated summaries MUST be verified by human."""
        if self.generated_by == "ai_generated" and not self.verified_by:
            raise ValueError(
                "AI-generated summaries MUST be verified by a human. "
                "Set verified_by field with human identifier."
            )
        return self

    def is_stale(self, current_content_hash: str) -> bool:
        """Check if summary is stale relative to current content."""
        if not self.source_content_hash:
            return True
        return self.source_content_hash != current_content_hash


# ============================================================================
# SECTION 16: Utility Functions
# ============================================================================

def generate_content_hash(content: str) -> str:
    """Generate hash for content change detection."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def create_metadata_enrichment(
    decision_id: str,
    field_path: str,
    enrichment_value: Any,
    reason: str,
    enriched_by: str,
    approved_by: str,
    enrichment_type: EnrichmentType = EnrichmentType.OPERATIONAL_TAG,
) -> MetadataEnrichment:
    """
    Factory function for creating metadata enrichments (LAW §10.7 compliant).

    Args:
        decision_id: Decision to enrich
        field_path: Must be in ENRICHABLE_FIELDS
        enrichment_value: Value to add
        reason: Why this enrichment (min 10 chars)
        enriched_by: Human who created
        approved_by: Human who approved (REQUIRED)
        enrichment_type: Type of enrichment

    Raises:
        ValueError: If field_path not in ENRICHABLE_FIELDS
    """
    return MetadataEnrichment(
        decision_id=decision_id,
        enrichment_type=enrichment_type,
        field_path=field_path,
        enrichment_value=enrichment_value,
        reason=reason,
        enriched_by=enriched_by,
        approved_by=approved_by,
    )


# Backward compatibility alias (deprecated - use create_metadata_enrichment)
def create_amendment(
    decision_id: str,
    field_path: str,
    new_value: Any,
    reason: str,
    amended_by: str,
    **kwargs  # Ignore old params
) -> MetadataEnrichment:
    """
    DEPRECATED: Use create_metadata_enrichment instead.

    This function exists for backward compatibility only.
    """
    import warnings
    warnings.warn(
        "create_amendment is deprecated. Use create_metadata_enrichment instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return MetadataEnrichment(
        decision_id=decision_id,
        enrichment_type=EnrichmentType.OPERATIONAL_TAG,
        field_path=field_path,
        enrichment_value=new_value,
        reason=reason,
        enriched_by=amended_by,
        approved_by=amended_by,  # Same as enriched_by for backward compat
    )


def create_blocker(
    description: str,
    category: BlockerCategory,
    severity: BlockerSeverity,
    created_by: str,
    affected_teams: List[str] = None,
    depends_on_decision_id: str = None
) -> Blocker:
    """Factory function for creating blockers."""
    return Blocker(
        category=category,
        severity=severity,
        description=description,
        created_by=created_by,
        affected_teams=affected_teams or [],
        depends_on_decision_id=depends_on_decision_id
    )


def create_team_adoption(
    team_id: str,
    team_name: str,
    contact_person: str = None,
    target_date: date = None
) -> TeamAdoption:
    """Factory function for creating team adoption entries."""
    return TeamAdoption(
        team_id=team_id,
        team_name=team_name,
        contact_person=contact_person,
        target_date=target_date
    )


# ============================================================================
# SECTION 17: Content Length Guidelines (Verbosity Control)
# ============================================================================

class ContentLengthConfig:
    """
    Content length limits and guidelines for preventing verbose writing.

    Principle: Every field has SPECIFIC purpose and LENGTH.
    - ENFORCE limits to prevent verbose, redundant content
    - GUIDE writers with word/character targets
    - VALIDATE at schema level where possible

    Word counts are approximate. Character limits are ENFORCED.
    """

    # ==========================================================================
    # Core Decision Fields
    # ==========================================================================

    # Statement: WHAT we decide (concise, actionable)
    STATEMENT_MIN_WORDS = 10
    STATEMENT_MAX_WORDS = 200
    STATEMENT_MIN_CHARS = 50
    STATEMENT_MAX_CHARS = 1500  # ~200 words max

    # Rationale: WHY we decide (focused reasoning, not essay)
    RATIONALE_MIN_WORDS = 20
    RATIONALE_MAX_WORDS = 500
    RATIONALE_MIN_CHARS = 100
    RATIONALE_MAX_CHARS = 4000  # ~500 words max

    # ==========================================================================
    # Constraint Fields
    # ==========================================================================

    # Constraint statement: ONE enforceable rule
    CONSTRAINT_MIN_CHARS = 20
    CONSTRAINT_MAX_CHARS = 500  # ~60 words max

    # Constraint check_command: runnable command
    CHECK_COMMAND_MAX_CHARS = 1000

    # ==========================================================================
    # Invariant Fields
    # ==========================================================================

    # Invariant: ONE truth statement
    INVARIANT_MIN_CHARS = 10
    INVARIANT_MAX_CHARS = 300  # ~40 words max

    # ==========================================================================
    # Summary Fields (Already enforced in StructuredSummary)
    # ==========================================================================

    HEADLINE_MAX_CHARS = 150       # 1 sentence, ~15-20 words
    ABSTRACT_MAX_CHARS = 500       # 2-3 sentences, ~50-80 words
    EXECUTIVE_MAX_CHARS = 1500     # 1 paragraph, ~100-200 words
    ROLE_SUMMARY_MAX_CHARS = 800   # Role-specific, ~100 words

    # ==========================================================================
    # Detail Fields
    # ==========================================================================

    # Context summary for RAG
    CONTEXT_SUMMARY_MAX_CHARS = 1000  # ~150 words

    # Micro summary for token-limited
    MICRO_SUMMARY_MAX_CHARS = 100    # ~20 words

    # Detailed content (unlimited but with sections)
    DETAILED_CONTENT_WARN_CHARS = 10000  # Warning if exceeds

    # Section content
    SECTION_CONTENT_MAX_CHARS = 5000  # ~700 words per section

    # ==========================================================================
    # List Item Limits
    # ==========================================================================

    # Key points in summary
    KEY_POINTS_MIN = 3
    KEY_POINTS_MAX = 7

    # Tags
    TAGS_MAX = 10

    # Tech stack
    TECH_STACK_MAX = 15

    # Quick answers
    QUICK_ANSWERS_MAX = 10

    # Invariants
    INVARIANTS_MAX = 20

    # Constraints
    CONSTRAINTS_MAX = 30


class WritingStyle(str, Enum):
    """Writing styles for different field types."""

    DECLARATIVE = "declarative"      # Statement: "We use X for Y"
    REASONING = "reasoning"          # Rationale: "Because X, therefore Y"
    IMPERATIVE = "imperative"        # Constraint: "MUST do X", "MUST NOT do Y"
    ASSERTIVE = "assertive"          # Invariant: "X is always true"
    DESCRIPTIVE = "descriptive"      # Content: Describe, explain, illustrate
    SUMMARY = "summary"              # Summary: Condense, highlight, distill


class WritingGuideline(BaseModel):
    """
    Panduan penulisan untuk setiap jenis field.

    Tujuan:
    1. Prevent verbose writing (2 paragraph cukup, jangan 5)
    2. Maintain consistency across decisions
    3. Enable machine processing (predictable format)
    4. Improve readability (dense, focused)
    """

    field_name: str = Field(..., description="Target field name")

    writing_style: WritingStyle = Field(
        ...,
        description="Expected writing style"
    )

    min_length: Optional[int] = Field(
        default=None,
        description="Minimum characters"
    )

    max_length: Optional[int] = Field(
        default=None,
        description="Maximum characters (ENFORCED)"
    )

    word_target: str = Field(
        ...,
        description="Target word count range"
    )

    structure: str = Field(
        ...,
        description="Expected structure/format"
    )

    good_example: str = Field(
        ...,
        description="Example of good writing"
    )

    bad_example: str = Field(
        ...,
        description="Example of verbose/bad writing"
    )

    anti_patterns: List[str] = Field(
        default_factory=list,
        description="Writing patterns to avoid"
    )

    quality_signals: List[str] = Field(
        default_factory=list,
        description="Signs of good writing"
    )


# Pre-defined writing guidelines for core fields
WRITING_GUIDELINES: Dict[str, WritingGuideline] = {

    "statement": WritingGuideline(
        field_name="statement",
        writing_style=WritingStyle.DECLARATIVE,
        min_length=ContentLengthConfig.STATEMENT_MIN_CHARS,
        max_length=ContentLengthConfig.STATEMENT_MAX_CHARS,
        word_target="10-200 words",
        structure="[SUBJECT] + [ACTION/DECISION] + [SCOPE/CONTEXT]",
        good_example=(
            "We use feature folders for React components to improve maintainability. "
            "Each feature (auth, dashboard, billing) has its own folder containing "
            "components, hooks, utils, and tests. Shared components go in /shared. "
            "This applies to all frontend code in the monorepo."
        ),
        bad_example=(
            "After extensive discussions and many meetings over the past few weeks, "
            "the team has collectively agreed and decided that moving forward we should "
            "probably consider using what is commonly referred to as 'feature folders' "
            "which is a popular approach in the React community for organizing our "
            "component files and related utilities in a way that groups them by feature "
            "rather than by type, which we believe might potentially help us with "
            "maintainability and developer experience, although we're not entirely sure..."
            # This is 3x longer saying the same thing
        ),
        anti_patterns=[
            "After extensive discussions...",
            "We have decided to probably...",
            "It is recommended that we might consider...",
            "Moving forward we should...",
            "The team has collectively agreed...",
            "Which we believe might potentially...",
        ],
        quality_signals=[
            "Direct verb: 'use', 'require', 'implement'",
            "Clear scope: 'all frontend', 'BE services', 'this module'",
            "Specific: names, paths, versions",
            "No hedging: avoid 'might', 'probably', 'consider'",
        ],
    ),

    "rationale": WritingGuideline(
        field_name="rationale",
        writing_style=WritingStyle.REASONING,
        min_length=ContentLengthConfig.RATIONALE_MIN_CHARS,
        max_length=ContentLengthConfig.RATIONALE_MAX_CHARS,
        word_target="20-500 words",
        structure="[PROBLEM/CONTEXT] → [OPTIONS CONSIDERED] → [WHY THIS CHOICE] → [EXPECTED BENEFIT]",
        good_example=(
            "Feature folders improve maintainability as codebase grows beyond 50+ components. "
            "Alternative approaches considered:\n"
            "1. Type-based folders (/components, /hooks) - becomes hard to navigate at scale\n"
            "2. Flat structure - too many files in one folder\n\n"
            "Feature folders chosen because:\n"
            "- Related code stays together (easier to understand feature)\n"
            "- Deletion is simple (remove one folder)\n"
            "- Team members can own features without conflicts\n\n"
            "Expected: 30% faster onboarding, reduced cross-feature dependencies."
        ),
        bad_example=(
            "So, the rationale behind this decision is multifaceted and involves several "
            "interconnected considerations that we feel are important to document here. "
            "First of all, it's worth mentioning that we had numerous discussions about "
            "this topic over the course of several sprint planning sessions. The team "
            "members expressed various opinions and perspectives. Some felt strongly about "
            "one approach while others had different views. After considering all the "
            "various factors and taking into account the different stakeholder requirements, "
            "we eventually came to the conclusion that this approach seems to be the most "
            "suitable for our particular context and circumstances..."
            # Lots of words, no actual reasoning
        ),
        anti_patterns=[
            "So, the rationale is multifaceted...",
            "It's worth mentioning that...",
            "We had numerous discussions...",
            "Various opinions and perspectives...",
            "Taking into account the different...",
            "Seems to be the most suitable...",
        ],
        quality_signals=[
            "States the problem first",
            "Lists alternatives considered",
            "Explains WHY chosen (not just WHAT)",
            "Quantifies benefits when possible",
            "Uses bullet points for clarity",
        ],
    ),

    "constraint": WritingGuideline(
        field_name="constraint",
        writing_style=WritingStyle.IMPERATIVE,
        min_length=ContentLengthConfig.CONSTRAINT_MIN_CHARS,
        max_length=ContentLengthConfig.CONSTRAINT_MAX_CHARS,
        word_target="10-60 words",
        structure="[MUST/MUST NOT/SHOULD] + [ACTION] + [CONDITION (optional)]",
        good_example="MUST use /v{n}/ prefix for all API endpoints (e.g., /v1/users, /v2/products)",
        bad_example=(
            "It is strongly recommended that developers should probably consider using "
            "a version prefix in the API endpoint URLs because this is generally considered "
            "a best practice in the industry and helps with API versioning over time"
        ),
        anti_patterns=[
            "It is recommended that...",
            "Developers should consider...",
            "Generally considered a best practice...",
            "This is because...",
        ],
        quality_signals=[
            "Starts with MUST, MUST NOT, SHOULD, or SHALL",
            "One enforceable rule per constraint",
            "Includes example when helpful",
            "Measurable/verifiable",
        ],
    ),

    "invariant": WritingGuideline(
        field_name="invariant",
        writing_style=WritingStyle.ASSERTIVE,
        min_length=ContentLengthConfig.INVARIANT_MIN_CHARS,
        max_length=ContentLengthConfig.INVARIANT_MAX_CHARS,
        word_target="5-40 words",
        structure="[SUBJECT] + [IS ALWAYS/NEVER] + [CONDITION]",
        good_example="All API responses include request_id header for tracing",
        bad_example=(
            "Generally speaking, in most cases, API responses should ideally contain "
            "some form of identifier that can potentially be used for tracing purposes"
        ),
        anti_patterns=[
            "Generally speaking...",
            "In most cases...",
            "Should ideally...",
            "Some form of...",
            "Can potentially be used...",
        ],
        quality_signals=[
            "States absolute truth",
            "No hedging (always, never, every)",
            "Testable assertion",
            "One invariant per statement",
        ],
    ),

    "headline": WritingGuideline(
        field_name="headline",
        writing_style=WritingStyle.SUMMARY,
        max_length=ContentLengthConfig.HEADLINE_MAX_CHARS,
        word_target="15-20 words",
        structure="[CORE DECISION IN ONE SENTENCE]",
        good_example="We use feature folders for React components to improve maintainability",
        bad_example="This document describes our team's decision regarding the organizational structure of our React component files",
        anti_patterns=[
            "This document describes...",
            "We have decided to...",
            "The purpose of this is...",
        ],
        quality_signals=[
            "Answers 'What did we decide?' in one line",
            "Active voice",
            "No fluff words",
        ],
    ),

    "abstract": WritingGuideline(
        field_name="abstract",
        writing_style=WritingStyle.SUMMARY,
        max_length=ContentLengthConfig.ABSTRACT_MAX_CHARS,
        word_target="50-80 words",
        structure="[WHAT] + [WHY] in 2-3 sentences",
        good_example=(
            "Feature folders group React components by feature (/auth, /dashboard) instead of type. "
            "This improves maintainability as the codebase grows and enables team ownership of features. "
            "Applies to all frontend code in the monorepo."
        ),
        bad_example=(
            "This decision document outlines our approach to organizing React component files. "
            "After careful consideration and discussion with various stakeholders, we have "
            "determined that a feature-based folder structure would be beneficial. The following "
            "sections will elaborate on the details of this decision and provide guidance on "
            "implementation. Please refer to the constraints section for specific rules..."
        ),
        anti_patterns=[
            "This decision document outlines...",
            "After careful consideration...",
            "The following sections will...",
            "Please refer to...",
        ],
        quality_signals=[
            "Dense information",
            "WHAT and WHY only",
            "No forward references",
            "Self-contained",
        ],
    ),
}


def validate_content_length(
    field_name: str,
    content: str,
    raise_on_exceed: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Validate content length against guidelines.

    Args:
        field_name: Name of field being validated
        content: Content to validate
        raise_on_exceed: If True, raise ValueError on exceed

    Returns:
        Tuple of (is_valid, warning_message)
    """
    guideline = WRITING_GUIDELINES.get(field_name)
    if not guideline:
        return True, None

    content_len = len(content)

    # Check minimum
    if guideline.min_length and content_len < guideline.min_length:
        msg = (
            f"{field_name} is too short: {content_len} chars "
            f"(minimum: {guideline.min_length}). "
            f"Target: {guideline.word_target}"
        )
        if raise_on_exceed:
            raise ValueError(msg)
        return False, msg

    # Check maximum
    if guideline.max_length and content_len > guideline.max_length:
        msg = (
            f"{field_name} is too long: {content_len} chars "
            f"(maximum: {guideline.max_length}). "
            f"Target: {guideline.word_target}. "
            f"Anti-patterns to avoid: {', '.join(guideline.anti_patterns[:3])}"
        )
        if raise_on_exceed:
            raise ValueError(msg)
        return False, msg

    return True, None


def check_anti_patterns(
    field_name: str,
    content: str
) -> List[str]:
    """
    Check content for anti-patterns.

    Returns list of detected anti-patterns.
    """
    guideline = WRITING_GUIDELINES.get(field_name)
    if not guideline:
        return []

    detected = []
    content_lower = content.lower()

    for pattern in guideline.anti_patterns:
        if pattern.lower() in content_lower:
            detected.append(pattern)

    return detected


def get_writing_tips(field_name: str) -> Optional[Dict[str, Any]]:
    """
    Get writing tips for a field.

    Returns dict with structure, examples, and tips.
    """
    guideline = WRITING_GUIDELINES.get(field_name)
    if not guideline:
        return None

    return {
        "field": field_name,
        "style": guideline.writing_style.value,
        "word_target": guideline.word_target,
        "structure": guideline.structure,
        "good_example": guideline.good_example,
        "bad_example": guideline.bad_example[:200] + "...",  # Truncate bad example
        "avoid": guideline.anti_patterns,
        "signals": guideline.quality_signals,
    }


# ============================================================================
# SECTION 18: Content Validators for Schema
# ============================================================================

def validate_statement(value: str) -> str:
    """Validate statement field."""
    validate_content_length("statement", value)

    # Check for anti-patterns (warning only)
    anti = check_anti_patterns("statement", value)
    if anti:
        import warnings
        warnings.warn(
            f"Statement contains verbose patterns: {anti}. "
            f"Consider rewriting for clarity.",
            UserWarning
        )

    return value


def validate_rationale(value: str) -> str:
    """Validate rationale field."""
    validate_content_length("rationale", value)

    # Check for anti-patterns (warning only)
    anti = check_anti_patterns("rationale", value)
    if anti:
        import warnings
        warnings.warn(
            f"Rationale contains verbose patterns: {anti}. "
            f"Consider rewriting for clarity.",
            UserWarning
        )

    return value


def validate_constraint_statement(value: str) -> str:
    """Validate constraint statement."""
    if len(value) > ContentLengthConfig.CONSTRAINT_MAX_CHARS:
        raise ValueError(
            f"Constraint too long: {len(value)} chars "
            f"(max: {ContentLengthConfig.CONSTRAINT_MAX_CHARS}). "
            f"Keep constraints atomic and focused."
        )
    return value


def validate_invariant(value: str) -> str:
    """Validate invariant statement."""
    if len(value) > ContentLengthConfig.INVARIANT_MAX_CHARS:
        raise ValueError(
            f"Invariant too long: {len(value)} chars "
            f"(max: {ContentLengthConfig.INVARIANT_MAX_CHARS}). "
            f"Keep invariants as simple truth assertions."
        )
    return value


# ============================================================================
# SECTION 19: Validation Classification System
# ============================================================================

class ValidationType(str, Enum):
    """
    Classification of validation rules.

    Per MANTRA-FIELD-SPEC:
    - DETERMINISTIC: Rules/formulas, no interpretation needed
    - SEMANTIC: AI validates meaning/quality
    - JUDGMENT: Human decision required
    """
    DETERMINISTIC = "D"  # 78 rules - code/regex/formula
    SEMANTIC = "S"       # 29 rules - AI interpretation
    JUDGMENT = "J"       # 15 rules - human decision


class FieldSource(str, Enum):
    """Source of field value generation."""
    AI = "ai"           # AI generates with prompt
    FORMULA = "formula" # Computed from other fields
    HUMAN = "human"     # Human provides directly
    SYSTEM = "system"   # Auto-generated (UUID, timestamp)


class ValidationRule(BaseModel):
    """A single validation rule with classification."""
    rule_id: str = Field(..., description="Unique rule identifier")
    field: str = Field(..., description="Field this rule applies to")
    description: str = Field(..., description="What this rule checks")
    validation_type: ValidationType = Field(..., description="D/S/J classification")
    check: str = Field(..., description="Check expression or description")
    error_message: str = Field(default="", description="Error message template")


class FieldSpec(BaseModel):
    """Specification for a single field."""
    field_name: str
    source: FieldSource
    prompt: Optional[str] = Field(default=None, description="AI prompt if source=ai")
    formula: Optional[str] = Field(default=None, description="Formula if source=formula")
    validations: List[ValidationRule] = Field(default_factory=list)


# Pre-defined validation rules with classification
VALIDATION_RULES: Dict[str, List[ValidationRule]] = {
    # === Core Fields ===
    "decision_id": [
        ValidationRule(
            rule_id="D-001",
            field="decision_id",
            description="UUID format",
            validation_type=ValidationType.DETERMINISTIC,
            check="regex ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        ),
    ],
    "decision_code": [
        ValidationRule(
            rule_id="D-002",
            field="decision_code",
            description="Format matches pattern",
            validation_type=ValidationType.DETERMINISTIC,
            check="regex ^[A-Z]+-[A-Z]+-[0-9]{3}$",
        ),
        ValidationRule(
            rule_id="D-003",
            field="decision_code",
            description="Unique within system",
            validation_type=ValidationType.DETERMINISTIC,
            check="db unique constraint",
        ),
    ],
    "statement": [
        ValidationRule(
            rule_id="D-004",
            field="statement",
            description="Length 50-1500 chars",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(value) >= 50 and len(value) <= 1500",
        ),
        ValidationRule(
            rule_id="S-001",
            field="statement",
            description="No hedging language",
            validation_type=ValidationType.SEMANTIC,
            check="AI checks for anti-patterns",
        ),
        ValidationRule(
            rule_id="S-002",
            field="statement",
            description="Matches domain/aspect",
            validation_type=ValidationType.SEMANTIC,
            check="AI verifies relevance to classification",
        ),
    ],
    "rationale": [
        ValidationRule(
            rule_id="D-005",
            field="rationale",
            description="Length 100-4000 chars",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(value) >= 100 and len(value) <= 4000",
        ),
        ValidationRule(
            rule_id="S-003",
            field="rationale",
            description="Contains reasoning, not just description",
            validation_type=ValidationType.SEMANTIC,
            check="AI verifies WHY is explained",
        ),
        ValidationRule(
            rule_id="S-004",
            field="rationale",
            description="Logically supports statement",
            validation_type=ValidationType.SEMANTIC,
            check="AI checks coherence with statement",
        ),
    ],
    "constraints": [
        ValidationRule(
            rule_id="D-006",
            field="constraints",
            description="Max 30 constraints",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(constraints) <= 30",
        ),
        ValidationRule(
            rule_id="D-007",
            field="constraints",
            description="Each statement 20-500 chars",
            validation_type=ValidationType.DETERMINISTIC,
            check="all(20 <= len(c.statement) <= 500 for c in constraints)",
        ),
        ValidationRule(
            rule_id="D-008",
            field="constraints",
            description="Unique constraint_ids",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(ids) == len(set(ids))",
        ),
        ValidationRule(
            rule_id="D-009",
            field="constraints",
            description="Starts with MUST/SHOULD/SHALL",
            validation_type=ValidationType.DETERMINISTIC,
            check="regex ^(MUST|MUST NOT|SHOULD|SHALL)",
        ),
        ValidationRule(
            rule_id="S-005",
            field="constraints",
            description="Enforceable and testable",
            validation_type=ValidationType.SEMANTIC,
            check="AI verifies each constraint is actionable",
        ),
    ],
    "invariants": [
        ValidationRule(
            rule_id="D-010",
            field="invariants",
            description="Max 20 invariants",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(invariants) <= 20",
        ),
        ValidationRule(
            rule_id="D-011",
            field="invariants",
            description="Each 10-300 chars",
            validation_type=ValidationType.DETERMINISTIC,
            check="all(10 <= len(i) <= 300 for i in invariants)",
        ),
        ValidationRule(
            rule_id="S-006",
            field="invariants",
            description="No hedging language",
            validation_type=ValidationType.SEMANTIC,
            check="AI checks for absolute statements",
        ),
    ],
    # === Classification Fields ===
    "domain_id": [
        ValidationRule(
            rule_id="D-012",
            field="domain_id",
            description="Valid enum value",
            validation_type=ValidationType.DETERMINISTIC,
            check="value in DomainId",
        ),
        ValidationRule(
            rule_id="J-001",
            field="domain_id",
            description="Classification matches content",
            validation_type=ValidationType.JUDGMENT,
            check="Human confirms domain is correct",
        ),
    ],
    "aspect_id": [
        ValidationRule(
            rule_id="D-013",
            field="aspect_id",
            description="Valid enum value",
            validation_type=ValidationType.DETERMINISTIC,
            check="value in AspectId",
        ),
        ValidationRule(
            rule_id="D-014",
            field="aspect_id",
            description="Compatible with domain",
            validation_type=ValidationType.DETERMINISTIC,
            check="is_aspect_compatible(domain_id, aspect_id)",
        ),
        ValidationRule(
            rule_id="J-002",
            field="aspect_id",
            description="Classification matches content",
            validation_type=ValidationType.JUDGMENT,
            check="Human confirms aspect is correct",
        ),
    ],
    "scope": [
        ValidationRule(
            rule_id="D-015",
            field="scope",
            description="Valid enum value",
            validation_type=ValidationType.DETERMINISTIC,
            check="value in Scope",
        ),
    ],
    "blast_radius": [
        ValidationRule(
            rule_id="D-016",
            field="blast_radius",
            description="Valid enum value",
            validation_type=ValidationType.DETERMINISTIC,
            check="value in BlastRadius",
        ),
        ValidationRule(
            rule_id="S-007",
            field="blast_radius",
            description="Reasonable for scope",
            validation_type=ValidationType.SEMANTIC,
            check="AI validates consistency with scope",
        ),
    ],
    # === Approval Fields ===
    "approved_by": [
        ValidationRule(
            rule_id="D-017",
            field="approved_by",
            description="Not empty when approved",
            validation_type=ValidationType.DETERMINISTIC,
            check="value is not None and len(value) > 0",
        ),
        ValidationRule(
            rule_id="D-018",
            field="approved_by",
            description="Must be human (not AI)",
            validation_type=ValidationType.DETERMINISTIC,
            check="not value.startswith('ai:')",
        ),
        ValidationRule(
            rule_id="J-003",
            field="approved_by",
            description="Has authority to approve",
            validation_type=ValidationType.JUDGMENT,
            check="Human verifies approver authority",
        ),
    ],
    "enriched_by": [
        ValidationRule(
            rule_id="D-019",
            field="enriched_by",
            description="Valid identifier format",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(value) > 0",
        ),
        # Note: Can be AI (ai:*) or human per §10.7.2
    ],
    # === Summary Fields ===
    "structured_summary.headline": [
        ValidationRule(
            rule_id="D-020",
            field="structured_summary.headline",
            description="Max 150 chars",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(value) <= 150",
        ),
    ],
    "structured_summary.abstract": [
        ValidationRule(
            rule_id="D-021",
            field="structured_summary.abstract",
            description="Max 500 chars",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(value) <= 500",
        ),
    ],
    "structured_summary.executive_summary": [
        ValidationRule(
            rule_id="D-022",
            field="structured_summary.executive_summary",
            description="Max 1500 chars",
            validation_type=ValidationType.DETERMINISTIC,
            check="len(value) <= 1500",
        ),
    ],
    "structured_summary.key_points": [
        ValidationRule(
            rule_id="D-023",
            field="structured_summary.key_points",
            description="3-7 items",
            validation_type=ValidationType.DETERMINISTIC,
            check="3 <= len(value) <= 7",
        ),
    ],
    # === Version Fields ===
    "version": [
        ValidationRule(
            rule_id="D-024",
            field="version",
            description="Semantic version format",
            validation_type=ValidationType.DETERMINISTIC,
            check="regex ^[0-9]+\\.[0-9]+\\.[0-9]+$",
        ),
    ],
    # === Temporal Fields ===
    "temporal_validity.sunset_date": [
        ValidationRule(
            rule_id="D-025",
            field="temporal_validity.sunset_date",
            description="Future date if set",
            validation_type=ValidationType.DETERMINISTIC,
            check="value > today() if value else True",
        ),
        ValidationRule(
            rule_id="J-004",
            field="temporal_validity.sunset_date",
            description="Reasonable timeframe",
            validation_type=ValidationType.JUDGMENT,
            check="Human confirms expiry is appropriate",
        ),
    ],
    # === Relation Fields ===
    "supersedes": [
        ValidationRule(
            rule_id="D-026",
            field="supersedes",
            description="Valid UUID if set",
            validation_type=ValidationType.DETERMINISTIC,
            check="valid_uuid(value) if value else True",
        ),
        ValidationRule(
            rule_id="D-027",
            field="supersedes",
            description="Cannot supersede self",
            validation_type=ValidationType.DETERMINISTIC,
            check="value != decision_id",
        ),
        ValidationRule(
            rule_id="D-028",
            field="supersedes",
            description="Referenced decision exists",
            validation_type=ValidationType.DETERMINISTIC,
            check="db exists check",
        ),
    ],
}


def get_validation_rules(field_name: str) -> List[ValidationRule]:
    """Get validation rules for a field."""
    return VALIDATION_RULES.get(field_name, [])


def get_rules_by_type(validation_type: ValidationType) -> List[ValidationRule]:
    """Get all rules of a specific type."""
    result = []
    for rules in VALIDATION_RULES.values():
        for rule in rules:
            if rule.validation_type == validation_type:
                result.append(rule)
    return result


def count_rules_by_type() -> Dict[ValidationType, int]:
    """Count rules by type."""
    counts = {t: 0 for t in ValidationType}
    for rules in VALIDATION_RULES.values():
        for rule in rules:
            counts[rule.validation_type] += 1
    return counts


# Field generation prompts
FIELD_PROMPTS: Dict[str, str] = {
    "statement": """Write a decision statement in 1-3 sentences.
Structure: [SUBJECT] + [ACTION/DECISION] + [SCOPE]

Rules:
- Use present tense, active voice
- Be specific: names, paths, versions
- No hedging: avoid 'might', 'probably', 'consider'
- Max 200 words

Bad: "After discussions, we decided to probably use..."
Good: "We use feature folders for React components."

Context: {user_input}
Domain: {domain_id}
Aspect: {aspect_id}""",

    "rationale": """Explain WHY this decision was made.
Structure: [PROBLEM] → [OPTIONS] → [CHOICE] → [BENEFIT]

Rules:
- State the problem first
- List alternatives considered (if any)
- Explain why THIS choice (not just what)
- Quantify benefits when possible
- Use bullet points for clarity
- Max 500 words

Statement: {statement}
Context: {user_input}""",

    "constraints": """Generate enforceable rules for this decision.
Each constraint:
- Starts with MUST, MUST NOT, SHOULD, SHALL
- One rule per constraint
- Include example when helpful
- Max 60 words each

Format: constraint_id (C-001), type, statement

Statement: {statement}
Rationale: {rationale}""",

    "invariants": """List things that must ALWAYS be true.
Each invariant:
- States absolute truth (no exceptions)
- One assertion per item
- Testable
- Max 40 words each

Statement: {statement}
Constraints: {constraints}""",

    "domain_id": """Classify into ONE domain: ARCH, CODE, DATA, SEC, OPS, PROC, UI, API, TEST, DOC.
Statement: {statement}
Return ONLY the code.""",

    "aspect_id": """Classify the aspect within domain {domain_id}.
Options: {valid_aspects}
Statement: {statement}
Return ONLY the code.""",

    "structured_summary.headline": """Write ONE sentence (max 20 words) summarizing the decision.
Statement: {statement}""",

    "structured_summary.abstract": """Write 2-3 sentences covering WHAT and WHY. Max 80 words.
Statement: {statement}
Rationale: {rationale}""",

    "structured_summary.executive_summary": """Write 1 paragraph (100-200 words) for stakeholders.
Statement: {statement}
Rationale: {rationale}
Scope: {scope}""",

    "structured_summary.key_points": """List 3-7 main takeaways. Each: 1 sentence, actionable.
Statement: {statement}
Constraints: {constraints}""",

    "structured_summary.for_developers": """Write ~100 words for developers. Focus: HOW to implement.
Statement: {statement}
Constraints: {constraints}""",

    "structured_summary.for_architects": """Write ~100 words for architects. Focus: System design implications.
Statement: {statement}
Rationale: {rationale}""",

    "structured_summary.for_managers": """Write ~100 words for managers. Focus: Business impact, resources.
Statement: {statement}
Scope: {scope}""",
}


def get_field_prompt(field_name: str, context: Dict[str, Any]) -> Optional[str]:
    """Get AI prompt for a field, formatted with context."""
    prompt = FIELD_PROMPTS.get(field_name)
    if not prompt:
        return None
    try:
        return prompt.format(**context)
    except KeyError:
        # Return unformatted if context missing
        return prompt
