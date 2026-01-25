# EXAMPLE-G4-001: API Versioning Strategy

> **Example Decision**: Copy and adapt for your organization.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `EXAMPLE-G4-001` |
| **group_id** | GROUP-4 (Execution & Evolution) |
| **feature_id** | F-15 (Environment & Promotion Rules) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | HIGH |
| **created_by** | [Your Name] |
| **created_at** | [Date] |
| **supersedes** | null |

---

## Statement

**All public APIs MUST use URL versioning with format `/api/v{major}/`. Breaking changes require major version increment.**

---

## Rationale

URL versioning with major-only in URL because:

1. **Explicit**: Version is visible in every request. No header inspection needed.

2. **Cacheable**: CDNs and proxies can cache by URL. Header versioning breaks caching.

3. **Debuggable**: Support can see version in logs, URLs, error reports.

4. **Client Friendly**: Simple to implement in any HTTP client. No special headers.

5. **Breaking Change Clarity**: Major version in URL signals "this might break." Minor/patch changes are backwards-compatible.

---

## Versioning Rules

### What Constitutes Breaking Change (Major Version)

| Change Type | Breaking? | Example |
|-------------|-----------|---------|
| Remove field | YES | Remove `customer.middle_name` |
| Rename field | YES | `customer_id` → `customerId` |
| Change field type | YES | `amount: string` → `amount: number` |
| Add required field | YES | New required `tenant_id` parameter |
| Change endpoint path | YES | `/users` → `/customers` |
| Change auth method | YES | API key → OAuth |

### Non-Breaking Changes (Minor/Patch)

| Change Type | Breaking? | Example |
|-------------|-----------|---------|
| Add optional field | NO | Add `customer.nickname` |
| Add new endpoint | NO | Add `GET /customers/{id}/preferences` |
| Add optional parameter | NO | Add `?include_deleted=true` |
| Fix bug (same contract) | NO | Fix calculation error |
| Performance improvement | NO | Faster response time |

---

## URL Structure

```
Public APIs:
https://api.example.com/api/v1/customers
https://api.example.com/api/v2/customers

Internal APIs (optional versioning):
https://internal.example.com/customers

Pattern:
/api/v{major}/{resource}

Examples:
GET  /api/v1/customers
GET  /api/v1/customers/{id}
POST /api/v1/customers
GET  /api/v2/customers        # Breaking changes from v1
```

---

## Constraints

### PROHIBITION
1. **P-001**: Breaking changes MUST NOT be introduced without major version increment
2. **P-002**: API versions MUST NOT be removed without deprecation process
3. **P-003**: Version numbers MUST NOT decrease (no v2 → v1 regression)
4. **P-004**: Header-based versioning MUST NOT be used for public APIs

### REQUIREMENT
1. **R-001**: All public APIs MUST include version in URL path
2. **R-002**: Breaking changes MUST increment major version
3. **R-003**: API documentation MUST reflect current version
4. **R-004**: Changelog MUST document all version changes

### LIMITATION
1. **L-001**: Maximum 3 major versions supported simultaneously
2. **L-002**: Internal APIs may use unversioned paths

---

## Invariants

These properties are ALWAYS true:

1. Version number in public API URLs
2. Major version increments for breaking changes
3. Backwards compatibility within same major version
4. Deprecation notice before version removal

---

## Implementation Reference

### Router Configuration

```python
from fastapi import APIRouter

# Version 1 routes
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/customers")
async def list_customers_v1():
    return {"customers": [...]}

# Version 2 routes (breaking changes)
v2_router = APIRouter(prefix="/api/v2")

@v2_router.get("/customers")
async def list_customers_v2():
    # New response format
    return {"data": [...], "meta": {...}}

# Register both versions
app.include_router(v1_router)
app.include_router(v2_router)
```

### Version Header (Informational)

```python
@app.middleware("http")
async def add_version_header(request, call_next):
    response = await call_next(request)
    # Informational header (not for routing)
    response.headers["X-API-Version"] = "1.2.3"
    return response
```

### OpenAPI Documentation

```yaml
openapi: 3.0.0
info:
  title: Customer API
  version: "1.2.3"
servers:
  - url: https://api.example.com/api/v1
    description: Version 1 (current)
  - url: https://api.example.com/api/v2
    description: Version 2 (beta)
```

---

## Version Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Version Lifecycle                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   v1 ─────────────────────────────────────────────────► EOL    │
│   │  CURRENT        MAINTAINED       DEPRECATED                 │
│   │  (18 months)    (12 months)      (6 months)                │
│   │                                                             │
│   └──► v2 ──────────────────────────────────────────► ...      │
│        │  CURRENT        MAINTAINED       DEPRECATED            │
│        │                                                        │
│        └──► v3 ─────────────────────────────► ...              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Timeline Example:
v1: 2024-01 → 2025-06 (CURRENT) → 2026-06 (MAINTAINED) → 2027-01 (EOL)
v2: 2025-06 → 2027-01 (CURRENT) → ...
```

---

## Client Migration Support

### Deprecation Headers

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: </api/v2/customers>; rel="successor-version"
```

### Migration Guide Template

```markdown
# Migrating from v1 to v2

## Breaking Changes
1. Response format changed from `{customers: [...]}` to `{data: [...], meta: {...}}`
2. `customer_id` renamed to `id`
3. Pagination now required for list endpoints

## Migration Steps
1. Update response parsing to use `data` field
2. Update field references: `customer_id` → `id`
3. Add pagination parameters to list calls

## Timeline
- v2 available: 2025-06-01
- v1 deprecated: 2026-06-01
- v1 sunset: 2027-01-01
```

---

## Related Decisions

- EXAMPLE-G4-002: Deprecation Policy (defines how versions are retired)
- EXAMPLE-G2-001: Service Boundary (API is service interface)
- [Future]: API Design Standards (GROUP-2/F-08)

---

## Evolution Path

Versioning strategy may evolve when:
- Client requirements change
- New versioning patterns emerge
- Scale requires different approach

Example evolution:
```
v1.0.0: "URL versioning with major only"
v1.1.0: "URL versioning + optional minor in Accept header"
v2.0.0: "GraphQL primary, REST versioned for legacy"
```

---

## Template Notes

**When adapting this example:**

1. Define what constitutes breaking vs non-breaking change
2. Specify URL pattern for your organization
3. Document version lifecycle (how long supported)
4. Include client migration support
5. Show implementation in your framework
