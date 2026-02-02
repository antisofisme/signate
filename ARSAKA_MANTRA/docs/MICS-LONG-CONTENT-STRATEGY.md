# MICS Long Content Strategy
# Bagaimana MANTRA Menangani Keputusan Panjang

**Version**: 1.0
**Last Updated**: 2026-01-27
**Issue**: MANTRA validation currently penalizes long content

---

## Problem Statement

### Current Validation Limits (Ditemukan di quality_scoring.py)

```python
# Q-001: Statement length
if 10 <= word_count <= 200:      # ✅ Full score
    score += 4
else:
    score += 2                    # ❌ Penalized if > 200 words

# Q-006: Rationale length
if 20 <= word_count <= 500:      # ✅ Full score
    score += 4
else:
    score += 2                    # ❌ Penalized if > 500 words
```

### Real-World Decision Examples yang Tidak Fit

**Contoh 1: Folder Structure Standard**
```markdown
## Statement
All projects must follow the standardized folder structure.

## Rationale
Consistent folder structure improves developer experience and...

## The ACTUAL Content (1500+ words):
```
src/
├── features/           # Feature-based modules
│   ├── auth/
│   │   ├── api/       # API handlers
│   │   ├── hooks/     # React hooks
│   │   ├── components/ # UI components
│   │   └── index.ts   # Public exports
│   └── ...
├── shared/
│   ├── components/    # Shared UI
│   ├── hooks/        # Shared hooks
│   └── utils/        # Utilities
...

### Rules:
1. Feature folders must contain index.ts
2. Shared components must not import from features
3. API handlers must be in api/ subfolder
...

### Examples:
Good: src/features/auth/api/login.ts
Bad: src/auth/login.ts
...
```

**Masalah**: Content yang berguna (struktur, rules, examples) tidak fit di 200+500 = 700 words limit.

---

**Contoh 2: Coding Convention Standard**
```markdown
## Statement
TypeScript code must follow the project coding conventions.

## Rationale
Consistent code style improves readability...

## The ACTUAL Content (2000+ words):

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | userData |
| Components | PascalCase | UserCard |
| Constants | UPPER_SNAKE | MAX_RETRIES |
...

### File Naming
- Components: PascalCase.tsx
- Hooks: useCamelCase.ts
- Utils: camelCase.ts
...

### Import Order
1. External packages
2. Internal modules
3. Relative imports
...

### Code Examples
```typescript
// Good
export function getUserData(id: string): Promise<User> {
  ...
}

// Bad
export function get_user_data(id) {
  ...
}
```
```

**Masalah**: Full coding convention bisa 2000-5000 words dengan examples.

---

## Analysis: Tiga Masalah Terpisah

### Problem 1: Validation Limits Terlalu Ketat

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT LIMITS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Statement:  10-200 words    ← Terlalu pendek untuk standards  │
│   Rationale:  20-500 words    ← Terlalu pendek untuk detail     │
│   Total:      ~700 words max  ← Tidak cukup untuk real specs    │
│                                                                  │
│   Real-world needs:                                              │
│   • Folder structure: 500-1500 words                            │
│   • Coding conventions: 1000-3000 words                         │
│   • Architecture decisions: 500-2000 words                      │
│   • API specifications: 1000-5000 words                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Problem 2: No Structure for Long Content

```
Current decision record:
{
  "statement": "Short summary",     ← Max 200 words
  "rationale": "Why we decided",    ← Max 500 words
  "constraints": [...],             ← List of rules
  "invariants": [...]               ← List of invariants
}

Missing:
• examples (code samples, diagrams)
• detailed_specification (full content)
• sections (structured breakdown)
• attachments (external files)
```

### Problem 3: Token Budget untuk Context Injection

```
┌─────────────────────────────────────────────────────────────────┐
│              TOKEN BUDGET PROBLEM                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Scenario: AI assistant needs context for coding task          │
│                                                                  │
│   Relevant decisions:                                            │
│   • Folder structure (2000 words = ~3000 tokens)                │
│   • Coding conventions (3000 words = ~4500 tokens)              │
│   • API patterns (1500 words = ~2250 tokens)                    │
│   • Security rules (1000 words = ~1500 tokens)                  │
│                                                                  │
│   Total: ~11,250 tokens just for decisions                      │
│                                                                  │
│   Problem:                                                       │
│   • Claude Code context: useful but fills up fast               │
│   • Smaller models: might not fit at all                        │
│   • User's actual request: needs room too!                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Solution Architecture

### Solution 1: Two-Layer Decision Content

```
┌─────────────────────────────────────────────────────────────────┐
│                  TWO-LAYER CONTENT MODEL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   LAYER A: Executive Summary (Validated, Token-Efficient)       │
│   ─────────────────────────────────────────────────────────     │
│   • statement: 10-200 words (WHAT)                              │
│   • rationale: 20-500 words (WHY)                               │
│   • constraints: List of key rules                              │
│   → Used for: Quick context, token-limited situations           │
│   → Validated: Yes (Q-001 to Q-025)                             │
│                                                                  │
│   LAYER B: Detailed Specification (Stored, Minimal Validation)  │
│   ─────────────────────────────────────────────────────────     │
│   • detailed_content: Markdown, unlimited length                │
│   • sections: Structured breakdown                              │
│   • examples: Code samples, diagrams                            │
│   → Used for: Full reference, on-demand fetch                   │
│   → Validated: Structure only (not length/readability)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Schema Update

```python
class Decision(BaseModel):
    # ... existing fields (Layer A) ...

    # NEW: Layer B - Detailed Content
    detailed_content: Optional[str] = Field(
        default=None,
        description="""
        Full specification in Markdown format.

        Use when decision requires:
        - Code examples
        - Folder structures
        - Detailed rules with examples
        - Diagrams (as ASCII or Mermaid)
        - Tables

        NOT validated for length/readability.
        Validated for: Markdown structure, no broken links.
        """
    )

    sections: List[ContentSection] = Field(
        default_factory=list,
        description="Structured sections for long content"
    )

    content_summary: Optional[str] = Field(
        default=None,
        description="Auto-generated 1-paragraph summary for token-efficient context"
    )


class ContentSection(BaseModel):
    """Structured section for detailed content"""
    section_id: str
    title: str
    section_type: SectionType  # OVERVIEW, RULES, EXAMPLES, STRUCTURE, DIAGRAM
    content: str
    order: int


class SectionType(str, Enum):
    OVERVIEW = "OVERVIEW"      # High-level explanation
    RULES = "RULES"            # List of rules/conventions
    EXAMPLES = "EXAMPLES"      # Code examples (good/bad)
    STRUCTURE = "STRUCTURE"    # Folder/file structures
    DIAGRAM = "DIAGRAM"        # ASCII/Mermaid diagrams
    REFERENCE = "REFERENCE"    # External links, docs
```

### Example: Folder Structure Decision

```json
{
  "decision_id": "...",
  "decision_code": "ARCH-F06-001-v1.0.0",
  "group_id": "ARCH",
  "feature_id": "F06",

  "statement": "All projects must follow the feature-based folder structure with strict module boundaries.",

  "rationale": "Feature-based structure improves code discoverability, enables lazy loading, and enforces bounded contexts. This structure scales from small to large applications because each feature is self-contained.",

  "constraints": [
    {"constraint_id": "C-001", "statement": "Feature folders must have index.ts as single export point", "type": "REQUIREMENT"},
    {"constraint_id": "C-002", "statement": "Shared components cannot import from feature folders", "type": "PROHIBITION"},
    {"constraint_id": "C-003", "statement": "Maximum 3 levels of nesting within feature folder", "type": "LIMITATION"}
  ],

  "detailed_content": "## Full Folder Structure\n\n```\nsrc/\n├── features/\n│   ├── auth/\n│   │   ├── api/\n│   │   │   ├── login.ts\n│   │   │   └── logout.ts\n│   │   ├── components/\n│   │   │   ├── LoginForm.tsx\n│   │   │   └── LogoutButton.tsx\n│   │   ├── hooks/\n│   │   │   └── useAuth.ts\n│   │   └── index.ts\n│   ├── dashboard/\n│   │   └── ...\n│   └── settings/\n│       └── ...\n├── shared/\n│   ├── components/\n│   │   ├── Button.tsx\n│   │   └── Input.tsx\n│   ├── hooks/\n│   │   └── useLocalStorage.ts\n│   └── utils/\n│       └── formatDate.ts\n├── pages/\n│   ├── index.tsx\n│   └── [...slug].tsx\n└── app/\n    ├── layout.tsx\n    └── providers.tsx\n```\n\n## Rules\n\n### Rule 1: Feature Module Exports\nEvery feature folder MUST have `index.ts` that re-exports public API:\n\n```typescript\n// features/auth/index.ts\nexport { LoginForm } from './components/LoginForm';\nexport { useAuth } from './hooks/useAuth';\nexport { login, logout } from './api';\n// Do NOT export internal components\n```\n\n### Rule 2: Import Boundaries\n\n**Allowed imports:**\n```typescript\n// From feature to shared - OK\nimport { Button } from '@/shared/components';\n\n// From feature to feature via index - OK\nimport { useAuth } from '@/features/auth';\n```\n\n**Prohibited imports:**\n```typescript\n// Direct import into feature internals - BAD\nimport { LoginForm } from '@/features/auth/components/LoginForm';\n\n// Shared importing from feature - BAD\nimport { useAuth } from '@/features/auth';\n```\n\n...(more rules, examples, diagrams)...",

  "sections": [
    {
      "section_id": "S-001",
      "title": "Folder Structure",
      "section_type": "STRUCTURE",
      "content": "```\nsrc/\n├── features/...\n```",
      "order": 1
    },
    {
      "section_id": "S-002",
      "title": "Module Export Rules",
      "section_type": "RULES",
      "content": "1. Every feature must have index.ts\n2. ...",
      "order": 2
    },
    {
      "section_id": "S-003",
      "title": "Import Examples",
      "section_type": "EXAMPLES",
      "content": "```typescript\n// Good\nimport...\n\n// Bad\nimport...\n```",
      "order": 3
    }
  ],

  "content_summary": "Feature-based folder structure with src/features/, src/shared/, and src/pages/. Features must export via index.ts, shared cannot import from features. Max 3 nesting levels."
}
```

---

## Solution 2: Smart Context Injection

### Tiered Content Delivery

```
┌─────────────────────────────────────────────────────────────────┐
│              SMART CONTEXT INJECTION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   TIER 1: Micro (100 tokens per decision)                       │
│   ────────────────────────────────────────                      │
│   content_summary only                                          │
│   Use: Many decisions, token-limited                            │
│   Example: "Feature-based structure, index.ts exports, no       │
│            cross-feature imports"                               │
│                                                                  │
│   TIER 2: Standard (500 tokens per decision)                    │
│   ────────────────────────────────────────                      │
│   statement + rationale + constraints                           │
│   Use: Moderate context, most common                            │
│                                                                  │
│   TIER 3: Detailed (2000+ tokens per decision)                  │
│   ────────────────────────────────────────                      │
│   Full content including detailed_content                       │
│   Use: Specific decision deep-dive                              │
│                                                                  │
│   TIER 4: Sections (Variable)                                   │
│   ────────────────────────────────────────                      │
│   Specific sections only (e.g., just EXAMPLES)                  │
│   Use: Need code examples, not full spec                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### MCP Tool Update

```python
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="mantra_get_context",
            description="Get decision context with configurable detail level",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "What you're working on"
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["micro", "standard", "detailed", "sections"],
                        "default": "standard",
                        "description": """
                        - micro: Just summaries (~100 tokens/decision)
                        - standard: Statement + rationale + constraints (~500 tokens)
                        - detailed: Full content including examples (~2000+ tokens)
                        - sections: Request specific section types
                        """
                    },
                    "section_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "If detail_level=sections, which types: RULES, EXAMPLES, STRUCTURE, DIAGRAM"
                    },
                    "max_decisions": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum decisions to return"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Token budget - system will adjust detail_level automatically"
                    }
                }
            }
        )
    ]
```

### Automatic Token Budget Management

```python
async def get_context_with_budget(
    task_description: str,
    max_tokens: int = 4000,
    preferred_detail: str = "standard"
) -> ContextResponse:
    """
    Get decision context while respecting token budget.

    Algorithm:
    1. Find relevant decisions (semantic search)
    2. Estimate tokens needed at preferred_detail
    3. If over budget, reduce detail level
    4. If still over, reduce decision count
    5. Never exceed max_tokens
    """

    # Find relevant decisions
    decisions = await find_relevant_decisions(task_description)

    # Estimate tokens per detail level
    TOKEN_ESTIMATES = {
        "micro": 100,
        "standard": 500,
        "detailed": 2500,
    }

    detail_level = preferred_detail
    included_decisions = []
    current_tokens = 0

    for decision in decisions:
        # Estimate tokens for this decision at current detail level
        estimated = estimate_tokens(decision, detail_level)

        if current_tokens + estimated > max_tokens:
            # Try lower detail level
            if detail_level == "detailed":
                detail_level = "standard"
                estimated = estimate_tokens(decision, detail_level)
            elif detail_level == "standard":
                detail_level = "micro"
                estimated = estimate_tokens(decision, detail_level)
            else:
                # Even micro doesn't fit, stop adding
                break

        if current_tokens + estimated <= max_tokens:
            included_decisions.append({
                "decision": decision,
                "detail_level": detail_level
            })
            current_tokens += estimated

    return ContextResponse(
        decisions=included_decisions,
        total_tokens=current_tokens,
        detail_levels_used=get_detail_summary(included_decisions),
        truncated=len(included_decisions) < len(decisions)
    )
```

---

## Solution 3: Validation Rules Update

### Updated Q-001 and Q-006

```python
def score_statement_quality(record: Dict[str, Any]) -> Tuple[int, QualityDimension]:
    """
    Score statement quality (Q-001 to Q-005).

    UPDATED: Statement is EXECUTIVE SUMMARY, not full content.
    Full content goes in detailed_content field.
    """
    statement = record.get('statement') or ''
    has_detailed_content = bool(record.get('detailed_content'))

    words = statement.lower().split()
    word_count = len(words)

    # Q-001: Length validation
    # If detailed_content exists, statement should be concise summary
    # If no detailed_content, statement can be longer

    if has_detailed_content:
        # Statement is summary - should be concise
        ideal_range = (10, 100)  # Shorter when detail exists
        max_acceptable = 200
    else:
        # Statement is complete decision - can be longer
        ideal_range = (20, 300)  # Allow longer
        max_acceptable = 500

    if ideal_range[0] <= word_count <= ideal_range[1]:
        score += 4
        rules_passed.append('Q-001')
    elif word_count <= max_acceptable:
        score += 3
        rules_passed.append('Q-001')
        suggestions.append(f'Consider adding detailed_content for specifications.')
    else:
        score += 2
        rules_failed.append('Q-001')
        suggestions.append(f'Statement is {word_count} words. Move detailed content to detailed_content field.')
```

### New Q-026 to Q-030: Detailed Content Validation

```python
def score_detailed_content_quality(record: Dict[str, Any]) -> Tuple[int, QualityDimension]:
    """
    Score detailed_content quality (Q-026 to Q-030).

    NEW validation for long-form content.
    Focus on STRUCTURE, not length.
    """
    detailed_content = record.get('detailed_content', '')
    sections = record.get('sections', [])

    score = 0
    rules_passed = []
    rules_failed = []
    suggestions = []

    if not detailed_content and not sections:
        # No detailed content - that's OK, not required
        return 0, QualityDimension(
            dimension='detailed_content',
            score=0,
            max_score=20,
            rules_passed=['Q-026'],  # Optional field
            rules_failed=[],
            suggestions=[]
        )

    # Q-026: Has headers/structure (if long)
    word_count = len(detailed_content.split())
    has_headers = bool(re.search(r'^#{1,3}\s', detailed_content, re.MULTILINE))

    if word_count > 200 and not has_headers:
        rules_failed.append('Q-026')
        suggestions.append('Long content should have Markdown headers for structure.')
    else:
        score += 4
        rules_passed.append('Q-026')

    # Q-027: Code blocks are valid (if present)
    code_blocks = re.findall(r'```(\w+)?\n(.*?)```', detailed_content, re.DOTALL)
    valid_languages = {'typescript', 'javascript', 'python', 'bash', 'json', 'yaml', 'sql', ''}

    invalid_langs = [lang for lang, _ in code_blocks if lang and lang.lower() not in valid_languages]
    if code_blocks and not invalid_langs:
        score += 4
        rules_passed.append('Q-027')
    elif invalid_langs:
        score += 2
        rules_failed.append('Q-027')
        suggestions.append(f'Unknown code block languages: {invalid_langs}')
    else:
        score += 4  # No code blocks is fine
        rules_passed.append('Q-027')

    # Q-028: Sections are properly typed
    valid_section_types = {'OVERVIEW', 'RULES', 'EXAMPLES', 'STRUCTURE', 'DIAGRAM', 'REFERENCE'}
    if sections:
        invalid_types = [s.section_type for s in sections if s.section_type not in valid_section_types]
        if not invalid_types:
            score += 4
            rules_passed.append('Q-028')
        else:
            score += 2
            rules_failed.append('Q-028')
            suggestions.append(f'Invalid section types: {invalid_types}')
    else:
        score += 4
        rules_passed.append('Q-028')

    # Q-029: Has examples if content mentions rules
    mentions_rules = any(kw in detailed_content.lower() for kw in ['must', 'should', 'cannot', 'prohibited'])
    has_examples = 'example' in detailed_content.lower() or any(s.section_type == 'EXAMPLES' for s in sections)

    if mentions_rules and has_examples:
        score += 4
        rules_passed.append('Q-029')
    elif mentions_rules and not has_examples:
        score += 2
        rules_failed.append('Q-029')
        suggestions.append('Content has rules but no examples. Add examples for clarity.')
    else:
        score += 4
        rules_passed.append('Q-029')

    # Q-030: Content aligns with statement
    statement = record.get('statement', '').lower()
    content_lower = detailed_content.lower()

    # Extract key terms from statement
    key_terms = set(re.findall(r'\b\w{4,}\b', statement)) - {'must', 'should', 'will', 'that', 'this', 'with'}
    terms_in_content = sum(1 for term in key_terms if term in content_lower)

    if len(key_terms) == 0 or terms_in_content / max(len(key_terms), 1) >= 0.5:
        score += 4
        rules_passed.append('Q-030')
    else:
        score += 2
        rules_failed.append('Q-030')
        suggestions.append('Detailed content should elaborate on statement terms.')

    return score, QualityDimension(
        dimension='detailed_content',
        score=score,
        max_score=20,
        rules_passed=rules_passed,
        rules_failed=rules_failed,
        suggestions=suggestions
    )
```

---

## Solution 4: Content Summary Generation

### Auto-Generate Token-Efficient Summary

```python
def generate_content_summary(decision: Dict[str, Any]) -> str:
    """
    Generate 1-paragraph summary (~50 words) for token-efficient context.

    Used when:
    - Many decisions needed
    - Token budget limited
    - Quick reference needed
    """
    statement = decision.get('statement', '')
    constraints = decision.get('constraints', [])
    detailed_content = decision.get('detailed_content', '')

    # Extract key points
    key_constraints = [c.get('statement', '')[:50] for c in constraints[:3]]

    # If detailed_content exists, extract key headers
    headers = re.findall(r'^##\s+(.+)$', detailed_content, re.MULTILINE)[:3]

    summary_parts = [
        statement[:100],  # First 100 chars of statement
    ]

    if key_constraints:
        summary_parts.append(f"Key rules: {'; '.join(key_constraints)}")

    if headers:
        summary_parts.append(f"Covers: {', '.join(headers)}")

    return ' '.join(summary_parts)[:300]  # Max 300 chars
```

---

## Implementation Checklist

### Phase 1: Schema Update
- [ ] Add `detailed_content` field to Decision model
- [ ] Add `ContentSection` model
- [ ] Add `SectionType` enum
- [ ] Add `content_summary` field
- [ ] Update database schema
- [ ] Migration script

### Phase 2: Validation Update
- [ ] Update Q-001 to consider `detailed_content` presence
- [ ] Update Q-006 to consider `detailed_content` presence
- [ ] Add Q-026 to Q-030 for detailed content
- [ ] Update quality scoring total (120 → 140)

### Phase 3: Context Injection
- [ ] Update MCP tools with detail_level parameter
- [ ] Implement token budget management
- [ ] Implement automatic content_summary generation
- [ ] Add section-based retrieval

### Phase 4: UI Update
- [ ] Add detailed_content editor (Markdown)
- [ ] Add sections management
- [ ] Add content preview
- [ ] Show content_summary in list view

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LONG CONTENT STRATEGY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   BEFORE:                           AFTER:                                   │
│   ──────                            ─────                                    │
│   • statement: 200 words max        • statement: Executive summary           │
│   • rationale: 500 words max        • rationale: Why (concise)               │
│   • No room for specs               • detailed_content: Full spec (new)      │
│   • Token budget issues             • sections: Structured breakdown         │
│                                     • content_summary: Auto-generated        │
│                                                                              │
│   VALIDATION:                                                                │
│   • Q-001/Q-006: Updated for two-layer model                                │
│   • Q-026-Q-030: NEW detailed content validation                            │
│   • Focus on STRUCTURE, not LENGTH                                          │
│                                                                              │
│   CONTEXT INJECTION:                                                         │
│   • Tier 1 (micro): summary only - 100 tokens                               │
│   • Tier 2 (standard): statement+rationale - 500 tokens                     │
│   • Tier 3 (detailed): full content - 2000+ tokens                          │
│   • Tier 4 (sections): specific sections only                               │
│   • Automatic budget management                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

