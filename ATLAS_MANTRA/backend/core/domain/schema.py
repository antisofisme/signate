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

class GroupId(str, Enum):
    """4 Groups per MANTRA-DEC-001"""
    INT = "INT"    # Intent & Direction (WHY/WHAT)
    ARCH = "ARCH"  # Architecture & Boundaries (HOW/WHERE)
    CTL = "CTL"    # Control, Policy & Risk (CAN/MUST NOT)
    EVO = "EVO"    # Execution & Evolution (CHANGE SAFELY)


class FeatureId(str, Enum):
    """16 Features per MANTRA-DEC-002"""
    F_01 = "F-01"
    F_02 = "F-02"
    F_03 = "F-03"
    F_04 = "F-04"
    F_05 = "F-05"
    F_06 = "F-06"
    F_07 = "F-07"
    F_08 = "F-08"
    F_09 = "F-09"
    F_10 = "F-10"
    F_11 = "F-11"
    F_12 = "F-12"
    F_13 = "F-13"
    F_14 = "F-14"
    F_15 = "F-15"
    F_16 = "F-16"


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


# ============================================================================
# Group-Feature Compatibility Matrix per MANTRA-DEC-002
# ============================================================================

GROUP_FEATURE_MATRIX = {
    GroupId.INT: [FeatureId.F_01, FeatureId.F_02, FeatureId.F_03, FeatureId.F_04],
    GroupId.ARCH: [FeatureId.F_05, FeatureId.F_06, FeatureId.F_07, FeatureId.F_08],
    GroupId.CTL: [FeatureId.F_09, FeatureId.F_10, FeatureId.F_11, FeatureId.F_12],
    GroupId.EVO: [FeatureId.F_13, FeatureId.F_14, FeatureId.F_15, FeatureId.F_16],
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

    Format: {group}-{feature}{seq:03d}-v{version}
    Example: INT-F01-001-v1.0.0

    Args:
        group_id: Group ID (INT, ARCH, CTL, EVO)
        feature_id: Feature ID (F-01 to F-16)
        sequence: Sequence number within the feature (1-based)
        version: Semver version string

    Returns:
        Human-readable decision code
    """
    # Extract group abbreviation
    group_abbr = group_id.value

    # Convert F-01 to F01 (remove dash)
    feature_num = feature_id.value.replace("-", "")

    return f"{group_abbr}-{feature_num}-{sequence:03d}-v{version}"


def parse_decision_code(code: str) -> Optional[dict]:
    """
    Parse a decision code back into its components.

    Args:
        code: Decision code like INT-F01-001-v1.0.0

    Returns:
        Dict with group_id, feature_id, sequence, version or None if invalid
    """
    pattern = r"^(INT|ARCH|CTL|EVO)-F(\d{2})-(\d{3})-v(\d+\.\d+\.\d+)$"
    match = re.match(pattern, code)

    if not match:
        return None

    return {
        "group_id": match.group(1),
        "feature_id": f"F-{match.group(2)}",
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
    related_decisions: List[str] = Field(default_factory=list)

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
                "feature_id": "F-01",
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
                "created_by": "human-admin"
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
