# ATLAS_PUGUH Database Migrations

## Overview

This directory contains database schema migrations for the ATLAS_PUGUH Control Plane.

**Database**: PostgreSQL 13+
**Migration Strategy**: Sequential, numbered migrations
**Rollback**: Not supported (append-only migration strategy)

## Migration Files

| Migration | Description | Tables/Features |
|-----------|-------------|-----------------|
| `001_initial_schema.sql` | Initial schema creation | 7 tables: decisions, workflows, workflow_transitions, rules, event_log, operations_audit, idempotency_cache, schema_migrations |
| `002_immutability_triggers.sql` | Immutability enforcement | Triggers to prevent UPDATE/DELETE on immutable tables |
| `003_rls_policies.sql` | Row-Level Security policies | Tenant isolation via RLS, database roles |

## Running Migrations

### Prerequisites

1. PostgreSQL 13+ installed
2. Database created
3. Superuser access (for RLS and trigger creation)

### Option 1: Run All Migrations (Fresh Install)

```bash
# Set database connection
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=infra_puguh
export DB_USER=postgres
export DB_PASSWORD=your_password

# Run initialization script
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f init_database.sh
```

### Option 2: Run Individual Migrations

```bash
# Run migrations in order
psql -h localhost -p 5432 -U postgres -d infra_puguh -f 001_initial_schema.sql
psql -h localhost -p 5432 -U postgres -d infra_puguh -f 002_immutability_triggers.sql
psql -h localhost -p 5432 -U postgres -d infra_puguh -f 003_rls_policies.sql
```

### Option 3: Docker Compose (Development)

```bash
# Copy migrations to Docker container
docker cp migrations/ infra-postgres:/migrations/

# Execute migrations
docker exec -i infra-postgres psql -U postgres -d infra_puguh < /migrations/001_initial_schema.sql
docker exec -i infra-postgres psql -U postgres -d infra_puguh < /migrations/002_immutability_triggers.sql
docker exec -i infra-postgres psql -U postgres -d infra_puguh < /migrations/003_rls_policies.sql
```

## Verifying Migrations

### Check Migration Status

```sql
-- List applied migrations
SELECT * FROM schema_migrations ORDER BY migration_id;
```

Expected output:
```
migration_id |      migration_name       |        applied_at
-------------+---------------------------+---------------------------
           1 | 001_initial_schema        | 2026-01-07 10:00:00+00
           2 | 002_immutability_triggers | 2026-01-07 10:00:01+00
           3 | 003_rls_policies          | 2026-01-07 10:00:02+00
```

### Verify Schema

```sql
-- List all tables
\dt

-- Expected tables:
-- decisions
-- workflows
-- workflow_transitions
-- rules
-- event_log
-- operations_audit
-- idempotency_cache
-- schema_migrations
```

### Verify Immutability Triggers

```sql
-- List all triggers
SELECT tgname, tgrelid::regclass FROM pg_trigger
WHERE tgname LIKE '%immutable%'
ORDER BY tgrelid::regclass::text;
```

Expected output:
```
decisions_immutable_before_update_delete
event_log_immutable_before_update_delete
workflow_transitions_immutable_before_update_delete
operations_audit_immutable_before_update_delete
workflows_terminal_state_immutable
idempotency_cache_immutable_before_update_delete
```

### Verify RLS Policies

```sql
-- List all RLS policies
SELECT tablename, policyname FROM pg_policies
WHERE tablename IN (
  'decisions', 'workflows', 'workflow_transitions',
  'rules', 'event_log', 'operations_audit', 'idempotency_cache'
)
ORDER BY tablename;
```

Expected output:
```
tablename               | policyname
-----------------------+---------------------------------
decisions               | decisions_tenant_isolation
event_log               | event_log_tenant_isolation
idempotency_cache       | idempotency_cache_tenant_isolation
operations_audit        | operations_audit_tenant_isolation
rules                   | rules_tenant_isolation
workflow_transitions    | workflow_transitions_tenant_isolation
workflows               | workflows_tenant_isolation
```

### Test Immutability

```sql
-- This should FAIL with immutability violation
SET app.current_tenant_id = '123e4567-e89b-12d3-a456-426614174000';

INSERT INTO decisions (decision_id, tenant_id, decision_type, context, outcome)
VALUES (
  '123e4567-e89b-12d3-a456-426614174001',
  '123e4567-e89b-12d3-a456-426614174000',
  'test.decision',
  '{"test": true}'::jsonb,
  'ALLOWED'
);

-- This should FAIL
UPDATE decisions SET outcome = 'DENIED' WHERE decision_id = '123e4567-e89b-12d3-a456-426614174001';
-- Expected: ERROR: Immutability violation: UPDATE operation not allowed on immutable table decisions

-- This should FAIL
DELETE FROM decisions WHERE decision_id = '123e4567-e89b-12d3-a456-426614174001';
-- Expected: ERROR: Immutability violation: DELETE operation not allowed on immutable table decisions
```

### Test Tenant Isolation

```sql
-- Set tenant context for tenant A
SET app.current_tenant_id = '123e4567-e89b-12d3-a456-426614174000';

-- Insert decision for tenant A
INSERT INTO decisions (decision_id, tenant_id, decision_type, context, outcome)
VALUES (
  '223e4567-e89b-12d3-a456-426614174001',
  '123e4567-e89b-12d3-a456-426614174000',
  'test.decision',
  '{"test": true}'::jsonb,
  'ALLOWED'
);

-- Query as tenant A (should see 1 row)
SELECT COUNT(*) FROM decisions;
-- Expected: 1

-- Set tenant context for tenant B
SET app.current_tenant_id = '999e4567-e89b-12d3-a456-426614174000';

-- Query as tenant B (should see 0 rows - RLS isolation)
SELECT COUNT(*) FROM decisions;
-- Expected: 0

-- Try to insert for tenant A while logged as tenant B (should FAIL)
INSERT INTO decisions (decision_id, tenant_id, decision_type, context, outcome)
VALUES (
  '323e4567-e89b-12d3-a456-426614174001',
  '123e4567-e89b-12d3-a456-426614174000',  -- Tenant A
  'test.decision',
  '{"test": true}'::jsonb,
  'ALLOWED'
);
-- Expected: ERROR: new row violates row-level security policy for table "decisions"
```

## Architecture Guarantees

After running all migrations, the following guarantees are enforced:

### ✅ Immutability (Multi-Layer)
- Database role permissions: `REVOKE UPDATE, DELETE`
- Triggers: `BEFORE UPDATE/DELETE RAISE EXCEPTION`
- Violation logging: All attempts logged to `operations_audit`

### ✅ Tenant Isolation
- RLS policies on all tables
- Cross-tenant queries return 0 rows
- Violations prevented at database level

### ✅ Atomicity
- Transactions: `SERIALIZABLE` isolation for decision creation
- Constraints: Foreign keys, check constraints
- All-or-nothing inserts

### ✅ Audit Trail
- `event_log`: Immutable event history
- `operations_audit`: Immutable audit trail (including failed attempts)
- `workflow_transitions`: Immutable state change history

### ✅ Determinism
- `evaluation_sequence`: Explicit rule ordering
- Version pinning: `rule_matched_id`, `rule_version`
- Idempotency: `UNIQUE(tenant_id, idempotency_key)`

## Troubleshooting

### Migration Failed Partway

If migration fails, check:

```sql
-- Check which migrations completed
SELECT * FROM schema_migrations ORDER BY migration_id;

-- Check for partial schema
\dt

-- If needed, drop all tables and restart
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

### RLS Blocking All Queries

```sql
-- Check if tenant_id is set
SELECT current_setting('app.current_tenant_id', true);

-- If empty, set it:
SET app.current_tenant_id = 'your-tenant-uuid';
```

### Trigger Errors

```sql
-- List all triggers
SELECT tgname, tgrelid::regclass FROM pg_trigger ORDER BY tgrelid::regclass::text;

-- Check trigger function
\df prevent_immutable_modification
\df prevent_terminal_workflow_modification
\df prevent_idempotency_cache_modification
```

## Phase 1 Success Criteria

Before proceeding to Phase 2, verify:

- ✅ All 3 migrations applied successfully
- ✅ All 7 tables created with correct schema
- ✅ All indexes created (24+ indexes)
- ✅ All triggers active (6 triggers)
- ✅ All RLS policies active (7 policies)
- ✅ Immutability test passes (UPDATE/DELETE fail)
- ✅ Tenant isolation test passes (cross-tenant queries return 0 rows)

## Next Steps

After database setup:

1. **Week 2-3**: Implement Core Service (decision engine, SDK)
2. **Week 4**: Testing (unit, integration, security, load)
3. **Week 5**: Deployment & Validation

## References

- **Architecture**: `/docs/layer-3/INFRA-LAY3-004-data-layer-implementation-standards.md`
- **Phase 1 Plan**: `/PHASE-1-EXECUTION-READY.md`
- **Database Conventions**: PostgreSQL 13+ standards
