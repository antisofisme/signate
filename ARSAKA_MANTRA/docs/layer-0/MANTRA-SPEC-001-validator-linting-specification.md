# MANTRA-SPEC-001: Validator / Linting Specification

**Document Type**: Validation Specification
**Version**: 1.2.0
**Status**: LOCKED
**Effective**: 2025-01-24
**Amended**: 2025-01-24
**Authority**: Human Decision Only

**Amendment**: This document has been amended by MANTRA-SPEC-001-AMENDMENT-001.
Rules S-019, S-020, and L-007 are DEPRECATED. See Amendment for details.

**Governing Artifacts**:
- MANTRA-LAW-001 (Decision Matrix Canon)
- DEC-001 (scope enumeration)
- DEC-002 (blast_radius enumeration)
- DEC-003 (constraints structure)
- DEC-004 (invariants structure)
- Decision Schema v1

**Authority Statement**: This specification derives validation rules from governing artifacts. It holds no independent authority. All rules trace to LAW, Decision Entries, or Schema. Humans retain final authority over interpretation and enforcement.

---

## 1. Document Metadata

**Document Type**: Validation Specification

**Version**: 1.2.0

**Governing Artifacts**:
- MANTRA-LAW-001 (Decision Matrix Canon)
- DEC-001 (scope enumeration)
- DEC-002 (blast_radius enumeration)
- DEC-003 (constraints structure)
- DEC-004 (invariants structure)
- Decision Schema v1

**Authority Statement**: This specification derives validation rules from governing artifacts. It holds no independent authority. All rules trace to LAW, Decision Entries, or Schema. Humans retain final authority over interpretation and enforcement.

---

## 2. Purpose and Scope

### 2.1 What This Validator Is Responsible For

The validator determines whether a decision record conforms to:
- Structural requirements defined in Decision Schema v1
- Consistency requirements defined in Decision Entries DEC-001 through DEC-004
- Compliance requirements defined in MANTRA-LAW-001

The validator produces a determination of VALID, INVALID, or REJECTED.

### 2.2 What This Validator Does NOT Do

The validator does NOT:
- Enforce decisions at runtime
- Execute workflow or approval logic
- Perform AI reasoning or inference
- Verify authorship identity
- Modify records
- Emit events or notifications
- Trigger side effects
- Grant or revoke authority
- Interpret ambiguous content
- Resolve conflicts between decisions

The validator is read-only, deterministic, and side-effect-free.

---

## 3. Validation Model

### 3.1 Validation Levels

Validation proceeds through three levels:

| Level | Name | Scope |
|-------|------|-------|
| 1 | Schema Validation | Structural conformance to Decision Schema v1 |
| 2 | Decision Consistency Validation | Semantic conformance to DEC-001 through DEC-004 |
| 3 | Law Compliance Validation | Authority and integrity conformance to MANTRA-LAW-001 |

### 3.2 Conceptual Distinction

**Schema Validation** (Level 1):
Verifies that the record is well-formed. Checks presence, type, format, and enumeration membership. Does not evaluate meaning.

**Decision Consistency Validation** (Level 2):
Verifies that field values are consistent with binding decisions. Checks group–feature compatibility, constraint structure completeness, and field value exclusivity.

**Law Compliance Validation** (Level 3):
Verifies that the record does not violate authority constraints. Checks authorship prohibitions, mutability rules, and status transition authority. Some rules in this level are conditional on authorship metadata availability.

---

## 4. Validation Rules

### 4.1 Level 1: Schema Validation Rules

| Rule ID | Condition | Failure Result | Governing Reference |
|---------|-----------|----------------|---------------------|
| S-001 | decision_id is present | INVALID | Schema: required |
| S-002 | decision_id is valid UUID format | INVALID | Schema: format |
| S-003 | group_id is present | INVALID | Schema: required |
| S-004 | group_id is one of: GROUP-1, GROUP-2, GROUP-3, GROUP-4 | INVALID | Schema: enum |
| S-005 | feature_id is present | INVALID | Schema: required |
| S-006 | feature_id is one of: F-01 through F-16 | INVALID | Schema: enum |
| S-007 | scope is present | INVALID | Schema: required |
| S-008 | scope is one of: ORGANIZATION, DOMAIN, APPLICATION | INVALID | DEC-001 |
| S-009 | blast_radius is present | INVALID | Schema: required |
| S-010 | blast_radius is one of: LOW, MEDIUM, HIGH, CRITICAL | INVALID | DEC-002 |
| S-011 | statement is present | INVALID | Schema: required |
| S-012 | statement has minimum length 1 | INVALID | Schema: minLength |
| S-013 | rationale is present | INVALID | Schema: required |
| S-014 | rationale has minimum length 1 | INVALID | Schema: minLength |
| S-015 | constraints is present | INVALID | Schema: required |
| S-016 | constraints is an array | INVALID | Schema: type |
| S-017 | invariants is present | INVALID | Schema: required |
| S-018 | invariants is an array | INVALID | Schema: type |
| ~~S-019~~ | ~~status is present~~ | ~~INVALID~~ | ~~DEPRECATED per AMENDMENT-001~~ |
| ~~S-020~~ | ~~status is one of: PROPOSED, ACTIVE, DEPRECATED~~ | ~~INVALID~~ | ~~DEPRECATED per AMENDMENT-001~~ |
| S-021 | version is present | INVALID | Schema: required |
| S-022 | version matches pattern `^[0-9]+\.[0-9]+\.[0-9]+$` | INVALID | Schema: pattern |

### 4.2 Level 2: Decision Consistency Rules

| Rule ID | Condition | Failure Result | Governing Reference |
|---------|-----------|----------------|---------------------|
| D-001 | If group_id = GROUP-1, then feature_id is one of: F-01, F-02, F-03, F-04 | INVALID | LAW §3.2 |
| D-002 | If group_id = GROUP-2, then feature_id is one of: F-05, F-06, F-07, F-08 | INVALID | LAW §3.3 |
| D-003 | If group_id = GROUP-3, then feature_id is one of: F-09, F-10, F-11, F-12 | INVALID | LAW §3.4 |
| D-004 | If group_id = GROUP-4, then feature_id is one of: F-13, F-14, F-15, F-16 | INVALID | LAW §3.5 |
| D-005 | Each constraint object contains constraint_id field | INVALID | DEC-003 |
| D-006 | Each constraint object contains statement field | INVALID | DEC-003 |
| D-007 | Each constraint object contains type field | INVALID | DEC-003 |
| D-008 | Each constraint.type is one of: PROHIBITION, REQUIREMENT, LIMITATION | INVALID | DEC-003 |
| D-009 | Each constraint.constraint_id has minimum length 1 | INVALID | DEC-003 |
| D-010 | Each constraint.statement has minimum length 1 | INVALID | DEC-003 |
| D-011 | All constraint.constraint_id values are unique within the decision | INVALID | DEC-003 |
| D-012 | Each invariant string has minimum length 1 | INVALID | DEC-004 |
| D-013 | scope contains exactly one value (not array, not multiple) | INVALID | DEC-001 |
| D-014 | blast_radius contains exactly one value (not array, not multiple) | INVALID | DEC-002 |

### 4.3 Level 3: Law Compliance Rules

#### 4.3.1 Unconditional Rules

| Rule ID | Condition | Failure Result | Governing Reference |
|---------|-----------|----------------|---------------------|
| L-009 | If content changed from prior version, version field was incremented | REJECTED | LAW §8.3 |
| L-010 | Decision belongs to exactly one group (group_id singular) | INVALID | LAW §3.1 |
| L-011 | Decision relates to exactly one feature (feature_id singular) | INVALID | LAW §3.1 |

#### 4.3.2 Authorship-Dependent Rules (Conditional)

The following rules depend on availability of trusted authorship metadata. If authorship metadata is unavailable, these rules are SKIPPED and an advisory note is included in the output.

| Rule ID | Condition | Failure Result | Governing Reference |
|---------|-----------|----------------|---------------------|
| L-001 | decision_id was not assigned by AI | INVALID | LAW §6.3 |
| L-002 | decision_id was not modified after creation | INVALID | LAW §2.3 |
| L-003 | group_id was not assigned by AI | INVALID | LAW §6.3 |
| L-004 | feature_id was not assigned by AI | INVALID | LAW §6.3 |
| L-005 | statement was not authored by AI | INVALID | LAW §2.3, §6.3 |
| L-006 | rationale was not authored by AI | INVALID | LAW §2.3, §6.3 |
| ~~L-007~~ | ~~status was not changed by AI~~ | ~~INVALID~~ | ~~DEPRECATED per AMENDMENT-001~~ |
| L-008 | approved_by does not contain AI identifier | INVALID | LAW §6.3 |

**Required Behavior When Authorship Metadata Is Unavailable**:
- Rules L-001 through L-008 are skipped
- Validation proceeds with remaining rules
- Output includes advisory note listing skipped rules
- Status is determined by non-skipped rules only

---

## 5. Validation Ordering and Short-Circuit Rules

### 5.1 Required Execution Order

Validation MUST proceed in the following order:

| Phase | Level | Rules |
|-------|-------|-------|
| 1 | Schema Validation | S-001 through S-022 |
| 2 | Decision Consistency Validation | D-001 through D-014 |
| 3 | Law Compliance Validation | L-001 through L-011 |

Within each phase, rules MUST be evaluated in rule ID order.

### 5.2 Short-Circuit Conditions

| Condition | Permitted Behavior |
|-----------|-------------------|
| Any Level 1 rule fails | MAY terminate before Level 2 |
| Any Level 2 rule fails | MAY terminate before Level 3 |
| Multiple failures in same level | MUST NOT terminate; report all failures in level |

### 5.3 Short-Circuit Rationale

Level 1 failures indicate malformed records. Semantic evaluation of malformed records is undefined.

Level 2 failures indicate inconsistency with binding decisions. Compliance evaluation of inconsistent records may produce misleading results.

Short-circuit is permitted, not required. Full evaluation across all levels is valid.

---

## 6. INVALID vs REJECTED Semantics

### 6.1 INVALID

**Definition**: A record is INVALID when it fails to meet structural, consistency, or authority requirements.

**Applicable Rules**: All rules except L-009.

**Legal Consequence**: Per LAW §7.4, the decision or action has no legal effect within the system.

**Interpretation**: An INVALID record does not constitute a valid decision. It cannot be referenced, enforced, or relied upon.

### 6.2 REJECTED

**Definition**: A record is REJECTED when an attempted change violates mutability or versioning requirements.

**Applicable Rules**: L-009 (version increment requirement).

**Legal Consequence**: Per LAW §7.4, the attempted change is nullified. Prior state persists.

**Interpretation**: REJECTED represents a prohibited action attempt, not a recoverable validation error. The change did not occur. The prior valid state remains authoritative. Re-submission with corrected versioning is required for the change to take effect.

### 6.3 Distinction Summary

| Aspect | INVALID | REJECTED |
|--------|---------|----------|
| Applies to | Record state | Change attempt |
| Meaning | Record is not a valid decision | Change was nullified |
| Prior state | Not applicable | Preserved and authoritative |
| Legal standing | None | Prior record retains standing |
| Recovery | Submit new valid record | Re-submit with correct version |

---

## 7. Validator Output Contract

### 7.1 Output Structure

The validator output MUST contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | Enumeration | Yes | VALID, INVALID, or REJECTED |
| violations | Array | Yes | List of rule violations; empty if VALID |
| skipped_rules | Array | Yes | List of rule IDs skipped due to missing metadata |
| advisory_notes | Array | No | Notes regarding skipped rules or partial evaluation |
| validated_at | Timestamp | Yes | UTC timestamp of validation |
| schema_version | String | Yes | Version of schema used (1.0.0) |
| specification_version | String | Yes | Version of this specification (1.1.0) |

### 7.2 Violation Structure

Each entry in the violations array MUST contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| rule_id | String | Yes | Rule identifier (e.g., S-001, D-005, L-003) |
| level | Enumeration | Yes | Schema, Decision, or Law |
| message | String | Yes | Description of the violation |
| field | String | No | Field path that caused the violation |
| failure_result | Enumeration | Yes | INVALID or REJECTED |
| governing_reference | String | Yes | LAW section, DEC number, or Schema reference |

### 7.3 Status Determination Rules

| Condition | Resulting Status |
|-----------|------------------|
| No violations and no skipped rules | VALID |
| No violations and some skipped rules | VALID (with advisory) |
| Any violation with INVALID failure_result | INVALID |
| All violations have REJECTED failure_result | REJECTED |
| Mix of INVALID and REJECTED violations | INVALID |

### 7.4 Side-Effect Prohibitions

The validator MUST NOT:
- Modify the input record
- Modify any stored record
- Create or delete records
- Emit events or messages
- Trigger workflows or approvals
- Change decision status
- Write to audit logs
- Invoke external systems
- Cache or persist results beyond output

The validator is stateless, side-effect-free, and deterministic. Given identical input and metadata availability, output MUST be identical.

---

## 8. Authority and Limitations

### 8.1 Authorship Detection Dependency

Rules L-001 through L-008 require determination of whether content was authored or assigned by AI.

This specification does NOT define:
- How authorship is detected
- How AI identifiers are recognized
- What constitutes "trusted" authorship metadata
- How authorship metadata is stored or transmitted

These mechanisms are implementation concerns outside this specification's scope.

When authorship metadata is unavailable:
- Rules L-001 through L-008 are skipped
- The validator reports which rules were skipped
- Validation continues with remaining rules
- The output includes advisory notes

When authorship metadata is available:
- Rules L-001 through L-008 are evaluated
- The validator relies on metadata accuracy
- The validator does not verify metadata authenticity

### 8.2 Explicit Non-Goals

This validator specification does NOT:
- Define runtime enforcement behavior
- Define workflow or approval logic
- Define notification or alerting systems
- Define authentication or authorization
- Define audit logging requirements
- Define persistence or storage
- Define API contracts
- Define event emission
- Define error recovery procedures
- Grant authority to automated systems
- Permit AI to validate its own output
- Permit self-modification

### 8.3 No Enforcement, Workflow, or Mutation Authority

The validator has no authority to:
- Prevent record creation
- Block record modification
- Enforce compliance
- Trigger remediation
- Escalate violations
- Notify stakeholders
- Modify system state

The validator produces output. Enforcement decisions based on output are human responsibility.

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-01-24 | Initial specification |
| 1.1.0 | 2025-01-24 | Clarified authorship-dependent rules, REJECTED semantics, version pattern |
| 1.2.0 | 2025-01-24 | AMENDMENT-001: Deprecated S-019, S-020, L-007 (status field removal) |

---

**END OF SPECIFICATION**
