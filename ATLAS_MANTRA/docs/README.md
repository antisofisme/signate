# ATLAS_MANTRA Documentation

**TYPE**: Law and Specification Repository
**STATUS**: Active
**AUTHORITY**: Human Decision Only

---

## Notice

Layer 0 contains constitutional law and binding schema. It is not guidance.

Higher layers contain specifications and operational boundaries subordinate to Layer 0.

---

## Structure

```
docs/
├── README.md                                        ← This file
├── layer-0/                                         ← Constitutional Law (LOCKED)
│   ├── README.md
│   ├── MANTRA-LAW-001-decision-matrix-canon.md      ← Constitutional Law
│   ├── MANTRA-SCHEMA-001-decision-schema-v1.json    ← JSON Schema
│   ├── MANTRA-DEC-001-004-schema-decisions.md       ← Binding Decisions
│   ├── MANTRA-DOC-001-decision-schema-reference.md  ← Reference Documentation
│   └── MANTRA-SPEC-001-validator-linting-specification.md ← Validator Specification
│
├── layer-1/                                         ← Implementation Specifications (FROZEN)
│   ├── README.md
│   ├── MANTRA-LAYER-1-BOUNDARY-001-implementation-boundary-rules.md ← Boundary Rules [FROZEN]
│   ├── MANTRA-L1-IMPL-VALIDATOR-001-validator-implementation-specification.md ← Validator [FROZEN]
│   ├── MANTRA-L1-IMPL-DECISION-STORE-001-decision-store-implementation-specification.md ← Store [FROZEN]
│   ├── MANTRA-L1-IMPL-PUBLIC-READ-API-001-public-read-api-implementation-specification.md ← Read API [FROZEN]
│   ├── MANTRA-L1-FREEZE-001-layer-1-freeze-declaration.md ← Freeze Declaration
│   └── MANTRA-L1-CORRECTION-001-layer-1-documentation-corrections.md ← Corrections
│
├── layer-2/                                         ← Technical Architecture (FROZEN)
│   ├── README.md
│   ├── MANTRA-LAYER-2-BOUNDARY-001-architecture-boundary-rules.md ← Architecture Boundary [FROZEN]
│   ├── MANTRA-L2-FREEZE-001-layer-2-boundary-freeze-declaration.md ← Boundary Freeze Declaration
│   ├── MANTRA-L2-IMPL-RUNTIME-TOPOLOGY-001-runtime-topology-specification.md ← Runtime Topology [FROZEN]
│   ├── MANTRA-L2-IMPL-DATA-FLOW-001-data-flow-realization-specification.md ← Data Flow [FROZEN]
│   ├── MANTRA-L2-IMPL-INTEGRATION-BOUNDARIES-001-integration-boundary-specification.md ← Integration [FROZEN]
│   ├── MANTRA-L2-IMPL-FAILURE-SURFACES-001-failure-surface-specification.md ← Failure Surfaces [FROZEN]
│   └── MANTRA-L2-IMPL-FREEZE-001-layer-2-implementation-freeze-declaration.md ← Implementation Freeze
│
└── layer-3/                                         ← Operational Guidelines (Boundary FROZEN)
    ├── README.md
    ├── MANTRA-LAYER-3-BOUNDARY-001-operational-boundary-rules.md ← Operational Boundary [FROZEN]
    └── MANTRA-L3-FREEZE-001-layer-3-boundary-freeze-declaration.md ← Boundary Freeze
```

---

## Layer 0: Constitutional Law

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

## Layer 1: Implementation Specifications (FROZEN)

Contains implementation specifications subordinate to Layer 0.

| Document | Type | Status |
|----------|------|--------|
| MANTRA-LAYER-1-BOUNDARY-001 | Boundary Specification | FROZEN |
| MANTRA-L1-IMPL-VALIDATOR-001 | Implementation Specification | FROZEN |
| MANTRA-L1-IMPL-DECISION-STORE-001 | Implementation Specification | FROZEN |
| MANTRA-L1-IMPL-PUBLIC-READ-API-001 | Implementation Specification | FROZEN |
| MANTRA-L1-FREEZE-001 | Governance Declaration | ACTIVE |
| MANTRA-L1-CORRECTION-001 | Correction Record | ACTIVE |

Layer 1 is FROZEN per MANTRA-L1-FREEZE-001.

Layer 1 implements. Layer 1 does not redefine.

Layer 0 prevails in all conflicts.

---

## Layer 2: Technical Architecture (FROZEN)

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

## Layer 3: Operational Guidelines (Boundary FROZEN)

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

## Layer Status

| Layer | Purpose | Status |
|-------|---------|--------|
| layer-0 | Constitutional Law | LOCKED |
| layer-1 | Implementation Specifications | FROZEN |
| layer-2 | Technical Architecture | FROZEN |
| layer-3 | Operational Guidelines | Boundary FROZEN |

Layer 0 is constitutionally sealed.

Layer 1 is frozen per MANTRA-L1-FREEZE-001.

Layer 2 is frozen per MANTRA-L2-FREEZE-001 and MANTRA-L2-IMPL-FREEZE-001.

Layer 3 Boundary is frozen per MANTRA-L3-FREEZE-001.

---

## Precedence Rule

**LAW > Decision Entries > Schema > Specification > Documentation**

---

## Layer 0 Immutability and Boundary Rule

All Layer 0 documents are constitutional and immutable.

They MUST NOT be modified, reinterpreted, or overridden by any lower layer.

Higher layers MAY reference Layer 0 documents but MUST NOT:

- Redefine authority
- Alter decision validity rules
- Expand AI permissions
- Introduce alternative interpretations

Any attempt to do so is INVALID per MANTRA-LAW-001.

---

**END OF README**
