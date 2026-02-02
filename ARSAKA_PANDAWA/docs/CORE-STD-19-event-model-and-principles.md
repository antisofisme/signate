# STD-19: Event Model & Event-Driven Standard

This document establishes the **standard structure, types, and handling rules** for event-driven communication across all modules and services in ARSAKA_PANDAWA. Events are the backbone of cross-module integration, audit trails, and observability.

---

## Core Principles (Non-Negotiable)

### 1. Events are Immutable
- Events describe facts that already happened
- Never modified, updated, or deleted after creation
- Immutability enables audit trail and forensics
- **See CORE-STD-20 Principle 2** for formal specification and reversal pattern details

### 2. Events are Fact-Based
- Events state what happened, not what should happen
- Example: ✅ `GuestCheckedOut` vs. ❌ `RequestGuestCheckout`
- Event is past-tense (already occurred)

### 3. Events Carry Minimum Sufficient Context
- Include all information needed by consumers
- No lookups required (avoid "fill in the details from database")
- Always include `tenant_id` (required for multi-tenancy)

### 4. Business Logic Lives in Services, Not Event Handlers
- Event handler = reaction mechanism only
- Handler does NOT make business decisions
- Handler does NOT validate (validation done in source service)
- Example: Handler updates AR ledger account, but doesn't decide if payment is valid

### 5. Events Don't Replace Database
- Events are supplements, not authoritative source
- Database (ledger, master data) is source of truth
- Events trigger state changes, but don't store state
- Query from database, not from event stream

### 6. Accounting Reliability
- Events must not corrupt ledger consistency
- Accounting is consumer, not victim
- Event payload must include full financial context (amounts, accounts, etc.)

---

## Standard Event Structure

Every event follows this envelope structure:

```typescript
interface EventEnvelope {
  // Event Identity
  event_id: string;                    // UUID - globally unique event identifier
  event_type: string;                  // e.g., "Guest.CheckedOut.v1", "Accounting.Payment.Recorded.v1"
  event_version: string;               // Version extracted from event_type (e.g., "v1", "v2") — MUST match suffix in event_type

  // Timing & Sequencing
  occurred_at: DateTime;               // When event occurred (in source system)
  published_at: DateTime;              // When event was published to broker

  // Context
  tenant_id: string;                   // REQUIRED - which tenant this event belongs to
  correlation_id: string;              // Trace related events across services
  causation_id?: string;               // Direct parent event (if triggered by another event)

  // Actor Information
  actor_type: "USER" | "SYSTEM" | "EXTERNAL";
  actor_id?: string;                   // user_id or system_id (null for external)

  // Source System
  source_service: string;              // e.g., "pms", "accounting", "payment-gateway"
  source_event_id?: string;            // Event ID in source system (for external events)

  // Signature & Verification
  signature: string;                   // HMAC-SHA256 of payload (for verification)

  // Payload
  payload: Record<string, any>;        // Event-specific data (see below)
}
```

### Required Fields Explanation

#### event_id
- UUID, globally unique identifier
- Used for idempotency (prevent duplicate processing)
- Example: `evt-550e8400-e29b-41d4-a716-446655440000`

#### event_type
- Hierarchical naming: `Domain.Entity.Action.vN` (see CORE-STD-20 for formal specification)
- Examples (matching STD-20 standard):
  - `Guest.CheckedOut.v1` (guest domain, check-out action)
  - `Accounting.Invoice.Finalized.v1` (accounting domain, invoice finalization)
  - `Platform.Subscription.Renewed.v1` (platform domain, subscription renewal)

#### tenant_id
- **REQUIRED in every event** (no exceptions)
- Ensures tenant isolation
- Consumers filter by tenant automatically
- Example: `org-123`

#### correlation_id
- Links related events across services
- Allows tracing a "request flow" across system
- Example: Guest checkout triggers invoice, payment, journal entries
  - All share same `correlation_id`
  - Enables analytics: "what did this guest checkout cascade?"

#### signature
- HMAC-SHA256 hash of payload
- Verifies event authenticity
- Prevents tampering in transit
- Calculated: `HMAC-SHA256(payload, secret_key)`

---

## Event Payload Size Guidelines

### Rule 1: Maximum Payload Size (Hard Limit)

**Event payload MUST be ≤ 10 KB** (including all nested objects)

**Rationale**:
- Event brokers (Kafka, RabbitMQ) have message size limits
- Network efficiency and latency (smaller events = faster processing)
- Storage efficiency (events retained 30 days = millions of events)
- Prevents accidental large payload bloat

**What counts toward 10 KB**:
- ✅ All data in `payload` object
- ✅ All fields in event envelope
- ❌ Envelope headers (managed by broker)

**Example**:
```json
{
  "event_id": "evt-123",       // Counted
  "event_type": "...",          // Counted
  "payload": {
    "invoice_id": "inv-001",   // Counted
    "line_items": [...]        // Counted - THIS should be limited
  }
}
```

### Rule 2: Inline vs. Reference Pattern

**Inline** (data in payload): Use for small, frequently needed data (< 1 KB)

```json
{
  "payload": {
    "invoice_id": "inv-001",
    "amount": 314.60,           // ✅ Inline (small)
    "customer_name": "John Doe", // ✅ Inline (small)
    "line_items": [            // ✅ Inline (if < 3 items)
      { "description": "Room", "amount": 200 },
      { "description": "Tax", "amount": 28.60 }
    ]
  }
}
```

**Reference** (ID only, consumer fetches from DB): Use for large or optional data (> 1 KB)

```json
{
  "payload": {
    "invoice_id": "inv-001",
    "amount": 314.60,
    // ❌ DON'T include full line item details
    // ✅ DO reference the invoice ID - consumer can fetch full details
    "line_item_count": 5       // Optional: for reference
  }
}
```

**Guideline Table**:

| Data | Size | Pattern | Example |
|------|------|---------|---------|
| ID, code, number | 50-200 B | Inline | `"invoice_id": "inv-001"` |
| Name, description | 50-500 B | Inline | `"customer_name": "John"` |
| Amount, count, status | < 100 B | Inline | `"amount": 314.60` |
| Address, address details | 200-500 B | Inline or Reference | Usually inline unless very detailed |
| List of < 5 items | < 2 KB | Inline | Invoice line items, payment details |
| List of > 5 items | > 2 KB | Reference only | Detailed GL entries, ledger account transactions |
| Nested objects (> 2 levels) | Varies | Inline if essential, Reference if optional | - |
| Attachment, binary data | Any size | NEVER inline, always Reference | `"document_url": "s3://..."`  |
| HTML/long text | > 500 B | Reference only | Store in DB, pass URL |

### Rule 3: What NOT to Include

❌ **Never include in payload**:
- Full documents (PDF, binary files) → Store in S3, pass URL
- Attachment blobs → Store in file system, pass path/URL
- Complete account ledger → Pass account ID, consumer fetches
- Full customer history → Pass customer ID, consumer queries
- Large lists (> 100 items) → Pass aggregate count, IDs, consumer fetches details
- Sensitive data (passwords, API keys, secrets) → Never publish in events
- Personally Identifiable Information (PII) beyond what consumer needs

**Example - What to REMOVE**:
```json
{
  // ❌ BAD: Entire customer history
  "customer_history": {
    "reservations": [...],     // 50 items = 10 KB
    "invoices": [...],         // 100 items = 30 KB
    "payments": [...]          // 50 items = 10 KB
  }
  // ✅ GOOD: Just references
  "customer_id": "cust-123",
  "reservation_count": 50,
  "invoice_count": 100
}
```

### Rule 4: Compression & Optimization

If approaching 10 KB limit:

1. **Use ID references instead of nested objects**:
   ```json
   // ❌ 12 KB (exceeds limit)
   { "folio": { ...full folio object... } }

   // ✅ 200 B (consumer fetches folio by ID)
   { "folio_id": "folio-456" }
   ```

2. **Use abbreviations for known enums**:
   ```json
   // ❌ 150 B
   { "payment_method": "CREDIT_CARD", "status": "COMPLETED" }

   // ✅ 50 B (if already defined standard)
   { "payment_method": "CC", "status": "DONE" }  // Only if standard
   ```

3. **Exclude optional fields**:
   ```json
   // ❌ Always 8 KB
   { "metadata": {}, "notes": "", "tags": [] }

   // ✅ Only 5 KB
   { ...only include if non-empty... }
   ```

### Rule 5: Telemetry & Monitoring

Track payload sizes:

```typescript
// On event publication
const payloadSize = JSON.stringify(event.payload).length;
metrics.recordEventSize(event.event_type, payloadSize);

if (payloadSize > 8192) {  // 8 KB warning threshold
  logger.warn(`Large event payload: ${event.event_type}=${payloadSize}B`);
}

if (payloadSize > 10240) {  // 10 KB hard limit
  throw new Error(`Event payload exceeds 10KB limit: ${payloadSize}B`);
}
```

**Monitoring Dashboard**:
- Average payload size per event type
- P95/P99 payload sizes (outlier detection)
- Events approaching 10 KB limit (alert at 9 KB)
- Payload size trend (growing = potential bloat)

---

## Event Version Consistency Validation

**Rule**: `event_version` field MUST match the version suffix in `event_type`. This is MANDATORY for all events.

### Version Format Specification

```
event_type format: {Module}.{Entity}.{Action}.v{N}
                                           ↑
                                    Version suffix

event_version format: v{N}
                      ↑
              MUST match the suffix above
```

### Validation Logic (Producer)

**Before publishing, event producer MUST validate version consistency:**

```typescript
function validateEventVersion(event: Event): void {
  // Step 1: Extract version from event_type
  const match = event.event_type.match(/\.v(\d+)$/);
  if (!match) {
    throw new ValidationError('INVALID_EVENT_TYPE',
      `event_type "${event.event_type}" does not end with .vN format`);
  }

  const expectedVersion = `v${match[1]}`;  // e.g., "v1"

  // Step 2: Verify event_version matches
  if (event.event_version !== expectedVersion) {
    throw new ValidationError('VERSION_MISMATCH',
      `event_version="${event.event_version}" does not match event_type suffix="${expectedVersion}"`
    );
  }
}

// Usage: Call before publishEvent()
const event = {
  event_type: 'Accounting.Invoice.Finalized.v2',
  event_version: 'v2',  // ✅ Matches
  ...
};
validateEventVersion(event);  // Passes
publishEvent(event);
```

### Validation Logic (Consumer)

**Event consumers MUST also validate version consistency before processing:**

```typescript
async function processEvent(event: Event): Promise<void> {
  // Step 1: Validate version consistency
  const match = event.event_type.match(/\.v(\d+)$/);
  const expectedVersion = `v${match[1]}`;

  if (event.event_version !== expectedVersion) {
    logger.error('VERSION_MISMATCH_DETECTED', {
      event_id: event.event_id,
      event_type: event.event_type,
      event_version: event.event_version,
      expected_version: expectedVersion,
      severity: 'CRITICAL'
    });

    // Route to DLQ (malformed event)
    await publishToDeadLetterQueue(event, 'SCHEMA_MISMATCH');

    throw new ValidationError('VERSION_MISMATCH',
      `Event ${event.event_id} has mismatched versions. Routed to DLQ.`
    );
  }

  // Step 2: Select handler based on event_version
  const handler = this.handlers.get(`${event.event_type}`);
  if (!handler) {
    throw new ValidationError('UNKNOWN_EVENT_TYPE',
      `No handler for ${event.event_type}`);
  }

  // Step 3: Route to version-specific handler
  switch (event.event_version) {
    case 'v1':
      return await handleV1(event);
    case 'v2':
      return await handleV2(event);
    default:
      throw new ValidationError('UNSUPPORTED_VERSION',
        `Unsupported version ${event.event_version} for ${event.event_type}`);
  }
}
```

### Error Handling Matrix

| Scenario | Producer | Consumer | Result |
|----------|----------|----------|--------|
| event_type=Inv.Fin.v1, event_version=v1 | ✅ Valid | ✅ Valid | Process normally |
| event_type=Inv.Fin.v2, event_version=v1 | ❌ Reject | ❌ Reject + DLQ | 400 Bad Request |
| event_type=Inv.Fin.v1, event_version=v2 | ❌ Reject | ❌ Reject + DLQ | 400 Bad Request |
| Missing event_version field | ❌ Reject | ❌ Reject + DLQ | 400 Bad Request |

### Testing Requirements

All implementations MUST test version validation:

```typescript
describe('Event Version Validation', () => {
  it('should accept event with matching version', () => {
    const event = {
      event_type: 'Accounting.Invoice.Finalized.v1',
      event_version: 'v1'
    };
    expect(() => validateEventVersion(event)).not.toThrow();
  });

  it('should reject event with mismatched version', () => {
    const event = {
      event_type: 'Accounting.Invoice.Finalized.v1',
      event_version: 'v2'  // MISMATCH
    };
    expect(() => validateEventVersion(event)).toThrow('VERSION_MISMATCH');
  });

  it('should reject event with missing event_version', () => {
    const event = {
      event_type: 'Accounting.Invoice.Finalized.v1'
      // event_version missing
    };
    expect(() => validateEventVersion(event)).toThrow();
  });

  it('should route mismatched events to DLQ', async () => {
    const event = {
      event_id: 'evt-123',
      event_type: 'Accounting.Invoice.Finalized.v1',
      event_version: 'v2'
    };
    await expect(processEvent(event)).rejects.toThrow('VERSION_MISMATCH');
    expect(dlqPublished).toContainEqual({
      event: event,
      reason: 'SCHEMA_MISMATCH'
    });
  });
});
```

---

## Event Categories

### 1. Identity & Tenant Lifecycle

**Domain**: `Platform` (tenant, subscription, membership operations)

Events:
- `Platform.Tenant.Created.v1` — New tenant (subscription) created
- `Platform.Tenant.Activated.v1` — Tenant approved and activated
- `Platform.Tenant.Suspended.v1` — Tenant suspended (payment failed)
- `Platform.Tenant.Reactivated.v1` — Suspended tenant reactivated
- `Platform.Tenant.DeletionRequested.v1` — Owner initiates deletion
- `Platform.Tenant.PermanentlyDeleted.v1` — Grace period expired, data deleted

**Related Events**:
- `Platform.Subscription.Started.v1` — Subscription module activated
- `Platform.Subscription.Renewed.v1` — Subscription renewed at billing cycle
- `Platform.Subscription.Expired.v1` — Subscription expired (payment failed)
- `Platform.Module.Activated.v1` — Module (PMS, POS, etc.) enabled for tenant
- `Platform.Module.Deactivated.v1` — Module disabled

**Member Events**:
- `Platform.Membership.Created.v1` — User invited to tenant
- `Platform.Membership.RoleChanged.v1` — User's role updated
- `Platform.Membership.Removed.v1` — User access revoked

---

### 2. PMS Core Events

**Domain**: `PMS` (guest, reservation, folio operations)

Reservation Events:
- `PMS.Reservation.Created.v1` — Reservation booked
- `PMS.Reservation.CheckedIn.v1` — Guest checked in
- `PMS.Reservation.CheckedOut.v1` — Guest checked out
- `PMS.Reservation.Cancelled.v1` — Reservation cancelled
- `PMS.Reservation.NoShow.v1` — Guest didn't arrive by deadline

Folio Events:
- `PMS.Folio.Opened.v1` — Billing record created at check-in
- `PMS.Folio.ChargePosted.v1` — Charge added to folio
- `PMS.Folio.ChargeReversed.v1` — Charge reversed/refunded
- `PMS.Folio.Settled.v1` — Folio closed and payment received

Operational Events:
- `PMS.NightAudit.Completed.v1` — End-of-day audit finished
- `PMS.Room.StatusChanged.v1` — Room status (clean, dirty, maintenance)

---

### 3. Transaction & Accounting Events

**Domain**: `Accounting` (invoice, payment, journal operations)

Invoice Events:
- `Accounting.Invoice.Created.v1` — Invoice generated from source event (folio, etc.)
- `Accounting.Invoice.Finalized.v1` — Invoice confirmed and posted to ledger
- `Accounting.Invoice.PartiallyPaid.v1` — Partial payment received
- `Accounting.Invoice.Paid.v1` — Invoice fully paid
- `Accounting.Invoice.Overdue.v1` — Payment deadline passed without payment
- `Accounting.Invoice.Reversed.v1` — Invoice corrected via reversing entry

Payment Events:
- `Accounting.Payment.Recorded.v1` — Payment posted to accounting
- `Accounting.Payment.Failed.v1` — Payment processing failed
- `Accounting.Payment.Refunded.v1` — Refund issued to customer

Journal Events:
- `Accounting.JournalEntry.Posted.v1` — GL entry created and posted
- `Accounting.JournalEntry.Reversed.v1` — Correction entry (original marked reversed)

Period Events:
- `Accounting.Period.ClosingStarted.v1` — Period close process initiated
- `Accounting.Period.Closed.v1` — Period locked (immutable)

---

### 4. Guest & Customer Events

**Domain**: `Guest` (guest lifecycle and loyalty)

- `Guest.Registered.v1` — Guest created account
- `Guest.FeedbackSubmitted.v1` — Guest survey/feedback
- `Guest.LoyaltyJoined.v1` — Guest enrolled in loyalty program
- `Guest.LoyaltyPointsEarned.v1` — Loyalty points earned
- `Guest.LoyaltyPointsRedeemed.v1` — Loyalty points used

---

### 5. System & Operational Events

**Domain**: `system`, `notification`

- `notification.sent` — Email/SMS sent to guest
- `webhook.received` — External webhook received (OTA booking, payment gateway)
- `webhook.failed` — Webhook processing failed
- `job.completed` — Background job finished
- `job.failed` — Background job failed with error
- `data.exported` — Data export completed
- `error.critical` — Critical system error

---

## Event Payloads (Examples)

### Example 1: GuestCheckedOut

**Event Type**: `PMS.Reservation.CheckedOut.v1` (authoritative - folio settlement is recorded as part of checkout)

```json
{
  "event_id": "evt-abc123",
  "event_type": "PMS.Reservation.CheckedOut.v1",
  "event_version": "v1",
  "occurred_at": "2025-12-27T11:00:00Z",
  "published_at": "2025-12-27T11:00:05Z",
  "tenant_id": "org-123",
  "correlation_id": "corr-xyz789",
  "actor_type": "USER",
  "actor_id": "staff-456",
  "source_service": "pms",
  "signature": "hmac-sha256-hash",

  "payload": {
    "folio_id": "folio-456",
    "guest_id": "guest-789",
    "reservation_id": "res-12345",
    "room_id": "room-101",
    "check_in_date": "2025-12-25",
    "check_out_date": "2025-12-27",
    "num_nights": 2,

    "charges": {
      "room_charge": 200.00,
      "ancillary": 86.00,
      "subtotal": 286.00,
      "tax": 28.60,
      "total": 314.60
    },

    "payment": {
      "method": "CREDIT_CARD",
      "amount_paid": 314.60,
      "balance_due": 0.00,
      "reference": "stripe-xyz789"
    }
  }
}
```

**Consumers**:
- Accounting: Create invoice + journal entries
- CRM: Update guest interaction history
- Reporting: Update occupancy metrics
- Notification: Send thank you email + receipt

---

### Example 2: PaymentRecorded

**Event Type**: `Accounting.Payment.Recorded.v1`

```json
{
  "event_id": "evt-def456",
  "event_type": "Accounting.Payment.Recorded.v1",
  "event_version": "v1",
  "occurred_at": "2025-12-27T11:00:00Z",
  "published_at": "2025-12-27T11:00:05Z",
  "tenant_id": "org-123",
  "correlation_id": "corr-xyz789",
  "causation_id": "evt-abc123",        // Triggered by guest checkout
  "actor_type": "SYSTEM",
  "source_service": "accounting",
  "signature": "hmac-sha256-hash",

  "payload": {
    "payment_id": "pay-98765",
    "invoice_id": "inv-001",
    "guest_id": "guest-789",
    "amount": 314.60,
    "currency": "USD",
    "payment_method": "CREDIT_CARD",
    "payment_processor_reference": "stripe-xyz789",
    "payment_date": "2025-12-27",
    "journal_entry_id": "je-002"
  }
}
```

**Consumers**:
- CRM: Mark invoice as paid
- Reporting: Revenue dashboard
- Email: Send payment confirmation

---

### Example 3: JournalPosted

**Event Type**: `journal_entry.posted`

```json
{
  "event_id": "evt-ghi789",
  "event_type": "Accounting.Journal.Posted.v1",
  "event_version": "v1",
  "occurred_at": "2025-12-27T11:00:10Z",
  "published_at": "2025-12-27T11:00:15Z",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "corr-xyz789",
  "causation_id": "evt-abc123",
  "actor_type": "SYSTEM",
  "source_service": "accounting",
  "signature": "hmac-sha256-hash",

  "payload": {
    "journal_entry_id": "je-001",
    "period": "2025-12",
    "entry_date": "2025-12-27",
    "description": "Guest checkout - invoice and room revenue",

    "lines": [
      {
        "account_code": "1200",
        "account_name": "Accounts Receivable",
        "debit": 314.60,
        "credit": 0
      },
      {
        "account_code": "4100",
        "account_name": "Room Revenue",
        "debit": 0,
        "credit": 200.00
      },
      {
        "account_code": "4200",
        "account_name": "Ancillary Revenue",
        "debit": 0,
        "credit": 86.00
      },
      {
        "account_code": "2300",
        "account_name": "Tax Payable",
        "debit": 0,
        "credit": 28.60
      }
    ],

    "total_debits": 314.60,
    "total_credits": 314.60,
    "balanced": true
  }
}
```

---

## Event Flow Examples

### Example Flow 1: Guest Checkout Cascade

```
Timeline:

1. guest.checked_out (PMS)
   ↓ Published

2. Accounting service consumes event
   → Creates invoice (if not exists)
   → Posts journal entries
   → Publishes: invoice.created

3. Invoice system publishes: invoice.finalized
   ↓

4. Payment service consumes checkout event
   → Records payment (from checkout payload)
   → Publishes: payment.recorded
   ↓

5. Journal service publishes: journal_entry.posted
   ↓

6. CRM service consumes all events
   → Updates guest interaction history
   → Updates revenue attribution
   ↓

7. Notification service consumes events
   → Sends receipt email (from payment.recorded)
   → Sends thank you (from guest.checked_out)
   ↓

8. Reporting service consumes events
   → Updates daily revenue dashboard
   → Updates occupancy metrics
   → Updates guest lifetime value

Total: 1 event triggers ~7-8 downstream reactions
All traced by same correlation_id
```

### Example Flow 2: Partial Payment Follow-up

```
Timeline:

1. invoice.partially_paid (Accounting)
   ↓

2. CRM service
   → Marks invoice as "partially paid"
   → Schedules reminder (due date + 5 days)
   ↓

3. Job scheduler (5 days later)
   → Publishes: invoice.overdue (no payment yet)
   ↓

4. Notification service
   → Sends payment reminder email
   ↓

5. Reporting service
   → Tracks "Days Sales Outstanding" (DSO) metric
   → Alerts if collection risk high
```

---

## Event Idempotency & Duplicate Prevention

**Problem**: Event might be published multiple times (broker retry, network issues)

**Solution**: Idempotency Keys

### Idempotency Key Format
```
{event_id}_{consumer_id}
```

Example:
```
evt-abc123_accounting-service
evt-abc123_notification-service
evt-abc123_crl-service
```

### Consumer Implementation
```typescript
async function handleGuestCheckedOut(event: Event) {
  // Check if already processed
  const idempotencyKey = `${event.event_id}_guest-checkout-handler`;
  const exists = await db.idempotency.get(idempotencyKey);

  if (exists) {
    // Already processed, return success silently
    return { idempotent: true };
  }

  try {
    // Process event
    await processCheckout(event);

    // Record as processed
    await db.idempotency.set(idempotencyKey, true, ttl: 7days);

  } catch (error) {
    // Leave idempotency key unset (retry allowed)
    throw error;
  }
}
```

### Idempotency Store
- Database table: `event_idempotency_keys`
- Columns: `key`, `processed_at`, `result`, `ttl`
- TTL: 7 days (prevents infinite growth)

---

## Event Ordering & Sequencing

### Problem
Messages can arrive out of order from broker

### Solution: Sequence Numbers

```json
{
  "event_id": "evt-abc123",
  "tenant_id": "org-123",
  "sequence_number": 42,           // Order within tenant
  "timestamp": "2025-12-27T11:00:00Z",
  "causation_id": "evt-xyz789"     // Previous event
}
```

### Consumer Logic
```typescript
// Store last processed sequence number
const lastSequence = await db.tenantState.getSequence(tenant_id);

if (event.sequence_number <= lastSequence) {
  // Already processed, ignore
  return;
}

if (event.sequence_number > lastSequence + 1) {
  // Out of order, wait for missing event
  await queue.hold(event);  // Re-queue for later
  return;
}

// Process in order
await process(event);
await db.tenantState.setSequence(tenant_id, event.sequence_number);
```

---

## Error Handling & Dead Letter Queue

### Event Processing Failure

```
Consumer receives event
  → Attempts to process
  → Fails (validation error, service down, etc.)
  → Retry mechanism:
    - 1st retry: 1 minute
    - 2nd retry: 5 minutes
    - 3rd retry: 30 minutes
    → If all fail: send to Dead Letter Queue (DLQ)
```

### Dead Letter Queue (DLQ) - Authoritative Error Handling Specification

**Policy**: Events that fail ALL retries → moved to DLQ (never lost, never discarded)

**DLQ Characteristics**:
- Separate, immutable queue for failed events
- Manual review required (not automatic reprocessing)
- Could indicate:
  - Bug in event consumer
  - Missing data or validation error
  - Service misconfiguration or dependency down
  - Schema mismatch (consumer expects different version)

**DLQ Processing Workflow**:
```
1. Event lands in DLQ with metadata:
   {
     "original_event_id": "evt-12345",
     "event_type": "Invoice.Finalized.v1",
     "entered_dlq_at": "2025-12-24T10:30:00Z",
     "retry_count": 3,
     "last_error": "Service timeout: accounting API down",
     "tenant_id": "hotel-123"
   }

2. Alert sent to operations team
   - Email notification
   - Monitoring dashboard flag
   - Slack alert (if configured)

3. Manual investigation:
   - Is event payload valid? (validate JSON schema)
   - Is consumer working? (check logs)
   - Is dependency service available? (health check)
   - Is this consumer version still supported? (version mismatch?)

4. Resolution (one of):
   a) Fix consumer bug → redeploy → re-process event
   b) Fix service configuration → wait for recovery → re-process
   c) Event is invalid → document reason → move to archive
   d) Event is obsolete → skip → move to archive

5. Re-processing:
   - Never automatic (manual approval required)
   - Idempotency key prevents duplicate processing
   - Re-process event as if it just published
```

**Retry Policy** (DEFAULT - can be customized per event type):
```
Attempt 1: Immediate
Attempt 2: 1 minute delay
Attempt 3: 5 minutes delay
Attempt 4: 30 minutes delay
After Attempt 4 fails → Move to DLQ
```

**Monitoring**:
- Track DLQ size (alert if > 10 events)
- Track retry rates (alert if > 10% of events)
- Log all DLQ movements (immutable audit trail)

---

## Event Versioning

### Problem
Event schema changes over time. Consumers may expect old or new format.

### Solution: Explicit Versioning

```json
{
  "event_id": "evt-abc123",
  "event_type": "PMS.Reservation.CheckedOut.v2",
  "event_version": "v2",              // Version of this event schema
  "occurred_at": "2025-12-27T11:00:00Z",

  "payload": {
    "reservation_id": "res-123",
    "guest_id": "guest-789",
    "folio_id": "folio-456",
    "room_number": "101",          // NEW in v2
    "checkout_channel": "front_desk"   // NEW in v2
  }
}
```

### Consumer Handling
```typescript
async function handleGuestCheckedOut(event: Event) {
  switch (event.event_version) {
    case 1:
      // Old format
      return handleV1(event);
    case 2:
      // New format
      return handleV2(event);
    default:
      // Unknown version
      throw new Error(`Unknown event version: ${event.event_version}`);
  }
}
```

### Migration Strategy
1. Publish events in old format (v1)
2. Update consumer to handle both v1 and v2
3. Update producer to emit v2
4. Monitor: ensure all consumers handle v2
5. Stop emitting v1 (after grace period)
6. Remove v1 handler from consumers

---

## Event Schema Evolution Guidelines

✅ **Safe Changes**:
- Add optional field to payload
- Add new event type (not breaking existing)
- Deprecate field (mark as unused but keep)

❌ **Unsafe Changes**:
- Remove field without versioning
- Change field type (string → number)
- Change field meaning/semantics
- Rename field without migration

---

## Observability & Monitoring

### Event Metrics

```
- Events published per minute (by type)
- Events consumed per minute (by consumer)
- Event processing latency (p50, p95, p99)
- Event processing errors (by consumer)
- DLQ size (events stuck)
- Idempotency key hits (duplicate prevention)
```

### Event Tracing

Every event automatically traceable via `correlation_id`:

```
POST /api/guest/checkout
  → Internal: correlation_id = "corr-xyz789"
  → Emits: guest.checked_out (correlation_id = "corr-xyz789")
  → Downstream: invoice.created (correlation_id = "corr-xyz789")
  → Downstream: payment.recorded (correlation_id = "corr-xyz789")
  → Downstream: journal_entry.posted (correlation_id = "corr-xyz789")

Can query: "Show me all events from correlation_id = corr-xyz789"
Result: Complete request cascade
```

### Correlation ID Rules (Authoritative)

**When to CREATE a new correlation_id**:

✅ **DO create new** when:
1. **External API Request** - REST/GraphQL call from client
   ```
   POST /api/guest/checkout → correlation_id = UUID()
   POST /api/invoice/create → correlation_id = UUID()
   ```

2. **Time-Triggered Event** - Scheduler/background job
   ```
   Daily end-of-day audit → correlation_id = UUID()
   Monthly period close → correlation_id = UUID()
   ```

3. **Independent Business Process** - Not triggered by another event
   ```
   Manual invoicing (staff creates) → correlation_id = UUID()
   Webhook from external system (payment gateway) → correlation_id = UUID()
   ```

**When to PROPAGATE correlation_id**:

✅ **DO propagate** when:
1. **Event-Triggered Handler** - Consumer processing event
   ```
   Payment.Recorded event (correlation_id=corr-xyz)
     → Creates AR adjustment (same correlation_id=corr-xyz)
   ```

2. **Synchronous Causation** - Direct causation_id relationship
   ```
   invoice.created (corr-xyz)
     → triggers accounting handler
     → emits journal_entry.posted (corr-xyz, causation_id=invoice.created)
   ```

3. **Same Business Transaction** - All events part of one flow
   ```
   Guest checkout cascade:
     - guest.checked_out (corr-xyz)
     - folio.settled (corr-xyz)
     - invoice.created (corr-xyz)
     - payment.recorded (corr-xyz)
     - journal_entry.posted (corr-xyz)
   ```

**Rule Summary**:

| Scenario | Action | Example |
|----------|--------|---------|
| User clicks API button | Create new | POST /checkout → corr-ABC |
| Scheduler runs job | Create new | 2 AM daily close → corr-XYZ |
| Event triggers handler | Propagate | Invoice received (corr-ABC) → create GL (corr-ABC) |
| Multi-step workflow | Propagate | Checkout → Invoice → Payment → Journal (all corr-ABC) |
| Error retry | Propagate | Failed journal post retry → same corr-id |
| Human manual action | Create new | Staff manually posts journal entry → corr-NEW |
| Webhook from external | Create new | Payment gateway → corr-UUID (not tied to PMS request) |

**Implementation**:

```typescript
// External API request handler
async function handleCheckoutRequest(req) {
  const correlationId = req.headers['x-correlation-id'] || generateUUID();
  // Service receives correlation_id or generates new one
  return await checkoutService.process(correlationId);
}

// Event consumer (propagate from trigger event)
async function handlePaymentRecorded(event) {
  // MUST propagate event.correlation_id to all downstream events
  const journalEvent = {
    event_id: generateUUID(),
    correlation_id: event.correlation_id,  // ← Propagate
    causation_id: event.event_id,          // ← Track source
    // ...
  };
  await eventBus.publish(journalEvent);
}

// Scheduled job (create new)
async function dailyPeriodClose() {
  const correlationId = generateUUID();  // ← Create new
  const events = [];

  events.push({
    event_type: 'Accounting.Period.ClosingStarted.v1',
    correlation_id: correlationId,
    // ...
  });

  // All events in this period close share same correlation_id
  await eventBus.publishBatch(events);
}
```

**Tracing Implications**:

```sql
-- Find all events from a user request
SELECT * FROM events
WHERE correlation_id = 'corr-xyz789'
ORDER BY occurred_at;

-- Result: User clicked checkout
--   → 7 events triggered
--   → 2 failures (retry)
--   → 5 successes
--   → Complete audit trail

-- Find all failures for a correlation_id
SELECT * FROM events
WHERE correlation_id = 'corr-xyz789'
  AND status = 'FAILED';

-- Result: Can debug entire flow
```

### Logging

Every event logged to centralized system (STD-17):

```json
{
  "timestamp": "2025-12-27T11:00:05Z",
  "level": "INFO",
  "message": "Event published",
  "event_id": "evt-abc123",
  "event_type": "guest.checked_out",
  "tenant_id": "org-123",
  "correlation_id": "corr-xyz789",
  "trace_id": "trace-123"
}
```

---

## Implementation Technologies

### Message Broker: RabbitMQ (or Kafka)
- Durability: persists messages
- Ordering: per-partition or per-tenant
- Replay: messages can be re-consumed from checkpoint
- Dead letter queue: automatic DLQ for failed consumers

### Consumer Framework: Celery (Python) or Bull (Node.js)
- Worker pool: horizontal scaling
- Retry logic: automatic exponential backoff
- Task tracking: monitor status of each event processing
- Scheduled tasks: one-time events (e.g., remind after 5 days)

### Real-time Broadcasting: Centrifugo (or Socket.io)
- WebSocket connections to clients
- Subscribe to specific topics (e.g., "tenant-123-notifications")
- Real-time delivery of events to web UI (guest confirmation, staff alerts)

### Event Store (Optional)
- Immutable log of all events
- Enables event sourcing (rebuild state from events)
- Enables audit trail (answer "what happened to this folio?")

---

## Event Governance Rules

### Mandatory for All Events
- [ ] Must have `event_id` (UUID)
- [ ] Must have `event_type` (with domain prefix)
- [ ] Must have `occurred_at` (when did it happen)
- [ ] Must have `tenant_id` (which tenant)
- [ ] Must have `signature` (HMAC verification)
- [ ] Payload must be serializable to JSON
- [ ] Must be immutable (never modified after publish)

### Mandatory for Financial Events
- [ ] Include all amounts (no lookups)
- [ ] Include account codes (for journal entries)
- [ ] Include period (for ledger posting)
- [ ] Include currency (for multi-currency tenants)

### Strongly Recommended
- [ ] Include `correlation_id` (trace related events)
- [ ] Include `causation_id` (direct parent event)
- [ ] Include `actor_type` and `actor_id` (who triggered this)
- [ ] Document schema (event description, payload examples)

---

## Related Documents

- **ARCH-07**: Design Patterns — Events as First-Class Citizen pattern
- **STD-03**: Registries & Events & Files — Event storage and schema registration
- **STD-17**: Logging & Observability — Logging events and tracing
- **SPEC-10**: Accounting Core Process — Journal entries from events
- **SPEC-09**: PMS Core Process — Folio events
- **SEC-02**: Data Protection — Event signature verification

---

## Compliance Checklist

- [ ] All events have required fields (event_id, event_type, tenant_id, signature)
- [ ] Event schema documented in schema registry
- [ ] Consumers implement idempotency (prevent duplicates)
- [ ] Dead Letter Queue configured and monitored
- [ ] Event versioning strategy documented
- [ ] Error handling for failed consumers defined
- [ ] Tracing via correlation_id implemented
- [ ] Financial events include full context (no lookups)
- [ ] Events are immutable (no updates after publish)
- [ ] Audit trail captures all published events
- [ ] Monitoring and alerting for event processing latency
- [ ] Consumer lag monitored (are consumers falling behind?)
