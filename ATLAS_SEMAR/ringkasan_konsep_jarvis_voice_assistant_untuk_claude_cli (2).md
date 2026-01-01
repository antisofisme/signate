# Ringkasan Konsep Jarvis Voice Assistant untuk Claude CLI

Dokumen ini adalah **ringkasan final konsep** Jarvis (voice-driven assistant) yang dirancang untuk membantu penggunaan **Claude CLI** secara efisien, aman, dan minim kelelahan mengetik. Dokumen ini ditujukan sebagai **acuan implementasi oleh AI assistant / AI coding agent**.

---

## 1. TUJUAN UTAMA

- Mengontrol Claude CLI menggunakan **suara**
- Mengurangi kebutuhan mengetik panjang
- Menyatukan input suara & keyboard ke **satu sesi Claude**
- Memberi pengalaman seperti "Jarvis", **tanpa membuat AI baru**

Jarvis **bukan LLM**, melainkan **input & orchestration layer**.

---

## 2. PRINSIP ARSITEKTUR (OPS I B)

- Claude CLI tetap **satu-satunya otak & memori**
- Jarvis **tidak menyimpan chat history LLM**
- Jarvis hanya menyimpan **metadata** (mode, intent, status)
- Semua input (suara & ketik) masuk ke **sesi Claude yang sama**

> Unity dicapai lewat satu jalur input, bukan dengan memori ganda.

---

## 3. KONSEP UI

### 3.1 UI Balon (Overlay)

- Bentuk: balon / HUD kecil (floating)
- Selalu ringan, tanpa history panjang
- Tidak menggantikan CLI

**Isi balon (maksimal):**
- Status: listening / processing / idle
- Mode aktif
- Ringkasan singkat (opsional)
- Konfirmasi aksi sensitif
- Saran command lanjutan

### 3.2 Mode Global Layer

- Mode berada di **layer paling atas (global state)**
- Bukan bagian chat
- Bukan bagian prompt

Mode awal:
- Coding
- Debug
- Explain

Mode mempengaruhi **cara prompt dibentuk**, bukan isi chat history.

---

## 4. ALUR KERJA INTI

1. User tekan push-to-talk
2. Jarvis merekam audio
3. Silence dibuang (VAD)
4. Audio dikirim ke STT (Whisper)
5. Teks diproses oleh Jarvis
6. Command & mode diterapkan
7. Teks dikirim ke Claude CLI
8. Enter dikirim otomatis
9. Output Claude muncul di CLI

---

## 5. COMMAND GRAMMAR (CONTOH)

- "kirim" / "lanjut" → Enter
- "ulang" → ulang instruksi terakhir
- "ringkas" → minta ringkasan
- "jelaskan" → mode explain
- "refactor" → perbaiki struktur kode
- "buat test" → generate unit test
- "mode coding" / "mode debug" → ganti mode

Command mengatur **alur**, bukan isi prompt.

---

## 6. KEAMANAN (WAJIB)

- Push-to-talk (tidak always listening)
- Tidak ada auto-execute shell command
- Aksi sensitif wajib konfirmasi
- Tidak ada autonomous agent

Aksi yang dilindungi:
- Hapus file
- Git force / reset
- Script berbahaya

---

## 7. LLM TAMBAHAN (OPSIONAL, NON-BLOCKING)

Jika tersedia API LLM tambahan:

**Prinsip:**
- Tidak di jalur utama (async)
- Tidak mempengaruhi latency

**Fungsi yang diperbolehkan:**
- Prompt refiner (untuk request berikutnya)
- Mode auto-suggestion
- Output summarizer (on-demand)
- Error insight
- Knowledge rule check (Aplikasi Besar)

**Yang dilarang:**
- Eksekusi command
- Mengubah prompt tanpa izin
- Menggantikan Claude

---

## 8. STACK & FRAMEWORK (DIREKOMENDASIKAN)

### Core Engine
- Python 3.11+

### Speech-to-Text
- Whisper (local via whisper.cpp atau Whisper API)

### Voice Detection
- Silero VAD / WebRTC VAD

### UI Overlay
- PySide6 (Qt for Python)

### Keyboard Automation
- AutoHotkey v2

### Konfigurasi
- YAML / TOML

---

## 9. NILAI UTAMA SISTEM

- Mengurangi kelelahan fisik & mental
- Konsistensi perilaku Claude
- Aman untuk penggunaan harian
- Tidak over-engineered
- Mudah dikembangkan bertahap

---

## 10. DEFINISI MVP

> Voice → Claude CLI + Mode + Context + Safety

Tanpa UI besar, tanpa agent otonom, tanpa kompleksitas berlebihan.

Dokumen ini dapat digunakan langsung sebagai **prompt spesifikasi** untuk AI coding assistant.

---

## 11. CONTOH ALUR NYATA (SIMULASI END-TO-END)

### Input User (Suara)
> "perbaiki tabel jurnal apakah sudah sesuai dengan standar"

### Alur Internal Jarvis (Ringkas)
1. **STT** mengubah suara menjadi teks (tanpa pemahaman konteks).
2. **Jarvis** mendeteksi:
   - intent: audit / perbaikan
   - domain: accounting / jurnal
   - mode: coding (atau auto-suggest ke coding)
3. **Jarvis** memuat aturan proyek *Aplikasi Besar* (accounting = financial spine).
4. **Jarvis** membungkus prompt sesuai standar proyek.

### Prompt yang Dikirim ke Claude CLI
Jarvis mengetikkan (tanpa user mengetik manual):

- Meminta pemeriksaan tabel jurnal
- Memaksa kriteria:
  - double-entry
  - append-only
  - period locking
  - multi-tenant
  - audit trail
  - pemisahan ledger dari logic operasional

### Respons Claude
Claude memberikan:
- evaluasi struktur tabel
- koreksi desain
- contoh struktur jurnal yang benar

### Peran LLM Tambahan (Async, Opsional)
- Tidak membaca seluruh jawaban
- Hanya mengecek **signal penting**:
  - apakah semua aturan accounting disebut

Jika lengkap:
> ✅ Standar accounting terpenuhi

Jika kurang:
> ⚠️ Ada standar yang belum disebut, tawarkan koreksi lanjutan

### Nilai yang Dihasilkan
- User tidak perlu menulis prompt panjang
- Claude dipaksa konsisten dengan standar proyek
- Tidak ada latency tambahan
- Tidak ada memori ganda

---

### Inti Contoh Ini
> **Jarvis menerjemahkan niat user ke bahasa arsitektur proyek, lalu menjaga kualitas jawaban Claude secara otomatis.**

