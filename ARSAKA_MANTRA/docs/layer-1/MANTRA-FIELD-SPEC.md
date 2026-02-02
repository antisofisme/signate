# MANTRA-FIELD-SPEC: Field Generation & Validation Specification

**Document Type**: Technical Specification
**Version**: 1.0.0
**Status**: REFERENCE ONLY
**Purpose**: Define how each field is generated (AI/formula/human) and validated

---

> **NOTE**: This document is for human reference only.
> **Source of Truth**: `backend/core/domain/field_meta.py`
>
> The `FIELD_REGISTRY` in `field_meta.py` is the canonical definition.
> If this document conflicts with code, **code wins**.

---

## Field Generation Model

Each field has:
- **Source**: Who/what generates the value
- **Prompt**: AI instruction (if AI-generated)
- **Validation**: How it's validated and classification

---

## Generation Sources

| Source | Code | Description |
|--------|------|-------------|
| AI | `ai` | AI generates with specific prompt |
| Formula | `formula` | Computed from other fields |
| Human | `human` | Human provides directly |
| System | `system` | Auto-generated (UUID, timestamp) |

---

## Validation Classification

| Type | Code | Count | Description |
|------|------|-------|-------------|
| DETERMINISTIC | `D` | 78 | Rules/formulas, no interpretation |
| SEMANTIC | `S` | 29 | AI validates meaning/quality |
| JUDGMENT | `J` | 15 | Human decision required |

---

## Core Fields

### decision_id
```yaml
field: decision_id
source: system
prompt: null
validation:
  - rule: UUID format
    type: D
    check: "regex ^[0-9a-f]{8}-..."
```

### decision_code
```yaml
field: decision_code
source: formula
prompt: null
formula: "{domain_id}-{aspect_id}-{sequence:03d}"
validation:
  - rule: Format matches pattern
    type: D
    check: "regex ^[A-Z]+-[A-Z]+-[0-9]{3}$"
  - rule: Unique within system
    type: D
    check: "db unique constraint"
```

### statement
```yaml
field: statement
source: ai
prompt: |
  Write a decision statement in 1-3 sentences.
  Structure: [SUBJECT] + [ACTION/DECISION] + [SCOPE]

  Rules:
  - Use present tense, active voice
  - Be specific: names, paths, versions
  - No hedging: avoid 'might', 'probably', 'consider'
  - Max 200 words

  Bad: "After discussions, we decided to probably use..."
  Good: "We use feature folders for React components."

  Context: {user_input}
  Domain: {domain_id}
  Aspect: {aspect_id}
validation:
  - rule: Length 50-1500 chars
    type: D
    check: "len(value) >= 50 and len(value) <= 1500"
  - rule: No hedging language
    type: S
    check: "AI checks for anti-patterns"
  - rule: Matches domain/aspect
    type: S
    check: "AI verifies relevance"
```

### rationale
```yaml
field: rationale
source: ai
prompt: |
  Explain WHY this decision was made.
  Structure: [PROBLEM] → [OPTIONS] → [CHOICE] → [BENEFIT]

  Rules:
  - State the problem first
  - List alternatives considered (if any)
  - Explain why THIS choice (not just what)
  - Quantify benefits when possible
  - Use bullet points for clarity
  - Max 500 words

  Bad: "After extensive discussions, we felt this was best..."
  Good: "Feature folders improve maintainability because..."

  Statement: {statement}
  Context: {user_input}
validation:
  - rule: Length 100-4000 chars
    type: D
    check: "len(value) >= 100 and len(value) <= 4000"
  - rule: Contains reasoning, not just description
    type: S
    check: "AI verifies WHY is explained"
  - rule: Logically supports statement
    type: S
    check: "AI checks coherence"
```

### constraints
```yaml
field: constraints
source: ai
prompt: |
  Generate enforceable rules for this decision.
  Each constraint:
  - Starts with MUST, MUST NOT, SHOULD, SHALL
  - One rule per constraint
  - Include example when helpful
  - Max 60 words each

  Format:
  - constraint_id: C-001, C-002, ...
  - type: MANDATORY | RECOMMENDED | PROHIBITED | CONDITIONAL
  - statement: The rule

  Bad: "It is recommended that developers consider..."
  Good: "MUST use /v{n}/ prefix for API endpoints"

  Statement: {statement}
  Rationale: {rationale}
validation:
  - rule: Max 30 constraints
    type: D
    check: "len(constraints) <= 30"
  - rule: Each statement 20-500 chars
    type: D
    check: "all(20 <= len(c.statement) <= 500)"
  - rule: Unique constraint_ids
    type: D
    check: "len(ids) == len(set(ids))"
  - rule: Starts with MUST/SHOULD/SHALL
    type: D
    check: "regex ^(MUST|SHOULD|SHALL)"
  - rule: Enforceable and testable
    type: S
    check: "AI verifies enforceability"
```

### invariants
```yaml
field: invariants
source: ai
prompt: |
  List things that must ALWAYS be true for this decision.
  Each invariant:
  - States absolute truth (no exceptions)
  - One assertion per item
  - Testable
  - Max 40 words each

  Bad: "Generally speaking, responses should have..."
  Good: "All API responses include request_id header"

  Statement: {statement}
  Constraints: {constraints}
validation:
  - rule: Max 20 invariants
    type: D
    check: "len(invariants) <= 20"
  - rule: Each 10-300 chars
    type: D
    check: "all(10 <= len(i) <= 300)"
  - rule: No hedging language
    type: S
    check: "AI checks for absolutes"
```

---

## Classification Fields

### domain_id
```yaml
field: domain_id
source: ai
prompt: |
  Classify this decision into ONE domain.

  Options:
  - ARCH: Architecture decisions
  - CODE: Coding standards
  - DATA: Data management
  - SEC: Security
  - OPS: Operations
  - PROC: Process
  - UI: User interface
  - API: API design
  - TEST: Testing
  - DOC: Documentation

  Statement: {statement}

  Return ONLY the domain code.
validation:
  - rule: Valid enum value
    type: D
    check: "value in DomainId"
  - rule: Matches content
    type: J
    check: "Human confirms classification"
```

### aspect_id
```yaml
field: aspect_id
source: ai
prompt: |
  Classify the aspect within domain {domain_id}.

  Options vary by domain. For {domain_id}:
  {valid_aspects}

  Statement: {statement}

  Return ONLY the aspect code.
validation:
  - rule: Valid enum value
    type: D
    check: "value in AspectId"
  - rule: Compatible with domain
    type: D
    check: "is_aspect_compatible(domain_id, aspect_id)"
  - rule: Matches content
    type: J
    check: "Human confirms classification"
```

### scope
```yaml
field: scope
source: ai
prompt: |
  Determine the scope of this decision.

  Options:
  - GLOBAL: Applies to entire organization
  - DOMAIN: Applies to specific domain
  - PROJECT: Applies to specific project
  - TEAM: Applies to specific team
  - MODULE: Applies to specific module

  Statement: {statement}

  Return ONLY the scope code.
validation:
  - rule: Valid enum value
    type: D
    check: "value in Scope"
```

### blast_radius
```yaml
field: blast_radius
source: ai
prompt: |
  Assess the impact level if this decision changes.

  Options:
  - LOW: Minimal impact, easy to change
  - MEDIUM: Moderate impact, some effort to change
  - HIGH: Significant impact, hard to change
  - CRITICAL: Breaking change, affects many systems

  Consider:
  - How many systems/teams affected?
  - How hard to rollback?
  - What breaks if this changes?

  Statement: {statement}
  Scope: {scope}

  Return ONLY the level code.
validation:
  - rule: Valid enum value
    type: D
    check: "value in BlastRadius"
  - rule: Reasonable for scope
    type: S
    check: "AI validates consistency"
```

---

## Summary Fields

### structured_summary.headline
```yaml
field: structured_summary.headline
source: ai
prompt: |
  Write ONE sentence (max 20 words) summarizing the decision.

  Bad: "This document describes our decision regarding..."
  Good: "We use feature folders for React components"

  Statement: {statement}
validation:
  - rule: Max 150 chars
    type: D
    check: "len(value) <= 150"
```

### structured_summary.abstract
```yaml
field: structured_summary.abstract
source: ai
prompt: |
  Write 2-3 sentences covering WHAT and WHY.
  Max 80 words. Self-contained.

  Statement: {statement}
  Rationale: {rationale}
validation:
  - rule: Max 500 chars
    type: D
    check: "len(value) <= 500"
```

### structured_summary.executive_summary
```yaml
field: structured_summary.executive_summary
source: ai
prompt: |
  Write 1 paragraph (100-200 words) for stakeholders.
  Include: decision, reason, impact, timeline if relevant.

  Statement: {statement}
  Rationale: {rationale}
  Scope: {scope}
  Blast_radius: {blast_radius}
validation:
  - rule: Max 1500 chars
    type: D
    check: "len(value) <= 1500"
```

### structured_summary.key_points
```yaml
field: structured_summary.key_points
source: ai
prompt: |
  List 3-7 main takeaways as bullet points.
  Each point: 1 sentence, actionable.

  Statement: {statement}
  Rationale: {rationale}
  Constraints: {constraints}
validation:
  - rule: 3-7 items
    type: D
    check: "3 <= len(value) <= 7"
```

### structured_summary.for_developers
```yaml
field: structured_summary.for_developers
source: ai
prompt: |
  Write ~100 words for developers.
  Focus: HOW to implement, code examples, gotchas.

  Statement: {statement}
  Constraints: {constraints}
validation:
  - rule: Max 800 chars
    type: D
    check: "len(value) <= 800"
```

### structured_summary.for_architects
```yaml
field: structured_summary.for_architects
source: ai
prompt: |
  Write ~100 words for architects.
  Focus: System design implications, integration points, scalability.

  Statement: {statement}
  Rationale: {rationale}
validation:
  - rule: Max 800 chars
    type: D
    check: "len(value) <= 800"
```

### structured_summary.for_managers
```yaml
field: structured_summary.for_managers
source: ai
prompt: |
  Write ~100 words for managers.
  Focus: Business impact, resources needed, risks.

  Statement: {statement}
  Rationale: {rationale}
  Scope: {scope}
validation:
  - rule: Max 800 chars
    type: D
    check: "len(value) <= 800"
```

---

## Computed Fields (Formula)

### version
```yaml
field: version
source: formula
formula: |
  if new_decision:
    return "1.0.0"
  elif breaking_change:
    return increment_major(prev_version)
  elif new_feature:
    return increment_minor(prev_version)
  else:
    return increment_patch(prev_version)
validation:
  - rule: Semantic version format
    type: D
    check: "regex ^[0-9]+\\.[0-9]+\\.[0-9]+$"
```

### created_at
```yaml
field: created_at
source: system
formula: "datetime.utcnow()"
validation:
  - rule: ISO 8601 format
    type: D
```

### content_hash
```yaml
field: content_hash
source: formula
formula: "sha256(statement + rationale + constraints + invariants)[:16]"
validation:
  - rule: 16 char hex
    type: D
    check: "regex ^[0-9a-f]{16}$"
```

### llm_optimization.total_token_count
```yaml
field: llm_optimization.total_token_count
source: formula
formula: "count_tokens(all_text_fields)"
validation:
  - rule: Positive integer
    type: D
    check: "value > 0"
```

### knowledge_consumption.reading_time_minutes
```yaml
field: knowledge_consumption.reading_time_minutes
source: formula
formula: "word_count / 200"  # 200 wpm average
validation:
  - rule: Positive number
    type: D
    check: "value > 0"
```

---

## Human Decision Fields

### approved_by
```yaml
field: approved_by
source: human
prompt: null  # Human provides
validation:
  - rule: Not empty when approved
    type: D
    check: "value is not None"
  - rule: Valid human identifier
    type: D
    check: "not value.startswith('ai:')"
  - rule: Has authority to approve
    type: J
    check: "Human verifies authority"
```

### temporal_validity.sunset_date
```yaml
field: temporal_validity.sunset_date
source: human
prompt: null  # Human decides expiry
validation:
  - rule: Future date if set
    type: D
    check: "value > today()"
  - rule: Reasonable timeframe
    type: J
    check: "Human confirms"
```

---

## Validation Summary by Type

### DETERMINISTIC (D) - 78 Rules
Checked by code/regex/formula. No interpretation.

Examples:
- Length limits
- Format validation (UUID, semver, regex)
- Enum membership
- Uniqueness constraints
- Range checks

### SEMANTIC (S) - 29 Rules
Checked by AI validator. Requires interpretation.

Examples:
- Content matches domain/aspect
- Rationale supports statement
- Constraints are enforceable
- No hedging language
- Logical coherence

### JUDGMENT (J) - 15 Rules
Requires human decision. Cannot be automated.

Examples:
- Classification correctness
- Authority verification
- Sunset date appropriateness
- Exception approval
- Conflict resolution

---

## Implementation Notes

### AI Prompt Template
```python
def get_field_prompt(field_name: str, context: dict) -> str:
    spec = FIELD_SPECS[field_name]
    if spec["source"] != "ai":
        return None
    return spec["prompt"].format(**context)
```

### Validation Execution
```python
def validate_field(field_name: str, value: Any, context: dict) -> List[ValidationResult]:
    results = []
    spec = FIELD_SPECS[field_name]

    for rule in spec["validation"]:
        if rule["type"] == "D":
            # Run deterministic check
            results.append(run_deterministic(rule, value))
        elif rule["type"] == "S":
            # Queue for AI validation
            results.append(queue_semantic(rule, value, context))
        elif rule["type"] == "J":
            # Flag for human review
            results.append(flag_for_human(rule, value))

    return results
```

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-01-29 | Initial specification |

---

**END OF FIELD SPECIFICATION**
