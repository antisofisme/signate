"""
MANTRA Schema Facade

Canonical exports for MANTRA domain models. This file provides:
1. Unified interface to all schema versions
2. Backward-compatible aliases (Decision = DecisionV3)
3. Convenience functions (generate_decision_code)

USAGE:
    from core.domain.schema import (
        Decision,           # Main decision model (alias for DecisionV3)
        DecisionCreate,     # Input DTO (alias for DecisionCreateV3)
        DomainId, AspectId, # Enums
        Constraint,         # Sub-models
        AuthorshipMetadata, # Authorship info for L-rules
        generate_decision_code,  # Code generation
    )

SCHEMA VERSIONS:
- v2 (schema_base.py): Extended fields, 80+ total
- v3 (schema_v3.py): Full enhanced, 100+ fields (CURRENT)
- MCP (schema_mcp.py): Minimal 24 fields for AI context

Per MANTRA-LAW-001: All schemas are constitutional and immutable once stored.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# =============================================================================
# Core Enums (from schema_base.py via schema_v3.py)
# =============================================================================

from .schema_v3 import (
    # Classification Enums
    DomainId,
    AspectId,
    Scope,
    BlastRadius,
    ConstraintType,
    RelationType,
    SectionType,
    ChangeType,
    StakeholderRole,
    ComplianceFramework,
    ApprovalStatus,
    AreaTag,
)

# =============================================================================
# Matrix Constants
# =============================================================================

from .schema_v3 import (
    DOMAIN_ASPECT_MATRIX,
    DOMAIN_LABELS,
    ASPECT_LABELS,
    is_aspect_compatible,
)

# =============================================================================
# Sub-Models (from schema_base.py via schema_v3.py)
# =============================================================================

from .schema_v3 import (
    Relation,
    ContentSection,
    Stakeholder,
    ApprovalRecord,
    ComplianceReference,
    TemporalValidity,
    QualityMetadata,
    ImplementationGuidance,
)

# Import Constraint from schema_base.py directly (not enhanced version)
from .schema_base import Constraint

# =============================================================================
# Main Decision Models (Aliases for backward compatibility)
# =============================================================================

from .schema_v3 import (
    DecisionV3,
    DecisionCreateV3,
)

# Canonical aliases - use these in application code
Decision = DecisionV3
DecisionCreate = DecisionCreateV3


# =============================================================================
# MCP Schema (Minimal for AI context)
# =============================================================================

from .schema_mcp import (
    MCPDecision,
    MCPConstraint,
    MCPDecisionCollection,
    ValidityState,
    ImpactLevel,
    from_full_decision,
    ConversionWarning,
    ConversionResult,
    CONSTRAINT_TYPE_MAPPING,
    CONSTRAINT_TYPE_REVERSE,
    map_constraint_type,
)


# =============================================================================
# Authorship Metadata (for L-rules validation)
# =============================================================================

class AuthorshipMetadata(BaseModel):
    """
    Authorship metadata for L-rules validation.

    Per MANTRA-LAW-001 §2.3: Human authorship is REQUIRED.
    This metadata helps validate that decisions are created by humans.

    L-rules (L-001 through L-008) check:
    - L-001: created_by must not be AI
    - L-002: approved_by must not be AI
    - L-003: Human must make final decision
    - L-004: Adequate review time
    - L-005: Stakeholder notification
    - L-006: Proper authority chain
    - L-007: Documentation requirements
    - L-008: Audit trail requirements
    """
    # Author information
    author_id: str = Field(..., description="Human author identifier (email/ID)")
    author_name: Optional[str] = Field(None, description="Human-readable name")
    author_role: Optional[str] = Field(None, description="Role: ARCHITECT, LEAD, SENIOR, etc.")

    # Organization context
    organization_id: Optional[str] = Field(None, description="Organization/tenant ID")
    team_id: Optional[str] = Field(None, description="Team/department ID")

    # Authorship verification
    is_human: bool = Field(True, description="Explicitly confirms author is human")
    verification_method: Optional[str] = Field(
        None,
        description="How authorship was verified: SSO, API_KEY, MANUAL"
    )

    # AI assistance disclosure (per LAW §6.5)
    ai_assisted: bool = Field(
        False,
        description="Whether AI was used to help draft the decision"
    )
    ai_assistance_scope: Optional[str] = Field(
        None,
        description="What AI helped with: DRAFTING, VALIDATION, REVIEW, etc."
    )

    # Timestamps
    verified_at: Optional[datetime] = Field(None, description="When authorship was verified")

    class Config:
        extra = "forbid"


# =============================================================================
# Decision Code Generation
# =============================================================================

def generate_decision_code(
    domain_id: DomainId,
    aspect_id: AspectId,
    sequence: int,
    version: str = "1.0.0"
) -> str:
    """
    Generate human-readable decision code.

    Format: {domain}-{aspect}-{sequence:03d}-v{version}
    Example: ARCH-A06-001-v1.0.0

    Args:
        domain_id: Domain classification
        aspect_id: Aspect within domain
        sequence: Sequence number within aspect (1-based)
        version: Semantic version string

    Returns:
        Formatted decision code string
    """
    # Extract domain and aspect strings
    domain = domain_id.value if isinstance(domain_id, DomainId) else domain_id
    aspect = aspect_id.value if isinstance(aspect_id, AspectId) else aspect_id

    # Format: DOMAIN-ASPECT-SEQ-vVERSION
    return f"{domain}-{aspect}-{sequence:03d}-v{version}"


def parse_decision_code(code: str) -> dict:
    """
    Parse a decision code into its components.

    Args:
        code: Decision code (e.g., "ARCH-A06-001-v1.0.0")

    Returns:
        Dict with domain_id, aspect_id, sequence, version

    Raises:
        ValueError: If code format is invalid
    """
    import re

    pattern = r"^([A-Z]+)-([A-Z][0-9]+)-([0-9]+)-v(.+)$"
    match = re.match(pattern, code)

    if not match:
        raise ValueError(f"Invalid decision code format: {code}")

    domain, aspect, sequence, version = match.groups()

    return {
        "domain_id": DomainId(domain),
        "aspect_id": AspectId(aspect),
        "sequence": int(sequence),
        "version": version,
    }


# =============================================================================
# Validation Rules Constants
# =============================================================================

from .schema_v3 import (
    # Validation Classification System
    ValidationType,
    FieldSource,
    ValidationRule,
    FieldSpec,
    VALIDATION_RULES as V3_VALIDATION_RULES,
    FIELD_PROMPTS,
    get_validation_rules,
    get_rules_by_type,
    count_rules_by_type,
    get_field_prompt,
)

# Alias for backward compatibility
VALIDATION_RULES = V3_VALIDATION_RULES

# =============================================================================
# Content Length & Writing Guidelines
# =============================================================================

from .schema_v3 import (
    ContentLengthConfig,
    WritingStyle,
    WritingGuideline,
    WRITING_GUIDELINES,
    validate_content_length,
    check_anti_patterns,
    get_writing_tips,
    validate_statement,
    validate_rationale,
    validate_constraint_statement,
    validate_invariant,
)

# =============================================================================
# Metadata Enrichment (LAW §10.7 compliant)
# =============================================================================

from .schema_v3 import (
    MetadataEnrichment,
    ENRICHABLE_FIELDS,
    IMMUTABLE_FIELDS,
    EnrichmentType,
    create_metadata_enrichment,
)

# =============================================================================
# Structured Summary
# =============================================================================

from .schema_v3 import (
    SummaryLevel,
    StructuredSummary,
)

# =============================================================================
# Migration Helpers
# =============================================================================

from .schema_base import (
    DATABASE_INDEXES,
    migrate_v1_to_v2,
)


def migrate_to_current(decision_dict: dict) -> Decision:
    """
    Migrate a decision dictionary to the current schema version.

    Handles:
    - v1 → current
    - v2 → current
    - v3 → current (no-op)

    Args:
        decision_dict: Decision data dictionary

    Returns:
        Decision instance (DecisionV3)
    """
    # Check for version indicators
    if "llm_optimization" in decision_dict or "temporal_validity" in decision_dict:
        # v2 or v3 - try direct parsing
        return Decision(**decision_dict)

    # Assume v1 - use migration helper
    v2 = migrate_v1_to_v2(decision_dict)
    # v2 to v3 is mostly compatible
    return Decision(**v2.model_dump())


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # =========================================================================
    # Main Models (Canonical)
    # =========================================================================
    "Decision",
    "DecisionCreate",
    "DecisionV3",
    "DecisionCreateV3",

    # =========================================================================
    # MCP Schema (AI Context)
    # =========================================================================
    "MCPDecision",
    "MCPConstraint",
    "MCPDecisionCollection",
    "ValidityState",
    "ImpactLevel",
    "from_full_decision",
    "ConversionWarning",
    "ConversionResult",
    "CONSTRAINT_TYPE_MAPPING",
    "CONSTRAINT_TYPE_REVERSE",
    "map_constraint_type",

    # =========================================================================
    # Classification Enums
    # =========================================================================
    "DomainId",
    "AspectId",
    "Scope",
    "BlastRadius",
    "ConstraintType",
    "RelationType",
    "SectionType",
    "ChangeType",
    "StakeholderRole",
    "ComplianceFramework",
    "ApprovalStatus",
    "AreaTag",

    # =========================================================================
    # Matrix Constants
    # =========================================================================
    "DOMAIN_ASPECT_MATRIX",
    "DOMAIN_LABELS",
    "ASPECT_LABELS",
    "is_aspect_compatible",

    # =========================================================================
    # Sub-Models
    # =========================================================================
    "Constraint",
    "Relation",
    "ContentSection",
    "Stakeholder",
    "ApprovalRecord",
    "ComplianceReference",
    "TemporalValidity",
    "QualityMetadata",
    "ImplementationGuidance",

    # =========================================================================
    # Authorship
    # =========================================================================
    "AuthorshipMetadata",

    # =========================================================================
    # Code Generation
    # =========================================================================
    "generate_decision_code",
    "parse_decision_code",

    # =========================================================================
    # Validation
    # =========================================================================
    "ValidationType",
    "FieldSource",
    "ValidationRule",
    "FieldSpec",
    "VALIDATION_RULES",
    "FIELD_PROMPTS",
    "get_validation_rules",
    "get_rules_by_type",
    "count_rules_by_type",
    "get_field_prompt",

    # =========================================================================
    # Content Guidelines
    # =========================================================================
    "ContentLengthConfig",
    "WritingStyle",
    "WritingGuideline",
    "WRITING_GUIDELINES",
    "validate_content_length",
    "check_anti_patterns",
    "get_writing_tips",
    "validate_statement",
    "validate_rationale",
    "validate_constraint_statement",
    "validate_invariant",

    # =========================================================================
    # Metadata Enrichment
    # =========================================================================
    "MetadataEnrichment",
    "ENRICHABLE_FIELDS",
    "IMMUTABLE_FIELDS",
    "EnrichmentType",
    "create_metadata_enrichment",

    # =========================================================================
    # Structured Summary
    # =========================================================================
    "SummaryLevel",
    "StructuredSummary",

    # =========================================================================
    # Migration
    # =========================================================================
    "DATABASE_INDEXES",
    "migrate_v1_to_v2",
    "migrate_to_current",
]
