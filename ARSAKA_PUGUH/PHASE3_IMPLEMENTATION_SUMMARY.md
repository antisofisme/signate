# ARSAKA_PUGUH - Phase 3 Implementation Summary

**Status**: IMPLEMENTATION READY
**Date**: 2026-01-24
**Focus**: EVENT BUS, OUTBOX PATTERN, CONSUMER RULES, OBSERVABILITY

---

## Overview

Phase 3 provides a RELIABLE EVENT DISTRIBUTION mechanism that:
- Delivers events from committed data only
- Never affects source of truth on failure
- Enables idempotent consumers
- Provides full observability

**CRITICAL PRINCIPLE**: Event = DELIVERY, not COMMAND. Event = FACT already happened.

---

## Phase 3 Scope

| Component | Purpose | Status |
|-----------|---------|--------|
| Migration 006 | Outbox pattern columns | ✅ |
| Event Schemas | Schema-first, versioned | ✅ |
| Event Publisher | Publishes to Kafka/Redpanda | ✅ |
| Outbox Poller | Polls unpublished events | ✅ |
| Consumer Framework | Idempotent, read-only | ✅ |
| Observability | Metrics, alerts | ✅ |
| Bypass Tests Phase 3 | Gate tests | ✅ |

---

## 1. DATABASE CHANGES

### Migration 006: Outbox Pattern

**File**: `backend/migrations/006_outbox_pattern.sql`

#### New Columns on event_log

| Column | Type | Purpose |
|--------|------|---------|
| `published_at` | TIMESTAMP | When published to event bus (NULL = not published) |
| `publish_attempts` | INTEGER | Number of publish attempts (for backoff) |
| `last_publish_error` | TEXT | Last error message (diagnostics) |
| `dlq_at` | TIMESTAMP | When moved to DLQ (NULL = not in DLQ) |

#### New Tables

| Table | Purpose |
|-------|---------|
| `event_outbox_config` | Poller, retry, DLQ configuration |
| `event_dlq` | Dead-letter queue tracking |

#### New Indexes

| Index | Purpose |
|-------|---------|
| `idx_event_log_outbox_unpublished` | Find unpublished events efficiently |
| `idx_event_log_dlq` | Monitor DLQ events |
| `idx_event_log_retry_candidates` | Find events ready for retry |

---

## 2. EVENT BUS INFRASTRUCTURE

### Directory Structure

```
backend/eventbus/
├── __init__.py       # Public exports
├── schemas.py        # Event envelope, schema versioning
├── topics.py         # Topic definitions, routing
├── publisher.py      # Event publisher
├── outbox.py         # Outbox poller, retry, DLQ
├── consumer.py       # Consumer framework
└── metrics.py        # Prometheus metrics
```

### Topics

| Topic | Events | Partitions |
|-------|--------|------------|
| `infra.decisions.events` | decision.* | 12 |
| `infra.workflows.events` | workflow.* | 12 |
| `infra.audit.events` | Fallback, system | 6 |

### Message Key

- **Key** = `aggregate_id` (UUID as bytes)
- **Purpose**: All events for same aggregate go to same partition
- **Effect**: Events are ordered per aggregate

---

## 3. EVENT SCHEMA

### EventEnvelope (Wire Format)

```python
@dataclass(frozen=True)
class EventEnvelope:
    # Identity
    event_id: str
    event_type: str
    schema_version: str

    # Aggregate reference
    aggregate_id: str
    aggregate_type: str

    # Multi-tenancy
    tenant_id: str

    # Timestamps
    occurred_at: str
    recorded_at: str
    published_at: str

    # Tracing
    trace_id: Optional[str]
    caused_by_user_id: Optional[str]

    # Payload
    payload: Dict[str, Any]
    source: str = "core"
```

### Schema Versioning

| Event Type | Current Version |
|------------|-----------------|
| decision.created | 1.0 |
| workflow.approved | 1.0 |
| workflow.rejected | 1.0 |

**RULE**: Breaking changes require new schema version.

---

## 4. OUTBOX PATTERN

### Flow

```
1. Begin transaction
2. Insert decision to decisions table
3. Insert event to event_log table (with published_at = NULL)
4. Commit transaction ← Decision is now durable
5. (Async) Outbox poller reads unpublished events
6. Outbox poller publishes to Kafka
7. If success: UPDATE event_log SET published_at = NOW()
8. If failure: Increment publish_attempts, retry with backoff
9. After max_attempts: Move to DLQ
```

### Retry Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_attempts` | 5 | Max publish attempts |
| `base_delay_ms` | 1000 | Initial retry delay |
| `max_delay_ms` | 60000 | Maximum retry delay |
| `backoff_multiplier` | 2.0 | Exponential backoff |

### Retry Schedule (with defaults)

| Attempt | Delay |
|---------|-------|
| 1 | 0 (immediate) |
| 2 | 1s |
| 3 | 2s |
| 4 | 4s |
| 5 | 8s |
| 6+ | DLQ |

---

## 5. CONSUMER RULES (NON-NEGOTIABLE)

### Consumers MUST:

| Rule | Enforcement |
|------|-------------|
| Be stateless | No instance state between messages |
| Be idempotent | Same event twice = same effect once |
| Be read-only toward Core | Cannot call mutation APIs |
| Complete in bounded time | Timeout enforced |

### Consumers MAY:

- Update read models (denormalized views)
- Trigger notifications
- Forward to external systems
- Call external APIs

### Consumers MAY NOT:

- Call Core mutation API
- Write to core tables (decisions, workflows, rules)
- Create new decisions
- Modify existing decisions

### Idempotency

Consumers use `IdempotencyStore` to track processed event IDs:

```python
# Check before processing
if await store.has_processed(event_id):
    return  # Skip duplicate

# Process event
await handle(event)

# Mark as processed
await store.mark_processed(event_id, consumer_group)
```

---

## 6. OBSERVABILITY

### Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `event_publish_lag_seconds` | Histogram | event_type |
| `event_publish_attempts` | Histogram | event_type |
| `event_publish_success_total` | Counter | event_type, tenant_id |
| `event_publish_failure_total` | Counter | event_type, tenant_id |
| `event_dlq_size` | Gauge | event_type, tenant_id |
| `consumer_lag_seconds` | Histogram | consumer_group, event_type |
| `consumer_messages_processed_total` | Counter | consumer_group, event_type, status |
| `outbox_pending_events` | Gauge | - |
| `outbox_poller_health` | Gauge | - |

### Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| EventDLQSizeWarning | dlq_size > 10 for 5m | warning |
| EventDLQSizeCritical | dlq_size > 100 for 5m | critical |
| EventPublishLagWarning | p95 lag > 30s | warning |
| EventPublishLagCritical | p95 lag > 300s | critical |
| OutboxPollerDown | health == 0 for 2m | critical |

### Structured Logs

All logs include:
- `event_id`
- `aggregate_id`
- `trace_id`
- `event_type`
- `tenant_id`

---

## 7. BYPASS TESTS (PHASE 3 GATE)

**File**: `backend/core/tests/test_bypass_phase3.py`

### Tests

| Test | Description | Expected |
|------|-------------|----------|
| Consumer cannot import DecisionRepository | No mutation access | PASS |
| Publisher returns False on failure | Not exception | PASS |
| Decision persists when publish fails | Outbox pattern | PASS |
| Idempotency store detects duplicates | Same event twice | PASS |
| Consumer skips duplicate events | Handler called once | PASS |
| Events have occurred_at timestamp | For ordering | PASS |
| Kafka key = aggregate_id | Partition ordering | PASS |
| Event replay with idempotency | No duplicate effects | PASS |
| Serialized event has schema_version | Versioning | PASS |

---

## Exit Criteria Verification

| Criteria | Status |
|----------|--------|
| Events published from committed data only | ✅ Outbox pattern |
| Decision immutable when event fails | ✅ Separate transactions |
| All consumers idempotent | ✅ IdempotencyStore required |
| No mutation path via events | ✅ Consumers read-only |
| Observability for stuck/delay | ✅ Metrics + alerts |
| Phase 2 enforcement unchanged | ✅ No changes |

---

## How to Apply Phase 3

### 1. Apply Database Migration

```bash
# Connect as superuser
psql -h localhost -U postgres -d infra

# Apply migration
\i backend/migrations/006_outbox_pattern.sql

# Verify columns exist
\d event_log
```

### 2. Install Dependencies

```bash
# Kafka client
pip install aiokafka>=0.8.0

# Or for Redpanda (compatible)
pip install aiokafka>=0.8.0
```

### 3. Configure Event Bus

```bash
# Environment variables
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_SCHEMA_REGISTRY_URL="http://localhost:8081"  # Optional
```

### 4. Start Outbox Poller

```python
from eventbus import OutboxPoller, OutboxConfig, EventPublisher
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Create session factory
engine = create_async_engine(DATABASE_URL)
session_factory = async_sessionmaker(engine)

# Create Kafka producer (or mock for testing)
from aiokafka import AIOKafkaProducer
producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
await producer.start()

# Create publisher
publisher = EventPublisher(producer=producer)

# Create and start poller
poller = OutboxPoller(
    session_factory=session_factory,
    publisher=publisher,
    config=OutboxConfig(batch_size=100, poll_interval_ms=1000)
)

await poller.start()
```

### 5. Run Bypass Tests

```bash
# Run Phase 3 bypass tests
pytest backend/core/tests/test_bypass_phase3.py -v

# All tests MUST pass before Phase 4
```

---

## Files Created/Modified

### Created:
- `backend/migrations/006_outbox_pattern.sql`
- `backend/eventbus/__init__.py`
- `backend/eventbus/schemas.py`
- `backend/eventbus/topics.py`
- `backend/eventbus/publisher.py`
- `backend/eventbus/outbox.py`
- `backend/eventbus/consumer.py`
- `backend/eventbus/metrics.py`
- `backend/core/tests/test_bypass_phase3.py`
- `PHASE3_IMPLEMENTATION_SUMMARY.md`

### Modified:
- `backend/core/repositories/models.py` (added outbox columns)

---

## NOT Implemented (Per Phase 3 Scope)

- ❌ Kafka cluster setup (infrastructure)
- ❌ Schema registry (optional, use schema_version in envelope)
- ❌ Consumer implementations (skeleton only)
- ❌ CMS for event monitoring (Phase 4+)
- ❌ Event sourcing (not required - events are delivery, not source)

---

## Security Notes

1. **Event bus credentials** must be secured in production
2. **Consumer idempotency** is MANDATORY - no exceptions
3. **DLQ events** may contain sensitive data - secure access
4. **Event replay** must be audited

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         REQUEST PATH                            │
│  (Synchronous - Same Transaction)                               │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │   SDK    │───▶│   Core   │───▶│ event_log│                  │
│  │  Client  │    │   API    │    │ (outbox) │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                        │              │                         │
│                        │              │                         │
│                   COMMIT ◄────────────┘                        │
│                   (decision is durable)                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       ASYNC PATH                                │
│  (Decoupled - After Commit)                                     │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Outbox   │───▶│ Publisher│───▶│  Kafka   │───▶│ Consumer │ │
│  │ Poller   │    │          │    │          │    │          │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │                                               │         │
│       │                                               │         │
│       ▼                                               ▼         │
│  ┌──────────┐                                   ┌──────────┐   │
│  │   DLQ    │                                   │  Read    │   │
│  │          │                                   │  Model   │   │
│  └──────────┘                                   └──────────┘   │
└─────────────────────────────────────────────────────────────────┘

CRITICAL:
- Decision committed BEFORE publish attempt
- Publish failure NEVER rolls back decision
- Consumer is READ-ONLY toward Core
```

---

## Next Steps

1. Run Phase 3 bypass tests
2. Set up Kafka/Redpanda cluster (infrastructure)
3. Deploy outbox poller as background service
4. Implement specific consumers (notifications, read models)
5. Proceed to Phase 4 only after all tests pass
