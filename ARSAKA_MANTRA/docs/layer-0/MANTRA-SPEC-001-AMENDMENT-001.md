# MANTRA-SPEC-001-AMENDMENT-001: Status Field Removal

**Document Type**: Constitutional Amendment
**Amends**: MANTRA-SPEC-001 v1.1.0
**Version**: 1.0.0
**Status**: RATIFIED
**Effective**: 2025-01-24
**Authority**: Human Decision Only

---

## 1. Amendment Statement

This amendment formally removes lifecycle/status semantics from the ARSAKA_MANTRA Decision Matrix system.

Per Human Decision, decision evolution is expressed **exclusively** via:
- `version` field (semantic versioning)
- `supersedes` field (reference to prior decision)

The `status` field is constitutionally removed.

---

## 2. Deprecated Rules

The following validation rules are **DEPRECATED** and no longer enforced:

| Rule ID | Original Condition | Governing Reference |
|---------|-------------------|---------------------|
| S-019 | status is present | Schema: required |
| S-020 | status is one of: PROPOSED, ACTIVE, DEPRECATED | Schema: enum |
| L-007 | status was not changed by AI | LAW §6.3 |

---

## 3. Schema Changes

### 3.1 Removed from Required Fields
- `status`

### 3.2 Removed Properties
- `status` property definition
- `Status` enum definition ($defs/Status)

### 3.3 Removed Invalid States
- "status transition performed by non-human"

---

## 4. Rationale

### 4.1 Problem Statement
The `status` field introduced lifecycle semantics (PROPOSED → ACTIVE → DEPRECATED) that implied mutability of decision records. This contradicted the absolute immutability mandate of MANTRA-LAW-001 §10.

### 4.2 Resolution
Decision lifecycle is now expressed through the existing version chain:
- New decisions have `version: "1.0.0"` and `supersedes: null`
- Evolved decisions have incremented version and reference prior decision via `supersedes`
- The **consumer** interprets which decision is "current" for a given group/feature

### 4.3 Immutability Preserved
Stored decisions remain absolutely immutable. No field may be modified after storage. Evolution occurs only through new decision records.

---

## 5. Conformance Requirements

### 5.1 Validator
- MUST NOT check for `status` field presence
- MUST NOT validate `status` enumeration
- MUST skip L-007 unconditionally (rule deprecated)
- Rule count reduced from 47 to 44

### 5.2 Store Service
- MUST NOT assign default status
- MUST NOT reference status in storage logic

### 5.3 Read API
- MUST NOT filter by status
- MUST NOT collapse versions based on status
- MUST return ALL decisions for consumer interpretation

### 5.4 Database
- MUST NOT have `status` column
- MUST NOT have `decision_status` enum type

---

## 6. Amendment Authority

This amendment was ratified by explicit Human Decision per MANTRA-LAW-001 §8.

### 6.1 Ratification Record
- **Decision**: Remove status field and lifecycle semantics
- **Authority**: Human (constitutional amendment authority)
- **Date**: 2025-01-24
- **Basis**: MANTRA-LAW-001 §8 (Amendment)

### 6.2 Supersession
This amendment supersedes any prior interpretation that required the `status` field.

---

## 7. Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-01-24 | Initial ratification |

---

**END OF AMENDMENT**
