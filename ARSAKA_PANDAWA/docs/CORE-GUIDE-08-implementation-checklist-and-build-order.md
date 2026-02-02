# GUIDE-08: Implementation Checklist & Build Order

This document is the **execution roadmap** for building ARSAKA_PANDAWA from zero to production-ready. It defines the safe build sequence to prevent architectural mistakes and rework.

**Audience**: Development teams, AI assistants, architects planning implementation sprints.

**Critical**: Follow this sequence. Skipping phases or building in wrong order causes major rework.

---

## Build Philosophy

```
Safe Sequence:
1. Foundation (identity, tenant, auth)
2. Integration backbone (events, messaging)
3. Financial spine (accounting, GL)
4. Operational domains (PMS, Inventory)
5. Cross-domain features (supplier, reports)
6. Security hardening
7. Reporting & analytics
8. Production readiness
```

**Key Principle**: *Cannot build operational domain without accounting foundation. Cannot build features without event backbone. Cannot go to production without security hardening.*

---

## PHASE 0: Technical Preparation

**Prerequisite**: Infrastructure and process setup

- [ ] **Repository Strategy**
  - [ ] Monorepo or multi-repo decision made (see ARCH-06)
  - [ ] Folder structure aligned with domains (domain-driven)
  - [ ] Branch strategy (main, staging, develop)

- [ ] **CI/CD Pipeline**
  - [ ] Build pipeline automated
  - [ ] Test automation (unit, integration)
  - [ ] Deployment automation (dev → staging → prod)
  - [ ] Database migrations automated

- [ ] **Development Standards**
  - [ ] Code style guide agreed
  - [ ] Naming conventions (domain, entity, API)
  - [ ] Folder structure conventions
  - [ ] Git commit message format

- [ ] **Environments**
  - [ ] Development environment (local or cloud)
  - [ ] Staging environment (production-like)
  - [ ] Production environment (HA, backups)
  - [ ] Monitoring (logging, metrics, alerts)

**Validation**:
```
cd project && npm install && npm test && npm build
→ Should succeed without errors
```

---

## PHASE 1: Global Foundation (MUST BE FIRST)

**Purpose**: Build the authorization and tenant isolation foundation that ALL other features depend on.

### 1.1 User & Authentication

- [ ] User entity created
- [ ] Password hashing (bcrypt)
- [ ] Session/JWT token generation
- [ ] Login API implemented
- [ ] Logout API implemented
- [ ] Password reset flow
- [ ] Email verification (optional)

**Tests**:
```
✓ User can register with email + password
✓ Invalid password rejected
✓ Correct password grants token
✓ Token validated on protected routes
✓ Token expires correctly
```

---

### 1.2 Tenant Entity

- [ ] Tenant entity created (database table)
- [ ] Tenant creation flow (admin)
- [ ] Tenant status lifecycle (draft → active → suspended)
- [ ] Tenant name, settings, timezone, currency
- [ ] Tenant deletion (soft delete)

**Tests**:
```
✓ User can create tenant
✓ Tenant has unique name (per operator)
✓ Tenant status transitions work
✓ Cannot delete active tenant
```

---

### 1.3 Membership (Role Assignment)

- [ ] Membership entity created
- [ ] User can be invited to tenant
- [ ] Invitation acceptance flow
- [ ] Role assignment (owner, admin, staff, guest)
- [ ] Role change workflow (promotion/demotion)
- [ ] User can leave tenant
- [ ] User cannot access data without membership

**Unique Rule**:
```
User can have ONLY ONE role per tenant
If promoted: update existing membership (don't create new)
If demoted: update existing membership (don't delete)
```

**Tests**:
```
✓ User invited to tenant receives invite
✓ User accepts invite → membership created
✓ User has correct role in tenant
✓ User cannot access other tenants' data
✓ User cannot access without membership
✓ Cannot have two roles in same tenant
```

---

### 1.4 Permissions & Authorization

- [ ] Permission system designed (atomic permissions)
  - [ ] `invoice.view`, `invoice.create`, `invoice.approve`, etc.
  - [ ] Permissions tied to roles
  - [ ] Permission checking on API endpoints

- [ ] Authorization middleware
  - [ ] Checks: (1) authenticated, (2) member of tenant, (3) has permission
  - [ ] Denies access if any check fails

**Tests**:
```
✓ User can view resource only if has permission
✓ User cannot create resource without permission
✓ Admin can approve but staff cannot
✓ Owner can delete but admin cannot
```

---

### 1.5 Subscription & Feature Gating

- [ ] App entity (module registry: PMS, Accounting, Inventory, etc.)
- [ ] TenantApp subscription (tenant subscribes to app)
- [ ] Subscription status (active, inactive, expired)
- [ ] Feature gate: app features hidden if not subscribed
- [ ] Permission × Subscription check
  - [ ] User can only do action if: has permission AND app is subscribed

**Tests**:
```
✓ Unsubscribed module hidden from UI
✓ API returns 403 if module not subscribed
✓ Subscribed module accessible
✓ Permission + Subscription both required
```

---

### 1.6 Audit Log (Append-Only)

- [ ] AuditLog table created (append-only, no deletes)
- [ ] All user actions logged: who, what, when
- [ ] Log includes: entity_type, action, entity_id, actor_id, timestamp
- [ ] Database trigger prevents deletion
- [ ] Log queryable by entity, user, date range

**Tests**:
```
✓ Every API call logged
✓ Cannot delete audit log entry (database prevents)
✓ Can query logs by date range
✓ Logs show complete history
```

---

### Phase 1 Validation Checkpoint

**STOP HERE**: Validate Phase 1 before proceeding to Phase 2.

```
Critical validations:
✓ User can belong to multiple tenants
✓ Data strictly isolated by tenant
✓ No cross-tenant data visible
✓ Membership × Subscription controls access
✓ All actions audited
```

**Test Scenario**:
```
1. Create User A
2. Create Tenant X, Tenant Y
3. Add User A as Owner of Tenant X
4. Add User A as Staff of Tenant Y
5. User A logs in
6. Verify: Can access X (as owner), cannot access Y (different session)
7. Switch to Y: Can access Y (as staff), cannot see X's data
8. Verify: Audit log shows all actions
```

---

## PHASE 2: Event Backbone (INTEGRATION FOUNDATION)

**Purpose**: Build the asynchronous integration layer that all modules depend on.

### 2.1 Message Broker

- [ ] RabbitMQ deployed (or equivalent: Kafka, AWS SNS/SQS)
- [ ] Connection pooling configured
- [ ] Dead-letter queue configured
- [ ] Message persistence enabled
- [ ] Monitoring/alerting on broker health

**Configuration**:
```
Exchange: events (topic exchange)
Queue naming: {service}.{event_type}
Routing key: {domain}.{entity}.{action}.{version}
```

---

### 2.2 Event Envelope & Versioning

- [ ] Event envelope structure standardized (see STD-19)
  ```json
  {
    "event_id": "uuid",
    "event_type": "Domain.Entity.Action.vN",
    "occurred_at": "ISO-8601",
    "tenant_id": "uuid",
    "correlation_id": "uuid",
    "payload": {}
  }
  ```

- [ ] Event versioning (Domain.Entity.Action.v1, v2, etc.)
- [ ] Backward compatibility rules enforced
- [ ] JSON schema validation per event type

**Tests**:
```
✓ Event has all required fields
✓ Event_id is unique
✓ tenant_id is never null
✓ correlation_id propagated
✓ Schema validation rejects invalid events
```

---

### 2.3 Event Publishing

- [ ] Event publishing abstraction
- [ ] Idempotent publish (duplicate events detected/ignored)
- [ ] Event serialization (JSON)
- [ ] Event signed (HMAC for integrity)

**Pattern**:
```typescript
// After creating/updating data:
const event = {
  event_id: uuid(),
  event_type: 'Domain.Entity.Action.v1',
  occurred_at: now(),
  tenant_id: getTenantId(),
  correlation_id: getCorrelationId(),
  payload: { ... }
};
await eventBus.publish(event);
```

---

### 2.4 Event Consumption (Subscriber Pattern)

- [ ] Event consumer abstraction
- [ ] Idempotency handling (event_id deduplication)
- [ ] Error handling (retries, dead-letter queue)
- [ ] Consumer lag monitoring

**Pattern**:
```typescript
eventBus.subscribe('Domain.Entity.Action.v1', async (event) => {
  // Check idempotency
  if (await alreadyProcessed(event.event_id)) return;

  try {
    // Process event
    await handleEvent(event);
    // Mark processed
    await markProcessed(event.event_id);
  } catch (error) {
    // Dead-letter queue
    await deadLetterQueue.push(event);
  }
});
```

---

### 2.5 Event Registry

- [ ] Catalog of all event types
- [ ] Event schema per type
- [ ] Producers and consumers documented
- [ ] Version history

**Tests**:
```
✓ All events conform to envelope
✓ Event consumers process without error
✓ Duplicate events handled (idempotent)
✓ Event replay doesn't corrupt data
```

---

### Phase 2 Validation Checkpoint

**Test Event Flow**:
```
1. Publish event to broker
2. Consumer subscribes
3. Event delivered within 5 seconds
4. Consumer processes idempotently
5. Duplicate event ignored
6. Failed consumer: message goes to DLQ
```

---

## PHASE 3: Accounting Core (FINANCIAL SPINE)

**CRITICAL**: Do NOT skip or shortcut this phase. All other domains depend on accounting integrity.

### 3.1 Chart of Accounts

- [ ] ChartOfAccount entity created
- [ ] Hierarchical GL structure (assets, liabilities, equity, revenue, expense)
- [ ] Account codes assigned
- [ ] Standard accounts seeded per tenant

**Standard Account Structure**:
```
1000 ASSETS
  1100 Current Assets
    1110 Cash
    1120 Accounts Receivable
  1200 Fixed Assets
4000 REVENUE
  4100 Room Revenue
  4200 F&B Revenue
5000 EXPENSES
  5100 Salaries
  5200 Supplies
```

---

### 3.2 Accounting Period & Locking

- [ ] AccountingPeriod entity created
- [ ] Period creation (monthly, quarterly, annual)
- [ ] Period status: open → locked → closed
- [ ] Prevent posting to locked/closed periods
- [ ] Period closing workflow

**Tests**:
```
✓ Can post to OPEN period
✓ Cannot post to LOCKED period
✓ Cannot post to CLOSED period
✓ Period transitions correctly
```

---

### 3.3 Journal Engine (Double-Entry Accounting)

- [ ] JournalEntry entity created
- [ ] JournalLine entity created
- [ ] Double-entry validation (debit = credit)
- [ ] Source tracking (invoice, payment, adjustment)
- [ ] Immutability after posting

**Double-Entry Rule**:
```
Every entry must balance:
SUM(debit) = SUM(credit)

Example:
  JournalEntry: "Guest Checkout"
    Line 1: DR 1120 (AR)      $1,000
    Line 2: CR 4100 (Revenue) $1,000
  Balance: $1,000 = $1,000 ✓
```

**Immutability**:
```
Once posted, journal entry CANNOT be edited.
To correct: Create reversing entry (negate original).
```

**Tests**:
```
✓ Entry posts only if balanced
✓ Cannot post unbalanced entry
✓ Cannot edit entry after posting
✓ Reversal creates new entry (doesn't edit original)
✓ GL balance = SUM(entries)
```

---

### 3.4 Invoice & Payment

- [ ] Invoice entity (AR/AP)
- [ ] Invoice status workflow (draft → approved → posted → paid)
- [ ] Payment allocation to invoice
- [ ] Outstanding amount tracking
- [ ] Event publishing (Invoice.Finalized, Payment.Recorded)

**Flow**:
```
Create Invoice
  → Approval (if >threshold)
  → Finalized (event published)
  → Accounting posts GL
  → Payment received
  → Payment recorded (event published)
  → GL updated
  → Invoice marked paid
```

---

### 3.5 Approval Workflow

- [ ] ApprovalRequest entity
- [ ] Threshold-based routing (e.g., >$5K needs admin approval)
- [ ] Multiple approvers if needed
- [ ] Approval history
- [ ] Events published (Approval.Requested, Approval.Decided)

**Example Rules**:
```
Amount < $5,000        → Auto-approved
$5,000 - $50,000       → Admin approval required
$50,000+               → Owner approval required
```

---

### Phase 3 STOP Checkpoint

**CRITICAL VALIDATION**: Do NOT proceed to Phase 4 until this passes:

```
Test: Complete transaction flow
1. Create Invoice for $10,000 (requires approval)
2. Owner approves
3. Invoice.Finalized event published
4. GL posts: DR AR, CR Revenue
5. Payment $10,000 recorded
6. Payment.Recorded event published
7. GL posts: DR Cash, CR AR
8. Verify: AR balance = $0

Validation:
✓ Double-entry maintained (debit=credit)
✓ Events published correctly
✓ GL integrity preserved
✓ Approval required for thresholds
✓ Trial Balance balanced (total DR = total CR)
```

**If this fails**: STOP. Do not proceed. Accounting integrity is broken.

---

## PHASE 4: Read Model & CQRS

**Purpose**: Build efficient query layer without impacting transactional system.

### 4.1 Projection Framework

- [ ] Projection handler pattern
- [ ] Idempotent projections
- [ ] Checkpoint tracking (which events processed)
- [ ] Rebuild capability

---

### 4.2 Accounting Read Models

- [ ] AR Aging report (join Invoice + Payment)
- [ ] AP Aging report
- [ ] Trial Balance (GL account summary)
- [ ] Daily Revenue summary
- [ ] Cash Flow summary

**Pattern**:
```
Event: Invoice.Finalized
  → Projection updates ar_aging_report
  → Query: SELECT * FROM ar_aging_report (fast)
```

---

### 4.3 Rebuild & Replay

- [ ] Event replay capability (rebuild projections from events)
- [ ] Checkpoint recovery
- [ ] Testing: delete read model → rebuild from events → verify matches

---

## PHASE 5: PMS Domain

**Now safe to build**: Authorization exists, accounting is stable, events working.

- [ ] Property entity
- [ ] RoomType, Room entities
- [ ] Reservation entity
- [ ] Stay entity
- [ ] Guest entity
- [ ] Folio entity (core operational record)
- [ ] Charge, Payment entities
- [ ] Night Audit process
- [ ] Invoice request to Accounting (via event)

**Critical**:
```
❌ PMS does NOT create JournalLine
❌ PMS does NOT post GL directly
✓ PMS creates Invoice (request)
✓ Accounting consumes and posts GL
```

---

## PHASE 6: Inventory Domain

- [ ] Item entity
- [ ] Warehouse entity
- [ ] Stock entity (current quantity)
- [ ] StockMovement entity (append-only history)
- [ ] GoodsReceipt entity
- [ ] InventoryValuation (unit cost)
- [ ] COGSEntry entity
- [ ] COGS event publishing

**Critical**:
```
❌ Inventory does NOT post GL
✓ Inventory creates COGSEntry
✓ Event triggers GL posting in Accounting
```

---

## PHASE 7: Supplier & Inter-Tenant Integration

- [ ] BusinessContract entity
- [ ] Partner API (inter-tenant PO → Invoice → AP)
- [ ] Approval across tenants
- [ ] Invoice reconciliation

**Critical**:
```
✓ Contract required for cross-tenant data
✓ No direct cross-tenant DB queries
✓ Events as integration mechanism
```

---

## PHASE 8: Security Hardening

- [ ] Permission audit (every action has permission check)
- [ ] Approval rule testing (thresholds enforced)
- [ ] Fraud signals (unusual patterns detected)
- [ ] Penetration testing
- [ ] Data encryption (PII, secrets)

**Checklist**:
- [ ] Cannot bypass authentication
- [ ] Cannot access other tenant's data
- [ ] Cannot edit GL (only reversals)
- [ ] Cannot post to closed periods
- [ ] Cannot create unbalanced entries
- [ ] Password policies enforced
- [ ] Session timeout configured

---

## PHASE 9: Reporting & Dashboards

- [ ] PMS reports (occupancy, revenue)
- [ ] Accounting reports (GL, income statement)
- [ ] Cross-tenant reports (with contract validation)
- [ ] Owner dashboard (multi-property summary)
- [ ] Real-time alerts

---

## PHASE 10: Production Readiness

- [ ] Monitoring & alerting
  - [ ] Database performance
  - [ ] Event broker lag
  - [ ] Error rates

- [ ] Backup & Restore testing
  - [ ] Full backup procedure
  - [ ] Restore procedure
  - [ ] Backup tested (not just created)

- [ ] Disaster Recovery drill
  - [ ] Failover procedure documented
  - [ ] Recovery time target (RTO) defined
  - [ ] Recovery point objective (RPO) defined

- [ ] Load testing
  - [ ] Sustained load test
  - [ ] Peak load test
  - [ ] Failure recovery tested

- [ ] Documentation
  - [ ] Runbooks for common issues
  - [ ] Architecture decision log
  - [ ] API documentation
  - [ ] Database schema documented

---

## Hard Rules (NEVER Violate)

| Rule | Impact | Prevention |
|------|--------|-----------|
| **Operational domain writes GL** | Financial corruption | Code review, tests |
| **Query report to OLTP tables** | Performance impact | Use read models only |
| **Cross-tenant without contract** | Data leak | API validation |
| **Edit GL after posting** | Audit trail broken | Database immutability |
| **User specifies tenant_id** | Authorization bypass | Derive from token |
| **Feature without subscription** | Revenue loss, confusion | Feature gate tests |

---

## Common Mistakes to Avoid

❌ **Building without events first**
- Leads to tight coupling, hard to integrate later
- **Fix**: Complete Phase 2 before domain development

❌ **Accounting shortcuts**
- "We'll handle financials later"
- Costs 10x more to fix
- **Fix**: Accounting before operations (Phase 3 before Phase 5)

❌ **Skipping approval workflows**
- Turns into compliance nightmare
- **Fix**: Build approval early (Phase 3)

❌ **Direct cross-tenant queries**
- Data leaks
- **Fix**: Events + contracts only

❌ **No audit logging**
- Cannot prove what happened
- **Fix**: Log everything (Phase 1)

---

## Testing Checklist

For each phase:

- [ ] Unit tests (>80% coverage)
- [ ] Integration tests (happy path + error cases)
- [ ] Tenant isolation tests (User A can't see User B's data)
- [ ] Authorization tests (permission checks work)
- [ ] Event tests (published, consumed, idempotent)
- [ ] Financial tests (GL balances, no data loss)
- [ ] Performance tests (query < 1 sec, event < 5 sec)

---

## Related Documents

- **ARCH-06**: Repository Governance — Organizing code by domain
- **ARCH-10**: Event-Driven Architecture — Event patterns and principles
- **REF-05**: Core Concepts — Identity, tenant, membership
- **REF-08**: Entity Relationship Model — Data structure overview
- **SEC-03**: Authorization, Approval & Audit — Permission implementation
