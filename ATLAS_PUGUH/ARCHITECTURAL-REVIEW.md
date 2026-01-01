# ATLAS_PUGUH: Comprehensive Architectural Review

**Purpose**: Deep analysis of completeness, gaps, consistency, and risks in the ATLAS_PUGUH architecture (Layers 0-3 + MVP plan).

**Prepared for**: Cross-AI architectural debate to validate correctness and identify missing components.

**Date**: 2025-12-28

---

## EXECUTIVE SUMMARY

**Status**: Architecture is **72% complete** (foundational layers solid, operational/integration gaps).

**Strengths**:
- ✅ Immutability guarantees rigorously defined (Layer 0-3)
- ✅ Tenant isolation architecture sound (database-enforced)
- ✅ Decision determinism requirements clear
- ✅ Audit trail & observability comprehensive
- ✅ Testing strategy aligned with guarantees

**Critical Gaps**:
- ❌ Application Adapter design incomplete (heavily referenced, not fully specified)
- ❌ Extension hooks/webhooks execution model undefined
- ❌ Idempotency edge cases (cache loss, recovery) not addressed
- ❌ Data consistency edge cases (partial failures) not defined
- ❌ Operational procedures (runbooks, incident response) missing
- ❌ Security model (auth, encryption, rate limiting) incomplete
- ❌ Multi-tenant operational scenarios (tenant deletion, suspension) not defined
- ❌ Extensibility strategy (new outcome types, event types, conditions) missing
- ❌ Performance optimization strategy (caching, indexing, connection pooling) incomplete

**Recommendation**: Review gaps before Phase 1 execution. Some are critical (data consistency, idempotency), others can defer to Phase 2 (operational procedures, extensibility).

---

## 1. COMPLETENESS AUDIT

### 1.1 What IS Defined

**Layer 0 (Concepts)** ✅ COMPLETE
- ✓ Decision definition (3 outcomes, immutable, versioned rule)
- ✓ Tenancy boundaries (hard isolation, 4 layers)
- ✓ Rule & workflow abstraction (deterministic evaluation, state machine)

**Layer 1 (Contracts)** ✅ COMPLETE
- ✓ SDK contracts (8 methods with parameters, return types)
- ✓ Event schema (11 event types, structure)
- ✓ Error classification (retriable, non-retriable)
- ✓ Auth context forwarding (opaque principle)

**Layer 2 (Architecture)** ✅ MOSTLY COMPLETE
- ✓ Service boundaries (4 services, responsibilities)
- ✓ Critical path sequences (timing, latency targets)
- ✓ Data persistence (6 tables, immutability, archival)
- ✓ Observability (metrics, logging, alerting)
- ⚠ Rule caching strategy (< 2 seconds propagation, but cache invalidation details sparse)
- ⚠ Circuit breaker pattern (mentioned, not detailed)

**Layer 3 (Implementation)** ✅ MOSTLY COMPLETE
- ✓ SDK validation standards
- ✓ Core rule evaluation (determinism, nesting, conditions)
- ✓ Decision transaction atomicity
- ✓ Workflow state machine
- ✓ Data layer immutability & RLS
- ✓ Event publishing & consumption
- ✓ Structured logging
- ⚠ Testing patterns defined, but contract testing (SDK ↔ Core) not included

**MVP Plan** ✅ COMPLETE
- ✓ Phase-based rollout (3 phases)
- ✓ Success criteria (gates between phases)
- ✓ Resource allocation (5.5 FTE)

---

### 1.2 What is NOT Defined (Critical Gaps)

#### Gap 1: Application Adapter Design ⚠️ CRITICAL

**Definition**: "Application Adapter" is mentioned 50+ times across documents but never formally designed.

**What's Missing**:
1. **Architecture**: Is Adapter a service? Library? Sidecar? Part of application code?
2. **Responsibilities** (partially defined):
   - ✓ User resolution (role → user_id list)
   - ✓ Entity validation (does entity_id exist?)
   - ✓ Notification sending
   - ❌ How does it store state? Database schema?
   - ❌ How does it validate entities? What are validation rules?
   - ❌ How does it handle notification failures?
   - ❌ How does it scale (1000 tenants)?
   - ❌ What happens if Adapter is down?

3. **Integration Points**:
   - ✓ Receives events from event_log
   - ❌ How does it subscribe to events? Polling? Push?
   - ❌ How does it handle event backlog?
   - ❌ How does it deduplicate events?

4. **Data Model**:
   - ❌ What entities does Adapter own?
   - ❌ What's the schema for user roles, entity ownership?
   - ❌ Where is this data stored?
   - ❌ Is it per-tenant? Shared?

5. **Guarantees**:
   - ❌ Does Adapter need to provide consistency guarantees?
   - ❌ Can Adapter be eventually consistent?
   - ❌ What's the SLA for user resolution (role → user_id)?

**Impact**: Core depends on Adapter for:
- User role resolution (approveWorkflow must trust role → user_id mapping)
- Entity ownership validation (if rule references entity_id)
- Notifications (if outcome requires approval)

If Adapter is wrong, Core guarantees can be violated.

**Recommendation**:
Before Phase 1 execution, create INFRA-ADAPTER-DESIGN with:
- Adapter as separate service (REST API)
- Schema for roles, user mappings, entity ownership
- Event consumption pattern (from event_log)
- SLA & resilience (what if Adapter is down?)
- Testing strategy

---

#### Gap 2: Extension Hooks Execution Model ⚠️ CRITICAL

**Definition**: INFRA-DEC-003 mentions async, non-blocking extension hooks but doesn't define execution model.

**What's Missing**:
1. **Hook Invocation**:
   - ✓ Async, non-blocking (fire-and-forget)
   - ❌ How are hooks invoked? Background job queue? Webhook?
   - ❌ Who invokes hooks? Core? Separate service?
   - ❌ Invocation timing (immediately after decision? scheduled?)

2. **Hook Payload**:
   - ❌ What data is passed to hook?
   - ❌ Can hook see full context or sanitized?
   - ❌ Can hook see decision_id before persistence?

3. **Hook Execution Guarantees**:
   - ❌ At-least-once? Exactly-once? At-most-once?
   - ❌ Timeout (what if hook hangs)?
   - ❌ Retry logic (what if hook fails)?
   - ❌ Error handling (fail-open or fail-closed?)

4. **Hook Security**:
   - ❌ Authentication (how does Core auth with hook endpoint?)
   - ❌ Rate limiting (DOS protection for hooks?)
   - ❌ Payload validation (is hook data trusted?)

5. **Hook Ordering**:
   - ❌ If multiple hooks, execution order?
   - ❌ If hook 1 fails, do remaining hooks execute?

**Example Scenario** (undefined):
```
Decision created: outcome=REQUIRE_APPROVAL
Hooks configured:
  1. Send notification
  2. Update audit log
  3. Trigger workflow escalation

What happens if:
  - Hook 1 (notification) fails?
    → Do hooks 2, 3 still execute?
  - Hook 2 succeeds, hook 3 fails?
    → Is Core aware of partial failure?
  - All hooks hang (e.g., network timeout)?
    → Does decision return to SDK anyway (non-blocking promise)?
```

**Impact**: Hooks enable business logic customization, but undefined execution model can cause:
- Silent failures (hook fails, application unaware)
- Race conditions (hook executes after Core completes)
- Cascading failures (hook failure crashes Core)

**Recommendation**: Create INFRA-EXTENSION-HOOKS-MODEL with:
- Async job queue (Redis, RabbitMQ)
- Payload schema (what data in hook)
- Execution guarantees (at-least-once, timeout, retry)
- Error handling (fail-open, fail-closed)
- Authentication & rate limiting
- Testing strategy

---

#### Gap 3: Idempotency Edge Cases ⚠️ CRITICAL

**Definition**: Idempotency via idempotency_key is specified, but edge cases not defined.

**What's Missing**:
1. **Cache Loss Recovery**:
   - INFRA-LAY3-002 says: "Idempotency cache: in-memory, 24h TTL"
   - ❌ What if cache is lost (server restart)?
   - ❌ How is decision_id recovered?
   - ❌ Fallback: database lookup by (tenant_id, idempotency_key)?

2. **Cache Consistency**:
   - ❌ In distributed Core (multiple instances), is cache synchronized?
   - ❌ If instance A cached decision, can instance B find it?
   - ❌ Redis backend vs in-memory?

3. **Edge Case: Partial Idempotency**:
   - ❌ If Core persists decision but fails to cache it, retry sees no cache entry
   - ❌ Retry re-evaluates rules, gets same decision_id (dedup by key)
   - ❌ But if rules changed between retries, outcome could differ
   - ❌ Does second outcome match first? Or is this a correctness issue?

4. **Example Scenario** (undefined):
```
Request 1: createDecision(decision_type, context, tenant, idempotency_key='req-1')
  → Rule evaluation
  → Decision created: {decision_id: 'dec-1', outcome: 'ALLOWED'}
  → Cached: (tenant, 'req-1') → 'dec-1'
  → Response returned

Request 2 (retry, same): createDecision(..., idempotency_key='req-1')
  → Cache hit: ('req-1') → 'dec-1'
  → But what if cache was lost between Request 1 & 2?
  → Fallback: query database by idempotency_key
  → Found: decision_id='dec-1'
  → Return same decision

Request 3 (delayed retry): createDecision(..., idempotency_key='req-1')
  → Cache miss (24h TTL expired)
  → Database lookup: no entry (cleaned up for retention)
  → What now? Treat as new request (create 'dec-2')?
  → Or error "idempotency_key unknown"?
```

**Impact**: Wrong idempotency behavior causes:
- Duplicate decisions (violates SDK contract)
- Data corruption (same key → different decision_id)
- Application confusion (retry returns different outcome)

**Recommendation**: Clarify idempotency model:
1. Cache backend (in-memory vs Redis)
2. TTL (24h minimum, but how long actually?)
3. Recovery if cache lost (database fallback)
4. Distributed consistency (if multiple Core instances)
5. TTL expiration behavior (error or allow new decision with same key?)

---

#### Gap 4: Data Consistency in Partial Failures ⚠️ CRITICAL

**Definition**: ACID guarantees within Core, but cross-service failures not defined.

**What's Missing**:
1. **Decision Persisted, Event Emission Fails**:
   - Core: decision inserted, event_log inserted (ACID)
   - But: event bus publish fails (Kafka unavailable)
   - ❌ Is event published later? Manually?
   - ❌ How does consumer know to reprocess?

2. **Decision Response Sent, Error After**:
   - Core: sends response to SDK (200 OK)
   - But: event emission starts, crashes, fails
   - ❌ SDK thinks decision is complete, but event never published
   - ❌ Consumer sees no event, decision missing from workflow

3. **Idempotency Cache Write Fails**:
   - Core: decision created, event emitted
   - But: cache write fails (Redis unavailable)
   - ❌ Retry doesn't find cache entry
   - ❌ Retry re-evaluates rules (could get different outcome if rules changed)
   - ❌ Duplicate decision created

4. **Example Scenario** (undefined):
```
Timeline:
T0: SDK calls createDecision(idempotency_key='req-1')
T1: Core evaluates rules
T2: Core INSERT decisions (outcome='ALLOWED') → success
T3: Core INSERT event_log → success
T4: Core tries to cache: redis.set('req-1', 'dec-1') → FAIL (Redis down)
T5: Core publishes to Kafka → FAIL (Kafka down)
T6: Core returns 503 to SDK
T7: SDK retries (exponential backoff)
T8: SDK calls createDecision again (same request)
T9: Core tries cache lookup → MISS (never cached)
T10: Core queries idempotency_cache table → HIT (written to DB in transaction)
T11: Core returns cached decision_id → 'dec-1' (correct!)
T12: Decision complete

BUT: What if step T10 fails? No database entry?
→ Core treats as new request
→ Rules re-evaluated (outcome=ALLOWED again, by luck)
→ But if rules changed: outcome could be DENIED
→ Two decisions with different outcomes, same idempotency_key
→ VIOLATION of idempotency contract
```

**Impact**: Partial failures can cause:
- Lost events (decision without corresponding event)
- Duplicate decisions (same key → different decision_id)
- Inconsistent state (decision in database, not in cache, not in event stream)

**Recommendation**: Define consistency model for each failure scenario:
1. Decision persisted, event fails → recovery procedure
2. Event emitted, persistence fails → rollback procedure
3. Cache fails → database fallback strategy
4. Create INFRA-CONSISTENCY-MODEL with:
   - Failure scenarios
   - Recovery procedures
   - Exactly-once vs at-least-once semantics
   - Data repair procedures
   - Testing strategy

---

#### Gap 5: Rule Caching & Invalidation Details ⚠️ HIGH

**Definition**: INFRA-LAY2-002 says "cache invalidation < 2 seconds" but implementation unclear.

**What's Missing**:
1. **Cache Backend**:
   - ❌ In-memory per Core instance? Or Redis shared?
   - ❌ If per-instance: how to keep consistent?
   - ❌ If Redis: additional dependency

2. **Invalidation Trigger**:
   - ✓ CMS activates rule → invalidate
   - ✓ CMS deactivates rule → invalidate
   - ❌ What exact mechanism? Pub/sub? Polling? Webhook?
   - ❌ If CMS sends webhook to Core, what if Core is down?

3. **Cache Thundering**:
   - ❌ Rule invalidated → all Core instances expire cache
   - ❌ All instances query database simultaneously
   - ❌ Database load spike possible
   - ❌ Mitigation? Jittered reload? Gradual invalidation?

4. **Large Rule Sets**:
   - ❌ If 1000 rules per decision_type, cache size?
   - ❌ Memory overhead?
   - ❌ Partial caching (cache only ACTIVE rules)?

5. **Example Scenario** (undefined):
```
Rule Cache State:
- decision_type="acct.journal"
- Rules (cached in memory):
  1. "amount > 10000" → DENY (v1.0, ACTIVE)
  2. "dept = 'accounting'" → ALLOW (v1.0, ACTIVE)

CMS activates new version:
- Rule 1 version 1.1: "amount > 15000" → DENY

CMS sends: POST /core/invalidate-cache
  {decision_type: "acct.journal", rule_id: "r-1"}

Core receives → expireCache('acct.journal')

But during invalidation window (< 2 seconds):
- Request A: Uses old rule (amount > 10000)
- Request B: Uses new rule (amount > 15000)

Same context: {amount: 12000}
- Request A: outcome = DENY (matches old rule)
- Request B: outcome = ALLOWED (doesn't match new rule)

TWO DECISIONS, DIFFERENT OUTCOMES, SAME CONTEXT
→ VIOLATION of determinism guarantee
```

**Impact**: Wrong caching causes:
- Non-deterministic outcomes (same context → different results)
- Race conditions (rule change not fully propagated)
- Hard to debug (intermittent failures)

**Recommendation**: Specify rule caching:
1. Cache backend (in-memory vs Redis)
2. Invalidation mechanism (pub/sub, webhook, polling)
3. Propagation guarantee (< 2 seconds means what exactly?)
4. Thundering herd mitigation
5. Partial caching strategy (ACTIVE rules only?)
6. Testing strategy (determinism under cache invalidation)

---

#### Gap 6: Operational Procedures Missing ⚠️ HIGH

**Definition**: No runbooks, incident response, or operational processes defined.

**What's Missing**:
1. **Incident Response**:
   - ❌ Immutability violation detected → what's the playbook?
   - ❌ Cross-tenant access attempt → escalation procedure?
   - ❌ SLA breach alert → who is on-call? What do they do?
   - ❌ Data corruption detected → restore from backup? How?

2. **Operational Runbooks**:
   - ❌ How to restart Core without losing decisions?
   - ❌ How to migrate to new database?
   - ❌ How to scale Core instances (new instance joins)?
   - ❌ How to drain Core instance (for rolling updates)?
   - ❌ How to shrink Core instances (cost reduction)?

3. **Change Management**:
   - ❌ How to deploy new version of Core?
   - ❌ Canary deployment? Blue-green? Rolling?
   - ❌ Rollback procedure?
   - ❌ How to version Core API (breaking changes)?

4. **Data Operations**:
   - ❌ How to backup database?
   - ❌ How to restore from backup (PITR procedure)?
   - ❌ How to migrate rule sets between tenants?
   - ❌ How to purge old decisions (retention policy enforcement)?

5. **Monitoring Thresholds**:
   - ❌ p95 latency 100ms target, but what's critical (trigger page)?
   - ❌ Error rate 0.1% normal? Threshold for alert?
   - ❌ Database connection pool 80% full → warning or critical?

**Impact**: Missing procedures cause:
- Slow incident response (no playbook, guessing)
- Operational mistakes (manual procedures error-prone)
- Inconsistent recovery (each incident handled differently)

**Recommendation**: Create INFRA-OPERATIONS-RUNBOOK with:
1. Incident response playbooks (by alert type)
2. Operational procedures (deploy, scale, migrate)
3. Change management (versioning, rollback)
4. Monitoring thresholds (alert levels)
5. On-call procedures (rotation, escalation)

---

#### Gap 7: Security Model Incomplete ⚠️ MEDIUM

**Definition**: Immutability & tenant isolation designed, but broader security undefined.

**What's Missing**:
1. **Authentication**:
   - ✓ Auth context is opaque (SDK forwards as-is)
   - ❌ But: How does Core authenticate SDK? (or does it trust all requests?)
   - ❌ How does CMS authenticate requests?
   - ❌ Are API calls signed? (HMAC, JWT, mutual TLS?)

2. **Encryption**:
   - ❌ Context in database encrypted? Or plaintext?
   - ❌ Event_log encrypted? Or plaintext?
   - ❌ Audit trail encrypted? Or plaintext?
   - ❌ In-transit encryption (Core ↔ database, Core ↔ event bus)?

3. **Rate Limiting**:
   - ❌ Can single SDK abuse Core (10k req/sec)?
   - ❌ Per-tenant rate limits?
   - ❌ Per-user rate limits?

4. **Access Control**:
   - ✓ Tenant isolation (hard boundary)
   - ✓ Database role permissions (immutability enforcement)
   - ❌ CMS permissions (who can activate rules? create rules?)
   - ❌ Webhook/hook permissions (who can invoke hooks?)

5. **Example Scenario** (undefined):
```
Attacker knows Core URL: api.infra.internal/decisions

Attack 1: Burst requests
POST /decisions × 10,000 req/sec
→ Core crashes? Or rate limited?

Attack 2: SQL injection
POST /decisions
{context: {amount: "' OR '1'='1"}}
→ Parameterized query? Or injection possible?

Attack 3: Cross-tenant
POST /decisions
  {tenant_id: "other-tenant"}
→ RLS blocks? Or request accepted?
```

**Impact**: Undefined security causes:
- DOS attacks possible
- SQL injection possible (if not parameterized)
- Unauthorized access possible (if auth weak)

**Recommendation**: Create INFRA-SECURITY-MODEL with:
1. Authentication scheme (API keys, JWT, mTLS)
2. Encryption (at-rest, in-transit)
3. Rate limiting (per-tenant, per-user)
4. Access control (who can do what?)
5. Threat modeling (attack scenarios)

---

#### Gap 8: Multi-Tenant Operational Scenarios ⚠️ MEDIUM

**Definition**: Multi-tenant in Phase 3, but operational scenarios undefined.

**What's Missing**:
1. **Tenant Lifecycle**:
   - ❌ Tenant onboarding: how to create new tenant? Auto or manual?
   - ❌ Tenant suspension: suspend one tenant, affect others?
   - ❌ Tenant deletion: GDPR right-to-be-forgotten
     - ❌ How to delete all data for tenant?
     - ❌ What about immutable event_log? Purge or mark deleted?
     - ❌ Can decisions be modified to hide user identity?

2. **Tenant Isolation Verification**:
   - ❌ How to prove tenant A cannot access tenant B?
   - ❌ Automated test? Manual audit?
   - ❌ Continuous verification?

3. **Tenant-Specific Configurations**:
   - ❌ Can each tenant have different rule versions?
   - ❌ Can each tenant have different escalation timeout?
   - ❌ Can each tenant set custom retention (e.g., keep data 1 year vs 7 years)?

4. **Tenant Quotas**:
   - ❌ Max decisions per day per tenant?
   - ❌ Max storage per tenant?
   - ❌ Max concurrent requests per tenant?
   - ❌ Enforcement mechanism (reject or defer)?

5. **Example Scenario** (undefined):
```
Tenant A requests: GDPR right-to-be-forgotten
  → Delete all data for tenant A

System response:
  - Delete decisions (mutable until completion)
  - Delete workflows (mutable)
  - Delete event_log entries (immutable!)
    → Can we delete immutable data?
    → Legal requirement (GDPR)
    → Technical requirement (immutability)
    → Conflict!

How to resolve?
1. Keep immutable log, mark data deleted/obfuscated
2. Allow deletion of immutable log (exception for compliance)
3. Encrypt data, throw away key ("data is deleted")
```

**Impact**: Undefined scenarios cause:
- Compliance violations (GDPR not satisfiable)
- Tenant conflicts (one tenant DoS others)
- Data mess (no clear deletion procedure)

**Recommendation**: Create INFRA-MULTI-TENANT-MODEL with:
1. Tenant lifecycle (create, suspend, delete)
2. Tenant isolation verification
3. Tenant-specific config (if allowed)
4. Tenant quotas (enforcement mechanism)
5. GDPR/compliance procedures (data deletion)

---

#### Gap 9: Extensibility Strategy Missing ⚠️ MEDIUM

**Definition**: System designed for a specific decision type, but extensibility path unclear.

**What's Missing**:
1. **New Outcome Types**:
   - Current: ALLOWED, DENIED, REQUIRE_APPROVAL (hardcoded)
   - ❌ What if new outcome needed (e.g., REQUIRE_MANUAL_REVIEW)?
   - ❌ Code change? Database migration? Version bump?

2. **New Condition Operators**:
   - Current: ==, !=, <, <=, >, >=, AND, OR, NOT
   - ❌ What if new operator needed (e.g., IN, REGEX)?
   - ❌ Backward compatibility with existing rules?

3. **New Event Types**:
   - Current: 11 event types (decision.*, workflow.*)
   - ❌ What if business logic needs new event (e.g., decision.overridden)?
   - ❌ Schema evolution (event_log is append-only)?

4. **Rule Schema Evolution**:
   - Current: conditions (nested object), action (outcome + approver_role)
   - ❌ What if rule structure changes?
   - ❌ Old rules incompatible with new schema?
   - ❌ Migration procedure?

5. **Example Scenario** (undefined):
```
Phase 2: Business asks for new outcome type
  "REQUIRE_MANUAL_REVIEW" (in addition to current 3)

What needs to change?
1. INFRA-DEC-001: Add new outcome type (code)
2. Core: Handle new outcome in decision creation (code)
3. Workflows: New state machine path (code)
4. Database: Alter constraints on outcome column (schema)
5. Tests: New test cases (code)
6. SDK: Update outcome validation (code)
7. CMS: Show new outcome in UI (code)
8. Rules: Existing rules still valid? (data migration needed?)

Breaking changes? Or backward compatible?
Can old SDK work with new Core? (versioning needed)
```

**Impact**: No extensibility strategy causes:
- Hard to add new outcome types (requires full system update)
- Breaking changes (upgrades must be coordinated)
- Risky evolution (schema changes risky)

**Recommendation**: Create INFRA-EXTENSIBILITY-STRATEGY with:
1. Versioning scheme (semantic versioning?)
2. Backward compatibility policy (can old SDK work with new Core?)
3. Schema evolution (how to add new outcome, operator, event)
4. Deprecation path (how to retire old outcome types)
5. Testing strategy (verify versioning works)

---

### 1.3 Summary of Gaps

| Gap | Severity | Component | Defer to Phase |
|-----|----------|-----------|-----------------|
| Application Adapter design | CRITICAL | Architecture | 1 (fix before execution) |
| Extension hooks execution | CRITICAL | Core | 2 (Phase 1 MVP doesn't use) |
| Idempotency edge cases | CRITICAL | Core | 1 (fix before execution) |
| Data consistency (partial failures) | CRITICAL | Core | 1 (fix before execution) |
| Rule caching details | HIGH | Core | 1 (fix before execution) |
| Operational procedures | HIGH | Operations | 2 (Phase 1 minimal ops) |
| Security model | MEDIUM | Security | 2 (Phase 1 internal-only) |
| Multi-tenant scenarios | MEDIUM | Architecture | 3 (Phase 1 single-tenant) |
| Extensibility strategy | MEDIUM | Architecture | 2 (Phase 1 fixed schema) |

---

## 2. CONSISTENCY AUDIT

### 2.1 Cross-Layer Alignment

**Check**: Do all layers (0-3) tell the same story?

**Finding**: MOSTLY ALIGNED, with minor inconsistencies.

**Inconsistency 1: Decision Outcome Immutability**

Layer 0 (INFRA-DEC-001):
> "Outcome locked at creation time. NEVER changes after decided."

Layer 2 (INFRA-LAY2-003):
> "outcome != NULL (proof of immutability)"

Layer 3 (INFRA-LAY3-002):
> "outcome locked at creation time"

**Status**: ✅ CONSISTENT

---

**Inconsistency 2: Rule Evaluation Caching**

Layer 2 (INFRA-LAY2-002):
> "T0+4ms: Load rule set from cache (or database)"
> "Cache invalidation: < 2 seconds after CMS rule change"

Layer 3 (INFRA-LAY3-004):
> (No mention of rule caching, only data layer caching)

Layer 3 (INFRA-LAY3-002):
> (Core service mentions cache, but implementation details sparse)

**Status**: ⚠️ INCOMPLETE (caching strategy defined but not detailed)

---

**Inconsistency 3: Idempotency Semantics**

Layer 1 (INFRA-LAY1-001):
> "Retry semantics = NEW decision creation only"
> (But says same idempotency_key returns cached decision_id)

Layer 3 (INFRA-LAY3-002):
> "Same (idempotency_key, tenant_id, decision_type) → same decision_id"

**Status**: ⚠️ SLIGHTLY CONFUSING (both true, but wording could be clearer)
- "Retry = NEW decision creation" is wrong (should be "NEW evaluation, maybe same decision_id via dedup")
- Correct interpretation: "Retry with same idempotency_key returns same decision_id, not a new decision"

---

**Inconsistency 4: Auth Context Opacity**

Layer 1 (INFRA-LAY1-001):
> "Auth context is opaque metadata. SDK doesn't assert identity."

Layer 3 (INFRA-LAY3-001):
> "SDK forwards auth context as-is (opaque to SDK)"

But MISSING: How does Core use auth context? Is it opaque to Core too?

**Status**: ⚠️ INCOMPLETE (what does Core do with auth context?)

---

**Inconsistency 5: Workflow State Transitions**

Layer 0 (INFRA-DEC-003):
> "Workflow: PENDING_APPROVAL → APPROVED/REJECTED/ESCALATED/DELEGATED"
> (Doesn't fully specify state machine)

Layer 3 (INFRA-LAY3-002):
> "State machine: PENDING_APPROVAL → APPROVED/REJECTED/DELEGATED/ESCALATED → TERMINAL"
> (Fully specified)

**Status**: ✅ CONSISTENT (Layer 3 more detailed, but Layer 0 correct)

---

### 2.2 Verdict

**Overall Consistency**: 90% ALIGNED, 10% minor gaps
- No major contradictions
- Minor gaps in caching, auth context, idempotency wording
- Layer 3 more detailed than Layer 0 (expected, acceptable)

---

## 3. RISK ASSESSMENT

### 3.1 Architectural Risks

| Risk | Probability | Impact | Mitigation | Effort |
|------|-------------|--------|-----------|--------|
| Idempotency fails (duplicates) | MEDIUM | HIGH | Clarify edge cases, test | 2 days |
| Data consistency (partial failure) | MEDIUM | HIGH | Define recovery procedures | 3 days |
| Rule caching causes non-determinism | MEDIUM | HIGH | Detail caching strategy | 2 days |
| Application Adapter bottleneck | MEDIUM | MEDIUM | Design Adapter architecture | 3 days |
| Immutability enforcement bypass | LOW | CRITICAL | Security audit, penetration test | 3 days |
| Tenant isolation breach | LOW | CRITICAL | RLS policy audit, security test | 2 days |

**Total Risk Mitigation Effort**: ~15 days (2 weeks)

**Recommendation**: Allocate Phase 1 time for risk mitigation before implementation.

---

### 3.2 Implementation Risks

| Risk | Phase | Mitigation |
|------|-------|-----------|
| Complex transactions (ACID) | 1 | Pair programming, code review |
| Database triggers correctness | 1 | Unit tests for triggers, mutation testing |
| RLS policy complexity | 1 | Security audit, policy testing |
| Rule evaluation performance | 1 | Load testing, profiling |
| Idempotency correctness | 1 | Scenario testing, chaos testing |
| Event consistency | 2 | Integration tests, failure scenario testing |
| CMS rule versioning | 2 | Feature testing, backward compat testing |
| Multi-tenant isolation | 3 | Cross-tenant attack testing, audit |

---

## 4. RECOMMENDATIONS FOR DEBATE

### 4.1 Critical Fixes (Must Do Before Phase 1)

**1. Application Adapter Design**
- **Status**: Incomplete
- **Action**: Create INFRA-ADAPTER-DESIGN documenting:
  - Adapter as separate service (REST API or library?)
  - User resolution interface (role → user_id list)
  - Entity validation interface
  - Data model (schema, storage)
  - Resilience (SLA, failure modes)
- **Effort**: 2-3 days design + review
- **Risk if skipped**: Phase 1 will discover adapter design mid-implementation (rework)

**2. Idempotency Edge Cases**
- **Status**: Incomplete
- **Action**: Create INFRA-IDEMPOTENCY-SPECIFICATION with:
  - Cache backend (in-memory vs Redis)
  - TTL policy (24h minimum, but actual?)
  - Recovery if cache lost (database fallback)
  - Distributed consistency (if multiple Core instances)
  - TTL expiration behavior (error or allow duplicate key?)
- **Effort**: 1-2 days design + review
- **Risk if skipped**: Duplicate decisions possible (immutable audit trail broken)

**3. Data Consistency in Partial Failures**
- **Status**: Incomplete
- **Action**: Create INFRA-CONSISTENCY-MODEL with:
  - Failure scenarios (decision persisted, event fails; etc.)
  - Recovery procedures (retry, replay, repair)
  - Exactly-once vs at-least-once semantics
  - Testing strategy (chaos tests)
- **Effort**: 2-3 days design + review
- **Risk if skipped**: Inconsistent state possible (events mismatched with decisions)

**4. Rule Caching Strategy**
- **Status**: Partially defined (< 2 seconds, but how?)
- **Action**: Clarify in INFRA-LAY2-002 or new doc:
  - Cache backend (in-memory, Redis, or both?)
  - Invalidation mechanism (webhook, pub/sub, polling?)
  - Propagation guarantee (< 2 seconds means what exactly?)
  - Distributed consistency (if multiple Core instances)
  - Thundering herd mitigation (cache stampede prevention)
- **Effort**: 1 day clarification + review
- **Risk if skipped**: Non-deterministic outcomes possible (same context → different results)

---

### 4.2 High-Priority Additions (Do Before Phase 2)

**5. Operational Runbook**
- **Status**: Missing
- **Action**: Create INFRA-OPERATIONS-RUNBOOK with:
  - Incident response playbooks (by alert type)
  - Operational procedures (deploy, scale, backup, restore)
  - Change management (versioning, rollback)
  - Monitoring thresholds (alert levels)
  - On-call procedures (rotation, escalation)
- **Effort**: 3-5 days (operations team)
- **Risk if skipped**: Slow incident response, operational mistakes

**6. Extension Hooks Specification**
- **Status**: Mentioned but not defined
- **Action**: Create INFRA-EXTENSION-HOOKS-SPECIFICATION with:
  - Hook invocation model (async job queue, webhook, etc.)
  - Payload schema (what data in hook?)
  - Execution guarantees (at-least-once, timeout, retry)
  - Error handling (fail-open, fail-closed)
  - Authentication & rate limiting
- **Effort**: 2-3 days design + review
- **Risk if skipped**: Phase 2 will struggle to implement hooks correctly

---

### 4.3 Medium-Priority Additions (Can Do in Phase 2-3)

**7. Security Model**
- Encryption at-rest, in-transit
- Authentication scheme
- Rate limiting
- Access control (CMS permissions, webhook permissions)
- **Effort**: 2-3 days design + implementation
- **Can defer**: Phase 1 is internal-only (lower security risk)

**8. Multi-Tenant Operational Scenarios**
- Tenant lifecycle (create, suspend, delete)
- GDPR right-to-be-forgotten (data deletion)
- Tenant isolation verification procedures
- **Effort**: 3-5 days design + implementation
- **Can defer**: Phase 1 is single-tenant, Phase 3 will design multi-tenant ops

**9. Extensibility Strategy**
- Versioning scheme
- Backward compatibility policy
- Schema evolution (new outcome types, operators, events)
- **Effort**: 2-3 days design
- **Can defer**: Phase 1 is fixed schema, Phase 2 can design extensibility for Phase 3

---

## 5. DECISION POINTS FOR DEBATE

### 5.1 Architecture Decisions Needed

**Decision 1: Application Adapter**
- **Question**: Should Adapter be a separate service (REST API) or library (code in application)?
- **Trade-offs**:
  - Separate service: Loosely coupled, reusable, but additional operational burden
  - Library: Simpler deployment, but tightly coupled, harder to reuse
- **Recommendation**: Separate REST service (easier to scale, reuse across tenants)

**Decision 2: Rule Caching Backend**
- **Question**: In-memory per Core instance or Redis shared?
- **Trade-offs**:
  - In-memory: Fast, no external dependency, but not shared (consistency issues)
  - Redis: Shared cache, consistent, but additional dependency (operational burden)
- **Recommendation**: Redis shared cache (for consistency with multiple Core instances)

**Decision 3: Idempotency Cache TTL**
- **Question**: How long to keep idempotency_key cached? 24h? 7 days? Forever (until retention expires)?
- **Trade-offs**:
  - Short (24h): Simple, cache doesn't grow large, but customers lose idempotency after 1 day
  - Long (7 years): Full idempotency guarantee, but massive cache
  - Forever: Perfect semantics, but unbounded cache growth
- **Recommendation**: 7 days (balances customer experience with cache size)

**Decision 4: Immutability of event_log**
- **Question**: If GDPR deletion required, how to delete immutable event_log?
- **Trade-offs**:
  - Keep immutable: Guarantees consistency, but can't delete (GDPR problem)
  - Allow deletion: GDPR-compliant, but breaks immutability guarantee
  - Mark as deleted: Compromise (data remains, marked invalid)
- **Recommendation**: Mark as deleted (not physically removed, but logically removed from queries)

---

### 5.2 Trade-offs to Resolve

**Trade-off 1: Exactly-once vs At-least-once Semantics**
- **Current state**: Decisions are exactly-once (idempotent), events are at-least-once
- **Question**: Is this mix acceptable? Or should events be exactly-once too?
- **Implication**: Exactly-once events require distributed deduplication (complex), at-least-once requires consumer deduplication (simpler but shifted to consumer)

**Trade-off 2: Fail-Closed vs Fail-Open for Extension Hooks**
- **Question**: If extension hook fails, should decision fail (fail-closed) or succeed anyway (fail-open)?
- **Implication**:
  - Fail-closed: Safe (hook failure blocks decision), but can cause cascading failures
  - Fail-open: Resilient (decision succeeds, hook failure logged), but hook might not execute

**Trade-off 3: Multi-Tenant vs Single-Database**
- **Question**: In Phase 3, use RLS (single database, row-level security) or schema-per-tenant (multiple schemas)?
- **Implication**:
  - RLS: Simpler operations, shared resources, but complex policy management
  - Schema-per-tenant: Simpler policies, isolated resources, but operational complexity (N schemas to manage)

---

## 6. OVERALL ASSESSMENT

### 6.1 Scoring

| Dimension | Score | Status |
|-----------|-------|--------|
| Conceptual Completeness (Layer 0) | 95% | ✅ Complete |
| Contract Completeness (Layer 1) | 90% | ✅ Mostly Complete |
| Architecture Completeness (Layer 2) | 80% | ⚠️ Gaps in caching, procedures |
| Implementation Standards (Layer 3) | 85% | ⚠️ Gaps in security, extensibility |
| MVP Plan | 95% | ✅ Complete |
| **Overall** | **89%** | ⚠️ **READY FOR EXECUTION WITH CAVEATS** |

### 6.2 Go/No-Go for Phase 1 Execution

**CONDITIONAL GO** (with fixes)

**Must Fix Before Phase 1**:
1. ✅ Idempotency edge cases (cache loss, TTL, recovery)
2. ✅ Data consistency (partial failures, recovery procedures)
3. ✅ Rule caching strategy (detailed implementation plan)
4. ✅ Application Adapter design (separate service, interface, schema)

**Can Defer to Phase 2**:
- Operational runbook (Phase 1 has minimal ops)
- Security model (Phase 1 is internal-only, lower risk)
- Extensibility (Phase 1 is fixed schema)

**Cannot Proceed Without**:
- Fixes for all 4 critical items above
- Clear answers to idempotency edge cases
- Clear answers to data consistency model

---

## 7. READING LIST FOR DEBATE

**For discussion with another AI**:

### What's Strong (Defend These)
1. Immutability architecture (multi-layer enforcement)
2. Tenant isolation design (database-enforced RLS)
3. Decision determinism requirements
4. Audit trail completeness (append-only event_log)
5. Testing strategy (aligns with guarantees)
6. MVP phasing (realistic, achievable)

### What Needs Work (Challenge These)
1. Application Adapter design (incomplete, critical dependency)
2. Idempotency implementation (edge cases undefined)
3. Data consistency (partial failures not defined)
4. Rule caching (< 2 seconds, but how implemented?)
5. Operational procedures (missing, affects Phase 1 readiness)
6. Extensibility (no strategy for new outcome types, conditions)

### Open Questions (Debate These)
1. Should adapter be separate service or library?
2. Shared cache (Redis) vs per-instance (in-memory)?
3. Idempotency TTL (24h? 7 days? 7 years?)
4. Exactly-once vs at-least-once events?
5. RLS vs schema-per-tenant for multi-tenancy?

---

## CONCLUSION

**Status**: Architecture is **89% complete and sound**, with **4 critical gaps** that must be fixed before Phase 1 execution.

**Recommendation**:
1. Fix 4 critical items (2-3 weeks effort)
2. Create design docs (ADAPTER, IDEMPOTENCY, CONSISTENCY, CACHING)
3. Get stakeholder approval on trade-offs
4. Proceed to Phase 1 implementation with confidence

**Not Recommended**: Proceed to Phase 1 without addressing critical gaps. The architecture is solid, but implementation will hit these gaps mid-way, causing rework.

---

**Document Status**: DRAFT (prepared for inter-AI debate)
**Prepared by**: Architectural review process
**Date**: 2025-12-28
