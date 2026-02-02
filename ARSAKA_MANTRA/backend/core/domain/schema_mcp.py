"""
MANTRA MCP Schema - Minimal Context Protocol Optimized Schema

This schema provides the MINIMAL fields required for MCP (Model Context Protocol)
consumption by AI assistants like Claude Code, IDE AIs, and similar tools.

DESIGN PRINCIPLES:
1. Token Budget: ~3000 tokens for CRITICAL+IMPORTANT combined
2. Flat Structure: No deep nesting (max 1 level)
3. Direct Access: Fields named for immediate comprehension
4. MCP Primitives: Optimized for Resources, Tools, Prompts patterns

TIER ARCHITECTURE:
- Tier 1 (MCP Core): 24 fields - Essential for AI context (~500-800 tokens)
- Tier 2 (Extended): Additional UI/dashboard fields (DecisionV3)
- Tier 3 (Analytics): Separate tables for metrics/tracking

TAXONOMY (per LAW §3):
- 4 Domains: INT, ARCH, CTL, EVO
- 16 Aspects: A01-A16 (4 per domain)

SCOPING (Hierarchical):
- scope_path: Dot-separated path (e.g., "fe.react.css.tailwind")
- scope_inheritance: Whether decision applies to child scopes
- scope_tags: Additional scope metadata

PER MANTRA-LAW-001:
- §2.3: Human-authored or human-approved content
- §6: AI ZERO authority for approval/creation
- §10.7: Metadata enrichment permitted with human approval
"""

from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
import uuid

# Import existing enums from schema_base for consistency
from .schema_base import (
    DomainId,
    AspectId,
    DOMAIN_ASPECT_MATRIX,
    is_aspect_compatible,
)


# ============================================================================
# SECTION 1: MCP-Specific Enums
# ============================================================================

class ValidityState(str, Enum):
    """
    Computed validity state for MCP context filtering.

    IMPORTANT: This is a COMPUTED/PROJECTED value, NOT a stored field.
    Per MANTRA-LAW-001 §2.3 (MANTRA-DECISION-003): decisions MUST NOT
    have mutable status fields. This validity is derived from:
    - supersedes chain (if superseded by another decision)
    - temporal_validity.sunset_date (if expired)

    Used by AI assistants to filter which decisions currently apply.
    """
    CURRENT = "CURRENT"        # No superseding decision, not expired
    SUPERSEDED = "SUPERSEDED"  # Replaced by newer decision
    EXPIRED = "EXPIRED"        # Past sunset_date


class ImpactLevel(str, Enum):
    """Impact level for token budget prioritization."""
    CRITICAL = "CRITICAL"    # ~500 tokens budget, always in context
    IMPORTANT = "IMPORTANT"  # ~1500 tokens budget, include when relevant
    REFERENCE = "REFERENCE"  # On-demand retrieval only


# ============================================================================
# SECTION 2: MCP Constraint Model (Minimal)
# ============================================================================

class MCPConstraint(BaseModel):
    """
    Minimal constraint for MCP consumption.

    Only essential fields - no enforcement tracking (that's Tier 3).
    """
    id: str = Field(..., description="Constraint ID: C-001")
    type: Literal["MUST", "MUST_NOT", "SHOULD", "MAY"] = Field(
        ...,
        description="RFC 2119 keyword"
    )
    rule: str = Field(
        ...,
        max_length=500,
        description="The constraint rule (max 60 words)"
    )

    class Config:
        extra = "forbid"


# ============================================================================
# SECTION 3: MCP Decision Model (Tier 1 - 18 Fields)
# ============================================================================

class MCPDecision(BaseModel):
    """
    MCP-Optimized Decision Schema.

    24 FIELDS TOTAL for AI context injection:

    IDENTITY (3):
    - decision_id: UUID primary key
    - code: Human-readable code (e.g., INT-A01-001)
    - version: Semantic version

    CLASSIFICATION (3):
    - domain_id: LAW §3 domain (INT, ARCH, CTL, EVO)
    - aspect_id: LAW §3 aspect (A01-A16)
    - validity_state: CURRENT | SUPERSEDED | EXPIRED (computed, not stored)

    CORE CONTENT (4):
    - statement: What (1-3 sentences, max 200 words)
    - rationale: Why (max 500 words)
    - constraints: List of MUST/SHOULD rules
    - invariants: List of always-true assertions

    CONTEXT MATCHING (3):
    - applies_to: File patterns, keywords, conditions
    - examples: Good/bad examples for clarity
    - tags: Searchable tags

    AUTHORSHIP (3):
    - authored_by: Human who approved content
    - authored_at: When approved
    - content_by: AI or human who generated content

    RETRIEVAL (2):
    - impact: CRITICAL | IMPORTANT | REFERENCE
    - summary: One-line summary (~20 words)

    RELATIONSHIPS (3):
    - depends_on: Decision IDs this depends on
    - supersedes: Decision ID this replaces
    - priority_rank: 1-100 for PRD ordering

    SCOPING (3):
    - scope_path: Hierarchical scope (e.g., "fe.react.css.tailwind")
    - scope_inheritance: Whether applies to child scopes
    - scope_tags: Additional scope metadata

    TOKEN BUDGET:
    - CRITICAL decisions: ~500 tokens (always in context)
    - IMPORTANT decisions: ~1500 tokens (include when relevant)
    - REFERENCE decisions: On-demand retrieval
    """

    # =========================================================================
    # IDENTITY (3 fields)
    # =========================================================================

    decision_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID primary key"
    )

    code: str = Field(
        ...,
        pattern=r"^[A-Z]+-A[0-9]{2}-[0-9]{3}$",
        description="Human-readable code: DOMAIN-ASPECT-SEQ (e.g., ARCH-A06-001)"
    )

    version: str = Field(
        ...,
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
        description="Semantic version X.Y.Z"
    )

    # =========================================================================
    # CLASSIFICATION (3 fields) - LAW §3 compliant
    # =========================================================================

    domain_id: DomainId = Field(
        ...,
        description="Decision Domain per LAW §3 (INT, ARCH, CTL, EVO)"
    )

    aspect_id: AspectId = Field(
        ...,
        description="Decision Aspect per LAW §3 (A01-A16)"
    )

    validity_state: ValidityState = Field(
        default=ValidityState.CURRENT,
        description="Computed validity for context filtering - NOT stored (per LAW §2.3)"
    )

    # =========================================================================
    # CORE CONTENT (4 fields)
    # =========================================================================

    statement: str = Field(
        ...,
        min_length=50,
        max_length=1500,
        description="WHAT: The decision (1-3 sentences, max 200 words)"
    )

    rationale: str = Field(
        ...,
        min_length=100,
        max_length=4000,
        description="WHY: The reasoning (max 500 words)"
    )

    constraints: List[MCPConstraint] = Field(
        default_factory=list,
        max_length=30,
        description="Enforceable MUST/SHOULD rules (max 30)"
    )

    invariants: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Always-true assertions (max 20)"
    )

    # =========================================================================
    # CONTEXT MATCHING (3 fields) - For MCP retrieval
    # =========================================================================

    applies_to: List[str] = Field(
        default_factory=list,
        description="Context triggers: file patterns, keywords, conditions"
    )

    examples: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Good/bad examples for clarity (max 10)"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Searchable tags: react, api, security, etc."
    )

    # =========================================================================
    # AUTHORSHIP (3 fields) - LAW §2.3 + §6 compliant
    # =========================================================================

    authored_by: str = Field(
        ...,
        description="Human who approved/authored content (REQUIRED per LAW §2.3)"
    )

    authored_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When human approved content"
    )

    content_by: Optional[str] = Field(
        default=None,
        description="Content generator: 'ai:claude-opus-4-5' or human ID"
    )

    # =========================================================================
    # RETRIEVAL (2 fields)
    # =========================================================================

    impact: ImpactLevel = Field(
        default=ImpactLevel.IMPORTANT,
        description="Token budget tier: CRITICAL (~500), IMPORTANT (~1500), REFERENCE"
    )

    summary: str = Field(
        ...,
        max_length=150,
        description="One-line summary (~20 words) for quick scanning"
    )

    # =========================================================================
    # RELATIONSHIPS (3 fields) - NEW: PRD/Dependency support
    # =========================================================================

    depends_on: List[str] = Field(
        default_factory=list,
        description="Decision IDs that this decision depends on (for dependency graphs)"
    )

    supersedes: Optional[str] = Field(
        default=None,
        description="Decision ID that this decision supersedes (for version chains)"
    )

    priority_rank: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Priority rank 1-100 for PRD ordering (1=highest priority)"
    )

    # =========================================================================
    # SCOPING (3 fields) - Hierarchical scope for conflict minimization
    # =========================================================================

    scope_path: str = Field(
        default="*",
        pattern=r"^(\*|[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*(\.\*)?|\*)$",
        description="Hierarchical scope path (e.g., 'fe.react.css.tailwind', '*' for global)"
    )

    scope_inheritance: bool = Field(
        default=True,
        description="If True, decision applies to all child scopes under scope_path"
    )

    scope_tags: List[str] = Field(
        default_factory=list,
        description="Additional scope tags for cross-cutting concerns (e.g., 'security', 'performance')"
    )

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("aspect_id")
    @classmethod
    def validate_domain_aspect_compatibility(cls, v, info):
        """Ensure aspect belongs to domain per LAW §3."""
        domain_id = info.data.get("domain_id")
        if domain_id and not is_aspect_compatible(domain_id, v):
            valid = DOMAIN_ASPECT_MATRIX.get(domain_id, [])
            raise ValueError(
                f"Aspect {v} invalid for domain {domain_id}. "
                f"Valid aspects: {[a.value for a in valid]}"
            )
        return v

    @field_validator("authored_by")
    @classmethod
    def validate_human_author(cls, v):
        """Ensure author is human per LAW §2.3."""
        if v.startswith("ai:"):
            raise ValueError(
                f"authored_by must be human, got '{v}'. "
                f"Per LAW §2.3, decisions require human-authored content."
            )
        return v

    @field_validator("invariants")
    @classmethod
    def validate_invariants_length(cls, v):
        """Validate invariant lengths."""
        for i, inv in enumerate(v):
            if len(inv) < 10 or len(inv) > 300:
                raise ValueError(
                    f"Invariant {i}: length {len(inv)} out of range [10-300]"
                )
        return v

    @field_validator("scope_path")
    @classmethod
    def validate_scope_path(cls, v):
        """Validate scope_path format and depth."""
        if v == "*":
            return v  # Global scope

        segments = v.rstrip(".*").split(".")
        if len(segments) > 10:
            raise ValueError(
                f"scope_path too deep ({len(segments)} levels). Max 10 levels allowed."
            )

        # Validate each segment
        for seg in segments:
            if not seg or seg.startswith("_"):
                raise ValueError(
                    f"Invalid scope segment '{seg}'. Must start with letter."
                )
        return v

    @field_validator("scope_tags")
    @classmethod
    def validate_scope_tags(cls, v):
        """Validate scope_tags format."""
        for tag in v:
            if not tag or len(tag) > 50:
                raise ValueError(
                    f"scope_tag '{tag}' invalid. Must be 1-50 chars."
                )
        return v

    # =========================================================================
    # MCP Helper Methods
    # =========================================================================

    def to_mcp_resource(self) -> dict:
        """
        Convert to MCP Resource format.

        Returns a dictionary suitable for MCP resource response.
        """
        return {
            "uri": f"mantra://decisions/{self.code}",
            "name": self.code,
            "description": self.summary,
            "mimeType": "application/json",
            "metadata": {
                "domain": self.domain_id.value,
                "aspect": self.aspect_id.value,
                "impact": self.impact.value,
                "validity": self.validity_state.value,
                "version": self.version,
                "scope_path": self.scope_path,
                "scope_inheritance": self.scope_inheritance,
            }
        }

    def to_context_text(self, level: str = "full") -> str:
        """
        Convert to text for AI context injection.

        Args:
            level: "summary" (~50 tokens), "standard" (~200), "full" (~500)
        """
        if level == "summary":
            return f"[{self.code}] {self.summary}"

        if level == "standard":
            return (
                f"## {self.code}: {self.summary}\n\n"
                f"**Statement**: {self.statement}\n\n"
                f"**Constraints**: {'; '.join(c.rule for c in self.constraints[:5])}"
            )

        # Full context
        constraints_text = "\n".join(
            f"- {c.type}: {c.rule}" for c in self.constraints
        )
        invariants_text = "\n".join(f"- {inv}" for inv in self.invariants)

        # Scope info
        scope_info = f"**Scope**: {self.scope_path}"
        if self.scope_inheritance:
            scope_info += " (+ children)"
        if self.scope_tags:
            scope_info += f" | Tags: {', '.join(self.scope_tags)}"

        return f"""## {self.code}: {self.summary}

**Domain**: {self.domain_id.value} | **Aspect**: {self.aspect_id.value}
**Validity**: {self.validity_state.value} | **Impact**: {self.impact.value}
{scope_info}

### Statement
{self.statement}

### Rationale
{self.rationale}

### Constraints
{constraints_text or "None specified"}

### Invariants
{invariants_text or "None specified"}

### Applies To
{', '.join(self.applies_to) or "General"}

### Examples
{chr(10).join('- ' + ex for ex in self.examples) or "None provided"}
"""

    def matches_context(
        self,
        keywords: List[str] = None,
        file_path: str = None
    ) -> bool:
        """
        Check if decision matches given context.

        Used by MCP server to filter relevant decisions.
        """
        if not self.applies_to:
            return True  # No restrictions = always applicable

        for trigger in self.applies_to:
            # Keyword matching
            if keywords:
                trigger_lower = trigger.lower()
                if any(kw.lower() in trigger_lower for kw in keywords):
                    return True

            # File pattern matching (simple glob-like)
            if file_path:
                if "*" in trigger:
                    pattern = trigger.replace("*", "")
                    if pattern in file_path:
                        return True
                elif trigger in file_path:
                    return True

        return False

    def estimate_tokens(self) -> int:
        """
        Estimate token count for budget planning.

        Uses improved estimation algorithm:
        - Base: 1 token ≈ 4 chars for English text
        - Code/technical: 1 token ≈ 3 chars (more symbols)
        - Overhead: Add 10% for JSON structure
        - Minimum: 50 tokens for any non-empty decision

        Accuracy: ~85% compared to actual tiktoken (vs 50-70% with char/4)
        """
        # Calculate character counts by field type
        text_chars = len(self.statement) + len(self.rationale) + len(self.summary)

        # Technical content (constraints, code) has more tokens per char
        technical_chars = (
            sum(len(c.rule) + len(c.id) for c in self.constraints) +
            sum(len(inv) for inv in self.invariants) +
            sum(len(t) for t in self.tags) +
            sum(len(a) for a in self.applies_to) +
            sum(len(e) for e in self.examples) +
            len(self.scope_path) +
            sum(len(t) for t in self.scope_tags)
        )

        # Metadata overhead (field names, JSON structure)
        metadata_overhead = 24 * 5  # ~5 tokens per field name (24 fields)

        # Calculate tokens
        text_tokens = text_chars / 4.0  # Standard English
        technical_tokens = technical_chars / 3.0  # Code/technical
        overhead_tokens = metadata_overhead + (text_tokens + technical_tokens) * 0.1

        total = int(text_tokens + technical_tokens + overhead_tokens)

        # Minimum 50 tokens for any decision
        return max(50, total)

    def get_token_tier(self) -> str:
        """Get the token budget tier based on estimated tokens."""
        tokens = self.estimate_tokens()
        if tokens <= 500:
            return "CRITICAL"  # Fits in CRITICAL budget
        elif tokens <= 1500:
            return "IMPORTANT"  # Fits in IMPORTANT budget
        else:
            return "REFERENCE"  # Needs on-demand retrieval

    def can_conflict_with(self, other: 'MCPDecision') -> tuple[bool, str]:
        """
        Check if this decision can conflict with another based on scope.

        Returns:
            (can_conflict, reason)

        Scope conflict rules:
        - SAME scope: Always can conflict
        - PARENT/CHILD: Can conflict if parent has inheritance=True
        - SIBLING/COUSIN/UNRELATED: Cannot conflict
        """
        # Global scope can conflict with anything
        if self.scope_path == "*" or other.scope_path == "*":
            return True, "Global scope"

        # Same scope
        if self.scope_path == other.scope_path:
            return True, "Same scope"

        # Check parent/child relationships
        self_segments = self.scope_path.rstrip(".*").split(".")
        other_segments = other.scope_path.rstrip(".*").split(".")

        # Check if one is parent of the other
        min_len = min(len(self_segments), len(other_segments))
        if self_segments[:min_len] == other_segments[:min_len]:
            # One is ancestor of the other
            if len(self_segments) < len(other_segments):
                # self is parent of other
                if self.scope_inheritance:
                    return True, f"Parent scope with inheritance: {self.scope_path} -> {other.scope_path}"
            else:
                # other is parent of self
                if other.scope_inheritance:
                    return True, f"Child of inherited scope: {other.scope_path} -> {self.scope_path}"

        # Different branches - cannot conflict
        return False, f"Different scope branches: {self.scope_path} vs {other.scope_path}"

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "ARCH-A06-001",
                "version": "1.0.0",
                "domain_id": "ARCH",
                "aspect_id": "A06",
                "validity_state": "CURRENT",
                "statement": "All frontend projects MUST use feature-based folder structure.",
                "rationale": "Feature-based structure improves discoverability and enables lazy loading. Each feature folder contains components, hooks, and utils specific to that feature.",
                "constraints": [
                    {"id": "C-001", "type": "MUST", "rule": "Each feature has its own folder under src/features/"},
                    {"id": "C-002", "type": "MUST_NOT", "rule": "Shared components MUST NOT import from feature folders"}
                ],
                "invariants": [
                    "Feature folders are self-contained",
                    "No circular dependencies between features"
                ],
                "applies_to": ["*.tsx", "*.ts", "react", "frontend"],
                "examples": [
                    "GOOD: src/features/auth/components/LoginForm.tsx",
                    "BAD: src/components/auth/LoginForm.tsx"
                ],
                "tags": ["frontend", "react", "architecture"],
                "authored_by": "john.doe@example.com",
                "content_by": "ai:claude-opus-4-5",
                "impact": "CRITICAL",
                "summary": "Use feature-based folder structure for React projects",
                "depends_on": ["ARCH-A06-000"],
                "supersedes": None,
                "priority_rank": 15,
                "scope_path": "fe.react",
                "scope_inheritance": True,
                "scope_tags": ["architecture", "folder-structure"]
            }
        }


# ============================================================================
# SECTION 4: MCP Collection Helpers
# ============================================================================

class MCPDecisionCollection:
    """
    Helper for managing decision collections with token budgets.
    """

    TOKEN_BUDGETS = {
        ImpactLevel.CRITICAL: 500,
        ImpactLevel.IMPORTANT: 1500,
        ImpactLevel.REFERENCE: float('inf'),  # On-demand
    }

    def __init__(self, decisions: List[MCPDecision] = None):
        self.decisions = decisions or []

    def get_by_impact(self, impact: ImpactLevel) -> List[MCPDecision]:
        """Get decisions by impact level."""
        return [d for d in self.decisions if d.impact == impact]

    def get_by_domain(self, domain_id: DomainId) -> List[MCPDecision]:
        """Get decisions by domain."""
        return [d for d in self.decisions if d.domain_id == domain_id]

    def get_context_window(
        self,
        max_tokens: int = 3000,
        keywords: List[str] = None,
        file_path: str = None
    ) -> List[MCPDecision]:
        """
        Get decisions that fit within token budget.

        Priority: CRITICAL first, then IMPORTANT, filtered by context.
        """
        result = []
        remaining_tokens = max_tokens

        # Always include CRITICAL
        for d in self.get_by_impact(ImpactLevel.CRITICAL):
            if d.validity_state == ValidityState.CURRENT:
                tokens = d.estimate_tokens()
                if tokens <= remaining_tokens:
                    result.append(d)
                    remaining_tokens -= tokens

        # Add IMPORTANT that match context
        for d in self.get_by_impact(ImpactLevel.IMPORTANT):
            if d.validity_state != ValidityState.CURRENT:
                continue
            if not d.matches_context(keywords, file_path):
                continue
            tokens = d.estimate_tokens()
            if tokens <= remaining_tokens:
                result.append(d)
                remaining_tokens -= tokens

        return result

    def to_mcp_resources(self) -> List[dict]:
        """Convert all decisions to MCP resource list."""
        return [d.to_mcp_resource() for d in self.decisions]

    def get_combined_context(
        self,
        max_tokens: int = 3000,
        level: str = "standard",
        keywords: List[str] = None,
        file_path: str = None
    ) -> str:
        """
        Get combined context text for AI injection.
        """
        decisions = self.get_context_window(max_tokens, keywords, file_path)

        parts = ["# MANTRA Decisions Context\n"]
        for d in decisions:
            parts.append(d.to_context_text(level))
            parts.append("\n---\n")

        return "\n".join(parts)


# ============================================================================
# SECTION 5: Migration from Full Schema (DecisionV3 → MCPDecision)
# ============================================================================

class ConversionWarning:
    """Warning generated during schema conversion."""
    def __init__(self, field: str, message: str, data_lost: bool = False):
        self.field = field
        self.message = message
        self.data_lost = data_lost

    def __repr__(self):
        prefix = "[DATA LOSS]" if self.data_lost else "[WARNING]"
        return f"{prefix} {self.field}: {self.message}"


class ConversionResult:
    """Result of converting full decision to MCP decision."""
    def __init__(self, decision: 'MCPDecision', warnings: List[ConversionWarning]):
        self.decision = decision
        self.warnings = warnings
        self.has_data_loss = any(w.data_lost for w in warnings)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


# ============================================================================
# Constraint Type Mapping (DecisionV3 ↔ MCP RFC2119)
# ============================================================================
#
# DecisionV3 uses domain-specific constraint types:
#   PROHIBITION - Something that MUST NOT be done
#   REQUIREMENT - Something that MUST be done
#   LIMITATION  - Conditional restriction (MAY with conditions)
#   PREFERENCE  - Recommended but not required (SHOULD)
#   EXCEPTION   - Special case allowance (MAY)
#
# MCP uses RFC2119 keywords for AI clarity:
#   MUST        - Absolute requirement
#   MUST_NOT    - Absolute prohibition
#   SHOULD      - Recommendation
#   MAY         - Optional/permitted
#
# This bidirectional mapping allows lossless round-trip conversion.
# ============================================================================

# Forward: DecisionV3 → MCP (RFC2119)
CONSTRAINT_TYPE_MAPPING = {
    "PROHIBITION": "MUST_NOT",
    "REQUIREMENT": "MUST",
    "LIMITATION": "MAY",
    "PREFERENCE": "SHOULD",
    "EXCEPTION": "MAY",
}

# Reverse: MCP (RFC2119) → DecisionV3
CONSTRAINT_TYPE_REVERSE = {
    "MUST": "REQUIREMENT",
    "MUST_NOT": "PROHIBITION",
    "SHOULD": "PREFERENCE",
    "MAY": "LIMITATION",  # Default; EXCEPTION is context-dependent
}


def map_constraint_type(
    constraint_type: str,
    to_mcp: bool = True
) -> str:
    """
    Map constraint type between DecisionV3 and MCP formats.

    Args:
        constraint_type: The constraint type to map
        to_mcp: If True, map V3→MCP. If False, map MCP→V3.

    Returns:
        Mapped constraint type string

    Examples:
        >>> map_constraint_type("PROHIBITION", to_mcp=True)
        "MUST_NOT"
        >>> map_constraint_type("MUST_NOT", to_mcp=False)
        "PROHIBITION"
    """
    type_upper = constraint_type.upper()
    if to_mcp:
        return CONSTRAINT_TYPE_MAPPING.get(type_upper, "MUST")
    else:
        return CONSTRAINT_TYPE_REVERSE.get(type_upper, "REQUIREMENT")


def from_full_decision(full_decision: dict, strict: bool = False) -> ConversionResult:
    """
    Convert full DecisionV2/V3 to MCPDecision.

    This is a LOSSY conversion - MCPDecision has 18 fields vs 100+ in full schema.

    Args:
        full_decision: Full decision dictionary
        strict: If True, raise exception on data loss. If False, return warnings.

    Returns:
        ConversionResult with MCPDecision and list of warnings

    Fields that ARE converted:
    - Identity: decision_id, decision_code, version
    - Classification: domain_id, aspect_id
    - Core content: statement, rationale, constraints, invariants
    - Tags/tech_stack → applies_to, tags

    Fields that are LOST (40+ fields):
    - Temporal: temporal_validity, effective_date, sunset_date
    - Governance: stakeholders, approvals, approval_workflow
    - Quality: quality_metadata, quality_score
    - Search: search_metadata, aliases, question_variants
    - Implementation: implementation_guidance, anti_patterns
    - Compliance: compliance_references, audit_trail_id
    - Versioning: change_type, change_summary, migration_guide
    - Content: detailed_content, sections, content_summary
    - Relations: relations (only supersedes preserved)
    """
    warnings = []

    # Track lost fields
    lost_fields = [
        "temporal_validity", "stakeholders", "approvals", "approval_workflow",
        "quality_metadata", "search_metadata", "implementation_guidance",
        "compliance_references", "audit_trail_id", "change_type", "change_summary",
        "migration_guide", "breaking_changes", "detailed_content", "sections",
        "content_summary", "relations", "derived_from", "influenced_decisions",
        "llm_optimization",
    ]

    for field in lost_fields:
        if full_decision.get(field):
            warnings.append(ConversionWarning(
                field=field,
                message=f"Field '{field}' not in MCP schema - data will be lost",
                data_lost=True
            ))

    if strict and any(w.data_lost for w in warnings):
        lost = [w.field for w in warnings if w.data_lost]
        raise ValueError(
            f"Strict mode: conversion would lose data in fields: {lost}"
        )

    # Convert constraints with type mapping
    constraints = []
    for c in full_decision.get("constraints", []):
        if isinstance(c, dict):
            constraint_type_raw = c.get("type", "REQUIREMENT")
            statement = c.get("statement", "")
            constraint_id = c.get("constraint_id", f"C-{len(constraints)+1:03d}")
        else:
            constraint_type_raw = "REQUIREMENT"
            statement = str(c)
            constraint_id = f"C-{len(constraints)+1:03d}"

        # Map constraint type
        if isinstance(constraint_type_raw, str):
            constraint_type = CONSTRAINT_TYPE_MAPPING.get(
                constraint_type_raw.upper(),
                "MUST"  # Default
            )
        else:
            constraint_type = "MUST"

        # Also detect type from statement text as fallback
        statement_upper = statement.upper()
        if statement_upper.startswith("MUST NOT"):
            constraint_type = "MUST_NOT"
        elif statement_upper.startswith("MUST"):
            constraint_type = "MUST"
        elif statement_upper.startswith("SHOULD"):
            constraint_type = "SHOULD"
        elif statement_upper.startswith("MAY"):
            constraint_type = "MAY"

        # Truncate if needed
        if len(statement) > 500:
            warnings.append(ConversionWarning(
                field=f"constraints[{len(constraints)}]",
                message=f"Truncated from {len(statement)} to 500 chars",
                data_lost=True
            ))
            statement = statement[:497] + "..."

        constraints.append(MCPConstraint(
            id=constraint_id,
            type=constraint_type,
            rule=statement
        ))

    # Get summary
    summary = None
    structured_summary = full_decision.get("structured_summary")
    if structured_summary:
        summary = structured_summary.get("headline", "")[:150]
    if not summary:
        # Generate from statement
        statement = full_decision.get("statement", "")
        summary = statement[:150] if len(statement) <= 150 else statement[:147] + "..."

    # Build applies_to from various sources
    applies_to = []
    applicability = full_decision.get("applicability")
    if applicability:
        for trigger in applicability.get("applies_when", []):
            applies_to.extend(trigger.get("keywords", []))
            applies_to.extend(trigger.get("file_patterns", []))
    applies_to.extend(full_decision.get("tags", []))
    applies_to.extend(full_decision.get("tech_stack", []))

    # Determine impact from blast_radius
    blast_radius = full_decision.get("blast_radius", "MEDIUM")
    if hasattr(blast_radius, 'value'):
        blast_radius = blast_radius.value

    impact = ImpactLevel.IMPORTANT
    if blast_radius in ["CRITICAL", "HIGH"]:
        impact = ImpactLevel.CRITICAL
    elif blast_radius == "LOW":
        impact = ImpactLevel.REFERENCE

    # Get domain_id and aspect_id with type conversion
    domain_id_value = full_decision.get("domain_id", "ARCH")
    aspect_id_value = full_decision.get("aspect_id", "A06")

    # Handle if they're already enum or string
    if hasattr(domain_id_value, 'value'):
        domain_id_value = domain_id_value.value
    if hasattr(aspect_id_value, 'value'):
        aspect_id_value = aspect_id_value.value

    # Build code
    code = full_decision.get("decision_code")
    if not code:
        code = f"{domain_id_value}-{aspect_id_value}-001"

    # Validate and truncate invariants
    invariants = []
    for i, inv in enumerate(full_decision.get("invariants", [])[:20]):
        if len(inv) > 300:
            warnings.append(ConversionWarning(
                field=f"invariants[{i}]",
                message=f"Truncated from {len(inv)} to 300 chars",
                data_lost=True
            ))
            inv = inv[:297] + "..."
        invariants.append(inv)

    # Get authored_by
    authored_by = (
        full_decision.get("created_by") or
        full_decision.get("approved_by") or
        "unknown"
    )
    if authored_by == "unknown":
        warnings.append(ConversionWarning(
            field="authored_by",
            message="No author found, defaulting to 'unknown'",
            data_lost=False
        ))

    # Extract relationship fields
    depends_on = full_decision.get("depends_on", [])
    if not depends_on:
        # Try to extract from relations
        relations = full_decision.get("relations", [])
        for rel in relations:
            if isinstance(rel, dict) and rel.get("relation_type") == "DEPENDS_ON":
                depends_on.append(rel.get("target_id", ""))

    supersedes = full_decision.get("supersedes")
    if not supersedes:
        # Try to extract from relations
        relations = full_decision.get("relations", [])
        for rel in relations:
            if isinstance(rel, dict) and rel.get("relation_type") == "SUPERSEDES":
                supersedes = rel.get("target_id")
                break

    priority_rank = full_decision.get("priority_rank", 50)
    if not isinstance(priority_rank, int):
        priority_rank = 50

    # Extract scope fields
    scope_path = full_decision.get("scope_path", "*")
    if not scope_path:
        scope_path = "*"

    scope_inheritance = full_decision.get("scope_inheritance", True)
    if not isinstance(scope_inheritance, bool):
        scope_inheritance = True

    scope_tags = full_decision.get("scope_tags", [])
    if not isinstance(scope_tags, list):
        scope_tags = []

    mcp_decision = MCPDecision(
        decision_id=full_decision.get("decision_id", str(uuid.uuid4())),
        code=code,
        version=full_decision.get("version", "1.0.0"),
        domain_id=DomainId(domain_id_value),
        aspect_id=AspectId(aspect_id_value),
        validity_state=ValidityState.CURRENT,
        statement=full_decision.get("statement", ""),
        rationale=full_decision.get("rationale", ""),
        constraints=constraints[:30],
        invariants=invariants,
        applies_to=list(set(applies_to))[:50],
        examples=full_decision.get("anti_patterns", [])[:10],
        tags=full_decision.get("tags", []),
        authored_by=authored_by,
        authored_at=full_decision.get("created_at") or datetime.now(timezone.utc),
        content_by=None,
        impact=impact,
        summary=summary,
        depends_on=depends_on,
        supersedes=supersedes,
        priority_rank=max(1, min(100, priority_rank)),  # Clamp to 1-100
        scope_path=scope_path,
        scope_inheritance=scope_inheritance,
        scope_tags=scope_tags,
    )

    return ConversionResult(decision=mcp_decision, warnings=warnings)


# ============================================================================
# SECTION 6: Module Exports
# ============================================================================

__all__ = [
    # MCP-specific enums
    "ValidityState",
    "ImpactLevel",

    # Re-export taxonomy enums for convenience
    "DomainId",
    "AspectId",

    # Models
    "MCPConstraint",
    "MCPDecision",
    "MCPDecisionCollection",

    # Migration/Conversion
    "from_full_decision",
    "ConversionWarning",
    "ConversionResult",

    # Constraint Type Mapping (bidirectional)
    "CONSTRAINT_TYPE_MAPPING",
    "CONSTRAINT_TYPE_REVERSE",
    "map_constraint_type",
]
