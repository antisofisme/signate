"""
MANTRA-SCHEMA-001 Implementation

This module provides the JSON Schema and validation types for the Decision Matrix.
Per MANTRA-LAW-001, this schema is constitutional and immutable.

4 Domains x 4 Aspects = 16 Decision Taxonomy

CRITICAL (Human Decision - Phase 4):
- Decision records are ABSOLUTELY IMMUTABLE
- There is NO lifecycle or status field
- Decision evolution is expressed ONLY via version + supersedes
- Domain models MUST NOT encode active/current/deprecated/valid semantics
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid
import re


# ============================================================================
# Enumerations per MANTRA-SCHEMA-001
# ============================================================================
#
# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN MAPPING (Abbreviated Code → MANTRA-LAW-001 Reference)
# ═══════════════════════════════════════════════════════════════════════════
#
# | Code | Law Reference   | Full Name                  | Scope          |
# |------|-----------------|----------------------------|----------------|
# | INT  | DOMAIN-1, §3.2  | Intent & Direction         | WHY / WHAT     |
# | ARCH | DOMAIN-2, §3.3  | Architecture & Boundaries  | HOW / WHERE    |
# | CTL  | DOMAIN-3, §3.4  | Control, Policy & Risk     | CAN / MUST NOT |
# | EVO  | DOMAIN-4, §3.5  | Execution & Evolution      | CHANGE SAFELY  |
#
# ═══════════════════════════════════════════════════════════════════════════
# ASPECT MAPPING (4 Aspects per Domain = 16 Total)
# ═══════════════════════════════════════════════════════════════════════════
#
# DOMAIN-1 (INT):  A01 Vision, A02 Problem, A03 Scope, A04 Principles
# DOMAIN-2 (ARCH): A05 Domain, A06 Service, A07 Data, A08 Integration
# DOMAIN-3 (CTL):  A09 Policy, A10 Authority, A11 Security, A12 Risk
# DOMAIN-4 (EVO):  A13 Lifecycle, A14 Reversibility, A15 Environment, A16 Drift
#
# ============================================================================

class DomainId(str, Enum):
    """
    4 Domains per MANTRA-LAW-001 §3

    Mapping:
    - INT  = DOMAIN-1 (§3.2) - Intent & Direction
    - ARCH = DOMAIN-2 (§3.3) - Architecture & Boundaries
    - CTL  = DOMAIN-3 (§3.4) - Control, Policy & Risk
    - EVO  = DOMAIN-4 (§3.5) - Execution & Evolution
    """
    INT = "INT"    # DOMAIN-1: Intent & Direction (WHY/WHAT)
    ARCH = "ARCH"  # DOMAIN-2: Architecture & Boundaries (HOW/WHERE)
    CTL = "CTL"    # DOMAIN-3: Control, Policy & Risk (CAN/MUST NOT)
    EVO = "EVO"    # DOMAIN-4: Execution & Evolution (CHANGE SAFELY)


class AspectId(str, Enum):
    """
    16 Aspects per MANTRA-LAW-001 §3.2-§3.5

    DOMAIN-1 (INT) - Intent & Direction:
    - A01: Vision & Outcome
    - A02: Problem Statement
    - A03: Scope & Non-Goals
    - A04: Principles & Values

    DOMAIN-2 (ARCH) - Architecture & Boundaries:
    - A05: Domain & Bounded Context
    - A06: Service & Module Boundary
    - A07: Data Ownership & Sovereignty
    - A08: Integration & Contract Model

    DOMAIN-3 (CTL) - Control, Policy & Risk:
    - A09: Policy & Rules
    - A10: Approval & Authority Model
    - A11: Security & Compliance Posture
    - A12: Risk & Blast Radius

    DOMAIN-4 (EVO) - Execution & Evolution:
    - A13: Decision Lifecycle
    - A14: Reversibility & Exit Strategy
    - A15: Environment & Promotion Rules
    - A16: Anti-Drift & Consistency
    """
    # DOMAIN-1 (INT): Intent & Direction
    A01 = "A01"  # Vision & Outcome
    A02 = "A02"  # Problem Statement
    A03 = "A03"  # Scope & Non-Goals
    A04 = "A04"  # Principles & Values
    # DOMAIN-2 (ARCH): Architecture & Boundaries
    A05 = "A05"  # Domain & Bounded Context
    A06 = "A06"  # Service & Module Boundary
    A07 = "A07"  # Data Ownership & Sovereignty
    A08 = "A08"  # Integration & Contract Model
    # DOMAIN-3 (CTL): Control, Policy & Risk
    A09 = "A09"  # Policy & Rules
    A10 = "A10"  # Approval & Authority Model
    A11 = "A11"  # Security & Compliance Posture
    A12 = "A12"  # Risk & Blast Radius
    # DOMAIN-4 (EVO): Execution & Evolution
    A13 = "A13"  # Decision Lifecycle
    A14 = "A14"  # Reversibility & Exit Strategy
    A15 = "A15"  # Environment & Promotion Rules
    A16 = "A16"  # Anti-Drift & Consistency


class Scope(str, Enum):
    """Decision scope per MANTRA-DEC-003"""
    ORGANIZATION = "ORGANIZATION"
    DOMAIN = "DOMAIN"
    APPLICATION = "APPLICATION"


class BlastRadius(str, Enum):
    """Impact level per MANTRA-DEC-003"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ConstraintType(str, Enum):
    """Constraint type per MANTRA-SCHEMA-001"""
    PROHIBITION = "PROHIBITION"
    REQUIREMENT = "REQUIREMENT"
    LIMITATION = "LIMITATION"


class AreaTag(str, Enum):
    """Area tags for decision impact"""
    FE = "FE"          # Frontend
    BE = "BE"          # Backend
    DB = "DB"          # Database
    INFRA = "INFRA"    # Infrastructure
    CICD = "CICD"      # CI/CD Pipeline
    API = "API"        # API Design
    SECURITY = "SECURITY"  # Security
    DEVOPS = "DEVOPS"  # DevOps


class RelationType(str, Enum):
    """
    Typed relation types per Decision Graph Model.

    - depends_on: This decision requires the target decision to be in effect
    - conflicts_with: This decision cannot coexist with target decision
    - informed_by: This decision was influenced by target decision

    Note: supersedes is NOT a relation type - it has special semantics
    (versioning/evolution) and remains a separate field.
    """
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    INFORMED_BY = "informed_by"


class SectionType(str, Enum):
    """
    Section types for detailed content structure.

    Used in two-layer content model where:
    - Layer A (statement/rationale): Executive summary, validated
    - Layer B (detailed_content/sections): Full specification, structure-validated

    MICS Long Content Strategy implementation.
    """
    OVERVIEW = "OVERVIEW"      # High-level explanation
    RULES = "RULES"            # List of rules/conventions
    EXAMPLES = "EXAMPLES"      # Code examples (good/bad patterns)
    STRUCTURE = "STRUCTURE"    # Folder/file structures, hierarchies
    DIAGRAM = "DIAGRAM"        # ASCII/Mermaid diagrams
    REFERENCE = "REFERENCE"    # External links, documentation references


class DetailLevel(str, Enum):
    """
    Detail level for context delivery.

    Used in MICS smart context injection to manage token budgets.
    """
    MICRO = "micro"           # ~100 tokens - content_summary only
    STANDARD = "standard"     # ~500 tokens - statement + rationale + constraints
    DETAILED = "detailed"     # ~2000+ tokens - full content including detailed_content
    SECTIONS = "sections"     # Variable - specific sections only


# ============================================================================
# Domain-Aspect Compatibility Matrix per MANTRA-LAW-001 §3.2-§3.5
# ============================================================================

DOMAIN_ASPECT_MATRIX = {
    DomainId.INT: [AspectId.A01, AspectId.A02, AspectId.A03, AspectId.A04],
    DomainId.ARCH: [AspectId.A05, AspectId.A06, AspectId.A07, AspectId.A08],
    DomainId.CTL: [AspectId.A09, AspectId.A10, AspectId.A11, AspectId.A12],
    DomainId.EVO: [AspectId.A13, AspectId.A14, AspectId.A15, AspectId.A16],
}

# ============================================================================
# Domain Metadata (for documentation and UI)
# ============================================================================

DOMAIN_LAW_REFERENCES = {
    DomainId.INT: "DOMAIN-1, §3.2",
    DomainId.ARCH: "DOMAIN-2, §3.3",
    DomainId.CTL: "DOMAIN-3, §3.4",
    DomainId.EVO: "DOMAIN-4, §3.5",
}

DOMAIN_LABELS = {
    DomainId.INT: "Intent & Direction",
    DomainId.ARCH: "Architecture & Boundaries",
    DomainId.CTL: "Control, Policy & Risk",
    DomainId.EVO: "Execution & Evolution",
}

DOMAIN_SCOPES = {
    DomainId.INT: "WHY / WHAT",
    DomainId.ARCH: "HOW / WHERE",
    DomainId.CTL: "CAN / MUST NOT",
    DomainId.EVO: "CHANGE SAFELY",
}

ASPECT_LABELS = {
    AspectId.A01: "Vision & Outcome",
    AspectId.A02: "Problem Statement",
    AspectId.A03: "Scope & Non-Goals",
    AspectId.A04: "Principles & Values",
    AspectId.A05: "Domain & Bounded Context",
    AspectId.A06: "Service & Module Boundary",
    AspectId.A07: "Data Ownership & Sovereignty",
    AspectId.A08: "Integration & Contract Model",
    AspectId.A09: "Policy & Rules",
    AspectId.A10: "Approval & Authority Model",
    AspectId.A11: "Security & Compliance Posture",
    AspectId.A12: "Risk & Blast Radius",
    AspectId.A13: "Decision Lifecycle",
    AspectId.A14: "Reversibility & Exit Strategy",
    AspectId.A15: "Environment & Promotion Rules",
    AspectId.A16: "Anti-Drift & Consistency",
}


def is_aspect_compatible(domain_id: DomainId, aspect_id: AspectId) -> bool:
    """Check if aspect is compatible with domain per MANTRA-DEC-002"""
    return aspect_id in DOMAIN_ASPECT_MATRIX.get(domain_id, [])


# ============================================================================
# Decision Code Generator
# ============================================================================

def generate_decision_code(
    domain_id: DomainId,
    aspect_id: AspectId,
    sequence: int,
    version: str
) -> str:
    """
    Generate human-readable decision code.

    Format: {domain}-{aspect}-{seq:03d}-v{version}
    Example: INT-A01-001-v1.0.0

    Args:
        domain_id: Domain ID (INT, ARCH, CTL, EVO)
        aspect_id: Aspect ID (A01 to A16)
        sequence: Sequence number within the aspect (1-based)
        version: Semver version string

    Returns:
        Human-readable decision code
    """
    domain_abbr = domain_id.value
    aspect_code = aspect_id.value  # Already A01, A02, etc.

    return f"{domain_abbr}-{aspect_code}-{sequence:03d}-v{version}"


def parse_decision_code(code: str) -> Optional[dict]:
    """
    Parse a decision code back into its components.

    Args:
        code: Decision code like INT-A01-001-v1.0.0

    Returns:
        Dict with domain_id, aspect_id, sequence, version or None if invalid
    """
    pattern = r"^(INT|ARCH|CTL|EVO)-(A\d{2})-(\d{3})-v(\d+\.\d+\.\d+)$"
    match = re.match(pattern, code)

    if not match:
        return None

    return {
        "domain_id": match.group(1),
        "aspect_id": match.group(2),  # A01, A02, etc.
        "sequence": int(match.group(3)),
        "version": match.group(4)
    }


# ============================================================================
# Domain Models
# ============================================================================

class Constraint(BaseModel):
    """Constraint entry per MANTRA-SCHEMA-001"""
    constraint_id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    type: ConstraintType

    class Config:
        extra = "forbid"


class Relation(BaseModel):
    """
    Typed relation to another decision.

    Per Decision Graph Model:
    - target_id: UUID of the target decision
    - type: Semantic type of the relation
    """
    target_id: str = Field(..., description="UUID of the target decision")
    type: RelationType = Field(..., description="Type of relation")

    class Config:
        extra = "forbid"


class ContentSection(BaseModel):
    """
    Structured section for detailed content.

    Part of the two-layer content model (MICS Long Content Strategy):
    - Enables structured breakdown of long specifications
    - Allows selective retrieval (e.g., just EXAMPLES sections)
    - Supports tiered context delivery for token budget management
    """
    section_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier within decision (e.g., S-001)"
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Section title (e.g., 'Folder Structure', 'Import Rules')"
    )
    section_type: SectionType = Field(
        ...,
        description="Type of content: OVERVIEW, RULES, EXAMPLES, STRUCTURE, DIAGRAM, REFERENCE"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Section content in Markdown format"
    )
    order: int = Field(
        default=0,
        ge=0,
        description="Display order (0-based)"
    )

    class Config:
        extra = "forbid"


class Decision(BaseModel):
    """
    Decision record per MANTRA-SCHEMA-001

    This is the core aggregate of ATLAS_MANTRA.
    Per MANTRA-LAW-001, stored decisions are ABSOLUTELY IMMUTABLE.

    Per Human Decision (Phase 4):
    - NO status field (lifecycle is NOT encoded in domain)
    - Evolution expressed via version + supersedes only

    UX Enhancement (Phase 5):
    - decision_code provides human-readable identifier
    - Format: {domain}-{aspect}{seq}-v{version}
    - Example: INT-A01-001-v1.0.0
    """
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_code: Optional[str] = Field(
        default=None,
        description="Human-readable decision code (e.g., INT-A01-001-v1.0.0). "
                   "Generated on storage, not required for creation."
    )
    domain_id: DomainId
    aspect_id: AspectId
    statement: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    constraints: List[Constraint] = Field(default_factory=list)
    invariants: List[str] = Field(default_factory=list)
    scope: Scope
    blast_radius: BlastRadius
    version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")

    # Optional fields
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    supersedes: Optional[str] = None

    # Relations (deprecated: related_decisions, use: relations)
    related_decisions: List[str] = Field(
        default_factory=list,
        description="DEPRECATED: Use 'relations' field instead. "
                   "Kept for backwards compatibility."
    )
    relations: List[Relation] = Field(
        default_factory=list,
        description="Typed relations: depends_on, conflicts_with, informed_by"
    )

    # Projection fields (for filtering and grouping)
    tags: List[str] = Field(
        default_factory=list,
        description="Area tags: FE, BE, DB, INFRA, CICD, API, SECURITY, DEVOPS"
    )
    tech_stack: List[str] = Field(
        default_factory=list,
        description="Technologies/frameworks: React, FastAPI, PostgreSQL, Docker, etc."
    )

    # =========================================================================
    # Two-Layer Content Model (MICS Long Content Strategy)
    # =========================================================================
    #
    # Layer A (Executive Summary - Validated):
    #   - statement: What the decision is (10-200 words)
    #   - rationale: Why the decision was made (20-500 words)
    #   - constraints: Key rules as structured list
    #
    # Layer B (Detailed Specification - Structure-Validated):
    #   - detailed_content: Full Markdown specification (unlimited)
    #   - sections: Structured breakdown for selective retrieval
    #   - content_summary: Auto-generated token-efficient summary
    #
    # =========================================================================

    detailed_content: Optional[str] = Field(
        default=None,
        description="""
        Full specification in Markdown format (Layer B).

        Use when decision requires:
        - Code examples with good/bad patterns
        - Folder/file structures
        - Detailed rules with examples
        - Diagrams (ASCII or Mermaid)
        - Tables and complex formatting

        NOT validated for length/readability.
        Validated for: Markdown structure, code block validity.
        """
    )
    sections: List[ContentSection] = Field(
        default_factory=list,
        description="""
        Structured sections for detailed content.

        Enables:
        - Selective retrieval (e.g., just EXAMPLES sections)
        - Tiered context delivery for token budget management
        - Organized presentation in UI

        Each section has: section_id, title, section_type, content, order
        """
    )
    content_summary: Optional[str] = Field(
        default=None,
        description="""
        Auto-generated token-efficient summary (~50-100 words).

        Used for:
        - MICRO detail level in context injection
        - Quick reference in decision lists
        - Token-limited AI assistants

        Generated from statement + key constraints + section titles.
        """
    )

    @field_validator("aspect_id")
    @classmethod
    def validate_domain_aspect_compatibility(cls, v, info):
        """Validate aspect is compatible with domain per MANTRA-DEC-002"""
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
        for invariant in v:
            if not invariant or len(invariant.strip()) == 0:
                raise ValueError("Invariant strings must not be empty")
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
        return v

    @field_validator("sections")
    @classmethod
    def validate_section_order(cls, v):
        """Ensure sections have valid order values"""
        if not v:
            return v
        # Sort by order if not already
        return sorted(v, key=lambda s: s.order)

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "550e8400-e29b-41d4-a716-446655440000",
                "decision_code": "ARCH-A06-001-v1.0.0",
                "domain_id": "ARCH",
                "aspect_id": "A06",
                "statement": "All projects must follow the feature-based folder structure with strict module boundaries.",
                "rationale": "Feature-based structure improves code discoverability, enables lazy loading, and enforces bounded contexts. Each feature is self-contained, enabling independent development and testing.",
                "constraints": [
                    {
                        "constraint_id": "C-001",
                        "statement": "Feature folders must have index.ts as single export point",
                        "type": "REQUIREMENT"
                    },
                    {
                        "constraint_id": "C-002",
                        "statement": "Shared components cannot import from feature folders",
                        "type": "PROHIBITION"
                    },
                    {
                        "constraint_id": "C-003",
                        "statement": "Maximum 3 levels of nesting within feature folder",
                        "type": "LIMITATION"
                    }
                ],
                "invariants": ["Module boundaries are enforced at build time"],
                "scope": "ORGANIZATION",
                "blast_radius": "HIGH",
                "version": "1.0.0",
                "supersedes": None,
                "created_by": "human-architect",
                "tags": ["FE", "BE", "INFRA"],
                "tech_stack": ["TypeScript", "React", "Vite"],
                "detailed_content": "## Full Folder Structure\n\n```\nsrc/\n├── features/\n│   ├── auth/\n│   │   ├── api/\n│   │   ├── components/\n│   │   ├── hooks/\n│   │   └── index.ts\n│   └── dashboard/\n├── shared/\n│   ├── components/\n│   └── utils/\n└── pages/\n```\n\n## Rules\n\n### Rule 1: Feature Module Exports\n\nEvery feature folder MUST have `index.ts`:\n\n```typescript\n// features/auth/index.ts\nexport { LoginForm } from './components/LoginForm';\nexport { useAuth } from './hooks/useAuth';\n```\n\n### Rule 2: Import Boundaries\n\n```typescript\n// Good - shared to feature\nimport { Button } from '@/shared/components';\n\n// Bad - direct internal import\nimport { LoginForm } from '@/features/auth/components/LoginForm';\n```",
                "sections": [
                    {
                        "section_id": "S-001",
                        "title": "Folder Structure",
                        "section_type": "STRUCTURE",
                        "content": "```\nsrc/\n├── features/\n├── shared/\n└── pages/\n```",
                        "order": 1
                    },
                    {
                        "section_id": "S-002",
                        "title": "Export Rules",
                        "section_type": "RULES",
                        "content": "1. Every feature must have index.ts\n2. Only export public API",
                        "order": 2
                    },
                    {
                        "section_id": "S-003",
                        "title": "Import Examples",
                        "section_type": "EXAMPLES",
                        "content": "```typescript\n// Good\nimport { Button } from '@/shared/components';\n\n// Bad\nimport { LoginForm } from '@/features/auth/components/LoginForm';\n```",
                        "order": 3
                    }
                ],
                "content_summary": "Feature-based folder structure with src/features/, src/shared/, src/pages/. Features export via index.ts only. Shared cannot import from features. Max 3 nesting levels."
            }
        }


# ============================================================================
# Input/Output DTOs
# ============================================================================

class DecisionCreate(BaseModel):
    """
    Input DTO for creating a new decision.

    Supports two-layer content model:
    - Layer A (required): statement, rationale, constraints
    - Layer B (optional): detailed_content, sections
    """
    domain_id: DomainId
    aspect_id: AspectId
    statement: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    constraints: List[Constraint] = Field(default_factory=list)
    invariants: List[str] = Field(default_factory=list)
    scope: Scope
    blast_radius: BlastRadius
    version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    created_by: str
    supersedes: Optional[str] = None
    related_decisions: List[str] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)

    # Two-Layer Content Model (Layer B - optional)
    detailed_content: Optional[str] = Field(
        default=None,
        description="Full specification in Markdown format"
    )
    sections: List[ContentSection] = Field(
        default_factory=list,
        description="Structured sections for detailed content"
    )


class AuthorshipMetadata(BaseModel):
    """
    Authorship metadata per MANTRA-SPEC-001 §4.3.2

    Used for Law Compliance Validation (L-001 through L-008).
    When unavailable, these rules are skipped.
    """
    author_type: str  # "human" or "ai"
    author_identifier: str
    timestamp: datetime
    is_approval: bool = False
