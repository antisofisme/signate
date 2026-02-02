# Schema Decision Entries (DEC-001 to DEC-004)

**Document Type**: Decision Record
**Status**: ACTIVE
**Authority**: Human Decision Only

---

## DEC-001: Scope Enumeration

**decision_id**: DEC-001

**group_id**: GROUP-2

**feature_id**: F-05

**scope**: ORGANIZATION

**blast_radius**: CRITICAL

**status**: ACTIVE

**version**: 1.0.0

### Statement

The `scope` field in Decision Schema v1 SHALL enumerate exactly three values: ORGANIZATION, DOMAIN, APPLICATION. All decisions MUST be assigned exactly one scope value. No additional scope values SHALL be added without amendment to this decision.

### Rationale

Three-level scope provides sufficient granularity for organizational, domain-level, and application-specific decisions without excessive fragmentation. This enumeration aligns with common bounded context hierarchies and reduces misclassification risk.

### Constraints

| constraint_id | statement | type |
|---------------|-----------|------|
| C-001-01 | Scope value MUST be one of: ORGANIZATION, DOMAIN, APPLICATION. | REQUIREMENT |
| C-001-02 | Scope value MUST NOT be empty or null. | PROHIBITION |
| C-001-03 | Scope value MUST NOT contain values outside the enumeration. | PROHIBITION |

### Invariants

- The enumeration contains exactly three values.
- The enumeration values are mutually exclusive.
- No decision may have multiple scope values.

---

## DEC-002: Blast Radius Enumeration

**decision_id**: DEC-002

**group_id**: GROUP-3

**feature_id**: F-12

**scope**: ORGANIZATION

**blast_radius**: CRITICAL

**status**: ACTIVE

**version**: 1.0.0

### Statement

The `blast_radius` field in Decision Schema v1 SHALL enumerate exactly four values: LOW, MEDIUM, HIGH, CRITICAL. All decisions MUST be assigned exactly one blast_radius value. No additional blast_radius values SHALL be added without amendment to this decision.

### Rationale

Four-level severity provides proportional impact signaling aligned with standard risk frameworks. Binary classification was rejected as insufficient for proportionality. Numeric scales were rejected due to subjectivity and inconsistency risk.

### Constraints

| constraint_id | statement | type |
|---------------|-----------|------|
| C-002-01 | Blast_radius value MUST be one of: LOW, MEDIUM, HIGH, CRITICAL. | REQUIREMENT |
| C-002-02 | Blast_radius value MUST NOT be empty or null. | PROHIBITION |
| C-002-03 | Blast_radius value MUST NOT contain values outside the enumeration. | PROHIBITION |

### Invariants

- The enumeration contains exactly four values.
- The enumeration values represent ordered severity from LOW to CRITICAL.
- No decision may have multiple blast_radius values.

---

## DEC-003: Constraints Field Structure

**decision_id**: DEC-003

**group_id**: GROUP-2

**feature_id**: F-08

**scope**: ORGANIZATION

**blast_radius**: HIGH

**status**: ACTIVE

**version**: 1.0.0

### Statement

The `constraints` field in Decision Schema v1 SHALL be structured as an array of typed constraint objects. Each constraint object MUST contain: constraint_id (string), statement (string), type (enumeration). The type field SHALL enumerate exactly three values: PROHIBITION, REQUIREMENT, LIMITATION.

### Rationale

Typed constraint objects enable machine-readable classification while preserving human-readable statements. Flat string arrays were rejected due to lack of validation capability. Fully relational structures were rejected due to excessive complexity.

### Constraints

| constraint_id | statement | type |
|---------------|-----------|------|
| C-003-01 | Each constraint object MUST contain constraint_id, statement, and type fields. | REQUIREMENT |
| C-003-02 | Constraint type MUST be one of: PROHIBITION, REQUIREMENT, LIMITATION. | REQUIREMENT |
| C-003-03 | Constraint_id MUST be unique within the decision. | REQUIREMENT |
| C-003-04 | Constraint statement MUST NOT be empty. | PROHIBITION |

### Invariants

- The constraints field is an array.
- Each array element is an object with three required fields.
- The type enumeration contains exactly three values.

---

## DEC-004: Invariants Field Structure

**decision_id**: DEC-004

**group_id**: GROUP-4

**feature_id**: F-16

**scope**: ORGANIZATION

**blast_radius**: HIGH

**status**: ACTIVE

**version**: 1.0.0

### Statement

The `invariants` field in Decision Schema v1 SHALL be structured as an array of strings. Each string MUST contain a human-readable invariant statement. No typed structure SHALL be applied to invariants.

### Rationale

Flat string arrays preserve simplicity and human readability for invariant statements. Typed objects were rejected to avoid misuse of conditional severity classifications. Consequence-linked structures were rejected due to potential conflict with MANTRA-LAW-001 §7.4.

### Constraints

| constraint_id | statement | type |
|---------------|-----------|------|
| C-004-01 | The invariants field MUST be an array of strings. | REQUIREMENT |
| C-004-02 | Each invariant string MUST NOT be empty. | PROHIBITION |
| C-004-03 | Invariant statements MUST NOT contain structured data or embedded objects. | PROHIBITION |

### Invariants

- The invariants field is an array.
- Each array element is a string.
- No typed classification is applied to invariants.

---

**END OF DECISION ENTRIES**
