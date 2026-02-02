# Domain Layer
# Business logic and decision aggregate

# Re-export constants (single source of truth)
from .constants import (
    # Domain & Aspect taxonomy
    VALID_DOMAINS, VALID_ASPECTS, DOMAIN_ASPECT_MATRIX,
    DOMAIN_LABELS, ASPECT_LABELS, DOMAIN_DESCRIPTIONS, ASPECT_DESCRIPTIONS,
    # Patterns
    UUID_PATTERN, VERSION_PATTERN, CODE_PATTERN, SCOPE_PATH_PATTERN,
    # Field constraints
    FIELD_LENGTH_CONSTRAINTS,
    # Impact & Blast radius
    VALID_IMPACTS, IMPACT_WEIGHTS, VALID_BLAST_RADIUS, BLAST_RADIUS_WEIGHTS,
    # Constraint types
    VALID_CONSTRAINT_TYPES, CONSTRAINT_TYPE_WEIGHTS,
    # Status enums
    DraftStatus, FieldReviewStatus, GateStatus,
    # Quality
    QUALITY_GRADE_THRESHOLDS, MINIMUM_QUALITY_SCORE,
    # MANTRA Law
    MantraLaw, LAW_VIOLATION_MESSAGES,
    # Functions
    get_aspects_for_domain, is_aspect_compatible, get_domain_for_aspect,
)

# Re-export key types from schema_v3 (primary schema - full 100+ fields)
from .schema_v3 import (
    # Main Decision Model
    DecisionV3,
    # Enums
    DomainId, AspectId, Scope, BlastRadius, ConstraintType,
    # Content Length & Writing Guidelines
    ContentLengthConfig, WritingStyle, WritingGuideline, WRITING_GUIDELINES,
    validate_content_length, check_anti_patterns, get_writing_tips,
    validate_statement, validate_rationale, validate_constraint_statement, validate_invariant,
    # Metadata Enrichment (LAW §10.7 compliant)
    MetadataEnrichment, ENRICHABLE_FIELDS, IMMUTABLE_FIELDS,
    EnrichmentType, create_metadata_enrichment,
    # Structured Summary
    SummaryLevel, StructuredSummary,
    # Validation Classification System
    ValidationType, FieldSource, ValidationRule, FieldSpec,
    VALIDATION_RULES, FIELD_PROMPTS,
    get_validation_rules, get_rules_by_type, count_rules_by_type, get_field_prompt,
)

# Re-export MCP-optimized schema (minimal 18 fields for AI context)
from .schema_mcp import (
    # MCP-specific enums
    ValidityState, ImpactLevel,
    # MCP Models
    MCPConstraint, MCPDecision, MCPDecisionCollection,
    # Migration helper (DecisionV3 → MCPDecision)
    from_full_decision, ConversionWarning, ConversionResult,
    # Constraint type mapping (bidirectional)
    CONSTRAINT_TYPE_MAPPING, CONSTRAINT_TYPE_REVERSE, map_constraint_type,
)

# Re-export Field Metadata (per LAW AMENDMENT-004)
from .field_meta import (
    # Enums
    LengthCategory, InputMode, ValidationLevel, ContentType,
    # Constants
    LENGTH_LIMITS, BULLET_LIMITS,
    # Classes
    FieldMeta, FIELD_REGISTRY,
    # Functions
    get_field_meta, get_ai_fields, get_rule_fields, get_required_fields,
    validate_length, get_ai_prompt,
)

# Re-export Three-Gate Validator (per LAW AMENDMENT-004)
from .validator import (
    # Enums
    ValidationResult, GateType, HumanDecisionAction,
    # Dataclasses
    ValidationIssue, GateResult, ValidationReport, HumanDecision, HumanApprovalAudit,
    # Functions
    compute_decision_hash,
    # Validators
    Gate1Validator, Gate2Validator, Gate3Validator, MantraValidator,
)

# Re-export Scope utilities (simple)
from .scope import (
    ScopeRelation, ScopeLayer, ScopePath,
    scopes_can_conflict, get_scope_relation, suggest_scope_path,
)

# Re-export Scope DAG (hierarchical with multiple parents)
from .scope_dag import (
    # Enums
    InheritanceType, ScopeRelation as DagScopeRelation,
    # Data classes
    ScopeNode, InheritanceInfo, ScopeDefinition,
    # Main class
    ScopeTree,
    # Functions
    determine_inheritance_type, create_scope_definition, generate_applies_to_description,
)

# Re-export Scope Registry (default tree + resolution)
from .scope_registry import (
    # Tree access
    get_default_tree, reset_default_tree,
    # Dynamic scope creation
    ensure_scope_exists, ensure_scopes_exist, auto_register_scope,
    # Scope resolution
    resolve_scope, resolve_scope_simple,
    # Registration
    register_custom_scope, register_batch_scopes,
    # Lookup
    find_scope_by_alias, get_scopes_by_tag, get_umbrella_scopes, get_shared_scopes,
    # Suggestions
    suggest_scopes, get_scope_hierarchy,
    # AI Retrieval
    get_applies_to_for_retrieval, scope_matches_query,
    # Legacy migration
    migrate_tags_to_scope, TAG_TO_SCOPE_MAP,
    # Constants
    DEFAULT_NODES, COMMON_SCOPE_PATTERNS,
)

# Re-export Decision Bundles
from .bundle import (
    BundleType, BundleStatus, MemberRole,
    BundleMember, DecisionBundle, BundleManager,
    create_topic_bundle, create_workflow_bundle,
)

__all__ = [
    # =========================================================================
    # CONSTANTS (Single Source of Truth)
    # =========================================================================
    # Domain & Aspect
    "VALID_DOMAINS", "VALID_ASPECTS", "DOMAIN_ASPECT_MATRIX",
    "DOMAIN_LABELS", "ASPECT_LABELS", "DOMAIN_DESCRIPTIONS", "ASPECT_DESCRIPTIONS",
    # Patterns
    "UUID_PATTERN", "VERSION_PATTERN", "CODE_PATTERN", "SCOPE_PATH_PATTERN",
    # Field constraints
    "FIELD_LENGTH_CONSTRAINTS",
    # Impact & Blast radius
    "VALID_IMPACTS", "IMPACT_WEIGHTS", "VALID_BLAST_RADIUS", "BLAST_RADIUS_WEIGHTS",
    # Constraint types
    "VALID_CONSTRAINT_TYPES", "CONSTRAINT_TYPE_WEIGHTS",
    # Status enums
    "DraftStatus", "FieldReviewStatus", "GateStatus",
    # Quality
    "QUALITY_GRADE_THRESHOLDS", "MINIMUM_QUALITY_SCORE",
    # MANTRA Law
    "MantraLaw", "LAW_VIOLATION_MESSAGES",
    # Functions
    "get_aspects_for_domain", "is_aspect_compatible", "get_domain_for_aspect",

    # =========================================================================
    # FULL SCHEMA (DecisionV3) - 100+ fields for UI/Dashboard
    # =========================================================================
    # Main Model
    "DecisionV3",
    # Classification
    "DomainId", "AspectId", "Scope", "BlastRadius", "ConstraintType",
    # Content Length & Writing
    "ContentLengthConfig", "WritingStyle", "WritingGuideline", "WRITING_GUIDELINES",
    "validate_content_length", "check_anti_patterns", "get_writing_tips",
    "validate_statement", "validate_rationale", "validate_constraint_statement", "validate_invariant",
    # Metadata Enrichment
    "MetadataEnrichment", "ENRICHABLE_FIELDS", "IMMUTABLE_FIELDS",
    "EnrichmentType", "create_metadata_enrichment",
    # Summary
    "SummaryLevel", "StructuredSummary",
    # Validation Classification
    "ValidationType", "FieldSource", "ValidationRule", "FieldSpec",
    "VALIDATION_RULES", "FIELD_PROMPTS",
    "get_validation_rules", "get_rules_by_type", "count_rules_by_type", "get_field_prompt",

    # =========================================================================
    # MCP SCHEMA (MCPDecision) - 18 fields for AI context
    # =========================================================================
    # MCP-specific enums
    "ValidityState", "ImpactLevel",
    # MCP Models
    "MCPConstraint", "MCPDecision", "MCPDecisionCollection",
    # Migration (DecisionV3 → MCPDecision)
    "from_full_decision", "ConversionWarning", "ConversionResult",
    # Constraint type mapping (bidirectional)
    "CONSTRAINT_TYPE_MAPPING", "CONSTRAINT_TYPE_REVERSE", "map_constraint_type",

    # =========================================================================
    # FIELD METADATA (per LAW AMENDMENT-004)
    # =========================================================================
    "LengthCategory", "InputMode", "ValidationLevel", "ContentType",
    "LENGTH_LIMITS", "BULLET_LIMITS",
    "FieldMeta", "FIELD_REGISTRY",
    "get_field_meta", "get_ai_fields", "get_rule_fields", "get_required_fields",
    "validate_length", "get_ai_prompt",

    # =========================================================================
    # THREE-GATE VALIDATOR (per LAW AMENDMENT-004)
    # =========================================================================
    "ValidationResult", "GateType", "HumanDecisionAction",
    "ValidationIssue", "GateResult", "ValidationReport", "HumanDecision", "HumanApprovalAudit",
    "compute_decision_hash",
    "Gate1Validator", "Gate2Validator", "Gate3Validator", "MantraValidator",

    # =========================================================================
    # SCOPE UTILITIES (Simple)
    # =========================================================================
    "ScopeRelation", "ScopeLayer", "ScopePath",
    "scopes_can_conflict", "get_scope_relation", "suggest_scope_path",

    # =========================================================================
    # SCOPE DAG (Hierarchical with Multiple Parents)
    # =========================================================================
    "InheritanceType", "DagScopeRelation",
    "ScopeNode", "InheritanceInfo", "ScopeDefinition",
    "ScopeTree",
    "determine_inheritance_type", "create_scope_definition", "generate_applies_to_description",

    # =========================================================================
    # SCOPE REGISTRY (Default Tree + Resolution)
    # =========================================================================
    "get_default_tree", "reset_default_tree",
    "ensure_scope_exists", "ensure_scopes_exist", "auto_register_scope",
    "resolve_scope", "resolve_scope_simple",
    "register_custom_scope", "register_batch_scopes",
    "find_scope_by_alias", "get_scopes_by_tag", "get_umbrella_scopes", "get_shared_scopes",
    "suggest_scopes", "get_scope_hierarchy",
    "get_applies_to_for_retrieval", "scope_matches_query",
    "migrate_tags_to_scope", "TAG_TO_SCOPE_MAP",
    "DEFAULT_NODES", "COMMON_SCOPE_PATTERNS",

    # =========================================================================
    # DECISION BUNDLES
    # =========================================================================
    "BundleType", "BundleStatus", "MemberRole",
    "BundleMember", "DecisionBundle", "BundleManager",
    "create_topic_bundle", "create_workflow_bundle",
]
