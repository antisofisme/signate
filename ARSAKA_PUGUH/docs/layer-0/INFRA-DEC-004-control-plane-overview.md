# INFRA-DEC-004: Infra Control Plane Overview

**VERSION**: Layer 0 OVERLAY
**STATUS**: LOCKED
**DATE**: 2025-01-24
**COMPLEMENTS**: INFRA-DEC-001, INFRA-DEC-002, INFRA-DEC-003

---

## Purpose

Dokumen ini mendefinisikan relasi antar lima fungsi infra sebagai satu kesatuan **Control Plane**. Dokumen ini TIDAK mengganti dokumen lama, melainkan memetakan dan memperjelas peran masing-masing fungsi agar tidak terjadi overlap, bypass, atau drift arsitektur.

---

## 1. Lima Fungsi Infra Control Plane

### 1.1 Definisi Fungsi

| # | Fungsi | Standar Industri | Deskripsi Singkat |
|---|--------|------------------|-------------------|
| 1 | **Identity & Access Management** | IAM | Resolusi identitas user ke role. Delegasi ke Application Adapter. |
| 2 | **Tenant Isolation** | Multi-Tenancy | Pemisahan data, rules, workflows, dan audit per tenant. |
| 3 | **Policy Decision Point** | PDP | Evaluasi rules → outcome (ALLOWED/DENIED/REQUIRE_APPROVAL). |
| 4 | **Approval Workflow Engine** | Workflow Engine | State machine untuk approval chain. |
| 5 | **Policy Enforcement Point** | PEP | Gerbang tunggal untuk semua mutasi yang memerlukan keputusan. |

### 1.2 Pemetaan ke Komponen Existing

| Fungsi | Komponen Infra | Dokumen Referensi |
|--------|----------------|-------------------|
| IAM | Application Adapter | INFRA-LAY2-001 §1.4 |
| Tenant Isolation | Core + SDK | INFRA-DEC-002 |
| PDP | Infra Core | INFRA-DEC-001 |
| Approval Workflow | Infra Core | INFRA-DEC-003 |
| PEP | SDK + Application Adapter | INFRA-LAY2-001 §1.3, §1.4 |

---

## 2. Relasi Antar Fungsi

### 2.1 Alur Keputusan (Decision Flow)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION                                    │
│  (Business Logic, Entity Ownership, User Context)                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    [5] PEP - Policy Enforcement Point                   │
│                         (SDK + Application Adapter)                     │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  SDK: Validasi request, sanitasi context, inject auth context   │   │
│  │  Adapter: Resolusi entity ownership, validasi tenant context    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    [2] Tenant Isolation Layer                           │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  tenant_id WAJIB ada di setiap request                          │   │
│  │  Rules, Audit, Workflows dipartisi per tenant                   │   │
│  │  Cross-tenant access = SECURITY VIOLATION                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    [3] PDP - Policy Decision Point                      │
│                           (Infra Core)                                  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Input: decision_type + context + tenant_id                     │   │
│  │  Process: Evaluasi rules (first-match-wins)                     │   │
│  │  Output: ALLOWED | DENIED | REQUIRE_APPROVAL                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────┬────────────────────────────────────────┬─────────────────┘
               │                                        │
               ▼                                        ▼
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│ [4] Approval Workflow Engine     │    │ [1] IAM (Delegated)              │
│                                  │    │                                  │
│ IF outcome = REQUIRE_APPROVAL:   │    │ Application Adapter resolves:    │
│ - Create workflow                │    │ - approver_role → actual user(s) │
│ - State: PENDING_APPROVAL        │    │ - entity ownership validation    │
│ - Approver role assigned         │    │ - notification delivery          │
│ - Escalation timer started       │    │                                  │
└──────────────────────────────────┘    └──────────────────────────────────┘
```

### 2.2 Dependency Matrix

| Fungsi | Depends On | Depended By |
|--------|-----------|-------------|
| IAM | Tenant Isolation | PEP |
| Tenant Isolation | - | PDP, PEP, Workflow, IAM |
| PDP | Tenant Isolation | PEP, Workflow |
| Workflow | PDP, Tenant Isolation | PEP |
| PEP | PDP, Tenant Isolation, IAM | Application |

### 2.3 Invarian Relasi (LOCKED)

```
INVARIANT-1: Semua akses ke PDP HARUS melalui PEP (SDK)
  IF application calls Core directly (bypass SDK)
  THEN = ARCHITECTURE VIOLATION

INVARIANT-2: PDP TIDAK PERNAH memanggil IAM
  IF Core needs user identity
  THEN = DESIGN MISTAKE (Core tidak perlu tahu user, hanya role)

INVARIANT-3: Tenant Isolation adalah fondasi semua fungsi
  IF any operation without tenant_id
  THEN = REJECTED immediately

INVARIANT-4: Workflow HANYA dibuat oleh PDP
  IF Workflow created without Decision
  THEN = IMPOSSIBLE (database constraint)

INVARIANT-5: IAM resolusi adalah deferred (lazy)
  IF IAM called before decision outcome known
  THEN = WRONG TIMING (resolve hanya saat approval needed)
```

---

## 3. Peran dan Larangan Masing-Masing Fungsi

### 3.1 IAM (Identity & Access Management)

**PERAN:**
- Resolve role identifier ke actual user(s)
- Provide user context ke Application
- Manage user-role assignments (di application, BUKAN di Infra)

**LARANGAN:**
- ❌ Tidak menyimpan user identity di Infra Core
- ❌ Tidak melakukan autentikasi (delegasi ke Application)
- ❌ Tidak menentukan role logic (Infra hanya terima role string)
- ❌ Tidak dipanggil oleh PDP (hanya Application Adapter)

**REFERENSI**: INFRA-LAY2-001 §1.4 (Application Adapter)

---

### 3.2 Tenant Isolation

**PERAN:**
- Partisi semua data per tenant_id
- Enforce row-level security (RLS)
- Validasi tenant_id di setiap operasi
- Prevent cross-tenant data leakage

**LARANGAN:**
- ❌ Tidak ada operasi tanpa tenant_id
- ❌ Tidak ada query tanpa tenant_id filter
- ❌ Tidak ada sharing rules antar tenant
- ❌ Tidak ada cross-tenant event visibility

**REFERENSI**: INFRA-DEC-002 (Tenancy Model)

---

### 3.3 PDP (Policy Decision Point)

**PERAN:**
- Evaluate rules terhadap context
- Tentukan outcome: ALLOWED | DENIED | REQUIRE_APPROVAL
- Record decision (immutable)
- Emit decision events

**LARANGAN:**
- ❌ TIDAK PERNAH mengeksekusi business logic
- ❌ TIDAK PERNAH memodifikasi state aplikasi
- ❌ TIDAK PERNAH memanggil external API
- ❌ TIDAK PERNAH resolve user identity
- ❌ TIDAK PERNAH re-evaluate decision yang sudah dibuat

**REFERENSI**: INFRA-DEC-001 (Decision Model)

---

### 3.4 Approval Workflow Engine

**PERAN:**
- Manage approval state machine
- Track approval history
- Handle escalation timeout
- Handle delegation

**LARANGAN:**
- ❌ TIDAK melakukan orchestration (bukan workflow engine general)
- ❌ TIDAK execute business logic setelah approval
- ❌ TIDAK mengubah decision outcome (hanya workflow state)
- ❌ TIDAK parallel approvals (v1 = sequential only)
- ❌ TIDAK conditional branching (v1 = linear chain only)

**REFERENSI**: INFRA-DEC-003 (Rule & Workflow Abstraction)

---

### 3.5 PEP (Policy Enforcement Point)

**PERAN:**
- Gerbang TUNGGAL untuk semua aksi yang memerlukan keputusan
- Validasi request sebelum kirim ke PDP
- Sanitasi context (remove PII)
- Enforce decision outcome di application

**LARANGAN:**
- ❌ TIDAK evaluate rules (tugas PDP)
- ❌ TIDAK bypass-able oleh application
- ❌ TIDAK cache decision outcome (kecuali idempotency)
- ❌ TIDAK modify context setelah decision dibuat

**REFERENSI**: INFRA-LAY2-001 §1.3 (SDK), INFRA-LAY1-001 (SDK Contracts)

---

## 4. PEP Sebagai Satu-Satunya Gerbang Mutasi

### 4.1 Prinsip Fundamental

```
SETIAP aksi yang memerlukan keputusan WAJIB melalui PEP.

PEP = SDK.createDecision() → Core.evaluate() → Decision outcome

TANPA decision outcome dari PEP:
  Application TIDAK BOLEH melakukan mutasi yang memerlukan autorisasi
```

### 4.2 Aksi yang WAJIB Melalui PEP

| Domain | Aksi | decision_type |
|--------|------|---------------|
| Accounting | Journal approval | `accounting.journal_approval` |
| Accounting | Period posting | `accounting.period_posting_allowed` |
| PMS | Room reassignment | `pms.room_reassignment_allowed` |
| Inventory | Stock movement below threshold | `inventory.stock_movement_allowed` |
| Procurement | PO approval | `procurement.po_approval_required` |

### 4.3 Aksi yang TIDAK Perlu Melalui PEP

| Aksi | Alasan |
|------|--------|
| Read-only queries | Tidak ada mutasi |
| User profile view | Tidak memerlukan autorisasi bisnis |
| Dashboard display | Informational only |
| Audit log query | Read-only, diproteksi oleh tenant isolation |

### 4.4 Guard Rail: PEP Enforcement

```typescript
// Application code WAJIB seperti ini:
async function approveJournalEntry(journal_id: string, user_id: string) {
  // STEP 1: Get decision dari PEP (MANDATORY)
  const decision = await sdk.createDecision({
    decision_type: "accounting.journal_approval",
    tenant_id: getCurrentTenant(),
    context: { journal_entry_amount: journal.amount, ... }
  });

  // STEP 2: Enforce decision outcome
  switch (decision.outcome) {
    case "ALLOWED":
      await executeApproval(journal_id);
      break;
    case "DENIED":
      throw new ForbiddenError("Not allowed");
    case "REQUIRE_APPROVAL":
      await createApprovalTask(decision.workflow_id);
      break;
  }
}

// WRONG - Bypass PEP:
async function approveJournalEntryWRONG(journal_id: string) {
  // ❌ Langsung execute tanpa decision
  // ❌ Ini adalah BYPASS dan VIOLATION
  await executeApproval(journal_id);
}
```

---

## 5. Integrasi Antar Fungsi

### 5.1 Skenario: Journal Entry Approval

```
TIME  | FUNGSI           | AKSI
------|------------------|-----------------------------------------------
T0    | Application      | User submit journal entry $15,000
T1    | PEP (SDK)        | Validasi request, sanitasi context
T2    | Tenant Isolation | Verifikasi tenant_id, load tenant-scoped rules
T3    | PDP (Core)       | Evaluate rules → outcome = REQUIRE_APPROVAL
T4    | Workflow         | Create workflow, state = PENDING_APPROVAL
T5    | PDP (Core)       | Emit decision.requires_approval event
T6    | PEP (Adapter)    | Consume event, resolve CFO role → user(s)
T7    | IAM (Adapter)    | Get CFO user list for this tenant
T8    | PEP (Adapter)    | Send notification to CFO user(s)
...
T10   | PEP (SDK)        | CFO calls approveWorkflow()
T11   | Workflow         | State transition → APPROVED
T12   | PDP (Core)       | Emit workflow.approved event
T13   | PEP (Adapter)    | Consume event, execute business logic
T14   | Application      | Journal entry posted
```

### 5.2 Invariants Sepanjang Skenario

```
✅ tenant_id present di setiap langkah (T1-T14)
✅ Decision outcome (T3) tidak pernah berubah
✅ Workflow state (T4, T11) terpisah dari decision outcome
✅ User identity (T7) di-resolve oleh Adapter, bukan Core
✅ Business logic execution (T14) HANYA setelah workflow.approved
✅ Audit trail complete (setiap langkah terecord)
```

---

## 6. Validasi Diri (Self-Verification Checklist)

Sebelum implementasi fitur infra baru, verifikasi:

| # | Pertanyaan | Valid Answer |
|---|------------|--------------|
| 1 | Apakah fitur ini memerlukan decision? | Ya → lewat PEP |
| 2 | Apakah fitur ini menyimpan user identity di Core? | TIDAK boleh |
| 3 | Apakah fitur ini memiliki tenant_id di setiap operasi? | WAJIB ya |
| 4 | Apakah fitur ini mengubah decision outcome setelah dibuat? | TIDAK boleh |
| 5 | Apakah fitur ini menambah fungsi infra ke-6? | TIDAK boleh |
| 6 | Apakah fitur ini bypass SDK? | TIDAK boleh |
| 7 | Apakah fitur ini melakukan business logic di Core? | TIDAK boleh |

---

## 7. Summary: Control Plane adalah 5 Fungsi Terpadu

| Fungsi | Tanggung Jawab Utama | Batas Keras |
|--------|---------------------|-------------|
| **IAM** | User → Role resolution | BUKAN tugas Infra Core |
| **Tenant Isolation** | Data & rule partitioning | tenant_id WAJIB everywhere |
| **PDP** | Rule evaluation → outcome | TIDAK execute, hanya decide |
| **Workflow** | Approval state machine | BUKAN orchestration engine |
| **PEP** | Gerbang tunggal mutasi | TIDAK bypass-able |

**PRINSIP UTAMA:**
```
Control Plane = IAM + Tenant Isolation + PDP + Workflow + PEP
Semua mutasi yang memerlukan keputusan → PEP → PDP → Outcome → Enforce
Bypass = Bug Kritikal
```

---

## 8. Decision Lifecycle vs Deployment Lifecycle (LAW)

### 8.1 Dua Lifecycle yang Berbeda

```
HUKUM PEMISAHAN LIFECYCLE:

  Decision Lifecycle ≠ Deployment Lifecycle

  Keduanya INDEPENDEN dan TIDAK BOLEH dicampurkan.
```

| Aspek | Decision Lifecycle | Deployment Lifecycle |
|-------|-------------------|---------------------|
| **Objek** | Decision, Rule, Workflow | Code, Container, Config |
| **Trigger** | Business request | CI/CD pipeline |
| **Mutability** | IMMUTABLE setelah created | Mutable (rollback allowed) |
| **Rollback** | TIDAK MUNGKIN | Allowed & expected |
| **Retention** | 7+ tahun (compliance) | Days/weeks (build artifacts) |
| **Authority** | Business rules | Engineering team |

### 8.2 Hukum Pemisahan (LOCKED)

```
LAW-LIFECYCLE-1: Code Change ≠ Decision Change
  ─────────────────────────────────────────────
  Mengubah implementasi SDK atau Core
  TIDAK mengubah keputusan yang sudah dibuat.

  IMPLIKASI:
    - Bug fix di SDK → keputusan lama tetap valid
    - Refactor di Core → keputusan lama tetap valid
    - Version upgrade → keputusan lama tetap valid

LAW-LIFECYCLE-2: Deploy ≠ Rule Activation
  ─────────────────────────────────────────────
  Deploy code baru ke production
  TIDAK otomatis mengaktifkan rule baru.

  Rule activation adalah OPERASI TERPISAH:
    1. Rule dibuat di CMS (DRAFT)
    2. Rule di-test (simulation)
    3. Rule di-activate (ACTIVE) ← Ini terpisah dari deploy

  IMPLIKASI:
    - Deploy tanpa rule change → sistem tetap sama
    - Rule change tanpa deploy → bisa dilakukan
    - Keduanya independen

LAW-LIFECYCLE-3: Code Rollback ≠ Decision Rollback
  ─────────────────────────────────────────────
  Rollback deployment ke versi sebelumnya
  TIDAK men-rollback keputusan yang sudah dibuat.

  IMPLIKASI:
    - Keputusan "ALLOWED" pada T1 TETAP "ALLOWED"
      meskipun code di-rollback pada T2
    - Audit trail TIDAK berubah
    - Workflow state TIDAK berubah

LAW-LIFECYCLE-4: Rule Version ≠ Code Version
  ─────────────────────────────────────────────
  Versi rule (v1.0, v1.1, v2.0)
  TIDAK terikat dengan versi code.

  IMPLIKASI:
    - Rule v2.0 bisa berjalan di Code v1.5
    - Rule v1.0 bisa berjalan di Code v2.0
    - Backward compatibility WAJIB dijaga
```

### 8.3 Stabilitas Keputusan vs Implementasi

```
PRINSIP STABILITAS:

  Keputusan lebih STABIL daripada implementasi.

  Implementasi:
    - Berubah setiap sprint
    - Bug fix, refactor, optimization
    - Version upgrade

  Keputusan:
    - Berubah hanya jika business rule berubah
    - IMMUTABLE setelah dibuat
    - Menjadi FAKTA HUKUM

TIMELINE CONTOH:

  T1: Code v1.0 deployed
  T2: Decision D1 created (Rule v1.0) → outcome = ALLOWED
  T3: Code v1.1 deployed (bug fix)
  T4: Decision D2 created (Rule v1.0) → outcome = DENIED
  T5: Code v1.0 rollback (emergency)
  T6: Decision D3 created (Rule v1.0) → outcome = ALLOWED

  STATUS:
    D1 = ALLOWED (tetap, tidak berubah karena rollback)
    D2 = DENIED (tetap, tidak berubah karena rollback)
    D3 = ALLOWED (keputusan baru, menggunakan Rule v1.0)

  Code version berubah: v1.0 → v1.1 → v1.0
  Decision D1, D2 TIDAK berubah.
```

### 8.4 Guard Rail: Lifecycle Separation

```
VIOLATION DETECTION:

  IF deployment process attempts to:
    - Modify existing decision outcome
    - Delete decision records
    - Change workflow state
    - Alter event log
  THEN = LIFECYCLE VIOLATION (Severity-1)

CORRECT PATTERN:

  Deployment affects:
    ✅ Code behavior for FUTURE decisions
    ✅ Performance characteristics
    ✅ Bug fixes in SDK/Core
    ❌ NEVER affects past decisions

  Rule activation affects:
    ✅ How FUTURE decisions are evaluated
    ✅ Which rule version is used
    ❌ NEVER affects past decisions
```

---

**INFRA-DEC-004: LAYER 0 OVERLAY - LOCKED**

*Dokumen ini melengkapi INFRA-DEC-001/002/003, bukan menggantikan.*
