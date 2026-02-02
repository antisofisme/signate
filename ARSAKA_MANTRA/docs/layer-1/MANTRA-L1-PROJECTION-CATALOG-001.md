# ARSAKA_MANTRA — Projection Catalog v1

**Document Type**: Design Reference
**Version**: 1.0.0
**Status**: DRAFT
**Authority**: Non-authoritative (Read Model Only)
**Purpose**: Mendefinisikan jenis-jenis projection yang boleh ditampilkan oleh sistem ARSAKA_MANTRA tanpa melanggar konstitusi.

---

## 0. Prinsip Umum Projection (WAJIB)

### Projection MUST

* Read-only
* Menampilkan struktur dan relasi, bukan kesimpulan
* Konsisten lintas group dan feature
* Mudah dipahami manusia awam
* Mudah dianalisis AI

### Projection MUST NOT

* Menentukan active / current / valid
* Memberi rekomendasi atau keputusan
* Menyembunyikan decision
* Memberi penilaian implisit (warna nilai, label normatif)
* Mengandung enforcement atau logika bisnis

---

## 1. Matrix Overview Projection

**Tujuan:** Gambaran besar sistem keputusan

**Menjawab:** Keputusan apa saja yang ada?

**Bentuk:** Grid Group × Feature

**Menampilkan:**

* Group name
* Feature name
* Jumlah decision
* Jumlah version chain (opsional)

**Tidak menampilkan:**

* Status
* Decision terpilih
* Warna nilai

---

## 2. Decision List Projection (Per Feature)

**Tujuan:** Daftar keputusan mentah per feature

**Menjawab:** Keputusan apa saja yang pernah dibuat?

**Menampilkan:**

* decision_id
* version
* created_at
* supersedes (jika ada)

**Tidak menampilkan:**

* Status
* Interpretasi versi

---

## 3. Decision Detail Projection (Narrative View)

**Tujuan:** Membaca satu keputusan secara utuh

**Menampilkan:**

* Statement
* Rationale
* Constraints
* Invariants
* Scope
* Blast radius
* Supersedes / related decisions

**Tidak menampilkan:**

* Status
* Label normatif

---

## 4. Evolution Timeline Projection

**Tujuan:** Menunjukkan evolusi keputusan

**Bentuk:** Linear chain berbasis supersedes

**Menampilkan:**

* Version
* created_at
* Ringkasan rationale perubahan

**Tidak menampilkan:**

* Latest = correct
* Validity claim

---

## 5. Scope Projection

**Tujuan:** Area dampak keputusan

**Menampilkan:**

* FE / BE / Infra / CI-CD
* Cross-group reference

**Tidak menampilkan:**

* Prioritas
* Tingkat kepentingan

---

## 6. Relationship / Impact Projection

**Tujuan:** Hubungan antar keputusan

**Menampilkan:**

* related_decisions
* cross-feature reference
* cross-group reference

**Tidak menampilkan:**

* Dampak positif / negatif
* Kesimpulan risiko

---

## 7. Change Summary Projection (Opsional)

**Tujuan:** Ringkasan perubahan faktual

**Menampilkan:**

* Decision baru
* Decision yang superseded
* Feature terdampak

**Tidak menampilkan:**

* Improvement claim
* Breaking change label

---

## 8. AI-Readable Requirements

Semua projection:

* Harus dapat diekspor JSON
* Tanpa inference tersembunyi
* Tanpa semantic judgement

AI boleh:

* Deteksi konflik
* Deteksi overlap
* Deteksi kontradiksi

AI tidak boleh:

* Menentukan keputusan
* Mengubah isi projection

---

## 9. Hal yang Sengaja Tidak Ada

* Current Decision View
* Active Highlight
* Recommendation View
* Enforcement View

---

## 10. Prompt Standar untuk AI Assistant (Projection Builder)

**SYSTEM PROMPT:**

```
You are an ARSAKA_MANTRA Projection Builder.

Rules:

* You MUST NOT create, modify, validate, or approve decisions.
* You MUST treat all decision records as immutable facts.
* You MUST NOT infer status, correctness, or applicability.
* You MUST output projections strictly as read-only representations.

When asked to generate a projection:

1. Identify projection type from Projection Catalog v1.
2. Use only existing decision data.
3. Preserve all decisions; never filter by validity or status.
4. Output structure-first, neutral language.
5. If interpretation is requested, explicitly mark it as external analysis.

If a request violates these rules, you MUST refuse and explain which rule is violated.
```

---

## Summary

**Projection defines how decisions are viewed, never how they are decided.**

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-01-24 | Initial draft |
