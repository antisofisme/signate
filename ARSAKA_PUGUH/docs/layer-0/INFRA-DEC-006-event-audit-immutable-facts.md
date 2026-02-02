# INFRA-DEC-006: Event & Audit as Immutable Facts

**VERSION**: Layer 0 OVERLAY
**STATUS**: LOCKED
**DATE**: 2025-01-24
**COMPLEMENTS**: INFRA-DEC-001, INFRA-LAY1-002, INFRA-LAY2-003

---

## Purpose

Dokumen ini menegaskan:
1. Event adalah FAKTA, bukan log biasa
2. Audit trail adalah BUKTI HUKUM
3. Relasi: Decision → Workflow → Event
4. Larangan mutasi terhadap fakta yang sudah terekam

---

## 1. Event Adalah Fakta, Bukan Log

### 1.1 Perbedaan Fundamental

| Aspek | Log (Debugging) | Event (Fakta) |
|-------|-----------------|---------------|
| **Tujuan** | Debug & troubleshoot | Rekam kejadian bisnis |
| **Retention** | Bisa dihapus setelah periode | Wajib dipertahankan (compliance) |
| **Mutability** | Bisa di-rotate, compress, delete | IMMUTABLE - tidak boleh diubah |
| **Format** | Freeform text | Structured, schema versioned |
| **Consumer** | Developers, ops | Business, audit, compliance, legal |
| **Reliability** | Best effort | At-least-once guarantee |
| **Legal Status** | Bukan bukti | Bukti hukum |

### 1.2 Event = Immutable Fact

```
DEFINISI:
  Event adalah FAKTA yang merepresentasikan kejadian yang sudah terjadi.

  Karakteristik FAKTA:
    1. Sudah terjadi (past tense)
    2. Tidak dapat diubah (immutable)
    3. Tidak dapat dihapus (append-only)
    4. Dapat diverifikasi (auditable)
    5. Dapat di-replay (reproducible)

CONTOH:
  Event: "decision.created"

  FAKTA yang direkam:
    - Decision dengan ID "dec-123" TELAH DIBUAT
    - Outcome ADALAH "REQUIRE_APPROVAL"
    - Rule yang match ADALAH "correction_amount_15000_cfo"
    - Timestamp kejadian ADALAH "2025-01-24T10:30:00Z"

  INI ADALAH FAKTA. Tidak bisa diubah.
  Jika salah, fakta baru dibuat (correction event), bukan edit fakta lama.
```

### 1.3 Append-Only Log

```
EVENT LOG STRUCTURE:

  ┌────────────────────────────────────────────────────────────┐
  │                    EVENT LOG (Append-Only)                 │
  │                                                            │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ Event 1: decision.created (T1)                      │  │
  │  │ { decision_id: "dec-123", outcome: "ALLOWED", ... } │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                           ↓                               │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ Event 2: decision.created (T2)                      │  │
  │  │ { decision_id: "dec-124", outcome: "DENIED", ... }  │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                           ↓                               │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ Event 3: workflow.approved (T3)                     │  │
  │  │ { workflow_id: "wf-456", approver: "CFO", ... }     │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                           ↓                               │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ Event N: ...                                         │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                                                            │
  │  OPERATIONS ALLOWED:                                      │
  │  ✅ APPEND (add new event at end)                        │
  │  ✅ READ (query events)                                   │
  │  ✅ ARCHIVE (move to cold storage, retain integrity)     │
  │                                                            │
  │  OPERATIONS FORBIDDEN:                                    │
  │  ❌ UPDATE (modify existing event)                        │
  │  ❌ DELETE (remove event)                                 │
  │  ❌ INSERT (add event in middle)                          │
  │  ❌ REORDER (change event sequence)                       │
  └────────────────────────────────────────────────────────────┘
```

---

## 2. Audit Trail Adalah Bukti Hukum

### 2.1 Legal Status of Audit Trail

```
DEFINISI:
  Audit Trail = Kronologi lengkap dari keputusan dan aksi
  yang dapat digunakan sebagai BUKTI HUKUM dalam:
    - Internal audit
    - External audit (Big 4, regulators)
    - Legal proceedings
    - Compliance verification
    - Dispute resolution

IMPLIKASI:
  1. HARUS lengkap (tidak ada gap)
  2. HARUS akurat (tidak ada distorsi)
  3. HARUS immutable (tidak dapat dimanipulasi)
  4. HARUS traceable (dari siapa, kapan, apa)
  5. HARUS accessible (dapat diakses saat diperlukan)
```

### 2.2 Audit Trail Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      AUDIT TRAIL STRUCTURE                       │
│                                                                  │
│  For every auditable action:                                    │
│                                                                  │
│  WHO:                                                           │
│    ├─ requester_user_id: Who initiated the request              │
│    ├─ approver_role: Who has authority to approve               │
│    └─ approved_by_user_id: Who actually approved (if any)       │
│                                                                  │
│  WHAT:                                                          │
│    ├─ decision_type: What kind of decision                      │
│    ├─ context: What data was used for decision                  │
│    ├─ outcome: What was the result                              │
│    └─ rule_matched: What rule determined the outcome            │
│                                                                  │
│  WHEN:                                                          │
│    ├─ requested_at: When decision was requested                 │
│    ├─ decided_at: When outcome was determined                   │
│    ├─ approved_at: When approval was given (if any)             │
│    └─ executed_at: When business action was executed            │
│                                                                  │
│  WHERE:                                                         │
│    ├─ tenant_id: Which tenant                                   │
│    ├─ source_system: Which application/module                   │
│    └─ trace_id: For distributed tracing                         │
│                                                                  │
│  WHY:                                                           │
│    ├─ rule_version: Which rule version was applied              │
│    ├─ context_summary: Sanitized business context               │
│    └─ comment: Optional human comment (approval/rejection)      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Compliance Requirements

| Regulation | Requirement | How Infra Complies |
|------------|-------------|-------------------|
| **SOX** | Complete audit trail for financial transactions | Decision + Event + Workflow history |
| **GDPR** | Data processing records | Event log with consent tracking |
| **PCI-DSS** | Access logging | Decision audit for sensitive actions |
| **HIPAA** | PHI access logging | Decision audit for health data access |
| **ISO 27001** | Information security logging | Complete event chain |
| **Local Tax Law** | Financial record retention | 7+ year event retention |

### 2.4 Audit Query Capabilities

```typescript
// Audit Query API

// Query 1: All decisions for a journal entry
const auditTrail = await infra.queryAudit({
  tenant_id: "hotel-123",
  filters: {
    decision_type: "accounting.journal_approval",
    context_contains: { journal_id: "jrnl-456" }
  },
  include: ["decision", "workflow", "events"]
});

// Returns:
{
  decision: {
    decision_id: "dec-789",
    outcome: "REQUIRE_APPROVAL",
    rule_matched: "correction_amount_15000_cfo",
    requested_at: "2025-01-24T10:30:00Z"
  },
  workflow: {
    workflow_id: "wf-012",
    state: "APPROVED",
    approver_role: "CFO",
    approved_by_user_id: "user-cfo-001",
    approved_at: "2025-01-24T14:45:00Z"
  },
  events: [
    { event_type: "decision.created", occurred_at: "T1" },
    { event_type: "workflow.created", occurred_at: "T2" },
    { event_type: "workflow.pending_approval", occurred_at: "T3" },
    { event_type: "workflow.approved", occurred_at: "T4" },
    { event_type: "workflow.completed", occurred_at: "T5" }
  ]
}

// Query 2: Who approved what in date range
const approvals = await infra.queryAudit({
  tenant_id: "hotel-123",
  filters: {
    event_type: "workflow.approved",
    occurred_after: "2025-01-01",
    occurred_before: "2025-01-31"
  }
});

// Query 3: All denials (for anomaly detection)
const denials = await infra.queryAudit({
  tenant_id: "hotel-123",
  filters: {
    outcome: "DENIED",
    occurred_after: "2025-01-24T00:00:00Z"
  }
});
```

---

## 3. Relasi: Decision → Workflow → Event

### 3.1 Entity Relationship

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTITY RELATIONSHIP                           │
│                                                                  │
│   DECISION (Aggregate Root)                                     │
│   └─ decision_id (PK)                                           │
│   └─ outcome: ALLOWED | DENIED | REQUIRE_APPROVAL               │
│   └─ rule_matched                                               │
│   └─ context (sanitized)                                        │
│   └─ IMMUTABLE after creation                                   │
│       │                                                          │
│       │ 1:0..1                                                   │
│       │ (Decision dapat memiliki 0 atau 1 Workflow)             │
│       ▼                                                          │
│   WORKFLOW (Child of Decision)                                  │
│   └─ workflow_id (PK)                                           │
│   └─ decision_id (FK) ────────────────► DECISION                │
│   └─ state: PENDING | APPROVED | REJECTED | ...                 │
│   └─ approver_role                                              │
│   └─ STATE MUTABLE, decision_id IMMUTABLE                       │
│       │                                                          │
│       │ 1:N                                                      │
│       │ (Workflow memiliki banyak state transitions)            │
│       ▼                                                          │
│   WORKFLOW_HISTORY (Audit Trail)                                │
│   └─ history_id (PK)                                            │
│   └─ workflow_id (FK) ────────────────► WORKFLOW                │
│   └─ previous_state                                             │
│   └─ new_state                                                  │
│   └─ timestamp                                                  │
│   └─ actor_user_id                                              │
│   └─ IMMUTABLE                                                  │
│                                                                  │
│   EVENT (Derived from State Changes)                            │
│   └─ event_id (PK)                                              │
│   └─ aggregate_id (decision_id or workflow_id)                  │
│   └─ event_type                                                 │
│   └─ payload (snapshot of state at time of event)               │
│   └─ occurred_at                                                │
│   └─ IMMUTABLE                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Event Chain (Ordered Sequence)

```
DECISION LIFECYCLE EVENTS:

  T1: decision.created
      ├─ decision_id assigned
      ├─ outcome determined
      └─ rule_matched recorded

  [IF outcome = REQUIRE_APPROVAL]

  T2: workflow.created
      ├─ workflow_id assigned
      ├─ decision_id linked
      └─ initial_state = PENDING_APPROVAL

  T3: workflow.pending_approval
      ├─ approver_role identified
      └─ notification triggered

  [APPROVAL PATH]

  T4a: workflow.approved
       ├─ approved_by_user_id recorded
       ├─ state = APPROVED
       └─ comment captured

  OR

  T4b: workflow.rejected
       ├─ rejected_by_user_id recorded
       ├─ state = REJECTED
       └─ reason captured

  OR

  T4c: workflow.escalated
       ├─ escalation_target_role
       ├─ state = ESCALATED
       └─ escalation_reason

  OR

  T4d: workflow.delegated
       ├─ delegated_to_user_id
       ├─ state = DELEGATED
       └─ delegation_reason

  T5: workflow.completed
      ├─ final_state recorded
      ├─ total_duration_seconds
      └─ state_transitions summary

GUARANTEE:
  Events are ALWAYS in chronological order within aggregate.
  T1 < T2 < T3 < T4 < T5 (strict ordering)
```

### 3.3 Event Derivation Rules

```
EVENT DERIVATION:

  State Change              →    Event Emitted
  ─────────────────────────────────────────────
  Decision created          →    decision.created
  Decision.outcome=ALLOWED  →    decision.allowed
  Decision.outcome=DENIED   →    decision.denied
  Decision.outcome=REQUIRE  →    decision.requires_approval
  Workflow created          →    workflow.created
  Workflow.state=PENDING    →    workflow.pending_approval
  Workflow.state=APPROVED   →    workflow.approved
  Workflow.state=REJECTED   →    workflow.rejected
  Workflow.state=ESCALATED  →    workflow.escalated
  Workflow.state=DELEGATED  →    workflow.delegated
  Workflow terminal state   →    workflow.completed

INVARIANT:
  Setiap state change PASTI menghasilkan event.
  Tidak ada state change tanpa event (observability guarantee).
```

---

## 4. Larangan Mutasi Terhadap Fakta

### 4.1 Immutability Rules (LOCKED)

```
RULE IM-1: Decision Outcome TIDAK PERNAH berubah
  decision.outcome = "ALLOWED"  →  FOREVER "ALLOWED"
  decision.outcome = "DENIED"   →  FOREVER "DENIED"
  decision.outcome = "REQUIRE_APPROVAL"  →  FOREVER "REQUIRE_APPROVAL"

  Workflow state dapat berubah (PENDING → APPROVED),
  tapi decision.outcome TETAP "REQUIRE_APPROVAL".

RULE IM-2: Event content TIDAK PERNAH berubah
  event.payload = { ... }  →  FOREVER { ... }
  event.metadata = { ... }  →  FOREVER { ... }
  event.occurred_at = T1  →  FOREVER T1

RULE IM-3: Workflow history TIDAK PERNAH dihapus
  Setiap state transition WAJIB terekam.
  Tidak ada "gap" dalam history.

RULE IM-4: Audit trail TIDAK PERNAH di-truncate
  Sebelum retention period berakhir,
  audit trail WAJIB lengkap dan accessible.

RULE IM-5: Context snapshot TIDAK PERNAH di-update
  Context yang digunakan untuk decision = snapshot at decision time.
  Jika context berubah kemudian, decision TIDAK re-evaluated.
```

### 4.2 Database Enforcement

```sql
-- DECISION TABLE: Immutable after INSERT
CREATE TABLE decisions (
  decision_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  decision_type VARCHAR(100) NOT NULL,
  outcome VARCHAR(20) NOT NULL CHECK (outcome IN ('ALLOWED', 'DENIED', 'REQUIRE_APPROVAL')),
  rule_matched VARCHAR(100),
  rule_version VARCHAR(20),
  context JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- NO updated_at column (immutable)
  -- NO UPDATE trigger allowed
);

-- PREVENT UPDATE on decisions
CREATE OR REPLACE FUNCTION prevent_decision_update()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Decisions are immutable. UPDATE is forbidden.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_decision_update
  BEFORE UPDATE ON decisions
  FOR EACH ROW
  EXECUTE FUNCTION prevent_decision_update();

-- PREVENT DELETE on decisions
CREATE OR REPLACE FUNCTION prevent_decision_delete()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Decisions are immutable. DELETE is forbidden.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_decision_delete
  BEFORE DELETE ON decisions
  FOR EACH ROW
  EXECUTE FUNCTION prevent_decision_delete();

-- EVENT LOG TABLE: Append-only
CREATE TABLE event_log (
  event_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  event_type VARCHAR(50) NOT NULL,
  aggregate_id UUID NOT NULL,
  aggregate_type VARCHAR(20) NOT NULL,
  payload JSONB NOT NULL,
  metadata JSONB,
  occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
  recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  schema_version VARCHAR(10) NOT NULL DEFAULT '1.0'

  -- NO updated_at (append-only)
);

-- PREVENT UPDATE on event_log
CREATE TRIGGER no_event_update
  BEFORE UPDATE ON event_log
  FOR EACH ROW
  EXECUTE FUNCTION prevent_event_update();

-- PREVENT DELETE on event_log (except archival after retention)
CREATE TRIGGER no_event_delete
  BEFORE DELETE ON event_log
  FOR EACH ROW
  EXECUTE FUNCTION prevent_event_delete();
```

### 4.3 Application Code Enforcement

```typescript
// SDK Level: Prevent modification attempts

class Decision {
  private readonly _decision_id: string;
  private readonly _outcome: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL";
  private readonly _rule_matched: string;
  private readonly _context: Readonly<object>;
  private readonly _created_at: Date;

  constructor(data: DecisionData) {
    this._decision_id = data.decision_id;
    this._outcome = data.outcome;
    this._rule_matched = data.rule_matched;
    this._context = Object.freeze(data.context); // Frozen
    this._created_at = data.created_at;

    // Freeze the entire object
    Object.freeze(this);
  }

  // Only getters, no setters
  get decision_id(): string { return this._decision_id; }
  get outcome(): string { return this._outcome; }
  get rule_matched(): string { return this._rule_matched; }
  get context(): object { return this._context; }
  get created_at(): Date { return this._created_at; }

  // Prevent any modification
  // TypeScript will error if someone tries to assign
}

// Core Level: Reject update requests
class DecisionRepository {
  async create(decision: Decision): Promise<Decision> {
    // INSERT only
    return await db.insert("decisions", decision);
  }

  async getById(id: string): Promise<Decision | null> {
    // SELECT only
    return await db.findOne("decisions", { decision_id: id });
  }

  // NO update method exists
  // NO delete method exists

  // If called via reflection or hack:
  async update(): Promise<never> {
    throw new ImmutabilityViolationError("Decisions cannot be updated");
  }

  async delete(): Promise<never> {
    throw new ImmutabilityViolationError("Decisions cannot be deleted");
  }
}
```

### 4.4 Monitoring for Immutability Violations

```yaml
# Prometheus Alerts for Immutability Violations

groups:
  - name: immutability_violations
    rules:
      - alert: DecisionUpdateAttempt
        expr: rate(infra_decision_update_attempts_total[5m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Decision update attempt detected"
          description: "SECURITY INCIDENT: Attempt to modify immutable decision"

      - alert: EventLogModificationAttempt
        expr: rate(infra_event_modification_attempts_total[5m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Event log modification attempt detected"
          description: "SECURITY INCIDENT: Attempt to modify append-only event log"

      - alert: AuditTrailGap
        expr: infra_audit_trail_gaps_detected > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Audit trail gap detected"
          description: "COMPLIANCE VIOLATION: Gap in audit trail sequence"
```

---

## 5. Correction Events (Bukan Update)

### 5.1 Ketika "Kesalahan" Terjadi

```
PRINSIP:
  Fakta yang sudah terekam TIDAK DAPAT diubah.
  Jika ada "kesalahan", buat FAKTA BARU yang merekam koreksi.

SKENARIO:
  Decision dibuat dengan context yang salah (user error).

WRONG:
  UPDATE decision SET context = {...} WHERE decision_id = 'dec-123'
  ❌ IMMUTABILITY VIOLATION

CORRECT:
  1. Decision lama tetap ada (immutable)
  2. User membuat request BARU dengan context yang benar
  3. Decision BARU dibuat dengan decision_id BARU
  4. Audit trail shows:
     - dec-123: ALLOWED (original, context X)
     - dec-456: DENIED (new, context Y)
  5. Business logic uses LATEST decision (dec-456)
```

### 5.2 Correction Event Pattern

```typescript
// Correction Event for administrative changes

Event: "decision.correction_note_added"
{
  event_id: "evt-999",
  event_type: "decision.correction_note_added",
  aggregate_id: "dec-123",  // References original decision
  payload: {
    original_decision_id: "dec-123",
    correction_note: "Original context was incorrect. See decision dec-456 for corrected evaluation.",
    correcting_decision_id: "dec-456",
    added_by_user_id: "admin-001",
    reason: "User reported incorrect amount in original request"
  },
  occurred_at: "2025-01-24T16:00:00Z"
}

// This is ADDITIVE, not MUTATIVE
// Original decision (dec-123) remains unchanged
// New event records the correction relationship
// Audit trail is complete and shows correction history
```

---

## 6. Retention & Archival

### 6.1 Retention Policy

```
HOT STORAGE (Active Query):
  Period: 0 - 90 days
  Location: Primary database
  SLA: Query < 500ms
  Full fidelity, all indexes

WARM STORAGE (Archive Query):
  Period: 90 days - 2 years
  Location: Object storage (S3/R2)
  SLA: Query < 5s (batch job)
  Compressed, queryable

COLD STORAGE (Compliance Archive):
  Period: 2 years - 7 years
  Location: Long-term archive (Glacier)
  SLA: Query < 24h (retrieval request)
  Encrypted, tamper-evident

DELETION:
  After retention period: GDPR-compliant deletion
  Audit log of deletion retained
  Hash of deleted records retained (integrity verification)
```

### 6.2 Archival Process

```
ARCHIVAL INVARIANTS:

1. DATA INTEGRITY
   - Hash of records before and after archival must match
   - Checksums verified during transfer
   - Tamper-evident seal applied

2. COMPLETENESS
   - All events for tenant archived together
   - No partial archival allowed
   - Verification count matches source

3. ACCESSIBILITY
   - Archived data must be retrievable
   - Retrieval process documented
   - Tested quarterly

4. COMPLIANCE
   - Retention period enforced
   - Early deletion = compliance violation
   - Legal hold support

ARCHIVAL FLOW:
  1. Mark records for archival (soft flag)
  2. Create archive bundle (encrypted)
  3. Generate integrity checksum
  4. Transfer to warm/cold storage
  5. Verify transfer (checksum match)
  6. Update index (point to archive)
  7. Remove from hot storage (after verification)
```

---

## 7. Summary: Immutability adalah Non-Negotiable

### 7.1 Core Principles

```
PRINCIPLE 1: Events are FACTS
  - Past tense, immutable, verifiable
  - Not debugging logs
  - Legal evidence quality

PRINCIPLE 2: Audit Trail is LEGAL EVIDENCE
  - WHO, WHAT, WHEN, WHERE, WHY
  - Complete, accurate, immutable
  - Compliance-ready

PRINCIPLE 3: Decision → Workflow → Event Chain
  - Clear relationship
  - Ordered sequence
  - No gaps allowed

PRINCIPLE 4: No Mutation of Facts
  - Database triggers prevent UPDATE/DELETE
  - Application code enforces immutability
  - Monitoring detects violations

PRINCIPLE 5: Corrections are Additive
  - Never modify existing fact
  - Add new fact that references correction
  - Audit trail shows full history
```

### 7.2 Enforcement Checklist

```markdown
IMMUTABILITY CHECKLIST:

Database Layer:
□ Decision table has no UPDATE trigger
□ Event log table has no UPDATE trigger
□ DELETE triggers only allow after retention
□ Audit trail table is append-only

Application Layer:
□ Decision objects are frozen (Object.freeze)
□ Repository has no update/delete methods
□ SDK returns immutable decision objects
□ Context is snapshot, not reference

Monitoring Layer:
□ Alert on UPDATE attempts
□ Alert on DELETE attempts
□ Alert on audit trail gaps
□ Alert on sequence violations

Compliance Layer:
□ Retention policy enforced
□ Archival process documented
□ Retrieval process tested
□ Legal hold supported
```

---

## 8. Failure Mode as Law (LOCKED)

### 8.1 Prinsip Hukum Failure Mode

```
DEKLARASI HUKUM:

  Failure mode BUKAN catatan teknis.
  Failure mode ADALAH HUKUM SISTEM.

  Setiap failure scenario memiliki RESPONS WAJIB yang:
    - TIDAK dapat di-override
    - TIDAK dapat di-bypass
    - TIDAK dapat di-ignore
```

### 8.2 Failure Mode Laws (LOCKED)

```
LAW-FAIL-1: PDP Failure → DENY (Fail-Closed)
  ─────────────────────────────────────────────
  KONDISI:
    - PDP tidak dapat mengevaluasi rule
    - Database tidak accessible
    - Rule configuration corrupt
    - Timeout pada rule evaluation

  RESPONS WAJIB:
    outcome = DENIED
    reason = "SYSTEM_FAILURE_FAILCLOSED"
    logged_as = SECURITY_EVENT

  ALASAN HUKUM:
    - Fail-open = security vulnerability
    - Ketidakpastian ≠ izin
    - Lebih baik menolak dengan aman daripada mengizinkan dengan risiko

  CODE PATTERN:
    try {
      outcome = await evaluateRules(context);
    } catch (error) {
      outcome = "DENIED";  // ← WAJIB, bukan "ALLOWED"
      reason = "SYSTEM_FAILURE_FAILCLOSED";
      await auditLog.security({
        event: "PDP_FAILURE_FAILCLOSED",
        error: error.message
      });
    }

LAW-FAIL-2: Workflow Timeout → ESCALATE atau DENY
  ─────────────────────────────────────────────
  KONDISI:
    - Approval tidak diberikan dalam timeout period
    - Approver tidak merespons

  RESPONS WAJIB (pilih salah satu, dikonfigurasi per rule):

    OPTION A: ESCALATE
      - Workflow di-escalate ke escalation_target_role
      - Timer reset untuk level berikutnya
      - Event: workflow.escalated

    OPTION B: DENY (jika sudah level tertinggi)
      - Workflow di-reject otomatis
      - Reason: "TIMEOUT_EXPIRED"
      - Event: workflow.rejected (reason: timeout)

  DILARANG:
    - Workflow tetap PENDING selamanya
    - Approval otomatis karena timeout
    - Silent ignore

  CODE PATTERN:
    async function handleTimeout(workflow) {
      if (workflow.can_escalate) {
        await escalateWorkflow(workflow);  // ← ESCALATE
      } else {
        await rejectWorkflow(workflow, "TIMEOUT_EXPIRED");  // ← DENY
      }
      // NEVER: leave as PENDING forever
    }

LAW-FAIL-3: Event Publish Failure → Decision Tetap Sah
  ─────────────────────────────────────────────
  KONDISI:
    - Event bus tidak available
    - Kafka/RabbitMQ down
    - Network partition

  RESPONS WAJIB:
    - Decision TETAP SAH dan TERSIMPAN
    - Event di-queue untuk retry
    - Eventual consistency accepted

  ALASAN HUKUM:
    - Decision adalah FAKTA, tidak tergantung event publish
    - Event adalah NOTIFIKASI, bukan validator
    - Decoupling: Decision ≠ Event delivery

  GUARANTEE:
    Decision stored in DB ✓
    Event queued for retry ✓
    No decision loss ✓

  CODE PATTERN:
    async function createDecision(request) {
      // STEP 1: Create decision (SYNCHRONOUS, BLOCKING)
      const decision = await db.insert("decisions", {...});

      // STEP 2: Publish event (ASYNC, NON-BLOCKING)
      try {
        await eventBus.publish("decision.created", decision);
      } catch (error) {
        // Event publish failed, but decision is VALID
        await retryQueue.enqueue({
          event: "decision.created",
          payload: decision,
          retry_count: 0
        });
        // Decision is STILL VALID
      }

      return decision;  // ← Return decision even if event failed
    }

LAW-FAIL-4: Audit Write Failure → SYSTEM HALT (Severity-1)
  ─────────────────────────────────────────────
  KONDISI:
    - Audit log tidak dapat ditulis
    - Audit database full/corrupt
    - Audit storage failure

  RESPONS WAJIB:
    - SYSTEM HALT untuk operasi yang memerlukan audit
    - Request DITOLAK sampai audit recovered
    - Alert SEVERITY-1 triggered
    - On-call engineer notified immediately

  ALASAN HUKUM:
    - Operasi tanpa audit = TIDAK SAH secara hukum
    - Audit gap = compliance violation
    - Lebih baik halt daripada operasi tanpa bukti

  DILARANG:
    - Proceed tanpa audit
    - Silent skip audit write
    - Buffering tanpa batas

  CODE PATTERN:
    async function createDecisionWithAudit(request) {
      // STEP 1: Write audit FIRST
      try {
        await auditLog.write({
          operation: "decision.create",
          request: sanitize(request),
          timestamp: now()
        });
      } catch (auditError) {
        // AUDIT FAILURE = SYSTEM HALT
        await alerting.critical({
          event: "AUDIT_WRITE_FAILURE",
          severity: 1,
          impact: "SYSTEM_HALT"
        });

        throw new SystemHaltError(
          "Audit write failed. System halted. " +
          "Decision creation blocked until audit recovered."
        );
      }

      // STEP 2: Only proceed if audit succeeded
      const decision = await db.insert("decisions", {...});
      return decision;
    }
```

### 8.3 Failure Mode Hierarchy

```
HIERARKI SEVERITY:

  SEVERITY-1 (SYSTEM HALT):
    - Audit write failure
    - Tenant isolation breach
    - Immutability violation detected

  SEVERITY-2 (DEGRADED):
    - Event publish failure (retry queued)
    - Non-critical database timeout

  SEVERITY-3 (NORMAL FAILURE):
    - Rule evaluation failure → DENY
    - Workflow timeout → ESCALATE/DENY

RESPONSE TIME SLA:

  | Severity | Detection | Response | Resolution |
  |----------|-----------|----------|------------|
  | 1        | Immediate | < 5 min  | < 1 hour   |
  | 2        | < 1 min   | < 15 min | < 4 hours  |
  | 3        | < 5 min   | < 1 hour | < 24 hours |
```

### 8.4 Failure Mode sebagai Invariant

```
INVARIANT YANG TIDAK BOLEH DILANGGAR:

  INV-FAIL-1: Fail-Closed Default
    Setiap uncertainty → DENY
    TIDAK ADA uncertainty → ALLOW

  INV-FAIL-2: Audit-First Guarantee
    Audit ditulis SEBELUM operasi
    Operasi TIDAK PERNAH tanpa audit

  INV-FAIL-3: Decision Independence
    Decision validity ≠ Event delivery success
    Decision tetap sah meskipun event gagal

  INV-FAIL-4: No Silent Failure
    Setiap failure WAJIB di-log
    Setiap failure WAJIB di-alert (sesuai severity)
    TIDAK ADA failure yang di-ignore

VALIDATION:

  Setiap implementasi WAJIB diuji:
    □ PDP failure → DENY?
    □ Workflow timeout → ESCALATE atau DENY?
    □ Event failure → Decision tetap sah?
    □ Audit failure → SYSTEM HALT?

  Test case coverage untuk setiap failure mode = MANDATORY
```

### 8.5 Summary: Failure Mode adalah Hukum

```
┌─────────────────────────────────────────────────────────────┐
│                 FAILURE MODE AS LAW                          │
│                                                              │
│  LAW-FAIL-1: PDP Failure → DENY (fail-closed)               │
│              Ketidakpastian bukan izin.                      │
│                                                              │
│  LAW-FAIL-2: Workflow Timeout → ESCALATE atau DENY          │
│              Tidak ada approval diam-diam.                   │
│                                                              │
│  LAW-FAIL-3: Event Failure → Decision tetap sah             │
│              Decision adalah fakta, bukan notifikasi.        │
│                                                              │
│  LAW-FAIL-4: Audit Failure → SYSTEM HALT                    │
│              Operasi tanpa bukti tidak sah.                  │
│                                                              │
│  PRINSIP: Lebih baik gagal dengan aman                      │
│           daripada sukses dengan risiko.                     │
└─────────────────────────────────────────────────────────────┘
```

---

**INFRA-DEC-006: LAYER 0 OVERLAY - LOCKED**

*Event adalah fakta. Audit adalah bukti hukum. Immutability adalah non-negotiable.*
*Failure mode adalah hukum sistem, bukan catatan teknis.*
