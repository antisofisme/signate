"""
MANTRA-SCHEMA-001 Implementation

This module provides the JSON Schema and validation types for the Decision Matrix.
Per MANTRA-LAW-001, this schema is constitutional and immutable.

4 Groups x 4 Features = 16 Decision Taxonomy

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
# GROUP MAPPING (Abbreviated Code → MANTRA-LAW-001 Reference)
# ═══════════════════════════════════════════════════════════════════════════
#
# | Code | Law Reference | Full Name                  | Scope          |
# |------|---------------|----------------------------|----------------|
# | INT  | GROUP-1, §3.2 | Intent & Direction         | WHY / WHAT     |
# | ARCH | GROUP-2, §3.3 | Architecture & Boundaries  | HOW / WHERE    |
# | CTL  | GROUP-3, §3.4 | Control, Policy & Risk     | CAN / MUST NOT |
# | EVO  | GROUP-4, §3.5 | Execution & Evolution      | CHANGE SAFELY  |
#
# ═══════════════════════════════════════════════════════════════════════════
# FEATURE MAPPING (4 Features per Group = 16 Total)
# ═══════════════════════════════════════════════════════════════════════════
#
# GROUP-1 (INT):  F01 Vision, F02 Problem, F03 Scope, F04 Principles
# GROUP-2 (ARCH): F05 Domain, F06 Service, F07 Data, F08 Integration
# GROUP-3 (CTL):  F09 Policy, F10 Authority, F11 Security, F12 Risk
# GROUP-4 (EVO):  F13 Lifecycle, F14 Reversibility, F15 Environment, F16 Drift
#
# ============================================================================

class GroupId(str, Enum):
    """
    4 Groups per MANTRA-LAW-001 §3

    Mapping:
    - INT  = GROUP-1 (§3.2) - Intent & Direction
    - ARCH = GROUP-2 (§3.3) - Architecture & Boundaries
    - CTL  = GROUP-3 (§3.4) - Control, Policy & Risk
    - EVO  = GROUP-4 (§3.5) - Execution & Evolution
    """
    INT = "INT"    # GROUP-1: Intent & Direction (WHY/WHAT)
    ARCH = "ARCH"  # GROUP-2: Architecture & Boundaries (HOW/WHERE)
    CTL = "CTL"    # GROUP-3: Control, Policy & Risk (CAN/MUST NOT)
    EVO = "EVO"    # GROUP-4: Execution & Evolution (CHANGE SAFELY)


class FeatureId(str, Enum):
    """
    16 Features per MANTRA-LAW-001 §3.2-§3.5

    GROUP-1 (INT) - Intent & Direction:
    - F01: Vision & Outcome
    - F02: Problem Statement
    - F03: Scope & Non-Goals
    - F04: Principles & Values

    GROUP-2 (ARCH) - Architecture & Boundaries:
    - F05: Domain & Bounded Context
    - F06: Service & Module Boundary
    - F07: Data Ownership & Sovereignty
    - F08: Integration & Contract Model

    GROUP-3 (CTL) - Control, Policy & Risk:
    - F09: Policy & Rules
    - F10: Approval & Authority Model
    - F11: Security & Compliance Posture
    - F12: Risk & Blast Radius

    GROUP-4 (EVO) - Execution & Evolution:
    - F13: Decision Lifecycle
    - F14: Reversibility & Exit Strategy
    - F15: Environment & Promotion Rules
    - F16: Anti-Drift & Consistency
    """
    # GROUP-1 (INT): Intent & Direction
    F01 = "F01"  # Vision & Outcome
    F02 = "F02"  # Problem Statement
    F03 = "F03"  # Scope & Non-Goals
    F04 = "F04"  # Principles & Values
    # GROUP-2 (ARCH): Architecture & Boundaries
    F05 = "F05"  # Domain & Bounded Context
    F06 = "F06"  # Service & Module Boundary
    F07 = "F07"  # Data Ownership & Sovereignty
    F08 = "F08"  # Integration & Contract Model
    # GROUP-3 (CTL): Control, Policy & Risk
    F09 = "F09"  # Policy & Rules
    F10 = "F10"  # Approval & Authority Model
    F11 = "F11"  # Security & Compliance Posture
    F12 = "F12"  # Risk & Blast Radius
    # GROUP-4 (EVO): Execution & Evolution
    F13 = "F13"  # Decision Lifecycle
    F14 = "F14"  # Reversibility & Exit Strategy
    F15 = "F15"  # Environment & Promotion Rules
    F16 = "F16"  # Anti-Drift & Consistency


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


# ============================================================================
# Group-Feature Compatibility Matrix per MANTRA-LAW-001 §3.2-§3.5
# ============================================================================

GROUP_FEATURE_MATRIX = {
    GroupId.INT: [FeatureId.F01, FeatureId.F02, FeatureId.F03, FeatureId.F04],
    GroupId.ARCH: [FeatureId.F05, FeatureId.F06, FeatureId.F07, FeatureId.F08],
    GroupId.CTL: [FeatureId.F09, FeatureId.F10, FeatureId.F11, FeatureId.F12],
    GroupId.EVO: [FeatureId.F13, FeatureId.F14, FeatureId.F15, FeatureId.F16],
}

# ============================================================================
# Group Metadata (for documentation and UI)
# ============================================================================

GROUP_LAW_REFERENCES = {
    GroupId.INT: "GROUP-1, §3.2",
    GroupId.ARCH: "GROUP-2, §3.3",
    GroupId.CTL: "GROUP-3, §3.4",
    GroupId.EVO: "GROUP-4, §3.5",
}

GROUP_LABELS = {
    GroupId.INT: "Intent & Direction",
    GroupId.ARCH: "Architecture & Boundaries",
    GroupId.CTL: "Control, Policy & Risk",
    GroupId.EVO: "Execution & Evolution",
}

GROUP_SCOPES = {
    GroupId.INT: "WHY / WHAT",
    GroupId.ARCH: "HOW / WHERE",
    GroupId.CTL: "CAN / MUST NOT",
    GroupId.EVO: "CHANGE SAFELY",
}

FEATURE_LABELS = {
    FeatureId.F01: "Vision & Outcome",
    FeatureId.F02: "Problem Statement",
    FeatureId.F03: "Scope & Non-Goals",
    FeatureId.F04: "Principles & Values",
    FeatureId.F05: "Domain & Bounded Context",
    FeatureId.F06: "Service & Module Boundary",
    FeatureId.F07: "Data Ownership & Sovereignty",
    FeatureId.F08: "Integration & Contract Model",
    FeatureId.F09: "Policy & Rules",
    FeatureId.F10: "Approval & Authority Model",
    FeatureId.F11: "Security & Compliance Posture",
    FeatureId.F12: "Risk & Blast Radius",
    FeatureId.F13: "Decision Lifecycle",
    FeatureId.F14: "Reversibility & Exit Strategy",
    FeatureId.F15: "Environment & Promotion Rules",
    FeatureId.F16: "Anti-Drift & Consistency",
}


def is_feature_compatible(group_id: GroupId, feature_id: FeatureId) -> bool:
    """Check if feature is compatible with group per MANTRA-DEC-002"""
    return feature_id in GROUP_FEATURE_MATRIX.get(group_id, [])


# ============================================================================
# Decision Code Generator
# ============================================================================

def generate_decision_code(
    group_id: GroupId,
    feature_id: FeatureId,
    sequence: int,
    version: str
) -> str:
    """
    Generate human-readable decision code.

    Format: {group}-{feature}-{seq:03d}-v{version}
    Example: INT-F01-001-v1.0.0

    Args:
        group_id: Group ID (INT, ARCH, CTL, EVO)
        feature_id: Feature ID (F01 to F16)
        sequence: Sequence number within the feature (1-based)
        version: Semver version string

    Returns:
        Human-readable decision code
    """
    group_abbr = group_id.value
    feature_code = feature_id.value  # Already F01, F02, etc.

    return f"{group_abbr}-{feature_code}-{sequence:03d}-v{version}"


def parse_decision_code(code: str) -> Optional[dict]:
    """
    Parse a decision code back into its components.

    Args:
        code: Decision code like INT-F01-001-v1.0.0

    Returns:
        Dict with group_id, feature_id, sequence, version or None if invalid
    """
    pattern = r"^(INT|ARCH|CTL|EVO)-(F\d{2})-(\d{3})-v(\d+\.\d+\.\d+)$"
    match = re.match(pattern, code)

    if not match:
        return None

    return {
        "group_id": match.group(1),
        "feature_id": match.group(2),  # F01, F02, etc.
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
    - Format: {group}-{feature}{seq}-v{version}
    - Example: INT-F01-001-v1.0.0
    """
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_code: Optional[str] = Field(
        default=None,
        description="Human-readable decision code (e.g., INT-F01-001-v1.0.0). "
                   "Generated on storage, not required for creation."
    )
    group_id: GroupId
    feature_id: FeatureId
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

    @field_validator("feature_id")
    @classmethod
    def validate_group_feature_compatibility(cls, v, info):
        """Validate feature is compatible with group per MANTRA-DEC-002"""
        group_id = info.data.get("group_id")
        if group_id and not is_feature_compatible(group_id, v):
            raise ValueError(
                f"Feature {v} is not compatible with group {group_id}. "
                f"Valid features for {group_id}: {GROUP_FEATURE_MATRIX[group_id]}"
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

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "550e8400-e29b-41d4-a716-446655440000",
                "decision_code": "INT-F01-001-v1.0.0",
                "group_id": "INT",
                "feature_id": "F01",
                "statement": "All user authentication must use multi-factor authentication",
                "rationale": "Security requirement for enterprise systems",
                "constraints": [
                    {
                        "constraint_id": "C-001",
                        "statement": "MFA must support TOTP and WebAuthn",
                        "type": "REQUIREMENT"
                    }
                ],
                "invariants": ["Authentication state is immutable once established"],
                "scope": "ORGANIZATION",
                "blast_radius": "HIGH",
                "version": "1.0.0",
                "supersedes": None,
                "created_by": "human-admin",
                "tags": ["BE", "SECURITY", "API"],
                "tech_stack": ["FastAPI", "JWT", "Redis"]
            }
        }


# ============================================================================
# Input/Output DTOs
# ============================================================================

class DecisionCreate(BaseModel):
    """Input DTO for creating a new decision"""
    group_id: GroupId
    feature_id: FeatureId
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
    tags: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)


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
