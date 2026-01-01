# ARCH-11: API Architecture & Boundaries

This document defines the architectural boundaries for the four API types in ATLAS_PANDAWA: Public, Internal, Partner, and Event. These boundaries prevent data leakage, enforce tenant isolation, and ensure clean module separation.

**Core Principle**: *APIs are scoped by audience and authentication model. Different scopes require different security, validation, and audit rules.*

---

## Why API Architecture Matters

### Problems Without Clear Boundaries

- Frontend accidentally calls internal module APIs (data leakage risk)
- Modules tightly coupled via synchronous API calls (scalability issues)
- Partner tenants access unauthorized data (security breach)
- No clear contract for inter-module communication (tight coupling)

### Benefits of Boundary-Based Architecture

| Benefit | How Achieved |
|---------|-------------|
| **Tenant Isolation** | tenant_id scoped to each API |
| **Loose Coupling** | Events for async, not direct API calls |
| **Security** | Authentication/authorization per API type |
| **Scalability** | Modules don't wait for each other (async patterns) |
| **Compliance** | Clear audit trail per API type |
| **Multi-Tenancy** | Partner APIs explicitly authorize cross-tenant access |

---

## Core Principles (Locked)

### Principle 1: APIs Follow Bounded Context
```
Each module defines its API boundaries.
No API exposes internal implementation details.
API contract is the boundary.
```

### Principle 2: Tenant Scope Mandatory
```
Every API must have tenant_id in request context.
User cannot specify tenant_id (derived from auth token).
API enforces: "Access only to my tenant's data"
```

### Principle 3: Public API ≠ Internal API
```
Never expose internal APIs to public consumers.
Public APIs optimized for user experience.
Internal APIs optimized for module integration.
```

### Principle 4: Event is Primary Integration Boundary
```
Modules integrate via events, not API calls.
Events: loosely coupled, asynchronous, immutable.
APIs: for immediate responses, not integration.
```

### Principle 5: No Cross-Tenant APIs Without Contract
```
Partner API requires BusinessContract.
Contract explicitly lists authorized operations.
Both tenants must approve integration.
```

### Principle 6: API Versioning Strategy
```
REST APIs: URL-based versioning (/api/v1, /api/v2)
GraphQL: Versionless with field-level deprecation
Events: Semantic versioning per event (Domain.Entity.Action.vN)

REST Versioning:
  /api/v1/...  (current version)
  /api/v2/...  (if incompatible changes needed)

Compatibility:
  - At least 1 version backward compatible
  - Deprecation window: 6 months notice
  - v1 to v2 migration path documented

Example:
  GET /api/v1/pms/reservations  → includes guest_name, room_type
  GET /api/v2/pms/reservations  → restructured response (incompatible)
  → Support both for 6 months
  → Deprecate v1 after 6 months

Events use semantic versioning independent of REST API:
  PMS.Reservation.Created.v1   (initial version)
  PMS.Reservation.Created.v2   (if fields added, schema evolved)
  Both versions coexist (consumers handle each version)
```

---

## API Type 1: Public API

### Purpose
User-facing APIs consumed by:
- Web browser (SPA)
- Mobile app
- PWA
- External integrations with explicit permission

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Authentication** | User token (JWT, OAuth) |
| **Scope** | user_id + tenant_id (from token) |
| **Rate Limiting** | Yes (per user) |
| **Response Format** | JSON (application/json) |
| **Error Handling** | User-friendly messages |
| **Logging** | Audit trail (who, what, when) |
| **Timeout** | < 30 seconds (user is waiting) |

### Naming Convention

```
GET    /api/v1/pms/reservations
POST   /api/v1/pms/reservations
GET    /api/v1/accounting/invoices/{id}
POST   /api/v1/accounting/payments
PUT    /api/v1/profile/user
DELETE /api/v1/memberships/{id}
```

### Request Pattern

```json
{
  "headers": {
    "Authorization": "Bearer <jwt-token>",
    "Content-Type": "application/json",
    "X-Tenant-ID": "<derived-from-token>"  // Never user-specified
  },
  "body": {
    // Business data
  }
}
```

### Response Pattern (Success)

```json
{
  "data": {
    "id": "uuid",
    "name": "Guest Name",
    ...
  },
  "meta": {
    "timestamp": "ISO-8601",
    "request_id": "uuid"
  }
}
```

### Response Pattern (Error)

```json
{
  "error": {
    "code": "INVOICE_NOT_FOUND",
    "message": "Invoice INV-001 not found in your account",
    "details": {
      "invoice_id": "..."
    }
  },
  "meta": {
    "timestamp": "ISO-8601",
    "request_id": "uuid"
  }
}
```

### Examples

#### PMS Operations
```
POST   /api/v1/pms/reservations          → Create reservation
GET    /api/v1/pms/reservations/{id}     → View reservation
PUT    /api/v1/pms/reservations/{id}     → Modify reservation
POST   /api/v1/pms/guests/{id}/check-in  → Check in guest
POST   /api/v1/pms/guests/{id}/check-out → Check out guest
```

#### Accounting
```
GET    /api/v1/accounting/invoices        → List invoices (AR)
POST   /api/v1/accounting/payments        → Record payment
GET    /api/v1/accounting/reports/balance-sheet → Financial statement
```

#### Inventory
```
GET    /api/v1/inventory/items            → List inventory
POST   /api/v1/inventory/adjustments      → Adjust stock
GET    /api/v1/inventory/reports/valuation → Inventory valuation
```

### Security Rules

**Must Enforce**:
1. User authenticated (valid token)
2. User is member of tenant (Membership check)
3. Tenant has app subscribed (TenantApp check)
4. User has required permission for action

**Validation**:
```typescript
// Pseudo-code
function handlePublicAPI(req) {
  // 1. Verify token
  const user = verifyToken(req.headers.authorization);
  if (!user) return 401 Unauthorized;

  // 2. Extract tenant from token
  const tenantId = user.tenant_id;  // NOT from request body

  // 3. Verify user is member of tenant
  const membership = await db.getMembership(user.id, tenantId);
  if (!membership) return 403 Forbidden;

  // 4. Verify tenant has app subscribed
  if (!await isTenantSubscribedTo(tenantId, 'PMS')) {
    return 403 Forbidden;
  }

  // 5. Check permissions based on role
  if (!hasPermission(membership.role, 'reservation.create')) {
    return 403 Forbidden;
  }

  // 6. Process request with tenant context
  const result = await createReservation(tenantId, req.body);

  // 7. Audit log
  await auditLog.record({
    user_id: user.id,
    tenant_id: tenantId,
    action: 'create',
    entity: 'reservation',
    result: 'success'
  });

  return 200 OK with result;
}
```

---

## API Type 2: Internal API

### Purpose
Module-to-module communication within the platform. **Never exposed to external consumers.**

### Examples
- Accounting Adapter calling GL posting API
- Subscription service checking feature gates
- Notification service sending alerts
- Reporting service querying read models

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Authentication** | Service token (mTLS certificate or JWT service account) |
| **Scope** | Service context (no user) |
| **Rate Limiting** | Yes (per service) |
| **Response Format** | JSON |
| **Error Handling** | Technical details OK (for ops) |
| **Logging** | System audit trail |
| **Timeout** | Configurable (default 60 seconds) |
| **Discovery** | Service mesh (e.g., Kubernetes DNS) |

### Naming Convention

```
POST   /_internal/accounting/journal
GET    /_internal/subscription/status
POST   /_internal/notification/send
GET    /_internal/read-model/occupancy
```

**Note**: `_internal` prefix signals "not for public use"

### Request Pattern

```json
{
  "headers": {
    "Authorization": "Bearer <service-token>",
    "X-Service-ID": "accounting-adapter",
    "X-Request-ID": "uuid"  // For tracing
  },
  "body": {
    "tenant_id": "uuid",  // Service specifies tenant
    // Technical data
  }
}
```

### Examples

#### GL Posting (Accounting Internal)
```typescript
POST /_internal/accounting/journal
{
  "tenant_id": "hotel-jakarta",
  "journal_entry": {
    "entry_date": "2025-12-23",
    "lines": [
      {
        "account_code": "1200",  // AR account
        "debit": 1500000,
        "description": "Guest folio checkout"
      },
      {
        "account_code": "4100",  // Room revenue
        "credit": 1500000,
        "description": "Room revenue"
      }
    ],
    "source_type": "folio",
    "source_id": "folio-123"
  }
}
```

#### Subscription Check (Feature Gate)
```typescript
GET /_internal/subscription/status?tenant_id=hotel-jakarta&app=PMS
Response:
{
  "is_active": true,
  "remaining_quota": 9999,
  "next_renewal": "2025-12-31"
}
```

#### Notification Sending
```typescript
POST /_internal/notification/send
{
  "tenant_id": "hotel-jakarta",
  "recipient_id": "user-123",
  "type": "invoice_approved",
  "data": {
    "invoice_id": "inv-001",
    "amount": 1500000
  }
}
```

### Security Rules

**Must Enforce**:
1. Service authenticated (valid service token)
2. Service authorized for operation (service-level permissions)
3. Tenant context included (can't access all tenants)

**Validation**:
```typescript
function handleInternalAPI(req) {
  // 1. Verify service token
  const service = verifyServiceToken(req.headers.authorization);
  if (!service) return 401 Unauthorized;

  // 2. Check service permission (can this service call this API?)
  if (!hasServicePermission(service.id, req.path)) {
    return 403 Forbidden;
  }

  // 3. Extract tenant from request
  const tenantId = req.body.tenant_id;
  if (!tenantId) return 400 Bad Request;

  // 4. Process with tenant isolation
  const result = await postJournal(tenantId, req.body.journal_entry);

  // 5. System audit log
  await systemAuditLog.record({
    service: service.id,
    tenant_id: tenantId,
    action: 'journal_post',
    result: 'success'
  });

  return 200 OK with result;
}
```

### Why Services Use Internal APIs (Not Events)

**Events good for**:
- Fire-and-forget notifications
- Eventual consistency OK
- No immediate response needed
- Can tolerate message loss (retry)

**Internal APIs needed for**:
- Immediate response required
- Transaction atomicity needed
- Validation + response in same call
- Strong consistency required

Example: GL posting MUST succeed immediately (can't be eventual consistency)

---

## API Type 3: Partner API

### Purpose
Inter-tenant integration between supplier and buyer tenants.

Examples:
- Hotel ordering from Laundry supplier
- Supplier issuing invoice to hotel
- Hotel approving supplier's invoice
- Supplier tracking delivery status

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Authentication** | Contract + Signature (HMAC-SHA256) |
| **Scope** | contract_id (limited to specific relationship) |
| **Rate Limiting** | Yes (per partner) |
| **Response Format** | JSON (with signature) |
| **Error Handling** | Technical details (both are operators) |
| **Logging** | Partner audit trail (both can query) |
| **Timeout** | 30-60 seconds |
| **Requirement** | BusinessContract must exist |

### Naming Convention

```
POST   /api/v1/partner/po/accept
POST   /api/v1/partner/invoice/issue
GET    /api/v1/partner/invoices
POST   /api/v1/partner/payments/confirm
```

### Request Pattern

```json
{
  "headers": {
    "X-Contract-ID": "<business_contract_id>",
    "X-Timestamp": "ISO-8601",
    "X-Signature": "HMAC-SHA256(<body>, <contract_secret>)"
  },
  "body": {
    "partner_tenant_id": "laundry-abc",
    // Business data
  }
}
```

### Examples

#### Hotel Issues Purchase Order to Supplier
```typescript
POST /api/v1/partner/po/issue
{
  "headers": {
    "X-Contract-ID": "contract-123",
    "X-Signature": "..."
  },
  "body": {
    "buyer_tenant_id": "hotel-jakarta",
    "seller_tenant_id": "laundry-abc",
    "po_number": "PO-2025-001",
    "items": [
      {
        "item_code": "DRY-CLEAN",
        "quantity": 100,
        "unit_price": 15000
      }
    ],
    "delivery_date": "2025-12-25",
    "total_amount": 1500000
  }
}

Response:
{
  "po_id": "po-123",
  "status": "acknowledged",
  "acknowledged_at": "2025-12-23T10:00:00Z",
  "signature": "..."
}
```

#### Supplier Issues Invoice to Hotel
```typescript
POST /api/v1/partner/invoice/issue
{
  "headers": {
    "X-Contract-ID": "contract-123",
    "X-Signature": "..."
  },
  "body": {
    "supplier_tenant_id": "laundry-abc",
    "buyer_tenant_id": "hotel-jakarta",
    "po_id": "po-123",
    "invoice_number": "INV-LAU-001",
    "amount": 1500000,
    "due_date": "2025-12-30"
  }
}
```

### Security Rules

**Must Enforce**:
1. Contract exists and is active
2. Request signature valid (HMAC verification)
3. Both tenants match contract participants
4. Request timestamp recent (prevent replay attacks)
5. Operation authorized by contract terms

**Validation**:
```typescript
function handlePartnerAPI(req) {
  // 1. Verify contract exists
  const contract = await db.getContract(req.headers['X-Contract-ID']);
  if (!contract || contract.status !== 'active') {
    return 403 Forbidden;
  }

  // 2. Verify signature
  const expectedSig = hmac256(JSON.stringify(req.body), contract.secret);
  if (req.headers['X-Signature'] !== expectedSig) {
    return 401 Unauthorized;  // Tampered or invalid signature
  }

  // 3. Verify timestamp is recent (prevent replay)
  const reqTime = new Date(req.headers['X-Timestamp']);
  if (Date.now() - reqTime > 5 * 60 * 1000) {  // 5 min window
    return 401 Unauthorized;
  }

  // 4. Verify tenants match contract
  const { buyer, seller } = extractTenantsFromRequest(req.body);
  if (!(
    (contract.buyer_tenant_id === buyer && contract.seller_tenant_id === seller) ||
    (contract.seller_tenant_id === buyer && contract.buyer_tenant_id === seller)
  )) {
    return 403 Forbidden;
  }

  // 5. Verify operation authorized by contract
  if (!contract.terms.allowed_operations.includes(req.path)) {
    return 403 Forbidden;
  }

  // 6. Process request
  const result = await issueInvoice(contract, req.body);

  // 7. Both-tenant audit log
  await partnerAuditLog.record({
    contract_id: contract.id,
    initiator_tenant: buyer,
    recipient_tenant: seller,
    operation: req.path,
    result: 'success'
  });

  // 8. Publish event (for async processing)
  await publishEvent({
    event_type: 'Supplier.Invoice.Issued.v1',
    tenant_id: seller,  // Seller's perspective
    correlation_id: generateCorrelationId(),
    payload: result
  });

  return 200 OK with result;
}
```

### Flow: Partner Integration

```
1. Hotel calls Partner API POST /po/issue
   ├─ Contract verified
   ├─ Signature validated
   └─ PO created in Supplier's tenant

2. Supplier's event handler consumes PO.Issued event
   ├─ Updates internal PO status
   └─ May publish PO.Acknowledged event

3. Hotel receives PO.Acknowledged event
   ├─ Updates local PO status
   └─ Can trigger notification

4. Supplier fulfills order, calls Partner API POST /invoice/issue
   ├─ Contract verified
   ├─ Signature validated
   └─ Invoice created in Hotel's tenant

5. Hotel's Accounting.Adapter consumes Invoice.Issued event
   ├─ Creates AP invoice
   └─ Publishes Approval.Requested (if >threshold)

6. Hotel approves via Partner API POST /approval/decide
   └─ Both tenants notified
```

---

## API Type 4: Event API (Message Bus)

### Purpose
Asynchronous, event-driven integration. **Not for query or request-response.**

### Characteristics

| Aspect | Detail |
|--------|--------|
| **Communication** | Publish/Subscribe (message broker) |
| **Audience** | Any interested consumer |
| **Response** | None (fire-and-forget) |
| **Ordering** | Guaranteed per tenant_id partition |
| **Delivery** | At-least-once (consumer idempotent) |
| **Data** | Immutable (append-only) |

### Examples

```
Event: Guest.CheckedOut.v1
Event: Invoice.Finalized.v1
Event: Supplier.Invoice.Issued.v1
Event: Approval.Requested.v1
Event: Journal.Posted.v1
```

### When to Use Events (vs APIs)

| Scenario | Use Event | Use API |
|----------|-----------|---------|
| Guest checks out → Accounting posts GL | Event | No |
| Admin needs AR aging report | No | API |
| Payment received → Mark invoice paid | API (immediate) | Then event |
| Cross-tenant supplier invoice | Event | + Partner API |
| Hotel queries occupancy | No | API |
| Night audit completes → Email report | Event | No |

### Rules for Event-Driven Integration

**✅ Use Events for**:
- State changes (guest checked out, payment received)
- Cross-module notifications (triggering workflows)
- Audit trail (what happened and when)
- Fire-and-forget scenarios

**❌ Don't Use Events for**:
- Query/retrieval (cannot query events)
- Request-response (events don't reply)
- Immediate strong consistency (eventual consistency only)
- Direct data transfer (events are thin notifications, not data dumps)

---

## API Responsibility Matrix

Which API type handles which responsibilities:

| Responsibility | Public API | Internal API | Partner API | Event API |
|---|---|---|---|---|
| User authentication | ✅ | ❌ | ❌ | ❌ |
| Service authentication | ❌ | ✅ | ❌ | ❌ |
| Cross-tenant operation | ❌ | ❌ | ✅ | ✅ (with contract) |
| PMS operations (search, create, update) | ✅ | ❌ | ❌ | ❌ |
| GL posting | ❌ | ✅ | ❌ | ❌ |
| Feature gating checks | ✅ (for response) | ✅ | ❌ | ❌ |
| Supplier integration | ❌ | ❌ | ✅ | ✅ |
| Accounting notifications | ❌ | ❌ | ❌ | ✅ |
| Guest checkout | ✅ | ❌ | ❌ | ✅ (publishes event) |
| Invoice approval | ✅ | ❌ | ✅ (cross-tenant) | ✅ (notifies) |
| Reporting/BI queries | ✅ | ❌ | ❌ | ❌ |

---

## Anti-Patterns (Forbidden)

### ❌ Anti-Pattern 1: Frontend Calls Internal API

```typescript
// WRONG: Frontend calls _internal API
fetch('/_internal/accounting/journal', {
  method: 'POST',
  body: JSON.stringify(...)
});

// RIGHT: Frontend calls Public API
fetch('/api/v1/accounting/invoices', {
  method: 'POST',
  body: JSON.stringify(...)
});
// Backend internally calls _internal/journal via adapter
```

**Consequence**: Security breach, audit trail pollution, tight coupling

---

### ❌ Anti-Pattern 2: Public API Posts Journal Entry

```typescript
// WRONG: Public API directly manipulates GL
app.post('/api/v1/accounting/journal', (req, res) => {
  db.insertJournalEntry(req.body);  // Direct GL manipulation
});

// RIGHT: Public API creates invoice, internal adapter posts GL
app.post('/api/v1/accounting/invoices', (req, res) => {
  const invoice = await createInvoice(req.body);
  // Adapter consumes Invoice.Finalized event and posts GL
});
```

**Consequence**: Accounting integrity compromised, no separation of concerns

---

### ❌ Anti-Pattern 3: Partner API Without Contract

```typescript
// WRONG: Partner API allowing any cross-tenant call
app.post('/api/v1/partner/invoice/issue', (req, res) => {
  // No contract check
  const invoice = await createInvoice(req.body);
});

// RIGHT: Partner API validates contract
function validateContract(contractId) {
  const contract = await db.getContract(contractId);
  if (!contract || contract.status !== 'active') {
    throw new Error('Invalid or inactive contract');
  }
  return contract;
}
```

**Consequence**: Data leak, unauthorized access

---

### ❌ Anti-Pattern 4: Querying Events

```typescript
// WRONG: Using events as query source
SELECT * FROM events
WHERE event_type = 'Guest.CheckedOut.v1'
  AND occurred_at BETWEEN $1 AND $2;

// RIGHT: Query read model (derived from events)
SELECT * FROM occupancy_snapshot
WHERE date = CURRENT_DATE;
```

**Consequence**: Slow queries, event ordering issues, incorrect data

---

## Implementation Patterns

### Pattern 1: Public API with Internal Adapter

```typescript
// Public API (user-facing)
app.post('/api/v1/pms/guests/check-out', async (req, res) => {
  const { reservationId } = req.body;
  const tenantId = req.user.tenant_id;

  // 1. User-friendly validation
  const reservation = await db.getReservation(tenantId, reservationId);
  if (!reservation || reservation.status !== 'checked_in') {
    return res.status(400).json({ error: 'Guest not checked in' });
  }

  // 2. Close folio
  const folio = await closeFolio(tenantId, reservation.folio_id);

  // 3. Publish event (adapter will consume)
  await publishEvent({
    event_type: 'Guest.CheckedOut.v1',
    tenant_id: tenantId,
    payload: { reservation_id: reservationId, folio_id: folio.id }
  });

  return res.json({ success: true, folio });
});

// Internal adapter (module-to-module)
eventBroker.subscribe('Guest.CheckedOut.v1', async (event) => {
  const { tenant_id, payload } = event;

  // Call internal GL posting API
  await fetch('/_internal/accounting/journal', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${SERVICE_TOKEN}` },
    body: JSON.stringify({
      tenant_id,
      journal_entry: {
        source_type: 'folio',
        source_id: payload.folio_id,
        lines: [
          { account: 'AR', debit: folio.amount },
          { account: 'REVENUE', credit: folio.amount }
        ]
      }
    })
  });
});
```

### Pattern 2: Partner API with Event Notification

```typescript
// Partner API (inter-tenant)
app.post('/api/v1/partner/invoice/issue', async (req, res) => {
  const contract = await validateContract(req.headers['X-Contract-ID']);

  // Create invoice in seller's tenant
  const invoice = await createInvoice(
    contract.seller_tenant_id,
    {
      ...req.body,
      buyer_tenant_id: contract.buyer_tenant_id,
      contract_id: contract.id
    }
  );

  // Publish event (buyer's event handler will consume)
  await publishEvent({
    event_type: 'Supplier.Invoice.Issued.v1',
    tenant_id: contract.buyer_tenant_id,  // Buyer's perspective
    correlation_id: generateCorrelationId(),
    payload: {
      invoice_id: invoice.id,
      buyer_tenant_id: contract.buyer_tenant_id,
      supplier_tenant_id: contract.seller_tenant_id,
      amount: invoice.amount
    }
  });

  return res.json(invoice);
});

// Buyer's event handler (async)
eventBroker.subscribe('Supplier.Invoice.Issued.v1', async (event) => {
  const { tenant_id, payload } = event;

  // Create AP invoice in buyer's system
  await createAPInvoice(tenant_id, {
    supplier_tenant_id: payload.supplier_tenant_id,
    amount: payload.amount,
    source_id: payload.invoice_id
  });

  // If >threshold, publish approval request
  if (payload.amount > 5000000) {
    await publishEvent({
      event_type: 'Approval.Requested.v1',
      tenant_id,
      payload: {
        entity_type: 'invoice',
        entity_id: payload.invoice_id,
        amount: payload.amount,
        required_role: 'admin'
      }
    });
  }
});
```

---

## Compliance Checklist

When designing API boundaries:

- [ ] API type identified (Public/Internal/Partner/Event)
- [ ] Authentication method appropriate for type
- [ ] tenant_id scoped correctly (user vs service vs contract)
- [ ] Permissions checked (role-based for public, service-based for internal)
- [ ] No internal APIs exposed to public
- [ ] Partner APIs require BusinessContract validation
- [ ] Cross-tenant access explicit and audited
- [ ] Error messages appropriate for audience (user-friendly vs technical)
- [ ] Rate limiting configured
- [ ] Timeout configured
- [ ] Audit logging configured
- [ ] API documented (OpenAPI/Swagger)
- [ ] Tests cover permission/tenant isolation scenarios

---

## Related Documents

- **ARCH-06**: Repository Governance — How repos align with API boundaries
- **ARCH-10**: Event-Driven Architecture — Event contract and integration patterns
- **SPEC-11**: Inter-Tenant Supplier Flow — Partner API flow examples
- **SEC-03**: Authorization, Approval & Audit — Permission enforcement at API level
- **STD-19**: Event Contract Standard — Event schema and versioning
- **GUIDE-05**: Frontend Tech Stack — How frontend consumes public APIs
