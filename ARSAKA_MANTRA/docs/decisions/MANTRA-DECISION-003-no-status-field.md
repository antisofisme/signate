# MANTRA-DECISION-003: No Status Field

> **Self-Validation**: This decision about MANTRA is recorded IN MANTRA.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `MANTRA-DECISION-003` |
| **group_id** | GROUP-4 |
| **feature_id** | F-13 (Decision Lifecycle) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | HIGH |
| **created_by** | ARSAKA_MANTRA Core Team |
| **created_at** | 2025-01-24 |
| **supersedes** | null |

---

## Statement

**Decision records SHALL NOT have a status field. Lifecycle is expressed through `version` + `supersedes` chain only.**

---

## Rationale

No status field because:

1. **Status is Interpretation**: What does "active" mean? If decision A is superseded by B, is A "deprecated"? What if B only partially supersedes A? Status requires interpretation that varies by context.

2. **Consumer Responsibility**: Different consumers have different interpretations:
   - Legal team: "Which decision was active on March 15?"
   - Engineering: "Which decision applies to service X?"
   - Compliance: "Show me all decisions, regardless of status"

   Each consumer interprets the supersedes chain for their context.

3. **Immutability Conflict**: If decisions are immutable, who changes the status? A status field implies mutation (DRAFT → ACTIVE → DEPRECATED). This violates immutability.

4. **Simplicity**: Without status, the model is simpler:
   - Decision exists or doesn't
   - Decision supersedes another or doesn't
   - No state machine, no transitions, no edge cases

5. **Audit Clarity**: With status, audit becomes complex:
   - "When did status change?"
   - "Who changed it?"
   - "Was the change authorized?"

   Without status, audit is simple: creation events only.

---

## How Lifecycle Works Without Status

```
Traditional (with status):
┌──────────┐    ┌──────────┐    ┌──────────┐
│  DRAFT   │ →  │  ACTIVE  │ →  │DEPRECATED│
└──────────┘    └──────────┘    └──────────┘
    │               │               │
    │  (mutation)   │  (mutation)   │
    └───────────────┴───────────────┘

MANTRA (without status):
┌──────────────┐
│ Decision v1  │ ← exists, no status
└──────────────┘
       │
       │ supersedes
       ▼
┌──────────────┐
│ Decision v2  │ ← exists, no status
└──────────────┘
       │
       │ supersedes
       ▼
┌──────────────┐
│ Decision v3  │ ← exists, no status
└──────────────┘

Consumer interprets:
- "Latest version" = follow supersedes chain to end
- "Active on date X" = find version created before X, not yet superseded by X
- "All versions" = return entire chain
```

---

## Constraints

### PROHIBITION
1. **P-001**: Schema MUST NOT include `status` field
2. **P-002**: API MUST NOT accept `status` parameter
3. **P-003**: UI MUST NOT show editable status dropdown
4. **P-004**: No "archive" or "delete" operations (status by another name)

### REQUIREMENT
1. **R-001**: Lifecycle MUST be expressed via `version` field
2. **R-002**: Evolution MUST be expressed via `supersedes` link
3. **R-003**: Read API MUST return all versions (consumer filters)
4. **R-004**: History endpoint MUST show full supersedes chain

### LIMITATION
1. **L-001**: Consumer MUST implement their own "current version" logic
2. **L-002**: No system-provided "active decisions" filter

---

## Invariants

These properties are ALWAYS true:

1. Decision schema has no `status` field
2. Every decision has exactly one `version` (semantic versioning)
3. Supersedes chain is acyclic (no circular references)
4. Consumer interprets lifecycle, system stores facts

---

## Consumer Interpretation Examples

### Example 1: "What's the current policy on expenses?"

```python
# Consumer logic (not MANTRA logic):
def get_current_decision(group, feature):
    # Get all decisions for this group/feature
    decisions = mantra.get_decisions(group=group, feature=feature)

    # Find the one not superseded by anything
    superseded_ids = {d.supersedes for d in decisions if d.supersedes}
    current = [d for d in decisions if d.id not in superseded_ids]

    return current[0] if current else None
```

### Example 2: "What was active on March 15, 2025?"

```python
def get_decision_at_date(group, feature, target_date):
    decisions = mantra.get_decisions(group=group, feature=feature)

    # Filter to decisions created before target date
    candidates = [d for d in decisions if d.created_at <= target_date]

    # Find the latest one not superseded before target date
    for d in sorted(candidates, key=lambda x: x.created_at, reverse=True):
        superseding = next((s for s in decisions
                          if s.supersedes == d.id
                          and s.created_at <= target_date), None)
        if not superseding:
            return d

    return None
```

---

## Related Decisions

- MANTRA-DECISION-001: Immutability Principle (no status = no mutation needed)
- MANTRA-DECISION-004: Supersedes Chain Model (evolution mechanism)

---

## Common Questions

**Q: How do I "deprecate" a decision?**
A: Create a new decision that supersedes it. The old decision remains, the new one explains the change.

**Q: How do I "draft" a decision before finalizing?**
A: Drafts are not stored in MANTRA. Use external tools (docs, wiki) for drafts. Only store when finalized.

**Q: How do I "delete" a wrong decision?**
A: You cannot delete. Create a superseding decision that corrects the error. The audit trail shows the correction.

**Q: How do I know which decisions are "current"?**
A: Follow the supersedes chain to find decisions not superseded by others. Or use the `/history` endpoint.

---

## Evolution Path

This decision is fundamental to MANTRA's architecture. Changing it would require:

1. Schema migration (adding status field)
2. State machine implementation
3. Mutation semantics definition
4. Audit trail for status changes

If needed, create MANTRA-DECISION-003 v2.0.0 with full architectural impact analysis.
