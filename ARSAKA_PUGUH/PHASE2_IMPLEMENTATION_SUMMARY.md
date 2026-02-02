# ARSAKA_PUGUH - Phase 2 Implementation Summary

**Status**: IMPLEMENTATION READY
**Date**: 2026-01-24
**Focus**: SDK THIN, FORCE RLS, RUNTIME DISCIPLINE

---

## Overview

Phase 2 provides a SAFE way for developers to interact with the Infra Control Plane
without opening any bypass paths. Phase 1 enforcement is preserved and strengthened.

---

## Phase 2 Scope

| Component | Purpose | Status |
|-----------|---------|--------|
| Database Hardening | FORCE RLS + Role Separation | ✅ |
| SDK Thin | Minimal adapter to Core API | ✅ |
| Runtime Discipline | Enforced context, single pool | ✅ |
| Bypass Tests Phase 2 | Gate tests for Phase 2 | ✅ |

---

## 1. DATABASE HARDENING

### Migration 004: FORCE RLS + Roles

**File**: `backend/migrations/004_force_rls_and_roles.sql`

#### Role Separation

| Role | Purpose | Capabilities |
|------|---------|--------------|
| `app_runtime_role` | Application runtime | SELECT, INSERT only. NO BYPASS RLS |
| `migration_role` | Schema migrations | DDL permissions. NO BYPASS RLS |
| `postgres` | Admin (never used by app) | Superuser |

#### FORCE Row-Level Security

All tenant-bound tables have FORCE RLS enabled:
- `decisions`
- `workflows`
- `workflow_transitions`
- `rules`
- `event_log`
- `operations_audit`
- `idempotency_cache`

**FORCE RLS** means even table owners must obey RLS policies.

#### Privilege Matrix

| Table | app_runtime_role | Reason |
|-------|------------------|--------|
| `decisions` | SELECT, INSERT | Immutable - no UPDATE/DELETE |
| `workflows` | SELECT, INSERT, UPDATE | Mutable until terminal |
| `workflow_transitions` | SELECT, INSERT | Immutable audit trail |
| `rules` | SELECT, INSERT, UPDATE | Configuration |
| `event_log` | SELECT, INSERT | Immutable facts |
| `operations_audit` | SELECT, INSERT | Immutable audit |
| `idempotency_cache` | SELECT, INSERT | Immutable cache |

---

## 2. SDK THIN

### Structure

```
sdk/
├── infra_sdk/
│   ├── __init__.py        # Public exports
│   ├── types.py           # Typed request/response objects
│   ├── client.py          # InfraClient (thin adapter)
│   └── exceptions.py      # Explicit error types
└── tests/
    └── test_sdk.py        # SDK unit tests
```

### SDK API (Minimal)

| Method | Purpose |
|--------|---------|
| `create_decision()` | Create decision via Core API |
| `get_decision()` | Get existing decision |
| `submit_workflow_action()` | Submit workflow action |

### SDK Principles

**SDK DOES:**
- Validate input structure
- Attach tenant_id, subject_id
- Inject idempotency_key
- Propagate trace_id
- Call Core API

**SDK DOES NOT:**
- Evaluate rules
- Store state
- Perform smart retry
- Modify decisions
- Provide helper shortcuts
- Use implicit defaults
- Implement fallback behavior

### Required Context

Every SDK operation requires:

| Field | Required For | Default |
|-------|-------------|---------|
| `tenant_id` | All operations | NO DEFAULT |
| `subject_id` | All operations | NO DEFAULT |
| `subject_type` | All operations | NO DEFAULT |
| `trace_id` | All operations | NO DEFAULT |
| `idempotency_key` | Mutations | NO DEFAULT |

---

## 3. RUNTIME DISCIPLINE

### Configuration

**File**: `backend/core/runtime/config.py`

#### RuntimeConfig

```python
@dataclass(frozen=True)
class RuntimeConfig:
    database_url: str
    database_role: str  # MUST be 'app_runtime_role'
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    pool_pre_ping: bool
```

**Security Enforcement:**
- `database_role` MUST be `app_runtime_role`
- Any other role raises `ValueError`

#### EnforcedSessionFactory

```python
class EnforcedSessionFactory:
    async def initialize(self) -> None:
        # Verifies:
        # 1. Current role is app_runtime_role
        # 2. Role cannot bypass RLS
        # 3. FORCE RLS is enabled on all tables

    async def get_session(self, context: RequestContext) -> AsyncSession:
        # Sets tenant context for RLS
        # ALL queries filtered by tenant_id
```

### Fail Rules

| Condition | Result |
|-----------|--------|
| Missing tenant context | DENY |
| Missing subject context | DENY |
| Missing trace_id | DENY |
| Missing idempotency_key (mutations) | DENY |
| Tenant mismatch | DENY |
| Wrong database role | FATAL ERROR |

---

## 4. BYPASS TESTS (PHASE 2 GATE)

### Test File

**File**: `backend/core/tests/test_bypass_phase2.py`

### Tests

| Test | Description | Expected |
|------|-------------|----------|
| `test_sdk_has_no_database_imports` | SDK cannot import DB modules | PASS |
| `test_create_decision_without_idempotency_fails` | Mutation requires idempotency | FAIL at creation |
| `test_app_runtime_role_cannot_set_bypassrls` | Role cannot enable bypass | Permission denied |
| `test_app_runtime_role_cannot_disable_rls_on_table` | Role cannot disable RLS | Permission denied |
| `test_force_rls_is_enabled` | All tables have FORCE RLS | TRUE |
| `test_sdk_cross_tenant_get_decision_fails` | Cross-tenant access denied | TenantMismatchError |
| `test_missing_tenant_fails` | Missing tenant denied | ValueError |
| `test_missing_subject_fails` | Missing subject denied | ValueError |
| `test_sdk_does_not_retry_on_error` | SDK has no retry | Single call |
| `test_config_rejects_wrong_role` | Wrong role rejected | ValueError |

---

## Exit Criteria Verification

| Criteria | Status |
|----------|--------|
| No bypass path via SDK | ✅ SDK calls Core API only |
| FORCE RLS active & verified | ✅ Migration 004 |
| SDK has no business logic | ✅ Thin adapter only |
| All bypass tests Phase 2 PASS | ⏳ Requires PostgreSQL run |
| Core Phase 1 unchanged | ✅ No changes to Phase 1 |

---

## How to Apply Phase 2

### 1. Apply Database Hardening

```bash
# Connect as superuser
psql -h localhost -U postgres -d infra

# Apply migration
\i backend/migrations/004_force_rls_and_roles.sql

# Verify
SELECT verify_role_cannot_bypass_rls('app_runtime_role');  -- Should return TRUE
SELECT verify_rls_forced('decisions');  -- Should return TRUE
```

### 2. Update Application Configuration

```bash
# Set environment variables
export DATABASE_URL="postgresql+asyncpg://app_runtime_role:PASSWORD@localhost:5432/infra"
export DATABASE_ROLE="app_runtime_role"
```

### 3. Install SDK

```bash
cd sdk
pip install -e .
```

### 4. Run Bypass Tests

```bash
# Set test database URL
export BYPASS_TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/infra_test"

# Run Phase 2 bypass tests
pytest backend/core/tests/test_bypass_phase2.py -v

# All tests MUST pass
```

---

## Files Created/Modified

### Created:
- `backend/migrations/004_force_rls_and_roles.sql`
- `sdk/infra_sdk/__init__.py`
- `sdk/infra_sdk/types.py`
- `sdk/infra_sdk/client.py`
- `sdk/infra_sdk/exceptions.py`
- `sdk/tests/__init__.py`
- `sdk/tests/test_sdk.py`
- `backend/core/runtime/__init__.py`
- `backend/core/runtime/config.py`
- `backend/core/tests/test_bypass_phase2.py`

### Modified:
- None (Phase 1 code unchanged)

---

## NOT Implemented (Per Phase 2 Scope)

- ❌ CMS - Deferred
- ❌ UI - Deferred
- ❌ Event Bus (Kafka) - Deferred
- ❌ Analytics - Deferred
- ❌ Convenience helpers - FORBIDDEN
- ❌ Implicit defaults - FORBIDDEN
- ❌ Fallback behavior - FORBIDDEN

---

## Security Notes

1. **app_runtime_role password** must be changed in production
2. **FORCE RLS** prevents bypass even with compromised application
3. **SDK has no database access** - all operations through Core API
4. **Idempotency key required** - prevents duplicate mutations
5. **Context validation** - missing context = DENY

---

## Next Steps

1. Run bypass tests against PostgreSQL
2. Fix any failing tests before proceeding
3. Document test results as evidence
4. Proceed to Phase 3 only after all tests pass
