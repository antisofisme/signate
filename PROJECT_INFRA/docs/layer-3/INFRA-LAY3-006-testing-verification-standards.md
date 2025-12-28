# INFRA-LAY3-006: Testing & Verification Standards

**VERSION**: Layer 3 DRAFT
**STATUS**: IN PROGRESS
**DATE**: 2025-12-28

---

## Overview

This document defines **testing and verification standards** for Infra implementation.

- **Scope**: Unit testing, integration testing, load testing, security testing, chaos testing, verification patterns
- **Source of Truth**: All Layer 0-3 standards are test requirements
- **Constraint**: Every guarantee must be verifiable by automated tests

**Key Principle**: **Verify before shipping.** Every architectural guarantee (immutability, tenant isolation, determinism, SLA) must be proven by automated tests.

---

## 1. Unit Testing Standards

### 1.1 SDK Unit Tests

```
REQUIREMENT: Test all SDK functions independently.

Test Suite: SDK Validation

TEST 1: validate_tenant_id
  Input: various tenant_id formats
  Cases:
    - Valid: "hotel-123" → pass
    - Invalid (too short): "a-b" → fail
    - Invalid (pattern): "HOTEL-123" (uppercase) → fail
    - Null: null → fail
    - Empty: "" → fail

TEST 2: validate_decision_type
  Input: various decision_type formats
  Cases:
    - Valid: "accounting.journal_approval" → pass
    - Invalid (missing module): "journal_approval" → fail
    - Invalid (uppercase): "Accounting.Journal_Approval" → fail
    - Invalid (4 parts): "a.b.c.d" → fail

TEST 3: sanitize_context
  Input: context with various fields
  Cases:
    - Valid: {user_id: "u-1", amount: 5000} → pass
    - Invalid (PII): {email: "user@company.com"} → fail
    - Invalid (credential): {password: "secret123"} → fail
    - Mixed: {user_id: "u-1", email: "x@y.com"} → fail (contains email)

TEST 4: validate_idempotency_key
  Input: various key formats
  Cases:
    - Valid: "req-abc-123" → pass
    - Valid (uuid): "550e8400-e29b-41d4-a716-446655440000" → pass
    - Invalid (special): "req$abc!" → fail
    - Too long: "a" * 256 → fail

Test Suite: SDK HTTP Client

TEST 5: classify_http_error
  Input: HTTP status codes
  Cases:
    - 400 (Bad Request): retriable=false
    - 401 (Unauthorized): retriable=false
    - 403 (Forbidden): retriable=false
    - 409 (Conflict): retriable=false
    - 500 (Server Error): retriable=true
    - 503 (Unavailable): retriable=true
    - timeout: retriable=true

TEST 6: retry_logic
  Input: simulated failures
  Cases:
    - First attempt succeeds: attempts=1
    - Second attempt succeeds: attempts=2
    - Max attempts exhausted: attempts=3, throws
    - Non-retriable error: attempts=1, throws immediately
    - Jitter added: exponential backoff within bounds

Test Suite: SDK Idempotency

TEST 7: idempotency_key_handling
  Input: idempotency_key provided or not
  Cases:
    - Not provided: SDK generates uuid
    - Provided: SDK uses as-is
    - Same key, same request: returns cached decision_id
    - Same key, different request: 409 Conflict

Implementation Pattern (Jest/Mocha):

  describe('SDK Validation', () => {
    test('validate_tenant_id: valid format', () => {
      expect(validate_tenant_id('hotel-123')).toBe(true);
    });

    test('validate_tenant_id: invalid format', () => {
      expect(() => validate_tenant_id('HOTEL-123'))
        .toThrow('INVALID_TENANT_ID');
    });

    test('sanitize_context: rejects PII', () => {
      const context = {user_id: 'u-1', email: 'x@y.com'};
      expect(() => sanitize_context(context))
        .toThrow('CONTEXT_CONTAINS_PII');
    });

    test('retry_logic: exponential backoff', () => {
      const delays = simulate_retry_delays(3);
      expect(delays[0]).toBeCloseTo(100, -1);      // ~100ms
      expect(delays[1]).toBeCloseTo(200, -1);      // ~200ms
      expect(delays[2]).toBeCloseTo(400, -1);      // ~400ms
    });
  });
```

### 1.2 Core Service Unit Tests

```
REQUIREMENT: Test rule evaluation, decision creation, workflow state machine.

Test Suite: Rule Evaluation (Determinism)

TEST 1: first_match_wins
  Rule Set:
    1. amount > 10000 → DENY
    2. department == 'accounting' → ALLOW
    3. default → REQUIRE_APPROVAL
  Test Cases:
    - Context {amount: 15000, dept: 'accounting'} → DENY (rule 1 matches)
    - Context {amount: 5000, dept: 'accounting'} → ALLOW (rule 2 matches)
    - Context {amount: 5000, dept: 'sales'} → REQUIRE_APPROVAL (rule 3 matches)

TEST 2: determinism
  Same (rule_set, context) run 100 times → always same outcome
  Seed random with same value → verify reproducible

TEST 3: condition_nesting_depth
  Invalid (depth 4): ((((A AND B) OR C) AND D)) → fail
  Valid (depth 3): (((A AND B) OR C) AND D) → pass

TEST 4: null_field_handling
  Context: {} (missing field)
  Rule: context.amount > 10000
  Result: Condition FALSE (null > 10000 is false)

TEST 5: type_mismatch_error
  Context: {amount: "fifteen thousand"} (string, not number)
  Rule: context.amount > 10000
  Result: Error logged, outcome DENIED

Test Suite: Decision Creation Transaction

TEST 6: atomicity
  Simulate failure at step 5 (workflow insert)
  Verify: decision NOT created (rollback)
  Verify: no orphaned workflow

TEST 7: immutability_lock
  Decision created with outcome=ALLOWED
  Attempt UPDATE: outcome=DENIED
  Result: Trigger rejects, exception thrown
  Verify: database logs UPDATE_ATTEMPT in audit

TEST 8: idempotency_deduplication
  Request 1: decision_id='dec-1', outcome='ALLOWED', idempotency_key='req-1'
  Request 2 (retry): same context, same idempotency_key
  Result: decision_id='dec-1' returned (cached, no new decision)

Test Suite: Workflow State Machine

TEST 9: state_transition_rules
  Cases:
    - PENDING_APPROVAL → APPROVED: allowed
    - PENDING_APPROVAL → REJECTED: allowed
    - APPROVED → REJECTED: forbidden
    - REJECTED → APPROVED: forbidden
    - Invalid state: rejected

TEST 10: delegation_flow
  PENDING_APPROVAL → DELEGATED (preserved in transitions table)
  → PENDING_APPROVAL (delegate complete)
  Verify: workflow_transitions has 2 records

Implementation Pattern:

  describe('Rule Evaluation', () => {
    test('first_match_wins: amount > 10000 matches', () => {
      const rules = load_test_rules('high_amount_rules');
      const context = {amount: 15000, department: 'accounting'};
      const result = evaluate_rules(rules, context);
      expect(result.outcome).toBe('DENY');
      expect(result.rule_matched).toBe('amount_over_10k_rule');
    });

    test('determinism: same context = same outcome', () => {
      const outcomes = [];
      for (let i = 0; i < 100; i++) {
        outcomes.push(evaluate_rules(rules, context).outcome);
      }
      const unique_outcomes = new Set(outcomes);
      expect(unique_outcomes.size).toBe(1);  // all same
    });
  });
```

### 1.3 Data Layer Unit Tests

```
REQUIREMENT: Test immutability triggers, RLS policies, indexes.

Test Suite: Immutability Triggers

TEST 1: prevent_decisions_update
  INSERT decision record
  Attempt: UPDATE decisions SET outcome='DENIED' WHERE decision_id=?
  Result: Exception "Immutable table" raised
  Verify: audit log has UPDATE_ATTEMPT entry

TEST 2: prevent_event_log_delete
  INSERT event record
  Attempt: DELETE FROM event_log WHERE event_id=?
  Result: Exception raised, row NOT deleted
  Verify: audit log has DELETE_ATTEMPT entry

TEST 3: audit_logging_on_violation
  Attempt UPDATE on immutable table
  Verify: operations_audit has entry with:
    - operation_type: 'UPDATE_ATTEMPT'
    - resource_id: affected record
    - action_status: 'DENIED'

Test Suite: RLS Policies

TEST 4: rls_enforces_tenant_isolation
  SET app.current_tenant_id = 'hotel-123'
  SELECT * FROM decisions
  Result: Only decisions with tenant_id='hotel-123' returned

  SET app.current_tenant_id = 'restaurant-456'
  SELECT * FROM decisions
  Result: Only decisions with tenant_id='restaurant-456' returned

TEST 5: rls_prevents_cross_tenant_insert
  SET app.current_tenant_id = 'hotel-123'
  INSERT INTO decisions (tenant_id='restaurant-456', ...)
  Result: Exception "check policy violated"

Test Suite: Indexing

TEST 6: index_supports_critical_queries
  EXPLAIN PLAN: SELECT * FROM decisions WHERE tenant_id=? AND created_at > ?
  Verify: Uses index (not full table scan)
  Verify: Estimated rows < actual returned (index selectivity good)

TEST 7: index_does_not_slow_inserts
  Baseline: 10,000 INSERTs without index (record time)
  With index: 10,000 INSERTs with index (compare time)
  Verify: Index insertion overhead < 10% (acceptable)

Implementation Pattern (PostgreSQL):

  BEGIN;
    -- Test immutability
    INSERT INTO decisions (decision_id, tenant_id, outcome, created_at)
    VALUES ('dec-1', 'hotel-123', 'ALLOWED', now());

    -- Try to update
    UPDATE decisions SET outcome='DENIED' WHERE decision_id='dec-1';
    -- Should fail with exception

  ROLLBACK;

  -- Test RLS
  SET app.current_tenant_id = 'hotel-123';
  SELECT COUNT(*) FROM decisions;  -- should return 0 (no data for this tenant)

  SET app.current_tenant_id = 'restaurant-456';
  SELECT COUNT(*) FROM decisions;  -- should return 0 (different tenant)
```

---

## 2. Integration Testing Standards

### 2.1 Happy Path Tests

```
REQUIREMENT: Test complete workflows end-to-end.

Test Suite: Decision Creation (Happy Path)

TEST 1: Decision.ALLOWED
  Setup:
    - Create rule: amount < 5000 → ALLOW
    - Activate rule
  Flow:
    1. SDK calls Core: createDecision("acct.journal", {amount: 3000}, tenant)
    2. Core evaluates rules → ALLOW
    3. Core persists decision → decision_id returned
    4. Core publishes event → event_log has entry
  Verify:
    - decision.outcome == 'ALLOWED'
    - decision.rule_matched == 'amount_under_5k_rule'
    - event_log has 'decision.created' entry
    - latency_ms < 100

TEST 2: Decision.REQUIRE_APPROVAL
  Setup:
    - Create rule: amount > 10000 → REQUIRE_APPROVAL (approver_role='CFO')
  Flow:
    1. SDK calls Core: createDecision with amount=15000
    2. Core creates decision (outcome=REQUIRE_APPROVAL)
    3. Core creates workflow (state=PENDING_APPROVAL)
    4. Core publishes events → decision.created, workflow.pending_approval
  Verify:
    - decision.approval_workflow_id is set
    - workflow.current_state == 'PENDING_APPROVAL'
    - 2 events in event_log (decision + workflow)

TEST 3: Workflow.APPROVED
  Setup:
    - Previous decision with REQUIRE_APPROVAL
    - Workflow in PENDING_APPROVAL state
  Flow:
    1. SDK calls Core: approveWorkflow(workflow_id, approver_role='CFO')
    2. Core verifies role matches
    3. Core inserts workflow_transition (PENDING → APPROVED)
    4. Core publishes event
  Verify:
    - workflow.current_state == 'APPROVED'
    - workflow.completed_at is set
    - workflow_transitions has entry
    - event_log has 'workflow.approved' entry

Test Suite: Idempotency

TEST 4: Idempotency Works
  Flow:
    1. First request: createDecision(decision_type, context, tenant, idempotency_key='req-1')
       Result: decision_id='dec-1', latency=80ms
    2. Retry (same request): createDecision(..., idempotency_key='req-1')
       Result: decision_id='dec-1' (same), latency=5ms (cache hit)
    3. Third retry (same request):
       Result: decision_id='dec-1', latency=4ms (cache hit)

TEST 5: Conflict Detection
  Flow:
    1. First request: createDecision({amount: 5000}, idempotency_key='req-1')
       Result: decision_id='dec-1'
    2. Retry with different context: createDecision({amount: 10000}, idempotency_key='req-1')
       Result: 409 Conflict error
       Message: "Idempotency key 'req-1' already used with different context"

Implementation Pattern (Jest):

  describe('Integration: Decision Creation', () => {
    test('Decision.ALLOWED: happy path', async () => {
      // Setup
      const rule = await cms.create_rule({
        decision_type: 'acct.journal',
        conditions: 'amount < 5000',
        action: {outcome: 'ALLOWED'}
      });
      await cms.activate_rule(rule.rule_id);

      // Act
      const decision = await sdk.createDecision(
        'acct.journal',
        {amount: 3000},
        'hotel-123'
      );

      // Assert
      expect(decision.outcome).toBe('ALLOWED');
      expect(decision.decision_id).toBeDefined();
      expect(decision.latency_ms).toBeLessThan(100);

      // Verify event logged
      const events = await core.query_events({
        aggregate_id: decision.decision_id
      });
      expect(events).toHaveLength(1);
      expect(events[0].event_type).toBe('decision.created');
    });

    test('Idempotency: same request returns cached result', async () => {
      const result1 = await sdk.createDecision(
        'acct.journal',
        {amount: 3000},
        'hotel-123',
        {idempotency_key: 'req-1'}
      );

      const result2 = await sdk.createDecision(
        'acct.journal',
        {amount: 3000},
        'hotel-123',
        {idempotency_key: 'req-1'}
      );

      expect(result1.decision_id).toBe(result2.decision_id);
      expect(result2.latency_ms).toBeLessThan(result1.latency_ms);
    });
  });
```

### 2.2 Error Path Tests

```
REQUIREMENT: Test error scenarios and recovery.

Test Suite: Validation Errors

TEST 1: SDK rejects invalid tenant_id
  Input: createDecision(..., tenant_id='HOTEL-123')
  Expected: 400 ValidationError "INVALID_TENANT_ID"
  Verify: Request NOT sent to Core

TEST 2: SDK rejects PII in context
  Input: createDecision(..., context={email: 'user@company.com'})
  Expected: 400 ValidationError "CONTEXT_CONTAINS_PII"
  Verify: Request NOT sent to Core

TEST 3: Core rejects invalid rule
  Setup: Create rule with invalid condition syntax
  Act: Activate rule
  Expected: 400 "INVALID_RULE" or fail at activation

Test Suite: Immutability Violations

TEST 4: Immutability violation logged
  Setup: Create decision
  Act: Attempt UPDATE (via SQL injection or admin tool)
  Expected: Trigger raises exception
  Verify: operations_audit has UPDATE_ATTEMPT entry
  Verify: Alert triggered (P0 security event)

Test Suite: Tenant Isolation

TEST 5: Cross-tenant access rejected
  Setup:
    - Tenant A creates decision: decision_id='dec-a'
    - Tenant B tries to access: getDecision('dec-a', tenant_b)
  Expected: 403 Forbidden or 0 results
  Verify: RLS policy enforced

TEST 6: Cross-tenant insert rejected
  Act: INSERT INTO decisions (tenant_id='OTHER-TENANT') as Tenant A
  Expected: RLS CHECK constraint violation
  Verify: Insert fails

Test Suite: Timeout & Retries

TEST 7: Network timeout triggers retry
  Setup: Simulate Core timeout on first attempt
  Act: SDK calls createDecision
  Expected: SDK retries, succeeds on second attempt
  Verify: Latency > retry delay (e.g., 150ms)

TEST 8: Max retries exhausted
  Setup: Simulate Core unavailable (all retries fail)
  Act: SDK calls createDecision
  Expected: TooManyRetriesError after 3 attempts
  Verify: Each attempt logged, alert triggered

Implementation Pattern:

  describe('Integration: Error Paths', () => {
    test('SDK rejects invalid tenant_id', async () => {
      const error = await sdk.createDecision(
        'acct.journal',
        {amount: 3000},
        'HOTEL-123'  // invalid
      ).catch(e => e);

      expect(error.error_code).toBe('VALIDATION_ERROR');
      expect(error.reason).toBe('INVALID_TENANT_ID');
    });

    test('Cross-tenant access rejected', async () => {
      // Create decision as tenant-a
      const decision = await sdk.createDecision(..., 'tenant-a');

      // Try to access as tenant-b
      const error = await sdk.getDecision(
        decision.decision_id,
        'tenant-b'
      ).catch(e => e);

      expect(error.status).toBe(403);
      expect(error.message).toContain('Forbidden');
    });
  });
```

---

## 3. Load Testing Standards

### 3.1 Latency SLA Verification

```
REQUIREMENT: Verify SLA targets under load.

SLA Targets (from INFRA-LAY2-002):

Decision Creation:
  - p50: < 50ms
  - p95: < 100ms
  - p99: < 200ms

Workflow Approval:
  - p95: < 100ms
  - p99: < 200ms

Load Testing Setup:

Tools: Apache JMeter, Locust, or k6

Configuration:
  - Concurrent users: 100, 500, 1000, 5000
  - Duration: 10 minutes each
  - Ramp-up: 60 seconds
  - Request type: createDecision (50%), getDecision (30%), approveWorkflow (20%)

Test Scenario:

SCENARIO 1: 100 concurrent users
  Expected:
    - p95 < 100ms
    - p99 < 200ms
    - Error rate < 0.1%
    - Throughput: 1000 req/sec

SCENARIO 2: 1000 concurrent users
  Expected:
    - p95 < 150ms (degradation acceptable)
    - p99 < 250ms
    - Error rate < 0.1%
    - Throughput: 5000 req/sec

SCENARIO 3: 5000 concurrent users
  Expected:
    - p95 < 200ms (max acceptable)
    - p99 < 300ms
    - Error rate < 1% (acceptable under extreme load)
    - Throughput: 10000 req/sec

Load Test Script (k6):

import http from 'k6/http';
import {check, sleep} from 'k6';

export let options = {
  stages: [
    {duration: '1m', target: 100},   // ramp up
    {duration: '5m', target: 100},   // sustain
    {duration: '1m', target: 0}       // ramp down
  ]
};

export default function() {
  // Create decision
  const decision_payload = {
    decision_type: 'accounting.journal_approval',
    tenant_id: `hotel-${Math.floor(Math.random() * 100)}`,
    context: {amount: Math.random() * 50000}
  };

  const decision_response = http.post(
    'https://api.infra.internal/decisions',
    JSON.stringify(decision_payload),
    {headers: {'Content-Type': 'application/json'}}
  );

  check(decision_response, {
    'status is 200': (r) => r.status === 200,
    'latency < 100ms': (r) => r.timings.duration < 100,
    'body has decision_id': (r) => r.json('decision_id') !== undefined
  });

  sleep(0.1);  // 100ms between requests per user
}

Analysis:

After test:
  1. Export results to CSV
  2. Calculate p50, p95, p99 latencies
  3. Compare against SLA targets
  4. Identify bottleneck:
     - Is it SDK validation?
     - Is it Core rule evaluation?
     - Is it database query?
     - Is it network latency?
  5. If SLA breached:
     - Optimize bottleneck
     - Re-test
     - Document root cause
```

### 3.2 Throughput & Resource Utilization

```
REQUIREMENT: Measure throughput and resource usage.

Metrics:

Throughput:
  - Requests per second (target: 5000+ req/sec)
  - Decisions per second (target: 5000 decisions/sec)
  - Events published per second (target: 5000 events/sec)

Resource Utilization:
  - CPU: target < 70% (headroom for spikes)
  - Memory: target < 80%
  - Network bandwidth: target < 60%
  - Database connections: target < 80% of pool

Monitoring During Load Test:

  - Real-time dashboard: CPU, memory, network, latency
  - Alerts: if p95 > 150ms or CPU > 80%
  - Database queries: identify slow queries
  - Error logs: track error rate

Scaling Test:

  1. Baseline (100 concurrent): p95=47ms, CPU=30%, connections=25
  2. 500 concurrent: p95=52ms, CPU=55%, connections=120
  3. 1000 concurrent: p95=78ms, CPU=72%, connections=240
  4. 2000 concurrent: p95=130ms (breach!), CPU=85%, connections=480

Analysis:
  - SLA breached at 2000 concurrent
  - Scaling point identified
  - Need to increase resources or optimize code
```

---

## 4. Security Testing Standards

### 4.1 Immutability Verification

```
REQUIREMENT: Verify immutability enforcement at all layers.

Test Suite: Immutability Layers

TEST 1: DB Role Permissions
  Act: Connect as infra_writer role, attempt UPDATE
  Expected: Permission denied
  Command: UPDATE decisions SET outcome='DENIED' WHERE decision_id=?
  Result: ERROR: permission denied for relation decisions

TEST 2: Database Triggers
  Act: Disable role permissions, attempt UPDATE via trigger
  Expected: Trigger raises exception
  Command: UPDATE decisions SET outcome='DENIED' WHERE decision_id=?
  Result: Exception: "Immutable table: decisions cannot be modified"

TEST 3: Storage Locks (Warm/Cold)
  Act: Copy archived file from warm storage, attempt modification
  Expected: WORM storage prevents modification
  Expected: Signature/hash mismatch detected

Verification Query:

  -- No UPDATEs should succeed
  SELECT COUNT(*) FROM decisions WHERE updated_at > created_at;
  Expected: 0

  -- No DELETEs should succeed
  SELECT COUNT(*) FROM decisions WHERE deleted_at IS NOT NULL;
  Expected: 0
```

### 4.2 Tenant Isolation Verification

```
REQUIREMENT: Verify tenant isolation enforced at database layer.

Test Suite: RLS Enforcement

TEST 1: RLS filters queries
  Setup:
    - hotel-123: 100 decisions
    - restaurant-456: 50 decisions
  Act:
    - SET app.current_tenant_id = 'hotel-123'
    - SELECT COUNT(*) FROM decisions
  Expected: 100 (only hotel-123 decisions)

  Act:
    - SET app.current_tenant_id = 'restaurant-456'
    - SELECT COUNT(*) FROM decisions
  Expected: 50 (only restaurant-456 decisions)

TEST 2: RLS prevents cross-tenant INSERT
  Act:
    - SET app.current_tenant_id = 'hotel-123'
    - INSERT INTO decisions (tenant_id='restaurant-456', ...)
  Expected: Exception "check policy violated"

TEST 3: Query without tenant_id context
  Act:
    - SELECT COUNT(*) FROM decisions
    - (No tenant_id filter in WHERE clause)
  Expected: RLS still applies (zero rows or error)

TEST 4: Cross-tenant access detected
  Act:
    - Attempt to fetch decision from wrong tenant
    - SQL: SELECT * FROM decisions WHERE decision_id=? AND tenant_id != current_tenant
  Expected: 0 rows (RLS silently filters)
  Verify: operations_audit logs cross_tenant_access_attempt
```

### 4.3 PII Rejection Verification

```
REQUIREMENT: Verify PII fields rejected in context.

Test Suite: PII Field Detection

TEST 1: Email rejected
  Input: {user_id: 'u-1', email: 'user@company.com'}
  Expected: 400 "CONTEXT_CONTAINS_PII"

TEST 2: Phone rejected
  Input: {user_id: 'u-1', phone: '555-1234'}
  Expected: 400 "CONTEXT_CONTAINS_PII"

TEST 3: SSN rejected
  Input: {user_id: 'u-1', ssn: '123-45-6789'}
  Expected: 400 "CONTEXT_CONTAINS_PII"

TEST 4: Password rejected
  Input: {user_id: 'u-1', password: 'secret123'}
  Expected: 400 "CONTEXT_CONTAINS_PII"

TEST 5: Credit card rejected
  Input: {user_id: 'u-1', credit_card: '4111-1111-1111-1111'}
  Expected: 400 "CONTEXT_CONTAINS_PII"

Comprehensive PII Test:

  const forbidden_fields = [
    'email', 'phone', 'ssn', 'password', 'credit_card',
    'passport_number', 'driver_license', 'salary', 'dob',
    'medical_record', 'fingerprint', 'api_key', 'secret'
  ];

  for (const field of forbidden_fields) {
    const context = {user_id: 'u-1', [field]: 'value'};
    const error = await sdk.createDecision(..., context).catch(e => e);
    expect(error.reason).toBe('CONTEXT_CONTAINS_PII');
    expect(error.details.forbidden_fields).toContain(field);
  }
```

---

## 5. Chaos Testing Standards

### 5.1 Fault Injection

```
REQUIREMENT: Test system behavior under failure conditions.

Chaos Experiments:

EXPERIMENT 1: Database Unavailable
  Setup:
    - Start load test (100 concurrent users)
    - After 30 seconds, shut down database
  Expected Behavior:
    - SDK gets 503 Service Unavailable
    - SDK retries (exponential backoff)
    - Circuit breaker opens (fail fast)
    - Users see timeout error
    - Alert triggered (P0)
  Recovery:
    - Restart database
    - Circuit breaker closes
    - Requests resume
    - Total downtime < 2 minutes

EXPERIMENT 2: Network Latency Spike
  Setup:
    - Inject 500ms latency to Core API
    - Measure SLA impact
  Expected Behavior:
    - Latencies increase (500ms network + processing)
    - p95 SLA breached
    - Alert triggered (P2 SLA breach)
    - No errors (just slower)
  Recovery:
    - Latency normalized
    - SLA restored
    - Verify no data loss

EXPERIMENT 3: Event Bus Unavailable
  Setup:
    - Shut down Kafka broker
    - Create decision (event publishing will fail)
  Expected Behavior:
    - Decision created successfully (persisted to event_log)
    - Event publication fails (best-effort)
    - Decision returned to SDK (latency not affected)
    - Alert triggered (P1 event bus unavailable)
  Recovery:
    - Restart Kafka
    - Consumer reprocesses events from event_log
    - No decision loss

EXPERIMENT 4: Database Corruption
  Setup:
    - Corrupt decision record (modify outcome)
    - Query decision
  Expected Behavior:
    - Trigger detects corruption (if UPDATE attempted)
    - Immutability violation logged
    - Alert triggered (P0 security event)

Chaos Framework:

  Tools: Chaos Monkey, Gremlin, or custom scripts

  Configuration:

  {
    "experiments": [
      {
        "name": "database_unavailable",
        "target": "postgresql_pod",
        "action": "stop_process",
        "duration": "2m",
        "schedule": "daily",
        "alerts": ["p0_database_down"]
      },
      {
        "name": "network_latency",
        "target": "core_api",
        "action": "add_latency",
        "latency_ms": 500,
        "duration": "5m",
        "alerts": ["p2_sla_breach"]
      }
    ]
  }
```

---

## 6. End-to-End Testing Standards

### 6.1 Complete Request Flow

```
REQUIREMENT: Test complete flow from SDK to database to events.

E2E Test Scenario:

FLOW: Decision.REQUIRE_APPROVAL → Workflow.APPROVED → Events

Step 1: SDK calls Core
  POST /decisions HTTP/1.1
  {
    decision_type: 'acct.journal',
    tenant_id: 'hotel-123',
    context: {amount: 15000},
    idempotency_key: 'e2e-test-1'
  }

Step 2: Core processes (trace_id: 'trace-1')
  - Validates request
  - Evaluates rules
  - Creates decision {decision_id: 'dec-1', outcome: 'REQUIRE_APPROVAL'}
  - Creates workflow {workflow_id: 'wf-1', state: 'PENDING_APPROVAL'}
  - Creates event {event_id: 'evt-1', type: 'decision.created'}

Step 3: Verify database state
  SELECT * FROM decisions WHERE decision_id = 'dec-1'
  → outcome='REQUIRE_APPROVAL', approval_workflow_id='wf-1'

  SELECT * FROM workflows WHERE workflow_id = 'wf-1'
  → current_state='PENDING_APPROVAL', decision_id='dec-1'

  SELECT * FROM event_log WHERE event_id = 'evt-1'
  → event_type='decision.created', payload contains 'dec-1'

Step 4: Approve workflow
  POST /workflows/wf-1/approve HTTP/1.1
  {
    approver_role: 'CFO',
    tenant_id: 'hotel-123',
    comment: 'Approved'
  }

Step 5: Verify state transitions
  SELECT * FROM workflow_transitions WHERE workflow_id = 'wf-1'
  → Record 1: PENDING_APPROVAL → APPROVED

  SELECT * FROM workflows WHERE workflow_id = 'wf-1'
  → current_state='APPROVED', completed_at IS NOT NULL

  SELECT * FROM event_log WHERE aggregate_id = 'wf-1'
  → event_type='workflow.approved'

Step 6: Verify event bus
  Kafka consumer receives event
  → event_type='workflow.approved'
  → aggregate_id='wf-1'
  → metadata.trace_id='trace-1'

Step 7: Verify audit trail
  SELECT * FROM operations_audit WHERE resource_id IN ('dec-1', 'wf-1')
  → Operation 1: CREATE decision
  → Operation 2: CREATE workflow
  → Operation 3: UPDATE workflow (state change)

Implementation Pattern (Cypress):

  describe('E2E: Decision Creation & Approval', () => {
    it('creates decision and approves workflow', () => {
      const trace_id = 'e2e-test-1';

      // Step 1: Create decision
      cy.request('POST', '/api/decisions', {
        decision_type: 'acct.journal',
        tenant_id: 'hotel-123',
        context: {amount: 15000},
        idempotency_key: trace_id
      }).then((response) => {
        const {decision_id, approval_workflow_id} = response.body;

        // Step 2: Verify database
        cy.query_database(`
          SELECT outcome FROM decisions WHERE decision_id='${decision_id}'
        `).should('include', 'REQUIRE_APPROVAL');

        // Step 3: Approve workflow
        cy.request('POST', `/api/workflows/${approval_workflow_id}/approve`, {
          approver_role: 'CFO',
          tenant_id: 'hotel-123'
        }).then((approve_response) => {
          const {current_state} = approve_response.body;

          // Step 4: Verify state
          expect(current_state).toBe('APPROVED');

          // Step 5: Verify events
          cy.query_database(`
            SELECT COUNT(*) FROM event_log WHERE aggregate_id='${approval_workflow_id}'
          `).should('equal', 2);  // decision.created + workflow.approved
        });
      });
    });
  });
```

---

## 7. Verification Patterns

### 7.1 Guarantee Verification

```
REQUIREMENT: Automated verification of all architectural guarantees.

Guarantee 1: Immutability Verification

  Automated Test:
    STEP 1: Query decisions table
      SELECT COUNT(*) as total FROM decisions;

    STEP 2: Query update attempts
      SELECT COUNT(*) as failed_updates
      FROM operations_audit
      WHERE operation_type='UPDATE_ATTEMPT';

    STEP 3: Verify
      Assert: failed_updates == 0 (OR all are DENIED status)
      Assert: No decision has updated_at > created_at

  Frequency: Daily
  Pass/Fail: Alert if failed_updates > 0

Guarantee 2: Tenant Isolation Verification

  Automated Test:
    STEP 1: Query cross-tenant attempts
      SELECT COUNT(*) as violations
      FROM operations_audit
      WHERE (source_tenant_id != target_tenant_id);

    STEP 2: Query RLS enforcement
      SET app.current_tenant_id = 'hotel-123';
      SELECT COUNT(*) as other_tenant_decisions
      FROM decisions
      WHERE tenant_id != 'hotel-123';

    STEP 3: Verify
      Assert: violations == 0
      Assert: other_tenant_decisions == 0

  Frequency: Daily
  Pass/Fail: Alert if violations > 0

Guarantee 3: SLA Compliance Verification

  Automated Test:
    STEP 1: Query latency metrics
      SELECT
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99
      FROM decisions
      WHERE created_at > now() - interval 1 hour;

    STEP 2: Verify
      Assert: p95 < 100ms
      Assert: p99 < 200ms
      Alert if breached

  Frequency: Hourly
  Pass/Fail: Alert if SLA breached

Guarantee 4: Event Consistency Verification

  Automated Test:
    STEP 1: Check for orphaned decisions (decision without event)
      SELECT COUNT(*) as orphaned
      FROM decisions d
      WHERE NOT EXISTS (
        SELECT 1 FROM event_log
        WHERE event_type='decision.created' AND aggregate_id=d.decision_id
      );

    STEP 2: Check for orphaned workflows (workflow without decision)
      SELECT COUNT(*) as orphaned
      FROM workflows w
      WHERE NOT EXISTS (
        SELECT 1 FROM decisions WHERE decision_id=w.decision_id
      );

    STEP 3: Verify
      Assert: orphaned == 0 (for both)
      Alert if orphaned > 0

  Frequency: Daily
  Pass/Fail: Alert if orphaned records found
```

---

## 8. Testing Implementation Checklist

```
Before releasing, verify all tests pass:

UNIT TESTS:
  ✓ SDK validation (tenant_id, decision_type, context, idempotency_key)
  ✓ SDK HTTP error classification (retriable, non-retriable)
  ✓ SDK retry logic (exponential backoff, jitter)
  ✓ Core rule evaluation (determinism, first-match, nesting)
  ✓ Core decision transaction (atomicity, idempotency)
  ✓ Core workflow state machine (transitions, terminal states)
  ✓ Data layer immutability (triggers, role permissions)
  ✓ Data layer RLS policies (tenant isolation)
  ✓ Data layer indexing (query plans)

INTEGRATION TESTS:
  ✓ Decision creation (happy path)
  ✓ Decision outcomes (ALLOWED, DENIED, REQUIRE_APPROVAL)
  ✓ Workflow approval (state transitions)
  ✓ Idempotency (cached decisions, conflict detection)
  ✓ Immutability violations (trigger enforcement)
  ✓ Tenant isolation (cross-tenant rejection)
  ✓ Validation errors (400 responses)
  ✓ Timeout & retries (error recovery)

LOAD TESTS:
  ✓ p95 < 100ms (at 100 concurrent users)
  ✓ p95 < 150ms (at 1000 concurrent users)
  ✓ p95 < 200ms (at 5000 concurrent users)
  ✓ Throughput: 5000+ req/sec
  ✓ CPU < 70%, Memory < 80%
  ✓ Error rate < 0.1% under load

SECURITY TESTS:
  ✓ Immutability (3-layer enforcement)
  ✓ Tenant isolation (RLS enforcement)
  ✓ PII rejection (all forbidden fields)
  ✓ Cross-tenant access prevention
  ✓ Audit logging (all violations logged)

CHAOS TESTS:
  ✓ Database unavailable (circuit breaker)
  ✓ Network latency (SLA impact)
  ✓ Event bus unavailable (decision survives)
  ✓ Database corruption (detected & alerted)

E2E TESTS:
  ✓ Complete decision flow (SDK → Core → Database → Events)
  ✓ Workflow approval flow
  ✓ Event propagation
  ✓ Audit trail completeness

VERIFICATION TESTS:
  ✓ Immutability verification (daily)
  ✓ Tenant isolation verification (daily)
  ✓ SLA compliance verification (hourly)
  ✓ Event consistency verification (daily)
  ✓ No data loss (continuous)
```

---

## 9. Summary: Testing as Guarantee Verification

✅ **Unit Testing**: Individual components (SDK, Core, data layer)
✅ **Integration Testing**: Workflows end-to-end (happy path, errors)
✅ **Load Testing**: SLA verification under throughput
✅ **Security Testing**: Immutability, isolation, PII, audit
✅ **Chaos Testing**: Fault injection, recovery verification
✅ **Verification Patterns**: Automated guarantee checks
✅ **E2E Testing**: Complete request flow, state consistency

**Status**: Layer 3.6 DRAFT, ready for review.

**LAYER 3 COMPLETE**: All 6 implementation standards documents created.
