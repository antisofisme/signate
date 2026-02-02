# MANTRA-LAW-001: Decision Matrix Canon

**TYPE**: Constitutional Law
**VERSION**: 1.1.0
**STATUS**: LOCKED
**EFFECTIVE**: 2025-01-24
**AMENDED**: 2025-01-24
**AUTHORITY**: Human Decision Only

---

## §1. Jurisdiction

This law governs all decisions within systems bound by the ARSAKA_MANTRA framework.

Compliance is REQUIRED. Non-compliance renders decisions INVALID.

---

## §2. Decision Matrix Definition

### §2.1 Binding Nature

The Decision Matrix is the sole authoritative structure for organizational decisions.

Any decision not conforming to this structure is INVALID.

### §2.2 Composition

The Decision Matrix consists of:
- Exactly four (4) Decision Groups.
- Exactly sixteen (16) Decision Features.
- No additional groups or features.

Any extension, reduction, or modification to this composition is FORBIDDEN without explicit human revision of this law.

### §2.3 Invalidity Conditions

A decision is INVALID if:
- It does not belong to exactly one (1) Decision Group.
- It does not relate to exactly one (1) Decision Feature.
- It was created, approved, or finalized by non-human authority.
- It lacks a human-authored statement.
- It lacks a human-authored rationale.
- It violates any provision of this law.

---

## §3. The Four Decision Groups

### §3.1 General Provisions

Each Decision Group has exclusive scope. Decisions MUST NOT span multiple groups.

A decision assigned to an incorrect group is INVALID.

A decision that cannot be assigned to exactly one group is INVALID.

### §3.2 Group 1: Intent & Direction

**Identifier**: GROUP-1
**Scope**: WHY / WHAT
**Exclusive Domain**: Decisions concerning purpose, objectives, and directional constraints.

**Features**:
| ID | Feature |
|----|---------|
| F-01 | Vision & Outcome |
| F-02 | Problem Statement |
| F-03 | Scope & Non-Goals |
| F-04 | Principles & Values |

**Violations**:
- Decisions concerning system structure MUST NOT appear in this group.
- Decisions concerning access control MUST NOT appear in this group.
- Decisions concerning change management MUST NOT appear in this group.

### §3.3 Group 2: Architecture & Boundaries

**Identifier**: GROUP-2
**Scope**: HOW / WHERE
**Exclusive Domain**: Decisions concerning system structure, ownership, and integration boundaries.

**Features**:
| ID | Feature |
|----|---------|
| F-05 | Domain & Bounded Context |
| F-06 | Service & Module Boundary |
| F-07 | Data Ownership & Sovereignty |
| F-08 | Integration & Contract Model |

**Violations**:
- Decisions concerning organizational purpose MUST NOT appear in this group.
- Decisions concerning access control MUST NOT appear in this group.
- Decisions concerning change management MUST NOT appear in this group.

### §3.4 Group 3: Control, Policy & Risk

**Identifier**: GROUP-3
**Scope**: CAN / MUST NOT
**Exclusive Domain**: Decisions concerning permissions, prohibitions, compliance posture, and risk tolerance.

**Features**:
| ID | Feature |
|----|---------|
| F-09 | Policy & Rules |
| F-10 | Approval & Authority Model |
| F-11 | Security & Compliance Posture |
| F-12 | Risk, Blast Radius & Failure Tolerance |

**Violations**:
- Decisions concerning organizational purpose MUST NOT appear in this group.
- Decisions concerning system structure MUST NOT appear in this group.
- Decisions concerning change management MUST NOT appear in this group.

### §3.5 Group 4: Execution Invariants & Evolution

**Identifier**: GROUP-4
**Scope**: CHANGE SAFELY
**Exclusive Domain**: Decisions concerning lifecycle, reversibility, environment rules, and drift prevention.

**Features**:
| ID | Feature |
|----|---------|
| F-13 | Decision Lifecycle |
| F-14 | Reversibility & Exit Strategy |
| F-15 | Environment & Promotion Rules |
| F-16 | Anti-Drift & Consistency Rules |

**Violations**:
- Decisions concerning organizational purpose MUST NOT appear in this group.
- Decisions concerning system structure MUST NOT appear in this group.
- Decisions concerning access control MUST NOT appear in this group.

---

## §4. Decision vs Feature

### §4.1 Definitions

**Decision**: A binding determination that establishes constraints, invariants, or boundaries.

**Feature**: A consequence or expression derived from a decision.

### §4.2 Hierarchy

Decisions govern Features. Features do not govern Decisions.

This hierarchy is absolute and non-negotiable.

### §4.3 Boundary Enforcement

Any Feature that alters, removes, or contradicts a constraint is automatically a Decision.

Any Feature that alters, removes, or contradicts an invariant is automatically a Decision.

Such alteration is INVALID unless recorded as a Decision through proper human authorization.

### §4.4 Feature Limitations

Features MUST NOT:
- Serve as source of truth.
- Override Decisions.
- Create new constraints.
- Modify existing invariants.

Violation of these limitations renders the Feature INVALID.

---

## §5. Sovereignty

### §5.1 Organization Sovereignty

The organization is the sole decision sovereign.

Applications are consumers. Applications are not owners.

### §5.2 Sovereignty Provisions

No application may create decisions on behalf of an organization without explicit human authorization.

No application may modify decisions without explicit human authorization.

No cross-organization decision is valid.

No implicit decision is valid.

### §5.3 Consumer Constraints

Consumers MUST NOT:
- Create decisions.
- Modify decisions.
- Approve decisions.
- Interpret decisions beyond literal meaning.

Violation renders the consumer action INVALID.

---

## §6. AI Authority

### §6.1 Authority Level

AI authority is ZERO.

AI has no decision-making power.

AI has no approval power.

AI has no rejection power.

### §6.2 Permitted AI Actions

AI MAY:
- Read decision records.
- Detect potential conflicts.
- Flag potential gaps.
- Generate advisory warnings.
- Produce analysis for human review.

### §6.3 Prohibited AI Actions

AI MUST NOT:
- Create decision identifiers.
- Assign decisions to groups or features.
- Change decision status.
- Approve or reject decisions.
- Finalize any decision.
- Imply approval through language.
- Override human determinations.

### §6.4 AI Output Disposition

Any AI output that contradicts this law MUST be discarded.

Any AI output that implies decision authority MUST be discarded.

Any AI output that finalizes a decision MUST be discarded.

Human review of AI output does not transfer authority to AI.

---

## §7. Failure & Misuse Modes

### §7.1 Misuse

Misuse occurs when:
- A decision is assigned to an incorrect group.
- A decision is assigned to an incorrect feature.
- A feature is treated as a decision source.
- AI output is treated as authoritative.
- Consumer actions modify decision meaning.

Consequence: INVALID.

### §7.2 Drift

Drift occurs when:
- Decision meaning changes without versioned record.
- Multiple interpretations of same decision exist.
- Consumers hold different versions of same decision.
- Silent modifications accumulate over time.

Consequence: INVALID. Affected decisions MUST be reconciled through human action.

### §7.3 Silent Reinterpretation

Silent reinterpretation occurs when:
- Decision meaning is altered without explicit revision.
- Constraints are relaxed without recorded decision.
- Invariants are modified without recorded decision.
- Scope is expanded or contracted without recorded decision.

Consequence: REJECTED. The original decision remains in force.

### §7.4 Consequence Enforcement

INVALID: The decision or action has no legal effect within the system.

REJECTED: The attempted change is nullified. Prior state persists.

DISCARDED: The output is removed from consideration entirely.

---

## §8. Amendment

### §8.1 Amendment Authority

Only explicit human decision may amend this law.

### §8.2 Amendment Constraints

Amendments MUST NOT:
- Add Decision Groups beyond four (4).
- Remove Decision Groups below four (4).
- Add Decision Features beyond sixteen (16).
- Remove Decision Features below sixteen (16).
- Transfer any authority to AI.
- Transfer any authority to applications.

### §8.3 Amendment Process

Amendments require:
- Human authorship.
- Explicit statement of change.
- Recorded rationale.
- Version increment.

---

## §9. Effective Date

This law is effective immediately upon publication.

All prior interpretations inconsistent with this law are superseded.

---

## §10. Layer 0 Immutability and Boundary Rule

### §10.1 Constitutional Status

All Layer 0 documents are constitutional and immutable.

### §10.2 Immutability Provision

Layer 0 documents MUST NOT be modified, reinterpreted, or overridden by any lower layer.

Modification of a Layer 0 document requires a new document version that explicitly supersedes the prior version, authored by human authority per §8.

### §10.3 Reference Permission

Higher layers MAY reference Layer 0 documents.

### §10.4 Boundary Prohibitions

Higher layers MUST NOT:
- Redefine authority established in Layer 0.
- Alter decision validity rules established in Layer 0.
- Expand AI permissions beyond those stated in §6.
- Introduce alternative interpretations of Layer 0 provisions.

### §10.5 Anti-Shadowing Rule

No document in any layer may create definitions, rules, or provisions that shadow, override, or contradict Layer 0 documents.

Any such attempt constitutes shadow law and is INVALID.

### §10.6 Violation Consequence

Any attempt to violate §10.2, §10.4, or §10.5 is INVALID per this law.

The violating provision has no legal effect within the system.

---

## Amendment History

| Version | Date | Change | Rationale |
|---------|------|--------|-----------|
| 1.0.0 | 2025-01-24 | Initial publication | Establish Decision Matrix Canon |
| 1.1.0 | 2025-01-24 | Added §10 (Immutability and Boundary Rule) | Close structural gap: explicit lock clause, anti-shadowing rule, boundary prohibitions for higher layers |

---

**END OF LAW**
