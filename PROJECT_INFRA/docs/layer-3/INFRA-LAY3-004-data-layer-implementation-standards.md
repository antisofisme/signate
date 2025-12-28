# INFRA-LAY3-004: Data Layer Implementation Standards

**VERSION**: Layer 3 DRAFT
**STATUS**: IN PROGRESS
**DATE**: 2025-12-28

---

## Overview

This document defines **implementation standards** for Infra data layer.

- **Scope**: Database selection, schema design, immutability enforcement, indexing, transactions, archival, backup
- **Source of Truth**: INFRA-LAY2-003 (Data Persistence Model)
- **Constraint**: Data layer MUST enforce immutability, tenant isolation, and atomicity

**Key Principle**: Database is **source of truth**, not application logic. All guarantees enforced at storage layer.

---

## 1. Database Selection Criteria

### 1.1 Database Technology

```
REQUIREMENT: Choose database that supports Row-Level Security (RLS) or schema-per-tenant.

Recommended: PostgreSQL 13+

Rationale:
  ✓ Native RLS support (built-in, mature, well-tested)
  ✓ JSONB support (for context snapshots, flexible)
  ✓ Native UUID type (immutable, globally unique)
  ✓ Trigger support (immutability enforcement)
  ✓ ACID transactions (atomic decision creation)
  ✓ Materialized views (projections for CMS queries)
  ✓ Open source (no vendor lock-in)
  ✓ Strong community (PostgreSQL production use)

Alternative: MySQL 8.0+

Rationale:
  ✓ Wide availability (hosted databases available)
  ✗ No RLS (must use schema-per-tenant or application logic)
  ✗ JSON support limited (JSONB not available)
  ⚠ Trigger support (limited, slower than PostgreSQL)
  ✓ ACID transactions (InnoDB)
  ⚠ Materialized views (workaround required)

Alternative: Cloud-Native (DynamoDB, Firestore, BigTable)

Rationale:
  ✗ No RLS (must be enforced in application)
  ✗ No schema enforcement (data shape not guaranteed)
  ✓ High scalability (multi-tenant native)
  ✗ Trigger support (limited or non-existent)
  ✗ Complex query support (limited to simple filters)
  ✓ Managed service (operational simplicity)

Recommendation: PostgreSQL for strict data consistency, Cloud-Native for high scalability.
Hybrid: PostgreSQL for hot storage (90 days), Cloud storage for warm/cold (archival).
```

### 1.2 Connection Management

```
REQUIREMENT: Manage database connections efficiently.

Connection Pool Configuration:

  pool_size: 20-100 (depends on throughput, p95 latency)
  idle_timeout: 5 minutes (close idle connections)
  connection_timeout: 10 seconds (fail fast)
  max_retries: 3 (with exponential backoff)
  statement_cache: enabled (prepared statements)

Per-Environment:

  Development:
    pool_size: 5
    idle_timeout: 30 seconds

  Production:
    pool_size: 100 (for 1000+ requests/second)
    idle_timeout: 5 minutes
    connection_timeout: 10 seconds
    circuit_breaker: enabled (fail open after N failures)

Monitoring:

  ✓ Active connections (current count)
  ✓ Idle connections (waiting)
  ✓ Connection errors (timeout, refused, etc.)
  ✓ Pool exhaustion events (alert if connections > 80% utilized)
  ✓ Connection latency (p95, p99)

Circuit Breaker Pattern:

  If database unavailable > 10 seconds:
    - Return 503 Service Unavailable to SDK
    - Log failure
    - Retry with exponential backoff
    - Once recovered, close breaker
```

---

## 2. Schema Design Standards

### 2.1 Table Definitions (Per INFRA-LAY2-003)

```
TABLE 1: decisions (Immutable)

CREATE TABLE decisions (
  decision_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  decision_type VARCHAR(256) NOT NULL,
  context JSONB NOT NULL,                    // sanitized context snapshot
  outcome VARCHAR(32) NOT NULL,              // ALLOWED, DENIED, REQUIRE_APPROVAL
  rule_matched VARCHAR(256),                 // which rule matched (nullable)
  rule_version VARCHAR(32),                  // version of rule used
  approval_workflow_id UUID,                 // link to workflow (if REQUIRE_APPROVAL)
  idempotency_key VARCHAR(256),              // for deduplication
  latency_ms INTEGER,                        // SDK → Core latency
  created_at TIMESTAMP NOT NULL,             // immutable, decided_at
  metadata JSONB,                            // trace_id, requester_user_id, source
  archived_at TIMESTAMP,                     // when archived to warm storage
  archive_location VARCHAR(512),             // URI to archived data

  CONSTRAINT outcome_valid CHECK (outcome IN ('ALLOWED', 'DENIED', 'REQUIRE_APPROVAL')),
  CONSTRAINT outcome_not_null CHECK (outcome IS NOT NULL)
);

INDEXES (MANDATORY per INFRA-LAY2-003):
  CREATE INDEX idx_decisions_tenant_id ON decisions(tenant_id);
  CREATE INDEX idx_decisions_tenant_decision_type ON decisions(tenant_id, decision_type);
  CREATE INDEX idx_decisions_tenant_created_at ON decisions(tenant_id, created_at DESC);
  CREATE INDEX idx_decisions_idempotency_key ON decisions(tenant_id, idempotency_key);
  CREATE UNIQUE INDEX idx_decisions_idempotency_unique ON decisions(tenant_id, idempotency_key);

---

TABLE 2: workflows (Mutable until terminal)

CREATE TABLE workflows (
  workflow_id UUID PRIMARY KEY,
  decision_id UUID NOT NULL,                 // link to decision (immutable)
  tenant_id UUID NOT NULL,                   // partition key
  current_state VARCHAR(32) NOT NULL,        // PENDING_APPROVAL, APPROVED, REJECTED, DELEGATED, ESCALATED
  approver_role VARCHAR(256) NOT NULL,       // role identifier (e.g., CFO)
  delegated_to_user_id UUID,                 // if delegated
  escalated_to_user_id UUID,                 // if escalated
  escalation_timeout_at TIMESTAMP,           // when escalation triggers
  created_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,                    // when terminal state reached
  metadata JSONB,                            // trace_id, etc.

  CONSTRAINT state_valid CHECK (current_state IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'DELEGATED', 'ESCALATED')),
  CONSTRAINT decision_fk FOREIGN KEY (decision_id) REFERENCES decisions(decision_id),
  CONSTRAINT terminal_state_immutable CHECK (completed_at IS NULL OR current_state IN ('APPROVED', 'REJECTED'))
);

INDEXES (MANDATORY):
  CREATE INDEX idx_workflows_tenant_id ON workflows(tenant_id);
  CREATE INDEX idx_workflows_decision_id ON workflows(decision_id);
  CREATE INDEX idx_workflows_tenant_decision_id ON workflows(tenant_id, decision_id);
  CREATE INDEX idx_workflows_approval_workflow_id ON workflows(tenant_id, decision_id);  // per amendment 6
  CREATE INDEX idx_workflows_escalation_timeout ON workflows(tenant_id, escalation_timeout_at);

---

TABLE 3: workflow_transitions (Append-Only, Immutable)

CREATE TABLE workflow_transitions (
  transition_id UUID PRIMARY KEY,
  workflow_id UUID NOT NULL,                 // link to workflow
  tenant_id UUID NOT NULL,                   // partition key
  from_state VARCHAR(32) NOT NULL,
  to_state VARCHAR(32) NOT NULL,
  action VARCHAR(32),                        // APPROVED, REJECTED, DELEGATED, ESCALATED
  acted_by_user_id UUID,                     // who made change
  approver_role VARCHAR(256),                // approver role
  comment TEXT,                              // optional reason
  created_at TIMESTAMP NOT NULL,

  CONSTRAINT workflow_fk FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);

INDEXES (MANDATORY):
  CREATE INDEX idx_workflow_transitions_workflow_id ON workflow_transitions(workflow_id);
  CREATE INDEX idx_workflow_transitions_tenant_created ON workflow_transitions(tenant_id, created_at DESC);

---

TABLE 4: rules (Rule configuration, with versioning)

CREATE TABLE rules (
  rule_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  decision_type VARCHAR(256) NOT NULL,
  rule_name VARCHAR(256) NOT NULL,
  description TEXT,
  conditions JSONB NOT NULL,                 // condition definition
  action JSONB NOT NULL,                     // action (outcome, approval_config)
  extension_hooks JSONB,                     // async hooks
  version VARCHAR(32) NOT NULL,              // e.g., "1.0", "1.1"
  status VARCHAR(32) NOT NULL,               // DRAFT, ACTIVE, DEPRECATED, DELETED
  evaluation_sequence INTEGER NOT NULL DEFAULT 0, // PHASE 1 CLARIFICATION: Explicit rule evaluation order
  created_by_user_id UUID,
  created_at TIMESTAMP NOT NULL,
  activated_at TIMESTAMP,                    // when activated
  deactivated_at TIMESTAMP,                  // when deactivated
  deactivation_reason TEXT,
  deleted_at TIMESTAMP,
  final_audit_report_uri VARCHAR(512),       // link to archived audit report
  archived_at TIMESTAMP,
  archive_location VARCHAR(512),             // URI to archived rule definition

  CONSTRAINT status_valid CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED', 'DELETED')),
  CONSTRAINT unique_active_per_type UNIQUE (tenant_id, decision_type, rule_name) WHERE status = 'ACTIVE'
);

INDEXES (MANDATORY):
  CREATE INDEX idx_rules_tenant_id ON rules(tenant_id);
  CREATE INDEX idx_rules_tenant_decision_type_status ON rules(tenant_id, decision_type, status);
  CREATE INDEX idx_rules_tenant_decision_type_active ON rules(tenant_id, decision_type) WHERE status = 'ACTIVE';
  CREATE INDEX idx_rules_evaluation_order ON rules(tenant_id, decision_type, evaluation_sequence) WHERE status = 'ACTIVE'; // PHASE 1 CLARIFICATION: Deterministic rule ordering

---

TABLE 5: event_log (Append-Only, Immutable, Source of Truth)

CREATE TABLE event_log (
  event_id UUID PRIMARY KEY,                 // globally unique forever
  event_type VARCHAR(256) NOT NULL,          // e.g., "decision.created"
  tenant_id UUID NOT NULL,                   // partition key
  aggregate_id UUID NOT NULL,                // decision_id or workflow_id
  aggregate_type VARCHAR(32) NOT NULL,       // "decision" or "workflow"
  payload JSONB NOT NULL,                    // event-specific data
  metadata JSONB,                            // source, caused_by_user_id, trace_id
  occurred_at TIMESTAMP NOT NULL,            // when event occurred (immutable)
  recorded_at TIMESTAMP NOT NULL,            // when persisted
  schema_version VARCHAR(32),
  archived_at TIMESTAMP,
  archive_location VARCHAR(512),

  CONSTRAINT event_type_valid CHECK (event_type IN (
    'decision.created', 'decision.allowed', 'decision.denied', 'decision.requires_approval',
    'workflow.created', 'workflow.pending_approval', 'workflow.approved', 'workflow.rejected',
    'workflow.delegated', 'workflow.escalated', 'workflow.completed'
  )),
  CONSTRAINT aggregate_type_valid CHECK (aggregate_type IN ('decision', 'workflow'))
);

INDEXES (MANDATORY):
  CREATE INDEX idx_event_log_tenant_occurred ON event_log(tenant_id, occurred_at DESC);
  CREATE INDEX idx_event_log_aggregate ON event_log(tenant_id, aggregate_id);
  CREATE INDEX idx_event_log_type ON event_log(tenant_id, event_type);

---

TABLE 6: operations_audit (Audit Trail, Immutable)

CREATE TABLE operations_audit (
  audit_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  operation_type VARCHAR(32) NOT NULL,      // CREATE, READ, UPDATE_ATTEMPT, DELETE_ATTEMPT
  resource_type VARCHAR(32) NOT NULL,        // decision, workflow, rule, event_log
  resource_id UUID,
  actor_user_id UUID,                        // who made the operation
  actor_role VARCHAR(256),
  action_status VARCHAR(32),                 // SUCCESS, FAILURE, DENIED
  reason_if_denied TEXT,                     // why denied
  timestamp TIMESTAMP NOT NULL,
  trace_id UUID,

  CONSTRAINT operation_type_valid CHECK (operation_type IN (
    'CREATE', 'READ', 'UPDATE_ATTEMPT', 'DELETE_ATTEMPT', 'ACTIVATE', 'DEACTIVATE'
  ))
);

INDEXES (MANDATORY):
  CREATE INDEX idx_operations_audit_tenant_timestamp ON operations_audit(tenant_id, timestamp DESC);
  CREATE INDEX idx_operations_audit_resource ON operations_audit(tenant_id, resource_id);

---

TABLE 7: idempotency_cache (Deduplication, Hot storage only)

CREATE TABLE idempotency_cache (
  tenant_id UUID NOT NULL,
  idempotency_key VARCHAR(256) NOT NULL,
  decision_id UUID NOT NULL,
  created_at TIMESTAMP NOT NULL,
  ttl TIMESTAMP,                              // cache expiration

  PRIMARY KEY (tenant_id, idempotency_key),
  FOREIGN KEY (decision_id) REFERENCES decisions(decision_id)
);

TTL Strategy:
  - entry_ttl = 24 hours (minimum, configurable)
  - Background job: delete expired entries
  - Frequency: hourly
```

### 2.2 RLS Policy Setup (Tenant Isolation)

```
REQUIREMENT: Enable RLS and set policies on all tables.

PostgreSQL RLS Setup:

-- Enable RLS on all tables
ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_transitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE operations_audit ENABLE ROW LEVEL SECURITY;

-- Create role for application user
CREATE ROLE app_role;
GRANT SELECT, INSERT, UPDATE ON decisions TO app_role;
GRANT SELECT, INSERT, UPDATE ON workflows TO app_role;
... (for all tables)

-- Create RLS policies
CREATE POLICY decisions_tenant_isolation ON decisions
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY workflows_tenant_isolation ON workflows
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Repeat for all tables with tenant_id

-- Application usage
-- Before queries, set tenant context:
SET app.current_tenant_id = 'hotel-123';

-- All queries automatically filtered by RLS
SELECT * FROM decisions;  -- implicit WHERE tenant_id = 'hotel-123'
```

---

## 3. Immutability Enforcement Standards

### 3.1 Trigger-Based Immutability

```
REQUIREMENT: Prevent UPDATE and DELETE on immutable tables.

PostgreSQL Trigger Implementation:

-- Trigger for decisions table (no UPDATE/DELETE allowed)
CREATE OR REPLACE FUNCTION prevent_decisions_modification()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'Immutable table: decisions cannot be modified or deleted';
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER decisions_immutable
BEFORE UPDATE OR DELETE ON decisions
FOR EACH ROW
EXECUTE FUNCTION prevent_decisions_modification();

-- Log failed attempts
CREATE OR REPLACE FUNCTION log_immutability_violation()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
    INSERT INTO operations_audit (
      audit_id, tenant_id, operation_type, resource_type, resource_id,
      actor_user_id, action_status, reason_if_denied, timestamp
    )
    VALUES (
      uuid_generate_v4(),
      COALESCE(OLD.tenant_id, NEW.tenant_id),
      TG_OP || '_ATTEMPT',
      'decision',
      COALESCE(OLD.decision_id, NEW.decision_id),
      current_user,
      'DENIED',
      'Immutable table violation',
      now()
    );

    RAISE EXCEPTION 'Immutability violation: % attempted on % record',
      TG_OP, 'decision';
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply to immutable tables
CREATE TRIGGER log_decisions_violation
BEFORE UPDATE OR DELETE ON decisions
FOR EACH ROW
EXECUTE FUNCTION log_immutability_violation();

-- Similar triggers for:
-- - event_log
-- - workflow_transitions
-- - operations_audit (audit trail itself is immutable)
```

### 3.2 Role-Based Immutability (Database Permissions)

```
REQUIREMENT: Enforce immutability at database role level.

PostgreSQL Role-Based Security:

-- Create read-only role
CREATE ROLE infra_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO infra_reader;

-- Create writer role (for INSERT only)
CREATE ROLE infra_writer;
GRANT SELECT, INSERT ON decisions TO infra_writer;
GRANT SELECT, INSERT ON workflows TO infra_writer;
GRANT SELECT, INSERT ON event_log TO infra_writer;
... (INSERT only, no UPDATE/DELETE)

-- REVOKE UPDATE/DELETE explicitly
REVOKE UPDATE, DELETE ON decisions FROM infra_writer;
REVOKE UPDATE, DELETE ON workflows FROM infra_writer;
REVOKE UPDATE, DELETE ON event_log FROM infra_writer;
... (for all immutable tables)

-- Application connects as infra_writer
-- Cannot execute UPDATE/DELETE even if syntax is correct
-- Database prevents at role level (layered defense)

Verification:
  -- This will fail with permission denied
  UPDATE decisions SET outcome = 'ALLOWED' WHERE decision_id = ?;
  → ERROR: permission denied for relation decisions
```

---

## 4. Indexing Strategy Standards

### 4.1 Index Design (Performance)

```
REQUIREMENT: Indexes MUST support critical queries without overhead.

Query Patterns (from INFRA-LAY2-002):

PATTERN 1: Fetch decision by tenant and decision_id
  SELECT * FROM decisions WHERE tenant_id = ? AND decision_id = ?
  → Index: (tenant_id, decision_id)

PATTERN 2: List decisions for tenant (paginated)
  SELECT * FROM decisions WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 100
  → Index: (tenant_id, created_at DESC)

PATTERN 3: Query decisions by type (for audit)
  SELECT * FROM decisions WHERE tenant_id = ? AND decision_type = ? AND created_at BETWEEN ? AND ?
  → Index: (tenant_id, decision_type, created_at)

PATTERN 4: Idempotency lookup
  SELECT decision_id FROM decisions WHERE tenant_id = ? AND idempotency_key = ?
  → Index: UNIQUE (tenant_id, idempotency_key)

PATTERN 5: List workflows by decision_id
  SELECT * FROM workflows WHERE tenant_id = ? AND decision_id = ?
  → Index: (tenant_id, decision_id)

PATTERN 6: List events by tenant and type
  SELECT * FROM event_log WHERE tenant_id = ? AND event_type = ? ORDER BY occurred_at DESC
  → Index: (tenant_id, event_type, occurred_at DESC)

Index Creation Best Practices:

-- Use partial indexes for status-specific queries
CREATE INDEX idx_rules_active_per_type
  ON rules(tenant_id, decision_type)
  WHERE status = 'ACTIVE';

-- Use covering indexes (include columns) to avoid table lookup
CREATE INDEX idx_decisions_tenant_outcome_covering
  ON decisions(tenant_id, outcome)
  INCLUDE (decision_type, rule_matched);

-- Avoid redundant indexes (PostgreSQL optimizer is smart)
-- Index A: (tenant_id, decision_type)
-- Index B: (tenant_id)
-- → Index B is redundant, remove it

-- Monitor index usage
SELECT * FROM pg_stat_user_indexes ORDER BY idx_scan DESC;
```

### 4.2 Index Maintenance

```
REQUIREMENT: Keep indexes healthy and performant.

Rebuild Schedule:

  -- Scheduled maintenance (weekly)
  REINDEX INDEX idx_decisions_tenant_id;
  REINDEX INDEX idx_decisions_tenant_created_at;
  ... (all indexes)

Unused Index Cleanup:

  -- Identify unused indexes
  SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;

  -- Drop if truly unused
  DROP INDEX idx_unused_index;

Bloat Monitoring:

  -- Check for bloated indexes
  SELECT * FROM pgstattuple_approx('idx_decisions_tenant_id');

  -- If bloat > 30%: REINDEX
  REINDEX INDEX idx_decisions_tenant_id;
```

---

## 5. Transaction & ACID Standards

### 5.1 Decision Creation Transaction (Atomic)

```
REQUIREMENT: Decision creation MUST be atomic (all-or-nothing).

Transaction Pattern:

BEGIN TRANSACTION
  ISOLATION LEVEL: SERIALIZABLE (strongest)

  STEP 1: Validate tenant isolation
    SELECT 1 FROM tenants WHERE tenant_id = ? FOR UPDATE;
    -- Lock prevents concurrent tenant deletion

  STEP 2: Load rule set
    SELECT * FROM rules
    WHERE tenant_id = ? AND decision_type = ? AND status = 'ACTIVE'
    ORDER BY creation_sequence ASC;
    -- Shared lock (multiple decisions can read simultaneously)

  STEP 3: Evaluate rules (in-memory, no database access)
    -- Application logic evaluates conditions
    -- No database queries

  STEP 4: Insert decision (immutable)
    INSERT INTO decisions (decision_id, tenant_id, outcome, ...)
    VALUES (?, ?, ?, ...)
    ON CONFLICT (tenant_id, idempotency_key) DO NOTHING;
    -- If idempotency key exists: silent conflict (return cached decision_id)

  STEP 5: Insert workflow (if REQUIRE_APPROVAL)
    INSERT INTO workflows (workflow_id, decision_id, tenant_id, ...)
    VALUES (?, ?, ?, ...)

  STEP 6: Insert event (atomic with decision)
    INSERT INTO event_log (event_id, tenant_id, aggregate_id, ...)
    VALUES (?, ?, ?, ...)

  STEP 7: Insert idempotency cache (durability)
    INSERT INTO idempotency_cache (tenant_id, idempotency_key, decision_id, ...)
    VALUES (?, ?, ?, ...)
    ON CONFLICT (tenant_id, idempotency_key) DO NOTHING;

COMMIT TRANSACTION
  -- All steps succeed together or all roll back
  -- No partial state

Rollback Cases:
  - RLS policy violation (cross-tenant access)
  - Constraint violation (outcome IS NULL, state invalid)
  - Idempotency key conflict (different context, same key)
  - Network failure (connection closed before commit)
```

### 5.2 Isolation Levels

```
REQUIREMENT: Choose appropriate isolation level per transaction.

Decision Creation:
  - SERIALIZABLE (strongest)
  - Rationale: Prevent concurrent modifications of same rule set
  - Cost: Slower, but safety critical

Workflow Approval:
  - READ COMMITTED (default, sufficient)
  - Rationale: Workflow state changes are independent
  - Cost: Fast

Rule CRUD (CMS):
  - READ COMMITTED (sufficient)
  - Rationale: Rule versions are immutable, no conflict possible
  - Cost: Fast

Query/Audit:
  - READ COMMITTED (sufficient)
  - Rationale: Reading historical data, not sensitive to stale reads
  - Cost: Fast
```

---

## 6. Archival & Storage Tiering Standards

### 6.1 Hot Storage (0-90 days)

```
TIER: Hot (Recent, frequently accessed)

Storage: SSD-backed database (PostgreSQL)
Retention: 0-90 days
Query Latency: < 100ms
Cost: High (per GB/month)
Access: Direct queries from Core, CMS

Data Included:
  - decisions (all)
  - workflows (all)
  - event_log (all)
  - rules (active, draft)
  - operations_audit (all)

Maintenance:
  - Indexes for fast queries
  - RLS policies active
  - Immutability triggers active
  - Backup frequency: hourly

Rotation: Data > 90 days → Archive to warm storage
  - Scheduled job: Every midnight
  - Target: decisions, workflows, event_log
  - Process:
    1. Identify records with created_at < now() - 90 days
    2. Compress (gzip)
    3. Copy to warm storage (S3, GCS, etc.)
    4. Verify hash
    5. Mark as archived (archive_location in metadata)
    6. (optional) Delete from hot storage
```

### 6.2 Warm Storage (90d - 7yr)

```
TIER: Warm (Medium-aged, occasional queries)

Storage: WORM Object Storage (S3, GCS, Azure Blob)
Retention: 90 days - 7 years
Query Latency: < 5 seconds (rehydration needed)
Cost: Low (per GB/month)
Access: CMS audit queries, compliance requests

Data Included:
  - decisions (archived, 90d - 7yr)
  - workflows (archived, 90d - 7yr)
  - event_log (archived, 90d - 7yr)
  - rules (deprecated, archived definitions)

Format:
  - Compressed: gzip
  - Serialization: JSON, Parquet, or Avro
  - Naming: s3://infra-archive/warm/decisions/tenant-123/2025-01-01.tar.gz
  - Hash: SHA256(file) stored in metadata

Retrieval (Rehydration):
  - CMS queries warm storage via API
  - API retrieves file from S3
  - Decompresses
  - Loads into temporary database
  - Serves query
  - SLA: < 1 hour rehydration
  - Cost: Data transfer charges (per GB read)
```

### 6.3 Cold Storage (7yr+)

```
TIER: Cold (Old, rarely accessed, archival)

Storage: Object Lock Immutable Archive (S3, GCS, Azure Blob)
Retention: 7+ years (compliance requirement)
Query Latency: < 1 hour (slow restore)
Cost: Very low (per GB/month)
Access: Legal discovery, compliance audit only

Data Included:
  - decisions (older than 7 years)
  - event_log (older than 7 years)
  - audit reports (deleted rule definitions, final audit snapshots)

Format:
  - Compressed: gzip
  - Serialization: JSON
  - Encryption: AES-256 (at rest)
  - Naming: s3://infra-archive/cold/decisions/tenant-123/2018-01-01.tar.gz
  - Hash: SHA256(file)

Object Lock Configuration:
  - Retention Mode: GOVERNANCE (cannot delete, but can modify with permission)
  - Retention Period: 7 years (automatic)
  - Legal Hold: Optional (if needed)

Retrieval (Rehydration):
  - Compliance officer requests data
  - Manual approval workflow
  - Retrieve from S3 (may take hours due to Glacier storage class)
  - Restore to temporary location
  - Extract and audit
  - SLA: < 1 day rehydration

Deletion Policy:
  - After 7+ year retention: can be deleted (if legal hold released)
  - Require approval from legal/compliance
  - Log deletion in audit trail
  - Delete with cryptographic proof (hash verification)
```

### 6.4 Archival Process

```
OPERATION: Move data from hot → warm → cold.

Automated Archival Job:

SCHEDULE: Daily (midnight UTC)

STEP 1: Identify hot data to archive
  SELECT * FROM decisions
  WHERE created_at < now() - interval 90 days
    AND archived_at IS NULL
  LIMIT 10000;  // batch process

STEP 2: Compress and upload to warm storage
  - gzip compress batch (decisions for single day)
  - Upload to S3: s3://infra-archive/warm/decisions/2025-01-01.tar.gz
  - Store hash in metadata
  - Log: archival_operation_started event

STEP 3: Verify integrity
  - Download file from S3
  - Hash check (SHA256)
  - Decompress and verify record count
  - Log: archival_operation_completed (SUCCESS or FAILURE)

STEP 4: Mark as archived (in hot storage metadata)
  UPDATE decisions SET
    archived_at = now(),
    archive_location = 's3://infra-archive/warm/decisions/2025-01-01.tar.gz'
  WHERE created_at < now() - interval 90 days AND archived_at IS NULL

STEP 5: (Optional) Delete from hot storage
  DELETE FROM decisions
  WHERE created_at < now() - interval 90 days
    AND archived_at IS NOT NULL

WARM → COLD (automatic, quarterly):

SCHEDULE: Quarterly (Jan 1, Apr 1, Jul 1, Oct 1)

STEP 1: Identify warm data older than 7 years
  - Query S3 listing: s3://infra-archive/warm/decisions/
  - Filter files with created_at < now() - 7 years

STEP 2: Copy from warm to cold storage
  - Copy from S3 (warm) to S3 Glacier (cold)
  - Enable Object Lock (GOVERNANCE, 7-year retention)
  - Store copy hash

STEP 3: Verify and mark transition
  - Confirm copy successful
  - Update metadata: archive_tier = 'cold'

STEP 4: Delete from warm storage (optional)
  - Delete warm copy after verification
  - Retain cold copy indefinitely

Failure Handling:

  If archival fails:
    - Log archival_operation_completed (FAILURE)
    - Alert: P1 (data integrity at risk)
    - Manual intervention required
    - Retry: next day
```

---

## 7. Backup & Disaster Recovery Standards

### 7.1 Backup Strategy

```
REQUIREMENT: Backup hot storage for disaster recovery.

Backup Frequency:

  - Hot storage: continuous (PITR - Point In Time Recovery)
  - Warm storage: daily snapshot
  - Cold storage: at archival time (immutable archive is backup)

PostgreSQL Hot Backup:

  -- Enable WAL (Write-Ahead Logging)
  wal_level = replica
  max_wal_senders = 10
  max_replication_slots = 10

  -- Setup streaming replication
  CREATE PUBLICATION hot_backup_pub FOR ALL TABLES;
  CREATE SUBSCRIPTION hot_backup_sub FROM standby_server;

  -- Backup frequency: continuous streaming
  -- Recovery: restore from timestamp (PITR)

Backup Testing:

  - Monthly: restore to test environment
  - Verify data integrity (record count, checksums)
  - Test failover procedure
  - Document recovery time (RTO)
  - Document recovery point (RPO)

SLA Target:

  - RTO (Recovery Time Objective): < 1 hour (restore from backup)
  - RPO (Recovery Point Objective): < 5 minutes (lost data acceptable)
```

### 7.2 Disaster Recovery Plan

```
REQUIREMENT: Plan for complete data loss scenarios.

Disaster Scenarios:

1. Single Table Corruption
   - Restore from transaction log (PITR)
   - RTO: < 10 minutes

2. Database Corruption (all tables)
   - Restore from full backup (previous day)
   - RTO: < 1 hour
   - RPO: < 24 hours

3. Data Center Failure
   - Failover to standby database (secondary datacenter)
   - RTO: < 5 minutes (automated failover)
   - RPO: < 1 minute (streaming replication)

4. Complete Data Loss (all backups destroyed)
   - Restore from warm storage (90d+)
   - RTO: < 4 hours (restore and rehydrate)
   - RPO: not applicable (all backup tiers lost is catastrophic)

Recovery Procedures:

  STEP 1: Assess damage
    - Identify scope (single record? entire table? all data?)
    - Notify stakeholders

  STEP 2: Isolate failed database
    - Stop application traffic
    - Prevent cascading failures

  STEP 3: Restore from backup
    - Choose backup point (before corruption)
    - Restore to test environment first
    - Verify integrity

  STEP 4: Failover
    - Switch DNS to restored database
    - Resume application traffic
    - Monitor for issues

  STEP 5: Investigate root cause
    - What caused the failure?
    - How to prevent next time?
    - Update disaster recovery plan

  STEP 6: Full recovery
    - Restore missing data (from warm storage if needed)
    - Rebuild indexes
    - Verify all constraints
```

---

## 8. Guard Rails: Data Layer Constraints

### 8.1 Non-Negotiable Guard Rails

```
GUARDRAIL 1: Tenant Isolation (Database-Enforced)
  - RLS policy on all tables (or schema-per-tenant)
  - Cross-tenant queries rejected (0 rows returned or error)
  - Query without tenant_id → silent filter (RLS enforces)

GUARDRAIL 2: Immutability (Multi-Layer)
  - DB role permissions: REVOKE UPDATE/DELETE
  - Triggers: BEFORE UPDATE/DELETE RAISE EXCEPTION
  - Storage: WORM/Object Lock on warm/cold
  - Breach of any layer does NOT compromise others

GUARDRAIL 3: Atomicity (Transactions)
  - Decision creation atomic (all-or-nothing)
  - Event persisted with decision (same transaction)
  - Idempotency deduplication in same transaction
  - SERIALIZABLE isolation for critical paths

GUARDRAIL 4: Immutable Audit Trail
  - operations_audit is append-only (no UPDATE/DELETE)
  - event_log is append-only (no UPDATE/DELETE)
  - workflow_transitions is append-only (no UPDATE/DELETE)

GUARDRAIL 5: Index Performance
  - All critical queries must have supporting indexes
  - p95 latency < 100ms (SLA target)
  - Queries without indexes: slow or timeout

GUARDRAIL 6: Archival Integrity
  - Hash verification on archive retrieval
  - Immutable archive (Object Lock on cold)
  - Compliance retention (7+ years)

GUARDRAIL 7: Backup & Recovery
  - Continuous backup (PITR capable)
  - RTO < 1 hour (restore from backup)
  - RPO < 5 minutes (lost data acceptable)
  - Monthly recovery drills (test procedures)

GUARDRAIL 8: Connection Pooling
  - Max connections limited (circuit breaker)
  - Connection timeout: 10 seconds (fail fast)
  - Pool exhaustion alerts
```

---

## 9. Data Layer Implementation Checklist

```
Before releasing data layer, verify:

DATABASE SETUP:
  ✓ Database selected (PostgreSQL recommended)
  ✓ Version: 13+ for RLS support
  ✓ Connection pooling configured (100 connections for 1000+ rps)
  ✓ Circuit breaker enabled (fail open after 10s unavailability)

SCHEMA:
  ✓ All 7 tables created (decisions, workflows, workflow_transitions, rules, event_log, operations_audit, idempotency_cache)
  ✓ All constraints enforced (outcome NOT NULL, state valid, etc.)
  ✓ All indexes created (mandatory indexes per specification)
  ✓ UNIQUE constraint on (tenant_id, idempotency_key)

IMMUTABILITY:
  ✓ Triggers on decisions, workflows, event_log, operations_audit
  ✓ BEFORE UPDATE/DELETE RAISE EXCEPTION
  ✓ DB role permissions: REVOKE UPDATE/DELETE
  ✓ All immutable tables: prevent modification at 3 layers

TENANT ISOLATION:
  ✓ RLS policies enabled on all tables
  ✓ Policy: (tenant_id = current_setting('app.current_tenant_id'))
  ✓ Query without tenant_id: RLS filters
  ✓ Cross-tenant access: returns 0 rows or error

TRANSACTIONS:
  ✓ Decision creation atomic (all steps in single transaction)
  ✓ Event persisted with decision (same transaction)
  ✓ Idempotency deduplication atomic
  ✓ Isolation level: SERIALIZABLE for decision creation

ARCHIVAL:
  ✓ Hot storage: SSD-backed database (0-90 days)
  ✓ Warm storage: WORM object storage (90d - 7yr)
  ✓ Cold storage: Object Lock immutable archive (7yr+)
  ✓ Archival job: automated, daily, with hash verification

BACKUP & RECOVERY:
  ✓ Continuous backup (WAL replication)
  ✓ PITR enabled (point-in-time recovery)
  ✓ RTO < 1 hour, RPO < 5 minutes
  ✓ Monthly recovery drills (procedures tested)

MONITORING:
  ✓ Connection pool utilization (alert at 80%)
  ✓ Query latency (p95, p99)
  ✓ Index size and bloat
  ✓ Archival success/failure
  ✓ Immutability violation attempts (must be 0)
  ✓ Cross-tenant access attempts (must be 0)

TESTING:
  ✓ Unit tests for triggers (prevent UPDATE/DELETE)
  ✓ Unit tests for RLS policies (tenant isolation)
  ✓ Integration tests for transaction atomicity
  ✓ Load tests (p95 < 100ms at 1000 rps)
  ✓ Disaster recovery tests (failover, restore)
```

---

## 10. Summary: Data Layer as Source of Truth

✅ **Database Selection**: PostgreSQL 13+ with RLS support
✅ **Schema Design**: 7 tables with immutability, tenant isolation, audit trail
✅ **Immutability Enforcement**: 3-layer (roles, triggers, storage locks)
✅ **Tenant Isolation**: RLS policies on all tables
✅ **Transaction Atomicity**: All-or-nothing, SERIALIZABLE isolation
✅ **Archival**: Hot → Warm → Cold with hash verification
✅ **Backup & Recovery**: Continuous PITR, RTO < 1 hour
✅ **Guard Rails**: Non-negotiable constraints enforced at storage layer

**Status**: Layer 3.4 DRAFT, ready for review.

**Next**: Event & Logging Implementation Standards (INFRA-LAY3-005).
