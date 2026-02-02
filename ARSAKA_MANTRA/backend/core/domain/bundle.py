"""
MANTRA Decision Bundles

Bundles are atomic retrieval units - groups of related decisions
that are ALWAYS retrieved together to ensure context completeness.

USE CASES:
1. TOPIC bundles: "React Hooks Best Practices" (5 related decisions)
2. WORKFLOW bundles: "API Endpoint Checklist" (sequential decisions)
3. CHECKLIST bundles: "Security Review" (all-or-nothing)

BENEFITS:
- Reduces retrieval complexity (1 bundle vs N decisions)
- Ensures related context is never missing
- Enables versioned "packages" of decisions
- Simplifies AI context injection

PER MANTRA-LAW-001:
- Bundles are metadata, not decisions themselves
- Bundle membership is mutable (unlike decisions)
- Human approval required for bundle creation
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class BundleType(str, Enum):
    """Type of decision bundle."""
    TOPIC = "TOPIC"           # Related by subject matter
    WORKFLOW = "WORKFLOW"     # Sequential steps/checklist
    CHECKLIST = "CHECKLIST"   # All-or-nothing verification
    CONTEXT = "CONTEXT"       # Context-specific grouping
    STARTER = "STARTER"       # Onboarding/getting started


class BundleStatus(str, Enum):
    """Bundle lifecycle status."""
    DRAFT = "DRAFT"           # Being assembled
    ACTIVE = "ACTIVE"         # Available for retrieval
    DEPRECATED = "DEPRECATED" # Replaced or outdated
    ARCHIVED = "ARCHIVED"     # Historical reference only


class MemberRole(str, Enum):
    """Role of a decision within a bundle."""
    PRIMARY = "PRIMARY"       # Core decision, always included
    SUPPORTING = "SUPPORTING" # Additional context, included by default
    OPTIONAL = "OPTIONAL"     # Included only if requested
    REFERENCE = "REFERENCE"   # Linked but not auto-included


# ============================================================================
# MODELS
# ============================================================================

class BundleMember(BaseModel):
    """A decision's membership in a bundle."""
    decision_id: str = Field(..., description="Decision UUID")
    decision_code: str = Field(..., description="Decision code for display")
    role: MemberRole = Field(default=MemberRole.PRIMARY)
    order: int = Field(default=0, description="Order within bundle (for WORKFLOW)")
    notes: Optional[str] = Field(default=None, description="Why this decision is included")

    class Config:
        extra = "forbid"


class DecisionBundle(BaseModel):
    """
    A bundle of related decisions for atomic retrieval.

    When a bundle is requested, ALL primary and supporting members
    are returned together, ensuring complete context.
    """

    # Identity
    bundle_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID primary key"
    )

    code: str = Field(
        ...,
        pattern=r"^BDL-[A-Z]+-[0-9]{3}$",
        description="Bundle code: BDL-CATEGORY-SEQ (e.g., BDL-REACT-001)"
    )

    name: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Human-readable bundle name"
    )

    # Classification
    bundle_type: BundleType = Field(
        default=BundleType.TOPIC,
        description="Type of bundle"
    )

    status: BundleStatus = Field(
        default=BundleStatus.DRAFT,
        description="Bundle lifecycle status"
    )

    # Content
    description: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="What this bundle covers and when to use it"
    )

    members: List[BundleMember] = Field(
        default_factory=list,
        description="Decisions in this bundle"
    )

    # Matching
    scope_paths: List[str] = Field(
        default_factory=list,
        description="Scope paths this bundle applies to"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Searchable tags"
    )

    trigger_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that trigger this bundle"
    )

    # Metadata
    version: str = Field(
        default="1.0.0",
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
        description="Bundle version"
    )

    created_by: str = Field(
        ...,
        description="Human who created the bundle"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: Optional[datetime] = Field(default=None)

    # Retrieval hints
    estimated_tokens: int = Field(
        default=0,
        description="Estimated token count for all primary+supporting members"
    )

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("members")
    @classmethod
    def validate_members(cls, v):
        """Ensure at least one PRIMARY member."""
        if v and not any(m.role == MemberRole.PRIMARY for m in v):
            raise ValueError("Bundle must have at least one PRIMARY member")
        return v

    @field_validator("created_by")
    @classmethod
    def validate_human_creator(cls, v):
        """Ensure creator is human."""
        if v.startswith("ai:"):
            raise ValueError("Bundles must be created by humans")
        return v

    # =========================================================================
    # Methods
    # =========================================================================

    def get_decision_ids(
        self,
        include_optional: bool = False,
        include_reference: bool = False
    ) -> List[str]:
        """
        Get decision IDs to retrieve for this bundle.

        Args:
            include_optional: Include OPTIONAL members
            include_reference: Include REFERENCE members

        Returns:
            List of decision IDs in order
        """
        result = []
        for member in sorted(self.members, key=lambda m: m.order):
            if member.role == MemberRole.PRIMARY:
                result.append(member.decision_id)
            elif member.role == MemberRole.SUPPORTING:
                result.append(member.decision_id)
            elif member.role == MemberRole.OPTIONAL and include_optional:
                result.append(member.decision_id)
            elif member.role == MemberRole.REFERENCE and include_reference:
                result.append(member.decision_id)
        return result

    def get_primary_ids(self) -> List[str]:
        """Get only PRIMARY member IDs."""
        return [
            m.decision_id for m in self.members
            if m.role == MemberRole.PRIMARY
        ]

    def add_member(
        self,
        decision_id: str,
        decision_code: str,
        role: MemberRole = MemberRole.SUPPORTING,
        order: Optional[int] = None,
        notes: Optional[str] = None
    ) -> None:
        """Add a decision to this bundle."""
        if order is None:
            order = len(self.members)

        self.members.append(BundleMember(
            decision_id=decision_id,
            decision_code=decision_code,
            role=role,
            order=order,
            notes=notes
        ))
        self.updated_at = datetime.now(timezone.utc)

    def remove_member(self, decision_id: str) -> bool:
        """Remove a decision from this bundle."""
        original_len = len(self.members)
        self.members = [m for m in self.members if m.decision_id != decision_id]
        if len(self.members) < original_len:
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def matches_context(
        self,
        scope_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ) -> tuple[bool, float]:
        """
        Check if bundle matches given context.

        Returns:
            (matches, score) - score is 0-1 relevance
        """
        score = 0.0
        matches = 0
        checks = 0

        # Scope matching
        if scope_path and self.scope_paths:
            checks += 1
            for bundle_scope in self.scope_paths:
                if bundle_scope == "*" or scope_path.startswith(bundle_scope):
                    matches += 1
                    break

        # Tag matching
        if tags and self.tags:
            checks += 1
            tag_overlap = len(set(tags) & set(self.tags))
            if tag_overlap > 0:
                matches += 1
                score += tag_overlap / len(self.tags)

        # Keyword matching
        if keywords and self.trigger_keywords:
            checks += 1
            kw_set = set(k.lower() for k in keywords)
            trigger_set = set(k.lower() for k in self.trigger_keywords)
            kw_overlap = len(kw_set & trigger_set)
            if kw_overlap > 0:
                matches += 1
                score += kw_overlap / len(self.trigger_keywords)

        if checks == 0:
            return True, 0.5  # No criteria = neutral match

        final_score = (matches / checks + score) / 2
        return matches > 0, final_score

    def to_summary(self) -> str:
        """Generate a brief summary for context injection."""
        member_count = len(self.members)
        primary_count = len(self.get_primary_ids())
        return (
            f"[{self.code}] {self.name} "
            f"({self.bundle_type.value}, {member_count} decisions, "
            f"{primary_count} primary)"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "bundle_id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "BDL-REACT-001",
                "name": "React Hooks Best Practices",
                "bundle_type": "TOPIC",
                "status": "ACTIVE",
                "description": "Essential decisions for using React hooks correctly. Covers useState, useEffect, custom hooks, and common pitfalls.",
                "members": [
                    {"decision_id": "dec-001", "decision_code": "ARCH-A06-001", "role": "PRIMARY", "order": 0},
                    {"decision_id": "dec-002", "decision_code": "ARCH-A06-002", "role": "PRIMARY", "order": 1},
                    {"decision_id": "dec-003", "decision_code": "ARCH-A06-010", "role": "SUPPORTING", "order": 2}
                ],
                "scope_paths": ["fe.react"],
                "tags": ["react", "hooks", "frontend"],
                "trigger_keywords": ["useState", "useEffect", "custom hook"],
                "estimated_tokens": 1200,
                "created_by": "john.doe@example.com"
            }
        }


# ============================================================================
# BUNDLE MANAGER
# ============================================================================

class BundleManager:
    """
    Manages bundle operations and retrieval.

    In-memory implementation; can be extended with DB persistence.
    """

    def __init__(self, bundles: Optional[List[DecisionBundle]] = None):
        self.bundles: Dict[str, DecisionBundle] = {}
        self._code_index: Dict[str, str] = {}  # code → bundle_id
        self._scope_index: Dict[str, Set[str]] = {}  # scope → bundle_ids
        self._tag_index: Dict[str, Set[str]] = {}  # tag → bundle_ids

        if bundles:
            for bundle in bundles:
                self.add_bundle(bundle)

    def add_bundle(self, bundle: DecisionBundle) -> None:
        """Add or update a bundle."""
        self.bundles[bundle.bundle_id] = bundle
        self._code_index[bundle.code] = bundle.bundle_id

        # Index by scope
        for scope in bundle.scope_paths:
            if scope not in self._scope_index:
                self._scope_index[scope] = set()
            self._scope_index[scope].add(bundle.bundle_id)

        # Index by tag
        for tag in bundle.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(bundle.bundle_id)

    def get_bundle(self, bundle_id: str) -> Optional[DecisionBundle]:
        """Get bundle by ID."""
        return self.bundles.get(bundle_id)

    def get_by_code(self, code: str) -> Optional[DecisionBundle]:
        """Get bundle by code."""
        bundle_id = self._code_index.get(code)
        return self.bundles.get(bundle_id) if bundle_id else None

    def find_bundles(
        self,
        scope_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        status: BundleStatus = BundleStatus.ACTIVE,
        limit: int = 10
    ) -> List[tuple[DecisionBundle, float]]:
        """
        Find bundles matching context.

        Returns:
            List of (bundle, score) tuples, sorted by score descending
        """
        candidates: Set[str] = set()

        # Get candidates from indexes
        if scope_path:
            for scope, bundle_ids in self._scope_index.items():
                if scope == "*" or scope_path.startswith(scope):
                    candidates.update(bundle_ids)

        if tags:
            for tag in tags:
                candidates.update(self._tag_index.get(tag, set()))

        # If no index hits, check all
        if not candidates:
            candidates = set(self.bundles.keys())

        # Score candidates
        results = []
        for bundle_id in candidates:
            bundle = self.bundles.get(bundle_id)
            if not bundle or bundle.status != status:
                continue

            matches, score = bundle.matches_context(scope_path, tags, keywords)
            if matches:
                results.append((bundle, score))

        # Sort by score and limit
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def get_decisions_for_context(
        self,
        scope_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        max_bundles: int = 5,
        include_optional: bool = False
    ) -> List[str]:
        """
        Get all decision IDs that should be retrieved for a context.

        This is the main retrieval method - finds matching bundles
        and returns their member decision IDs.
        """
        bundles = self.find_bundles(
            scope_path=scope_path,
            tags=tags,
            keywords=keywords,
            limit=max_bundles
        )

        decision_ids: List[str] = []
        seen: Set[str] = set()

        for bundle, score in bundles:
            for dec_id in bundle.get_decision_ids(include_optional=include_optional):
                if dec_id not in seen:
                    decision_ids.append(dec_id)
                    seen.add(dec_id)

        return decision_ids

    def get_all_active(self) -> List[DecisionBundle]:
        """Get all active bundles."""
        return [
            b for b in self.bundles.values()
            if b.status == BundleStatus.ACTIVE
        ]

    def remove_bundle(self, bundle_id: str) -> bool:
        """Remove a bundle."""
        bundle = self.bundles.pop(bundle_id, None)
        if bundle:
            self._code_index.pop(bundle.code, None)
            # Clean up indexes
            for scope in bundle.scope_paths:
                if scope in self._scope_index:
                    self._scope_index[scope].discard(bundle_id)
            for tag in bundle.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(bundle_id)
            return True
        return False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_topic_bundle(
    code: str,
    name: str,
    description: str,
    decision_ids: List[tuple[str, str]],  # (id, code) pairs
    scope_paths: List[str],
    tags: List[str],
    created_by: str
) -> DecisionBundle:
    """
    Create a TOPIC bundle quickly.

    Args:
        decision_ids: List of (decision_id, decision_code) tuples
    """
    members = [
        BundleMember(
            decision_id=dec_id,
            decision_code=dec_code,
            role=MemberRole.PRIMARY if i == 0 else MemberRole.SUPPORTING,
            order=i
        )
        for i, (dec_id, dec_code) in enumerate(decision_ids)
    ]

    return DecisionBundle(
        code=code,
        name=name,
        bundle_type=BundleType.TOPIC,
        status=BundleStatus.ACTIVE,
        description=description,
        members=members,
        scope_paths=scope_paths,
        tags=tags,
        created_by=created_by
    )


def create_workflow_bundle(
    code: str,
    name: str,
    description: str,
    steps: List[tuple[str, str, str]],  # (id, code, step_description)
    scope_paths: List[str],
    tags: List[str],
    created_by: str
) -> DecisionBundle:
    """
    Create a WORKFLOW bundle with ordered steps.
    """
    members = [
        BundleMember(
            decision_id=dec_id,
            decision_code=dec_code,
            role=MemberRole.PRIMARY,
            order=i,
            notes=step_desc
        )
        for i, (dec_id, dec_code, step_desc) in enumerate(steps)
    ]

    return DecisionBundle(
        code=code,
        name=name,
        bundle_type=BundleType.WORKFLOW,
        status=BundleStatus.ACTIVE,
        description=description,
        members=members,
        scope_paths=scope_paths,
        tags=tags,
        created_by=created_by
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "BundleType",
    "BundleStatus",
    "MemberRole",
    # Models
    "BundleMember",
    "DecisionBundle",
    # Manager
    "BundleManager",
    # Convenience
    "create_topic_bundle",
    "create_workflow_bundle",
]
