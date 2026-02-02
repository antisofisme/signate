# GUIDE-002: API Reference

**TYPE**: Developer Guide
**STATUS**: Active
**VERSION**: 2.0.0
**DATE**: 2025-01-25

---

## Base URL

```
Production: http://31.97.111.175:8002/api/v1
Local:      http://localhost:8002/api/v1
```

---

## Authentication

Currently, ARSAKA_MANTRA does not require authentication. All endpoints are public.

Human identity is tracked via `stored_by`, `proposed_by`, `challenger`, and `actor` fields in requests.

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/validate` | Validate a decision |
| POST | `/decisions/propose` | Propose a decision (validate without storing) |
| POST | `/decisions` | Store a decision |
| GET | `/decisions` | List all decisions |
| GET | `/decisions/{id}` | Get single decision |
| POST | `/decisions/{id}/challenge` | Challenge a decision |
| GET | `/decisions/{id}/compare/{other_id}` | Compare two decisions |
| GET | `/decisions/{id}/history` | Get version chain |
| GET | `/grouped` | Get decisions grouped by group/feature |
| GET | `/audit` | List audit entries |

---

## Endpoint Details

### 1. Health Check

```
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "ARSAKA_MANTRA",
  "version": "1.0.0",
  "timestamp": "2025-01-25T10:30:00Z"
}
```

---

### 2. Validate Decision

Validates a decision record against MANTRA-SCHEMA-001 and MANTRA-SPEC-001 without storing.

```
POST /validate
```

**Request Body**:
```json
{
  "record": {
    "group_id": "GROUP-1",
    "feature_id": "F-01",
    "statement": "All API endpoints must use versioned paths",
    "rationale": "Ensures backward compatibility",
    "constraints": [
      {
        "constraint_id": "C-001",
        "statement": "Version format: /v{major}",
        "type": "REQUIREMENT"
      }
    ],
    "invariants": ["Version number only increases"],
    "scope": "ORGANIZATION",
    "blast_radius": "HIGH",
    "version": "1.0.0",
    "created_by": "architect-team"
  },
  "authorship_metadata": {
    "author_type": "human",
    "author_identifier": "john.doe@company.com",
    "timestamp": "2025-01-25T10:00:00Z",
    "is_approval": false
  }
}
```

**Response** (200 OK):
```json
{
  "status": "VALID",
  "violations": [],
  "skipped_rules": [],
  "advisory_notes": ["Decision meets all schema requirements"],
  "validated_at": "2025-01-25T10:30:00Z",
  "schema_version": "1.0.0",
  "specification_version": "1.0.0"
}
```

**Note**: If `authorship_metadata` is invalid or missing, L-rules (L-001 through L-008) are skipped and noted in `advisory_notes`.

---

### 3. Propose Decision *(New in v2)*

Validates a decision and prepares it for storage WITHOUT storing. Returns a `decision_id` that can be used when storing.

```
POST /decisions/propose
```

**Request Body**:
```json
{
  "decision": {
    "group_id": "GROUP-1",
    "feature_id": "F-01",
    "statement": "All API endpoints must use versioned paths",
    "rationale": "Ensures backward compatibility",
    "constraints": [],
    "invariants": [],
    "scope": "ORGANIZATION",
    "blast_radius": "HIGH",
    "version": "1.0.0",
    "created_by": "architect-team"
  },
  "proposed_by": "john.doe@company.com",
  "authorship_metadata": {
    "author_type": "human",
    "author_identifier": "john.doe@company.com",
    "timestamp": "2025-01-25T10:00:00Z",
    "is_approval": false
  }
}
```

**Response** (200 OK):
```json
{
  "result": "READY",
  "proposal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "decision_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef",
  "decision": {
    "decision_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef",
    "group_id": "GROUP-1",
    "feature_id": "F-01",
    "statement": "All API endpoints must use versioned paths",
    "...": "..."
  },
  "validation_status": "VALID",
  "violations": [],
  "advisory_notes": ["Decision is valid and ready to store."],
  "warnings": [],
  "skipped_rules": ["L-001", "L-002", "L-003", "L-004", "L-005", "L-006", "L-007", "L-008"],
  "proposed_at": "2025-01-25T10:30:00Z"
}
```

**New Fields (v2)**:
- `warnings`: Explicit warnings about parsing failures (e.g., invalid authorship_metadata)
- `skipped_rules`: Rules that were not applied (e.g., L-rules when authorship missing)

**Result Values**:
- `READY`: Decision is valid, can be stored
- `INVALID`: Validation failed, see `violations`

---

### 4. Store Decision *(Updated in v2)*

Stores a validated decision immutably.

```
POST /decisions
```

**Request Body**:
```json
{
  "decision": {
    "group_id": "GROUP-1",
    "feature_id": "F-01",
    "statement": "All API endpoints must use versioned paths",
    "rationale": "Ensures backward compatibility",
    "constraints": [],
    "invariants": [],
    "scope": "ORGANIZATION",
    "blast_radius": "HIGH",
    "version": "1.0.0",
    "created_by": "architect-team",
    "supersedes": null
  },
  "stored_by": "john.doe@company.com",
  "decision_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef"
}
```

**New Field (v2)**:
- `decision_id` (optional): If provided (from propose), uses this ID instead of generating new one

**Response** (201 Created):
```json
{
  "result": "STORED",
  "decision_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef",
  "stored_at": "2025-01-25T10:31:00Z"
}
```

**Error Responses**:

| Status | Result | Description |
|--------|--------|-------------|
| 400 | INVALID_SUPERSEDES | Supersedes chain validation failed |
| 409 | ALREADY_EXISTS | Decision ID already exists |
| 500 | STORE_ERROR | Technical failure |

**Example Error (400 Bad Request)**:
```json
{
  "detail": "Supersedes target 'abc-123' not found. Cannot supersede a non-existent decision."
}
```

**Supersedes Validation (New in v2)**:
When `supersedes` is set, the system validates:
1. Target decision exists
2. No circular reference in chain
3. No other decision already supersedes the same target

---

### 5. List Decisions

Returns all stored decisions with pagination.

```
GET /decisions?limit=100&offset=0&group_id=GROUP-1
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 100 | Max results (1-1000) |
| offset | int | 0 | Pagination offset |
| group_id | string | null | Filter by group |

**Response** (200 OK):
```json
{
  "decisions": [
    {
      "decision_id": "...",
      "group_id": "GROUP-1",
      "feature_id": "F-01",
      "statement": "...",
      "rationale": "...",
      "constraints": [
        {
          "constraint_id": "C-001",
          "statement": "...",
          "type": "REQUIREMENT"
        }
      ],
      "invariants": ["..."],
      "scope": "ORGANIZATION",
      "blast_radius": "HIGH",
      "version": "1.0.0",
      "created_by": "...",
      "created_at": "2025-01-25T10:30:00Z",
      "approved_by": null,
      "approved_at": null,
      "supersedes": null,
      "related_decisions": []
    }
  ],
  "total_count": 1,
  "limit": 100,
  "offset": 0
}
```

---

### 6. Get Single Decision

```
GET /decisions/{decision_id}
```

**Response** (200 OK):
```json
{
  "decision_id": "...",
  "group_id": "GROUP-1",
  "...": "..."
}
```

**Error** (404 Not Found):
```json
{
  "detail": "Decision abc-123 not found"
}
```

---

### 7. Challenge Decision

Creates a new decision that supersedes the challenged one. The challenged decision remains immutable.

```
POST /decisions/{decision_id}/challenge
```

**Request Body**:
```json
{
  "challenger": "jane.doe@company.com",
  "challenge_rationale": "Original decision too restrictive for microservices",
  "proposed_replacement": {
    "group_id": "GROUP-1",
    "feature_id": "F-01",
    "statement": "API versioning required for public endpoints only",
    "rationale": "Internal services can use latest version",
    "constraints": [],
    "invariants": [],
    "scope": "ORGANIZATION",
    "blast_radius": "MEDIUM",
    "version": "2.0.0",
    "created_by": "jane.doe@company.com"
  }
}
```

**Response** (201 Created):
```json
{
  "result": "STORED",
  "challenged_decision_id": "original-uuid",
  "new_decision_id": "new-uuid",
  "stored_at": "2025-01-25T11:00:00Z"
}
```

**Note**: The new decision automatically has:
- `supersedes` = challenged decision ID
- `related_decisions` includes challenged decision ID

---

### 8. Compare Decisions

Compares two decisions side-by-side.

```
GET /decisions/{decision_id}/compare/{other_decision_id}?actor=john.doe
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| actor | string | Yes | Human identifier performing comparison |

**Response** (200 OK):
```json
{
  "result": "COMPARABLE",
  "decision_a": { "decision_id": "...", "...": "..." },
  "decision_b": { "decision_id": "...", "...": "..." },
  "differences": [
    {
      "field_name": "statement",
      "value_a": "Original statement",
      "value_b": "Updated statement",
      "change_type": "modified"
    },
    {
      "field_name": "constraint:C-002",
      "value_a": null,
      "value_b": { "...": "..." },
      "change_type": "added"
    }
  ],
  "is_supersedes_chain": true,
  "supersedes_direction": "b_supersedes_a",
  "common_group": true,
  "common_feature": true,
  "error_message": null
}
```

**Result Values**:
- `COMPARABLE`: Both decisions found
- `NOT_FOUND_A`: First decision not found
- `NOT_FOUND_B`: Second decision not found
- `NOT_FOUND_BOTH`: Neither found
- `ERROR`: Technical error

**Change Types**:
- `modified`: Value changed
- `added`: Field added in B
- `removed`: Field removed in B

---

### 9. Get Decision History

Returns the complete supersedes chain for a decision.

```
GET /decisions/{decision_id}/history?actor=john.doe
```

**Response** (200 OK):
```json
{
  "result": "COMPARABLE",
  "decision_id": "current-uuid",
  "chain": [
    { "decision_id": "oldest-uuid", "version": "1.0.0", "...": "..." },
    { "decision_id": "middle-uuid", "version": "1.1.0", "supersedes": "oldest-uuid", "...": "..." },
    { "decision_id": "current-uuid", "version": "2.0.0", "supersedes": "middle-uuid", "...": "..." }
  ],
  "total_versions": 3,
  "error_message": null
}
```

**Note**: Chain is ordered from oldest to newest.

---

### 10. Get Grouped Decisions

Returns all decisions grouped by group_id and feature_id.

```
GET /grouped
```

**Response** (200 OK):
```json
{
  "grouped": {
    "GROUP-1": {
      "F-01": [
        { "decision_id": "...", "...": "..." },
        { "decision_id": "...", "...": "..." }
      ],
      "F-02": [...]
    },
    "GROUP-2": {...}
  },
  "generated_at": "2025-01-25T10:30:00Z"
}
```

---

### 11. List Audit Entries

Returns audit trail with optional filtering.

```
GET /audit?limit=100&offset=0&event_type=DECISION_STORED&actor=john.doe
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 100 | Max results (1-1000) |
| offset | int | 0 | Pagination offset |
| decision_id | string | null | Filter by decision |
| event_type | string | null | Filter by event type |
| actor | string | null | Filter by actor |

**Event Types**:
- `DECISION_PROPOSED`
- `DECISION_VALIDATED`
- `DECISION_STORED`
- `DECISION_READ`
- `DECISION_COMPARED`
- `CHALLENGE_CREATED`

**Response** (200 OK):
```json
{
  "result": "RETRIEVED",
  "entries": [
    {
      "event_id": "event-uuid",
      "event_type": "DECISION_STORED",
      "actor": "john.doe@company.com",
      "actor_type": "human",
      "decision_id": "decision-uuid",
      "timestamp": "2025-01-25T10:31:00Z",
      "metadata": {
        "_metadata_type": "StoredMetadata",
        "storage_version": 1,
        "supersedes": null,
        "version": "1.0.0"
      }
    }
  ],
  "total_count": 1,
  "limit": 100,
  "offset": 0,
  "error_message": null
}
```

**Typed Metadata (New in v2)**:

Each event type has structured metadata with `_metadata_type` identifier:

| Event Type | Metadata Type | Fields |
|------------|---------------|--------|
| DECISION_PROPOSED | ProposedMetadata | proposal_id, validation_status, violations_count |
| DECISION_STORED | StoredMetadata | storage_version, supersedes, version |
| CHALLENGE_CREATED | ChallengeMetadata | challenged_decision_id, challenge_rationale, new_decision_id |
| DECISION_COMPARED | CompareMetadata | compared_with, differences_count, is_supersedes_chain, common_group, common_feature |
| DECISION_READ | ReadMetadata | operation, chain_length, filters |

---

## Common Types

### Constraint

```json
{
  "constraint_id": "C-001",
  "statement": "Description of the constraint",
  "type": "REQUIREMENT"
}
```

**Constraint Types**:
- `PROHIBITION`: Something that MUST NOT happen
- `REQUIREMENT`: Something that MUST happen
- `LIMITATION`: A bounded condition

### Group IDs

- `GROUP-1`: Intent & Direction (WHY/WHAT)
- `GROUP-2`: Architecture & Boundaries (HOW/WHERE)
- `GROUP-3`: Control, Policy & Risk (CAN/MUST NOT)
- `GROUP-4`: Execution & Evolution (CHANGE SAFELY)

### Feature IDs

| Group | Features |
|-------|----------|
| GROUP-1 | F-01, F-02, F-03, F-04 |
| GROUP-2 | F-05, F-06, F-07, F-08 |
| GROUP-3 | F-09, F-10, F-11, F-12 |
| GROUP-4 | F-13, F-14, F-15, F-16 |

### Scope

- `ORGANIZATION`: Applies to entire organization
- `DOMAIN`: Applies to specific domain
- `APPLICATION`: Applies to specific application

### Blast Radius

- `LOW`: Limited impact
- `MEDIUM`: Moderate impact
- `HIGH`: Significant impact
- `CRITICAL`: Critical impact

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 500 | Internal Server Error - Technical failure |

---

## Changelog

### v2.0.0 (2025-01-25)
- Added `warnings` and `skipped_rules` to ProposeResponse
- Added `decision_id` parameter to StoreRequest
- Added `INVALID_SUPERSEDES` store result
- Added supersedes chain validation
- Added typed audit metadata with `_metadata_type`

### v1.0.0 (Initial)
- Basic CRUD operations
- Validation endpoint
- Audit trail

---

**Document End**
