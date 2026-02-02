# INFRA-LAY3-005: Event & Logging Implementation Standards

**VERSION**: Layer 3 DRAFT
**STATUS**: IN PROGRESS
**DATE**: 2025-12-28

---

## Overview

This document defines **implementation standards** for event publishing and logging.

- **Scope**: Event bus selection, publishing patterns, consumer patterns, log aggregation, structured logging, trace propagation
- **Source of Truth**: INFRA-LAY1-002 (Event Model), INFRA-LAY2-004 (Monitoring & Observability)
- **Constraint**: Events are facts (immutable), not commands; logging is append-only and correlatable

**Key Principle**: Events are **immutable facts**, emitted asynchronously. Logging is **diagnostic data**, structured and correlated by trace ID.

---

## 1. Event Bus Selection & Configuration

### 1.1 Event Bus Technology

```
REQUIREMENT: Choose event bus for at-least-once delivery and ordering guarantees.

Recommended: Apache Kafka

Rationale:
  ✓ At-least-once delivery guarantee (consumer deduplicates by event_id)
  ✓ Ordering per partition (events for same tenant in order)
  ✓ Retention configurable (7+ years for compliance)
  ✓ Consumer groups (multiple subscribers, independent offset tracking)
  ✓ Fault tolerance (replicated, no data loss)
  ✓ High throughput (millions of events/day)
  ✓ Open source (no vendor lock-in)
  ✓ Mature ecosystem (battle-tested)

Configuration:

  Topic: infra-events
  Partitions: 50 (for parallelism, hash key = tenant_id)
  Replication Factor: 3 (fault tolerance)
  Retention: 30 days (hot, for recent subscribers)
  Backup: Archive to S3 every 24 hours (cold storage)

  Consumer Group: infra-subscribers
  Auto-commit: disabled (manual commit for idempotency)
  Isolation Level: read_committed (no uncommitted messages)

Alternative: RabbitMQ

Rationale:
  ✓ Message queue (task distribution)
  ✗ Ordering not guaranteed per queue (must use ordering plugin)
  ⚠ Retention: messages auto-deleted after delivered
  ✓ Simpler setup than Kafka (easier operations)
  ✗ Scaling: not as efficient as Kafka for high volume

Alternative: Google Pub/Sub

Rationale:
  ✓ Managed service (no infrastructure)
  ✓ At-least-once delivery
  ✗ Ordering: not guaranteed (use ordering key for per-key ordering)
  ✓ Retention: 7 days default (configurable)
  ✓ Integrated with GCP services
  ✗ Vendor lock-in (Google Cloud only)

Recommendation: Kafka for production multi-tenant systems, RabbitMQ for simpler use cases.
```

### 1.2 Event Routing

```
REQUIREMENT: Route events to correct subscribers efficiently.

Topic Strategy (Kafka):

Option A: Single Topic, Partitioned by Tenant

Topic: infra-events

Partitions: Keyed by tenant_id
  - Partition 0: events for tenant-aaa, tenant-bbb, tenant-ccc
  - Partition 1: events for tenant-ddd, tenant-eee, tenant-fff
  - ...
  - Partition 49: events for tenant-xxx, tenant-yyy, tenant-zzz

Advantages:
  ✓ Ordering per tenant (events in tenant order)
  ✓ Consumer per partition (parallel processing)
  ✓ Simple routing (hash(tenant_id) % partitions)

Disadvantages:
  ✗ Hot partitions (if one tenant has many events, uneven load)
  ✗ Rebalancing on partition scaling

Option B: Multiple Topics, One per Event Type

Topics:
  - infra-events.decision.created
  - infra-events.decision.allowed
  - infra-events.workflow.approved
  - infra-events.workflow.rejected
  - ...

Advantages:
  ✓ Subscribers only consume relevant events
  ✓ Easy to add new event types
  ✗ Event ordering NOT guaranteed across topics

Option C: Hybrid (Recommended)

Single topic: infra-events
Partition Key: tenant_id (ensures tenant ordering)
Event Type: in payload (subscribers filter client-side)

Configuration:

  {
    "event_id": "evt-123",
    "event_type": "decision.created",    // subscribers filter on this
    "tenant_id": "hotel-123",            // partition key
    "payload": {...}
  }

  Kafka routing:
    key = tenant_id
    → partition = hash(key) % 50
    → events for hotel-123 always go to same partition
    → ordering guaranteed per tenant
```

---

## 2. Event Publishing Standards

### 2.1 Publishing Pattern

```
REQUIREMENT: Publish events asynchronously, non-blocking to caller.

Publishing Flow:

STEP 1: Event created in database (INFRA-LAY3-002)
  INSERT INTO event_log (event_id, event_type, tenant_id, payload, occurred_at)
  → Event persisted, transaction committed

STEP 2: Event published to bus (async, fire-and-forget)
  AsyncTask.invoke_in_background(() => {
    kafka.produce(
      topic="infra-events",
      key=event.tenant_id,     // partition key for ordering
      value=event.to_json(),
      headers={"trace-id": event.trace_id}
    );
  });
  → Does NOT block decision return
  → Does NOT affect SLA

STEP 3: Return decision to SDK (fast)
  {
    decision_id: "dec-xyz-789",
    outcome: "ALLOWED",
    approval_workflow_id: null
  }
  → Latency: < 100ms p95 (includes event persistence, not bus publish)

STEP 4: Event bus delivery (background)
  - Kafka broker receives event
  - Broker replicates to replicas
  - Consumer subscribes and processes
  - At-least-once guarantee

Publishing Implementation:

async function publishEvent(event) {
  try {
    const record = {
      topic: 'infra-events',
      key: event.tenant_id,      // partition key
      value: JSON.stringify(event),
      headers: {
        'trace-id': event.metadata.trace_id,
        'event-type': event.event_type
      }
    };

    // Fire-and-forget (do NOT await)
    kafka_producer.send(record).catch(error => {
      logger.error('Event publication failed', {
        event_id: event.event_id,
        error: error.message,
        trace_id: event.metadata.trace_id
      });
      // Alert: P1 (event loss risk)
    });

  } catch (error) {
    logger.error('Event creation failed', {
      error: error.message,
      trace_id: event.metadata.trace_id
    });
  }
}

Critical: Publishing FAILURE does NOT affect decision.
  - Decision already persisted in event_log
  - Bus publish is best-effort
  - Consumers can re-query event_log by timestamp if bus fails
```

### 2.2 Event Deduplication

```
REQUIREMENT: Handle duplicate event publications gracefully.

Scenario: Core publishes same event twice (network retry)

Event 1:
  event_id: "evt-123",
  event_type: "decision.created",
  decision_id: "dec-xyz-789"

Event 2 (duplicate, same event_id):
  event_id: "evt-123",
  event_type: "decision.created",
  decision_id: "dec-xyz-789"

Consumer Deduplication:

  -- Create deduplication table
  CREATE TABLE event_consumer_state (
    consumer_group VARCHAR(256),
    event_id UUID,
    processed_at TIMESTAMP,

    PRIMARY KEY (consumer_group, event_id)
  );

  -- Consumer logic
  function process_event(event, consumer_group) {
    // Check if already processed
    SELECT processed_at FROM event_consumer_state
    WHERE consumer_group = ? AND event_id = ?;

    if (already_processed) {
      return; // skip duplicate
    }

    // Process event (apply to state, call webhook, etc.)
    application_logic(event);

    // Mark as processed (atomic with processing)
    INSERT INTO event_consumer_state (consumer_group, event_id, processed_at)
    VALUES (?, ?, now())
    ON CONFLICT (consumer_group, event_id) DO NOTHING;  // idempotent
  }

Guarantee:
  - Duplicate events processed once
  - State remains consistent
  - Event_id used for deduplication (globally unique)
```

---

## 3. Event Consumer Patterns

### 3.1 Consumer Subscription

```
REQUIREMENT: Consumers subscribe to events in publish-subscribe pattern.

Consumer Types:

TYPE 1: Application Adapter (Application-specific)
  - Subscribes to: decision.created, workflow.approved, workflow.rejected
  - Purpose: Trigger business logic (notifications, webhooks, etc.)
  - Processing: Event → business logic → side effects
  - Failure: Log, alert, retry

TYPE 2: Audit & Compliance (Multi-tenant)
  - Subscribes to: all event types
  - Purpose: Immutable audit trail (already in event_log)
  - Processing: Event → audit database (separate from hot storage)
  - Failure: Alert P1 (audit trail loss)

TYPE 3: Analytics & Reporting (Batch)
  - Subscribes to: all event types
  - Purpose: Analytics (rule effectiveness, approval SLA, etc.)
  - Processing: Event → data warehouse (nightly batch)
  - Failure: Alert P2 (analytics delay acceptable)

TYPE 4: Monitoring & Alerting (Real-time)
  - Subscribes to: decision.*, workflow.*
  - Purpose: Alerts on SLA breaches, unusual patterns
  - Processing: Event → metric aggregation → alert
  - Failure: Alert P1 (monitoring blind spot)

Consumer Group Management (Kafka):

  Consumer Group: app-adapter-group
  Consumers: 5 instances
  Topic: infra-events
  Partitions: 50
  → Each consumer handles 10 partitions

  Auto-scaling:
    - Monitor consumer lag
    - If lag > 10,000 messages: spin up new consumer
    - If lag < 1,000 messages: decommission consumer

Consumer Implementation:

  class EventConsumer {
    constructor(bootstrap_servers, topic, consumer_group, processor_fn) {
      this.kafka = new Kafka({
        brokers: bootstrap_servers,
        clientId: 'infra-event-consumer'
      });
      this.consumer = this.kafka.consumer({groupId: consumer_group});
      this.topic = topic;
      this.processor = processor_fn;
    }

    async run() {
      await this.consumer.subscribe({topic: this.topic});

      await this.consumer.run({
        eachMessage: async ({topic, partition, message}) => {
          try {
            const event = JSON.parse(message.value);
            const trace_id = message.headers['trace-id'];

            // Process with tracing
            await this.processor(event, trace_id);

            // Consumer framework auto-commits offset
          } catch (error) {
            logger.error('Event processing failed', {
              event_id: event.event_id,
              error: error.message,
              trace_id: trace_id
            });
            // Alert: P1 or P2 depending on event type
            throw error;  // reprocess on retry
          }
        }
      });
    }
  }
```

### 3.2 Consumer Failure Handling

```
REQUIREMENT: Handle consumer failures gracefully (no data loss).

Failure Scenario: Consumer crashes during event processing

Kafka Guarantees:
  - Offset auto-commit disabled (manual control)
  - Consumer crashes → offset not committed
  - Message re-delivered to new consumer instance
  - At-least-once delivery guaranteed

Failure Recovery:

  SCENARIO 1: Transient error (network timeout)
    - Consumer throws exception
    - Kafka rebalances to new consumer
    - Message reprocessed
    - Deduplication table prevents duplicate processing

  SCENARIO 2: Poison message (invalid event)
    - Consumer throws exception (cannot parse)
    - Message stuck (reprocessed forever)
    - Solution: dead-letter queue

Dead-Letter Queue (DLQ):

  CREATE TOPIC: infra-events.dlq

  Consumer Logic:

    async function process_event(event) {
      try {
        // Normal processing
        validate_event(event);
        apply_event(event);
      } catch (error) {
        // Log error
        logger.error('Event processing failed', {
          event_id: event.event_id,
          error: error.message
        });

        // Send to DLQ
        kafka.produce({
          topic: 'infra-events.dlq',
          key: event.tenant_id,
          value: JSON.stringify({
            original_event: event,
            error: error.message,
            failed_at: now(),
            retry_count: 0
          })
        });

        // Alert: P1 (manual review required)
        alert_operations_team('Event in DLQ');
      }
    }

  DLQ Processing:
    - Manual review by ops team
    - Fix root cause
    - Resubmit to main topic
```

---

## 4. Structured Logging Standards

### 4.1 Log Format

```
REQUIREMENT: All logs MUST be structured (JSON), not free-form text.

Log Structure:

{
  "timestamp": "2025-12-27T10:30:01.050Z",     // ISO 8601
  "level": "INFO" | "WARN" | "ERROR" | "FATAL",
  "logger_name": "infra.core.decision",         // component
  "message": "Decision created successfully",   // human-readable
  "trace_id": "trace-abc-123",                  // correlation
  "request_id": "req-xyz-456",                  // request tracking
  "tenant_id": "hotel-123",                     // tenant context
  "service": "core",                            // which service
  "version": "3.1.2",                           // app version
  "environment": "production",                  // environment
  "context": {
    "decision_id": "dec-xyz-789",
    "decision_type": "accounting.journal_approval",
    "outcome": "ALLOWED",
    "latency_ms": 47,
    "rule_matched": "high_amount_rule"
  },
  "error": {
    "type": "ValidationError",
    "message": "context contains PII",
    "stack_trace": "..."
  }
}

Log Levels:

INFO:  Normal operation (decision created, workflow approved)
       → log unconditionally, always searchable
       Example: "Decision created: dec-xyz-789, outcome: ALLOWED"

WARN:  Degraded operation (rule evaluation slow, cache miss)
       → log for investigation
       Example: "Rule evaluation slow: 80ms (SLA: 45ms)"

ERROR: Failure (SDK validation error, immutability violation attempt)
       → log immediately, alert
       Example: "Immutability violation attempted: UPDATE on decision record"

FATAL: Unrecoverable error (database crash, OOM)
       → log immediately, alert P0
       Example: "Database connection lost, circuit breaker open"

Structured Field Usage:

  - trace_id: Correlate all logs for single request
  - request_id: Track individual HTTP request
  - tenant_id: Filter logs by tenant (debugging)
  - service: Identify which service emitted log
  - context: Additional data relevant to log
```

### 4.2 Logging Implementation

```
REQUIREMENT: Implement structured logging across all services.

Logger Configuration (TypeScript/Node.js example):

import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({stack: true}),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'infra-core',
    version: '3.1.2',
    environment: process.env.NODE_ENV
  },
  transports: [
    new winston.transports.File({filename: 'error.log', level: 'error'}),
    new winston.transports.File({filename: 'combined.log'})
  ]
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

Usage:

async function createDecision(decision_type, context, tenant_id, trace_id) {
  logger.info('Decision creation started', {
    trace_id,
    tenant_id,
    decision_type,
    context_keys: Object.keys(context)
  });

  try {
    // ... decision creation logic ...

    logger.info('Decision created', {
      trace_id,
      tenant_id,
      context: {
        decision_id,
        outcome,
        rule_matched,
        latency_ms
      }
    });

  } catch (error) {
    logger.error('Decision creation failed', {
      trace_id,
      tenant_id,
      decision_type,
      error: {
        type: error.constructor.name,
        message: error.message,
        stack: error.stack
      }
    });
    throw error;
  }
}

Log Aggregation (Splunk, Datadog, ELK):

  -- All services send logs to centralized aggregator
  -- Configuration:
  {
    "transport": "splunk",
    "endpoint": "https://splunk.company.com:8088",
    "hec_token": "XXXXX",
    "batch_size": 100,
    "flush_interval_ms": 5000
  }

  -- Logs indexed by trace_id for correlation
  -- Searchable by tenant_id, service, level
```

---

## 5. Trace ID Propagation Standards

### 5.1 Trace ID Lifecycle

```
REQUIREMENT: Trace ID threaded through entire request lifecycle.

Generation:

  SOURCE: SDK or Application

  If application provides trace_id:
    - Use as-is
    - Validate format (UUID or alphanumeric)

  If application does NOT provide trace_id:
    - SDK generates: uuid()
    - Example: "550e8400-e29b-41d4-a716-446655440000"

Propagation:

  Step 1: Application → SDK
    const decision = await sdk.createDecision(
      decision_type,
      context,
      tenant_id,
      idempotency_key,
      {trace_id: "my-trace-id"}  // optional
    );

  Step 2: SDK → Core (HTTP Header)
    POST /decisions HTTP/1.1
    Host: core.infra.internal
    X-Trace-ID: my-trace-id   ← propagated
    Content-Type: application/json
    {...}

  Step 3: Core logs (all operations)
    logger.info('Decision creation', {
      trace_id: "my-trace-id",     ← propagated
      tenant_id: "hotel-123",
      ...
    });

  Step 4: Event Log (event metadata)
    {
      event_id: "evt-123",
      event_type: "decision.created",
      metadata: {
        trace_id: "my-trace-id",   ← propagated
        caused_by_user_id: "user-123"
      }
    }

  Step 5: Event Bus (message headers)
    kafka.produce({
      topic: "infra-events",
      value: {...},
      headers: {
        "trace-id": "my-trace-id"  ← propagated
      }
    });

  Step 6: Consumer logs
    logger.info('Event processed', {
      trace_id: "my-trace-id",     ← same trace ID
      event_id: "evt-123",
      ...
    });

Trace ID Format:

  - Format: UUID (preferred) or alphanumeric string
  - Pattern: ^[a-zA-Z0-9_-]{1,256}$
  - Examples:
    - "550e8400-e29b-41d4-a716-446655440000" (UUID)
    - "request-abc-123" (custom)
    - "trace-12345" (any alphanumeric)
```

### 5.2 Trace Correlation

```
REQUIREMENT: Query all logs for single trace ID across all services.

Correlation Query (Splunk):

  trace_id=my-trace-id
  | sort _time

  Results (in order):
    1. SDK validation (2025-12-27T10:30:01.001Z)
    2. SDK calls Core (2025-12-27T10:30:01.003Z)
    3. Core validates tenant (2025-12-27T10:30:01.004Z)
    4. Core evaluates rules (2025-12-27T10:30:01.045Z)
    5. Core persists decision (2025-12-27T10:30:01.050Z)
    6. Core publishes event (2025-12-27T10:30:01.055Z)
    7. Core returns response (2025-12-27T10:30:01.060Z)
    8. SDK returns to application (2025-12-27T10:30:01.075Z)
    9. Consumer processes event (2025-12-27T10:30:01.120Z)
    10. Audit logger records (2025-12-27T10:30:01.125Z)

  Total latency: 124ms (end-to-end)

Debugging Benefits:
  - Trace single request through entire system
  - Identify bottleneck (rule evaluation = 40ms)
  - Verify decision path (which rules evaluated?)
  - Audit completeness (all systems logged?)
```

---

## 6. Log Levels & Sampling Standards

### 6.1 Log Level Decisions

```
REQUIREMENT: Choose appropriate log level per event type.

Decision Creation Log Level:

  Normal path (decision created): INFO
    → Always logged (important for audit)
    → Example: "Decision created: outcome=ALLOWED"

  Slow path (p95 > 100ms): WARN
    → Logged for SLA investigation
    → Example: "Decision latency slow: 120ms (SLA: 100ms)"

  Error path (exception): ERROR
    → Always logged (debugging required)
    → Example: "Rule evaluation error: condition_eval_error"

SDK Validation Log Level:

  Validation failure (invalid input): INFO
    → Not an error (client bug, not infrastructure issue)
    → Example: "Validation failed: context contains PII"

  Validation timeout (should not happen): WARN
    → May indicate resource constraint
    → Example: "Validation timeout after 5 seconds"

Security Event Log Level:

  Immutability violation attempted: ERROR
    → Always logged (security investigation required)
    → Example: "UPDATE attempt on immutable decision record"

  Cross-tenant access attempted: ERROR
    → Always logged (security incident)
    → Example: "Cross-tenant access: hotel-123 → restaurant-456"

Rule Activation Log Level:

  Rule activated (CMS change): INFO
    → Normal operation, audit trail
    → Example: "Rule 'high_amount_rule' version 1.1 activated"

  Rule activation failure (syntax error): WARN
    → CMS admin should investigate
    → Example: "Rule activation failed: invalid condition syntax"
```

### 6.2 Log Sampling (High-Volume Events)

```
REQUIREMENT: Sample high-volume events to reduce storage cost.

Events to Sample:

  - SDK validation failures (high volume)
  - Non-error decisions (high volume)
  - Consumer processing (high volume)

Events to NOT Sample:

  - Errors (always log)
  - Security events (always log)
  - SLA breaches (always log)
  - Rule changes (always log)

Sampling Configuration:

  SDK Validation Failures:
    - Sample rate: 10% (log 1 in 10)
    - Examples: "context invalid", "decision_type invalid"
    - Purpose: Detect patterns (e.g., high rate of invalid inputs)

  Non-Error Decisions:
    - Sample rate: 100% (always log for audit)
    - Decision creation is core operation
    - Must be logged for compliance

  Consumer Processing:
    - Sample rate: 1% (log 1 in 100)
    - Purpose: Verify consumer working, not detailed logs

Sampling Implementation:

  function should_log(event_type, sample_rate) {
    if (sample_rate === 100) return true;  // always log
    return Math.random() * 100 < sample_rate;
  }

  if (should_log('validation_failure', 10)) {
    logger.info('Validation failed: context invalid', {...});
  }
```

---

## 7. Guard Rails: Event & Logging Constraints

### 7.1 Non-Negotiable Guard Rails

```
GUARDRAIL 1: Event Immutability
  - Events are append-only in event_log
  - No UPDATE/DELETE operations
  - Events published once (deduplication on consume)

GUARDRAIL 2: At-Least-Once Delivery
  - Event persisted before publishing
  - Bus delivery best-effort
  - Consumers deduplicate by event_id
  - Re-query event_log if bus fails

GUARDRAIL 3: Trace ID Correlation
  - Trace ID threaded through entire request
  - All logs include trace_id
  - Searchable by trace_id across services

GUARDRAIL 4: Structured Logging
  - All logs JSON formatted
  - Include: timestamp, level, trace_id, tenant_id, message
  - Searchable, not free-form text

GUARDRAIL 5: Event Ordering
  - Events ordered per tenant (partition key = tenant_id)
  - No reordering across tenants (independent streams)
  - Order critical for audit trail

GUARDRAIL 6: Consumer Idempotency
  - Consumers deduplicate by event_id
  - Processing idempotent (can reprocess without side effects)
  - At-least-once delivery handled by deduplication

GUARDRAIL 7: Log Retention
  - Structured logs: 90 days (hot storage)
  - Event logs: 7+ years (compliance)
  - Security events: 7+ years (immutable)

GUARDRAIL 8: Publishing Non-Blocking
  - Event publication async (fire-and-forget)
  - Does NOT block decision return
  - Failure to publish does NOT fail decision
```

---

## 8. Event & Logging Implementation Checklist

```
Before releasing event & logging system, verify:

EVENT BUS:
  ✓ Event bus selected (Kafka recommended)
  ✓ Topic created (infra-events, 50 partitions)
  ✓ Replication factor: 3 (fault tolerance)
  ✓ Retention: 30 days hot, archive to S3 for cold storage
  ✓ Consumer groups configured (per subscriber type)
  ✓ Dead-letter queue created (infra-events.dlq)

EVENT PUBLISHING:
  ✓ Events persisted to event_log (before publishing)
  ✓ Publishing async (non-blocking to caller)
  ✓ Partition key: tenant_id (ordering per tenant)
  ✓ Event headers: trace-id, event-type
  ✓ Failure handling: log and alert
  ✓ Deduplication: event_id unique

EVENT CONSUMING:
  ✓ Consumer deduplication table (event_consumer_state)
  ✓ Manual offset commits (not auto)
  ✓ Error handling (log, alert, DLQ)
  ✓ Poison message handling (DLQ)
  ✓ Consumer group rebalancing (auto-scaling)

STRUCTURED LOGGING:
  ✓ All logs JSON formatted
  ✓ Include: timestamp, level, trace_id, tenant_id, message
  ✓ Errors include: exception type, message, stack trace
  ✓ Context fields: decision_id, outcome, latency_ms, etc.
  ✓ Log levels appropriate (INFO/WARN/ERROR/FATAL)

TRACE ID PROPAGATION:
  ✓ Trace ID generated by SDK if not provided
  ✓ Trace ID propagated in HTTP headers
  ✓ Trace ID in event metadata
  ✓ Trace ID in all logs
  ✓ Searchable by trace_id (log aggregator)

LOG AGGREGATION:
  ✓ Centralized log aggregator configured (Splunk, Datadog, ELK)
  ✓ All services ship logs (streaming)
  ✓ Logs indexed by trace_id, tenant_id, service
  ✓ Searchable queries (log level, error, etc.)
  ✓ Retention: 90 days hot, archival older

MONITORING & ALERTING:
  ✓ Error log alerts (P1 for errors)
  ✓ Security event alerts (P0 for violations)
  ✓ Event processing lag alert (consumer lag > 10k)
  ✓ Dead-letter queue alerts (P1 for poison messages)
  ✓ Log rate anomalies (unusual spike)

SECURITY & COMPLIANCE:
  ✓ Event logs immutable (no UPDATE/DELETE)
  ✓ Event logs 7+ years retention
  ✓ Audit trail complete (every state change logged)
  ✓ PII not in logs (sanitized contexts)
  ✓ Tenant isolation in logs (tenant_id scoped)

TESTING:
  ✓ Unit tests for event structure
  ✓ Integration tests with event bus
  ✓ Integration tests for consumer deduplication
  ✓ Load tests (event throughput)
  ✓ Failure tests (bus unavailable, poison message)
```

---

## 9. Summary: Events & Logging as Diagnostic & Audit

✅ **Event Bus**: Kafka with tenant-based partitioning, at-least-once delivery
✅ **Event Publishing**: Async, non-blocking, persisted before bus publish
✅ **Event Consuming**: Deduplication by event_id, idempotent processing
✅ **Structured Logging**: JSON format, trace ID correlation, searchable
✅ **Trace Propagation**: UUID-based trace ID through entire request
✅ **Guard Rails**: Immutable events, at-least-once delivery, non-blocking publish

**Status**: Layer 3.5 DRAFT, ready for review.

**Next**: Testing & Verification Standards (INFRA-LAY3-006).
