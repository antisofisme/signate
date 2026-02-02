# MANTRA-LAW-001-AMENDMENT-004: Verbosity Control & Projection Boundary

**Document Type**: Constitutional Law Amendment
**Amends**: MANTRA-LAW-001 v1.1.0
**Version**: 1.0.0
**Status**: PROPOSED
**Effective**: Upon Human Approval
**Authority**: Human Decision Only

---

## Amendment Summary

Adds three critical provisions:
1. **§11 - Verbosity Ceiling Law**: Field length limits
2. **§12 - Normative vs Descriptive Law**: Content classification
3. **§13 - Projection Boundary Law**: Summary ≠ source of truth

---

## §11 Verbosity Ceiling Law

### §11.1 Principle

Brevity is mandatory. Verbose content is INVALID.

### §11.2 Field Length Categories

| Category | Format | Max Length | Example Fields |
|----------|--------|------------|----------------|
| SENTENCE | 1-2 sentences | 150 chars | summary, headline |
| PARAGRAPH | 1-2 paragraphs | 500 chars | statement |
| BLOCK | 2-4 paragraphs | 2000 chars | rationale |
| BULLET | List items | 10 items × 100 chars | constraints, invariants |

### §11.3 Enforcement

- Validator MUST reject content exceeding limits
- AI MUST NOT generate verbose content
- Human MAY request exception with recorded justification

### §11.4 Writing Rules

1. **Bullet > Paragraph**: Use bullets when listing
2. **One Idea Per Field**: No mixing concepts
3. **No Repetition**: Same idea MUST NOT appear twice
4. **No Narrative**: Operational language only

---

## §12 Normative vs Descriptive Law

### §12.1 Principle

Every decision content MUST be classified as normative or descriptive.

### §12.2 Classification

| Type | Code | Definition | Example |
|------|------|------------|---------|
| RULE | `R` | Binding constraint | "MUST use feature folders" |
| RATIONALE | `A` | Reasoning/justification | "Because it improves discoverability" |
| CONTEXT | `C` | Background/description | "The team discussed this on 2024-01" |

### §12.3 Binding Nature

- **RULE**: Binding. Violation = non-compliance.
- **RATIONALE**: Explanatory. Supports RULE understanding.
- **CONTEXT**: Informational. No binding effect.

### §12.4 Field Classification

| Field | Type | Binding |
|-------|------|---------|
| statement | R | Yes |
| constraints | R | Yes |
| invariants | R | Yes |
| rationale | A | No |
| examples | C | No |
| applies_to | C | No |

---

## §13 Projection Boundary Law

### §13.1 Principle

Summaries and projections are NOT sources of truth.

### §13.2 Definitions

| Term | Definition |
|------|------------|
| **Source** | Original canonical data in MANTRA |
| **Projection** | Derived view (summary, export, UI display) |

### §13.3 Hierarchy

```
SOURCE (canonical)
   ↓ generates
PROJECTION (derived)
```

### §13.4 Rules

1. Projections MUST NOT be cited as authority
2. Projections MUST NOT modify source
3. Conflicts resolved by SOURCE, not projection
4. AI summaries are ALWAYS projections

### §13.5 Projection Types

| Type | Purpose | Authoritative |
|------|---------|---------------|
| Executive Summary | Quick overview | NO |
| Decision Map | Visualization | NO |
| MCP Context | AI injection | NO |
| UI Display | Human viewing | NO |

### §13.6 Implication for AI

When AI summarizes a long document into MANTRA:
- The summary is a **projection**
- Human MUST verify accuracy
- Original document remains reference
- MANTRA stores the **distilled decision**, not the summary

---

## Schema Implementation Requirements

### Field Metadata (Required)

Every field definition MUST include:

```python
class FieldMeta:
    intent: str           # What this field captures
    max_length: int       # Character limit
    length_category: str  # SENTENCE | PARAGRAPH | BLOCK | BULLET
    input_mode: str       # manual | formula | ai | hybrid
    validation_level: str # hard | soft | advisory
    content_type: str     # R (rule) | A (rationale) | C (context)
```

### Example

```python
FIELD_META = {
    "statement": FieldMeta(
        intent="The decision itself",
        max_length=500,
        length_category="PARAGRAPH",
        input_mode="ai",
        validation_level="hard",
        content_type="R"
    ),
    "rationale": FieldMeta(
        intent="Why this decision",
        max_length=2000,
        length_category="BLOCK",
        input_mode="ai",
        validation_level="hard",
        content_type="A"
    ),
}
```

---

## Validator Requirements

### Three-Gate Validation

| Gate | Type | Checks | Blocker |
|------|------|--------|---------|
| **Gate 1** | Script/Formula | Length, format, uniqueness | Hard |
| **Gate 2** | AI Validator | Redundancy, ambiguity, verbosity | Soft |
| **Gate 3** | Human Gate | Acceptance/rejection | Hard |

### Gate 1: Deterministic (Script)

- Character count within limit
- Required fields present
- Format compliance (UUID, semver, etc.)
- Reference validity

### Gate 2: AI Heuristic

- Detect repetition across fields
- Flag ambiguous language
- Detect over-explanation
- Suggest compression

### Gate 3: Human Final

- Accept as-is
- Reject with reason
- Request revision
- Grant exception

**CRITICAL**: No decision passes without Gate 3.

---

## Approval

| Role | Name | Date | Decision |
|------|------|------|----------|
| Author | Claude Code | 2026-01-29 | PROPOSED |
| Human Reviewer | ___________ | ___________ | PENDING |
| Human Approver | ___________ | ___________ | PENDING |

---

**END OF AMENDMENT**
