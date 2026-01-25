# MANTRA-DECISION-004: Supersedes Chain Model

> **Self-Validation**: This decision about MANTRA is recorded IN MANTRA.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `MANTRA-DECISION-004` |
| **group_id** | GROUP-4 |
| **feature_id** | F-13 (Decision Lifecycle) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | HIGH |
| **created_by** | ATLAS_MANTRA Core Team |
| **created_at** | 2025-01-24 |
| **supersedes** | null |

---

## Statement

**Decision evolution is expressed through `supersedes` links forming an immutable chain. Each decision may supersede at most one prior decision.**

---

## Rationale

Supersedes chain because:

1. **Explicit Evolution**: When decision B supersedes A, the relationship is explicit. No guessing about "which version replaced which."

2. **Preserved Context**: Both A and B remain in the system. You can see what changed and why (B's rationale explains the evolution).

3. **Immutability Compatible**: No need to modify A when B is created. A stays exactly as it was. B just links to A.

4. **Audit Trail**: The chain IS the history. No separate "change log" needed.

5. **Branching Support**: Decision A can be superseded by B (for context X) and C (for context Y). Multiple evolution paths are possible.

---

## Chain Structure

```
Single Chain (most common):
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Decision A  │ ←── │ Decision B  │ ←── │ Decision C  │
│ v1.0.0      │     │ v1.1.0      │     │ v2.0.0      │
│ supersedes: │     │ supersedes: │     │ supersedes: │
│ null        │     │ A           │     │ B           │
└─────────────┘     └─────────────┘     └─────────────┘

Reading: "C supersedes B supersedes A"
Current: C (not superseded by anything)
History: A → B → C


Branching Chain (context-specific evolution):
                    ┌─────────────┐
              ┌──── │ Decision B  │  (for web platform)
              │     │ supersedes: │
              │     │ A           │
┌─────────────┐     └─────────────┘
│ Decision A  │
│ supersedes: │
│ null        │     ┌─────────────┐
└─────────────┘     │ Decision C  │  (for mobile platform)
              └──── │ supersedes: │
                    │ A           │
                    └─────────────┘

Reading: "Both B and C supersede A for different contexts"
Current: Depends on context (web → B, mobile → C)
```

---

## Constraints

### PROHIBITION
1. **P-001**: A decision MUST NOT supersede itself
2. **P-002**: Circular supersedes chains MUST NOT exist (A→B→C→A)
3. **P-003**: `supersedes` field MUST NOT be modified after creation

### REQUIREMENT
1. **R-001**: `supersedes` MUST be null OR valid existing decision_id
2. **R-002**: Referenced decision MUST exist in the system
3. **R-003**: API MUST validate supersedes reference on creation
4. **R-004**: History endpoint MUST traverse full chain

### LIMITATION
1. **L-001**: Only ONE direct supersedes link per decision (not multiple)
2. **L-002**: Use `related_decisions` for non-supersedes relationships

---

## Invariants

These properties are ALWAYS true:

1. Supersedes chain is acyclic (directed acyclic graph)
2. Supersedes link is immutable once set
3. Chain traversal always terminates (no infinite loops)
4. Every decision has exactly 0 or 1 supersedes link

---

## Implementation Reference

```python
# Schema
class Decision(BaseModel):
    decision_id: str
    version: str                    # Semantic version
    supersedes: Optional[str]       # decision_id or null
    related_decisions: List[str]    # For non-supersedes relationships

# Validation
def validate_supersedes(decision: Decision, repository: Repository):
    if decision.supersedes is None:
        return True  # First in chain, OK

    # Check referenced decision exists
    referenced = repository.find_by_id(decision.supersedes)
    if referenced is None:
        raise ValidationError(f"Supersedes target not found: {decision.supersedes}")

    # Check no circular reference
    if would_create_cycle(decision, repository):
        raise ValidationError("Circular supersedes chain detected")

    return True
```

---

## Version Numbering Convention

While not enforced, recommended versioning:

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Clarification (no semantic change) | PATCH | 1.0.0 → 1.0.1 |
| Refinement (narrower/broader scope) | MINOR | 1.0.0 → 1.1.0 |
| Replacement (different approach) | MAJOR | 1.0.0 → 2.0.0 |

```
Example chain:
v1.0.0: "All expenses require approval"
v1.0.1: "All expenses require approval" (typo fix in rationale)
v1.1.0: "Expenses over $100 require approval" (refinement)
v2.0.0: "Expenses use automated rules engine" (replacement)
```

---

## Related Decisions

- MANTRA-DECISION-001: Immutability Principle (supersedes preserves immutability)
- MANTRA-DECISION-003: No Status Field (supersedes replaces status)

---

## API Usage

### Creating a Superseding Decision

```bash
POST /api/v1/decisions
{
  "decision": {
    "group_id": "GROUP-3",
    "feature_id": "F-09",
    "statement": "Expenses over $500 require manager approval",
    "rationale": "Threshold increased from $100 to reduce approval bottleneck",
    "version": "1.2.0",
    "supersedes": "dec-001-original-id",
    ...
  },
  "stored_by": "john.smith"
}
```

### Getting Version History

```bash
GET /api/v1/decisions/{id}/history

Response:
{
  "decision_id": "dec-003",
  "chain": [
    { "decision_id": "dec-001", "version": "1.0.0", "supersedes": null },
    { "decision_id": "dec-002", "version": "1.1.0", "supersedes": "dec-001" },
    { "decision_id": "dec-003", "version": "1.2.0", "supersedes": "dec-002" }
  ],
  "total_versions": 3
}
```

---

## Common Questions

**Q: Can decision supersede multiple decisions?**
A: No. Use `supersedes` for single parent, `related_decisions` for others.

**Q: Can multiple decisions supersede the same decision?**
A: Yes. This creates a branch (see diagram above).

**Q: How do I merge branches?**
A: Create new decision that supersedes one branch, with `related_decisions` linking to the other.

**Q: What if supersedes target is deleted?**
A: Decisions cannot be deleted (MANTRA-DECISION-001). Target always exists.

---

## Evolution Path

This model is core to MANTRA. Changes would require:

1. Schema changes to supersedes field
2. Migration of existing chains
3. API compatibility layer

If needed, create MANTRA-DECISION-004 v2.0.0 with migration strategy.
