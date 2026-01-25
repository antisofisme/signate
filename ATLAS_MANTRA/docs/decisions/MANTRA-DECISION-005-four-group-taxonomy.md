# MANTRA-DECISION-005: Four-Group Taxonomy

> **Self-Validation**: This decision about MANTRA is recorded IN MANTRA.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `MANTRA-DECISION-005` |
| **group_id** | GROUP-1 |
| **feature_id** | F-03 (Scope & Non-Goals) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | CRITICAL |
| **created_by** | ATLAS_MANTRA Core Team |
| **created_at** | 2025-01-24 |
| **supersedes** | null |

---

## Statement

**MANTRA organizes decisions into exactly 4 Groups with 4 Features each, creating a 16-cell taxonomy. This structure is fixed and cannot be extended without constitutional amendment.**

---

## Rationale

Fixed 4×4 taxonomy because:

1. **Completeness**: The 4 groups cover all decision dimensions:
   - WHY/WHAT (intent)
   - HOW/WHERE (architecture)
   - CAN/MUST NOT (control)
   - CHANGE (evolution)

2. **Mutual Exclusivity**: Each decision belongs to exactly ONE group. No overlap, no ambiguity about categorization.

3. **Simplicity**: 16 cells is manageable. More would create decision paralysis. Fewer would force artificial grouping.

4. **Consistency**: Fixed taxonomy means all organizations using MANTRA speak the same language. Decision "GROUP-2/F-06" means the same thing everywhere.

5. **Governance**: Extending the taxonomy requires constitutional amendment, preventing scope creep and maintaining discipline.

---

## The Four Groups

### GROUP-1: Intent & Direction (WHY/WHAT)

**Question answered**: "Why are we doing this? What are we trying to achieve?"

| Feature | Focus |
|---------|-------|
| F-01: Vision & Outcome | Long-term goals, success criteria |
| F-02: Problem Statement | What problem are we solving? |
| F-03: Scope & Non-Goals | What's in/out of scope? |
| F-04: Principles & Values | Guiding principles, trade-offs |

**Example decisions**:
- "Our product will focus on SMB market" (F-01)
- "We solve the inventory tracking problem" (F-02)
- "Real-time sync is out of scope for v1" (F-03)
- "We prioritize simplicity over features" (F-04)

---

### GROUP-2: Architecture & Boundaries (HOW/WHERE)

**Question answered**: "How will we build it? Where do things belong?"

| Feature | Focus |
|---------|-------|
| F-05: Domain & Bounded Context | Business domain boundaries |
| F-06: Service & Module Boundary | Technical component boundaries |
| F-07: Data Ownership & Sovereignty | Who owns what data? |
| F-08: Integration & Contract Model | How systems communicate |

**Example decisions**:
- "Payment is a separate bounded context" (F-05)
- "Auth service is standalone microservice" (F-06)
- "Customer data owned by CRM domain" (F-07)
- "All APIs use REST with JSON" (F-08)

---

### GROUP-3: Control, Policy & Risk (CAN/MUST NOT)

**Question answered**: "What's allowed? What's forbidden? What's the risk?"

| Feature | Focus |
|---------|-------|
| F-09: Policy & Rules | Business rules, constraints |
| F-10: Approval & Authority Model | Who can approve what? |
| F-11: Security & Compliance Posture | Security requirements |
| F-12: Risk, Blast Radius & Failure Tolerance | Risk assessment |

**Example decisions**:
- "Expenses over $1000 require approval" (F-09)
- "Only C-level can approve vendor contracts" (F-10)
- "All PII must be encrypted at rest" (F-11)
- "Payment failures must not block checkout" (F-12)

---

### GROUP-4: Execution & Evolution (CHANGE SAFELY)

**Question answered**: "How do we change safely? How do things evolve?"

| Feature | Focus |
|---------|-------|
| F-13: Decision Lifecycle | How decisions evolve |
| F-14: Reversibility & Exit Strategy | How to undo/exit |
| F-15: Environment & Promotion Rules | Dev→Staging→Prod |
| F-16: Anti-Drift & Consistency Rules | Preventing divergence |

**Example decisions**:
- "Decisions evolve via supersedes chain" (F-13)
- "All vendor contracts must have exit clause" (F-14)
- "No direct commits to production" (F-15)
- "Config drift checked weekly" (F-16)

---

## Constraints

### PROHIBITION
1. **P-001**: Groups MUST NOT be added beyond GROUP-1 through GROUP-4
2. **P-002**: Features MUST NOT be added beyond F-01 through F-16
3. **P-003**: A decision MUST NOT span multiple groups
4. **P-004**: Schema MUST NOT accept group_id outside defined set

### REQUIREMENT
1. **R-001**: Every decision MUST have exactly one group_id
2. **R-002**: Every decision MUST have exactly one feature_id
3. **R-003**: Feature MUST belong to correct group (F-01 to F-04 = GROUP-1, etc.)
4. **R-004**: Validation MUST reject mismatched group/feature combinations

### LIMITATION
1. **L-001**: "Miscellaneous" or "Other" category does not exist
2. **L-002**: If decision doesn't fit, reconsider decision scope

---

## Invariants

These properties are ALWAYS true:

1. Exactly 4 groups exist: GROUP-1, GROUP-2, GROUP-3, GROUP-4
2. Exactly 16 features exist: F-01 through F-16
3. Each feature belongs to exactly one group
4. Group/Feature relationship is immutable

---

## Feature-Group Mapping

```
GROUP-1 (Intent)      GROUP-2 (Architecture)   GROUP-3 (Control)       GROUP-4 (Evolution)
├── F-01 Vision       ├── F-05 Domain          ├── F-09 Policy         ├── F-13 Lifecycle
├── F-02 Problem      ├── F-06 Service         ├── F-10 Authority      ├── F-14 Reversibility
├── F-03 Scope        ├── F-07 Data            ├── F-11 Security       ├── F-15 Environment
└── F-04 Principles   └── F-08 Integration     └── F-12 Risk           └── F-16 Anti-Drift
```

---

## Implementation Reference

```python
# backend/core/domain/schema.py

class GroupId(str, Enum):
    GROUP_1 = "GROUP-1"  # Intent & Direction
    GROUP_2 = "GROUP-2"  # Architecture & Boundaries
    GROUP_3 = "GROUP-3"  # Control, Policy & Risk
    GROUP_4 = "GROUP-4"  # Execution & Evolution

class FeatureId(str, Enum):
    # GROUP-1 Features
    F_01 = "F-01"  # Vision & Outcome
    F_02 = "F-02"  # Problem Statement
    F_03 = "F-03"  # Scope & Non-Goals
    F_04 = "F-04"  # Principles & Values
    # GROUP-2 Features
    F_05 = "F-05"  # Domain & Bounded Context
    F_06 = "F-06"  # Service & Module Boundary
    F_07 = "F-07"  # Data Ownership
    F_08 = "F-08"  # Integration & Contract
    # GROUP-3 Features
    F_09 = "F-09"  # Policy & Rules
    F_10 = "F-10"  # Approval & Authority
    F_11 = "F-11"  # Security & Compliance
    F_12 = "F-12"  # Risk & Blast Radius
    # GROUP-4 Features
    F_13 = "F-13"  # Decision Lifecycle
    F_14 = "F-14"  # Reversibility & Exit
    F_15 = "F-15"  # Environment & Promotion
    F_16 = "F-16"  # Anti-Drift & Consistency

# Validation
GROUP_FEATURE_MAP = {
    GroupId.GROUP_1: [FeatureId.F_01, FeatureId.F_02, FeatureId.F_03, FeatureId.F_04],
    GroupId.GROUP_2: [FeatureId.F_05, FeatureId.F_06, FeatureId.F_07, FeatureId.F_08],
    GroupId.GROUP_3: [FeatureId.F_09, FeatureId.F_10, FeatureId.F_11, FeatureId.F_12],
    GroupId.GROUP_4: [FeatureId.F_13, FeatureId.F_14, FeatureId.F_15, FeatureId.F_16],
}
```

---

## Related Decisions

- MANTRA-DECISION-003: No Status Field (lifecycle is GROUP-4/F-13 concern)
- MANTRA-DECISION-004: Supersedes Chain (evolution is GROUP-4 concern)

---

## Common Questions

**Q: What if my decision doesn't fit any feature?**
A: The decision may be too broad. Split into multiple decisions, each fitting one feature.

**Q: Can I create a GROUP-5?**
A: No. This requires constitutional amendment to Layer 0. The 4-group structure is intentionally fixed.

**Q: What about cross-cutting concerns?**
A: Use `related_decisions` to link decisions across groups. Each decision still belongs to one group.

**Q: Why 4 groups, not 3 or 5?**
A: 4 groups map to fundamental decision dimensions: Intent, Structure, Control, Change. This is derived from enterprise architecture frameworks.

---

## Evolution Path

The 4-group structure is constitutional (Layer 0). To change:

1. Propose amendment to MANTRA-LAW-001
2. Document rationale for expansion/contraction
3. Assess impact on existing decisions
4. Requires human approval at constitutional level

This is intentionally difficult. Taxonomy stability enables cross-organization consistency.
