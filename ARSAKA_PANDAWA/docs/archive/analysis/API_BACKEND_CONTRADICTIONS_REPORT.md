# API & Backend Architecture Contradictions Report

> Backend System Architect Analysis
>
> **Date**: 2025-12-07
> **Scope**: API Design, Validation, Transaction Handling, Event Integration, Approval Workflows
> **Documents Analyzed**:
> - DEVELOPMENT_STANDARDS.md
> - DEVELOPMENT_STANDARDS_V2.md
> - BUSINESS_ACCOUNTING_STANDARDS.md
> - BUSINESS_ACCOUNTING_STANDARDS_V2.md

---

## Executive Summary

This report identifies **CRITICAL contradictions** between development standards and business/accounting requirements that will cause **API design inconsistencies**, **validation failures**, and **transaction integrity issues** if not addressed.

### Severity Classification

| Severity | Count | Impact |
|----------|-------|--------|
| **CRITICAL** | 8 | System will fail or produce incorrect results |
| **HIGH** | 6 | Major functionality broken or inconsistent |
| **MEDIUM** | 4 | Degraded user experience or maintainability issues |

---

## 1. REST API PATTERNS CONTRADICTIONS

### 1.1 CRITICAL: Journal Entry URL Naming Inconsistency

**Development Standards (DEVELOPMENT_STANDARDS.md:237)**:
```
Resource naming: plural, kebab-case
Examples: /users, /room-types, /folio-transactions
```

**Accounting Standards (BUSINESS_ACCOUNTING_STANDARDS.md:257-299)**:
```
Journal Types:
- GJ - General Journal
- SJ - Sales Journal
- CR - Cash Receipt
- CD - Cash Disbursement
- AJ - Adjusting Journal
```

**CONTRADICTION**:
- Dev Standards say: `/folio-transactions` (kebab-case)
- Accounting has: Journal types with codes (GJ, SJ, CR, etc.)

**Missing API Design**:
```
❌ No clear endpoint structure for:
GET  /api/v1/journals                    # List all journals?
GET  /api/v1/journal-entries             # Better name?
GET  /api/v1/accounting/journals         # Nested under accounting?
GET  /api/v1/accounting/general-journals # Per type?
GET  /api/v1/accounting/sales-journals
```

**RECOMMENDATION**:
```python
# Option 1: Single resource with type filter (RECOMMENDED)
GET    /api/v1/accounting/journals?type=GJ
GET    /api/v1/accounting/journals/{id}
POST   /api/v1/accounting/journals
PATCH  /api/v1/accounting/journals/{id}
DELETE /api/v1/accounting/journals/{id}  # Soft delete for DRAFT only

# Option 2: Nested by type (if types have different DTOs)
GET    /api/v1/accounting/general-journals
GET    /api/v1/accounting/sales-journals
GET    /api/v1/accounting/cash-receipts
```

**DECISION NEEDED**: Choose Option 1 or 2 and document in DEVELOPMENT_STANDARDS.md

---

### 1.2 HIGH: Custom Action Endpoints for Status Transitions

**Development Standards (DEVELOPMENT_STANDARDS.md:253)**:
```
Custom Action: POST /{resource}/{id}/{action}
Example: POST /api/v1/reservations/1/cancel
```

**Accounting Standards (BUSINESS_ACCOUNTING_STANDARDS.md:318-337)**:
```
Status Flow: DRAFT → PENDING → APPROVED → POSTED
Actions: approve, reject, void, reverse
```

**CONTRADICTION**:
- Dev Standards show `cancel` action
- Accounting needs: `submit`, `approve`, `reject`, `post`, `void`

**MISSING API ENDPOINTS**:
```
❌ Journal status transitions not defined:

POST /api/v1/accounting/journals/{id}/submit     # DRAFT → PENDING
POST /api/v1/accounting/journals/{id}/approve    # PENDING → APPROVED
POST /api/v1/accounting/journals/{id}/reject     # PENDING → DRAFT
POST /api/v1/accounting/journals/{id}/post       # APPROVED → POSTED
POST /api/v1/accounting/journals/{id}/void       # POSTED → VOIDED (creates reversing entry)
```

**RECOMMENDATION**:
```python
# Add to DEVELOPMENT_STANDARDS.md Section 1.4:

## Accounting Module Actions

| Action | Method | URL | Request Body | Description |
|--------|--------|-----|--------------|-------------|
| Submit for Approval | POST | `/journals/{id}/submit` | `{"reason": str}` | DRAFT → PENDING |
| Approve | POST | `/journals/{id}/approve` | `{"approver_note": str}` | PENDING → APPROVED |
| Reject | POST | `/journals/{id}/reject` | `{"reason": str}` | PENDING → REJECTED |
| Post to GL | POST | `/journals/{id}/post` | `{"posting_date": date}` | APPROVED → POSTED |
| Void | POST | `/journals/{id}/void` | `{"reason": str}` | POSTED → VOIDED |
```

---

### 1.3 CRITICAL: Missing Auto-Post API Endpoint

**Accounting Standards V2 (BUSINESS_ACCOUNTING_STANDARDS_V2.md:146-183)**:
```python
"SJ": {"auto_post": true, "require_approval": false},
"PJ": {"auto_post": false, "require_approval": true},
```

**CONTRADICTION**:
- Accounting defines auto-post behavior per journal type
- NO API endpoint defined for integration auto-posting

**MISSING INTEGRATION ENDPOINT**:
```
❌ No endpoint for PMS/POS to auto-create and post journals:

POST /api/v1/accounting/integration/auto-post
Request Body:
{
  "source_module": "pms",
  "source_id": "12345",
  "transaction_type": "room_charge",
  "journal_type": "SJ",
  "entries": [
    {"account_code": "1103-001", "debit": 1680000},
    {"account_code": "4101-001-RM", "credit": 1500000},
    {"account_code": "2103-001", "credit": 180000}
  ],
  "metadata": {
    "room_number": "101",
    "guest_name": "John Smith"
  }
}

Response:
{
  "status": "posted" | "pending_approval" | "failed",
  "journal_id": 123,
  "journal_number": "SJ-2025-12-00045",
  "error": null
}
```

**RECOMMENDATION**:
Add integration-specific endpoints to DEVELOPMENT_STANDARDS.md:
```python
# Integration Auto-Post Endpoint
POST /api/v1/accounting/integration/auto-post
POST /api/v1/accounting/integration/retry/{queue_id}
GET  /api/v1/accounting/integration/failed-queue
```

---

## 2. VALIDATION LAYER CONTRADICTIONS

### 2.1 CRITICAL: Hard vs Soft Rules Validation Pattern

**Development Standards V2 (DEVELOPMENT_STANDARDS_V2.md:112-183)**:
```python
# Source of Truth: Backend Pydantic DTOs
class CreateReservationDTO(BaseModel):
    guest_id: int
    room_id: int
    arrival_date: date
    departure_date: date

    @field_validator('departure_date')
    def validate_dates(cls, v, info):
        if v <= info.data['arrival_date']:
            raise ValueError("Departure must be after arrival")
```

**Accounting Standards (BUSINESS_ACCOUNTING_STANDARDS.md:2600-2703)**:
```python
Hard Rules: Embedded in code (double-entry, immutability)
Soft Rules: Configurable via UI (tax rates, thresholds, formulas)
```

**CONTRADICTION**:
- Dev Standards: Validation in Pydantic DTOs (static)
- Accounting: Soft rules stored in database (dynamic)

**PROBLEM**:
```python
# ❌ This breaks Soft Rules pattern:
class CreateJournalDTO(BaseModel):
    tax_rate: Decimal = Field(ge=0, le=100)  # HARDCODED - Should be from DB!

    @field_validator('total_debit')
    def check_balance(cls, v, info):
        if v != info.data['total_credit']:
            raise ValueError("Debit must equal Credit")  # ✅ HARD RULE - OK
```

**RECOMMENDATION**:
Create TWO validation layers:

```python
# Layer 1: Pydantic DTO - Hard Rules Only
class CreateJournalEntryDTO(BaseModel):
    """Hard rules validation only"""
    organization_id: int
    journal_type: str
    transaction_date: date
    entries: List[JournalLineDTO]

    @field_validator('entries')
    def validate_balance(cls, v):
        """HARD RULE: Debit = Credit"""
        total_debit = sum(e.debit for e in v)
        total_credit = sum(e.credit for e in v)
        if total_debit != total_credit:
            raise ValueError("Journal must be balanced")
        return v

# Layer 2: Business Rules Service - Soft Rules
class JournalBusinessRulesValidator:
    """Soft rules validation from database"""

    def __init__(self, org_id: int):
        self.org_id = org_id
        self.rules = self._load_rules(org_id)

    async def validate_tax_rate(self, tax_type: str, rate: Decimal):
        """SOFT RULE: Tax rate from configuration"""
        configured_rate = await self._get_tax_rate(tax_type)
        if rate != configured_rate:
            raise SoftRuleViolation(f"Tax rate should be {configured_rate}%")

    async def validate_approval_threshold(self, amount: Decimal):
        """SOFT RULE: Approval threshold from configuration"""
        threshold = await self._get_approval_threshold()
        return amount >= threshold  # True = needs approval

    async def validate_auto_post(self, journal_type: str):
        """SOFT RULE: Auto-post configuration"""
        config = await self._get_auto_post_config(journal_type)
        return config.auto_post
```

**USE CASE INTEGRATION**:
```python
class CreateJournalEntryUseCase:
    async def execute(self, dto: CreateJournalEntryDTO) -> JournalEntry:
        # 1. Hard rules validated by Pydantic DTO ✅

        # 2. Load soft rules validator
        soft_rules = JournalBusinessRulesValidator(dto.organization_id)

        # 3. Validate soft rules
        needs_approval = await soft_rules.validate_approval_threshold(dto.total_amount)
        can_auto_post = await soft_rules.validate_auto_post(dto.journal_type)

        # 4. Determine status
        if can_auto_post and not needs_approval:
            status = JournalStatus.POSTED
        elif needs_approval:
            status = JournalStatus.PENDING_APPROVAL
        else:
            status = JournalStatus.DRAFT

        # 5. Create journal
        journal = await self.repo.create(dto, status=status)

        # 6. Emit event
        await self.event_bus.publish(JournalCreated(journal))

        return journal
```

**DECISION NEEDED**:
- Add `JournalBusinessRulesValidator` pattern to DEVELOPMENT_STANDARDS_V2.md
- Document Soft Rules validation architecture

---

### 2.2 HIGH: Missing Validation Response Format

**Development Standards (DEVELOPMENT_STANDARDS.md:1906-1991)**:
```python
Response Format:
{
  "success": true,
  "data": {...},
  "message": "Success"
}
```

**Accounting Standards**: No response format defined for validation errors

**CONTRADICTION**:
- Dev Standards define success/error response
- Accounting has validation errors but no response format

**RECOMMENDATION**:
```python
# Add to DEVELOPMENT_STANDARDS.md Section 6.3

## Validation Error Response Format

### Hard Rule Violations (400 - Client Error)
{
  "success": false,
  "error_code": "VALIDATION_FAILED",
  "message": "Journal validation failed",
  "details": [
    {
      "field": "entries",
      "error": "DEBIT_CREDIT_IMBALANCE",
      "message": "Total debit (100000) does not equal total credit (112000)",
      "violation_type": "HARD_RULE"
    }
  ]
}

### Soft Rule Violations (200 - Warning)
{
  "success": true,
  "data": {...},
  "warnings": [
    {
      "field": "tax_rate",
      "error": "TAX_RATE_MISMATCH",
      "message": "Tax rate 11% differs from configured rate 12%",
      "violation_type": "SOFT_RULE",
      "configured_value": 12.0,
      "provided_value": 11.0,
      "can_override": true
    }
  ]
}
```

---

## 3. TRANSACTION HANDLING CONTRADICTIONS

### 3.1 CRITICAL: Missing Transaction Boundary Pattern

**Development Standards**: Uses individual repository calls, no explicit transactions

**Accounting Standards (BUSINESS_ACCOUNTING_STANDARDS.md:390-409)**:
```python
Void Process:
1. User request void
2. Approval (if required)
3. System creates reversing entry  # ← Multi-step transaction
4. Original marked as VOIDED
5. Both entries linked
```

**CONTRADICTION**:
- Accounting requires atomic multi-step operations
- Dev Standards don't show transaction boundary management

**MISSING PATTERN**:
```python
# ❌ No transaction context manager in Dev Standards

class VoidJournalUseCase:
    async def execute(self, journal_id: int, reason: str):
        # This needs to be ATOMIC:
        # 1. Validate journal is POSTED
        # 2. Create reversing entry
        # 3. Link entries
        # 4. Update original status
        # 5. Emit event
        # All or nothing!
```

**RECOMMENDATION**:
Add transaction pattern to DEVELOPMENT_STANDARDS.md:

```python
# Transaction Context Manager Pattern

from contextlib import asynccontextmanager

class UnitOfWork:
    """Manages transaction boundaries"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._repositories = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()

    def get_repository(self, repo_class):
        """Lazy load repositories"""
        if repo_class not in self._repositories:
            self._repositories[repo_class] = repo_class(self.db)
        return self._repositories[repo_class]

# Usage in Use Case
class VoidJournalUseCase:
    async def execute(self, journal_id: int, reason: str, user_id: int):
        async with UnitOfWork(self.db) as uow:
            # All operations in single transaction
            journal_repo = uow.get_repository(JournalRepository)

            # 1. Validate
            original = await journal_repo.get_by_id(journal_id)
            if original.status != JournalStatus.POSTED:
                raise BusinessRuleViolation("Can only void POSTED journals")

            # 2. Check approval requirement
            if await self._requires_approval(original.total_amount):
                raise ApprovalRequiredError("Void requires approval")

            # 3. Create reversing entry
            reversing = await journal_repo.create_reversing(original)

            # 4. Link entries
            original.voided_by_id = reversing.id
            original.status = JournalStatus.VOIDED
            reversing.reverses_id = original.id

            # 5. Save changes
            await journal_repo.update(original)

            # 6. Emit event (after commit via event listener)
            await self.event_bus.publish(JournalVoided(
                journal_id=original.id,
                reversing_id=reversing.id,
                reason=reason,
                user_id=user_id
            ))

            # Transaction auto-commits here if no exceptions

        return reversing
```

---

### 3.2 CRITICAL: Integration Transaction Atomicity

**Accounting Standards V2 (BUSINESS_ACCOUNTING_STANDARDS_V2.md:36-78)**:
```python
PMS Transaction → Accounting Service → Journal Entry
# Event-driven pattern shown
```

**CONTRADICTION**:
- Integration creates journal from external transaction
- What happens if journal creation fails?
- No compensating transaction pattern defined

**PROBLEM SCENARIO**:
```
PMS creates room charge → Event published → Accounting creates journal → FAILS
❌ PMS transaction committed, Accounting failed - DATA INCONSISTENCY!
```

**RECOMMENDATION**:
Implement **Saga Pattern** with compensating transactions:

```python
# Saga Orchestrator Pattern

class IntegrationSagaOrchestrator:
    """Coordinates distributed transaction across services"""

    async def execute_pms_charge_to_journal(
        self,
        pms_transaction_id: str,
        charge_data: dict
    ):
        saga_id = uuid4()

        try:
            # Step 1: Reserve in integration queue
            queue_entry = await self._create_queue_entry(
                saga_id=saga_id,
                source="pms",
                source_id=pms_transaction_id,
                data=charge_data,
                status="PROCESSING"
            )

            # Step 2: Create journal entry
            journal = await self._create_journal(charge_data)

            # Step 3: Update queue entry
            queue_entry.status = "COMPLETED"
            queue_entry.journal_id = journal.id
            await self._update_queue_entry(queue_entry)

            # Step 4: Emit success event
            await self.event_bus.publish(IntegrationSucceeded(
                saga_id=saga_id,
                journal_id=journal.id
            ))

        except Exception as e:
            # Compensating transaction
            await self._handle_failure(
                saga_id=saga_id,
                queue_entry=queue_entry,
                error=e
            )
            raise

    async def _handle_failure(self, saga_id, queue_entry, error):
        """Compensating transaction"""
        # Mark queue entry as failed
        queue_entry.status = "FAILED"
        queue_entry.error_message = str(error)
        queue_entry.retry_count += 1
        await self._update_queue_entry(queue_entry)

        # Emit failure event (PMS can decide to rollback or retry)
        await self.event_bus.publish(IntegrationFailed(
            saga_id=saga_id,
            source_id=queue_entry.source_id,
            error=str(error),
            can_retry=queue_entry.retry_count < 3
        ))
```

**DECISION NEEDED**:
- Add Saga Pattern to DEVELOPMENT_STANDARDS.md
- Define compensating transaction rules

---

## 4. EVENT-DRIVEN INTEGRATION CONTRADICTIONS

### 4.1 CRITICAL: Event Schema Not Defined

**Accounting Standards V2 (BUSINESS_ACCOUNTING_STANDARDS_V2.md:50-77)**:
```python
# Source module publishes event
event = TransactionEvent(
    source="pms",
    type="room_charge",
    transaction_id=12345,
    data={...}
)
```

**STANDARDS_AUDIT_REPORT.md (line 360)**:
```
Event Schema Standard - CRITICAL MISSING
- Event naming
- Payload format
- Versioning
```

**CONTRADICTION**:
- Accounting shows event usage
- NO event schema standard defined
- NO event versioning strategy

**RECOMMENDATION**:
Create event schema standard:

```python
# Add to DEVELOPMENT_STANDARDS.md - New Section: Event Architecture

## Event Schema Standard

### Event Naming Convention
Format: `{domain}.{entity}.{action}.{version}`

Examples:
- `accounting.journal.created.v1`
- `pms.room_charge.posted.v1`
- `inventory.stock.adjusted.v1`

### Event Envelope Structure
{
  "event_id": "uuid",
  "event_type": "accounting.journal.created.v1",
  "event_version": "1.0",
  "timestamp": "2025-12-07T10:30:45.123Z",
  "source": {
    "service": "pms",
    "instance": "pms-api-01",
    "trace_id": "abc123"
  },
  "metadata": {
    "correlation_id": "xyz789",
    "causation_id": "previous-event-id",
    "user_id": 42,
    "organization_id": 1
  },
  "payload": {
    # Domain-specific data
  }
}

### Event Payload Schemas

#### accounting.journal.created.v1
{
  "journal_id": 123,
  "journal_number": "SJ-2025-12-00045",
  "journal_type": "SJ",
  "status": "posted",
  "total_debit": 1680000,
  "total_credit": 1680000,
  "entries": [
    {
      "account_code": "1103-001",
      "debit": 1680000,
      "credit": 0
    }
  ],
  "source_reference": {
    "module": "pms",
    "transaction_id": "12345"
  }
}

#### pms.room_charge.posted.v1
{
  "transaction_id": "12345",
  "room_number": "101",
  "guest_name": "John Smith",
  "charge_amount": 1500000,
  "tax_amount": 180000,
  "total_amount": 1680000,
  "department": "RM",
  "posting_date": "2025-12-07"
}

### Event Versioning Strategy

1. **Schema Evolution Rules**:
   - Add new optional fields: BACKWARD COMPATIBLE ✅
   - Add new required fields: BREAKING CHANGE ❌ → Bump version
   - Remove fields: BREAKING CHANGE ❌ → Bump version
   - Rename fields: BREAKING CHANGE ❌ → Bump version

2. **Version Support Policy**:
   - Current version (v1): Fully supported
   - Previous version (v0): Deprecated, 6-month support
   - Old versions: Unsupported

3. **Migration Path**:
   ```python
   # Publish both versions during transition
   await event_bus.publish(RoomChargePostedV1(...))  # New consumers
   await event_bus.publish(RoomChargePostedV0(...))  # Legacy consumers
   ```
```

---

### 4.2 HIGH: RabbitMQ Event Bus Not Implemented

**STANDARDS_AUDIT_REPORT.md (line 91-95)**:
```
Event-Driven Architecture - RESOLVED
- Message Broker: RabbitMQ (NOT Redis)
- Celery + RabbitMQ defined
```

**Development Standards**: NO RabbitMQ implementation guide

**RECOMMENDATION**:
Add RabbitMQ event bus implementation:

```python
# Add to DEVELOPMENT_STANDARDS.md - Event Architecture Section

## RabbitMQ Event Bus Implementation

### Exchange Configuration
```python
import aio_pika

class RabbitMQEventBus:
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.connection_url)
        self.channel = await self.connection.channel()

        # Declare exchanges
        await self.channel.declare_exchange(
            "accounting.events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        await self.channel.declare_exchange(
            "pms.events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

    async def publish(self, event: DomainEvent):
        """Publish event to appropriate exchange"""
        exchange_name = f"{event.domain}.events"
        routing_key = f"{event.domain}.{event.entity}.{event.action}"

        message = aio_pika.Message(
            body=event.to_json().encode(),
            content_type="application/json",
            headers={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "event_version": event.event_version,
                "timestamp": event.timestamp.isoformat()
            },
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        exchange = await self.channel.get_exchange(exchange_name)
        await exchange.publish(message, routing_key=routing_key)

    async def subscribe(
        self,
        exchange: str,
        routing_key: str,
        handler: Callable
    ):
        """Subscribe to events"""
        queue_name = f"{handler.__module__}.{handler.__name__}"

        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": f"{exchange}.dlx",
                "x-message-ttl": 86400000  # 24 hours
            }
        )

        exchange_obj = await self.channel.get_exchange(exchange)
        await queue.bind(exchange_obj, routing_key=routing_key)

        await queue.consume(self._make_handler(handler))

    def _make_handler(self, handler: Callable):
        async def wrapper(message: aio_pika.IncomingMessage):
            async with message.process():
                event_data = json.loads(message.body.decode())
                await handler(event_data)
        return wrapper

# Usage
event_bus = RabbitMQEventBus("amqp://guest:guest@localhost:5672")
await event_bus.connect()

# Publisher
await event_bus.publish(JournalCreated(...))

# Subscriber
async def handle_journal_created(event):
    print(f"Journal created: {event['journal_id']}")

await event_bus.subscribe(
    "accounting.events",
    "accounting.journal.created",
    handle_journal_created
)
```

---

## 5. APPROVAL WORKFLOW CONTRADICTIONS

### 5.1 CRITICAL: Approval API Endpoints Missing

**Accounting Standards (BUSINESS_ACCOUNTING_STANDARDS.md:339-364)**:
```
Approval Workflow:
- ALL journals < 10M → Finance Staff
- 10-100M → Finance Manager
- > 100M → Finance Director
- GJ, AJ → Always requires approval
```

**Development Standards**: No approval workflow endpoints defined

**RECOMMENDATION**:
```python
# Add to DEVELOPMENT_STANDARDS.md Section 1.4

## Approval Workflow Endpoints

### Get Pending Approvals
GET /api/v1/accounting/approvals/pending
Query Params:
  - approver_id: int (optional, defaults to current user)
  - journal_type: str (optional)
  - min_amount: decimal (optional)

Response:
{
  "success": true,
  "data": {
    "items": [
      {
        "journal_id": 123,
        "journal_number": "GJ-2025-12-00001",
        "journal_type": "GJ",
        "total_amount": 50000000,
        "submitted_by": "john.doe",
        "submitted_at": "2025-12-07T10:30:00Z",
        "approval_level": 1,
        "current_approver_role": "Finance Manager"
      }
    ],
    "total": 5,
    "pending_my_action": 3
  }
}

### Approve Journal
POST /api/v1/accounting/journals/{id}/approve
Request Body:
{
  "approver_note": "Approved - looks good",
  "approved_amount": 50000000  # Confirm amount
}

Response:
{
  "success": true,
  "data": {
    "journal_id": 123,
    "status": "approved",  # or "pending_approval" if multi-level
    "next_approver": null,  # or role name if multi-level
    "can_post": true
  }
}

### Reject Journal
POST /api/v1/accounting/journals/{id}/reject
Request Body:
{
  "reason": "Missing supporting documents",
  "return_to_draft": true
}

Response:
{
  "success": true,
  "data": {
    "journal_id": 123,
    "status": "rejected",
    "can_edit": true
  }
}

### Get Approval History
GET /api/v1/accounting/journals/{id}/approval-history

Response:
{
  "success": true,
  "data": {
    "approvals": [
      {
        "level": 1,
        "approver_name": "Jane Smith",
        "approver_role": "Finance Staff",
        "action": "approved",
        "note": "Looks good",
        "approved_at": "2025-12-07T11:00:00Z"
      },
      {
        "level": 2,
        "approver_name": "John Manager",
        "approver_role": "Finance Manager",
        "action": "pending",
        "note": null,
        "approved_at": null
      }
    ]
  }
}
```

---

### 5.2 HIGH: Multi-Level Approval Logic Missing

**Accounting Standards (BUSINESS_ACCOUNTING_STANDARDS.md:344-353)**:
```sql
journal_approval_rules (
    approval_order,        -- Level (1, 2, 3)
    approver_role_id
)
```

**CONTRADICTION**:
- Database schema supports multi-level approval
- No business logic defined for approval flow

**RECOMMENDATION**:
```python
# Add to DEVELOPMENT_STANDARDS.md - Business Logic Section

## Multi-Level Approval Use Case

class ApproveJournalUseCase:
    async def execute(
        self,
        journal_id: int,
        approver_id: int,
        note: str
    ) -> ApprovalResult:
        async with UnitOfWork(self.db) as uow:
            journal_repo = uow.get_repository(JournalRepository)
            approval_repo = uow.get_repository(ApprovalRepository)

            # 1. Get journal
            journal = await journal_repo.get_by_id(journal_id)
            if journal.status != JournalStatus.PENDING_APPROVAL:
                raise InvalidStatusError("Journal not pending approval")

            # 2. Get approval rules
            rules = await self._get_approval_rules(
                journal.organization_id,
                journal.journal_type,
                journal.total_amount
            )

            # 3. Get current approval level
            current_level = await approval_repo.get_current_level(journal_id)

            # 4. Validate approver
            required_role = rules[current_level].approver_role_id
            approver = await self.user_repo.get_by_id(approver_id)
            if approver.role_id != required_role:
                raise UnauthorizedError(
                    f"Requires {required_role} role to approve"
                )

            # 5. Record approval
            await approval_repo.create(
                journal_id=journal_id,
                level=current_level,
                approver_id=approver_id,
                note=note,
                approved_at=datetime.now()
            )

            # 6. Check if more approvals needed
            if current_level < len(rules):
                # More approvals needed
                journal.status = JournalStatus.PENDING_APPROVAL
                next_level = current_level + 1
                next_approver = rules[next_level].approver_role_id
                result = ApprovalResult(
                    status="pending_next_level",
                    next_level=next_level,
                    next_approver=next_approver
                )
            else:
                # All approvals completed
                journal.status = JournalStatus.APPROVED
                result = ApprovalResult(
                    status="approved",
                    can_post=True
                )

            await journal_repo.update(journal)

            # 7. Emit event
            await self.event_bus.publish(JournalApproved(
                journal_id=journal_id,
                level=current_level,
                approver_id=approver_id,
                final_approval=result.status == "approved"
            ))

            return result
```

---

## 6. AUTO-POST LOGIC CONTRADICTIONS

### 6.1 CRITICAL: Auto-Post vs Manual Entry Business Logic

**Accounting Standards V2 (BUSINESS_ACCOUNTING_STANDARDS_V2.md:146-163)**:
```json
"SJ": {"auto_post": true, "require_approval": false},
"PJ": {"auto_post": false, "require_approval": true},
```

**CONTRADICTION**:
- Integration journals can auto-post
- Manual journals always need approval?
- NO clear business rules

**RECOMMENDATION**:
Define clear auto-post rules:

```python
# Add to BUSINESS_ACCOUNTING_STANDARDS.md - Section 10.5

## Auto-Post Business Rules

### Rule Matrix

| Journal Type | Source | Auto-Post | Approval Required | Reason |
|--------------|--------|-----------|-------------------|--------|
| SJ | Integration | ✅ | ❌ | Sales are validated in source system |
| SJ | Manual | ❌ | ✅ | Manual entries need review |
| PJ | Integration | ❌ | ✅ | Purchases need approval |
| PJ | Manual | ❌ | ✅ | Purchases always need approval |
| CR | Integration | ✅ | ❌ | Payments are validated in source |
| CR | Manual | ❌ | ✅ | Manual receipts need review |
| GJ | Any | ❌ | ✅ | Adjustments always need approval |
| AJ | Any | ❌ | ✅ | Adjustments always need approval |

### Business Logic Implementation

```python
class DetermineJournalStatusUseCase:
    async def execute(
        self,
        journal_type: str,
        source: str,  # 'integration' or 'manual'
        total_amount: Decimal,
        organization_id: int
    ) -> JournalStatus:
        # 1. Get auto-post configuration
        config = await self._get_auto_post_config(
            organization_id,
            journal_type
        )

        # 2. Check if manual entry
        if source == 'manual':
            # Manual entries never auto-post
            return JournalStatus.DRAFT

        # 3. Check journal type rules
        if journal_type in ['GJ', 'AJ']:
            # Adjustments always need approval
            return JournalStatus.PENDING_APPROVAL

        # 4. Check auto-post configuration
        if not config.auto_post:
            return JournalStatus.DRAFT

        # 5. Check approval threshold
        if config.require_approval:
            threshold = await self._get_approval_threshold(organization_id)
            if total_amount >= threshold:
                return JournalStatus.PENDING_APPROVAL

        # 6. Can auto-post
        return JournalStatus.POSTED
```

---

### 6.2 MEDIUM: Validation Before Auto-Post

**PROBLEM**:
- Auto-post journals skip manual review
- Need extra validation to prevent errors

**RECOMMENDATION**:
```python
# Add to BUSINESS_ACCOUNTING_STANDARDS_V2.md - Section 10.6

## Auto-Post Validation Rules

### Pre-Post Validation Checklist

class AutoPostValidator:
    """Extra validation for auto-posted journals"""

    async def validate(self, journal: JournalEntry):
        """Run comprehensive validation before auto-post"""
        errors = []

        # 1. Account existence
        for entry in journal.entries:
            account = await self.account_repo.get_by_code(entry.account_code)
            if not account:
                errors.append(f"Account {entry.account_code} not found")
            if not account.is_active:
                errors.append(f"Account {entry.account_code} is inactive")

        # 2. Period open
        period = await self.period_repo.get_by_date(journal.transaction_date)
        if period.status not in [PeriodStatus.OPEN]:
            errors.append(f"Period {period.name} is {period.status}")

        # 3. Department valid
        if journal.department_code:
            dept = await self.dept_repo.get_by_code(journal.department_code)
            if not dept or not dept.is_active:
                errors.append(f"Invalid department {journal.department_code}")

        # 4. Tax rates match configuration
        for entry in journal.entries:
            if entry.tax_type:
                configured_rate = await self._get_tax_rate(entry.tax_type)
                if entry.tax_rate != configured_rate:
                    errors.append(
                        f"Tax rate {entry.tax_rate} != configured {configured_rate}"
                    )

        # 5. Source reference exists
        if journal.source_module:
            source_exists = await self._verify_source_transaction(
                journal.source_module,
                journal.source_id
            )
            if not source_exists:
                errors.append(
                    f"Source transaction {journal.source_module}:{journal.source_id} not found"
                )

        if errors:
            raise AutoPostValidationError(errors)

        return True
```

---

## 7. SUMMARY OF REQUIRED FIXES

### CRITICAL (Must Fix Before Development)

| # | Issue | Location | Action Required |
|---|-------|----------|-----------------|
| 1 | Journal Entry URL Pattern | DEV_STANDARDS.md | Define `/api/v1/accounting/journals` endpoints |
| 2 | Status Transition Endpoints | DEV_STANDARDS.md | Add submit/approve/reject/post/void endpoints |
| 3 | Auto-Post Integration Endpoint | DEV_STANDARDS.md | Add `/accounting/integration/auto-post` |
| 4 | Hard vs Soft Rules Validation | DEV_STANDARDS_V2.md | Add 2-layer validation pattern |
| 5 | Transaction Boundary Pattern | DEV_STANDARDS.md | Add UnitOfWork pattern |
| 6 | Integration Transaction Atomicity | DEV_STANDARDS.md | Add Saga pattern |
| 7 | Event Schema Standard | DEV_STANDARDS.md | Define event naming and versioning |
| 8 | Approval API Endpoints | DEV_STANDARDS.md | Add approval workflow endpoints |

### HIGH (Fix in Phase 1)

| # | Issue | Location | Action Required |
|---|-------|----------|-----------------|
| 9 | Validation Response Format | DEV_STANDARDS.md | Add hard/soft rule violation formats |
| 10 | RabbitMQ Event Bus Implementation | DEV_STANDARDS.md | Add event bus code examples |
| 11 | Multi-Level Approval Logic | DEV_STANDARDS.md | Add approval use case |
| 12 | Auto-Post Business Rules | ACCOUNTING_STANDARDS.md | Define auto-post rule matrix |
| 13 | Auto-Post Validation | ACCOUNTING_STANDARDS.md | Add pre-post validation |
| 14 | DTO Naming for Accounting | DEV_STANDARDS.md | Add accounting-specific DTOs |

### MEDIUM (Fix in Phase 2)

| # | Issue | Location | Action Required |
|---|-------|----------|-----------------|
| 15 | Integration Queue Error Handling | ACCOUNTING_STANDARDS.md | Add retry/DLQ patterns |
| 16 | Event Versioning Migration | DEV_STANDARDS.md | Add version migration guide |
| 17 | Saga Compensating Transactions | DEV_STANDARDS.md | Document rollback patterns |
| 18 | Approval Notification Events | DEV_STANDARDS.md | Add notification events |

---

## 8. IMPLEMENTATION ROADMAP

### Week 1: API Design Finalization
- [ ] Define all accounting module endpoints
- [ ] Create OpenAPI specification
- [ ] Review and approve URL patterns
- [ ] Document status transition flows

### Week 2: Validation Architecture
- [ ] Implement 2-layer validation pattern
- [ ] Create JournalBusinessRulesValidator
- [ ] Add validation response formats
- [ ] Write validation tests

### Week 3: Transaction Handling
- [ ] Implement UnitOfWork pattern
- [ ] Add Saga orchestrator
- [ ] Create compensating transaction logic
- [ ] Test atomic operations

### Week 4: Event Architecture
- [ ] Define event schemas
- [ ] Implement RabbitMQ event bus
- [ ] Add event versioning
- [ ] Create event handlers

### Week 5: Approval Workflows
- [ ] Implement approval endpoints
- [ ] Add multi-level approval logic
- [ ] Create approval notifications
- [ ] Test approval flows

### Week 6: Integration & Testing
- [ ] Implement auto-post logic
- [ ] Add integration validation
- [ ] End-to-end testing
- [ ] Documentation finalization

---

## 9. DECISION LOG

### Decisions Needed

| # | Decision | Options | Recommended | Owner |
|---|----------|---------|-------------|-------|
| 1 | Journal Entry URL Structure | Option 1 (single resource) vs Option 2 (per-type) | Option 1 | Backend Architect |
| 2 | Validation Layer Pattern | Single layer vs Two layers | Two layers (Hard + Soft) | Backend Architect |
| 3 | Transaction Pattern | Manual vs UnitOfWork | UnitOfWork | Backend Architect |
| 4 | Integration Pattern | Direct call vs Saga | Saga with queue | Backend Architect |
| 5 | Event Versioning | Major.Minor vs Separate events | Major.Minor | Backend Architect |
| 6 | Auto-Post Rules | Source-based vs Amount-based | Combined (Source + Amount + Type) | Business Analyst |

### Approved Decisions

| # | Decision | Outcome | Date |
|---|----------|---------|------|
| - | - | - | - |

---

## 10. REFERENCES

### Documents
- DEVELOPMENT_STANDARDS.md
- DEVELOPMENT_STANDARDS_V2.md
- BUSINESS_ACCOUNTING_STANDARDS.md
- BUSINESS_ACCOUNTING_STANDARDS_V2.md
- STANDARDS_AUDIT_REPORT.md
- PMS_ARCHITECTURE_WEAKNESSES_REPORT.md

### Patterns Referenced
- Unit of Work Pattern
- Saga Pattern
- Event-Driven Architecture
- Domain Events
- Repository Pattern
- Business Rules Engine

---

**End of Report**

Generated by: Backend System Architect
Date: 2025-12-07
Version: 1.0
