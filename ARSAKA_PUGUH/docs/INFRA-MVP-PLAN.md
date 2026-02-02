# INFRA-MVP-PLAN: Minimal Viable Product Rollout

**VERSION**: MVP Planning Phase
**STATUS**: DRAFT (Awaiting approval for execution)
**DATE**: 2025-12-28

---

## Executive Summary

**MVP Vision**: A single-tenant decision engine with rule evaluation and immutable audit trail.

**Success Criteria**:
- Single tenant can create decisions with 3 outcomes (ALLOWED, DENIED, REQUIRE_APPROVAL)
- Rules are deterministic and rule changes are audit-logged
- All Layer 0-3 guarantees are implemented and tested
- Decision latency: p95 < 100ms
- Immutability, tenant isolation, SLA verified by automated tests

**Scope Constraint**: MVP is **intentionally minimal** to validate architecture before scaling.

---

## 1. MVP Scope Definition

### 1.1 In Scope (MVP Deliverables)

**Core Decision Engine** (INFRA-LAY3-002):
- ✅ createDecision() endpoint (SDK method)
- ✅ Rule evaluation (deterministic, first-match-wins)
- ✅ 3 outcomes: ALLOWED, DENIED, REQUIRE_APPROVAL
- ✅ Idempotency support (same idempotency_key = same decision_id)
- ✅ Decision immutability (outcome locked at creation)
- ✅ Tenant isolation (single tenant, data isolated)

**SDK** (INFRA-LAY3-001):
- ✅ createDecision(decision_type, context, tenant_id, idempotency_key?)
- ✅ getDecision(decision_id, tenant_id)
- ✅ Request validation (tenant_id, decision_type, context format)
- ✅ Context sanitization (reject PII)
- ✅ Error handling (retriable, non-retriable)
- ✅ Retry logic (exponential backoff)

**Data Persistence** (INFRA-LAY3-004):
- ✅ decisions table (immutable)
- ✅ event_log table (append-only)
- ✅ operations_audit table (audit trail)
- ✅ Immutability enforcement (triggers, role permissions)
- ✅ RLS policies (tenant isolation)
- ✅ Indexes (critical queries)

**Rule Configuration** (INFRA-LAY3-003 - Minimal):
- ✅ Rule CRUD (create, read, update, activate)
- ✅ Rule versioning (DRAFT → ACTIVE → DEPRECATED)
- ✅ Rule testing (test endpoint)
- ✅ Audit logging (rule changes)

**Observability** (INFRA-LAY2-004 - Core Metrics):
- ✅ Decision latency metrics (p95, p99)
- ✅ Error logging (structured JSON)
- ✅ Trace ID propagation
- ✅ Immutability violation alerts

**Testing** (INFRA-LAY3-006 - MVP Subset):
- ✅ Unit tests (SDK, Core validation)
- ✅ Integration tests (happy path, errors)
- ✅ Security tests (immutability, isolation)
- ✅ Load tests (p95 < 100ms)

### 1.2 Out of Scope (Post-MVP)

**Workflow Approval** (Complex state machine):
- ❌ Workflow creation (REQUIRE_APPROVAL outcome still stored)
- ❌ approveWorkflow(), rejectWorkflow(), delegateWorkflow()
- ❌ Workflow escalation on timeout
- ❌ workflow_transitions table
- ❌ Approval notifications
- **Defer**: Phase 2

**CMS Advanced Features**:
- ❌ Rule UI/Dashboard (use CLI or API only in MVP)
- ❌ Rule comparison (side-by-side versions)
- ❌ Bulk rule import/export
- ❌ Rule performance analytics
- **Defer**: Phase 2

**Multi-Tenant Operational Features**:
- ❌ Tenant onboarding workflows
- ❌ Cross-tenant reporting
- ❌ Tenant-specific SLAs
- ❌ Tenant-specific rule versioning strategies
- **Defer**: Phase 3

**Event Bus & Consumers**:
- ❌ Kafka/event bus integration
- ❌ Event consumer framework
- ❌ Event-driven business logic (notifications, webhooks)
- ❌ Event replay/reprocessing
- **Defer**: Phase 2 (events persisted to event_log, bus not required)

**Archival & Cold Storage**:
- ❌ Hot → Warm → Cold tiering
- ❌ Data archival automation
- ❌ Cold storage rehydration
- **Defer**: Phase 3 (hot storage only in MVP)

**Advanced Monitoring**:
- ❌ Distributed tracing (Jaeger, Zipkin)
- ❌ Custom dashboards (Grafana, Datadog)
- ❌ Alerting platform (Pagerduty, Opsgenie)
- ❌ SLA reporting
- **Defer**: Phase 2 (basic metrics/logs sufficient)

---

## 2. MVP Phasing

### 2.1 Phase 1: Core Decision Engine (Foundation)

**Focus**: Build the decision engine with immutability guarantees and audit trail.

**Deliverables**:

**Service: Core** (INFRA-LAY3-002)
- ✅ Rule evaluation engine (deterministic, first-match-wins)
- ✅ Decision creation transaction (atomic, immutable)
- ✅ Database persistence (decisions, event_log, operations_audit tables)
- ✅ Immutability enforcement (triggers, role permissions)
- ✅ Tenant isolation (RLS policy enforcement)

**Service: SDK** (INFRA-LAY3-001)
- ✅ createDecision() implementation
- ✅ getDecision() implementation
- ✅ Request validation (pre-flight)
- ✅ Context sanitization (PII rejection)
- ✅ Error classification & retry logic
- ✅ Idempotency support

**Service: Data Layer** (INFRA-LAY3-004)
- ✅ PostgreSQL setup (13+)
- ✅ Schema: decisions, event_log, operations_audit tables
- ✅ Immutability triggers
- ✅ RLS policies
- ✅ Indexes for critical queries
- ✅ Connection pooling & circuit breaker

**Testing** (INFRA-LAY3-006):
- ✅ Unit tests: SDK validation, Core rule evaluation
- ✅ Integration tests: decision creation happy path & error paths
- ✅ Security tests: immutability, tenant isolation
- ✅ Load tests: p95 < 100ms (100 concurrent users)

**Artifacts**:
- Core service (HTTP API)
- SDK library
- Database schema
- Test suite (80%+ coverage)
- Documentation (API reference, getting started)

**Success Criteria**:
- ✅ Decision latency: p95 < 100ms
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Immutability verified (triggers prevent UPDATE/DELETE)
- ✅ Tenant isolation verified (RLS prevents cross-tenant access)
- ✅ Load test: 1000 req/sec, p95 < 100ms

**Golden Path Example (Phase 1)**:

```
1. Create rule (via API):
   POST /rules
   {
     decision_type: "inventory.stock_transfer",
     conditions: "context.quantity <= 100",
     action: {outcome: "ALLOW"}
   }
   → rule_id: "r-stock-limit-rule"

2. Activate rule (via API):
   POST /rules/r-stock-transfer-rule/activate
   → status: "ACTIVE"

3. Create decision (SDK):
   const decision = await sdk.createDecision(
     "inventory.stock_transfer",
     {quantity: 50, warehouse: "A"},
     "tenant-1"
   );
   → {
       decision_id: "dec-xyz",
       outcome: "ALLOWED",
       rule_matched: "stock_limit_rule"
     }

4. Verify audit trail (API):
   GET /audit?decision_id=dec-xyz
   → All state changes logged:
     - Rule created
     - Rule activated
     - Decision created
     - Event emitted

5. Verify immutability (attempt to modify - should fail):
   UPDATE decisions SET outcome='DENIED' WHERE decision_id='dec-xyz'
   → Exception: "Immutable table"
   → operations_audit: UPDATE_ATTEMPT logged
```

---

### 2.2 Phase 2: Rule Management & Observability

**Focus**: CMS rule management and operational observability (metrics, logs).

**Deliverables**:

**Service: CMS** (INFRA-LAY3-003):
- ✅ Rule CRUD API (full: create, read, update, activate, deactivate)
- ✅ Rule versioning (DRAFT → ACTIVE → DEPRECATED)
- ✅ Rule testing endpoint (test DRAFT before activation)
- ✅ Audit querying (rule change history, decision audit trail)
- ✅ Rule validation (syntax, conditions, nesting depth)

**Event Bus Integration** (INFRA-LAY3-005):
- ✅ Event publishing to Kafka (async, non-blocking)
- ✅ Event consumer framework (template)
- ✅ Deduplication support (event_consumer_state table)
- ✅ Dead-letter queue (DLQ for poison messages)

**Observability** (INFRA-LAY2-004):
- ✅ Metrics collection: decision latency, rule evaluation time, error rate
- ✅ Structured logging (JSON format, trace ID correlation)
- ✅ Log aggregation (centralized, searchable)
- ✅ Alert thresholds (SLA breaches, immutability violations)

**Testing**:
- ✅ Unit tests: CMS rule CRUD, versioning logic
- ✅ Integration tests: rule activation & decision impact
- ✅ Load tests: CMS operations (rule changes don't block decisions)
- ✅ Event tests: Kafka publishing, consumer deduplication

**Artifacts**:
- CMS service (HTTP API + CLI)
- Kafka topic setup (infra-events)
- Event consumer template
- Metrics/logging configuration
- Observability dashboards (basic)

**Success Criteria**:
- ✅ Rule activation < 1 second (fast rule changes)
- ✅ CMS operations do NOT impact Core latency
- ✅ Event publishing 99%+ successful
- ✅ All observability metrics collected and queryable
- ✅ SLA breaches detected and alerted

---

### 2.3 Phase 3: Workflow Approval & Advanced Features

**Focus**: Multi-step approval workflows and enterprise features.

**Deliverables**:

**Workflow Approval System** (INFRA-LAY3-002, 003):
- ✅ Workflow state machine (PENDING_APPROVAL → APPROVED/REJECTED/ESCALATED)
- ✅ approveWorkflow(), rejectWorkflow(), escalateWorkflow() endpoints
- ✅ Delegation flow (delegate to another approver)
- ✅ Escalation on timeout (automatic escalation if pending > N hours)
- ✅ workflow_transitions table (append-only audit trail)

**Advanced Features**:
- ✅ Multi-tenant support (scaling to 100+ tenants)
- ✅ Tenant-specific rule strategies
- ✅ Archival & tiering (hot → warm → cold storage)
- ✅ Advanced monitoring (distributed tracing, custom dashboards)
- ✅ Compliance reporting (GDPR, HIPAA, SOX)

**Testing**:
- ✅ Workflow state machine tests
- ✅ Approval workflow integration tests
- ✅ Chaos tests (failure recovery)
- ✅ E2E tests (complete decision → approval flow)

**Artifacts**:
- Workflow approval service
- Archival automation
- Compliance reporting
- Advanced observability

**Success Criteria**:
- ✅ Workflows complete in < 100ms (p95)
- ✅ Escalation works correctly (timeout + notification)
- ✅ All Layer 0-3 guarantees verified in production
- ✅ 100+ tenants supported simultaneously
- ✅ Compliance requirements met

---

## 3. MVP Resource Requirements

### 3.1 Team Composition

**Backend Engineers** (3 FTE):
- 1 Core service (rule evaluation, decision creation)
- 1 Data layer (PostgreSQL, immutability, RLS)
- 1 SDK + CMS API

**DevOps/Platform Engineer** (1 FTE):
- Database setup & management
- Observability (metrics, logs, alerting)
- Kafka setup (Phase 2)

**QA/Test Engineer** (1 FTE):
- Test automation (unit, integration, load, security)
- Test data generation

**Product/Architecture** (0.5 FTE):
- MVP scope refinement
- Feature prioritization
- Stakeholder communication

**Total**: 5.5 FTE

### 3.2 Skills Required

**Core Competencies**:
- SQL (PostgreSQL) & transaction handling
- API design & HTTP error handling
- Microservices architecture
- Database security (RLS, triggers)
- Testing (unit, integration, load)
- Git & code review processes

**Nice-to-Have**:
- Kafka / event streaming
- Distributed systems
- Security (encryption, audit logging)

---

## 4. MVP Dependencies & Blockers

### 4.1 External Dependencies

**Infrastructure**:
- PostgreSQL 13+ database (managed or self-hosted)
- Kafka 2.8+ (Phase 2 onwards)
- Observability stack (Prometheus, ELK, or managed service)

**Third-Party Services** (None required for MVP):
- No external auth service required (opaque context only)
- No notification service required (Phase 2)
- No compliance tooling required (app-side responsibility)

### 4.2 Internal Dependencies

**Layer 0-3 Documentation** (✓ Complete):
- All architectural guarantees defined
- All implementation standards locked
- Ready for code reference

**Decisions**:
- Programming languages for SDK (TypeScript, Go, Python?)
- Framework choices (Express, FastAPI, Spring?)
- Deployment target (Docker, Kubernetes, Lambda?)
- → **Decision point: Before Phase 1 execution**

### 4.3 Blockers

**None**. Architecture is complete and ready for implementation.

**Risk mitigation**:
- Code reviews (enforce Layer 3 standards)
- Automated testing (verify all guarantees)
- Pair programming (complex areas: transactions, RLS, triggers)

---

## 5. MVP Rollout Strategy

### 5.1 Phase 1 Rollout (Foundation)

**Target**: Deploy Core + SDK + Data layer

**Rollout Steps**:
1. Set up PostgreSQL database
2. Create schema (decisions, event_log, operations_audit tables)
3. Implement Core service (rule evaluation, decision creation)
4. Implement SDK (createDecision, getDecision)
5. Implement immutability triggers & RLS policies
6. Write & run comprehensive tests
7. Deploy to development environment
8. Deploy to staging environment (pre-production testing)
9. Collect user feedback
10. Deploy to production (single tenant)

**Rollout Validation**:
- ✅ All tests pass (unit, integration, security, load)
- ✅ Immutability verified (no successful UPDATE/DELETE)
- ✅ Tenant isolation verified (RLS prevents cross-tenant access)
- ✅ SLA met (p95 < 100ms)
- ✅ Observability working (logs, metrics, traces)

### 5.2 Phase 2 Rollout (CMS + Observability)

**Target**: Deploy CMS + Kafka + Metrics

**Rollout Steps**:
1. Set up Kafka cluster
2. Create infra-events topic
3. Implement CMS service (rule CRUD, versioning)
4. Implement event publishing (async, non-blocking)
5. Implement event consumer template
6. Set up observability (Prometheus, ELK, alerting)
7. Write & run tests
8. Deploy to staging
9. Collect feedback
10. Deploy to production

**Rollout Validation**:
- ✅ Rule changes don't impact decision latency
- ✅ Events published successfully (99%+ delivery)
- ✅ Observability metrics collected (latency, errors, etc.)
- ✅ Alerts trigger correctly (SLA breach, violations)

### 5.3 Phase 3 Rollout (Workflows + Scale)

**Target**: Deploy workflow approval, multi-tenant support

**Rollout Steps**:
1. Implement workflow state machine
2. Implement approval endpoints
3. Implement escalation logic
4. Migrate to multi-tenant data model
5. Set up archival automation
6. Write & run tests
7. Deploy to production (phased: 10% → 50% → 100% tenants)

**Rollout Validation**:
- ✅ Workflows complete < 100ms (p95)
- ✅ Escalation triggers correctly
- ✅ Multi-tenant isolation verified
- ✅ Archival working correctly
- ✅ All Layer 0-3 guarantees verified at scale

---

## 6. MVP Success Metrics

### 6.1 Technical Metrics

| Metric | Target | Phase |
|--------|--------|-------|
| Decision latency (p95) | < 100ms | 1 |
| Decision latency (p99) | < 200ms | 1 |
| Workflow approval latency (p95) | < 100ms | 3 |
| Error rate | < 0.1% | 1 |
| Immutability violations | 0 | 1 |
| Cross-tenant access attempts | 0 | 1 |
| Test coverage | > 80% | 1 |
| Uptime | > 99.5% | 2 |
| Event delivery success | > 99% | 2 |

### 6.2 Operational Metrics

| Metric | Target | Phase |
|--------|--------|-------|
| Time to deploy (Phase 1) | < 2 hours | 1 |
| Time to rollback | < 15 minutes | 1 |
| Mean time to recovery (MTTR) | < 30 minutes | 2 |
| Incident response time | < 5 minutes | 2 |

### 6.3 Quality Metrics

| Metric | Target | Phase |
|--------|--------|-------|
| Code review coverage | 100% | 1 |
| Security test coverage | 100% | 1 |
| Layer 3 standard compliance | 100% | 1 |
| Documentation completeness | 100% | 2 |

---

## 7. MVP Risk Assessment

### 7.1 High-Risk Areas

**Risk 1: Immutability Enforcement**
- **Severity**: HIGH (architectural guarantee)
- **Likelihood**: LOW (well-defined in Layer 3)
- **Mitigation**: Unit tests for triggers, security tests for violation detection
- **Contingency**: Audit trail proves violations occurred (alerting)

**Risk 2: Tenant Isolation (RLS)**
- **Severity**: HIGH (security, compliance)
- **Likelihood**: LOW (RLS is PostgreSQL built-in)
- **Mitigation**: Security tests, code review, RLS policy validation
- **Contingency**: Schema-per-tenant fallback (if RLS has bugs)

**Risk 3: Transaction Atomicity**
- **Severity**: HIGH (data consistency)
- **Likelihood**: LOW (well-defined in Layer 3)
- **Mitigation**: Integration tests, chaos testing
- **Contingency**: Backup & recovery procedures

### 7.2 Medium-Risk Areas

**Risk 4: Idempotency Cache Consistency**
- **Severity**: MEDIUM (decision duplication possible)
- **Likelihood**: MEDIUM (cache timing issues)
- **Mitigation**: Cache TTL management, hash verification
- **Contingency**: Deduplication by idempotency_key in database

**Risk 5: Event Bus Failure (Phase 2)**
- **Severity**: MEDIUM (event loss possible)
- **Likelihood**: LOW (Kafka replication 3x)
- **Mitigation**: Dead-letter queue, event_log as source of truth
- **Contingency**: Manual event replay from event_log

**Risk 6: Performance Degradation**
- **Severity**: MEDIUM (SLA breach)
- **Likelihood**: MEDIUM (depends on implementation quality)
- **Mitigation**: Load testing, continuous monitoring, auto-scaling
- **Contingency**: Database query optimization, caching layer

### 7.3 Low-Risk Areas

**Risk 7: Scope Creep**
- **Severity**: LOW (delays, but architecture sound)
- **Likelihood**: MEDIUM (MVP requires discipline)
- **Mitigation**: Strict scope definition (this document), feature gating
- **Contingency**: Defer to Phase 2/3

---

## 8. MVP Timeline (Milestones, not Durations)

### Phase 1: Foundation (Core + SDK + Data)

**Milestone 1.1**: Database schema ready
- Decisions, event_log, operations_audit tables created
- Immutability triggers deployed
- RLS policies enforced

**Milestone 1.2**: Core service ready
- Rule evaluation engine implemented
- Decision creation transaction working
- All unit tests passing

**Milestone 1.3**: SDK ready
- createDecision() & getDecision() implemented
- Validation & sanitization working
- Retry logic & error classification working

**Milestone 1.4**: Integration tests ready
- Happy path tests passing
- Error path tests passing
- Security tests passing

**Milestone 1.5**: Load tests ready
- p95 < 100ms verified
- 1000 concurrent users sustained
- No data loss under load

**Milestone 1.6**: Staging deployment
- Phase 1 deployed to staging
- User acceptance testing (UAT)
- Feedback incorporated

**Milestone 1.7**: Production deployment
- Phase 1 live (single tenant)
- Monitoring & alerting active
- Runbooks documented

---

### Phase 2: CMS + Observability (Rule Management + Events)

**Milestone 2.1**: CMS service ready
- Rule CRUD API working
- Rule versioning & activation working
- Audit logging working

**Milestone 2.2**: Kafka integration
- Event publishing (async) working
- Consumer deduplication working
- Dead-letter queue handling

**Milestone 2.3**: Observability
- Metrics collection (latency, errors)
- Structured logging (JSON)
- Alerting thresholds configured

**Milestone 2.4**: Phase 2 tests
- CMS tests passing
- Event tests passing
- Observability tests passing

**Milestone 2.5**: Staging & production
- Phase 2 staged
- User feedback
- Production deployment

---

### Phase 3: Workflows + Multi-Tenant

**Milestone 3.1**: Workflow approval ready
- State machine implemented
- Escalation logic working
- workflow_transitions table populated

**Milestone 3.2**: Multi-tenant ready
- Tenant onboarding process
- Data isolation verified (100+ tenants)
- Tenant-specific configurations

**Milestone 3.3**: Archival ready
- Hot → Warm migration (scheduled)
- Cold storage setup
- Rehydration working

**Milestone 3.4**: Phase 3 tests & production
- All tests passing
- Chaos tests validating recovery
- Production deployment (phased)

---

## 9. MVP Constraints & Assumptions

### 9.1 Constraints

**Single Decision Type in MVP**:
- Recommendation: Choose ONE decision_type for Phase 1 (e.g., "inventory.stock_transfer")
- Rationale: Proves architecture works, simpler rule set, faster validation
- Expand: Phase 2 (add more decision types once core is solid)

**Single Tenant in MVP**:
- Recommendation: Deploy with tenant_id = "mvp-internal" (Infra team's internal tenant)
- Rationale: Validates isolation & auditing, simpler testing
- Expand: Phase 3 (multi-tenant support)

**No External Dependencies**:
- No auth service integration (opaque context only)
- No notification service (Phase 2)
- No compliance tooling (application responsibility)
- Rationale: Keep MVP scope tight

**PostgreSQL Only**:
- No schema-per-tenant (RLS sufficient for MVP)
- No database-per-tenant (scaling decision later)
- Rationale: Simpler setup, easier testing

### 9.2 Assumptions

**Team Composition**:
- 5.5 FTE backend engineers available
- Code review discipline (all changes reviewed)
- CI/CD pipeline available (tests run on every commit)

**Infrastructure**:
- PostgreSQL 13+ available
- Docker available (containerization)
- Kubernetes OR managed hosting available

**Tools**:
- Git + GitHub available
- Observability tools (Prometheus, ELK, or SaaS) available
- Load testing tool (k6, JMeter, or similar) available

**Knowledge**:
- Team familiar with SQL transactions & ACID guarantees
- Team familiar with API design & error handling
- Team familiar with testing (unit, integration, load)

---

## 10. MVP Success Criteria (Gate for Phase 2)

**Before proceeding to Phase 2, verify**:

✅ **Phase 1 Deployment**:
- [ ] Core service deployed to production
- [ ] SDK library released (package manager)
- [ ] Database schema in place
- [ ] All tests passing (unit, integration, security, load)

✅ **Guarantees Verified**:
- [ ] Immutability: No successful UPDATE/DELETE on immutable tables
- [ ] Tenant isolation: Cross-tenant queries return 0 rows
- [ ] Determinism: Same rule + context = same outcome (tested 100x)
- [ ] SLA: p95 latency < 100ms (measured under 1000 concurrent users)
- [ ] Audit trail: All state changes logged, queryable

✅ **Operational Readiness**:
- [ ] Monitoring & alerting configured
- [ ] Runbooks documented (incident response)
- [ ] Backup & recovery tested
- [ ] Rollback procedures tested
- [ ] On-call support team trained

✅ **Stakeholder Feedback**:
- [ ] Product owner approves Phase 1
- [ ] Security team approves immutability & isolation
- [ ] Operations team approves deployment & monitoring
- [ ] Users (internal) have tested and provided feedback

---

## 11. Summary: MVP as Validation Gate

**Phase 1 validates**: Architecture → Implementation → Testing pipeline works.

**Phase 2 adds**: Operational sophistication (rule management, observability, events).

**Phase 3 scales**: Multi-tenant, complex workflows, enterprise features.

**Key Decision**: Lock Phase 1 before starting Phase 2.
- If Phase 1 reveals architectural flaw: fix Layer 0-3, iterate.
- If Phase 1 succeeds: proceed to Phase 2 (phased approach).

**MVP is NOT production-ready for scale**:
- Single tenant only
- Limited monitoring
- No advanced features

**MVP IS production-ready for validation**:
- All Layer 0-3 guarantees implemented
- All guarantees verified by tests
- Ready for internal/beta users
- Foundation for scaling

---

**STATUS**: INFRA-MVP-PLAN DRAFT, ready for review and approval.

**Next**: User approval → Phase 1 execution begins.
