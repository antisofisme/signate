# MANTRA-WRITING-GUIDELINES: Content Length & Style Standards

**Document Type**: Writing Standard
**Version**: 1.0.0
**Status**: ACTIVE
**Purpose**: Prevent verbose writing, ensure consistency across decisions

---

## Executive Summary

This document defines **writing standards** for MANTRA decision fields to:
1. **Prevent verbose writing** - 2 paragraphs sufficient, not 5
2. **Ensure consistency** - Same structure across all decisions
3. **Enable machine processing** - Predictable format for AI/search
4. **Improve readability** - Dense, focused content

---

## Core Principle: Say More with Less

| Bad (Verbose) | Good (Concise) |
|---------------|----------------|
| "After extensive discussions and many meetings over the past few weeks, the team has collectively agreed and decided that moving forward we should probably consider using..." | "We use feature folders for React components." |
| "It is strongly recommended that developers should probably consider..." | "MUST use /v{n}/ prefix for all API endpoints" |
| "Generally speaking, in most cases, API responses should ideally contain some form of..." | "All API responses include request_id header" |

---

## Field Length Limits

### Core Fields (ENFORCED)

| Field | Min | Max | Word Target | Purpose |
|-------|-----|-----|-------------|---------|
| `statement` | 50 chars | 1500 chars | 10-200 words | WHAT we decide |
| `rationale` | 100 chars | 4000 chars | 20-500 words | WHY we decide |
| `constraint` | 20 chars | 500 chars | 10-60 words | ONE enforceable rule |
| `invariant` | 10 chars | 300 chars | 5-40 words | ONE truth assertion |

### Summary Fields (ENFORCED)

| Field | Max | Word Target | Purpose |
|-------|-----|-------------|---------|
| `headline` | 150 chars | 15-20 words | One-liner |
| `abstract` | 500 chars | 50-80 words | WHAT + WHY |
| `executive_summary` | 1500 chars | 100-200 words | For stakeholders |
| `for_developers` | 800 chars | ~100 words | Technical focus |
| `for_architects` | 800 chars | ~100 words | Design focus |
| `for_managers` | 800 chars | ~100 words | Business focus |

### List Limits (ENFORCED)

| Field | Min | Max | Purpose |
|-------|-----|-----|---------|
| `key_points` | 3 | 7 | Main takeaways |
| `tags` | - | 10 | Classification |
| `tech_stack` | - | 15 | Technologies |
| `invariants` | - | 20 | Truth assertions |
| `constraints` | - | 30 | Enforceable rules |

---

## Writing Styles by Field Type

### 1. Statement (DECLARATIVE)

**Structure**: `[SUBJECT] + [ACTION/DECISION] + [SCOPE/CONTEXT]`

**Style**: Direct, present tense, no hedging

**Example**:
```
We use feature folders for React components to improve maintainability.
Each feature (auth, dashboard, billing) has its own folder containing
components, hooks, utils, and tests. Shared components go in /shared.
This applies to all frontend code in the monorepo.
```

**Anti-patterns to AVOID**:
- ❌ "After extensive discussions..."
- ❌ "We have decided to probably..."
- ❌ "It is recommended that we might consider..."
- ❌ "Moving forward we should..."
- ❌ "The team has collectively agreed..."

**Quality signals**:
- ✅ Direct verb: 'use', 'require', 'implement'
- ✅ Clear scope: 'all frontend', 'BE services', 'this module'
- ✅ Specific: names, paths, versions
- ✅ No hedging: avoid 'might', 'probably', 'consider'

---

### 2. Rationale (REASONING)

**Structure**: `[PROBLEM/CONTEXT] → [OPTIONS CONSIDERED] → [WHY THIS CHOICE] → [EXPECTED BENEFIT]`

**Style**: Logical flow, bullet points welcome

**Example**:
```
Feature folders improve maintainability as codebase grows beyond 50+ components.

Alternative approaches considered:
1. Type-based folders (/components, /hooks) - becomes hard to navigate at scale
2. Flat structure - too many files in one folder

Feature folders chosen because:
- Related code stays together (easier to understand feature)
- Deletion is simple (remove one folder)
- Team members can own features without conflicts

Expected: 30% faster onboarding, reduced cross-feature dependencies.
```

**Anti-patterns to AVOID**:
- ❌ "So, the rationale is multifaceted..."
- ❌ "It's worth mentioning that..."
- ❌ "We had numerous discussions..."
- ❌ "Various opinions and perspectives..."
- ❌ "Seems to be the most suitable..."

**Quality signals**:
- ✅ States the problem first
- ✅ Lists alternatives considered
- ✅ Explains WHY chosen (not just WHAT)
- ✅ Quantifies benefits when possible
- ✅ Uses bullet points for clarity

---

### 3. Constraint (IMPERATIVE)

**Structure**: `[MUST/MUST NOT/SHOULD] + [ACTION] + [CONDITION (optional)]`

**Style**: Command form, one rule per constraint

**Example**:
```
MUST use /v{n}/ prefix for all API endpoints (e.g., /v1/users, /v2/products)
```

**Anti-patterns to AVOID**:
- ❌ "It is recommended that..."
- ❌ "Developers should consider..."
- ❌ "Generally considered a best practice..."
- ❌ "This is because..."

**Quality signals**:
- ✅ Starts with MUST, MUST NOT, SHOULD, or SHALL
- ✅ One enforceable rule per constraint
- ✅ Includes example when helpful
- ✅ Measurable/verifiable

---

### 4. Invariant (ASSERTIVE)

**Structure**: `[SUBJECT] + [IS ALWAYS/NEVER] + [CONDITION]`

**Style**: Absolute truth, no exceptions

**Example**:
```
All API responses include request_id header for tracing
```

**Anti-patterns to AVOID**:
- ❌ "Generally speaking..."
- ❌ "In most cases..."
- ❌ "Should ideally..."
- ❌ "Some form of..."

**Quality signals**:
- ✅ States absolute truth
- ✅ No hedging (always, never, every)
- ✅ Testable assertion
- ✅ One invariant per statement

---

### 5. Headline (SUMMARY)

**Structure**: `[CORE DECISION IN ONE SENTENCE]`

**Style**: Active voice, no fluff

**Example**:
```
We use feature folders for React components to improve maintainability
```

**Anti-patterns to AVOID**:
- ❌ "This document describes..."
- ❌ "We have decided to..."
- ❌ "The purpose of this is..."

---

### 6. Abstract (SUMMARY)

**Structure**: `[WHAT] + [WHY] in 2-3 sentences`

**Style**: Dense information, self-contained

**Example**:
```
Feature folders group React components by feature (/auth, /dashboard) instead of type.
This improves maintainability as the codebase grows and enables team ownership of features.
Applies to all frontend code in the monorepo.
```

---

## Validation at Runtime

The schema enforces these limits at validation time:

```python
from schema_v3_enhanced import (
    validate_content_length,
    check_anti_patterns,
    get_writing_tips,
)

# Validate length (raises ValueError if exceeded)
validate_content_length("statement", my_statement)

# Check for verbose patterns (returns list of detected patterns)
anti_patterns = check_anti_patterns("statement", my_statement)
if anti_patterns:
    print(f"Warning: Verbose patterns detected: {anti_patterns}")

# Get writing tips for a field
tips = get_writing_tips("rationale")
print(tips["structure"])  # Expected structure
print(tips["good_example"])  # Good example
print(tips["avoid"])  # Anti-patterns to avoid
```

---

## Why This Matters

### For Writers
- Clear expectations = faster writing
- No guessing about length
- Templates for consistency

### For Readers
- Predictable format = faster scanning
- Dense content = less wasted time
- Quality signals = trustworthy content

### For AI/Search
- Structured format = better embeddings
- Consistent length = balanced token usage
- Predictable patterns = higher retrieval accuracy

---

## Summary Table

| If you're writing... | Use style... | Keep it under... | Structure as... |
|---------------------|--------------|------------------|-----------------|
| Statement | Declarative | 200 words | WHAT + WHERE |
| Rationale | Reasoning | 500 words | PROBLEM → OPTIONS → CHOICE → BENEFIT |
| Constraint | Imperative | 60 words | MUST/SHOULD + ACTION |
| Invariant | Assertive | 40 words | X IS ALWAYS Y |
| Headline | Summary | 20 words | ONE SENTENCE |
| Abstract | Summary | 80 words | WHAT + WHY |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-01-29 | Initial release with length limits and writing styles |

---

**END OF WRITING GUIDELINES**
