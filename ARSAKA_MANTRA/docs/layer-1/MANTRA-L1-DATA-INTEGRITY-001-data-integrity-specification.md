# MANTRA-L1-DATA-INTEGRITY-001: Data Integrity Specification

**TYPE**: Implementation Specification
**STATUS**: Active
**VERSION**: 1.0.0
**DATE**: 2025-01-25
**LAYER**: 1 (Implementation)

---

## 1. Purpose

This specification defines data integrity mechanisms for the ARSAKA_MANTRA Decision Store, ensuring:

1. **Supersedes chain validity** - No orphaned pointers, no circular references
2. **Typed audit metadata** - Consistent, queryable audit trail structure
3. **Explicit error handling** - No silent failures, all warnings visible
4. **ID continuity** - Decision IDs preserved between propose and store

---

## 2. Governing References

| Reference | Section | Requirement |
|-----------|---------|-------------|
| MANTRA-LAW-001 | §10 | Stored decisions MUST NOT be modified or deleted |
| MANTRA-LAW-001 | §6 | Human authority required for all decision operations |
| MANTRA-L1-IMPL-DECISION-STORE-001 | §3 | Write-once, append-only semantics |

---

## 3. Supersedes Chain Validation

### 3.1 Problem Statement

Without validation, the following data integrity issues can occur:

| Issue | Impact | Example |
|-------|--------|---------|
| Orphaned pointers | Broken version chain | Decision supersedes non-existent ID |
| Circular reference | Infinite traversal loop | A → B → C → A |
| Multiple supersedes | Ambiguous "current" version | Both X and Y supersede Z |

### 3.2 Validation Rules

Before storing a decision with `supersedes` set, the system MUST validate:

```
RULE-1: Target Existence
  IF decision.supersedes IS NOT NULL:
    THEN repository.find_by_id(decision.supersedes) MUST exist
    ERROR: "Supersedes target '{id}' not found"

RULE-2: No Circular Reference
  IF decision.supersedes IS NOT NULL:
    chain = repository.find_supersedes_chain(decision.supersedes)
    decision.decision_id MUST NOT be in chain
    ERROR: "Circular supersedes chain detected"

RULE-3: Unique Supersedes
  IF decision.supersedes IS NOT NULL:
    No other stored decision may have the same supersedes target
    ERROR: "Multiple decisions cannot supersede the same target"
```

### 3.3 Store Result

New store result for validation failures:

```python
class StoreResult(str, Enum):
    STORED = "STORED"              # Success
    ALREADY_EXISTS = "ALREADY_EXISTS"  # Immutability constraint
    STORE_ERROR = "STORE_ERROR"    # Technical/IO failure
    INVALID_SUPERSEDES = "INVALID_SUPERSEDES"  # Chain validation failed
```

### 3.4 HTTP Response Mapping

| StoreResult | HTTP Status | Description |
|-------------|-------------|-------------|
| STORED | 201 Created | Decision stored successfully |
| ALREADY_EXISTS | 409 Conflict | Decision ID already exists |
| INVALID_SUPERSEDES | 400 Bad Request | Supersedes chain invalid |
| STORE_ERROR | 500 Internal Server Error | Technical failure |

---

## 4. Typed Audit Metadata

### 4.1 Problem Statement

Unstructured `metadata: dict` makes audit entries hard to:
- Query by specific fields
- Validate at write time
- Present consistently in UI

### 4.2 Typed Metadata Models

Each audit event type has a corresponding metadata model:

#### ProposedMetadata (DECISION_PROPOSED)
```python
@dataclass
class ProposedMetadata:
    proposal_id: str         # Ephemeral proposal identifier
    validation_status: str   # VALID, INVALID, REJECTED
    violations_count: int    # Number of validation violations
    _metadata_type: str = "ProposedMetadata"
```

#### StoredMetadata (DECISION_STORED)
```python
@dataclass
class StoredMetadata:
    storage_version: int     # Always 1 for new decisions
    supersedes: Optional[str]  # ID of superseded decision
    version: str             # Semantic version
    _metadata_type: str = "StoredMetadata"
```

#### ChallengeMetadata (CHALLENGE_CREATED)
```python
@dataclass
class ChallengeMetadata:
    challenged_decision_id: str  # Original decision being challenged
    challenge_rationale: str     # Human explanation
    new_decision_id: str         # New superseding decision
    _metadata_type: str = "ChallengeMetadata"
```

#### CompareMetadata (DECISION_COMPARED)
```python
@dataclass
class CompareMetadata:
    compared_with: str         # Other decision ID
    differences_count: int     # Number of different fields
    is_supersedes_chain: bool  # Whether in same chain
    common_group: bool         # Same group_id
    common_feature: bool       # Same feature_id
    _metadata_type: str = "CompareMetadata"
```

#### ReadMetadata (DECISION_READ)
```python
@dataclass
class ReadMetadata:
    operation: str            # get, list, history, etc.
    chain_length: Optional[int]  # For history operation
    filters: Optional[dict]   # Applied filters
    _metadata_type: str = "ReadMetadata"
```

### 4.3 Metadata Type Identification

All typed metadata includes `_metadata_type` field for:
- Frontend type discrimination
- Query filtering
- Schema validation

---

## 5. Explicit Warning Handling

### 5.1 Problem Statement

Silent failures hide important information:
- Invalid `authorship_metadata` format → L-rules silently skipped
- No indication to user what was skipped

### 5.2 Solution: Warnings Field

ProposeResponse now includes explicit warnings:

```json
{
  "result": "READY",
  "proposal_id": "...",
  "decision_id": "...",
  "warnings": [
    "Invalid authorship_metadata format: field 'author_type' is required. L-rules (L-001 through L-008) will be skipped."
  ],
  "skipped_rules": ["L-001", "L-002", "L-003", "L-004", "L-005", "L-006", "L-007", "L-008"],
  "violations": [],
  "advisory_notes": [...]
}
```

### 5.3 Warning Sources

| Condition | Warning Message |
|-----------|-----------------|
| Invalid authorship_metadata | "Invalid authorship_metadata format: {error}. L-rules will be skipped." |
| Missing authorship_metadata | (No warning, but skipped_rules populated) |

---

## 6. Decision ID Continuity

### 6.1 Problem Statement

When using propose → store workflow:
1. `POST /decisions/propose` generates `decision_id`
2. `POST /decisions` generates NEW `decision_id`

This breaks traceability between proposal and stored decision.

### 6.2 Solution

StoreRequest now accepts optional `decision_id`:

```json
{
  "decision": {...},
  "stored_by": "human-user",
  "decision_id": "abc-123-from-propose"  // Optional
}
```

Behavior:
- If `decision_id` provided: Use it (must not already exist)
- If `decision_id` null: Generate new UUID

### 6.3 Workflow Example

```bash
# Step 1: Propose (get decision_id)
RESPONSE=$(curl -X POST /api/v1/decisions/propose -d '{"decision": {...}}')
DECISION_ID=$(echo $RESPONSE | jq -r '.decision_id')

# Step 2: Store with same ID
curl -X POST /api/v1/decisions -d '{
  "decision": {...},
  "stored_by": "human-user",
  "decision_id": "'$DECISION_ID'"
}'

# Result: Stored decision has same ID as proposed
```

---

## 7. API Changes Summary

### 7.1 New/Modified Request Fields

| Endpoint | Field | Type | Description |
|----------|-------|------|-------------|
| POST /decisions | decision_id | Optional[str] | Preserve ID from propose |

### 7.2 New/Modified Response Fields

| Endpoint | Field | Type | Description |
|----------|-------|------|-------------|
| POST /decisions/propose | warnings | List[str] | Explicit warnings |
| POST /decisions/propose | skipped_rules | List[str] | Rules skipped |
| POST /decisions | result | Enum | Now includes INVALID_SUPERSEDES |
| GET /audit | metadata._metadata_type | str | Identifies metadata type |

---

## 8. Data Flow Diagrams

### 8.1 Propose Flow (After Fixes)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Request                                                             │
│  ├── decision: DecisionCreate                                       │
│  ├── proposed_by: str                                               │
│  └── authorship_metadata: Optional[Dict]                            │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────────────────────────────┐                        │
│  │ Parse authorship_metadata               │                        │
│  │ ├── Success: authorship = parsed        │                        │
│  │ └── Failure: warnings += error message  │ ◄── EXPLICIT           │
│  └─────────────────────────────────────────┘                        │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────────────────────────────┐                        │
│  │ propose_decision()                       │                        │
│  │ 1. Generate proposal_id + decision_id   │                        │
│  │ 2. Create Decision object               │                        │
│  │ 3. Validate (with authorship if valid)  │                        │
│  │ 4. Record DECISION_PROPOSED audit       │ ◄── Typed metadata     │
│  └─────────────────────────────────────────┘                        │
│           │                                                          │
│           ▼                                                          │
│  Response                                                            │
│  ├── result: READY | INVALID                                        │
│  ├── proposal_id: str                                               │
│  ├── decision_id: str  ◄───────────── PRESERVED for store           │
│  ├── warnings: List[str]  ◄───────── NEW: explicit warnings         │
│  └── skipped_rules: List[str]  ◄──── NEW: rules not applied         │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Store Flow (After Fixes)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Request                                                             │
│  ├── decision: DecisionCreate                                       │
│  ├── stored_by: str                                                 │
│  └── decision_id: Optional[str]  ◄─────────── NEW: from propose     │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────────────────────────────┐                        │
│  │ 1. Use decision_id OR generate new      │                        │
│  │ 2. Check already exists (immutability)  │                        │
│  │ 3. Validate supersedes chain  ◄─────────│ NEW: data integrity    │
│  │    ├── Target exists?                   │                        │
│  │    ├── No circular reference?           │                        │
│  │    └── No duplicate supersedes?         │                        │
│  │ 4. Store if all checks pass             │                        │
│  │ 5. Record DECISION_STORED audit         │ ◄── Typed metadata     │
│  └─────────────────────────────────────────┘                        │
│           │                                                          │
│           ▼                                                          │
│  Response                                                            │
│  ├── result: STORED | ALREADY_EXISTS | INVALID_SUPERSEDES | ERROR   │
│  ├── decision_id: str                                               │
│  └── stored_at: datetime                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Frontend Type Definitions

### 9.1 TypeScript Interfaces

```typescript
// Typed audit metadata
interface ProposedMetadata {
  _metadata_type: 'ProposedMetadata'
  proposal_id: string
  validation_status: string
  violations_count: number
}

interface StoredMetadata {
  _metadata_type: 'StoredMetadata'
  storage_version: number
  supersedes: string | null
  version: string
}

interface ChallengeMetadata {
  _metadata_type: 'ChallengeMetadata'
  challenged_decision_id: string
  challenge_rationale: string
  new_decision_id: string | null
}

// ProposeResponse with warnings
interface ProposeResponse {
  result: 'READY' | 'INVALID'
  proposal_id: string
  decision_id: string
  warnings: string[]        // NEW
  skipped_rules: string[]   // NEW
  violations: Violation[]
  // ...
}

// Store function with decision_id
store: async (
  decision: DecisionCreate,
  storedBy: string,
  decisionId?: string  // NEW: preserve from propose
) => StoreResponse
```

---

## 10. Verification Checklist

### 10.1 Supersedes Chain Validation

- [ ] Store with non-existent supersedes → 400 INVALID_SUPERSEDES
- [ ] Store creating circular reference → 400 INVALID_SUPERSEDES
- [ ] Store with duplicate supersedes → 400 INVALID_SUPERSEDES
- [ ] Store with valid supersedes → 201 STORED

### 10.2 Typed Audit Metadata

- [ ] DECISION_PROPOSED has ProposedMetadata
- [ ] DECISION_STORED has StoredMetadata
- [ ] CHALLENGE_CREATED has ChallengeMetadata
- [ ] DECISION_COMPARED has CompareMetadata
- [ ] DECISION_READ has ReadMetadata
- [ ] All metadata has _metadata_type field

### 10.3 Warning Handling

- [ ] Invalid authorship_metadata → warnings populated
- [ ] Skipped L-rules → skipped_rules populated
- [ ] Frontend displays warnings

### 10.4 Decision ID Continuity

- [ ] Propose returns decision_id
- [ ] Store accepts decision_id
- [ ] Stored decision has same ID as proposed

---

## 11. Implementation Status

| Component | File | Status |
|-----------|------|--------|
| Supersedes validation | `store_decision.py` | ✅ Implemented |
| Typed metadata models | `decision.py` | ✅ Implemented |
| Warning handling | `routes.py` | ✅ Implemented |
| Decision ID continuity | `routes.py` | ✅ Implemented |
| Frontend types | `api.ts` | ✅ Implemented |

---

## 12. Appendix: Test Commands

```bash
# Test 1: Supersedes chain validation (non-existent)
curl -X POST http://localhost:8002/api/v1/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "decision": {
      "group_id": "GROUP-1",
      "feature_id": "F-01",
      "statement": "Test",
      "rationale": "Test",
      "constraints": [],
      "invariants": [],
      "scope": "APPLICATION",
      "blast_radius": "LOW",
      "version": "1.0.0",
      "created_by": "test-user",
      "supersedes": "non-existent-id"
    },
    "stored_by": "test-user"
  }'
# Expected: 400 "Supersedes target 'non-existent-id' not found"

# Test 2: Warning handling (invalid authorship)
curl -X POST http://localhost:8002/api/v1/decisions/propose \
  -H "Content-Type: application/json" \
  -d '{
    "decision": {...},
    "proposed_by": "human",
    "authorship_metadata": {"invalid": "format"}
  }'
# Expected: Response includes "warnings" with parse error

# Test 3: Decision ID continuity
PROPOSE=$(curl -X POST http://localhost:8002/api/v1/decisions/propose -d '...')
DECISION_ID=$(echo $PROPOSE | jq -r '.decision_id')

curl -X POST http://localhost:8002/api/v1/decisions \
  -d "{\"decision\": {...}, \"stored_by\": \"human\", \"decision_id\": \"$DECISION_ID\"}"

curl http://localhost:8002/api/v1/decisions/$DECISION_ID
# Expected: Decision exists with same ID
```

---

**Document End**
