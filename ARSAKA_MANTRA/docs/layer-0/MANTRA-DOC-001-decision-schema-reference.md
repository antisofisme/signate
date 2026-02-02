# Decision Schema v1 — Reference Documentation

---

## 1. Document Metadata

**Document Type**: Technical-Legal Reference

**Schema Version**: 1.0.0

**Schema File**: MANTRA-SCHEMA-001-decision-schema-v1.json

**Governing Law**: MANTRA-LAW-001 (Decision Matrix Canon)

**Authority Statement**: All decisions, amendments, and interpretations require explicit human authorization. No automated system, AI, or application holds decision authority.

---

## 2. Purpose of the Decision Schema

### 2.1 What This Schema Is For

Decision Schema v1 defines the structural representation of decision records within systems governed by the ARSAKA_MANTRA framework.

The schema establishes:
- The set of fields required for a valid decision record
- The set of fields permitted as optional metadata
- Valid enumerations for categorical fields
- Structural requirements for complex fields
- Compatibility constraints between decision groups and features

### 2.2 What This Schema Does NOT Do

The schema does NOT:
- Define runtime behavior
- Define enforcement mechanisms
- Define workflow sequences
- Define user interface presentation
- Define storage or persistence requirements
- Define API contracts
- Define event handling
- Define notification or alerting
- Define authentication or authorization
- Establish decision precedence between records

The schema is structural. It defines form, not function.

---

## 3. Relationship to Governing Artifacts

### 3.1 Derivation from MANTRA-LAW-001

Decision Schema v1 is derived from MANTRA-LAW-001 and is subordinate to it.

The following schema elements derive directly from the LAW:

| LAW Section | Schema Element |
|-------------|----------------|
| §2.2 Composition | GroupId enumeration (4 values) |
| §2.2 Composition | FeatureId enumeration (16 values) |
| §2.3 Invalidity Conditions | Required fields (statement, rationale) |
| §3.2–§3.5 Group Definitions | Group–Feature compatibility constraints |
| §4.1 Definitions | Constraints and invariants as decision components |
| §5 Sovereignty | Organizational scope requirement |
| §6 AI Authority | AI prohibition declarations |
| §7 Failure Modes | Invalid state classifications |
| §8.3 Amendment Process | Version field requirement |

### 3.2 Binding Effect of Decision Entries

Four Decision Entries resolve ambiguities in the schema and are binding:

| Entry | Field | Binding Resolution |
|-------|-------|-------------------|
| DEC-001 | scope | Three-value enumeration: ORGANIZATION, DOMAIN, APPLICATION |
| DEC-002 | blast_radius | Four-value enumeration: LOW, MEDIUM, HIGH, CRITICAL |
| DEC-003 | constraints | Typed object array with constraint_id, statement, type |
| DEC-004 | invariants | String array without typed structure |

These entries are FINAL. The schema conforms to their specifications exactly.

### 3.3 Conflict Precedence Rule

If conflict exists between governing artifacts:

**LAW > Decision Entries > Schema**

The LAW prevails over all. Decision Entries prevail over schema structure. The schema MUST NOT contradict either.

---

## 4. Field-by-Field Reference

### 4.1 decision_id

**Type**: String (UUID format)

**Required**: Yes

**Mutability**: Immutable after creation

**Valid Values**: Any valid UUID

**Invalid Conditions**:
- Assigned by AI
- Assigned by non-system entity
- Modified after initial assignment
- Empty or null

**Authority Constraints**: System-assigned only. Human and AI MUST NOT assign.

---

### 4.2 group_id

**Type**: Enumeration

**Required**: Yes

**Mutability**: Immutable

**Valid Values**: GROUP-1, GROUP-2, GROUP-3, GROUP-4

**Invalid Conditions**:
- Value outside enumeration
- Empty or null
- Multiple values assigned
- Incompatible with assigned feature_id

**Authority Constraints**: Human assignment only. AI MUST NOT assign.

---

### 4.3 feature_id

**Type**: Enumeration

**Required**: Yes

**Mutability**: Immutable

**Valid Values**: F-01 through F-16

**Compatibility Requirement**:
- GROUP-1 permits: F-01, F-02, F-03, F-04
- GROUP-2 permits: F-05, F-06, F-07, F-08
- GROUP-3 permits: F-09, F-10, F-11, F-12
- GROUP-4 permits: F-13, F-14, F-15, F-16

**Invalid Conditions**:
- Value outside enumeration
- Empty or null
- Multiple values assigned
- Incompatible with assigned group_id

**Authority Constraints**: Human assignment only. AI MUST NOT assign.

---

### 4.4 scope

**Type**: Enumeration

**Required**: Yes

**Mutability**: Mutable via version increment only

**Valid Values**: ORGANIZATION, DOMAIN, APPLICATION

**Invalid Conditions**:
- Value outside enumeration
- Empty or null
- Multiple values assigned

**Authority Constraints**: Human assignment only. AI MUST NOT assign.

---

### 4.5 blast_radius

**Type**: Enumeration

**Required**: Yes

**Mutability**: Mutable via version increment only

**Valid Values**: LOW, MEDIUM, HIGH, CRITICAL

**Ordering**: LOW < MEDIUM < HIGH < CRITICAL (severity ascending)

**Invalid Conditions**:
- Value outside enumeration
- Empty or null
- Multiple values assigned

**Authority Constraints**: Human assignment only. AI MUST NOT assign.

---

### 4.6 statement

**Type**: String

**Required**: Yes

**Mutability**: Mutable via version increment only

**Minimum Length**: 1 character

**Invalid Conditions**:
- Empty or null
- Authored by AI
- Contains non-normative language where normative is required

**Authority Constraints**: Human authorship only. AI MUST NOT author.

---

### 4.7 rationale

**Type**: String

**Required**: Yes

**Mutability**: Mutable via version increment only

**Minimum Length**: 1 character

**Invalid Conditions**:
- Empty or null
- Authored by AI

**Authority Constraints**: Human authorship only. AI MUST NOT author.

---

### 4.8 constraints

**Type**: Array of Constraint Objects

**Required**: Yes (empty array permitted)

**Mutability**: Mutable via version increment only

**Object Structure**:

| Sub-field | Type | Required | Valid Values |
|-----------|------|----------|--------------|
| constraint_id | String | Yes | Non-empty, unique within decision |
| statement | String | Yes | Non-empty |
| type | Enumeration | Yes | PROHIBITION, REQUIREMENT, LIMITATION |

**Invalid Conditions**:
- Constraint object missing constraint_id
- Constraint object missing statement
- Constraint object missing type
- constraint_id is empty
- statement is empty
- type value outside enumeration
- constraint_id duplicated within same decision

**Authority Constraints**: Human authorship only. AI MUST NOT author constraint content.

---

### 4.9 invariants

**Type**: Array of Strings

**Required**: Yes (empty array permitted)

**Mutability**: Mutable via version increment only

**Element Type**: String (non-empty)

**Invalid Conditions**:
- Array element is empty string
- Array element contains structured data
- Array element contains embedded objects

**Authority Constraints**: Human authorship only. AI MUST NOT author invariant content.

---

### 4.10 status

**Type**: Enumeration

**Required**: Yes

**Mutability**: Mutable by human action only

**Valid Values**: PROPOSED, ACTIVE, DEPRECATED

**Transition Constraint**: Status transitions require human action. Automated transitions are INVALID.

**Invalid Conditions**:
- Value outside enumeration
- Transition performed by AI
- Transition performed by automated system without human trigger

**Authority Constraints**: Human action only. AI MUST NOT change status.

---

### 4.11 version

**Type**: String (Semantic Versioning)

**Required**: Yes

**Mutability**: Increment only

**Format**: MAJOR.MINOR.PATCH (e.g., 1.0.0)

**Increment Requirement**: Version MUST be incremented when any mutable field changes.

**Invalid Conditions**:
- Format does not match pattern
- Not incremented after content change
- Decremented

**Authority Constraints**: Human or system may increment. AI MUST NOT determine version.

---

### 4.12 Optional Fields

The following fields are optional:

| Field | Type | Purpose |
|-------|------|---------|
| created_by | String | Human identifier of creator |
| created_at | DateTime | Timestamp of creation |
| approved_by | String | Human identifier of approver |
| approved_at | DateTime | Timestamp of approval |
| supersedes | UUID | Reference to prior decision replaced by this one |
| related_decisions | Array of UUID | References to related decisions |

**Invalid Conditions for approved_by**:
- Contains AI identifier
- Contains automated system identifier

---

## 5. Validation and Invalid States

### 5.1 Structural Validity

A decision record is structurally valid when:
- All required fields are present
- All field values conform to defined types
- All enumeration values fall within permitted sets
- Group–feature compatibility is satisfied
- All constraint objects contain required sub-fields
- All invariant strings are non-empty
- Version follows semantic versioning format

### 5.2 Categories of Invalid States

**Category A: Identity Violations**
- decision_id assigned by non-system entity
- decision_id modified after creation

**Category B: Classification Violations**
- group_id outside enumeration
- feature_id outside enumeration
- feature_id incompatible with group_id

**Category C: Authorship Violations**
- statement authored by AI
- rationale authored by AI
- approved_by contains AI identifier

**Category D: Content Violations**
- statement empty or absent
- rationale empty or absent
- scope outside enumeration or empty
- blast_radius outside enumeration or empty

**Category E: Constraint Violations**
- Constraint missing required sub-field
- Constraint type outside enumeration
- constraint_id not unique within decision
- constraint_id or statement empty

**Category F: Invariant Violations**
- Invariant string empty

**Category G: Lifecycle Violations**
- Status changed by non-human
- Version not incremented after change

### 5.3 Consequence of Invalid States

Per MANTRA-LAW-001 §7.4:

**INVALID**: The decision or action has no legal effect within the system.

**REJECTED**: The attempted change is nullified. Prior state persists.

---

## 6. AI Interaction Rules

### 6.1 Permitted AI Actions

AI MAY:
- Read decision records
- Detect potential conflicts between decisions
- Flag potential gaps in decision coverage
- Generate advisory warnings
- Produce analysis for human review

### 6.2 Prohibited AI Actions

AI MUST NOT:
- Create decision_id values
- Assign group_id values
- Assign feature_id values
- Write statement content
- Write rationale content
- Write constraint content
- Write invariant content
- Change status values
- Approve decisions
- Reject decisions
- Finalize decisions
- Imply approval through language
- Override human determinations

### 6.3 Disposition of AI Output

AI output that contradicts MANTRA-LAW-001 MUST be discarded.

AI output that implies decision authority MUST be discarded.

AI output that finalizes a decision MUST be discarded.

Human review of AI output does not transfer authority to AI.

AI output remains advisory unless explicitly adopted by human action.

---

## 7. Explicit Non-Goals

Decision Schema v1 intentionally does NOT define:

- Runtime enforcement logic
- Policy evaluation algorithms
- Workflow automation sequences
- Approval routing mechanisms
- Notification or alerting systems
- User interface presentation
- Data persistence mechanisms
- API contracts for schema consumption
- Event emission patterns
- Authentication requirements
- Authorization mechanisms
- Audit logging requirements
- Decision precedence rules between records
- Conflict resolution procedures
- Escalation procedures
- Rollback mechanisms
- Migration procedures
- Versioning strategies beyond format
- Inter-system communication protocols
- Error handling behavior
- Recovery procedures

These concerns belong in higher-layer specifications, not in the structural schema.

---

**END OF DOCUMENT**
