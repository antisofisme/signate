"""
MANTRA Field Metadata - Per LAW AMENDMENT-004

Every field has explicit metadata:
- intent: What this field captures
- max_length: Character limit
- length_category: SENTENCE | PARAGRAPH | BLOCK | BULLET
- input_mode: manual | formula | ai | hybrid
- validation_level: hard | soft | advisory
- content_type: R (rule) | A (rationale) | C (context)
"""

from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass


class LengthCategory(str, Enum):
    """Field length categories per LAW §11.2"""
    SENTENCE = "SENTENCE"      # 1-2 sentences, max 150 chars
    PARAGRAPH = "PARAGRAPH"    # 1-2 paragraphs, max 500 chars
    BLOCK = "BLOCK"            # 2-4 paragraphs, max 2000 chars
    BULLET = "BULLET"          # List items, max 10 × 100 chars


class InputMode(str, Enum):
    """How field is populated"""
    MANUAL = "manual"      # Human types directly
    FORMULA = "formula"    # Computed from other fields
    AI = "ai"              # AI generates, human approves
    HYBRID = "hybrid"      # AI suggests, human edits


class ValidationLevel(str, Enum):
    """Validation strictness"""
    HARD = "hard"          # Reject if fails
    SOFT = "soft"          # Warn but allow
    ADVISORY = "advisory"  # Suggest only


class ContentType(str, Enum):
    """Content classification per LAW §12"""
    RULE = "R"         # Binding constraint
    RATIONALE = "A"    # Reasoning/justification
    CONTEXT = "C"      # Background/description


# Length limits per category
LENGTH_LIMITS = {
    LengthCategory.SENTENCE: 150,
    LengthCategory.PARAGRAPH: 500,
    LengthCategory.BLOCK: 2000,
    LengthCategory.BULLET: 1000,  # 10 items × 100 chars
}

BULLET_LIMITS = {
    "max_items": 10,
    "max_item_length": 100,
}


@dataclass
class FieldMeta:
    """Metadata for a MANTRA field"""
    name: str
    intent: str
    max_length: int
    length_category: LengthCategory
    input_mode: InputMode
    validation_level: ValidationLevel
    content_type: ContentType
    required: bool = False
    ai_prompt: Optional[str] = None


# ============================================================================
# FIELD METADATA REGISTRY
# ============================================================================

FIELD_REGISTRY: Dict[str, FieldMeta] = {
    # -------------------------------------------------------------------------
    # IDENTITY FIELDS
    # -------------------------------------------------------------------------
    "decision_id": FieldMeta(
        name="decision_id",
        intent="Unique identifier",
        max_length=36,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.FORMULA,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.CONTEXT,
        required=True,
    ),

    "code": FieldMeta(
        name="code",
        intent="Human-readable code",
        max_length=20,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.FORMULA,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.CONTEXT,
        required=True,
    ),

    "version": FieldMeta(
        name="version",
        intent="Semantic version",
        max_length=15,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.FORMULA,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.CONTEXT,
        required=True,
    ),

    # -------------------------------------------------------------------------
    # CLASSIFICATION FIELDS
    # -------------------------------------------------------------------------
    "domain_id": FieldMeta(
        name="domain_id",
        intent="Decision domain (INT/ARCH/CTL/EVO)",
        max_length=10,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.CONTEXT,
        required=True,
        ai_prompt="Classify into ONE domain: INT (intent), ARCH (architecture), CTL (control), EVO (evolution). Return code only.",
    ),

    "aspect_id": FieldMeta(
        name="aspect_id",
        intent="Decision aspect (A01-A16)",
        max_length=5,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.CONTEXT,
        required=True,
        ai_prompt="Classify aspect within domain. Return A01-A16 code only.",
    ),

    # -------------------------------------------------------------------------
    # CORE CONTENT FIELDS (RULE type - binding)
    # -------------------------------------------------------------------------
    "statement": FieldMeta(
        name="statement",
        intent="The decision itself - WHAT",
        max_length=500,
        length_category=LengthCategory.PARAGRAPH,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.RULE,
        required=True,
        ai_prompt="""Write decision statement in 1-3 sentences.
Structure: [SUBJECT] + [ACTION/DECISION] + [SCOPE]
Rules:
- Present tense, active voice
- Be specific: names, paths, versions
- No hedging: avoid 'might', 'probably'
- Max 500 chars""",
    ),

    "rationale": FieldMeta(
        name="rationale",
        intent="Why this decision - reasoning",
        max_length=2000,
        length_category=LengthCategory.BLOCK,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.RATIONALE,
        required=True,
        ai_prompt="""Explain WHY in 2-4 paragraphs.
Structure: [PROBLEM] → [OPTIONS] → [CHOICE] → [BENEFIT]
Rules:
- State problem first
- List alternatives if any
- Explain why THIS choice
- Use bullets for clarity
- Max 2000 chars""",
    ),

    "constraints": FieldMeta(
        name="constraints",
        intent="Enforceable MUST/SHOULD rules",
        max_length=1000,
        length_category=LengthCategory.BULLET,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.RULE,
        required=False,
        ai_prompt="""Generate enforceable rules.
Each constraint:
- Starts with MUST, MUST NOT, SHOULD, MAY
- One rule per item
- Max 100 chars each
- Max 10 constraints""",
    ),

    "invariants": FieldMeta(
        name="invariants",
        intent="Always-true assertions",
        max_length=1000,
        length_category=LengthCategory.BULLET,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.RULE,
        required=False,
        ai_prompt="""List things that ALWAYS hold true.
Each invariant:
- Absolute truth (no exceptions)
- Testable
- Max 100 chars each
- Max 10 invariants""",
    ),

    # -------------------------------------------------------------------------
    # CONTEXT FIELDS (non-binding)
    # -------------------------------------------------------------------------
    "summary": FieldMeta(
        name="summary",
        intent="One-line summary for quick scanning",
        max_length=150,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.CONTEXT,
        required=True,
        ai_prompt="Write ONE sentence (max 20 words) summarizing the decision. No meta-language.",
    ),

    "applies_to": FieldMeta(
        name="applies_to",
        intent="When/where decision applies",
        max_length=500,
        length_category=LengthCategory.BULLET,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.SOFT,
        content_type=ContentType.CONTEXT,
        required=False,
        ai_prompt="List context triggers: file patterns (*.tsx), keywords (react), conditions. Max 10 items.",
    ),

    "examples": FieldMeta(
        name="examples",
        intent="Good/bad examples",
        max_length=500,
        length_category=LengthCategory.BULLET,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.SOFT,
        content_type=ContentType.CONTEXT,
        required=False,
        ai_prompt="List examples prefixed with GOOD: or BAD:. Max 5 examples.",
    ),

    "tags": FieldMeta(
        name="tags",
        intent="Searchable keywords",
        max_length=200,
        length_category=LengthCategory.BULLET,
        input_mode=InputMode.HYBRID,
        validation_level=ValidationLevel.ADVISORY,
        content_type=ContentType.CONTEXT,
        required=False,
    ),

    # -------------------------------------------------------------------------
    # AUTHORSHIP FIELDS
    # -------------------------------------------------------------------------
    "authored_by": FieldMeta(
        name="authored_by",
        intent="Human who approved",
        max_length=100,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.MANUAL,
        validation_level=ValidationLevel.HARD,
        content_type=ContentType.CONTEXT,
        required=True,
    ),

    "content_by": FieldMeta(
        name="content_by",
        intent="Content generator (AI or human)",
        max_length=100,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.FORMULA,
        validation_level=ValidationLevel.SOFT,
        content_type=ContentType.CONTEXT,
        required=False,
    ),

    # -------------------------------------------------------------------------
    # RETRIEVAL FIELDS
    # -------------------------------------------------------------------------
    "impact": FieldMeta(
        name="impact",
        intent="Token budget tier",
        max_length=20,
        length_category=LengthCategory.SENTENCE,
        input_mode=InputMode.AI,
        validation_level=ValidationLevel.SOFT,
        content_type=ContentType.CONTEXT,
        required=False,
        ai_prompt="Assess impact: CRITICAL (foundational), IMPORTANT (relevant), REFERENCE (on-demand). Return code only.",
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_field_meta(field_name: str) -> Optional[FieldMeta]:
    """Get metadata for a field."""
    return FIELD_REGISTRY.get(field_name)


def get_ai_fields() -> List[str]:
    """Get fields that use AI input."""
    return [
        name for name, meta in FIELD_REGISTRY.items()
        if meta.input_mode in [InputMode.AI, InputMode.HYBRID]
    ]


def get_rule_fields() -> List[str]:
    """Get fields that are binding rules."""
    return [
        name for name, meta in FIELD_REGISTRY.items()
        if meta.content_type == ContentType.RULE
    ]


def get_required_fields() -> List[str]:
    """Get required fields."""
    return [
        name for name, meta in FIELD_REGISTRY.items()
        if meta.required
    ]


def validate_length(field_name: str, value: str) -> tuple[bool, str]:
    """Validate field length against metadata."""
    meta = get_field_meta(field_name)
    if not meta:
        return True, ""

    if len(value) > meta.max_length:
        return False, f"{field_name}: {len(value)} chars exceeds max {meta.max_length}"

    return True, ""


def get_ai_prompt(field_name: str) -> Optional[str]:
    """Get AI prompt for a field."""
    meta = get_field_meta(field_name)
    return meta.ai_prompt if meta else None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "LengthCategory",
    "InputMode",
    "ValidationLevel",
    "ContentType",
    # Constants
    "LENGTH_LIMITS",
    "BULLET_LIMITS",
    # Classes
    "FieldMeta",
    # Registry
    "FIELD_REGISTRY",
    # Functions
    "get_field_meta",
    "get_ai_fields",
    "get_rule_fields",
    "get_required_fields",
    "validate_length",
    "get_ai_prompt",
]
