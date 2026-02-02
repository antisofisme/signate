# ARCH-10: Event-Driven Architecture

This document describes the **event-driven architectural pattern** that serves as the backbone for integration, observability, and audit across ARSAKA_PANDAWA. Events are the primary mechanism for loose coupling between modules and tenants.

**Core Principle**: *Events are immutable facts of what happened. They enable asynchronous integration without direct dependencies.*

---

## Why Event-Driven Architecture

### Problem It Solves

Without events:
- Modules tightly coupled (Module A calls Module B's API directly)
- No audit trail of what triggered what
- Difficult to add new consumers (e.g., "send email when payment recorded")
- Synchronous blocking = performance problems
- Cross-tenant workflows impossible

With events:
- Modules loosely coupled (Module A publishes, Module B subscribes)
- Complete audit trail of causal chain
- New consumers added without changing existing code
- Asynchronous non-blocking = better performance
- Inter-tenant integration via event bridges

### Core Benefits

| Benefit | How Achieved |
|---------|-------------|
| **Loose Coupling** | Producers don't know consumers; via message broker |
| **Audit Trail** | Every event immutably stored with timestamp, actor, correlation |
| **Scalability** | Async processing; can scale consumers independently |
| **Observability** | Follow correlation_id across module boundaries |
| **Extensibility** | New business logic added as event consumers without modifying producers |
| **Tenant Isolation** | tenant_id on every event enables filtering at infrastructure level |
| **Financial Integrity** | Accounting can consume events independently, verify & post GL |

---

## Fundamental Principles (Locked)

### Principle 1: Event Immutability
```
Event cannot be modified or deleted after publication.
Historical record preserved forever.
Corrections issued as new events (reversal pattern).
```

### Principle 2: Fact-Based Semantics
```
Events represent facts about what already happened in the system.
NOT commands ("please do X")
NOT queries ("tell me X")
Statement: "Guest checked out" (past tense, immutable fact)
```

### Principle 3: Minimum Context, Maximum Sufficiency
```
Include only essential data needed for consumers.
Not the entire domain object (that's in database).
Example: Guest checkout publishes reservation_id + folio_id,
  not the entire guest profile, folio ledger, etc.
```

### Principle 4: Logic Not in Handlers
```
Event handlers are reactive, not prescriptive.
Business logic lives in domain entities, not event handlers.
Event handler: "Mark folio as closed"
NOT: "Check if guest overstayed, calculate penalties, ..."
```

### Principle 5: Accounting as Consumer, Not Victim
```
Financial data integrity must be guaranteed regardless of event timing.
Accounting doesn't depend on event ordering.
Accounting doesn't fail if event consumer crashes.
Strategy: Accounting uses events as input but validates independently.
```

---

## Event Structure (Standard Envelope)

All events conform to this structure:

```json
{
  "event_id": "uuid (unique event identifier)",
  "event_type": "Domain.Entity.Action.vN (e.g., PMS.Guest.CheckedOut.v1)",
  "event_version": "v1",
  "occurred_at": "ISO-8601 (when event happened in source)",
  "tenant_id": "uuid (MANDATORY - tenant context)",
  "actor_type": "user|system|external",
  "actor_id": "uuid|null (who triggered)",
  "correlation_id": "uuid (links related events)",
  "payload": {
    // Domain-specific event data
  }
}
```

---

## Event Categories

### 1. Identity & Tenant Events

**Purpose**: Track tenant lifecycle and membership changes

| Event | When | Consumer |
|-------|------|----------|
| `Tenant.Created` | New tenant registered | Audit log, billing setup |
| `Tenant.Activated` | Tenant approved and active | Feature gate activation |
| `Tenant.Suspended` | Tenant suspended (non-payment) | Feature gates disabled |
| `Subscription.Started` | Tenant added app module | Feature gate enabled |
| `Subscription.Expired` | Subscription period ended | Feature gate disabled |
| `Membership.Created` | User joined tenant | Access control updated |
| `Membership.RoleChanged` | User promoted/demoted | Permission evaluation |

**Example**:
```json
{
  "event_type": "Membership.RoleChanged.v1",
  "payload": {
    "user_id": "alice-123",
    "tenant_id": "hotel-jakarta",
    "old_role": "staff",
    "new_role": "admin"
  }
}
```

---

### 2. PMS Core Events

**Purpose**: Operational changes in property management

| Event | When | Consumer |
|-------|------|----------|
| `Reservation.Created` | New reservation booked | Accounting (AR setup), notification |
| `Reservation.Cancelled` | Reservation cancelled | Accounting (AR reversal) |
| `Guest.CheckedIn` | Guest checks in | Folio activated for charges |
| `Guest.CheckedOut` | Guest departs, folio closes | Accounting (invoice creation) |
| `Folio.Opened` | Billing record created | Accounting (AR account created) |
| `Folio.Closed` | All charges finalized | Accounting (ready for posting) |
| `NightAudit.Completed` | Daily close run | Accounting (daily GL posting), reporting |

**Example**:
```json
{
  "event_type": "Guest.CheckedOut.v1",
  "payload": {
    "reservation_id": "res-456",
    "folio_id": "folio-789",
    "room_id": "room-101",
    "checked_out_at": "2025-12-23T11:30:00Z",
    "total_charges": 1500000,
    "nights_stayed": 3
  }
}
```

---

### 3. Transaction & Accounting Events

**Purpose**: Financial transactions and ledger operations

| Event | When | Consumer |
|-------|------|----------|
| `Invoice.Created` | Invoice record created | Audit log |
| `Invoice.Finalized` | Invoice locked, ready to post | GL adapter (posts journal entries) |
| `Payment.Recorded` | Payment applied to invoice | GL adapter (posts AR payment) |
| `Payment.Failed` | Payment declined | Notification (alert user) |
| `Journal.Posted` | GL entry recorded | Audit log, reporting |
| `Period.Closed` | Accounting period locked | Feature gates (no more posting allowed) |

**Example**:
```json
{
  "event_type": "Invoice.Finalized.v1",
  "payload": {
    "invoice_id": "inv-001",
    "amount": 1500000,
    "currency": "IDR",
    "source": "PMS",
    "due_date": "2025-12-30",
    "folio_id": "folio-789"
  }
}
```

---

### 4. Guest Journey Events

**Purpose**: Customer lifecycle and engagement

| Event | When | Consumer |
|-------|------|----------|
| `Guest.Registered` | Guest profile created | CRM, notification |
| `Guest.FeedbackSubmitted` | Guest submitted review/complaint | Quality management, notification |
| `Guest.MembershipJoined` | Guest enrolled in loyalty program | Loyalty engine, notification |

**Example**:
```json
{
  "event_type": "Guest.FeedbackSubmitted.v1",
  "payload": {
    "guest_id": "guest-123",
    "rating": 4.5,
    "comment": "Great stay, excellent service",
    "submitted_at": "2025-12-24T10:00:00Z"
  }
}
```

---

### 5. System & Operational Events

**Purpose**: Platform-level operations and monitoring

| Event | When | Consumer |
|-------|------|----------|
| `Notification.Sent` | Notification delivered | Audit log |
| `Webhook.Received` | External webhook received | Audit log, error handling |
| `BackgroundJob.Failed` | Async job failed | Error alerting, retry mechanism |
| `DataSync.Completed` | Data export/import completed | Audit log |

**Example**:
```json
{
  "event_type": "Notification.Sent.v1",
  "payload": {
    "notification_id": "notif-456",
    "recipient_id": "user-123",
    "channel": "email|sms|push",
    "status": "sent|failed",
    "sent_at": "2025-12-23T15:00:00Z"
  }
}
```

---

## Main Integration Flows

### Flow 1: Guest Checkout → Accounting (Full Specification)

**Prerequisites**:
- Tenant must have Accounting module subscribed (subscription_status = 'active')
- Accounting module must be enabled (is_enabled = true)
- Guest folio must have all charges posted

**Event Contract - PMS.Reservation.CheckedOut.v1**:
```json
{
  "event_type": "PMS.Reservation.CheckedOut.v1",
  "event_id": "evt-checkout-123",
  "correlation_id": "res-12345",
  "tenant_id": "hotel-001",
  "occurred_at": "2025-12-24T14:30:00Z",

  "payload": {
    "reservation_id": "res-12345",
    "folio_id": "folio-456",
    "guest_id": "guest-789",
    "room_id": "room-101",
    "check_in_date": "2025-12-20",
    "check_out_date": "2025-12-24",
    "num_nights": 4,
    "total_charges": 400.00,
    "taxes": 40.00,
    "total_amount_due": 440.00,
    "charges": [
      { "description": "Room charge", "amount": 100.00, "gl_account": "4100" },
      { "description": "Breakfast", "amount": 10.00, "gl_account": "4200" },
      { "description": "Resort fee", "amount": 15.00, "gl_account": "4150" }
    ],
    "payments": [
      { "method": "CARD", "amount": 440.00, "reference": "stripe-xyz" }
    ],
    "balance_due": 0.00
  }
}
```

**Processing Flow**:
```
1. PMS posts checkout and publishes PMS.Reservation.CheckedOut.v1
   (timeout waiting for acknowledgment: 5 seconds)

2. Message broker delivers to Accounting.Adapter consumer
   (retry policy: immediate, 1min, 5min, 30min → DLQ)

3. Accounting.Adapter processes event:
   ✅ Validates folio data present and complete
   ✅ Checks Accounting subscription active
   ❌ If not subscribed: log warning, event processed (no error)
   ❌ If validation fails: DLQ, alert operations team

4. Accounting creates Invoice:
   {
     "id": "inv-600001",
     "tenant_id": "hotel-001",
     "source": "PMS",
     "source_reference": "folio-456",
     "amount_due": 440.00,
     "status": "FINALIZED",
     "due_date": "2025-12-25"
   }

5. Accounting publishes Accounting.Invoice.Finalized.v1
   (same correlation_id as original checkout event)

6. GL.Adapter consumes Invoice.Finalized:
   ✅ Posts journal entries (see SEC-03 for immutability rules)

   DR 1200 (Guest Receivable)    440.00
   CR 4100 (Room Revenue)                 100.00
   CR 4200 (F&B Revenue)                   10.00
   CR 4150 (Resort Fee Revenue)            15.00
   CR 2100 (Sales Tax Liability)           40.00

7. GL publishes Accounting.JournalEntry.Posted.v1
   (continues same correlation_id)

8. Audit trail shows complete flow:
   [evt-checkout-123, inv-600001, je-800001]
   All with correlation_id = res-12345
```

**Error Handling**:
| Scenario | Handling | Recovery |
|----------|----------|----------|
| Accounting not subscribed | Log, continue (no error) | No action needed |
| Accounting subscription disabled | Log, continue (no error) | Owner enables subscription |
| Invoice creation fails | DLQ, alert team | Fix issue + manual re-process |
| GL posting fails | DLQ, alert team | Fix issue + manual re-process |
| Network timeout | Retry up to 30min | Auto-retry (max 4 attempts) |

**Key Points**:
- PMS doesn't call Accounting API directly (event-based only)
- Accounting independently creates invoice from event data
- GL posts based on invoice, not event (event is trigger only)
- If Accounting not subscribed: PMS continues normally (no blocking)
- All steps traced via correlation_id (same ID for all 3 events)
- 5-second acknowledgment timeout prevents stuck checkouts

---

### Flow 2: Payment Recording

```
Payment received (POS, gateway, cash)
    ↓
POS publishes Payment.Recorded event
    ↓
Accounting.Adapter consumes
    ↓
Applies payment to invoice in AR
    ↓
Publishes Payment.Applied event
    ↓
GL.Adapter consumes Payment.Applied
    ↓
Posts journal entries:
  DR Cash (debit cash account)
  CR Guest AR Account (credit receivable)
    ↓
Audit trail completes flow
```

---

### Flow 3: Inter-Tenant Supplier Order

```
Hotel (Tenant A) creates Purchase Order
    ↓
Publishes Supplier.PurchaseOrder.Issued event
    (published with buyer_tenant_id=A, supplier_tenant_id=B)
    ↓
Event broker forwards to Supplier's (B) event stream
    ↓
Supplier.Adapter in Tenant B consumes
    ↓
Creates PO record in Supplier's system
    ↓
Supplier publishes Supplier.Invoice.Issued
    (published with supplier_tenant_id=B, buyer_tenant_id=A)
    ↓
Event broker forwards to Hotel's event stream
    ↓
Hotel.Accounting.Adapter consumes
    ↓
Records as Accounts Payable (invoice from supplier)
    ↓
GL posts: DR Expense, CR AP Liability
    ↓
Both tenants have independent, accurate records
```

---

### Flow 4: Approval Workflow

```
Invoice created for $100,000 (exceeds approval threshold)
    ↓
Accounting publishes Approval.Requested event
    (required_role: owner, amount: 100000)
    ↓
Approval.Workflow consumes
    ↓
Creates approval task and notifies owners
    ↓
Owner approves → publishes Approval.Decided event
    ↓
Accounting.Adapter consumes Approval.Decided
    ↓
Marks invoice as approved
    ↓
GL.Adapter consumes → posts journal
    ↓
Audit shows: Request → Notification → Decision → Posted
```

---

## Implementation Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Message Broker** | RabbitMQ | Event distribution, queue management |
| **Event Storage** | PostgreSQL (append-only table) | Immutable event log for audit |
| **Event Serialization** | JSON | Language-agnostic format |
| **Async Workers** | Celery (Python) | Background job processing |
| **Real-time Delivery** | Centrifugo | WebSocket for live UI updates |
| **Event Schema** | JSON Schema | Contract validation |
| **Tracing** | OpenTelemetry + correlation_id | Flow tracing across services |

### Deployment Pattern

```
┌─────────────┐
│   Module A  │
│  (PMS)      │──── publish ────→ ┌──────────────┐
└─────────────┘                    │              │
                                   │ RabbitMQ     │
┌─────────────┐                    │ (Message     │
│   Module B  │                    │  Broker)     │
│(Accounting) │←─── subscribe ─────│              │
└─────────────┘                    └──────────────┘
                                           │
                                    store in
                                           │
                                   ┌───────────────┐
                                   │PostgreSQL     │
                                   │(Event Log)    │
                                   └───────────────┘
```

### Event Processing Guarantees

| Guarantee | How Achieved |
|-----------|-------------|
| **At-least-once delivery** | Message broker retries until ACK |
| **Idempotent processing** | Consumer checks event_id before processing |
| **Ordered within tenant** | Partitioning by tenant_id in message broker |
| **Immutable audit trail** | Database trigger prevents event updates |
| **Correlation tracing** | correlation_id links related events |

---

## Event Publishing Guidelines

### When to Publish

✅ **Publish an event when**:
- A fact has occurred (state change in database)
- Other modules might care about it
- The event represents business significance
- You want it in the audit trail

❌ **Don't publish an event when**:
- You're trying to trigger immediate behavior (use service calls)
- It's internal to a single module
- It's just a log message
- You need guaranteed ordering across tenants

### Publishing Pattern

```typescript
// 1. Create fact in database (update model)
const folio = await updateFolio(folioId, { status: 'CLOSED' });

// 2. Create event from fact
const event = {
  event_id: uuid(),
  event_type: 'Guest.CheckedOut.v1',
  occurred_at: new Date().toISOString(),
  tenant_id: folio.tenant_id,
  actor_type: 'user',
  actor_id: userId,
  correlation_id: correlationId,
  payload: {
    reservation_id: folio.reservation_id,
    folio_id: folio.id,
    total_charges: folio.total_charges
  }
};

// 3. Sign event
event.signature = signEvent(event);

// 4. Publish to broker
await publishEvent(event);

// 5. Store to audit log
await auditLog.append(event);
```

---

## Event Consumption Guidelines

### Consumer Pattern

```typescript
// 1. Subscribe to event type
eventBroker.subscribe('Guest.CheckedOut.v1', async (event) => {

  // 2. Verify signature
  if (!verifySignature(event)) {
    throw new Error('Event signature invalid');
  }

  // 3. Check idempotency (prevent reprocessing)
  if (await alreadyProcessed(event.event_id)) {
    return;  // Already handled, skip
  }

  try {
    // 4. Extract correlation for tracing
    const { correlation_id, payload } = event;

    // 5. Process event (business logic)
    const invoice = await createInvoiceFromFolio(payload.folio_id);

    // 6. Mark as processed
    await markProcessed(event.event_id);

    // 7. Publish result events if needed
    await publishEvent({
      event_type: 'Invoice.Finalized.v1',
      correlation_id,  // Preserve chain
      payload: { invoice_id: invoice.id, ... }
    });

  } catch (error) {
    // 8. Error handling (retry or dead-letter queue)
    await handleError(event, error);
  }
});
```

---

## Non-Negotiable Rules

### ❌ Hard Rules (Cannot be Broken)

| Rule | Why | Violation Example |
|------|-----|-------------------|
| **Events never replace database** | Events are append-only log, not source of truth for queries | Querying events to find "all paid invoices" |
| **Events never used for direct queries** | Event ordering not guaranteed; slow compared to DB | `SELECT * FROM events WHERE amount > $X` |
| **Correlation_id must be preserved** | Enables tracing across module boundaries | Creating new correlation_id instead of propagating |
| **tenant_id always required** | Enables isolation and filtering | Publishing event without tenant context |
| **Event handlers are reactive only** | Business logic in domain, not handlers | Event handler that creates new entities beyond immediate reaction |
| **Payment never waits for event** | Accounting integrity doesn't depend on async events | Blocking user until "payment.confirmed" event received |

---

## Monitoring & Observability

### Tracing Events

Use correlation_id to trace flows:

```sql
-- Find all events for a guest checkout flow
SELECT event_id, event_type, occurred_at, actor_id
FROM event_log
WHERE correlation_id = 'abc-correlation-123'
ORDER BY occurred_at;

-- Results show: checkout → invoice → payment → journal
-- Complete causal chain visible
```

### Metrics to Track

| Metric | Purpose |
|--------|---------|
| **Events published/sec** | Throughput monitoring |
| **Event processing latency** | Performance tracking |
| **Dead-letter queue depth** | Error accumulation |
| **Consumer lag** | Real-time vs. batch |
| **Event replay time** | Recovery capability |

---

## Error Handling

### Event Processing Failures

**If consumer crashes during processing**:
1. Message broker retries with exponential backoff
2. Consumer implements idempotency check
3. If still failing: move to dead-letter queue
4. Alert operations team for manual intervention

**If event signature invalid**:
1. Reject event immediately
2. Log to security audit trail
3. Alert security team

**If consumer falls behind (lag)**:
1. Scale up consumer instances
2. Parallelize processing where safe
3. Consider splitting event stream by tenant

---

## Relationship to Other Architecture Patterns

| Pattern | Relationship |
|---------|--------------|
| **CQRS (ARCH-07)** | Events are core to CQRS; write models publish, read models consume |
| **Event Sourcing** | Not fully implemented; events stored separately from state |
| **Saga Pattern** | Used for multi-step processes (checkout → invoice → payment) |
| **Adapter Pattern** | Modules use adapters to translate to/from events |

---

## Testing Event-Driven Flows

### Unit Test Pattern

```typescript
test('Guest checkout publishes CheckedOut event', async () => {
  const mockPublish = jest.fn();
  const folio = { id: 'f1', tenant_id: 't1', reservation_id: 'r1' };

  await checkoutGuest(folio, { publishEvent: mockPublish });

  expect(mockPublish).toHaveBeenCalledWith(
    expect.objectContaining({
      event_type: 'Guest.CheckedOut.v1',
      tenant_id: 't1',
      correlation_id: expect.any(String)
    })
  );
});
```

### Integration Test Pattern

```typescript
test('Guest checkout flow: checkout → invoice → GL', async () => {
  const eventLog = [];

  // Subscribe to all events
  broker.subscribeAll((event) => eventLog.push(event));

  // Trigger checkout
  await pms.checkoutGuest(reservationId);

  // Wait for event processing
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Verify event chain
  expect(eventLog).toContainEqual(
    expect.objectContaining({ event_type: 'Guest.CheckedOut.v1' })
  );
  expect(eventLog).toContainEqual(
    expect.objectContaining({ event_type: 'Invoice.Finalized.v1' })
  );
  expect(eventLog).toContainEqual(
    expect.objectContaining({ event_type: 'Journal.Posted.v1' })
  );

  // Verify all have same correlation_id
  const correlationIds = eventLog.map(e => e.correlation_id);
  expect(new Set(correlationIds).size).toBe(1);
});
```

---

## Migration to Event-Driven

If starting from synchronous architecture:

### Phase 1: Add Events (Non-Breaking)
- Keep existing API calls
- Additionally publish events
- Consumers start reading events
- Full backward compatibility

### Phase 2: Gradual Consumer Migration
- Migrate consumers from API calls to event subscriptions one at a time
- Verify each consumer works with events
- Maintain dual paths (API + events) during transition

### Phase 3: Deprecate APIs
- Once all consumers on events, deprecate old APIs
- Keep APIs as fallback for 90 days
- Monitor for issues before full removal

---

## Compliance Checklist

When designing event-driven flow:

- [ ] All events conform to envelope structure
- [ ] correlation_id propagated through chain
- [ ] tenant_id on every event
- [ ] Event immutability enforced (append-only storage)
- [ ] Consumers implement idempotency
- [ ] Signatures validated before consuming
- [ ] Error handling includes dead-letter queue
- [ ] Monitoring & tracing configured
- [ ] Tests cover happy path and error cases
- [ ] Documentation includes example event chains
- [ ] Cross-tenant events have explicit approval flow

---

## References

- **STD-19**: Event Contract Standard — Formal schema and versioning rules
- **ARCH-07**: Design Patterns & Concepts — CQRS pattern details
- **SPEC-11**: Inter-Tenant Supplier Flow — Event-driven cross-tenant integration
- **STD-17**: Logging & Observability — Structured logging of events
- **SEC-03**: Authorization, Approval & Audit — Event-based approval workflows
