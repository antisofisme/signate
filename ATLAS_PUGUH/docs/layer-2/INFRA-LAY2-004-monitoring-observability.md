# INFRA-LAY2-004: Monitoring & Observability

**VERSION**: Layer 2 DRAFT
**STATUS**: IN PROGRESS
**DATE**: 2025-12-27

---

## Overview

This document defines **observability requirements** for Infra:
- Metrics (what to measure)
- Logging (what to record)
- Alerting (when to notify)
- Audit trail (compliance & verification)

**Purpose**: Observability is prerequisite for:
- Verifying immutability guarantees in production
- Detecting tenant isolation violations
- Compliance with audit & retention requirements
- Safe operational debugging

**Scope**: Layer 2 (foundational requirements, NOT implementation/tooling choice)

---

## 1. Core Observability Principles

### 1.1 Requirements (Non-Negotiable)

```
PRINCIPLE 1: Immutability Verifiable
  - Every write operation logged (CREATE, UPDATE, DELETE attempt)
  - Unauthorized modifications detected (UPDATE/DELETE on immutable)
  - Audit trail proves no tampering occurred

PRINCIPLE 2: Tenant Isolation Verifiable
  - Cross-tenant access attempts logged (security events)
  - Tenant isolation violations surfaced immediately
  - Audit queries prove no cross-tenant leaks

PRINCIPLE 3: SLA Compliance Measurable
  - Decision latency tracked (SDK → Core time)
  - Approval workflow SLA tracked (pending approval time)
  - Archival migration SLA tracked (hot→warm, warm→cold time)
  - Alerts on SLA breach

PRINCIPLE 4: Auditability Complete
  - Every action traceable to decision/workflow/rule
  - Request ID threaded through all logs (correlation)
  - Timestamp immutable (proves ordering)
  - User/role identified (who took action)

PRINCIPLE 5: Explainability Possible
  - Decision outcome explainable (which rule matched, why)
  - Workflow state changes auditable (who, when, why)
  - Rule changes tracked (version history)
```

### 1.2 What is NOT in Scope

```
NOT INCLUDED (Implementation Layer 3+):
  - Tool selection (Prometheus, DataDog, Splunk, etc.)
  - Infrastructure (log aggregation, metric storage)
  - Authentication/Authorization of monitoring access
  - Dashboard design or tooling
  - Alerting platform (Pagerduty, Opsgenie, etc.)
  - SLA tooling (ServiceNow, incident tracking)

IN SCOPE (Observability Requirements):
  - What metrics must be collected
  - What logs must be recorded
  - What events must trigger alerts
  - What audit trail must be maintained
```

---

## 2. Metrics: What to Measure

### 2.1 Critical Path Metrics (Decision Creation)

```
METRIC: decision_creation_latency_ms
  Unit: milliseconds
  Measured: Time from SDK call to response returned
  Dimensions:
    - decision_type (e.g., "accounting.journal_approval")
    - tenant_id
    - outcome (ALLOWED | DENIED | REQUIRE_APPROVAL)

  SLA Target:
    - p50: < 50ms
    - p95: < 100ms
    - p99: < 200ms

  Alert: If p95 > 150ms (SLA breach)

METRIC: rule_evaluation_time_ms
  Unit: milliseconds
  Measured: Time to evaluate all rules (until match)
  Dimensions:
    - decision_type
    - tenant_id
    - rule_matched (if any)

  SLA Target:
    - p95: < 45ms

  Alert: If p95 > 60ms (approaching SLA limit)

METRIC: decision_outcome_distribution
  Dimensions:
    - decision_type
    - outcome (ALLOWED | DENIED | REQUIRE_APPROVAL)

  Purpose: Track if rules are behaving as expected
  Alert: If outcome distribution shifts suddenly
          (e.g., DENIED rate jumps from 5% to 50%)
```

### 2.2 Critical Path Metrics (Workflow Approval)

```
METRIC: workflow_approval_latency_ms
  Unit: milliseconds
  Measured: Time from approve/reject call to response

  SLA Target:
    - p95: < 100ms

  Alert: If p95 > 150ms

METRIC: workflow_pending_duration_minutes
  Unit: minutes
  Measured: Time from workflow created to terminal state
  Dimensions:
    - decision_type
    - approver_role
    - terminal_state (APPROVED | REJECTED)

  Purpose: Track approval SLA (approval should be timely)
  Alert: If workflow pending > escalation_timeout (approval stalled)

METRIC: workflow_escalation_count
  Unit: count
  Measured: Number of workflows that hit escalation timeout
  Dimensions:
    - decision_type
    - escalation_target_role

  Purpose: Track if approvers are responsive
  Alert: If escalation count spikes (escalations indicate delays)
```

### 2.3 Data Integrity Metrics

```
METRIC: immutability_violation_attempts
  Unit: count (per minute)
  Measured: Attempts to UPDATE or DELETE immutable records
  Dimensions:
    - table (decisions | workflows | event_log | etc.)
    - violation_type (UPDATE_ATTEMPT | DELETE_ATTEMPT)
    - source (SDK | CMS | unknown)

  SLA: Must be zero (any attempt is security event)
  Alert: IMMEDIATE (critical security alert)

METRIC: cross_tenant_access_attempts
  Unit: count (per minute)
  Measured: Queries filtered to wrong tenant (tenant_id mismatch)
  Dimensions:
    - source_tenant_id
    - target_tenant_id (attempted to access)

  SLA: Must be zero (security event)
  Alert: IMMEDIATE (critical security alert)

METRIC: idempotency_key_collisions
  Unit: count (per minute)
  Measured: Same idempotency_key with different context
  Dimensions:
    - decision_type
    - tenant_id

  SLA: Must be zero (indicates misuse)
  Alert: Escalate to application team (usage error)
```

### 2.4 Archival Metrics

```
METRIC: archival_migration_duration_hours
  Unit: hours
  Measured: Time to migrate data from hot→warm or warm→cold
  Dimensions:
    - table (decisions | workflows | events | etc.)
    - migration_direction (hot_to_warm | warm_to_cold)
    - tenant_id

  SLA Target:
    - hot_to_warm: < 24 hours
    - warm_to_cold: < 7 days

  Alert: If migration not completed within SLA

METRIC: archival_failure_count
  Unit: count (per day)
  Measured: Number of archival jobs that failed
  Dimensions:
    - table
    - migration_direction
    - error_reason (copy_failed | verify_failed | delete_failed)

  Alert: Any failure is escalated (data integrity risk)

METRIC: cold_storage_rehydration_time_minutes
  Unit: minutes
  Measured: Time to restore data from cold to warm (if requested)
  Dimensions:
    - table
    - tenant_id

  SLA Target: < 60 minutes
  Alert: If rehydration not completed within SLA
```

### 2.5 Rule Configuration Metrics

```
METRIC: active_rules_per_decision_type
  Unit: count
  Dimensions:
    - decision_type
    - tenant_id

  Purpose: Track rule coverage
  Alert: If decision_type has 0 active rules (fail-closed)

METRIC: rule_version_distribution
  Dimensions:
    - decision_type
    - version
    - status (ACTIVE | DRAFT | DEPRECATED)

  Purpose: Track rule lifecycle

METRIC: rule_evaluation_error_count
  Unit: count (per minute)
  Dimensions:
    - decision_type
    - error_reason (condition_eval_error | timeout | etc.)

  Alert: Any evaluation error is logged (indicates misconfiguration)
```

---

## 3. Logging: What to Record

### 3.1 Decision Creation Logs (Immutable)

```
LOG EVENT: decision.created
Timestamp: occurred_at (immutable)
Fields:
  - decision_id (uuid)
  - tenant_id (partition key)
  - decision_type
  - requester_user_id
  - outcome (ALLOWED | DENIED | REQUIRE_APPROVAL)
  - rule_matched (single rule name)
  - rule_version
  - context_summary (sanitized, no PII)
  - requested_at
  - decided_at
  - latency_ms (SDK + Core time)
  - trace_id (for correlation)

Retention: Immutable, append-only
Purpose: Audit trail, compliance, explainability

Example:
  {
    "event_type": "decision.created",
    "decision_id": "dec-xyz-789",
    "tenant_id": "hotel-123",
    "outcome": "ALLOWED",
    "rule_matched": "inbound_movement_allowed",
    "latency_ms": 47,
    "trace_id": "trace-abc-123",
    "timestamp": "2025-12-27T10:30:01.050Z"
  }
```

### 3.2 Workflow State Transition Logs (Immutable)

```
LOG EVENT: workflow.state_changed
Timestamp: occurred_at (immutable)
Fields:
  - workflow_id (uuid)
  - tenant_id (partition key)
  - decision_id (link to decision)
  - from_state
  - to_state
  - action (APPROVED | REJECTED | DELEGATED | ESCALATED)
  - approver_role (role identifier)
  - acted_by_user_id (who performed action, from auth context)
  - comment (optional, for audit)
  - timestamp
  - latency_ms (state transition time)
  - trace_id (correlation)

Retention: Immutable, append-only
Purpose: Audit trail, SLA tracking, approval history

Example:
  {
    "event_type": "workflow.state_changed",
    "workflow_id": "wf-pqr-456",
    "from_state": "PENDING_APPROVAL",
    "to_state": "APPROVED",
    "acted_by_user_id": "user-cfo-001",
    "approver_role": "CFO",
    "latency_ms": 52,
    "timestamp": "2025-12-27T14:45:00Z"
  }
```

### 3.3 Security Event Logs (Critical)

```
LOG EVENT: security_violation_attempt
Timestamp: occurred_at
Fields:
  - violation_type (IMMUTABILITY_VIOLATION | TENANT_MISMATCH | UNAUTHORIZED_ROLE)
  - resource_type (decision | workflow | event_log | rule)
  - resource_id
  - tenant_id (attempted)
  - target_tenant_id (if cross-tenant)
  - attempted_action (UPDATE | DELETE | CROSS_TENANT_READ)
  - source_user_id (if identifiable)
  - source_ip (if available)
  - timestamp
  - trace_id

Retention: Immutable, long-term (7+ years for compliance)
Purpose: Security audit, intrusion detection, forensics
Alert: IMMEDIATE (critical security event)

Example:
  {
    "event_type": "security_violation_attempt",
    "violation_type": "IMMUTABILITY_VIOLATION",
    "resource_type": "decision",
    "attempted_action": "UPDATE",
    "resource_id": "dec-xyz-789",
    "tenant_id": "hotel-123",
    "timestamp": "2025-12-27T15:30:00Z"
  }
```

### 3.4 Rule Execution Logs (Debug)

```
LOG EVENT: rule_evaluation_error
Timestamp: occurred_at
Fields:
  - decision_id
  - tenant_id
  - decision_type
  - rule_id (attempted to evaluate)
  - rule_version
  - error_type (condition_eval_error | timeout | null_pointer | etc.)
  - error_message
  - context_snapshot (what was provided)
  - timestamp
  - trace_id

Retention: Hot storage only (90 days, for debugging)
Purpose: Debugging rule issues, identifying misconfiguration
Alert: Escalate to CMS admin (rule misconfiguration)

Example:
  {
    "event_type": "rule_evaluation_error",
    "decision_id": "dec-xyz-789",
    "decision_type": "accounting.journal_approval",
    "rule_id": "correction_rule_1",
    "error_type": "condition_eval_error",
    "error_message": "Field 'amount' not found in context",
    "timestamp": "2025-12-27T10:30:01Z"
  }
```

### 3.5 Archival Operation Logs (Operational)

```
LOG EVENT: archival_operation_started
Timestamp: started_at
Fields:
  - operation_id (uuid)
  - table_name (decisions | workflows | events | etc.)
  - migration_direction (hot_to_warm | warm_to_cold)
  - tenant_id_filter (or "all_tenants")
  - records_to_migrate (count)
  - source_location (hot | warm)
  - target_location (warm | cold)
  - scheduled_sla_hours
  - timestamp

LOG EVENT: archival_operation_completed
Timestamp: completed_at
Fields:
  - operation_id (same as started_at)
  - status (SUCCESS | FAILURE)
  - records_migrated (count)
  - duration_hours
  - verification_result (PASSED | FAILED)
  - timestamp

Retention: Hot storage (90 days archival log)
Purpose: Operational tracking, SLA monitoring
Alert: If status = FAILURE or duration > SLA
```

### 3.6 Compliance & Audit Logs (Long-Term)

```
LOG EVENT: rule_activated
Timestamp: occurred_at
Fields:
  - rule_id
  - decision_type
  - tenant_id
  - version
  - activated_by_user_id (CMS admin)
  - timestamp

LOG EVENT: rule_deactivated
Timestamp: occurred_at
Fields:
  - rule_id
  - version
  - deactivated_by_user_id
  - reason
  - timestamp

LOG EVENT: data_deletion_initiated
Timestamp: occurred_at
Fields:
  - deletion_reason (RETENTION_EXPIRED | LEGAL_HOLD_RELEASED | etc.)
  - table_name
  - record_count
  - date_range
  - approved_by_user_id
  - timestamp

LOG EVENT: data_deleted
Timestamp: completed_at
Fields:
  - deletion_id
  - records_deleted (count)
  - hash_of_deleted_data (for verification)
  - timestamp

Retention: Cold storage (7+ years, immutable)
Purpose: Compliance, legal discovery, audit trail
```

---

## 4. Alerting: When to Notify

### 4.1 Critical Alerts (Immediate Action Required)

```
ALERT: Immutability Violation Attempted
Trigger: immutability_violation_attempts > 0 (any attempt)
Severity: CRITICAL (P0)
Notification: Immediate to security team
Action: Investigate source, audit logs, check for intrusion
Example: "UPDATE attempted on immutable decision record from source IP X.X.X.X"

ALERT: Cross-Tenant Access Attempted
Trigger: cross_tenant_access_attempts > 0
Severity: CRITICAL (P0)
Notification: Immediate to security team
Action: Investigate source, audit access patterns
Example: "Attempted cross-tenant access: hotel-123 → restaurant-456"

ALERT: Rule Evaluation Error
Trigger: rule_evaluation_error_count > 0 (per minute)
Severity: CRITICAL (P1)
Notification: Escalate to CMS admin
Action: Investigate rule misconfiguration, fix immediately
Example: "Rule 'correction_rule_1' evaluation failed: Field 'amount' missing"

ALERT: Archival Operation Failed
Trigger: archival_failure_count > 0 (any failure)
Severity: CRITICAL (P1)
Notification: Escalate to CMS operations
Action: Investigate failure, retry migration, verify data integrity
Example: "Archival migration failed: decisions table hot→warm, copy_failed"
```

### 4.2 Warning Alerts (Timely Attention Required)

```
ALERT: Decision SLA Breach (p95)
Trigger: decision_creation_latency_ms (p95) > 150ms
Severity: HIGH (P2)
Notification: Ops team
Action: Investigate Core performance, check for resource constraints
Escalate: If p95 > 200ms (SLA breach)
Example: "Decision latency SLA breach: p95=165ms (target=100ms)"

ALERT: Workflow Approval SLA Breach
Trigger: workflow_pending_duration_minutes > escalation_timeout
Severity: HIGH (P2)
Notification: Workflow approvers team
Action: Follow up on pending approvals, check for stalled workflow
Example: "Workflow wf-xyz-789 pending > 24h (escalation timeout)"

ALERT: Archival Migration SLA Approaching
Trigger: archival_migration_duration_hours > SLA × 0.8
Severity: MEDIUM (P3)
Notification: Ops team
Action: Monitor migration, ensure completion within SLA
Example: "Migration hot→warm at 20h, SLA is 24h (80% complete)"

ALERT: Escalation Rate Spike
Trigger: workflow_escalation_count (24h) > baseline × 2
Severity: MEDIUM (P3)
Notification: Ops team
Action: Investigate approval delays, check for systemic issues
Example: "Escalations spiked to 50 (normal: 5) in last hour"
```

### 4.3 Informational Alerts (Monitoring & Tracking)

```
ALERT: Rule Configuration Changed
Trigger: rule_activated OR rule_deactivated event
Severity: INFO
Notification: CMS audit log
Action: Record for compliance, track rule versioning
Example: "Rule 'correction_rule_2' deactivated v1.2, activated v1.3"

ALERT: Idempotency Key Reused
Trigger: idempotency_key collision detected
Severity: INFO
Notification: Application team
Action: Verify expected (retry) or unexpected (bug)
Example: "Idempotency key 'req-123' reused 3x in 2 hours"

ALERT: Cold Storage Rehydration Requested
Trigger: data_rehydration_requested event
Severity: INFO
Notification: Ops team
Action: Track compliance queries, monitor rehydration SLA
Example: "Cold storage rehydration: decisions table for hotel-123 (2021-2022)"
```

---

## 5. Audit Trail: Compliance Requirements

### 5.1 Immutable Audit Log (Source of Truth)

```
AUDIT LOG TABLE: operations_audit
Partition Key: tenant_id
Sort Key: timestamp

Immutable schema:
  - audit_id (uuid, unique forever)
  - tenant_id (partition key)
  - operation_type (CREATE | READ | UPDATE_ATTEMPT | DELETE_ATTEMPT)
  - resource_type (decision | workflow | rule | event_log)
  - resource_id
  - actor_user_id (who performed action)
  - actor_role (user's role at time of action)
  - action_status (SUCCESS | FAILURE | DENIED)
  - reason_if_denied (authorization error, validation error, etc.)
  - timestamp (immutable, proof of ordering)
  - trace_id (correlation with logs)

Retention: Immutable, 7+ years (compliance)
Storage: Cold tier after 7 years (immutable archive)
Access: CMS audit querying, read-only
```

### 5.2 Explainability: Decision Audit Trail

```
For every decision, audit trail must answer:

Q1: "What decision was made?"
A: decision_id, outcome, rule_matched, rule_version

Q2: "When was it made?"
A: decided_at (immutable timestamp)

Q3: "Who requested it?"
A: requester_user_id, tenant_id

Q4: "What context was used?"
A: context_snapshot (sanitized, immutable)

Q5: "Why this outcome?"
A: rule_matched name + rule_version → explains logic

Q6: "How fast was it?"
A: latency_ms (decided_at - requested_at)

Q7: "What happened after?"
A: If REQUIRE_APPROVAL:
     - workflow_id
     - workflow.state_changes (transitions log)
     - approval records (who, when, what)

Explainability Query (CMS):
  SELECT decision_id, outcome, rule_matched, context_snapshot
  FROM decisions
  WHERE decision_id = 'dec-xyz-789'
    AND tenant_id = 'hotel-123'

  SELECT * FROM workflow_transitions
  WHERE workflow_id = (SELECT approval_workflow_id FROM decisions ...)
  ORDER BY timestamp

  Result: Complete audit trail of decision + workflow lifecycle
```

### 5.3 Compliance Queries (Audit Trail Verification)

```
Query 1: "Did any unauthorized modifications occur?"
  SELECT COUNT(*) as violation_count
  FROM operations_audit
  WHERE tenant_id = 'hotel-123'
    AND action_status = 'DENIED'
    AND operation_type IN ('UPDATE_ATTEMPT', 'DELETE_ATTEMPT')
    AND timestamp >= '2025-01-01'

  Expected: 0 (no violations)

Query 2: "Was tenant isolation maintained?"
  SELECT COUNT(*) as cross_tenant_count
  FROM operations_audit
  WHERE (source_tenant_id != target_tenant_id)
    AND timestamp >= '2025-01-01'

  Expected: 0 (no cross-tenant access)

Query 3: "Was archival SLA met?"
  SELECT COUNT(*) as missed_sla
  FROM archival_operations_audit
  WHERE status = 'FAILED'
     OR duration_hours > scheduled_sla_hours
    AND timestamp >= '2025-01-01'

  Expected: 0 (no missed SLA)

Query 4: "Which decisions were DENIED, and why?"
  SELECT decision_id, rule_matched, context_snapshot, decided_at
  FROM decisions
  WHERE tenant_id = 'hotel-123'
    AND outcome = 'DENIED'
    AND decided_at BETWEEN '2025-12-01' AND '2025-12-31'
  ORDER BY decided_at DESC

  Purpose: Audit trail for compliance report
```

---

## 6. Correlation & Traceability

### 6.1 Trace ID (Request Correlation)

```
TRACE ID: Unique identifier threaded through entire request lifecycle

Assignment:
  - SDK generates trace_id = uuid() at createDecision() call
  - OR: Application provides trace_id in SDK call
  - SDK includes trace_id in HTTP header to Core

Flow:
  Application
    ↓ (trace_id: trace-abc-123)
  SDK
    ↓ (X-Trace-ID: trace-abc-123)
  Core
    ↓ (stores trace_id in decision record)
  Event Log
    ↓ (stores trace_id in event records)
  Logs
    ↓ (all logs tagged with trace_id)

Benefit:
  grep trace_id across all logs/events/audit
  → complete request lifecycle (request → decision → events → audit)
```

### 6.2 Resource Correlation

```
Decision ID ↔ Workflow ID ↔ Approval Records ↔ Events

decision_id:
  ↓ (if outcome = REQUIRE_APPROVAL)
  approval_workflow_id in decision record

workflow_id:
  ↓ (links to)
  workflow_transitions (all state changes)
  approval records (who approved, when)
  events (workflow.approved, workflow.rejected, etc.)

Correlation Query:
  SELECT d.decision_id, d.outcome, w.workflow_id, wt.to_state
  FROM decisions d
  LEFT JOIN workflows w ON d.approval_workflow_id = w.workflow_id
  LEFT JOIN workflow_transitions wt ON w.workflow_id = wt.workflow_id
  WHERE d.decision_id = 'dec-xyz-789'
    AND d.tenant_id = 'hotel-123'

  Result: Complete decision + workflow lifecycle
```

---

## 7. Observability for Verification

### 7.1 Immutability Verification

```
Verification Process:
  1. Query decisions table for all records
     - Count = N records
     - Check outcome is not NULL (populated)

  2. Query operations_audit for UPDATE/DELETE attempts
     - Count should be 0 (no successful modifications)
     - Any attempts logged as security_violation_attempt

  3. Verify no orphaned records
     - Every workflow has corresponding decision
     - Every approval_record has corresponding workflow

  4. Spot-check immutability at storage layer
     - Verify WORM/Object Lock enabled on cold tier
     - Verify role-based permissions (REVOKE UPDATE/DELETE)
     - Verify triggers in place (reject UPDATE/DELETE)

  Result: Immutability verified end-to-end
```

### 7.2 Tenant Isolation Verification

```
Verification Process:
  1. Query cross_tenant_access_attempts metric
     - Count must be 0 (no cross-tenant access)

  2. Verify RLS policies or schema-per-tenant
     - SELECT without tenant_id must return 0 rows
     - OR: Must fail with authorization error

  3. Audit queries by tenant
     - Verify no tenant queries other tenant's data
     - Check audit trail for tenant_id in WHERE clause

  4. Review operations_audit for tenant mismatches
     - Check for source_tenant != target_tenant
     - Must be 0 (no unauthorized cross-tenant operations)

  Result: Tenant isolation verified end-to-end
```

### 7.3 SLA Compliance Verification

```
Verification Process:
  1. Query decision_creation_latency_ms metric
     - p95 <= 100ms (within SLA)
     - p99 <= 200ms (acceptable)

  2. Query workflow_pending_duration_minutes
     - Average approval time (operational SLA)
     - Alert if > escalation_timeout

  3. Query archival_migration_duration_hours
     - hot_to_warm: Must complete within 24h
     - warm_to_cold: Must complete within 7d

  4. Review alert history
     - Check if SLA breaches were alerted
     - Verify corrective actions taken

  Result: SLA compliance verified via metrics & alerts
```

---

## 8. Summary: Observability is Foundational

✅ **Metrics**: Decision latency, workflow SLA, archival SLA, immutability attempts
✅ **Logging**: Immutable audit trail (decisions, workflows, security events, rules, archival)
✅ **Alerting**: Critical (P0), Warning (P2), Informational (INFO)
✅ **Audit Trail**: Source of truth for compliance, explainability
✅ **Correlation**: Trace ID threads through entire request lifecycle
✅ **Verification**: Immutability, tenant isolation, SLA compliance all auditable

**Status**: Monitoring & Observability requirements complete, ready for review.

**Next**: Await feedback, then lock Layer 2.4, then conclude Layer 2 or continue to remaining scope.
