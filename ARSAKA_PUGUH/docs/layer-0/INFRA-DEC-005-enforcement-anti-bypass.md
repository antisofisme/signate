# INFRA-DEC-005: Enforcement & Anti-Bypass Rules

**VERSION**: Layer 0 OVERLAY
**STATUS**: LOCKED
**DATE**: 2025-01-24
**COMPLEMENTS**: INFRA-DEC-001, INFRA-DEC-002, INFRA-DEC-003, INFRA-DEC-004

---

## Purpose

Dokumen ini mendefinisikan:
1. Aksi yang WAJIB melalui PEP (Policy Enforcement Point)
2. Definisi bypass sebagai bug kritikal
3. Pola arsitektur benar vs salah
4. Guard rails untuk mencegah bypass

---

## 1. Definisi: Apa itu Bypass?

### 1.1 Definisi Formal

```
BYPASS = Eksekusi aksi yang memerlukan keputusan TANPA melalui PEP

Matematika:
  Aksi A memerlukan keputusan D
  PEP menghasilkan D

  BYPASS terjadi JIKA:
    A dieksekusi TANPA D
    ATAU
    A dieksekusi dengan D yang di-forge (tidak dari PEP)
    ATAU
    A dieksekusi dengan D dari tenant lain
```

### 1.2 Klasifikasi Bypass

| Tipe | Deskripsi | Severity |
|------|-----------|----------|
| **Direct Bypass** | Application memanggil Core langsung tanpa SDK | CRITICAL |
| **Skip Bypass** | Application mengeksekusi tanpa memanggil SDK sama sekali | CRITICAL |
| **Forge Bypass** | Application membuat decision object palsu | CRITICAL |
| **Tenant Bypass** | Application menggunakan decision dari tenant lain | CRITICAL |
| **Cache Bypass** | Application menggunakan decision expired/invalid | HIGH |
| **Outcome Bypass** | Application mengabaikan decision outcome | CRITICAL |

### 1.3 Bypass = Bug Kritikal

```
KEBIJAKAN:
  Bypass terdeteksi = Bug SEVERITY-1 (Critical)

  Response Time:
    - Detection: Immediately (real-time monitoring)
    - Investigation: < 1 hour
    - Fix deployment: < 4 hours
    - Post-mortem: < 24 hours

  Impact:
    - Audit trail incomplete = compliance violation
    - Authorization bypassed = security incident
    - Data integrity compromised = regulatory risk
```

---

## 2. Aksi yang WAJIB Melalui PEP

### 2.1 Daftar Aksi Wajib (Per Domain)

#### Accounting Domain

| Aksi | decision_type | Alasan |
|------|--------------|--------|
| Approve journal entry | `accounting.journal_approval` | Financial control |
| Post to closed period | `accounting.period_posting_allowed` | Period lock enforcement |
| Override budget limit | `accounting.budget_override` | Spending control |
| Void posted transaction | `accounting.void_allowed` | Reversal control |
| Adjust reconciliation | `accounting.reconciliation_adjust` | Bank rec integrity |

#### PMS Domain

| Aksi | decision_type | Alasan |
|------|--------------|--------|
| Reassign occupied room | `pms.room_reassignment_allowed` | Guest impact |
| Override room rate | `pms.rate_override` | Revenue control |
| Extend checkout time | `pms.checkout_extension` | Inventory impact |
| Apply discount > threshold | `pms.discount_approval` | Revenue leakage |
| Upgrade room free | `pms.free_upgrade` | Revenue impact |

#### Inventory Domain

| Aksi | decision_type | Alasan |
|------|--------------|--------|
| Stock movement below safety | `inventory.stock_movement_allowed` | Safety stock protection |
| Write-off inventory | `inventory.writeoff_approval` | Asset control |
| Transfer between locations | `inventory.transfer_approval` | Location control |
| Adjust stock count | `inventory.adjustment_approval` | Audit trail |

#### Procurement Domain

| Aksi | decision_type | Alasan |
|------|--------------|--------|
| Approve PO > threshold | `procurement.po_approval_required` | Spending control |
| Change approved vendor | `procurement.vendor_change` | Vendor management |
| Emergency purchase | `procurement.emergency_approval` | Expedited control |
| Exceed budget line | `procurement.budget_exceed` | Budget control |

#### HR Domain

| Aksi | decision_type | Alasan |
|------|--------------|--------|
| Approve overtime > limit | `hr.overtime_approval` | Labor cost control |
| Salary adjustment | `hr.salary_change_approval` | Compensation control |
| Terminate employee | `hr.termination_approval` | Legal compliance |
| Access sensitive data | `hr.sensitive_data_access` | Privacy control |

### 2.2 Kriteria: Aksi Memerlukan Decision

```
Aksi A WAJIB melalui PEP JIKA memenuhi SALAH SATU kriteria:

1. FINANCIAL IMPACT
   - Melibatkan uang > threshold
   - Mengubah financial record
   - Mempengaruhi revenue/cost

2. AUTHORIZATION REQUIRED
   - Memerlukan approval dari role tertentu
   - Melanggar policy default
   - Override system constraint

3. AUDIT REQUIREMENT
   - Regulatory requirement untuk record
   - Compliance audit point
   - Legal evidence requirement

4. IRREVERSIBLE ACTION
   - Tidak bisa di-undo
   - Permanent state change
   - External system impact

5. MULTI-PARTY IMPACT
   - Mempengaruhi guest/customer
   - Mempengaruhi vendor/supplier
   - Mempengaruhi employee
```

### 2.3 Aksi yang TIDAK Perlu Decision

| Aksi | Alasan Exempted |
|------|-----------------|
| View report | Read-only, no mutation |
| Search/filter data | Query only |
| Export data (non-sensitive) | No state change |
| Update user preference | Personal, no business impact |
| Send notification | Informational only |
| Generate preview | No persistence |

---

## 3. Arsitektur Benar vs Salah

### 3.1 Arsitektur BENAR: Via PEP

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│                                                                  │
│   User Request                                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  Application Service                                    │   │
│   │                                                         │   │
│   │  async function approveJournal(journalId, userId) {    │   │
│   │                                                         │   │
│   │    // STEP 1: Build context                            │   │
│   │    const journal = await journalRepo.get(journalId);   │   │
│   │    const context = {                                   │   │
│   │      journal_entry_amount: journal.amount,             │   │
│   │      journal_entry_type: journal.type                  │   │
│   │    };                                                  │   │
│   │                                                         │   │
│   │    // STEP 2: Call PEP (SDK) - MANDATORY               │   │
│   │    const decision = await infra.createDecision({       │   │
│   │      decision_type: "accounting.journal_approval",     │   │
│   │      tenant_id: getCurrentTenant(),                    │   │
│   │      context: context                                  │   │
│   │    });                                                 │   │
│   │                                                         │   │
│   │    // STEP 3: Enforce outcome                          │   │
│   │    if (decision.outcome === "ALLOWED") {               │   │
│   │      await journalRepo.approve(journalId);             │   │
│   │    } else if (decision.outcome === "DENIED") {         │   │
│   │      throw new ForbiddenError(decision.reason);        │   │
│   │    } else {                                            │   │
│   │      await workflowAdapter.createTask(                 │   │
│   │        decision.workflow_id                            │   │
│   │      );                                                │   │
│   │    }                                                   │   │
│   │  }                                                     │   │
│   └────────────────────────────────────────────────────────┘   │
│                          │                                      │
└──────────────────────────│──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PEP (SDK)                                │
│  - Validate request                                             │
│  - Sanitize context                                             │
│  - Forward to Core                                              │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PDP (INFRA CORE)                           │
│  - Evaluate rules                                               │
│  - Determine outcome                                            │
│  - Record decision (immutable)                                  │
│  - Emit events                                                  │
└─────────────────────────────────────────────────────────────────┘

✅ CORRECT: Decision obtained before execution
✅ CORRECT: Outcome enforced by application
✅ CORRECT: Audit trail complete
```

### 3.2 Arsitektur SALAH: Skip Bypass

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│                                                                  │
│   User Request                                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  Application Service                                    │   │
│   │                                                         │   │
│   │  async function approveJournalWRONG(journalId, userId) │   │
│   │  {                                                      │   │
│   │    // ❌ NO DECISION REQUESTED                          │   │
│   │    // ❌ DIRECT EXECUTION = BYPASS                      │   │
│   │                                                         │   │
│   │    const journal = await journalRepo.get(journalId);   │   │
│   │    await journalRepo.approve(journalId);  // ❌ BYPASS │   │
│   │  }                                                      │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

❌ WRONG: No decision obtained
❌ WRONG: No PEP involvement
❌ WRONG: No audit trail
❌ WRONG: Authorization bypassed
❌ SEVERITY-1 BUG
```

### 3.3 Arsitektur SALAH: Direct Core Call

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  Application Service                                    │   │
│   │                                                         │   │
│   │  async function approveJournalWRONG(journalId, userId) │   │
│   │  {                                                      │   │
│   │    // ❌ CALLING CORE DIRECTLY = BYPASS                 │   │
│   │    // ❌ SDK VALIDATION SKIPPED                         │   │
│   │                                                         │   │
│   │    const decision = await fetch(                        │   │
│   │      "http://infra-core:8000/v1/decisions",  // ❌     │   │
│   │      {                                                  │   │
│   │        method: "POST",                                  │   │
│   │        body: JSON.stringify({ ... })                   │   │
│   │      }                                                  │   │
│   │    );                                                   │   │
│   │  }                                                      │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼ (direct call, bypassing SDK)
┌─────────────────────────────────────────────────────────────────┐
│                      PDP (INFRA CORE)                           │
└─────────────────────────────────────────────────────────────────┘

❌ WRONG: SDK bypassed
❌ WRONG: Context not sanitized
❌ WRONG: Auth context not injected properly
❌ WRONG: No SDK validation
❌ SEVERITY-1 BUG
```

### 3.4 Arsitektur SALAH: Outcome Ignored

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  Application Service                                    │   │
│   │                                                         │   │
│   │  async function approveJournalWRONG(journalId, userId) │   │
│   │  {                                                      │   │
│   │    // Decision requested (correct)                      │   │
│   │    const decision = await infra.createDecision({...}); │   │
│   │                                                         │   │
│   │    // ❌ OUTCOME IGNORED = BYPASS                       │   │
│   │    // ❌ ALWAYS EXECUTE REGARDLESS OF OUTCOME           │   │
│   │                                                         │   │
│   │    await journalRepo.approve(journalId);  // ❌ BYPASS │   │
│   │  }                                                      │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

❌ WRONG: Decision outcome ignored
❌ WRONG: DENIED outcome not enforced
❌ WRONG: REQUIRE_APPROVAL not handled
❌ SEVERITY-1 BUG
```

### 3.5 Arsitektur SALAH: Forged Decision

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  Application Service                                    │   │
│   │                                                         │   │
│   │  async function approveJournalWRONG(journalId, userId) │   │
│   │  {                                                      │   │
│   │    // ❌ FORGED DECISION = BYPASS                       │   │
│   │    // ❌ DECISION NOT FROM PDP                          │   │
│   │                                                         │   │
│   │    const fakeDecision = {                              │   │
│   │      decision_id: "fake-123",                          │   │
│   │      outcome: "ALLOWED",  // ❌ FORGED                 │   │
│   │      rule_matched: "none"                              │   │
│   │    };                                                   │   │
│   │                                                         │   │
│   │    if (fakeDecision.outcome === "ALLOWED") {           │   │
│   │      await journalRepo.approve(journalId);  // ❌      │   │
│   │    }                                                    │   │
│   │  }                                                      │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

❌ WRONG: Decision forged locally
❌ WRONG: No PDP involvement
❌ WRONG: No audit trail in Infra
❌ WRONG: Security violation
❌ SEVERITY-1 BUG
```

---

## 4. Guard Rails: Mencegah Bypass

### 4.1 Code Review Checklist

```markdown
## Bypass Prevention Checklist (Code Review)

### For Every Mutation That Requires Authorization:

- [ ] Is `infra.createDecision()` called BEFORE the mutation?
- [ ] Is the decision_type correct for this action?
- [ ] Is tenant_id obtained from authenticated session?
- [ ] Is context properly built (no hardcoded values)?
- [ ] Is decision.outcome checked with exhaustive switch/if?
- [ ] Is DENIED outcome properly handled (throw error)?
- [ ] Is REQUIRE_APPROVAL outcome properly handled (workflow created)?
- [ ] Is there NO direct Core API call (only via SDK)?
- [ ] Is there NO forged decision object?
- [ ] Is the mutation ONLY executed after ALLOWED outcome?

### Red Flags (Auto-Reject in Code Review):

- [ ] `fetch("http://infra-core...")` - Direct Core call
- [ ] `const decision = { outcome: "ALLOWED" }` - Forged decision
- [ ] Missing `infra.createDecision()` before database mutation
- [ ] `if (decision.outcome === "ALLOWED" || true)` - Bypass logic
- [ ] `// TODO: add decision check later` - Missing enforcement
```

### 4.2 Automated Detection Rules

```typescript
// ESLint/Custom Lint Rules for Bypass Detection

// RULE 1: Detect direct Core API calls
// Pattern: fetch/axios/http call to infra-core without SDK
{
  "no-direct-infra-core-call": {
    pattern: /fetch\(.*infra-core.*\/v1\/decisions/,
    message: "Direct Core API call detected. Use SDK instead."
  }
}

// RULE 2: Detect forged decision objects
// Pattern: Decision object created inline without SDK call
{
  "no-forged-decision": {
    pattern: /const.*decision.*=.*\{.*outcome.*:.*"ALLOWED"/,
    message: "Forged decision object detected. Decision must come from SDK."
  }
}

// RULE 3: Detect mutation without decision
// Pattern: Database mutation methods without prior SDK call
{
  "require-decision-before-mutation": {
    functions: ["approve", "void", "override", "adjust", "reassign"],
    requirePrior: "infra.createDecision",
    message: "Mutation requires decision check. Call infra.createDecision() first."
  }
}
```

### 4.3 Runtime Detection

```typescript
// Middleware: Decision Verification
async function verifyDecisionMiddleware(ctx, next) {
  const { action, entityId, tenantId } = ctx.request;

  // Check if action requires decision
  if (ACTIONS_REQUIRING_DECISION.includes(action)) {
    const decisionId = ctx.headers["x-decision-id"];

    if (!decisionId) {
      // LOG AS BYPASS ATTEMPT
      await auditLog.critical({
        event: "BYPASS_ATTEMPT_DETECTED",
        action: action,
        entityId: entityId,
        tenantId: tenantId,
        reason: "Missing decision ID",
        timestamp: new Date()
      });

      throw new SecurityViolationError("Decision required for this action");
    }

    // Verify decision exists and is valid
    const decision = await infra.getDecision(decisionId);

    if (!decision) {
      await auditLog.critical({
        event: "FORGED_DECISION_DETECTED",
        decisionId: decisionId,
        reason: "Decision not found in Infra"
      });

      throw new SecurityViolationError("Invalid decision");
    }

    if (decision.tenant_id !== tenantId) {
      await auditLog.critical({
        event: "TENANT_BYPASS_DETECTED",
        decisionId: decisionId,
        expectedTenant: tenantId,
        actualTenant: decision.tenant_id
      });

      throw new SecurityViolationError("Tenant mismatch");
    }

    if (decision.outcome !== "ALLOWED") {
      await auditLog.critical({
        event: "OUTCOME_BYPASS_DETECTED",
        decisionId: decisionId,
        outcome: decision.outcome
      });

      throw new SecurityViolationError("Decision not allowed");
    }
  }

  await next();
}
```

### 4.4 Monitoring & Alerting

```yaml
# Prometheus Alerting Rules for Bypass Detection

groups:
  - name: bypass_detection
    rules:
      - alert: BypassAttemptDetected
        expr: rate(infra_bypass_attempts_total[5m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Bypass attempt detected"
          description: "{{ $value }} bypass attempts in last 5 minutes"

      - alert: MutationWithoutDecision
        expr: rate(app_mutations_total[5m]) > rate(infra_decisions_total[5m]) * 1.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Mutations exceeding decisions"
          description: "Possible bypass: mutations > decisions by {{ $value }}%"

      - alert: ForgedDecisionDetected
        expr: rate(infra_forged_decision_detected_total[5m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Forged decision detected"
          description: "Security incident: forged decision attempt"
```

---

## 5. Response Protocol: Bypass Terdeteksi

### 5.1 Immediate Response (T + 0)

```
1. ALERT triggered → On-call engineer notified
2. Automatic:
   - Log enrichment enabled
   - Request tracing activated
   - Suspicious requests isolated (if possible)

3. Manual (within 15 minutes):
   - Identify source of bypass
   - Assess impact scope
   - Determine if ongoing or past event
```

### 5.2 Investigation (T + 1h)

```
1. Root Cause Analysis:
   - Code path that caused bypass
   - Developer/team responsible
   - Timeline of bypass occurrence

2. Impact Assessment:
   - How many records affected?
   - Which tenants impacted?
   - Compliance implications?

3. Evidence Collection:
   - Audit logs
   - Request traces
   - Code commits
```

### 5.3 Remediation (T + 4h)

```
1. Code Fix:
   - Fix bypass vulnerability
   - Add guard rails
   - Add tests

2. Data Remediation:
   - Identify affected records
   - Create compensating decisions (if needed)
   - Update audit trail

3. Deployment:
   - Emergency hotfix deployment
   - Rollback if needed
```

### 5.4 Post-Mortem (T + 24h)

```
1. Documentation:
   - Timeline of events
   - Root cause
   - Impact assessment
   - Remediation steps

2. Prevention:
   - New lint rules
   - New code review checklist items
   - New automated tests

3. Communication:
   - Internal stakeholders
   - Affected tenants (if required)
   - Compliance/legal (if required)
```

---

## 6. Exceptions: Ketika Bypass Diizinkan

### 6.1 Tidak Ada Exception untuk Production

```
KEBIJAKAN:
  Bypass TIDAK PERNAH diizinkan di production environment.

  Tidak ada:
    - Admin override
    - Emergency bypass
    - "Just this once" bypass
    - Backdoor for debugging

  Semua aksi yang memerlukan keputusan WAJIB melalui PEP.
  Tanpa exception.
```

### 6.2 Development/Testing Only

```
HANYA di development/testing environment:

1. Unit Tests:
   - Mock SDK responses allowed
   - Forged decisions allowed (for testing)
   - Guard: TEST_ENV flag must be set

2. Integration Tests:
   - Real SDK calls required
   - Real decisions required
   - Test tenant isolation enforced

3. Load Tests:
   - Real SDK calls required
   - Test tenant with high rate limit
   - Real decisions recorded

GUARD:
  if (process.env.NODE_ENV === "production") {
    // All guard rails ENABLED
    // NO bypass allowed
  }
```

---

## 7. Summary: Anti-Bypass adalah Non-Negotiable

### 7.1 Prinsip Utama

```
1. SETIAP aksi yang memerlukan keputusan → PEP → PDP → Outcome → Enforce
2. BYPASS = Bug Kritikal = Severity-1 = Immediate Response
3. TIDAK ADA exception di production
4. Detection + Prevention + Response = Defense in Depth
```

### 7.2 Checklist untuk Developer

```markdown
SEBELUM commit code yang melakukan mutasi:

□ Apakah aksi ini memerlukan decision? (lihat Section 2.1)
□ Apakah saya sudah call infra.createDecision()?
□ Apakah saya sudah handle semua 3 outcome?
□ Apakah saya TIDAK melakukan direct Core call?
□ Apakah saya TIDAK membuat forged decision object?
□ Apakah mutation HANYA dieksekusi jika outcome = ALLOWED?
```

### 7.3 Guard Rails Summary

| Layer | Guard Rail | Detection |
|-------|------------|-----------|
| Code Review | Checklist | Manual |
| Lint | ESLint rules | Automated |
| Runtime | Middleware | Automated |
| Monitoring | Prometheus alerts | Automated |
| Audit | Log analysis | Automated + Manual |

---

## Appendix A: AI Boundary Rule (LAW)

### A.1 Status Hukum AI dalam Control Plane

```
DEKLARASI HUKUM:

  AI (Artificial Intelligence, LLM, Agent, Copilot)
  BUKAN actor dalam Control Plane.

  AI TIDAK MEMILIKI:
    - Kewenangan membuat keputusan
    - Kemampuan memicu mutasi
    - Hak mengaktifkan rule
    - Status sebagai approver
```

### A.2 AI sebagai Non-Actor (LOCKED)

```
LAW-AI-1: AI BUKAN Decision Maker
  ─────────────────────────────────────────────
  AI TIDAK BOLEH membuat keputusan atas nama sistem.

  DILARANG:
    - AI memanggil infra.createDecision() secara otonom
    - AI menentukan outcome (ALLOWED/DENIED)
    - AI menggantikan PDP dalam evaluasi rule

  ALASAN:
    - Keputusan adalah tanggung jawab hukum
    - AI tidak memiliki akuntabilitas legal
    - Audit trail harus traceable ke manusia/sistem

LAW-AI-2: AI BUKAN Mutation Trigger
  ─────────────────────────────────────────────
  AI TIDAK BOLEH memicu aksi yang memerlukan keputusan.

  DILARANG:
    - AI mengeksekusi approval secara otonom
    - AI men-trigger workflow state change
    - AI melakukan entity mutation tanpa human approval

  ALASAN:
    - Mutasi adalah konsekuensi bisnis
    - AI tidak bertanggung jawab atas konsekuensi
    - Human-in-the-loop WAJIB untuk aksi berisiko

LAW-AI-3: AI BUKAN Rule Activator
  ─────────────────────────────────────────────
  AI TIDAK BOLEH mengubah status rule menjadi ACTIVE.

  DILARANG:
    - AI mengaktifkan rule draft secara otonom
    - AI menonaktifkan rule ACTIVE
    - AI memodifikasi rule condition/action

  ALASAN:
    - Rule activation mengubah perilaku sistem
    - Perubahan rule memerlukan approval manusia
    - Audit trail harus menunjuk manusia yang bertanggung jawab
```

### A.3 AI sebagai Advisor (ALLOWED)

```
PERAN AI YANG DIIZINKAN:

  ✅ PROPOSE (Mengusulkan)
     AI boleh mengusulkan:
       - Draft rule baru
       - Perubahan rule existing
       - Konfigurasi decision_type
     OUTPUT = Proposal document, BUKAN aksi

  ✅ ANALYZE (Menganalisis)
     AI boleh menganalisis:
       - Decision history untuk pattern
       - Rule effectiveness
       - Anomaly detection
     OUTPUT = Analysis report, BUKAN keputusan

  ✅ VERIFY (Memverifikasi)
     AI boleh memverifikasi:
       - Konsistensi rule dengan policy
       - Syntax validation
       - Conflict detection
     OUTPUT = Verification result, BUKAN approval

  ✅ DRAFT (Membuat draft)
     AI boleh membuat:
       - Rule draft (status = DRAFT, bukan ACTIVE)
       - Documentation draft
       - Test case suggestion
     OUTPUT = Draft content, BUKAN production artifact
```

### A.4 Enforcement: AI Output = Proposal Only

```
HUKUM OUTPUT AI:

  SETIAP output AI = PROPOSAL
  PROPOSAL ≠ AKSI
  PROPOSAL memerlukan HUMAN APPROVAL sebelum menjadi AKSI

IMPLEMENTATION PATTERN:

  // WRONG: AI triggers action directly
  async function aiAutoApprove(journalId) {
    const decision = await ai.analyze(journalId);
    if (decision.recommendation === "approve") {
      await infra.createDecision(...);  // ❌ AI sebagai actor
      await journal.approve(journalId);  // ❌ AI sebagai trigger
    }
  }

  // CORRECT: AI creates proposal, human approves
  async function aiPropose(journalId) {
    const analysis = await ai.analyze(journalId);

    // AI output = proposal
    await proposals.create({
      type: "journal_approval",
      entity_id: journalId,
      ai_recommendation: analysis.recommendation,
      ai_reasoning: analysis.reasoning,
      status: "PENDING_HUMAN_REVIEW"  // ✅ Requires human
    });

    // Human reviews and takes action
    // Human calls infra.createDecision()
    // Human is the actor, not AI
  }

AUDIT TRAIL:

  Setiap aksi WAJIB menunjuk ke HUMAN actor:
    created_by: "user-123"  ✅ Human
    created_by: "ai-agent"  ❌ VIOLATION

  AI involvement harus di-record sebagai ADVISOR:
    assisted_by: "ai-agent-v2"
    ai_proposal_id: "prop-456"
```

### A.5 Guard Rail: AI Boundary Enforcement

```
DETECTION RULES:

  IF api_caller.type === "ai" OR api_caller.type === "agent":
    IF action IN [createDecision, approveWorkflow, activateRule]:
      REJECT with "AI_ACTOR_VIOLATION"
      LOG as SECURITY_EVENT

  IF decision.created_by matches AI_AGENT_PATTERN:
    REJECT with "AI_ACTOR_VIOLATION"
    LOG as SECURITY_EVENT

  IF rule.activated_by matches AI_AGENT_PATTERN:
    REJECT with "AI_ACTOR_VIOLATION"
    LOG as SECURITY_EVENT

MONITORING:

  Alert jika terdeteksi:
    - AI calling decision endpoint directly
    - AI identifier in created_by field
    - AI triggering rule activation
```

### A.6 Summary: AI adalah Advisor, Bukan Actor

```
┌─────────────────────────────────────────────────────────────┐
│                    AI BOUNDARY RULE                          │
│                                                              │
│  AI dalam Control Plane:                                    │
│                                                              │
│    ❌ BUKAN decision maker                                  │
│    ❌ BUKAN mutation trigger                                │
│    ❌ BUKAN rule activator                                  │
│    ❌ BUKAN approver                                        │
│                                                              │
│    ✅ ADALAH advisor                                        │
│    ✅ ADALAH analyzer                                       │
│    ✅ ADALAH proposal generator                             │
│    ✅ ADALAH verification assistant                         │
│                                                              │
│  OUTPUT AI = PROPOSAL                                       │
│  PROPOSAL → HUMAN REVIEW → HUMAN ACTION                     │
│                                                              │
│  Akuntabilitas = MANUSIA, bukan AI                          │
└─────────────────────────────────────────────────────────────┘
```

---

**INFRA-DEC-005: LAYER 0 OVERLAY - LOCKED**

*Bypass adalah bug kritikal. Tidak ada exception. Enforce atau fail.*
*AI adalah advisor, bukan actor. Output AI adalah proposal, bukan aksi.*
