# API & Backend Contradictions - Visual Diagrams

## 1. Validation Layer Contradiction

```
┌─────────────────────────────────────────────────────────────────┐
│ DEVELOPMENT STANDARDS (Current)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Request → Pydantic DTO → Use Case → Repository → Database     │
│            │                                                     │
│            └── All validation here (STATIC)                     │
│                                                                 │
│  ❌ Problem: Tax rates, thresholds hardcoded in DTO            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ACCOUNTING STANDARDS (Required)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Request → Pydantic DTO ─┬→ Use Case → Repository → Database   │
│            │             │                                      │
│            │             └→ Business Rules Service              │
│            │                │                                   │
│            └── HARD RULES  └── SOFT RULES (from DB)            │
│                (immutable)     (configurable)                   │
│                                                                 │
│  ✅ Solution: Two-layer validation                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Transaction Boundary Contradiction

```
┌─────────────────────────────────────────────────────────────────┐
│ DEVELOPMENT STANDARDS (Current)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Void Journal Use Case:                                         │
│                                                                 │
│  1. Get original journal        ← No transaction wrapper       │
│  2. Create reversing entry      ← Each step separate           │
│  3. Update original status      ← Can fail here! ❌            │
│  4. Link entries                ← Partial data if exception    │
│  5. Emit event                                                  │
│                                                                 │
│  ❌ Risk: Database inconsistency if step 3 fails               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ACCOUNTING STANDARDS (Required)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Void Journal Use Case:                                         │
│                                                                 │
│  ┌─ UnitOfWork ──────────────────────────────────┐             │
│  │  1. Get original journal                      │             │
│  │  2. Create reversing entry                    │             │
│  │  3. Update original status                    │             │
│  │  4. Link entries                              │             │
│  │  ↓                                             │             │
│  │  COMMIT (all succeed) or ROLLBACK (any fail) │             │
│  └───────────────────────────────────────────────┘             │
│  5. Emit event (after commit)                                   │
│                                                                 │
│  ✅ Solution: Atomic operations with UnitOfWork                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Event Architecture Contradiction

```
┌─────────────────────────────────────────────────────────────────┐
│ DEVELOPMENT STANDARDS (Current)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Event mentioned in text:                                       │
│  "Event-driven architecture with RabbitMQ"                      │
│                                                                 │
│  ❌ But NO definition of:                                      │
│     - Event schema                                              │
│     - Event naming convention                                   │
│     - Event versioning strategy                                 │
│     - RabbitMQ implementation                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ACCOUNTING STANDARDS (Shows Usage)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PMS → Event → Accounting Service → Journal                    │
│                                                                 │
│  event = TransactionEvent(                                      │
│    source="pms",                                                │
│    type="room_charge",  ← What's the schema? ❌                │
│    data={...}           ← What format? ❌                       │
│  )                                                              │
│                                                                 │
│  ❌ No event schema = Integration will fail                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ REQUIRED SOLUTION                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Event Envelope Standard:                                       │
│  {                                                              │
│    "event_type": "pms.room_charge.posted.v1",                   │
│    "event_version": "1.0",                                      │
│    "timestamp": "2025-12-07T10:30:45Z",                         │
│    "source": {                                                  │
│      "service": "pms",                                          │
│      "instance": "pms-api-01"                                   │
│    },                                                           │
│    "payload": {                                                 │
│      "transaction_id": "12345",                                 │
│      "amount": 100                                              │
│    }                                                            │
│  }                                                              │
│                                                                 │
│  ✅ Solution: Define complete event architecture               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Journal Status Flow - Missing API Endpoints

```
┌─────────────────────────────────────────────────────────────────┐
│ ACCOUNTING STANDARDS (Business Logic Defined)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Status Flow:                                                   │
│                                                                 │
│  DRAFT ──submit──→ PENDING ──approve──→ APPROVED ──post──→ POSTED
│    ↓                  ↓                                      ↓   │
│  DELETE            REJECT                                  VOID  │
│  (soft)           (to draft)                          (reversing)│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ DEVELOPMENT STANDARDS (Only Shows)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST /api/v1/reservations/1/cancel  ← Generic example         │
│                                                                 │
│  ❌ Missing accounting-specific endpoints:                     │
│     POST /api/v1/accounting/journals/{id}/submit               │
│     POST /api/v1/accounting/journals/{id}/approve              │
│     POST /api/v1/accounting/journals/{id}/reject               │
│     POST /api/v1/accounting/journals/{id}/post                 │
│     POST /api/v1/accounting/journals/{id}/void                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ REQUIRED SOLUTION                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Complete API Specification:                                    │
│                                                                 │
│  CRUD Operations:                                               │
│  GET    /api/v1/accounting/journals                             │
│  POST   /api/v1/accounting/journals                             │
│  GET    /api/v1/accounting/journals/{id}                        │
│  PATCH  /api/v1/accounting/journals/{id}  (DRAFT only)          │
│  DELETE /api/v1/accounting/journals/{id}  (DRAFT only, soft)    │
│                                                                 │
│  Status Transitions:                                            │
│  POST /api/v1/accounting/journals/{id}/submit                   │
│  POST /api/v1/accounting/journals/{id}/approve                  │
│  POST /api/v1/accounting/journals/{id}/reject                   │
│  POST /api/v1/accounting/journals/{id}/post                     │
│  POST /api/v1/accounting/journals/{id}/void                     │
│                                                                 │
│  Integration:                                                   │
│  POST /api/v1/accounting/integration/auto-post                  │
│  GET  /api/v1/accounting/integration/failed-queue               │
│                                                                 │
│  Approvals:                                                     │
│  GET  /api/v1/accounting/approvals/pending                      │
│  GET  /api/v1/accounting/journals/{id}/approval-history         │
│                                                                 │
│  ✅ Solution: Define complete accounting API                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Integration Auto-Post Flow - Missing Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│ CURRENT: No Integration Pattern Defined                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PMS creates transaction                                        │
│     ↓                                                           │
│  ??? (How does it reach accounting?)                           │
│     ↓                                                           │
│  Accounting creates journal                                     │
│                                                                 │
│  ❌ Problems:                                                  │
│     - What if journal creation fails?                           │
│     - How to retry?                                             │
│     - How to track failures?                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ REQUIRED: Saga Pattern with Integration Queue                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ PMS Service ────────────────────────────────────────────┐  │
│  │ 1. Create room charge (transaction committed)           │  │
│  │ 2. Publish event: pms.room_charge.posted.v1             │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │                                                     │
│           ▼                                                     │
│  ┌─ RabbitMQ ──────────────────────────────────────────────┐  │
│  │ Exchange: pms.events                                     │  │
│  │ Routing: pms.room_charge.posted                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │                                                     │
│           ▼                                                     │
│  ┌─ Accounting Service ────────────────────────────────────┐  │
│  │ 1. Receive event                                         │  │
│  │ 2. Create integration queue entry (PROCESSING)           │  │
│  │ 3. Validate data                                         │  │
│  │ 4. Check auto-post rules                                 │  │
│  │ 5. Create journal entry                                  │  │
│  │    ├─ Success → Queue status: COMPLETED                  │  │
│  │    └─ Failure → Queue status: FAILED                     │  │
│  │                 Emit: integration.failed event           │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │                                                     │
│           ▼                                                     │
│  ┌─ Integration Queue Table ───────────────────────────────┐  │
│  │ id | saga_id | source | source_id | status | error      │  │
│  │ 1  | uuid1   | pms    | 12345     | COMPLETED | null    │  │
│  │ 2  | uuid2   | pms    | 12346     | FAILED    | "Tax.." │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ✅ Benefits:                                                  │
│     - Atomic operations via queue                               │
│     - Retry mechanism                                           │
│     - Failure tracking                                          │
│     - Compensating transactions                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Approval Workflow - Missing Multi-Level Logic

```
┌─────────────────────────────────────────────────────────────────┐
│ ACCOUNTING STANDARDS (Requirements)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Approval Rules:                                                │
│  - Amount < 10M    → Finance Staff (Level 1)                    │
│  - Amount 10-100M  → Finance Manager (Level 2)                  │
│  - Amount > 100M   → Finance Director (Level 3)                 │
│  - GJ/AJ journals  → Always requires approval                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ DEVELOPMENT STANDARDS                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ No approval workflow logic defined                         │
│  ❌ No multi-level approval pattern                            │
│  ❌ No approval state machine                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ REQUIRED SOLUTION                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Multi-Level Approval Flow (Amount: 50M):                       │
│                                                                 │
│  1. User submits journal (50M)                                  │
│      ↓                                                          │
│  2. System checks approval rules                                │
│      → Amount 50M = Requires Level 1 + Level 2                  │
│      ↓                                                          │
│  3. Status: PENDING_APPROVAL                                    │
│     Current Level: 1                                            │
│     Required Approver: Finance Staff                            │
│      ↓                                                          │
│  4. Finance Staff approves                                      │
│      ↓                                                          │
│  5. System checks: More approvals needed?                       │
│      → Yes, Level 2 required                                    │
│      ↓                                                          │
│  6. Status: PENDING_APPROVAL                                    │
│     Current Level: 2                                            │
│     Required Approver: Finance Manager                          │
│      ↓                                                          │
│  7. Finance Manager approves                                    │
│      ↓                                                          │
│  8. System checks: More approvals needed?                       │
│      → No, all approvals complete                               │
│      ↓                                                          │
│  9. Status: APPROVED (can now be posted)                        │
│                                                                 │
│  ✅ Implementation needed in Use Case layer                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Complete Architecture - Before vs After

```
┌─────────────────────────────────────────────────────────────────┐
│ BEFORE (Current Standards)                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Request → Pydantic DTO → Use Case → Repository → Database     │
│                                                                 │
│  ❌ Missing:                                                   │
│     - Transaction boundaries                                    │
│     - Soft rules validation                                     │
│     - Event bus integration                                     │
│     - Approval workflow                                         │
│     - Integration patterns                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ AFTER (Required for Accounting)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ API Layer ─────────────────────────────────────────────┐   │
│  │ Request validation (Pydantic - Hard Rules)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  ┌─ Use Case Layer ───────────────────────────────────────┐   │
│  │ ┌─ UnitOfWork ────────────────────────────────────┐    │   │
│  │ │ Business logic                                   │    │   │
│  │ │ Soft rules validation (Business Rules Service)  │    │   │
│  │ │ Repository operations                            │    │   │
│  │ │ COMMIT / ROLLBACK                                │    │   │
│  │ └──────────────────────────────────────────────────┘    │   │
│  │ Event publishing (after commit)                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  ┌─ Event Bus (RabbitMQ) ─────────────────────────────────┐   │
│  │ Publish domain events                                   │   │
│  │ Subscribe to integration events                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  ┌─ Event Handlers ───────────────────────────────────────┐   │
│  │ Integration auto-post                                   │   │
│  │ Approval notifications                                  │   │
│  │ Audit logging                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ✅ Complete architecture with all patterns                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

**3 Critical Architectural Gaps**:
1. **Validation**: Need 2-layer (Hard + Soft rules)
2. **Transactions**: Need UnitOfWork + Saga patterns
3. **Events**: Need complete event architecture

**8 Missing API Endpoints**:
- Journal CRUD + Status transitions
- Integration auto-post
- Approval workflows

**Fix Timeline**: 4-6 weeks before development can start safely

**Risk**: If not fixed → Integration failures, data corruption, broken workflows

---

See full report: `API_BACKEND_CONTRADICTIONS_REPORT.md`
