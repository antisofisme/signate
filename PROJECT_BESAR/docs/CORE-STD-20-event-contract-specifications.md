# STD-19: Event Contract Standard

This document defines the **formal event schema, naming conventions, versioning rules, and integrity requirements** for all events in PROJECT_BESAR. Event contracts are binding agreements between producers and consumers across modules and tenants.

**Usage**: Consult this when:
- Publishing events from any module
- Implementing event consumers
- Evolving event schemas
- Designing cross-tenant integrations

---

## Core Principles (Locked)

### Principle 1: Backward Compatibility
```
Event schema changes must not break existing consumers.
Consumer versioning allows gradual migration.
```

### Principle 2: Immutable Payload (Authoritative Specification)
```
Events cannot be edited after publication.
Corrections issued as new events (reversal pattern).

IMMUTABILITY RULES:
✅ Create new events to correct/reverse (e.g., refund as separate event)
✅ All events append-only to event log
✅ Never update or delete any event after publishing
✅ Enables forensics and audit trail integrity
❌ Never modify event payload
❌ Never delete from event stream
❌ Never rewrite event timestamp

REVERSAL PATTERN:
- Original event: "Accounting.Invoice.Created.v1" (amount: +1000)
- Reversal event: "Accounting.Invoice.Reversed.v1" (causation_id → original, amount: -1000)
- Net effect: +1000 -1000 = 0, but full history preserved
```

### Principle 3: Explicit Versioning
```
Version embedded in event_type (authoritative source of truth).
Format: Domain.Entity.Action.v<N>
v1, v2, v3 = different contracts (consumers implement explicitly).
event_version field mirrors event_type version for query convenience.
```

### Principle 4: Tenant-First
```
tenant_id ALWAYS mandatory.
No event without tenant context.
Enables tenant isolation and filtering.
```

### Principle 5: Correlation-Driven
```
All cross-module processes use correlation_id.
Allows tracing causal chains across boundaries.
Required for approval workflows and inter-tenant flows.
```

---

## Event Envelope (Global Standard)

All events MUST conform to this envelope structure:

```json
{
  "event_id": "uuid",
  "event_type": "string (Domain.Entity.Action.vN)",
  "event_version": "v1",
  "occurred_at": "ISO-8601 timestamp",
  "tenant_id": "uuid (mandatory)",
  "actor_type": "user|system|external",
  "actor_id": "uuid|null",
  "correlation_id": "uuid",
  "payload": {
    // Domain-specific fields
  }
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | UUID | ✅ | Unique event identifier |
| `event_type` | String | ✅ | **Authoritative** event contract name with version (e.g., `Accounting.Invoice.Finalized.v1`) |
| `event_version` | String | ✅ | **Convenience field**: Semantic version extracted from `event_type` (v1, v2). Must match the version in `event_type`. |
| `occurred_at` | ISO-8601 | ✅ | Timestamp when event occurred in source system |
| `tenant_id` | UUID | ✅ | **MANDATORY** - tenant context (must be UUID v4 format, no prefixes) |
| `actor_type` | Enum | ✅ | Who triggered: USER, SYSTEM (scheduler), EXTERNAL (API) |
| `actor_id` | UUID | ❌ | User/system ID (null if external) |
| `correlation_id` | UUID | ✅ | Links related events across modules (MANDATORY - required for all events) |
| `signature` | String | ✅ | **REQUIRED** - HMAC-SHA256 hash for event authentication and tamper detection |
| `payload` | Object | ✅ | Domain-specific event data |

---

## Naming Convention

### Format
```
<Domain>.<Entity>.<Action>.<vVersion>
```

### Rules
1. **Domain**: Operational module (Accounting, PMS, Inventory, HR, Supplier, Approval, etc.)
2. **Entity**: What changed (Invoice, Guest, Reservation, PurchaseOrder, etc.)
3. **Action**: What happened (Created, Updated, Finalized, Approved, etc.)
4. **Version**: Explicit version (v1, v2, v3)

### Examples
```
✅ Accounting.Invoice.Finalized.v1
✅ PMS.Guest.CheckedIn.v1
✅ Supplier.Invoice.Issued.v1
✅ Approval.Request.Approved.v2
❌ accounting-invoice-finalized (wrong format)
❌ InvoiceFinalizedEvent (missing version, wrong case)
❌ Accounting.Invoice.Finalized (missing version)
```

---

## Core Accounting Events

### Accounting.Invoice.Finalized.v1

Published when invoice is locked and ready for posting.

```json
{
  "invoice_id": "uuid",
  "invoice_number": "INV-2025-001",
  "amount": 1200000,
  "currency": "IDR",
  "source": "PMS|POS|External|Supplier",
  "due_date": "ISO-8601",
  "created_at": "ISO-8601",
  "finalized_at": "ISO-8601"
}
```

**Consumer**: Accounting.Adapter (posts journal entries to GL)

---

### Accounting.Payment.Recorded.v1

Published when payment is allocated to invoice.

```json
{
  "payment_id": "uuid",
  "invoice_id": "uuid",
  "amount": 1200000,
  "currency": "IDR",
  "method": "cash|transfer|gateway",
  "recorded_at": "ISO-8601",
  "reference": "string (bank reference, check number, etc.)"
}
```

**Consumer**: Accounting.Adapter (posts GL entries, updates AR aging)

---

### Accounting.Period.Closed.v1

Published when accounting period is locked.

```json
{
  "period_id": "uuid",
  "period_start": "ISO-8601",
  "period_end": "ISO-8601",
  "status": "closed",
  "locked_at": "ISO-8601",
  "locked_by": "uuid"
}
```

**Consumer**: Audit trail (marks period immutable)

---

## PMS Core Events

### PMS.Reservation.Created.v1

Published when reservation is made.

```json
{
  "reservation_id": "uuid",
  "guest_id": "uuid",
  "checkin_date": "ISO-8601",
  "checkout_date": "ISO-8601",
  "room_id": "uuid",
  "room_type": "standard|deluxe|suite",
  "nightly_rate": 500000,
  "total_nights": 3,
  "created_at": "ISO-8601"
}
```

**Consumer**: Accounting.Adapter (creates AR folio)

---

### PMS.Guest.CheckedIn.v1

Published when guest checks in.

```json
{
  "reservation_id": "uuid",
  "guest_id": "uuid",
  "folio_id": "uuid",
  "room_number": "string",
  "checked_in_at": "ISO-8601"
}
```

**Consumer**: Accounting (activates folio for charges)

---

### PMS.Guest.CheckedOut.v1

Published when guest checks out and folio closes.

```json
{
  "reservation_id": "uuid",
  "folio_id": "uuid",
  "guest_id": "uuid",
  "total_charges": 1500000,
  "total_payments": 1500000,
  "checked_out_at": "ISO-8601"
}
```

**Consumer**: Accounting.Adapter (finalizes folio invoice, posts GL)

---

## Inventory Events

### Inventory.StockAdjusted.v1

Published when stock quantity changes.

```json
{
  "item_id": "uuid",
  "quantity_before": 100,
  "quantity_after": 95,
  "adjustment_reason": "usage|damage|recount|receipt",
  "adjusted_at": "ISO-8601",
  "adjusted_by": "uuid"
}
```

**Consumer**: Accounting.Adapter (records COGS if usage)

---

## Inter-Tenant Supplier Events

### Supplier.PurchaseOrder.Issued.v1

Published by buyer tenant when PO is sent to supplier.

```json
{
  "po_id": "uuid",
  "buyer_tenant_id": "uuid",
  "supplier_tenant_id": "uuid",
  "supplier_name": "string",
  "total_amount": 5000000,
  "currency": "IDR",
  "items": [
    {
      "item_id": "uuid",
      "quantity": 10,
      "unit_price": 500000
    }
  ],
  "delivery_date": "ISO-8601",
  "issued_at": "ISO-8601"
}
```

**Consumers**:
- Supplier tenant (creates purchase order in own system)
- Buyer tenant Accounting (records AP commitment)

---

### Supplier.Invoice.Issued.v1

Published by supplier tenant when invoice issued to buyer.

```json
{
  "invoice_id": "uuid",
  "po_id": "uuid",
  "buyer_tenant_id": "uuid",
  "supplier_tenant_id": "uuid",
  "invoice_number": "string (supplier's invoice number)",
  "amount": 5000000,
  "currency": "IDR",
  "due_date": "ISO-8601",
  "issued_at": "ISO-8601"
}
```

**Consumers**:
- Buyer tenant Accounting (records AP invoice)
- Supplier tenant Accounting (records AR invoice)

---

### Supplier.Invoice.Approved.v1

Published by buyer tenant when invoice approved for payment.

```json
{
  "invoice_id": "uuid",
  "po_id": "uuid",
  "buyer_tenant_id": "uuid",
  "supplier_tenant_id": "uuid",
  "approved_at": "ISO-8601",
  "approved_by": "uuid",
  "approval_level": "standard|override"
}
```

**Consumer**: Supplier tenant (marks invoice for payment expectation)

---

## Approval Events

### Approval.Requested.v1

Published when action requires approval (e.g., invoice >$5K).

```json
{
  "approval_id": "uuid",
  "entity_type": "invoice|purchase_order|payment|refund",
  "entity_id": "uuid",
  "amount": 50000000,
  "required_role": "admin|owner",
  "threshold": 5000000,
  "requested_by": "uuid",
  "requested_at": "ISO-8601",
  "context": {
    "reason": "string (why approval needed)"
  }
}
```

**Consumer**: Approval.Workflow (notifies approvers, waits for decision)

---

### Approval.Decided.v1

Published when approver decides (approved/rejected).

```json
{
  "approval_id": "uuid",
  "entity_id": "uuid",
  "decision": "approved|rejected",
  "decided_by": "uuid",
  "decided_at": "ISO-8601",
  "notes": "string|null"
}
```

**Consumers**:
- Original process (continues if approved)
- Audit trail (records decision)

---

## Event Publishing & Consumption

### Publishing Rules

1. **Always validate** payload against schema before publishing
2. **Include correlation_id** for any process that will have multiple events
3. **Set occurred_at** to actual time in source system, not publishing time
4. **Sign event** with HMAC or digital signature (see Security section below)
5. **Idempotent keys** for critical events (invoice, payment) to prevent duplicates

### Consumer Rules

1. **Never trust raw payload** - validate against schema
2. **Handle unknown fields gracefully** - don't fail on extra fields (forward compatibility)
3. **Implement idempotency** - store `event_id` to prevent processing duplicates
4. **Track correlation_id** - link related events for tracing
5. **Implement exponential backoff** on processing failures

---

## Versioning Strategy

### When to Create New Version

**v2 needed if**:
- Removing required field → Breaking change
- Renaming field → Breaking change
- Changing field type → Breaking change
- Adding new **required** field → Breaking change

**v1 can absorb if**:
- Adding optional field → Not breaking
- Adding new nested object → Not breaking
- Narrowing allowed values (if optional) → Might be compatible

### Migration Path Example

```typescript
// Old event stream has mixed v1 and v2
function processEvent(event) {
  if (event.event_type === 'Accounting.Invoice.Finalized.v1') {
    return handleV1(event.payload);
  } else if (event.event_type === 'Accounting.Invoice.Finalized.v2') {
    return handleV2(event.payload);
  }
}

// Gradually migrate producers
// Once all producers emit v2, can deprecate v1 handler
// Delete v1 handlers only after 90+ days of zero v1 events
```

---

## Security & Integrity Rules

### Event Signing

All events MUST be signed before publishing:

```typescript
// HMAC signature
const signature = crypto
  .createHmac('sha256', SECRET_KEY)
  .update(JSON.stringify(event))
  .digest('hex');

event.signature = signature;
```

### Consumer Verification

Consumers MUST verify signature before processing:

```typescript
function isValidEvent(event) {
  const expected = crypto
    .createHmac('sha256', SECRET_KEY)
    .update(JSON.stringify({...event, signature: undefined}))
    .digest('hex');

  return event.signature === expected;
}
```

### Audit Logging

- **ALL events** recorded to immutable audit log
- Audit log append-only (no deletes)
- Includes signature for tampering detection
- Queryable by: event_type, tenant_id, correlation_id, occurred_at range

### Tenant Isolation

- Events for Tenant A cannot be read by Tenant B (database-level filtering)
- Event consumers scoped to tenant context
- Cross-tenant events (Supplier flows) use separate flow with explicit approval

---

## Hard Rules (Non-Negotiable)

### ❌ Forbidden Practices

| Practice | Why | Example |
|----------|-----|---------|
| Schema change without version | Breaks existing consumers | Adding field to Accounting.Invoice.Finalized.v1 |
| Consumer depends on optional field | Optional fields can disappear | `if (event.optional_field) {...}` |
| Using event stream as query | Events are write-only log, not queryable DB | `SELECT * FROM events WHERE amount > $X` |
| Mutating event after publish | Breaks audit trail and consumer contracts | Updating event payload after it's published |
| Omitting tenant_id | Breaks tenant isolation | Publishing event without tenant context |
| **Omitting correlation_id** | **Breaks event tracing and correlation** | **Publishing event without correlation_id (ALWAYS REQUIRED)** |
| Using event for immediate data sync | Events are async, not guaranteed ordering | Publishing event and immediately reading from DB before consumer processes |
| Free-form event_type | Makes discoverability and versioning impossible | Publishing as "event_123" or "stuff_happened" |
| Omitting signature | Enables tampering and security breaches | Publishing unsigned events |

---

## Event Lifecycle Example

### Scenario: Hotel Guest Checkout

```
1. Guest checks out
   └─ PMS publishes: PMS.Guest.CheckedOut.v1
      payload: {reservation_id, folio_id, charges}
      correlation_id: "abc-123"

2. Accounting.Adapter consumes event
   └─ Creates Accounting.Invoice.Finalized.v1
      correlation_id: "abc-123" (same)
      Publishes for GL posting

3. Accounting.GL consumes Finalize event
   └─ Posts journal entries (AR debit, Revenue credit)
   └─ Publishes: Accounting.Invoice.Posted.v1
      correlation_id: "abc-123"

4. Audit log stores all 3 events
   - Can trace full causal chain via correlation_id
   - All events signed and immutable
   - Queries: "Show me all events for folio_id XYZ"
```

---

## Event Schema Validation

### Using JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Accounting.Invoice.Finalized.v1",
  "type": "object",
  "required": [
    "event_id",
    "event_type",
    "occurred_at",
    "tenant_id",
    "correlation_id",
    "invoice_id",
    "amount",
    "currency"
  ],
  "properties": {
    "invoice_id": {
      "type": "string",
      "format": "uuid"
    },
    "amount": {
      "type": "integer",
      "minimum": 0
    },
    "currency": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  }
}
```

### Runtime Validation

```typescript
import Ajv from 'ajv';

const ajv = new Ajv();
const validate = ajv.compile(SCHEMA);

if (!validate(event)) {
  throw new Error(`Invalid event: ${JSON.stringify(validate.errors)}`);
}
```

---

## Troubleshooting Guide

### Issue: Consumer Fails on New Field

**Symptom**: Consumer throws error on `unknown field X`

**Root Cause**: Consumer too strict, doesn't handle forward compatibility

**Fix**: Update consumer to ignore unknown fields
```typescript
// Instead of: const { knownField } = event.payload;
// Do: const { knownField, ...unknownFields } = event.payload;
// (ignore unknownFields)
```

---

### Issue: Events Processed Out of Order

**Symptom**: Payment event processed before Invoice.Finalized event

**Root Cause**: Events are NOT ordered by default, async processing

**Fix**: Implement idempotency with correlation_id
```typescript
// Store processed events by correlation_id + event_type
// Skip reprocessing if already handled
const key = `${event.correlation_id}:${event.event_type}`;
if (alreadyProcessed(key)) return;
```

---

### Issue: Cross-Tenant Event Leakage

**Symptom**: User sees events from other tenant

**Root Cause**: Missing tenant_id filter in consumer

**Fix**: Always filter by tenant_id
```typescript
// WRONG: SELECT * FROM events WHERE event_type = 'PMS.Guest.CheckedOut.v1'
// RIGHT: SELECT * FROM events WHERE event_type = 'PMS.Guest.CheckedOut.v1' AND tenant_id = $1
```

---

## Compliance Checklist

When defining new event:

- [ ] Event conforms to global envelope structure
- [ ] event_type follows Domain.Entity.Action.vN naming
- [ ] tenant_id included
- [ ] correlation_id included for cross-module flows
- [ ] Payload schema documented (required vs optional)
- [ ] Consumer(s) identified
- [ ] Versioning strategy defined
- [ ] Signature validation required before consuming
- [ ] Audit logging configured
- [ ] Backward compatibility considered
- [ ] Test: publish and consume locally
- [ ] Test: verify signature validation
- [ ] Test: verify tenant isolation
- [ ] Test: verify idempotent reprocessing

---

## References

- **STD-17**: Logging & Observability — Structured logging alongside events
- **ARCH-07**: Design Patterns & Concepts — CQRS and event sourcing patterns
- **SPEC-11**: Inter-Tenant Supplier Flow — Event-driven cross-tenant integration
- **SEC-03**: Authorization, Approval & Audit — Audit logging of all events
- **STD-08**: Multi-Tenant Backup & Restore — Event log implications for restore
