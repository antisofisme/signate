"""
MANTRA Domain Constants - Single Source of Truth

This module consolidates all domain constants used across ARSAKA_MANTRA.
Import from here instead of scattered locations.

Usage:
    from core.domain.constants import (
        VALID_DOMAINS,
        VALID_ASPECTS,
        DOMAIN_ASPECT_MATRIX,
        DOMAIN_LABELS,
        ASPECT_LABELS,
    )

Categories:
- Domain & Aspect: 4x4 taxonomy
- Validation: Thresholds, lengths, patterns
- Field: Constraints per field
- Impact: Blast radius classifications
- Status: Workflow statuses
"""

from typing import Dict, List, Set, Any
from enum import Enum


# =============================================================================
# SECTION 1: DOMAIN & ASPECT TAXONOMY
# =============================================================================

# Valid domain IDs (4 domains per MANTRA-LAW-001 §3)
VALID_DOMAINS: Set[str] = {"INT", "ARCH", "CTL", "EVO"}

# Valid aspect IDs (16 aspects, 4 per domain)
VALID_ASPECTS: Set[str] = {f"A{i:02d}" for i in range(1, 17)}

# Domain-Aspect compatibility matrix
DOMAIN_ASPECT_MATRIX: Dict[str, List[str]] = {
    "INT": ["A01", "A02", "A03", "A04"],   # Intent and Direction
    "ARCH": ["A05", "A06", "A07", "A08"],  # Architecture and Boundaries
    "CTL": ["A09", "A10", "A11", "A12"],   # Control, Policy and Risk
    "EVO": ["A13", "A14", "A15", "A16"],   # Execution and Evolution
}

# Domain labels for display
DOMAIN_LABELS: Dict[str, str] = {
    "INT": "Intent and Direction",
    "ARCH": "Architecture and Boundaries",
    "CTL": "Control, Policy and Risk",
    "EVO": "Execution and Evolution",
}

# Domain descriptions
DOMAIN_DESCRIPTIONS: Dict[str, str] = {
    "INT": "WHY/WHAT - Vision, goals, scope, principles",
    "ARCH": "HOW/WHERE - Structure, boundaries, data, integration",
    "CTL": "CAN/MUST NOT - Policy, authority, security, risk",
    "EVO": "CHANGE SAFELY - Lifecycle, reversibility, environments, consistency",
}

# Aspect labels for display
ASPECT_LABELS: Dict[str, str] = {
    "A01": "Vision and Outcome",
    "A02": "Problem Statement",
    "A03": "Scope and Non-Goals",
    "A04": "Principles and Values",
    "A05": "Domain and Bounded Context",
    "A06": "Service and Module Boundary",
    "A07": "Data Ownership and Sovereignty",
    "A08": "Integration and Contract Model",
    "A09": "Policy and Rules",
    "A10": "Approval and Authority Model",
    "A11": "Security and Compliance Posture",
    "A12": "Risk and Blast Radius",
    "A13": "Decision Lifecycle",
    "A14": "Reversibility and Exit Strategy",
    "A15": "Environment and Promotion Rules",
    "A16": "Anti-Drift and Consistency",
}

# Aspect descriptions
ASPECT_DESCRIPTIONS: Dict[str, str] = {
    "A01": "Long-term vision, desired outcomes, success metrics",
    "A02": "Problem being solved, context, pain points",
    "A03": "What's included, what's explicitly excluded",
    "A04": "Guiding principles, team values, non-negotiables",
    "A05": "Bounded contexts, domain boundaries, ubiquitous language",
    "A06": "Service ownership, module boundaries, API contracts",
    "A07": "Data ownership, data sovereignty, data flow",
    "A08": "Integration patterns, contracts, dependencies",
    "A09": "Business policies, technical rules, governance",
    "A10": "Approval workflows, authority levels, escalation",
    "A11": "Security posture, compliance requirements, audit",
    "A12": "Risk assessment, blast radius, mitigation",
    "A13": "Decision lifecycle, review cadence, expiration",
    "A14": "Rollback strategy, exit plan, reversibility",
    "A15": "Environment rules, promotion gates, deployment",
    "A16": "Drift detection, consistency enforcement, guardrails",
}


# =============================================================================
# SECTION 2: VALIDATION PATTERNS
# =============================================================================

# UUID pattern
UUID_PATTERN: str = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# Version pattern (semantic versioning)
VERSION_PATTERN: str = r"^[0-9]+\.[0-9]+\.[0-9]+$"

# Decision code pattern: DOMAIN-ASPECT-SEQUENCE
CODE_PATTERN: str = r"^[A-Z]+-A[0-9]{2}-[0-9]{3}$"

# Scope path pattern: dot-separated, lowercase, or wildcard
SCOPE_PATH_PATTERN: str = r"^(\*|[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*(\.\*)?|\*)$"


# =============================================================================
# SECTION 3: FIELD CONSTRAINTS
# =============================================================================

class FieldConstraint:
    """Container for field-specific constraints."""
    pass


# Statement field constraints
STATEMENT_MIN_LENGTH: int = 50
STATEMENT_MAX_LENGTH: int = 1500
STATEMENT_RECOMMENDED_MIN: int = 100
STATEMENT_RECOMMENDED_MAX: int = 500

# Rationale field constraints
RATIONALE_MIN_LENGTH: int = 100
RATIONALE_MAX_LENGTH: int = 5000
RATIONALE_RECOMMENDED_MIN: int = 200
RATIONALE_RECOMMENDED_MAX: int = 1000

# Summary field constraints
SUMMARY_MIN_LENGTH: int = 20
SUMMARY_MAX_LENGTH: int = 200

# Title field constraints
TITLE_MIN_LENGTH: int = 10
TITLE_MAX_LENGTH: int = 100

# Priority rank constraints
PRIORITY_RANK_MIN: int = 1
PRIORITY_RANK_MAX: int = 100

# Field length constraints as dict (for programmatic access)
FIELD_LENGTH_CONSTRAINTS: Dict[str, Dict[str, int]] = {
    "statement": {
        "min": STATEMENT_MIN_LENGTH,
        "max": STATEMENT_MAX_LENGTH,
        "recommended_min": STATEMENT_RECOMMENDED_MIN,
        "recommended_max": STATEMENT_RECOMMENDED_MAX,
    },
    "rationale": {
        "min": RATIONALE_MIN_LENGTH,
        "max": RATIONALE_MAX_LENGTH,
        "recommended_min": RATIONALE_RECOMMENDED_MIN,
        "recommended_max": RATIONALE_RECOMMENDED_MAX,
    },
    "summary": {
        "min": SUMMARY_MIN_LENGTH,
        "max": SUMMARY_MAX_LENGTH,
    },
    "title": {
        "min": TITLE_MIN_LENGTH,
        "max": TITLE_MAX_LENGTH,
    },
}


# =============================================================================
# SECTION 4: IMPACT & BLAST RADIUS
# =============================================================================

# Valid impact levels
VALID_IMPACTS: Set[str] = {"CRITICAL", "IMPORTANT", "REFERENCE"}

# Impact weights for ranking
IMPACT_WEIGHTS: Dict[str, float] = {
    "CRITICAL": 1.0,
    "IMPORTANT": 0.7,
    "REFERENCE": 0.4,
}

# Impact descriptions
IMPACT_DESCRIPTIONS: Dict[str, str] = {
    "CRITICAL": "Platform-wide, must be followed by all teams",
    "IMPORTANT": "Standard practice, recommended for most cases",
    "REFERENCE": "Informational, advisory only",
}

# Valid blast radius levels
VALID_BLAST_RADIUS: Set[str] = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

# Blast radius weights for ranking
BLAST_RADIUS_WEIGHTS: Dict[str, float] = {
    "LOW": 0.3,
    "MEDIUM": 0.5,
    "HIGH": 0.8,
    "CRITICAL": 1.0,
}

# Blast radius descriptions
BLAST_RADIUS_DESCRIPTIONS: Dict[str, str] = {
    "LOW": "Single component, easy rollback",
    "MEDIUM": "Multiple components, moderate effort to change",
    "HIGH": "Cross-service impact, significant coordination needed",
    "CRITICAL": "Platform-wide, requires extensive planning",
}


# =============================================================================
# SECTION 5: CONSTRAINT TYPES
# =============================================================================

# Valid constraint types
VALID_CONSTRAINT_TYPES: Set[str] = {"MUST", "MUST_NOT", "SHOULD", "MAY"}

# Constraint type weights (for scoring)
CONSTRAINT_TYPE_WEIGHTS: Dict[str, float] = {
    "MUST": 1.0,
    "MUST_NOT": 1.0,
    "SHOULD": 0.7,
    "MAY": 0.3,
}

# Constraint type descriptions
CONSTRAINT_TYPE_DESCRIPTIONS: Dict[str, str] = {
    "MUST": "Required - violation is a blocker",
    "MUST_NOT": "Prohibited - violation is a blocker",
    "SHOULD": "Recommended - violation is a warning",
    "MAY": "Optional - informational only",
}


# =============================================================================
# SECTION 6: STATUS & WORKFLOW
# =============================================================================

# Decision workflow statuses (for drafts, not stored decisions)
class DraftStatus(str, Enum):
    """Status of a decision draft."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FINALIZED = "finalized"


# Field review statuses
class FieldReviewStatus(str, Enum):
    """Status of individual field review."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


# Validation gate results
class GateStatus(str, Enum):
    """Status of validation gate."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"
    ERROR = "ERROR"


# =============================================================================
# SECTION 7: QUALITY THRESHOLDS
# =============================================================================

# Quality scoring thresholds
QUALITY_GRADE_THRESHOLDS: Dict[str, int] = {
    "EXCELLENT": 90,
    "GOOD": 75,
    "FAIR": 60,
    "POOR": 40,
    "REJECT": 0,
}

# Minimum quality scores for approval
MINIMUM_QUALITY_SCORE: int = 60
MINIMUM_STATEMENT_SCORE: int = 50
MINIMUM_RATIONALE_SCORE: int = 50

# Readability thresholds (Flesch Reading Ease)
MINIMUM_READABILITY_SCORE: int = 30  # Technical content can be complex
RECOMMENDED_READABILITY_SCORE: int = 50


# =============================================================================
# SECTION 8: AREA TAGS
# =============================================================================

# Valid area tags
VALID_AREA_TAGS: Set[str] = {
    # Technical areas
    "FE", "BE", "DB", "INFRA", "CICD", "API", "SECURITY", "DEVOPS",
    # Extended areas
    "DATA", "ML", "MOBILE", "TESTING", "PERF", "UX", "ARCH", "DOCS", "GOVERNANCE",
}

# Area tag labels
AREA_TAG_LABELS: Dict[str, str] = {
    "FE": "Frontend",
    "BE": "Backend",
    "DB": "Database",
    "INFRA": "Infrastructure",
    "CICD": "CI/CD Pipeline",
    "API": "API Design",
    "SECURITY": "Security",
    "DEVOPS": "DevOps",
    "DATA": "Data Engineering",
    "ML": "Machine Learning",
    "MOBILE": "Mobile Development",
    "TESTING": "Testing Strategy",
    "PERF": "Performance",
    "UX": "User Experience",
    "ARCH": "Architecture",
    "DOCS": "Documentation",
    "GOVERNANCE": "Governance",
}


# =============================================================================
# SECTION 9: RELATION TYPES
# =============================================================================

# Valid relation types
VALID_RELATION_TYPES: Set[str] = {
    "depends_on",
    "conflicts_with",
    "informed_by",
    "superseded_by",
    "enables",
    "constrains",
    "implements",
    "extends",
}

# Relation type descriptions
RELATION_TYPE_DESCRIPTIONS: Dict[str, str] = {
    "depends_on": "This decision requires the target to be in effect",
    "conflicts_with": "This decision cannot coexist with target",
    "informed_by": "This decision was influenced by target",
    "superseded_by": "Target decision supersedes this one",
    "enables": "This decision enables/unlocks the target",
    "constrains": "This decision adds constraints to target",
    "implements": "This decision implements policy from target",
    "extends": "This decision extends/specializes the target",
}


# =============================================================================
# SECTION 10: MANTRA LAW REFERENCES
# =============================================================================

class MantraLaw:
    """MANTRA-LAW-001 section references."""
    HUMAN_AUTHORSHIP = "§2.3"      # Human authorship required
    AI_ZERO_AUTHORITY = "§6"       # AI has ZERO authority
    IMMUTABILITY = "§4"            # Stored decisions are immutable
    APPEND_ONLY = "§5"             # No UPDATE, no DELETE


# Law violation messages
LAW_VIOLATION_MESSAGES: Dict[str, str] = {
    "AI_AUTHOR": f"MANTRA-LAW-001 {MantraLaw.HUMAN_AUTHORSHIP}: authored_by must be human",
    "AI_APPROVER": f"MANTRA-LAW-001 {MantraLaw.AI_ZERO_AUTHORITY}: AI cannot approve decisions",
    "UPDATE_ATTEMPT": f"MANTRA-LAW-001 {MantraLaw.IMMUTABILITY}: Cannot update stored decision",
    "DELETE_ATTEMPT": f"MANTRA-LAW-001 {MantraLaw.APPEND_ONLY}: Cannot delete stored decision",
}


# =============================================================================
# SECTION 11: CACHE & TTL CONSTANTS
# =============================================================================

# Cache TTL values (in seconds)
CACHE_TTL_SHORT: int = 60          # 1 minute
CACHE_TTL_MEDIUM: int = 300        # 5 minutes
CACHE_TTL_LONG: int = 3600         # 1 hour
CACHE_TTL_DAY: int = 86400         # 24 hours

# Default cache TTL per data type
CACHE_TTL_DEFAULTS: Dict[str, int] = {
    "decision": CACHE_TTL_LONG,
    "search_results": CACHE_TTL_MEDIUM,
    "validation_result": CACHE_TTL_SHORT,
    "user_session": CACHE_TTL_DAY,
    "analytics": CACHE_TTL_MEDIUM,
}


# =============================================================================
# SECTION 12: SEARCH & RETRIEVAL CONSTANTS
# =============================================================================

# Default search limits
DEFAULT_SEARCH_LIMIT: int = 10
MAX_SEARCH_LIMIT: int = 100

# Similarity thresholds
SIMILARITY_THRESHOLD_STRICT: float = 0.8
SIMILARITY_THRESHOLD_NORMAL: float = 0.65
SIMILARITY_THRESHOLD_LOOSE: float = 0.5

# Default ranking weights
DEFAULT_RANKING_WEIGHTS: Dict[str, float] = {
    "impact": 0.25,
    "blast_radius": 0.20,
    "recency": 0.15,
    "usage": 0.15,
    "similarity": 0.25,
}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_aspects_for_domain(domain_id: str) -> List[str]:
    """Get valid aspects for a domain."""
    return DOMAIN_ASPECT_MATRIX.get(domain_id, [])


def is_aspect_compatible(domain_id: str, aspect_id: str) -> bool:
    """Check if aspect is compatible with domain."""
    return aspect_id in get_aspects_for_domain(domain_id)


def get_domain_for_aspect(aspect_id: str) -> str:
    """Get domain for an aspect."""
    for domain, aspects in DOMAIN_ASPECT_MATRIX.items():
        if aspect_id in aspects:
            return domain
    return ""


def get_field_constraint(field: str, constraint: str) -> int:
    """Get specific constraint for a field."""
    return FIELD_LENGTH_CONSTRAINTS.get(field, {}).get(constraint, 0)


__all__ = [
    # Domain & Aspect
    "VALID_DOMAINS",
    "VALID_ASPECTS",
    "DOMAIN_ASPECT_MATRIX",
    "DOMAIN_LABELS",
    "DOMAIN_DESCRIPTIONS",
    "ASPECT_LABELS",
    "ASPECT_DESCRIPTIONS",
    # Patterns
    "UUID_PATTERN",
    "VERSION_PATTERN",
    "CODE_PATTERN",
    "SCOPE_PATH_PATTERN",
    # Field constraints
    "FIELD_LENGTH_CONSTRAINTS",
    "STATEMENT_MIN_LENGTH",
    "STATEMENT_MAX_LENGTH",
    "RATIONALE_MIN_LENGTH",
    "RATIONALE_MAX_LENGTH",
    # Impact & Blast Radius
    "VALID_IMPACTS",
    "IMPACT_WEIGHTS",
    "VALID_BLAST_RADIUS",
    "BLAST_RADIUS_WEIGHTS",
    # Constraint types
    "VALID_CONSTRAINT_TYPES",
    "CONSTRAINT_TYPE_WEIGHTS",
    # Status enums
    "DraftStatus",
    "FieldReviewStatus",
    "GateStatus",
    # Quality
    "QUALITY_GRADE_THRESHOLDS",
    "MINIMUM_QUALITY_SCORE",
    # Area tags
    "VALID_AREA_TAGS",
    "AREA_TAG_LABELS",
    # Relations
    "VALID_RELATION_TYPES",
    "RELATION_TYPE_DESCRIPTIONS",
    # MANTRA Law
    "MantraLaw",
    "LAW_VIOLATION_MESSAGES",
    # Cache
    "CACHE_TTL_DEFAULTS",
    # Search
    "DEFAULT_SEARCH_LIMIT",
    "MAX_SEARCH_LIMIT",
    "SIMILARITY_THRESHOLD_NORMAL",
    "DEFAULT_RANKING_WEIGHTS",
    # Functions
    "get_aspects_for_domain",
    "is_aspect_compatible",
    "get_domain_for_aspect",
    "get_field_constraint",
]
