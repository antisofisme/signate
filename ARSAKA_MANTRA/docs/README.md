# ARSAKA_MANTRA Documentation

**TYPE**: Law and Specification Repository
**STATUS**: Active
**AUTHORITY**: Human Decision Only

> **Easy to leave, hard to want to leave.**

---

## Quick Start

New to MANTRA? Start here:

| Document | Purpose |
|----------|---------|
| [VALUE-001: Why MANTRA?](./value/VALUE-001-why-mantra.md) | Understand the problem MANTRA solves |
| [GUIDE-001: Getting Started](./guides/GUIDE-001-getting-started.md) | Record your first decision in 5 minutes |
| [Examples](./examples/README.md) | Real-world decision templates |
| [Self-Recorded Decisions](./decisions/README.md) | How MANTRA uses MANTRA |

---

## Documentation Structure

```
docs/
├── README.md                 ← This file (start here)
│
├── value/                    ← WHY use MANTRA
│   └── VALUE-001-why-mantra.md
│
├── guides/                   ← HOW to use MANTRA
│   └── GUIDE-001-getting-started.md
│
├── examples/                 ← TEMPLATE decisions
│   ├── README.md
│   ├── EXAMPLE-G1-001-product-vision.md
│   ├── EXAMPLE-G1-002-problem-scope.md
│   ├── EXAMPLE-G2-001-service-boundary.md
│   ├── EXAMPLE-G2-002-data-ownership.md
│   ├── EXAMPLE-G3-001-access-control.md
│   ├── EXAMPLE-G3-002-approval-authority.md
│   ├── EXAMPLE-G4-001-api-versioning.md
│   └── EXAMPLE-G4-002-deprecation-policy.md
│
├── decisions/                ← MANTRA's own decisions (self-validation)
│   ├── README.md
│   ├── MANTRA-DECISION-001-immutability-principle.md
│   ├── MANTRA-DECISION-002-ai-authority-zero.md
│   ├── MANTRA-DECISION-003-no-status-field.md
│   ├── MANTRA-DECISION-004-supersedes-chain.md
│   └── MANTRA-DECISION-005-four-group-taxonomy.md
│
└── layer-*/                  ← Constitutional & Technical (see below)
```

---

## User Documentation

### Value Proposition

| Document | Summary |
|----------|---------|
| [VALUE-001](./value/VALUE-001-why-mantra.md) | Why MANTRA exists, what problem it solves, easy to leave philosophy |

### Guides

| Document | Summary |
|----------|---------|
| [GUIDE-001](./guides/GUIDE-001-getting-started.md) | 5-minute quick start, record your first decision |
| [GUIDE-002](./guides/GUIDE-002-api-reference.md) | Complete API reference with all endpoints |

### Examples (Templates)

| Group | Examples |
|-------|----------|
| INT (Intent) | [Product Vision](./examples/EXAMPLE-G1-001-product-vision.md), [Problem Scope](./examples/EXAMPLE-G1-002-problem-scope.md) |
| ARCH (Architecture) | [Service Boundary](./examples/EXAMPLE-G2-001-service-boundary.md), [Data Ownership](./examples/EXAMPLE-G2-002-data-ownership.md) |
| CTL (Control) | [Access Control](./examples/EXAMPLE-G3-001-access-control.md), [Approval Authority](./examples/EXAMPLE-G3-002-approval-authority.md) |
| EVO (Evolution) | [API Versioning](./examples/EXAMPLE-G4-001-api-versioning.md), [Deprecation Policy](./examples/EXAMPLE-G4-002-deprecation-policy.md) |

### Self-Recorded Decisions

MANTRA records decisions about itself, demonstrating the system works:

| Decision | Statement |
|----------|-----------|
| [MANTRA-DECISION-001](./decisions/MANTRA-DECISION-001-immutability-principle.md) | Decisions MUST NOT be modified or deleted |
| [MANTRA-DECISION-002](./decisions/MANTRA-DECISION-002-ai-authority-zero.md) | AI authority in decision-making is ZERO |
| [MANTRA-DECISION-003](./decisions/MANTRA-DECISION-003-no-status-field.md) | No status field, lifecycle via supersedes |
| [MANTRA-DECISION-004](./decisions/MANTRA-DECISION-004-supersedes-chain.md) | Evolution via supersedes chain |
| [MANTRA-DECISION-005](./decisions/MANTRA-DECISION-005-four-group-taxonomy.md) | 4 Groups × 4 Features = 16-cell taxonomy |

---

## Technical Documentation

> **Notice**: Layer documentation contains constitutional law and binding specifications.
> It is not guidance. See User Documentation above for onboarding.

### Layer Structure

```
layer-0/              ← Constitutional Law (LOCKED)
layer-1/              ← Implementation Specifications (FROZEN)
layer-2/              ← Technical Architecture (FROZEN)
layer-3/              ← Operational Guidelines (Boundary FROZEN)
```

---

### Layer 0: Constitutional Law

Contains binding law and schema governing the Decision Matrix.

| Document | Type | Status |
|----------|------|--------|
| MANTRA-LAW-001 | Constitutional Law | LOCKED |
| MANTRA-SCHEMA-001 | JSON Schema | FINAL |
| MANTRA-DEC-001-004 | Decision Entries | ACTIVE |
| MANTRA-DOC-001 | Reference | FINAL |
| MANTRA-SPEC-001 | Validator Specification | LOCKED |

Non-compliance renders decisions INVALID.

Do not use for onboarding or tutorials.

---

### Layer 1: Implementation Specifications (FROZEN)

Contains implementation specifications subordinate to Layer 0.

| Document | Type | Status |
|----------|------|--------|
| MANTRA-LAYER-1-BOUNDARY-001 | Boundary Specification | FROZEN |
| MANTRA-L1-IMPL-VALIDATOR-001 | Implementation Specification | FROZEN |
| MANTRA-L1-IMPL-DECISION-STORE-001 | Implementation Specification | FROZEN |
| MANTRA-L1-IMPL-PUBLIC-READ-API-001 | Implementation Specification | FROZEN |
| [MANTRA-L1-DATA-INTEGRITY-001](./layer-1/MANTRA-L1-DATA-INTEGRITY-001-data-integrity-specification.md) | Data Integrity Specification | ACTIVE |
| MANTRA-L1-FREEZE-001 | Governance Declaration | ACTIVE |
| MANTRA-L1-CORRECTION-001 | Correction Record | ACTIVE |

Layer 1 is FROZEN per MANTRA-L1-FREEZE-001.

Layer 1 implements. Layer 1 does not redefine.

Layer 0 prevails in all conflicts.

---

### Layer 2: Technical Architecture (FROZEN)

Contains architectural boundary and implementation specifications subordinate to Layer 0 and Layer 1.

| Document | Type | Status |
|----------|------|--------|
| MANTRA-LAYER-2-BOUNDARY-001 | Boundary Specification | FROZEN |
| MANTRA-L2-FREEZE-001 | Governance Declaration | ACTIVE |
| MANTRA-L2-IMPL-RUNTIME-TOPOLOGY-001 | Implementation Specification | FROZEN |
| MANTRA-L2-IMPL-DATA-FLOW-001 | Implementation Specification | FROZEN |
| MANTRA-L2-IMPL-INTEGRATION-BOUNDARIES-001 | Implementation Specification | FROZEN |
| MANTRA-L2-IMPL-FAILURE-SURFACES-001 | Implementation Specification | FROZEN |
| MANTRA-L2-IMPL-FREEZE-001 | Governance Declaration | ACTIVE |

Layer 2 Boundary is FROZEN per MANTRA-L2-FREEZE-001.

Layer 2 Implementation Specifications are FROZEN per MANTRA-L2-IMPL-FREEZE-001.

Layer 2 defines architectural shape. Layer 2 does not define runtime behavior.

---

### Layer 3: Operational Guidelines (Boundary FROZEN)

Contains operational boundary specifications subordinate to Layer 0, Layer 1, and Layer 2.

| Document | Type | Status |
|----------|------|--------|
| MANTRA-LAYER-3-BOUNDARY-001 | Boundary Specification | FROZEN |
| MANTRA-L3-FREEZE-001 | Governance Declaration | ACTIVE |

Layer 3 Boundary is FROZEN per MANTRA-L3-FREEZE-001.

Layer 3 defines operational limits and discipline.

Layer 3 does not define implementation, automation, or procedures.

All frozen layers prevail in conflicts.

---

### Layer Status

| Layer | Purpose | Status |
|-------|---------|--------|
| layer-0 | Constitutional Law | LOCKED |
| layer-1 | Implementation Specifications | FROZEN |
| layer-2 | Technical Architecture | FROZEN |
| layer-3 | Operational Guidelines | Boundary FROZEN |

---

### Precedence Rule

**LAW > Decision Entries > Schema > Specification > Documentation**

---

### Immutability Rules

All Layer 0 documents are constitutional and immutable.

Higher layers MAY reference Layer 0 documents but MUST NOT:
- Redefine authority
- Alter decision validity rules
- Expand AI permissions
- Introduce alternative interpretations

Any violation is INVALID per MANTRA-LAW-001.

---

## Access MANTRA

**URL**: `http://31.97.111.175:3001`

| Endpoint | Purpose |
|----------|---------|
| `/` | Dashboard - View decisions by group |
| `/decisions` | All decisions |
| `/validator` | Validate decision format |
| `/audit` | Audit log |
| `/docs` | API documentation |

---

## Core Principles

| Principle | Description |
|-----------|-------------|
| **Immutable** | Decisions cannot be changed or deleted |
| **Human Authority** | Only humans can create/approve decisions |
| **Explicit Evolution** | Change happens via supersedes, not edits |
| **Structured Taxonomy** | 4 Groups × 4 Features = 16 categories |
| **Audit Trail** | Every action is logged permanently |

---

## The 4×4 Taxonomy

```
INT: Intent & Direction (WHY/WHAT)
├── F01: Vision & Outcome
├── F02: Problem Statement
├── F03: Scope & Non-Goals
└── F04: Principles & Values

ARCH: Architecture & Boundaries (HOW/WHERE)
├── F05: Domain & Bounded Context
├── F06: Service & Module Boundary
├── F07: Data Ownership & Sovereignty
└── F08: Integration & Contract Model

CTL: Control, Policy & Risk (CAN/MUST NOT)
├── F09: Policy & Rules
├── F10: Approval & Authority Model
├── F11: Security & Compliance Posture
└── F12: Risk, Blast Radius & Failure Tolerance

EVO: Execution & Evolution (CHANGE SAFELY)
├── F13: Decision Lifecycle
├── F14: Reversibility & Exit Strategy
├── F15: Environment & Promotion Rules
└── F16: Anti-Drift & Consistency Rules
```

---

**Easy to leave. Hard to want to leave.**
