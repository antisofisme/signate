"""
MANTRA-SCHEMA-002: Comprehensive Decision Schema v2

This module provides the enhanced JSON Schema and validation types for the Decision Matrix.
Per MANTRA-LAW-001, this schema is constitutional and immutable once stored.

DESIGN GOALS:
1. Score 9.5+/10 for Knowledge, Guidance, Search, and Governance dimensions
2. Handle ALL identified edge cases
3. Remain implementable (not over-engineered)
4. Follow industry best practices (ADR, TOGAF, compliance frameworks)

KEY ENHANCEMENTS over v1:
- Temporal validity (effective_date, sunset_date, review_by)
- Multi-stakeholder governance (stakeholders, approval_workflow)
- Compliance tracking (compliance_references, audit_trail)
- AI/LLM optimization (embedding_text, token_count, prompt_hints)
- Graph relationships (enhanced relations with context)
- Versioning improvements (change_type, migration_guide)
- Search optimization (search_keywords, aliases)
- Quality metadata (quality_score, validation_history)
- Lineage tracking (derived_from, influenced_decisions)
- Execution guidance (implementation_guidance, anti_patterns)

MIGRATION PATH:
- All v1 fields remain with same semantics
- New fields have sensible defaults or are Optional
- Database migration adds columns with NULL defaults
- Existing records remain valid without modification
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
from datetime import datetime, date
import uuid
import re
import hashlib


# ============================================================================
# SECTION 1: Core Enumerations (Extended from v1)
# ============================================================================

class DomainId(str, Enum):
    """
    4 Domains per MANTRA-LAW-001 section 3

    Mapping:
    - INT  = DOMAIN-1 (section 3.2) - Intent and Direction
    - ARCH = DOMAIN-2 (section 3.3) - Architecture and Boundaries
    - CTL  = DOMAIN-3 (section 3.4) - Control, Policy and Risk
    - EVO  = DOMAIN-4 (section 3.5) - Execution and Evolution
    """
    INT = "INT"    # Intent and Direction (WHY/WHAT)
    ARCH = "ARCH"  # Architecture and Boundaries (HOW/WHERE)
    CTL = "CTL"    # Control, Policy and Risk (CAN/MUST NOT)
    EVO = "EVO"    # Execution and Evolution (CHANGE SAFELY)


class AspectId(str, Enum):
    """
    16 Aspects per MANTRA-LAW-001 section 3.2-3.5

    DOMAIN-1 (INT) - Intent and Direction:
    - A01: Vision and Outcome
    - A02: Problem Statement
    - A03: Scope and Non-Goals
    - A04: Principles and Values

    DOMAIN-2 (ARCH) - Architecture and Boundaries:
    - A05: Domain and Bounded Context
    - A06: Service and Module Boundary
    - A07: Data Ownership and Sovereignty
    - A08: Integration and Contract Model

    DOMAIN-3 (CTL) - Control, Policy and Risk:
    - A09: Policy and Rules
    - A10: Approval and Authority Model
    - A11: Security and Compliance Posture
    - A12: Risk and Blast Radius

    DOMAIN-4 (EVO) - Execution and Evolution:
    - A13: Decision Lifecycle
    - A14: Reversibility and Exit Strategy
    - A15: Environment and Promotion Rules
    - A16: Anti-Drift and Consistency
    """
    # DOMAIN-1 (INT): Intent and Direction
    A01 = "A01"  # Vision and Outcome
    A02 = "A02"  # Problem Statement
    A03 = "A03"  # Scope and Non-Goals
    A04 = "A04"  # Principles and Values
    # DOMAIN-2 (ARCH): Architecture and Boundaries
    A05 = "A05"  # Domain and Bounded Context
    A06 = "A06"  # Service and Module Boundary
    A07 = "A07"  # Data Ownership and Sovereignty
    A08 = "A08"  # Integration and Contract Model
    # DOMAIN-3 (CTL): Control, Policy and Risk
    A09 = "A09"  # Policy and Rules
    A10 = "A10"  # Approval and Authority Model
    A11 = "A11"  # Security and Compliance Posture
    A12 = "A12"  # Risk and Blast Radius
    # DOMAIN-4 (EVO): Execution and Evolution
    A13 = "A13"  # Decision Lifecycle
    A14 = "A14"  # Reversibility and Exit Strategy
    A15 = "A15"  # Environment and Promotion Rules
    A16 = "A16"  # Anti-Drift and Consistency


class Scope(str, Enum):
    """Decision scope per MANTRA-DEC-003"""
    ORGANIZATION = "ORGANIZATION"  # Applies across entire organization
    DOMAIN = "DOMAIN"              # Applies within a bounded domain/team
    APPLICATION = "APPLICATION"    # Applies to specific application only


class BlastRadius(str, Enum):
    """Impact level per MANTRA-DEC-003"""
    LOW = "LOW"           # Single component, easy rollback
    MEDIUM = "MEDIUM"     # Multiple components, moderate effort to change
    HIGH = "HIGH"         # Cross-service impact, significant coordination needed
    CRITICAL = "CRITICAL" # Platform-wide, requires extensive planning


class ConstraintType(str, Enum):
    """Constraint type per MANTRA-SCHEMA-001"""
    PROHIBITION = "PROHIBITION"  # MUST NOT do X
    REQUIREMENT = "REQUIREMENT"  # MUST do X
    LIMITATION = "LIMITATION"    # MAY do X only under conditions
    PREFERENCE = "PREFERENCE"    # SHOULD prefer X (v2: softer guidance)
    EXCEPTION = "EXCEPTION"      # v2: Carve-out from other constraints


class RelationType(str, Enum):
    """
    Typed relation types per Decision Graph Model.

    v1 Relations:
    - depends_on: This decision requires the target decision to be in effect
    - conflicts_with: This decision cannot coexist with target decision
    - informed_by: This decision was influenced by target decision

    v2 Relations (NEW):
    - superseded_by: Target decision supersedes this one (reverse of supersedes)
    - enables: This decision enables/unlocks the target decision
    - constrains: This decision adds constraints to target decision
    - implements: This decision implements policy/principle from target
    - extends: This decision extends/specializes the target decision
    """
    # v1 Relations
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    INFORMED_BY = "informed_by"
    # v2 Relations
    SUPERSEDED_BY = "superseded_by"
    ENABLES = "enables"
    CONSTRAINS = "constrains"
    IMPLEMENTS = "implements"
    EXTENDS = "extends"


class SectionType(str, Enum):
    """Section types for detailed content structure (MICS Long Content Strategy)"""
    OVERVIEW = "OVERVIEW"      # High-level explanation
    RULES = "RULES"            # List of rules/conventions
    EXAMPLES = "EXAMPLES"      # Code examples (good/bad patterns)
    STRUCTURE = "STRUCTURE"    # Folder/file structures, hierarchies
    DIAGRAM = "DIAGRAM"        # ASCII/Mermaid diagrams
    REFERENCE = "REFERENCE"    # External links, documentation references
    RATIONALE = "RATIONALE"    # v2: Extended rationale/context
    ALTERNATIVES = "ALTERNATIVES"  # v2: Alternatives considered
    MIGRATION = "MIGRATION"    # v2: Migration/adoption guide
    ANTIPATTERN = "ANTIPATTERN"  # v2: What NOT to do


class ChangeType(str, Enum):
    """
    v2: Type of change from previous version.

    Helps understand evolution without deep diff analysis.
    """
    INITIAL = "INITIAL"           # First version of this decision
    CLARIFICATION = "CLARIFICATION"  # Wording improved, same intent
    EXTENSION = "EXTENSION"       # Added scope, new constraints
    RELAXATION = "RELAXATION"     # Removed/loosened constraints
    CORRECTION = "CORRECTION"     # Fixed error in previous version
    DEPRECATION = "DEPRECATION"   # Marking for future removal
    REPLACEMENT = "REPLACEMENT"   # Fundamentally different approach


class StakeholderRole(str, Enum):
    """
    v2: Stakeholder roles for multi-stakeholder governance.
    """
    AUTHOR = "AUTHOR"             # Created the decision
    APPROVER = "APPROVER"         # Has authority to approve
    REVIEWER = "REVIEWER"         # Provided feedback
    AFFECTED = "AFFECTED"         # Team/domain affected by decision
    CONSULTANT = "CONSULTANT"     # Subject matter expert consulted
    IMPLEMENTER = "IMPLEMENTER"   # Responsible for implementation


class ComplianceFramework(str, Enum):
    """
    v2: Common compliance frameworks for reference.
    """
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI_DSS"
    TOGAF = "TOGAF"
    CUSTOM = "CUSTOM"


class ApprovalStatus(str, Enum):
    """
    v2: Status of approval workflow.

    NOTE: This is WORKFLOW status, not decision status.
    Per MANTRA-LAW-001, decisions themselves have no lifecycle status.
    """
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"  # Approved with conditions


# ============================================================================
# SECTION 2: Area Tags (Extended)
# ============================================================================

class AreaTag(str, Enum):
    """Area tags for decision impact - v2 extended"""
    # v1 Tags
    FE = "FE"              # Frontend
    BE = "BE"              # Backend
    DB = "DB"              # Database
    INFRA = "INFRA"        # Infrastructure
    CICD = "CICD"          # CI/CD Pipeline
    API = "API"            # API Design
    SECURITY = "SECURITY"  # Security
    DEVOPS = "DEVOPS"      # DevOps
    # v2 Tags
    DATA = "DATA"          # Data Engineering/Analytics
    ML = "ML"              # Machine Learning/AI
    MOBILE = "MOBILE"      # Mobile Development
    TESTING = "TESTING"    # Testing Strategy
    PERF = "PERF"          # Performance
    UX = "UX"              # User Experience
    ARCH = "ARCH"          # Architecture
    DOCS = "DOCS"          # Documentation
    GOVERNANCE = "GOVERNANCE"  # Governance/Process


# ============================================================================
# SECTION 3: Domain Compatibility Matrix
# ============================================================================

DOMAIN_ASPECT_MATRIX = {
    DomainId.INT: [AspectId.A01, AspectId.A02, AspectId.A03, AspectId.A04],
    DomainId.ARCH: [AspectId.A05, AspectId.A06, AspectId.A07, AspectId.A08],
    DomainId.CTL: [AspectId.A09, AspectId.A10, AspectId.A11, AspectId.A12],
    DomainId.EVO: [AspectId.A13, AspectId.A14, AspectId.A15, AspectId.A16],
}

DOMAIN_LABELS = {
    DomainId.INT: "Intent and Direction",
    DomainId.ARCH: "Architecture and Boundaries",
    DomainId.CTL: "Control, Policy and Risk",
    DomainId.EVO: "Execution and Evolution",
}

ASPECT_LABELS = {
    AspectId.A01: "Vision and Outcome",
    AspectId.A02: "Problem Statement",
    AspectId.A03: "Scope and Non-Goals",
    AspectId.A04: "Principles and Values",
    AspectId.A05: "Domain and Bounded Context",
    AspectId.A06: "Service and Module Boundary",
    AspectId.A07: "Data Ownership and Sovereignty",
    AspectId.A08: "Integration and Contract Model",
    AspectId.A09: "Policy and Rules",
    AspectId.A10: "Approval and Authority Model",
    AspectId.A11: "Security and Compliance Posture",
    AspectId.A12: "Risk and Blast Radius",
    AspectId.A13: "Decision Lifecycle",
    AspectId.A14: "Reversibility and Exit Strategy",
    AspectId.A15: "Environment and Promotion Rules",
    AspectId.A16: "Anti-Drift and Consistency",
}


def is_aspect_compatible(domain_id: DomainId, aspect_id: AspectId) -> bool:
    """Check if aspect is compatible with domain"""
    return aspect_id in DOMAIN_ASPECT_MATRIX.get(domain_id, [])


# ============================================================================
# SECTION 4: Sub-Models (Nested Structures)
# ============================================================================

class Constraint(BaseModel):
    """
    Constraint entry - represents a single enforceable rule.

    v2 Enhancements:
    - enforcement_level: How strictly this should be enforced
    - automated_check: Whether this can be checked automatically
    - check_command: Optional command/script to verify compliance
    """
    constraint_id: str = Field(..., min_length=1, description="Unique ID like C-001")
    statement: str = Field(..., min_length=1, description="The constraint statement")
    type: ConstraintType = Field(..., description="Type of constraint")

    # v2 Fields
    enforcement_level: Optional[str] = Field(
        default="STRICT",
        description="STRICT: Block violations, ADVISORY: Warn only, AUDIT: Log for review"
    )
    automated_check: bool = Field(
        default=False,
        description="Whether this constraint can be verified automatically"
    )
    check_command: Optional[str] = Field(
        default=None,
        description="CLI command or script path to verify this constraint"
    )
    exception_process: Optional[str] = Field(
        default=None,
        description="How to request an exception to this constraint"
    )

    class Config:
        extra = "forbid"


class Relation(BaseModel):
    """
    Typed relation to another decision.

    v2 Enhancements:
    - context: Why this relation exists
    - strength: How strong/important is this relation
    - bidirectional: Whether the inverse relation should also be created
    """
    target_id: str = Field(..., description="UUID of the target decision")
    type: RelationType = Field(..., description="Type of relation")

    # v2 Fields
    context: Optional[str] = Field(
        default=None,
        description="Explanation of why this relation exists"
    )
    strength: Optional[str] = Field(
        default="NORMAL",
        description="STRONG: Critical dependency, NORMAL: Standard relation, WEAK: Informational"
    )
    bidirectional: bool = Field(
        default=False,
        description="If true, create inverse relation on target"
    )

    class Config:
        extra = "forbid"


class ContentSection(BaseModel):
    """
    Structured section for detailed content (MICS Long Content Strategy).

    v2 Enhancements:
    - token_count: Pre-computed token count for LLM context budgeting
    - importance: Priority for inclusion when token-limited
    """
    section_id: str = Field(..., min_length=1, description="Unique ID like S-001")
    title: str = Field(..., min_length=1, description="Section title")
    section_type: SectionType = Field(..., description="Type of content")
    content: str = Field(..., min_length=1, description="Markdown content")
    order: int = Field(default=0, ge=0, description="Display order (0-based)")

    # v2 Fields
    token_count: Optional[int] = Field(
        default=None,
        description="Pre-computed token count (GPT-4 tokenizer)"
    )
    importance: Optional[str] = Field(
        default="NORMAL",
        description="HIGH: Always include, NORMAL: Include if space, LOW: Optional"
    )

    class Config:
        extra = "forbid"


class Stakeholder(BaseModel):
    """
    v2: Stakeholder information for multi-stakeholder governance.

    Enables tracking who is involved in decision lifecycle.
    """
    identifier: str = Field(..., description="Person/team identifier (email, team name)")
    role: StakeholderRole = Field(..., description="Role in this decision")
    added_at: Optional[datetime] = Field(default=None, description="When stakeholder was added")
    comment: Optional[str] = Field(default=None, description="Stakeholder's input/comment")

    class Config:
        extra = "forbid"


class ApprovalRecord(BaseModel):
    """
    v2: Record of an approval action.

    Enables multi-approver workflows and audit trails.
    """
    approver_id: str = Field(..., description="Approver identifier")
    status: ApprovalStatus = Field(..., description="Approval status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    comment: Optional[str] = Field(default=None, description="Approval comment")
    conditions: Optional[List[str]] = Field(
        default=None,
        description="Conditions for conditional approval"
    )

    class Config:
        extra = "forbid"


class ComplianceReference(BaseModel):
    """
    v2: Reference to compliance framework requirement.

    Links decision to external compliance requirements.
    """
    framework: ComplianceFramework = Field(..., description="Compliance framework")
    requirement_id: str = Field(..., description="Specific requirement ID (e.g., SOC2 CC6.1)")
    description: Optional[str] = Field(default=None, description="How this decision addresses requirement")
    evidence_location: Optional[str] = Field(
        default=None,
        description="Where compliance evidence can be found"
    )

    class Config:
        extra = "forbid"


class TemporalValidity(BaseModel):
    """
    v2: Temporal validity information.

    Enables time-bounded decisions and scheduled reviews.
    """
    effective_date: Optional[date] = Field(
        default=None,
        description="When this decision becomes effective"
    )
    sunset_date: Optional[date] = Field(
        default=None,
        description="When this decision expires (if ever)"
    )
    review_by: Optional[date] = Field(
        default=None,
        description="Date by which this decision should be reviewed"
    )
    review_frequency_days: Optional[int] = Field(
        default=None,
        description="How often to review (e.g., 90 for quarterly)"
    )

    class Config:
        extra = "forbid"


class QualityMetadata(BaseModel):
    """
    v2: Quality assessment metadata.

    Captures quality scoring results for fast filtering.
    """
    overall_score: int = Field(default=0, ge=0, le=100)
    grade: str = Field(default="UNKNOWN", description="EXCELLENT/GOOD/FAIR/POOR/REJECT")
    statement_score: int = Field(default=0, ge=0, le=100)
    rationale_score: int = Field(default=0, ge=0, le=100)
    coherence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    validated_at: Optional[datetime] = Field(default=None)
    validation_version: Optional[str] = Field(
        default=None,
        description="Version of validator used"
    )

    class Config:
        extra = "forbid"


class ImplementationGuidance(BaseModel):
    """
    v2: Implementation guidance for adopting this decision.

    Helps teams understand HOW to apply the decision.
    """
    estimated_effort: Optional[str] = Field(
        default=None,
        description="SMALL/MEDIUM/LARGE/XLARGE"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="What must be in place before implementing"
    )
    steps: List[str] = Field(
        default_factory=list,
        description="High-level implementation steps"
    )
    common_pitfalls: List[str] = Field(
        default_factory=list,
        description="Common mistakes to avoid"
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="How to know implementation is complete"
    )
    rollback_procedure: Optional[str] = Field(
        default=None,
        description="How to roll back if needed"
    )

    class Config:
        extra = "forbid"


class LLMOptimization(BaseModel):
    """
    v2: LLM/AI optimization metadata.

    Pre-computed data for efficient AI context injection.
    """
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

    class Config:
        extra = "forbid"


class SearchMetadata(BaseModel):
    """
    v2: Search optimization metadata.

    Enables better full-text and semantic search.
    """
    aliases: List[str] = Field(
        default_factory=list,
        description="Alternative names/abbreviations for this decision"
    )
    search_keywords: List[str] = Field(
        default_factory=list,
        description="Additional search keywords not in content"
    )
    question_variants: List[str] = Field(
        default_factory=list,
        description="Questions this decision answers (for Q&A search)"
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 5: Main Decision Model (v2)
# ============================================================================

class DecisionV2(BaseModel):
    """
    Decision record per MANTRA-SCHEMA-002 (v2)

    This is the enhanced core aggregate of ATLAS_MANTRA.
    Per MANTRA-LAW-001, stored decisions are ABSOLUTELY IMMUTABLE.

    v2 DESIGN PRINCIPLES:
    1. All v1 fields preserved with same semantics
    2. New fields are Optional with sensible defaults
    3. Computed fields derived from content where possible
    4. Denormalization for search/query performance
    5. Pre-computation for AI/LLM optimization

    FIELD CATEGORIES:
    - Identity: decision_id, decision_code
    - Classification: domain_id, aspect_id
    - Content (Layer A): statement, rationale, constraints, invariants
    - Content (Layer B): detailed_content, sections, content_summary
    - Metadata: scope, blast_radius, version, tags, tech_stack
    - Authorship: created_by, created_at, approved_by, approved_at
    - Relations: supersedes, related_decisions, relations
    - Temporal (v2): temporal_validity
    - Governance (v2): stakeholders, approvals, compliance_references
    - Quality (v2): quality_metadata
    - Implementation (v2): implementation_guidance
    - Search (v2): search_metadata
    - AI/LLM (v2): llm_optimization
    """

    # =========================================================================
    # Identity Fields
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
    # Classification Fields
    # =========================================================================

    domain_id: DomainId = Field(..., description="Domain classification")
    aspect_id: AspectId = Field(..., description="Aspect within domain")

    # =========================================================================
    # Content Fields - Layer A (Executive Summary)
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
    constraints: List[Constraint] = Field(
        default_factory=list,
        description="Enforceable rules/requirements"
    )
    invariants: List[str] = Field(
        default_factory=list,
        description="Things that must always be true"
    )

    # =========================================================================
    # Content Fields - Layer B (Detailed Specification)
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
    # Core Metadata Fields
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
    # Authorship Fields
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
    # Relation Fields
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
    # v2: Temporal Validity
    # =========================================================================

    temporal_validity: Optional[TemporalValidity] = Field(
        default=None,
        description="Time-bounded validity and review schedule"
    )

    # =========================================================================
    # v2: Multi-Stakeholder Governance
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
    # v2: Compliance Tracking
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
    # v2: Versioning Enhancements
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
    # v2: Quality Metadata
    # =========================================================================

    quality_metadata: Optional[QualityMetadata] = Field(
        default=None,
        description="Quality scoring results (denormalized for queries)"
    )

    # =========================================================================
    # v2: Implementation Guidance
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
    # v2: Search Optimization
    # =========================================================================

    search_metadata: Optional[SearchMetadata] = Field(
        default=None,
        description="Search optimization data"
    )

    # =========================================================================
    # v2: AI/LLM Optimization
    # =========================================================================

    llm_optimization: Optional[LLMOptimization] = Field(
        default=None,
        description="Pre-computed data for AI context injection"
    )

    # =========================================================================
    # v2: Lineage Tracking
    # =========================================================================

    derived_from: List[str] = Field(
        default_factory=list,
        description="External sources this decision is based on (URLs, doc refs)"
    )
    influenced_decisions: List[str] = Field(
        default_factory=list,
        description="Decision IDs that cite this decision (denormalized, updated on reference)"
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

    @field_validator("invariants")
    @classmethod
    def validate_invariants(cls, v):
        """Ensure invariants are non-empty strings"""
        for i, inv in enumerate(v):
            if not inv or len(inv.strip()) == 0:
                raise ValueError(f"Invariant at index {i} must not be empty")
        return v

    @field_validator("constraints")
    @classmethod
    def validate_constraint_uniqueness(cls, v):
        """Ensure constraint_ids are unique within decision"""
        ids = [c.constraint_id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("constraint_id must be unique within decision")
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

    @model_validator(mode='after')
    def validate_approval_workflow(self):
        """Ensure approval workflow matches approvals"""
        if self.approval_workflow == "SINGLE" and len(self.approvals) > 1:
            # Single workflow but multiple approvals - mark latest as effective
            pass  # Allow this - just use latest
        return self

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_all_tags(self) -> List[str]:
        """Get all tags including inferred from tech_stack."""
        all_tags = set(self.tags)
        # Could add inference logic here
        return list(all_tags)

    def get_total_token_estimate(self) -> int:
        """Estimate total tokens for LLM context."""
        if self.llm_optimization and self.llm_optimization.total_token_count:
            return self.llm_optimization.total_token_count
        # Rough estimate: ~0.75 tokens per character
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
        # Default: combine key content
        parts = [
            self.statement,
            self.rationale,
            " ".join(self.invariants),
            " ".join(c.statement for c in self.constraints),
        ]
        return " ".join(parts)

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "550e8400-e29b-41d4-a716-446655440000",
                "decision_code": "ARCH-A06-001-v1.0.0",
                "domain_id": "ARCH",
                "aspect_id": "A06",
                "statement": "All frontend projects must follow feature-based folder structure with strict module boundaries.",
                "rationale": "Feature-based structure improves code discoverability, enables lazy loading, and enforces bounded contexts. Each feature is self-contained.",
                "constraints": [
                    {
                        "constraint_id": "C-001",
                        "statement": "Feature folders must have index.ts as single export point",
                        "type": "REQUIREMENT",
                        "enforcement_level": "STRICT",
                        "automated_check": True,
                        "check_command": "npm run lint:exports"
                    }
                ],
                "invariants": ["Module boundaries are enforced at build time"],
                "scope": "ORGANIZATION",
                "blast_radius": "HIGH",
                "version": "1.0.0",
                "tags": ["FE", "ARCH"],
                "tech_stack": ["TypeScript", "React"],
                "temporal_validity": {
                    "effective_date": "2024-01-01",
                    "review_by": "2025-01-01"
                },
                "implementation_guidance": {
                    "estimated_effort": "MEDIUM",
                    "prerequisites": ["TypeScript configured", "ESLint installed"],
                    "steps": ["Create features/ directory", "Move code to feature folders"]
                },
                "change_type": "INITIAL"
            }
        }


# ============================================================================
# SECTION 6: Input/Output DTOs
# ============================================================================

class DecisionCreateV2(BaseModel):
    """
    Input DTO for creating a new v2 decision.

    Only required fields are mandatory; v2 enhancements are optional.
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

    # Optional v1 fields
    constraints: List[Constraint] = Field(default_factory=list)
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
    change_summary: Optional[str] = None
    migration_guide: Optional[str] = None
    breaking_changes: List[str] = Field(default_factory=list)
    implementation_guidance: Optional[ImplementationGuidance] = None
    anti_patterns: List[str] = Field(default_factory=list)
    search_metadata: Optional[SearchMetadata] = None
    derived_from: List[str] = Field(default_factory=list)


# ============================================================================
# SECTION 7: Migration Helpers
# ============================================================================

def migrate_v1_to_v2(v1_decision: dict) -> DecisionV2:
    """
    Migrate a v1 decision dictionary to v2 DecisionV2 model.

    All v1 fields map directly; v2 fields get sensible defaults.
    """
    # Map v1 fields directly
    v2_data = {
        "decision_id": v1_decision.get("decision_id"),
        "decision_code": v1_decision.get("decision_code"),
        "domain_id": v1_decision.get("domain_id"),
        "aspect_id": v1_decision.get("aspect_id"),
        "statement": v1_decision.get("statement"),
        "rationale": v1_decision.get("rationale"),
        "scope": v1_decision.get("scope"),
        "blast_radius": v1_decision.get("blast_radius"),
        "version": v1_decision.get("version"),
        "created_by": v1_decision.get("created_by"),
        "created_at": v1_decision.get("created_at"),
        "approved_by": v1_decision.get("approved_by"),
        "approved_at": v1_decision.get("approved_at"),
        "supersedes": v1_decision.get("supersedes"),
        "related_decisions": v1_decision.get("related_decisions", []),
        "tags": v1_decision.get("tags", []),
        "tech_stack": v1_decision.get("tech_stack", []),
        "detailed_content": v1_decision.get("detailed_content"),
        "content_summary": v1_decision.get("content_summary"),
    }

    # Migrate constraints
    v1_constraints = v1_decision.get("constraints", [])
    v2_data["constraints"] = [
        Constraint(
            constraint_id=c.get("constraint_id"),
            statement=c.get("statement"),
            type=ConstraintType(c.get("type")),
        )
        for c in v1_constraints
    ]

    # Migrate invariants
    v2_data["invariants"] = v1_decision.get("invariants", [])

    # Migrate relations
    v1_relations = v1_decision.get("relations", [])
    v2_data["relations"] = [
        Relation(
            target_id=r.get("target_id"),
            type=RelationType(r.get("type")),
        )
        for r in v1_relations
    ]

    # Migrate sections
    v1_sections = v1_decision.get("sections", [])
    v2_data["sections"] = [
        ContentSection(
            section_id=s.get("section_id"),
            title=s.get("title"),
            section_type=SectionType(s.get("section_type")),
            content=s.get("content"),
            order=s.get("order", 0),
        )
        for s in v1_sections
    ]

    # Set v2 defaults
    v2_data["change_type"] = ChangeType.INITIAL

    return DecisionV2(**v2_data)


# ============================================================================
# SECTION 8: Database Indexing Strategy
# ============================================================================

DATABASE_INDEXES = """
-- Primary indexes (required)
CREATE UNIQUE INDEX IF NOT EXISTS idx_decisions_id ON decisions(decision_id);
CREATE INDEX IF NOT EXISTS idx_decisions_domain ON decisions(domain_id);
CREATE INDEX IF NOT EXISTS idx_decisions_aspect ON decisions(aspect_id);
CREATE INDEX IF NOT EXISTS idx_decisions_domain_aspect ON decisions(domain_id, aspect_id);
CREATE INDEX IF NOT EXISTS idx_decisions_scope ON decisions(scope);
CREATE INDEX IF NOT EXISTS idx_decisions_blast_radius ON decisions(blast_radius);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_supersedes ON decisions(supersedes) WHERE supersedes IS NOT NULL;

-- v2 indexes for temporal queries
CREATE INDEX IF NOT EXISTS idx_decisions_effective_date
    ON decisions((temporal_validity->>'effective_date')::date)
    WHERE temporal_validity IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_decisions_sunset_date
    ON decisions((temporal_validity->>'sunset_date')::date)
    WHERE temporal_validity IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_decisions_review_by
    ON decisions((temporal_validity->>'review_by')::date)
    WHERE temporal_validity IS NOT NULL;

-- v2 indexes for quality filtering
CREATE INDEX IF NOT EXISTS idx_decisions_quality_score
    ON decisions((quality_metadata->>'overall_score')::int)
    WHERE quality_metadata IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_decisions_quality_grade
    ON decisions(quality_metadata->>'grade')
    WHERE quality_metadata IS NOT NULL;

-- v2 indexes for full-text search
CREATE INDEX IF NOT EXISTS idx_decisions_statement_fts
    ON decisions USING gin(to_tsvector('english', statement));
CREATE INDEX IF NOT EXISTS idx_decisions_rationale_fts
    ON decisions USING gin(to_tsvector('english', rationale));
CREATE INDEX IF NOT EXISTS idx_decisions_combined_fts
    ON decisions USING gin(to_tsvector('english', statement || ' ' || rationale));

-- v2 indexes for tag/tech filtering (GIN for array containment)
CREATE INDEX IF NOT EXISTS idx_decisions_tags ON decisions USING gin(tags jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_decisions_tech_stack ON decisions USING gin(tech_stack jsonb_path_ops);

-- v2 indexes for compliance queries
CREATE INDEX IF NOT EXISTS idx_decisions_compliance
    ON decisions USING gin(compliance_references);

-- v2 composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_decisions_active_by_domain
    ON decisions(domain_id, created_at DESC)
    WHERE supersedes IS NULL;
"""


# ============================================================================
# SECTION 9: Validation Rules Summary
# ============================================================================

VALIDATION_RULES = """
SCHEMA VALIDATION (S-xxx):
- S-001: decision_id required, UUID format
- S-002: domain_id required, enum value
- S-003: aspect_id required, enum value
- S-004: statement required, non-empty string
- S-005: rationale required, non-empty string
- S-006: scope required, enum value
- S-007: blast_radius required, enum value
- S-008: version required, semver format
- S-009: constraints array, valid structure
- S-010: invariants array of strings
- S-011: relations array, valid structure
- S-012 (v2): temporal_validity valid date format
- S-013 (v2): stakeholders valid structure
- S-014 (v2): approvals valid structure
- S-015 (v2): compliance_references valid structure

CONSISTENCY VALIDATION (D-xxx):
- D-001: aspect must be compatible with domain
- D-002: constraint_ids unique within decision
- D-003: section_ids unique within decision
- D-004: supersedes must reference existing decision
- D-005: supersedes must be same domain/aspect
- D-006: related_decisions must exist
- D-007: no circular relations
- D-008 (v2): effective_date <= sunset_date
- D-009 (v2): review_by >= created_at
- D-010 (v2): breaking_changes requires change_type != INITIAL

GOVERNANCE VALIDATION (L-xxx):
- L-001: created_by must not be AI
- L-002: approved_by must not be AI
- L-003 (v2): CRITICAL blast_radius requires approval
- L-004 (v2): compliance_references validated against framework
- L-005 (v2): multi-approver workflow satisfied

QUALITY VALIDATION (Q-xxx):
- Q-001: statement 10-200 words
- Q-002: statement has action verb
- Q-003: no vague words
- Q-004: technical terminology present
- Q-005: rationale explains "why"
- Q-006: rationale references context
- Q-007: constraints are actionable
- Q-008: constraints are verifiable
- Q-009 (v2): implementation_guidance if HIGH/CRITICAL
- Q-010 (v2): anti_patterns for PROHIBITION constraints
"""
