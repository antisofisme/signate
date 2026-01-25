# MANTRA-DECISION-001: Immutability Principle

> **Self-Validation**: This decision about MANTRA is recorded IN MANTRA.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `MANTRA-DECISION-001` |
| **group_id** | GROUP-3 |
| **feature_id** | F-09 (Policy & Rules) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | CRITICAL |
| **created_by** | ATLAS_MANTRA Core Team |
| **created_at** | 2025-01-24 |
| **supersedes** | null |

---

## Statement

**Stored decisions MUST NOT be modified or deleted. All modifications are INVALID.**

---

## Rationale

Immutability is the foundation of decision governance because:

1. **Audit Trail Integrity**: If decisions can be modified after creation, the audit trail becomes unreliable. Organizations cannot prove what was decided at a specific point in time.

2. **Accountability**: When decisions are immutable, the person who created/approved the decision remains accountable. Modification would allow shifting blame.

3. **Trust**: Stakeholders trust the system because they know records cannot be tampered with.

4. **Compliance**: Regulatory requirements (SOX, GDPR right-to-explanation) require proof of decisions at specific times. Mutable records fail compliance.

5. **Evolution Clarity**: When decisions cannot be modified, evolution is explicit through `supersedes` chain. This creates clear version history rather than hidden changes.

---

## Constraints

### PROHIBITION
1. **P-001**: Decision records MUST NOT have UPDATE operations
2. **P-002**: Decision records MUST NOT have DELETE operations
3. **P-003**: Database triggers MUST prevent modification attempts
4. **P-004**: API MUST NOT expose modification endpoints

### REQUIREMENT
1. **R-001**: All changes MUST create new decision with `supersedes` link
2. **R-002**: Original decision MUST remain accessible forever
3. **R-003**: Storage layer MUST enforce write-once semantics

### LIMITATION
1. **L-001**: Typo corrections are NOT exempt from immutability
2. **L-002**: Even "administrative" changes require new version

---

## Invariants

These properties are ALWAYS true:

1. `decision.created_at` never changes after creation
2. `decision.statement` never changes after creation
3. `decision.rationale` never changes after creation
4. Every decision has exactly one `created_at` timestamp
5. Decision count only increases, never decreases

---

## Implementation Reference

Per MANTRA-LAW-001 §10 and MANTRA-L1-IMPL-DECISION-STORE-001:

```python
# backend/core/domain/decision.py
@dataclass
class StoredDecision:
    decision: Decision
    stored_at: datetime
    stored_by: str
    _is_immutable: bool = field(default=False)

    def __setattr__(self, name, value):
        if hasattr(self, "_is_immutable") and self._is_immutable:
            raise AttributeError(
                "StoredDecision is immutable per MANTRA-LAW-001 §10. "
                "Modification is INVALID."
            )
        super().__setattr__(name, value)
```

---

## Related Decisions

- MANTRA-DECISION-003: Status Field Removal (consequence of immutability)
- MANTRA-DECISION-004: Supersedes Chain Model (evolution mechanism)

---

## Evolution Path

This decision is foundational and unlikely to change. If organizational needs require modification capability:

1. Create MANTRA-DECISION-001 v2.0.0 with `supersedes: MANTRA-DECISION-001`
2. Document rationale for change
3. Both versions remain in system permanently
