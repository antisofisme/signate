# MANTRA Self-Recorded Decisions

> **Self-Validation**: MANTRA uses MANTRA to record decisions about MANTRA.

This directory contains decisions about the MANTRA system itself, recorded using the MANTRA framework. This serves as:

1. **Self-validation**: Proves the system works
2. **Template**: Shows how decisions should be recorded
3. **Credibility**: Demonstrates we use what we build

---

## Decision Index

| ID | Group | Feature | Statement |
|----|-------|---------|-----------|
| [MANTRA-DECISION-001](./MANTRA-DECISION-001-immutability-principle.md) | GROUP-3 | F-09 | Stored decisions MUST NOT be modified or deleted |
| [MANTRA-DECISION-002](./MANTRA-DECISION-002-ai-authority-zero.md) | GROUP-3 | F-10 | AI authority in decision-making is ZERO |
| [MANTRA-DECISION-003](./MANTRA-DECISION-003-no-status-field.md) | GROUP-4 | F-13 | Decision records SHALL NOT have a status field |
| [MANTRA-DECISION-004](./MANTRA-DECISION-004-supersedes-chain.md) | GROUP-4 | F-13 | Decision evolution via supersedes links |
| [MANTRA-DECISION-005](./MANTRA-DECISION-005-four-group-taxonomy.md) | GROUP-1 | F-03 | 4 Groups × 4 Features = 16-cell taxonomy |

---

## Decision Distribution

```
GROUP-1 (Intent & Direction): 1 decision
├── F-03: MANTRA-DECISION-005 (Taxonomy)

GROUP-3 (Control & Policy): 2 decisions
├── F-09: MANTRA-DECISION-001 (Immutability)
└── F-10: MANTRA-DECISION-002 (AI Authority)

GROUP-4 (Execution & Evolution): 2 decisions
├── F-13: MANTRA-DECISION-003 (No Status)
└── F-13: MANTRA-DECISION-004 (Supersedes Chain)
```

---

## Relationships

```
MANTRA-DECISION-001 (Immutability)
    │
    ├── enables → MANTRA-DECISION-003 (No Status Field)
    │             "Because decisions are immutable, no status mutation needed"
    │
    └── enables → MANTRA-DECISION-004 (Supersedes Chain)
                  "Evolution via new records, not modification"

MANTRA-DECISION-002 (AI Authority Zero)
    │
    └── reinforces → MANTRA-DECISION-001
                     "AI cannot modify because it has zero authority"

MANTRA-DECISION-005 (Taxonomy)
    │
    └── structures → All other decisions
                     "Provides GROUP/FEATURE classification"
```

---

## How to Use These as Templates

Each decision document shows:

1. **Decision Record Table**: Metadata (group, feature, version, etc.)
2. **Statement**: Clear, one-sentence decision
3. **Rationale**: WHY this decision (required, cannot be empty)
4. **Constraints**: What MUST/MUST NOT happen
5. **Invariants**: What is ALWAYS true
6. **Implementation Reference**: How it's implemented in code
7. **Related Decisions**: Links to other decisions
8. **Evolution Path**: How this decision might change

When recording your own decisions, use this structure.

---

## Note on Self-Reference

These decisions were initially identified in `MANTRA-L1-DOGFOODING-ANALYSIS-001` as "decisions made but not recorded."

By recording them formally, we:
1. Fix the credibility gap
2. Demonstrate the system works
3. Provide real examples for users
4. Prove we believe in our own product
