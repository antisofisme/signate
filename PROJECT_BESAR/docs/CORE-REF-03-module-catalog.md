# REF-03: Module Catalog & Inventory

This document is the **definitive inventory of all modules** in PROJECT_BESAR. It specifies each module's role, architectural classification, subscription model, and dependencies.

**Usage**: Consult this catalog when designing new modules, planning integrations, or understanding the system architecture.

---

## Module Inventory Structure

Every module is classified by:

| Attribute | Definition |
|-----------|-----------|
| **Module Type** | Foundation / Engine / Domain / Add-on / Digital |
| **Subscription** | Mandatory / Optional / Not subscribed |
| **Standalone Tech** | Can function independently from other modules |
| **Standalone Product** | Can be sold/licensed independently |
| **Database** | Has own schema or shared |
| **Events** | Publishes and/or consumes |
| **Dependencies** | Which modules this depends on |

---

## 1. Foundation Modules (Mandatory, Non-Negotiable)

These modules are **always present** and **cannot be disabled**. They form the platform backbone.

### 1.1 Auth & Identity Management

| Attribute | Value |
|-----------|-------|
| **Role** | Global identity, authentication, session management |
| **Subscription** | Mandatory (always present) |
| **Standalone** | N/A (platform requirement) |
| **Database** | Own schema (`identity`, `users`, `sessions`, `oauth`) |
| **Events** | Publishes: `user.registered`, `user.logged_in`, `user.logged_out` |
| **Dependencies** | None |

**Responsibilities**:
- User registration and verification
- Password management and reset
- OAuth2 / OpenID Connect integration
- Session management
- MFA (multi-factor authentication)
- Audit trail of auth events

**Integrations**:
- All modules require authenticated user
- CRM uses user identity for guest profiles
- Audit Log consumes auth events
- Notification Engine sends login confirmations

---

### 1.2 Multi-Tenancy Engine

| Attribute | Value |
|-----------|-------|
| **Role** | Tenant isolation, context injection, data segregation |
| **Subscription** | Mandatory |
| **Database** | Own schema (`tenants`, `memberships`, `roles`) |
| **Events** | Publishes: `tenant.created`, `tenant.activated`, `tenant.suspended` |
| **Dependencies** | Auth & Identity (for user-tenant relationships) |

**Responsibilities**:
- Tenant creation and management
- User-to-tenant membership
- Role assignment per tenant
- Tenant context injection (ensure no cross-tenant access)
- Tenant data isolation enforcement
- Multi-tenancy configuration

**Database Tables**:
```
Tenant (tenant_id, name, status, created_at)
Membership (user_id, tenant_id, role, created_at)
TenantApp (tenant_id, app_code, subscription_status, is_enabled, subscribed_at)
  subscription_status ∈ {active, inactive, expired, cancelled}
  is_enabled ∈ {true, false}
  access = (subscription_status = 'active' AND is_enabled = true)
```

---

### 1.3 Audit Log Engine

| Attribute | Value |
|-----------|-------|
| **Role** | Immutable audit trail of all system actions |
| **Subscription** | Mandatory |
| **Database** | Own append-only schema (`audit_logs`) |
| **Events** | Consumes all events from event bus |
| **Dependencies** | Event Registry (subscribes to all events) |

**Responsibilities**:
- Capture all sensitive operations (logins, data changes, approvals)
- Immutable storage (no updates/deletes after posting)
- Timestamp and actor tracking
- Forensics and compliance reporting

**Example Audit Log Entry**:
```json
{
  "audit_id": "audit-123456",
  "timestamp": "2025-12-27T11:00:00Z",
  "actor_type": "USER",
  "actor_id": "staff-456",
  "tenant_id": "org-123",
  "action": "invoice.payment_recorded",
  "resource_type": "Invoice",
  "resource_id": "inv-001",
  "old_value": { "status": "OPEN", "paid_amount": 0 },
  "new_value": { "status": "PAID", "paid_amount": 314.60 },
  "result": "SUCCESS"
}
```

---

### 1.4 API Gateway & Versioning

| Attribute | Value |
|-----------|-------|
| **Role** | HTTP API contracts, versioning, rate limiting |
| **Subscription** | Mandatory |
| **Database** | Schema versioning metadata |
| **Events** | Publishes: `api.request`, `api.error` |
| **Dependencies** | Auth & Identity (validates tokens) |

**Responsibilities**:
- API endpoint routing
- Request/response validation
- API versioning (v1, v2, etc.)
- Rate limiting per user/IP
- CORS and security headers
- API documentation

---

### 1.5 Workflow & State Machine Engine

| Attribute | Value |
|-----------|-------|
| **Role** | Business process workflows, state transitions |
| **Subscription** | Mandatory |
| **Database** | Own schema (`workflows`, `state_machines`, `workflow_instances`) |
| **Events** | Publishes/Consumes workflow events |
| **Dependencies** | Event Registry |

**Responsibilities**:
- Define state machines for business processes
- Enforce valid state transitions
- Trigger actions on state changes
- Compensation/rollback on failure
- Workflow instance tracking

**Example Workflow**: Guest Checkout
```
States: CheckedIn → CheckingOut → Closed
Transitions:
  CheckedIn → CheckingOut (on user action "initiate checkout")
  CheckingOut → Closed (on event "payment.received")
  CheckingOut → CheckedIn (on action "cancel checkout")
```

---

### 1.6 Event Registry & Event Bus

| Attribute | Value |
|-----------|-------|
| **Role** | Event schema registry, event publishing/consuming |
| **Subscription** | Mandatory (platform backbone) |
| **Database** | Own schema (`event_schemas`, `event_log`, `subscriptions`) |
| **Events** | Publishes: `event.published`, `event.consumed` |
| **Dependencies** | None |

**Responsibilities**:
- Schema registry for all event types
- Event versioning and evolution
- Publish/subscribe mechanism
- Event persistence (immutable log)
- Dead-letter queue management
- Consumer lag tracking

**Technology**: RabbitMQ or Apache Kafka

---

### 1.7 Notification Engine

| Attribute | Value |
|-----------|-------|
| **Role** | Email, SMS, in-app notifications |
| **Subscription** | Mandatory |
| **Database** | Own schema (`notification_templates`, `sent_notifications`) |
| **Events** | Consumes: all domain events |
| **Dependencies** | Event Registry |

**Responsibilities**:
- Email delivery (via SendGrid, AWS SES)
- SMS delivery (via Twilio, AWS SNS)
- In-app notifications (via Centrifugo)
- Notification templates
- Delivery status tracking
- Unsubscribe management

**Example**: On `guest.checked_out` event, send:
- Receipt email to guest
- Thank you in-app notification
- Staff confirmation alert

---

### 1.8 Search Engine & Indexing

| Attribute | Value |
|-----------|-------|
| **Role** | Full-text search, indexing |
| **Subscription** | Mandatory |
| **Database** | Elasticsearch or similar |
| **Events** | Consumes: all data change events |
| **Dependencies** | Event Registry |

**Responsibilities**:
- Index guest data, reservations, invoices
- Full-text search across system
- Auto-sync from database changes
- Search result ranking
- Search analytics

**Indexed Entities**:
- Guests (name, email, phone)
- Reservations (guest, date, room)
- Invoices (customer, amount, date)

---

### 1.9 Import / Export Engine

| Attribute | Value |
|-----------|-------|
| **Role** | Bulk data import (CSV, Excel) and export |
| **Subscription** | Mandatory |
| **Database** | Shared (no dedicated schema) |
| **Events** | Consumes: import completion events |
| **Dependencies** | Validation & DTO (data format checking) |

**Responsibilities**:
- CSV/Excel import parsing
- Data validation against schemas
- Batch processing (async jobs)
- Error reporting and rollback
- Export to CSV/Excel
- Audit trail of imports

**Example**: Import 1000 guest records
```
1. Upload CSV
2. Validate format and data (check email format, required fields)
3. Process in background job (100 records at a time)
4. Log errors in import report
5. Notify user when complete
```

---

### 1.10 Backup & Disaster Recovery

| Attribute | Value |
|-----------|-------|
| **Role** | Backup scheduling, restore, DR testing |
| **Subscription** | Mandatory |
| **Database** | Metadata only (actual backups in Neon/S3) |
| **Events** | Publishes: `backup.completed`, `restore.completed` |
| **Dependencies** | None |

**Responsibilities**:
- Daily/hourly backup scheduling
- Point-in-time recovery
- Selective restore (specific tenant, time range)
- Backup verification
- DR testing (restore to test environment)
- Data retention policy enforcement

**See**: STD-08 Backup & Restore Standard

---

### 1.11 Observability (Logging, Tracing, Metrics)

| Attribute | Value |
|-----------|-------|
| **Role** | Centralized logging, distributed tracing, metrics |
| **Subscription** | Mandatory |
| **Database** | Elasticsearch, Prometheus, Jaeger |
| **Events** | Consumes: all events |
| **Dependencies** | Event Registry |

**Responsibilities**:
- Centralized log collection (JSON structured logs)
- Distributed tracing via trace_id/correlation_id
- Metrics collection (requests, errors, latency)
- Dashboards and alerting
- Log retention and archival

**See**: STD-17 Logging & Observability Standard

---

### 1.12 Circuit Breaker & Resilience

| Attribute | Value |
|-----------|-------|
| **Role** | Service resilience, fallback handling |
| **Subscription** | Mandatory |
| **Database** | No persistent storage |
| **Events** | Publishes: `service.degraded`, `service.recovered` |
| **Dependencies** | None |

**Responsibilities**:
- Monitor downstream service health
- Trip circuit on failure threshold
- Fallback responses
- Automatic recovery detection
- Graceful degradation

---

### 1.13 Feature Flags & Gating

| Attribute | Value |
|-----------|-------|
| **Role** | Feature toggling, A/B testing, gradual rollout |
| **Subscription** | Mandatory |
| **Database** | Own schema (`feature_flags`, `flag_values`) |
| **Events** | Publishes: `feature_flag.toggled` |
| **Dependencies** | None |

**Responsibilities**:
- Feature flag evaluation
- Per-tenant feature control
- Gradual rollout (percentage-based)
- A/B testing support
- Real-time flag updates (no deploy needed)

**Example**:
```
Flag: "new_payment_processor"
Value: ACTIVE for 10% of tenants
Action: Gradually increase to 50%, then 100%
Rollback: Flip flag to false immediately
```

---

### 1.14 Offline & Progressive Web App (PWA)

| Attribute | Value |
|-----------|-------|
| **Role** | Offline support, PWA features |
| **Subscription** | Mandatory (for web app) |
| **Database** | Local browser storage (IndexedDB) |
| **Events** | Consumes: sync events when online |
| **Dependencies** | Event Registry |

**Responsibilities**:
- Service worker for offline support
- Sync queue for offline actions
- PWA manifest
- Install-to-home-screen support
- Offline data cache strategy

---

## 2. Core Engine Services (Backend Services, No UI)

These are backend services reused by multiple modules.

### 2.1 Accounting Core Engine

| Attribute | Value |
|-----------|-------|
| **Role** | General Ledger, journal posting, period closing |
| **Subscription** | Core (can be sold independently) |
| **Standalone Tech** | Yes |
| **Standalone Product** | Yes |
| **Database** | Own schema (`ledger`, `journals`, `accounts`, `periods`) |
| **Events** | Publishes: `journal.posted`, `period.closed` / Consumes: `invoice.created`, `payment.recorded` |
| **Dependencies** | Event Registry |

**Responsibilities**:
- Chart of accounts management
- Journal entry posting (double-entry)
- Ledger maintenance (append-only)
- Period closing and lock
- Financial reporting (Trial Balance, P&L, Balance Sheet)
- Tax tracking and reporting

**See**: SPEC-10 Accounting Core Process, BIZ-01/02/03 Accounting Concepts

---

### 2.2 Payment Service

| Attribute | Value |
|-----------|-------|
| **Role** | Payment processing abstraction |
| **Subscription** | Core engine |
| **Standalone Tech** | Yes |
| **Database** | Own schema (`payment_transactions`, `payment_methods`) |
| **Events** | Publishes: `payment.recorded`, `payment.failed`, `refund.issued` |
| **Dependencies** | Accounting Core Engine (for ledger posting) |

**Responsibilities**:
- Credit card processing (Stripe, PayPal)
- Payment method tokenization
- Refund processing
- Payment status tracking
- PCI compliance handling

**Integrations**:
- PMS: Guest payments at checkout
- POS: Payment processing
- HR: Payroll payments

---

### 2.3 OCR Service (Optical Character Recognition)

| Attribute | Value |
|-----------|-------|
| **Role** | Document scanning and data extraction |
| **Subscription** | Core engine |
| **Standalone Tech** | Yes |
| **Database** | Own schema (`ocr_jobs`, `extracted_data`) |
| **Events** | Publishes: `document.scanned`, `data.extracted` / Consumes: `import.requested` |
| **Dependencies** | Event Registry |

**Responsibilities**:
- Invoice scanning (PDF → JSON)
- Receipt recognition
- Document classification
- Data extraction and validation
- OCR accuracy monitoring

---

## 3. Core Business Domain Modules (With UI)

These are subscription-based modules with user interfaces.

### 3.1 PMS (Property Management System)

| Attribute | Value |
|-----------|-------|
| **Role** | Reservations, check-in/out, folio management |
| **Subscription** | Optional (but bundled with Accounting for sale) |
| **Standalone Tech** | Yes |
| **Standalone Product** | No (must bundle with Accounting) |
| **Database** | Own schema (`reservations`, `folios`, `rooms`) |
| **Events** | Publishes: `guest.checked_in`, `guest.checked_out`, `folio.charge_posted` |
| **Dependencies** | Accounting Core (via adapter) |

**Responsibilities**:
- Reservation creation and management
- Room availability and assignment
- Guest check-in/check-out
- Folio (billing record) management
- Charge posting
- Night audit

**Modules in scope**: Reservations, Check-in/Check-out, Folio, Night Audit

**See**: SPEC-09 PMS Core Process, ARCH-04 Digital Signage (player integration)

---

### 3.2 POS (Point of Sale)

| Attribute | Value |
|-----------|-------|
| **Role** | Sales transactions, payment processing |
| **Subscription** | Optional |
| **Standalone Tech** | Yes |
| **Standalone Product** | Yes or bundled (can be sold with PMS or alone) |
| **Database** | Own schema (`sales_orders`, `items`, `payments`) |
| **Events** | Publishes: `sale.completed`, `payment.recorded` |
| **Dependencies** | Accounting Core (via adapter), Payment Service |

**Responsibilities**:
- Item/menu management
- Sales order creation
- Payment processing
- Till management
- Discount and promotion handling
- Sales reporting

**Can integrate with**:
- Inventory (track stock usage)
- PMS (charge to room)

---

### 3.3 ACC (Accounting Application)

| Attribute | Value |
|-----------|-------|
| **Role** | User interface for accounting operations |
| **Subscription** | Optional |
| **Standalone Tech** | Yes |
| **Standalone Product** | Yes |
| **Database** | Uses Accounting Core Engine database |
| **Events** | Consumes: all domain events / Publishes: manual journal entries |
| **Dependencies** | Accounting Core Engine |

**Responsibilities**:
- Accounting dashboard
- Invoice management
- Payment recording
- Journal entry creation (manual)
- Report generation
- Period closing
- Tax reporting

**Users**: Accountants, finance managers, auditors

---

### 3.4 INV (Inventory Management)

| Attribute | Value |
|-----------|-------|
| **Role** | Stock tracking, inventory movements |
| **Subscription** | Optional |
| **Standalone Tech** | Yes |
| **Standalone Product** | Yes |
| **Database** | Own schema (`inventory_items`, `stock_levels`, `movements`) |
| **Events** | Publishes: `stock.used`, `stock.received` / Consumes: `sale.completed` (from POS) |
| **Dependencies** | Event Registry |

**Responsibilities**:
- Item master data
- Stock level tracking
- Physical count
- Stock movement (in/out)
- Low stock alerts
- FIFO/LIFO costing (if needed)

**Integration with POS**: Track inventory depletion on sales

---

### 3.5 PROC (Procurement)

| Attribute | Value |
|-----------|-------|
| **Role** | Purchase orders, supplier management |
| **Subscription** | Optional |
| **Standalone Tech** | Yes |
| **Standalone Product** | Yes |
| **Database** | Own schema (`purchase_orders`, `suppliers`, `received_goods`) |
| **Events** | Publishes: `purchase_order.created`, `goods.received` |
| **Dependencies** | INV (Inventory), Accounting Core (for expense posting) |

**Responsibilities**:
- Supplier management
- Purchase order creation
- Goods receipt
- Invoice matching (3-way match)
- Expense recording

**Integration**: PO → Goods Receipt → Invoice → Payment → Accounting

---

### 3.6 HRM (Human Resources & Payroll)

| Attribute | Value |
|-----------|-------|
| **Role** | Employee management, payroll processing |
| **Subscription** | Optional |
| **Standalone Tech** | Yes |
| **Standalone Product** | Yes |
| **Database** | Own schema (`employees`, `payroll`, `attendance`) |
| **Events** | Publishes: `payroll.processed` / Consumes: attendance events |
| **Dependencies** | Accounting Core (for payroll expense posting) |

**Responsibilities**:
- Employee records
- Attendance tracking
- Payroll calculation
- Salary payment
- Tax withholding
- Benefits management

---

### 3.7-3.9 Service Add-ons (SPA, GYM, Laundry)

These are specialized modules for hotel services.

| Module | Role | Standalone Tech | Standalone Product | Depends On |
|--------|------|-----------------|-------------------|-----------|
| **SPA** | Spa treatments & bookings | Yes | Bundle with PMS | PMS, Accounting |
| **GYM** | Gym membership & billing | Yes | Bundle with PMS | PMS, Accounting |
| **LDR** (Laundry) | Laundry services tracking | Yes | Bundle with PMS | PMS, Accounting |

All publish events to Accounting for revenue recognition.

---

### 3.10-3.11 Distribution & Sales

| Module | Role | Standalone Tech | Standalone Product | Depends On |
|--------|------|-----------------|-------------------|-----------|
| **CRS** (Central Reservation System) | Multi-property bookings | Yes | Yes (if multi-property) | PMS |
| **S&C** (Sales & Content) | Sales team tools, content | Yes | Yes | PMS |

---

## 4. Cross-Module Add-Ons (Event Consumers)

These modules enhance other modules but cannot exist independently.

### 4.1 ICH (Internal Collaboration Hub)

| Attribute | Value |
|-----------|-------|
| **Role** | Chat, notes, task management across modules |
| **Subscription** | Optional add-on |
| **Standalone Tech** | No (requires at least one domain) |
| **Database** | Own schema (`conversations`, `tasks`, `notes`) |
| **Events** | Consumes: domain events / Publishes: collaboration events |
| **Dependencies** | At least one domain module (PMS, POS, etc.) |

**Features**:
- Guest-staff chat
- Internal staff notes
- Task assignments
- Notifications on actions

---

### 4.2 FDA (Fraud & Audit Intelligence)

| Attribute | Value |
|-----------|-------|
| **Role** | Fraud detection, audit intelligence |
| **Subscription** | Optional add-on |
| **Standalone Tech** | No (requires Accounting) |
| **Database** | Own schema (`fraud_alerts`, `patterns`) |
| **Events** | Consumes: all financial events |
| **Dependencies** | Accounting Core |

**Features**:
- Unusual transaction detection
- Duplicate invoice detection
- Amount anomaly detection
- Audit trail analysis
- Compliance rule checking

---

### 4.3 Advanced Notification

| Attribute | Value |
|-----------|-------|
| **Role** | Rule-based, workflow-triggered notifications |
| **Subscription** | Optional add-on |
| **Database** | Extends Notification Engine |
| **Dependencies** | Notification Engine, Workflow Engine |

**Features**:
- Custom notification rules
- Conditional notifications
- Notification scheduling
- Recipient targeting

---

### 4.4 Reporting & Analytics (BI)

| Attribute | Value |
|-----------|-------|
| **Role** | Business intelligence, analytics, dashboards |
| **Subscription** | Optional add-on |
| **Standalone Tech** | No (requires domain data) |
| **Database** | Data warehouse (read models) |
| **Events** | Consumes: all events |
| **Dependencies** | At least one domain module |

**Features**:
- Executive dashboards
- Revenue reports
- Custom reports
- Data export
- Trend analysis
- Forecasting

---

## 5. Digital & Signage Domain (Optional)

Specialized domain for digital signage and device management.

| Module | Role | Standalone | Depends On |
|--------|------|-----------|-----------|
| **Device Management** | Device provisioning, control | Yes | Infrastructure |
| **Content Management** | Content creation, CMS | Yes | Device Management |
| **Playlist & Schedule** | Content scheduling | Yes | Content Management |
| **Realtime Player** | Playback engine | Yes | Playlist, Device Management |
| **Device Monitoring** | Health, status, diagnostics | Yes | Device Management |

**See**: ARCH-04 Digital Signage Module Architecture

---

## 6. Architectural Principles (Locked)

These principles govern all modules:

### P1: Module = Bounded Context
- Each module is a self-contained business capability
- Clear boundaries (input/output)
- Minimal coupling to other modules
- Can be tested independently

### P2: Integration via Events, Not Database
- Modules communicate through events
- No direct database access between modules
- No stored procedures calling other modules
- Enables independent deployment

### P3: Accounting is Single Source of Truth
- All financial records flow through Accounting Core
- No module maintains its own ledger
- Accounting final arbiter of financial data
- Enables audit compliance

### P4: No Cross-Module Master Data
- Master data owned by single module
- Example: Guest owned by CRM, not shared with PMS
- PMS references guest via event/ID, not duplication
- Prevents inconsistency

### P5: Subscription ≠ Architecture
- Module can be disabled without breaking architecture
- Subscription is feature gating (UI/functionality)
- NOT changing database structure
- NOT enabling/disabling tables
- All code paths present, but some gated

---

## 7. Module Dependency Graph

```
Foundation (Always present)
├─ Auth & Identity
├─ Multi-Tenancy
├─ Audit Log
├─ API Gateway
├─ Workflow Engine
├─ Event Registry
├─ Notification
├─ Search
├─ Import/Export
├─ Backup/DR
├─ Observability
├─ Circuit Breaker
├─ Feature Flags
└─ PWA/Offline

Core Engines
├─ Accounting Core ← Payment Service
└─ OCR Service

Business Domains
├─ PMS → Accounting Core (via Adapter)
├─ POS → Accounting Core (via Adapter)
├─ INV
├─ PROC → INV
├─ HRM → Accounting Core
├─ SPA/GYM/LDR → PMS, Accounting
└─ CRS, S&C → PMS

Cross-Module Add-ons
├─ ICH → PMS/POS/etc
├─ FDA → Accounting
├─ Advanced Notification → Notification Engine
└─ Reporting → All modules (event consumers)

Digital Signage
├─ Device Management
├─ Content Management → Device Management
├─ Playlist & Schedule → Content Management
├─ Realtime Player → Playlist, Device Management
└─ Device Monitoring → Device Management
```

---

## 8. Subscription Combinations

### Combination A: Accounting Only
```
Selected: Accounting (ACC module)
Includes: Accounting Core, Payment Service
Use case: Tax accounting, external bookkeeping
```

### Combination B: Hotel (Default)
```
Selected: PMS + Accounting
Includes: PMS, Accounting, Payment Service, Reporting (optional)
Use case: Full hotel operations
```

### Combination C: Restaurant
```
Selected: POS + Accounting
Includes: POS, Accounting, Payment Service, Inventory (optional)
Use case: Restaurant or F&B operation
```

### Combination D: Full Enterprise
```
Selected: PMS + POS + Accounting + Inventory + HRM
Includes: All above + Procurement, CRM, Reporting
Use case: Large enterprise with multiple operations
```

---

## 9. Implementation Checklist

When adding a new module:

- [ ] Classified into one of 5 categories
- [ ] Dependencies documented
- [ ] Standalone technical vs. product decision made
- [ ] Adapter created (if operational module)
- [ ] Event contracts defined (what publishes/consumes)
- [ ] Database schema designed (or uses shared schema)
- [ ] UI/UX designed (if applicable)
- [ ] Feature gating implemented
- [ ] Tests cover all workflows
- [ ] Documentation created (module guide)
- [ ] Observability instrumented (logging, metrics)
- [ ] Security review completed

---

## References

- **ARCH-09**: Modularization Principles — Architectural principles for modules
- **ARCH-02**: Module Architecture — Internal module design patterns
- **STD-19**: Event Model — How modules communicate
- **SPEC-10**: Accounting Core Process — Accounting module operations
- **SPEC-09**: PMS Core Process — PMS module operations
- **ARCH-06**: Repository Governance — How modules align with git repositories
