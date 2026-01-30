# Domain Layer
# Business logic and decision aggregate

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

# Re-export Scope utilities
from .scope import (
    ScopeRelation, ScopeLayer, ScopePath,
    scopes_can_conflict, get_scope_relation, suggest_scope_path,
)

# Re-export Decision Bundles
from .bundle import (
    BundleType, BundleStatus, MemberRole,
    BundleMember, DecisionBundle, BundleManager,
    create_topic_bundle, create_workflow_bundle,
)

__all__ = [
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
    # SCOPE UTILITIES
    # =========================================================================
    "ScopeRelation", "ScopeLayer", "ScopePath",
    "scopes_can_conflict", "get_scope_relation", "suggest_scope_path",

    # =========================================================================
    # DECISION BUNDLES
    # =========================================================================
    "BundleType", "BundleStatus", "MemberRole",
    "BundleMember", "DecisionBundle", "BundleManager",
    "create_topic_bundle", "create_workflow_bundle",
]
