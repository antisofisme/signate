# API & Backend Contradictions - Action Checklist

> Actionable checklist to fix contradictions before development starts

**Report**: API_BACKEND_CONTRADICTIONS_REPORT.md
**Date**: 2025-12-07
**Owner**: Backend Architect + Business Analyst

---

## Phase 1: CRITICAL FIXES (Week 1-2)

### 1.1 Define Event Architecture

**Owner**: Backend Architect
**Deadline**: Week 1
**Document**: DEVELOPMENT_STANDARDS.md - New Section 8

- [ ] Event naming convention: `{domain}.{entity}.{action}.{version}`
- [ ] Event envelope structure (event_type, timestamp, payload)
- [ ] Event versioning strategy (v1, v2, migration path)
- [ ] Event payload schemas for:
  - [ ] `accounting.journal.created.v1`
  - [ ] `accounting.journal.posted.v1`
  - [ ] `accounting.journal.voided.v1`
  - [ ] `pms.room_charge.posted.v1`
  - [ ] `pms.payment.received.v1`
  - [ ] `pos.sale.completed.v1`
- [ ] Event schema validation rules
- [ ] Backward compatibility rules
- [ ] Breaking change policy

**Deliverable**: Complete event architecture section in Dev Standards

---

### 1.2 Add Transaction Boundary Patterns

**Owner**: Backend Architect
**Deadline**: Week 1
**Document**: DEVELOPMENT_STANDARDS.md - Section 5.X

- [ ] UnitOfWork pattern implementation
  - [ ] Context manager (`async with UnitOfWork(db)`)
  - [ ] Commit/Rollback logic
  - [ ] Repository access within UoW
- [ ] Saga pattern for distributed transactions
  - [ ] Saga orchestrator class
  - [ ] Compensating transaction logic
  - [ ] Integration queue pattern
- [ ] Code examples:
  - [ ] Void journal use case with UoW
  - [ ] Integration auto-post with Saga
  - [ ] Multi-step transaction example
- [ ] Error handling in transactions
- [ ] Optimistic locking pattern

**Deliverable**: Transaction patterns documented with code examples

---

### 1.3 Implement 2-Layer Validation

**Owner**: Backend Architect
**Deadline**: Week 1-2
**Document**: DEVELOPMENT_STANDARDS_V2.md - Section 8.3

- [ ] Hard rules validation layer (Pydantic DTOs)
  - [ ] Format validation
  - [ ] Type validation
  - [ ] Required fields
  - [ ] Data integrity rules (debit=credit)
- [ ] Soft rules validation layer (Business Rules Service)
  - [ ] `JournalBusinessRulesValidator` class
  - [ ] Tax rate validation from config
  - [ ] Approval threshold from config
  - [ ] Auto-post rules from config
  - [ ] Formula evaluation
- [ ] Integration in Use Cases
  - [ ] Load soft rules validator
  - [ ] Validate hard rules (automatic in Pydantic)
  - [ ] Validate soft rules (explicit call)
  - [ ] Differentiate hard vs soft rule errors
- [ ] Response formats:
  - [ ] Hard rule violations (400 error)
  - [ ] Soft rule violations (200 with warnings)

**Deliverable**: 2-layer validation pattern with examples

---

### 1.4 Define Accounting API Endpoints

**Owner**: Backend Architect
**Deadline**: Week 1
**Document**: DEVELOPMENT_STANDARDS.md - Section 1.4 (extend)

- [ ] Journal CRUD Endpoints
  - [ ] `GET /api/v1/accounting/journals`
  - [ ] `POST /api/v1/accounting/journals`
  - [ ] `GET /api/v1/accounting/journals/{id}`
  - [ ] `PATCH /api/v1/accounting/journals/{id}` (DRAFT only)
  - [ ] `DELETE /api/v1/accounting/journals/{id}` (DRAFT only, soft)
- [ ] Status Transition Endpoints
  - [ ] `POST /api/v1/accounting/journals/{id}/submit`
  - [ ] `POST /api/v1/accounting/journals/{id}/approve`
  - [ ] `POST /api/v1/accounting/journals/{id}/reject`
  - [ ] `POST /api/v1/accounting/journals/{id}/post`
  - [ ] `POST /api/v1/accounting/journals/{id}/void`
- [ ] Integration Endpoints
  - [ ] `POST /api/v1/accounting/integration/auto-post`
  - [ ] `GET /api/v1/accounting/integration/failed-queue`
  - [ ] `POST /api/v1/accounting/integration/retry/{queue_id}`
- [ ] Approval Endpoints
  - [ ] `GET /api/v1/accounting/approvals/pending`
  - [ ] `GET /api/v1/accounting/journals/{id}/approval-history`
- [ ] Request/Response DTOs for each endpoint
- [ ] Error response formats

**Deliverable**: Complete accounting API specification

---

## Phase 2: HIGH PRIORITY (Week 2-3)

### 2.1 RabbitMQ Event Bus Implementation

**Owner**: Backend Architect
**Deadline**: Week 2
**Document**: DEVELOPMENT_STANDARDS.md - Section 8.1

- [ ] RabbitMQ connection setup
- [ ] Exchange configuration
  - [ ] `accounting.events` (TOPIC exchange)
  - [ ] `pms.events` (TOPIC exchange)
  - [ ] `pos.events` (TOPIC exchange)
- [ ] `RabbitMQEventBus` class implementation
  - [ ] `publish()` method
  - [ ] `subscribe()` method
  - [ ] Error handling
  - [ ] Retry logic
- [ ] Dead Letter Queue (DLQ) configuration
- [ ] Event persistence strategy
- [ ] Consumer group pattern
- [ ] Code examples:
  - [ ] Publishing events
  - [ ] Subscribing to events
  - [ ] Error scenarios

**Deliverable**: Complete RabbitMQ implementation guide

---

### 2.2 Approval Workflow Logic

**Owner**: Backend Architect + Business Analyst
**Deadline**: Week 2
**Document**: DEVELOPMENT_STANDARDS.md - Section 9.X (new)

- [ ] Multi-level approval state machine
  - [ ] DRAFT → PENDING_L1 → PENDING_L2 → APPROVED
  - [ ] Rejection flows
- [ ] `ApproveJournalUseCase` implementation
  - [ ] Get approval rules
  - [ ] Validate approver role
  - [ ] Check approval level
  - [ ] Record approval
  - [ ] Determine next level
  - [ ] Update journal status
- [ ] Approval notification events
  - [ ] `ApprovalRequested`
  - [ ] `ApprovalCompleted`
  - [ ] `ApprovalRejected`
  - [ ] `ApprovalEscalated`
- [ ] Approval history tracking
- [ ] Permission checks per approval level

**Deliverable**: Complete approval workflow implementation

---

### 2.3 Auto-Post Rules Matrix

**Owner**: Business Analyst
**Deadline**: Week 2
**Document**: BUSINESS_ACCOUNTING_STANDARDS.md - Section 10.5 (extend)

- [ ] Define auto-post rules for each journal type
  - [ ] SJ (Sales Journal)
  - [ ] PJ (Purchase Journal)
  - [ ] CR (Cash Receipt)
  - [ ] CD (Cash Disbursement)
  - [ ] PY (Payroll Journal)
  - [ ] IV (Inventory Journal)
  - [ ] GJ (General Journal)
  - [ ] AJ (Adjusting Journal)
- [ ] Source-based rules (integration vs manual)
- [ ] Amount-based thresholds
- [ ] Approval requirement matrix
- [ ] `DetermineJournalStatusUseCase` logic
- [ ] Configuration UI mockups

**Deliverable**: Complete auto-post decision matrix

---

### 2.4 Pre-Post Validation

**Owner**: Backend Architect
**Deadline**: Week 3
**Document**: BUSINESS_ACCOUNTING_STANDARDS_V2.md - Section 10.6 (extend)

- [ ] `AutoPostValidator` class
- [ ] Validation checklist:
  - [ ] Account existence and status
  - [ ] Period open/closed check
  - [ ] Department validity
  - [ ] Tax rate configuration match
  - [ ] Source transaction verification
  - [ ] Balance validation
- [ ] Validation error handling
- [ ] Queue entry for failed validations
- [ ] Retry mechanism
- [ ] Manual override process

**Deliverable**: Auto-post validation logic

---

## Phase 3: MEDIUM PRIORITY (Week 3-4)

### 3.1 Integration Queue Pattern

**Owner**: Backend Architect
**Deadline**: Week 3
**Document**: DEVELOPMENT_STANDARDS.md - Section 10.X (new)

- [ ] Integration queue table design
- [ ] Queue status flow (PENDING → PROCESSING → COMPLETED/FAILED)
- [ ] Saga orchestrator implementation
- [ ] Retry logic with exponential backoff
- [ ] DLQ (Dead Letter Queue) handling
- [ ] Manual intervention UI
- [ ] Queue monitoring dashboard

**Deliverable**: Integration queue implementation

---

### 3.2 DTO Naming for Accounting

**Owner**: Backend Architect
**Deadline**: Week 3
**Document**: DEVELOPMENT_STANDARDS.md - Section 1.3 (extend)

- [ ] Define accounting-specific DTOs:
  - [ ] `CreateJournalEntryDTO`
  - [ ] `UpdateJournalEntryDTO`
  - [ ] `JournalEntryResponseDTO`
  - [ ] `SubmitJournalDTO`
  - [ ] `ApproveJournalDTO`
  - [ ] `RejectJournalDTO`
  - [ ] `VoidJournalDTO`
  - [ ] `AutoPostJournalDTO`
- [ ] Validation rules in each DTO
- [ ] Field-level documentation
- [ ] Example request/response payloads

**Deliverable**: Complete DTO definitions

---

### 3.3 Error Handling Patterns

**Owner**: Backend Architect
**Deadline**: Week 3
**Document**: DEVELOPMENT_STANDARDS.md - Section 7.X (extend)

- [ ] Hard rule violation errors (4xx)
- [ ] Soft rule violation warnings (2xx)
- [ ] Transaction rollback errors
- [ ] Integration failure errors
- [ ] Approval rejection errors
- [ ] Error response format consistency
- [ ] Error codes catalog
- [ ] Frontend error handling guide

**Deliverable**: Complete error handling guide

---

### 3.4 Event Versioning Migration

**Owner**: Backend Architect
**Deadline**: Week 4
**Document**: DEVELOPMENT_STANDARDS.md - Section 8.2 (new)

- [ ] Version upgrade strategy
- [ ] Backward compatibility rules
- [ ] Dual publishing during migration
- [ ] Consumer version detection
- [ ] Event schema registry
- [ ] Version deprecation policy
- [ ] Migration timeline template

**Deliverable**: Event versioning migration guide

---

## Phase 4: DOCUMENTATION (Week 4)

### 4.1 Create OpenAPI Specification

**Owner**: Backend Architect
**Deadline**: Week 4
**Document**: New file - ACCOUNTING_API_SPECIFICATION.md

- [ ] Complete OpenAPI 3.0 spec for accounting module
- [ ] All endpoints documented
- [ ] Request/response schemas
- [ ] Error responses
- [ ] Authentication requirements
- [ ] Example requests
- [ ] Code generation setup

**Deliverable**: OpenAPI spec file

---

### 4.2 Update Development Standards

**Owner**: Backend Architect
**Deadline**: Week 4
**Document**: DEVELOPMENT_STANDARDS.md

- [ ] Add all new sections
- [ ] Review for consistency
- [ ] Add code examples
- [ ] Add diagrams
- [ ] Cross-reference with accounting standards
- [ ] Get team approval

**Deliverable**: Updated Dev Standards v2.0

---

### 4.3 Update Accounting Standards

**Owner**: Business Analyst
**Deadline**: Week 4
**Document**: BUSINESS_ACCOUNTING_STANDARDS.md

- [ ] Add auto-post rules
- [ ] Add approval workflow details
- [ ] Add integration patterns
- [ ] Add validation rules
- [ ] Add error scenarios
- [ ] Get stakeholder approval

**Deliverable**: Updated Accounting Standards v2.0

---

### 4.4 Create Implementation Examples

**Owner**: Backend Architect
**Deadline**: Week 4
**Document**: New file - ACCOUNTING_IMPLEMENTATION_EXAMPLES.md

- [ ] Complete use case examples:
  - [ ] Create manual journal entry
  - [ ] Integration auto-post from PMS
  - [ ] Multi-level approval flow
  - [ ] Void posted journal
  - [ ] Failed integration retry
- [ ] Repository implementations
- [ ] Event handler examples
- [ ] Test cases

**Deliverable**: Implementation examples document

---

## Decision Log

### Decisions Required (Week 1)

| # | Decision | Options | Deadline | Owner |
|---|----------|---------|----------|-------|
| 1 | Journal Entry URL Structure | Option 1: `/journals?type=GJ`<br>Option 2: `/general-journals` | Day 2 | Backend Architect |
| 2 | Validation Layer Pattern | Single layer vs Two layers | Day 2 | Backend Architect |
| 3 | Transaction Pattern | Manual vs UnitOfWork | Day 3 | Backend Architect |
| 4 | Integration Pattern | Direct call vs Saga | Day 3 | Backend Architect |
| 5 | Event Versioning | Major.Minor vs Separate events | Day 4 | Backend Architect |
| 6 | Auto-Post Rules | Source-based vs Amount-based vs Combined | Day 5 | Business Analyst |

**Decision Meeting**: Schedule for Day 1 of Week 1

---

## Review Checkpoints

### Week 1 Review
- [ ] All critical decisions made
- [ ] Event architecture approved
- [ ] Transaction patterns approved
- [ ] API endpoints approved

### Week 2 Review
- [ ] 2-layer validation implemented
- [ ] RabbitMQ setup complete
- [ ] Auto-post rules finalized
- [ ] Approval workflow defined

### Week 3 Review
- [ ] Integration queue working
- [ ] Pre-post validation complete
- [ ] DTOs defined
- [ ] Error handling consistent

### Week 4 Review
- [ ] OpenAPI spec complete
- [ ] All documentation updated
- [ ] Examples provided
- [ ] Team training scheduled

---

## Risk Mitigation

### If Week 1 Decisions Delayed
**Risk**: Development blocked
**Mitigation**:
- Escalate to project manager
- Schedule emergency decision meeting
- Document blockers

### If RabbitMQ Setup Issues
**Risk**: Event integration broken
**Mitigation**:
- Fall back to database event queue temporarily
- Plan migration path
- Document technical debt

### If Approval Logic Complex
**Risk**: Implementation delayed
**Mitigation**:
- Start with simple single-level approval
- Add multi-level in Phase 2
- Document future enhancements

---

## Success Criteria

### Week 1-2 Complete
- ✅ All CRITICAL fixes documented
- ✅ Architecture decisions made
- ✅ Event schema defined
- ✅ Transaction patterns approved

### Week 3-4 Complete
- ✅ All HIGH priority items documented
- ✅ OpenAPI spec created
- ✅ Standards updated
- ✅ Examples provided

### Ready for Development
- ✅ No contradictions between documents
- ✅ All patterns defined with code examples
- ✅ API endpoints completely specified
- ✅ Validation layers clear
- ✅ Transaction handling robust
- ✅ Event architecture complete
- ✅ Team trained and aligned

---

## Notes

- This checklist is based on contradictions found in API_BACKEND_CONTRADICTIONS_REPORT.md
- Each item should be tracked in project management tool
- Weekly reviews are mandatory
- All documentation must be peer-reviewed
- Code examples must be working and tested

---

**Start Date**: TBD
**Target Completion**: 4 weeks from start
**Review Cadence**: Weekly
**Final Approval**: Before development sprint planning
