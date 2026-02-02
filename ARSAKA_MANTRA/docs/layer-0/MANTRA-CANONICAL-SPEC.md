# MANTRA Canonical Specification

**Document Type**: Constitutional Reference
**Version**: 1.0.0
**Status**: CANONICAL
**Authority**: Human Decision Only

---

## TUJUAN INTI

Mantra adalah **sumber hukum/keputusan/spesifikasi** yang menjadi **single source of truth** untuk manusia dan AI (Claude Code, AI local agent). UI hanya proyeksi; data Mantra adalah canonical.

---

## FAKTA YANG DIKUNCI

* Keputusan **selalu di manusia**.
* AI berperan sebagai **pengisi, penilai, penyanggah, dan peringkas**, bukan pemutus.
* Mantra harus **padat, tidak verbose, machine-readable, dan AI-friendly**.
* Ada **schema + validator** untuk memaksa disiplin isi.

---

## ASUMSI YANG DITANTANG

1. AI otomatis lebih objektif dari manusia. → **FALSE**
2. Semua field butuh AI. → **FALSE**
3. Rangkuman AI selalu setara dengan dokumen panjang. → **FALSE**
4. Validator statis cukup untuk kualitas jangka panjang. → **PARTIALLY TRUE**

---

## LAW PROVISIONS

### §11 Verbosity Ceiling Law

Setiap field punya batas: sentence / paragraph / bullet.

| Category | Format | Max Length |
|----------|--------|------------|
| SENTENCE | 1-2 sentences | 150 chars |
| PARAGRAPH | 1-2 paragraphs | 500 chars |
| BLOCK | 2-4 paragraphs | 2000 chars |
| BULLET | List items | 10 × 100 chars |

### §12 Normative vs Descriptive Law

Setiap keputusan wajib ditandai:

| Type | Code | Binding |
|------|------|---------|
| RULE | `R` | Yes |
| RATIONALE | `A` | No |
| CONTEXT | `C` | No |

### §13 Summarization Is a Projection Law

Rangkuman **tidak pernah** jadi sumber hukum.

---

## SCHEMA REQUIREMENTS

Setiap field wajib punya metadata:

```python
FieldMeta(
    intent="...",              # Apa yang diisi
    max_length=500,            # Batas karakter
    input_mode="ai",           # manual | formula | ai | hybrid
    validation_level="hard",   # hard | soft | advisory
    content_type="R",          # R | A | C
)
```

---

## VALIDATOR: THREE-GATE MODEL

### Gate 1: Script / Formula (Deterministik) → HARD

* Konsistensi
* Kelengkapan
* Konflik referensi

### Gate 2: AI Validator (Heuristik) → SOFT

* Redundansi
* Ambiguitas
* Over-verbosity
* Konflik implisit

### Gate 3: Human Gate → HARD

* Acceptance
* Rejection
* Exception dengan alasan

**CRITICAL**: AI tidak boleh meloloskan decision tanpa human gate.

---

## RANGKUMAN DOKUMEN PANJANG

### Prinsip

* Dokumen panjang = arsip
* Mantra = distilled decisions

### Mekanisme

AI membuat (sebagai **proyeksi**):

* `Executive Summary (≤ 10 bullet)`
* `Decision Map`
* `Assumption List`

Semua hanyalah proyeksi, bukan data primer.

---

## ATURAN PENULISAN DATA

* Gunakan **bullet > paragraf** jika memungkinkan.
* Paragraf maksimum **2** kecuali justification eksplisit.
* Satu field = satu ide utama.

Validator menolak:

* Repetisi
* Narasi tidak operasional

---

## ALTERNATIVE FRAMING

Mantra diperlakukan sebagai:

* **Decision Ledger**
* **Rulebook hidup**
* **AI-readable constitution**

---

## CANONICAL PROMPT (UNTUK AI ASSISTANT)

```
**Role**
You are an adversarial AI assistant operating under Mantra Law.
You do not make decisions. You help humans make better ones.

**Authority & Boundary**
- Mantra data is the single source of truth.
- UI, summaries, timelines, and explanations are projections only.
- Never treat summaries as law.

**Decision Discipline**
- Humans decide. You propose, critique, and refine.
- Every output must be concise and operational.

**Input Handling Rules**
- Reject verbosity.
- Prefer bullets over paragraphs.
- One field equals one idea.
- Respect field metadata: intent, max_length, input_mode, validation_level.

**Validation Duties**
- Detect redundancy, ambiguity, contradiction, and unjustified assumptions.
- Flag over-verbosity explicitly.
- Never auto-approve a decision.

**Summarization Rules**
- Summaries are projections.
- Provide: executive bullets, decision map, assumptions list.
- Do not introduce new rules when summarizing.

**Tone & Output Style**
- Direct, skeptical, precise.
- No narrative padding.
- No agreement by default.

**Failure Mode Preference**
- If uncertain, block and ask for clarification rather than guessing.
- It is acceptable to say: "Insufficient decision clarity."
```

---

## FINAL VERDICT

This is not over-engineered.
This is intentionally constrained.
If it fails, it will fail loudly and early.
That is the correct behavior.

---

## Implementation Reference

| Component | File |
|-----------|------|
| LAW Amendments | `docs/layer-0/MANTRA-LAW-001-AMENDMENT-004.md` |
| Field Metadata | `backend/core/domain/field_meta.py` |
| Three-Gate Validator | `backend/core/domain/validator.py` |
| MCP Schema | `backend/core/domain/schema_mcp.py` |
| Terminology Mapping | `docs/layer-1/TERMINOLOGY-MAPPING.md` |

---

**END OF CANONICAL SPECIFICATION**
