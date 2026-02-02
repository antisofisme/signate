# Development Flow Guide

> Panduan flow development untuk memastikan semua standar diterapkan dengan benar.
> Dokumen ini adalah "gatekeeper" yang memvalidasi setiap task terhadap standar yang sudah dibuat.

---

## Cara Menggunakan Dokumen Ini

### Untuk AI Assistant

```
1. Identifikasi jenis task yang diminta user
2. Cari flow yang sesuai di dokumen ini
3. Ikuti setiap STEP secara berurutan
4. Di setiap step:
   - Baca KONTEKS untuk memahami apa yang harus dilakukan
   - Buka ACUAN untuk melihat standar detail
   - Pastikan semua CHECKLIST terpenuhi
   - Baru lanjut ke step berikutnya
5. TIDAK BOLEH skip step manapun
6. Jika ada checklist yang tidak terpenuhi, perbaiki dulu
```

### Untuk Developer

```
1. Sebelum mulai task, tentukan flow mana yang relevan
2. Gunakan checklist sebagai self-review
3. Pastikan semua checkpoint hijau sebelum submit PR
```

---

## Index: Daftar Flow

### A. BACKEND FLOWS

| # | Flow | Deskripsi | Jump |
|---|------|-----------|------|
| A1 | [Create API Endpoint](#flow-a1-create-api-endpoint) | Membuat endpoint API baru | [→](#flow-a1-create-api-endpoint) |
| A2 | [Create Database Table](#flow-a2-create-database-table) | Membuat table/migration baru | [→](#flow-a2-create-database-table) |
| A3 | [Create Service/Business Logic](#flow-a3-create-servicebusiness-logic) | Membuat business logic | [→](#flow-a3-create-servicebusiness-logic) |
| A4 | [Create Background Job](#flow-a4-create-background-job) | Membuat Celery task | [→](#flow-a4-create-background-job) |
| A5 | [Create Event/Message](#flow-a5-create-eventmessage) | Membuat event publisher/consumer | [→](#flow-a5-create-eventmessage) |
| A6 | [Create Integration (External API)](#flow-a6-create-integration) | Integrasi dengan API external | [→](#flow-a6-create-integration) |

### B. FRONTEND FLOWS

| # | Flow | Deskripsi | Jump |
|---|------|-----------|------|
| B1 | [Create UI Component](#flow-b1-create-ui-component) | Membuat component React baru | [→](#flow-b1-create-ui-component) |
| B2 | [Create Page/View](#flow-b2-create-pageview) | Membuat halaman baru | [→](#flow-b2-create-pageview) |
| B3 | [Create Form](#flow-b3-create-form) | Membuat form dengan validasi | [→](#flow-b3-create-form) |
| B4 | [Create Data Table](#flow-b4-create-data-table) | Membuat table dengan fitur lengkap | [→](#flow-b4-create-data-table) |
| B5 | [Create Real-time Feature](#flow-b5-create-real-time-feature) | Fitur dengan WebSocket | [→](#flow-b5-create-real-time-feature) |

### C. FULL FEATURE FLOWS

| # | Flow | Deskripsi | Jump |
|---|------|-----------|------|
| C1 | [Create CRUD Feature](#flow-c1-create-crud-feature) | Fitur CRUD lengkap (BE + FE) | [→](#flow-c1-create-crud-feature) |
| C2 | [Create Report Feature](#flow-c2-create-report-feature) | Fitur report/export | [→](#flow-c2-create-report-feature) |
| C3 | [Create Search Feature](#flow-c3-create-search-feature) | Fitur search dengan Meilisearch | [→](#flow-c3-create-search-feature) |
| C4 | [Create Notification Feature](#flow-c4-create-notification-feature) | Fitur notifikasi | [→](#flow-c4-create-notification-feature) |
| C5 | [Create File Upload Feature](#flow-c5-create-file-upload-feature) | Fitur upload file | [→](#flow-c5-create-file-upload-feature) |

### D. MODULE FLOWS

| # | Flow | Deskripsi | Jump |
|---|------|-----------|------|
| D1 | [Create New Module](#flow-d1-create-new-module) | Membuat module baru dari awal | [→](#flow-d1-create-new-module) |
| D2 | [Add Feature to Module](#flow-d2-add-feature-to-module) | Menambah fitur ke module existing | [→](#flow-d2-add-feature-to-module) |

### E. MAINTENANCE FLOWS

| # | Flow | Deskripsi | Jump |
|---|------|-----------|------|
| E1 | [Bug Fix](#flow-e1-bug-fix) | Memperbaiki bug | [→](#flow-e1-bug-fix) |
| E2 | [Refactoring](#flow-e2-refactoring) | Refactoring code | [→](#flow-e2-refactoring) |
| E3 | [Performance Optimization](#flow-e3-performance-optimization) | Optimasi performa | [→](#flow-e3-performance-optimization) |
| E4 | [Security Fix](#flow-e4-security-fix) | Perbaikan keamanan | [→](#flow-e4-security-fix) |

### F. DOCUMENTATION FLOWS

| # | Flow | Deskripsi | Jump |
|---|------|-----------|------|
| F1 | [Update Module Documentation](#flow-f1-update-module-documentation) | Update docs module | [→](#flow-f1-update-module-documentation) |
| F2 | [Update API Documentation](#flow-f2-update-api-documentation) | Update API docs | [→](#flow-f2-update-api-documentation) |

---

## Standards Reference Map

Peta referensi standar yang digunakan di setiap flow:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STANDARDS REFERENCE MAP                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEVELOPMENT_STANDARDS.md (V1)                                              │
│  ├── #1 Naming Conventions     → API, Database, Frontend, All               │
│  ├── #2 Database Patterns      → Database tasks                             │
│  ├── #3 RBAC/Permission        → API Security, Auth                         │
│  ├── #4 Audit Log              → Database, API (write operations)           │
│  ├── #5 Caching                → API, Performance                           │
│  ├── #6 API Patterns           → API tasks                                  │
│  └── #7 Error Handling         → API, Frontend, All                         │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V2.md                                                │
│  ├── #8 Validation             → API, Frontend Forms                        │
│  ├── #9 Testing                → All tasks (testing phase)                  │
│  ├── #10 Code Structure        → All tasks                                  │
│  ├── #11 Frontend Patterns     → Frontend tasks                             │
│  ├── #12 Infrastructure        → Deployment, DevOps                         │
│  ├── #13 Payment/Licensing     → Payment features                           │
│  ├── #14 TimescaleDB           → Time-series data                           │
│  ├── #15 Logging/Observability → All tasks                                  │
│  └── #16 i18n                  → Frontend, API messages                     │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V3.md                                                │
│  ├── #17 Centralized Registries → Module registration                       │
│  ├── #18 Event/Message Schema  → Event-driven features                      │
│  └── #19 File/Media Handling   → File upload features                       │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V4.md                                                │
│  ├── #20 Real-time/WebSocket   → Real-time features                         │
│  ├── #21 Background Jobs       → Celery tasks                               │
│  └── #22 Search (Meilisearch)  → Search features                            │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V5.md                                                │
│  ├── #23 Notification          → Notification features                      │
│  ├── #24 API Versioning        → API versioning                             │
│  ├── #25 Feature Flags         → Feature toggles                            │
│  └── #26 Performance SLA       → Performance requirements                   │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V6.md                                                │
│  └── #27 Lookup Tables         → Master data, dropdowns                     │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V7.md                                                │
│  ├── #28 State Machine         → Workflow, status transitions               │
│  ├── #29 Multi-tenancy         → All tasks (tenant isolation)               │
│  └── #30 Rate Limiting         → API security                               │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V8.md                                                │
│  ├── #31 Backup/DR             → Database, critical data                    │
│  ├── #32 Webhook               → External integrations                      │
│  └── #33 Report Generation     → Report features                            │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V9.md                                                │
│  ├── #34 Import/Export         → Bulk data features                         │
│  ├── #35 Email Templates       → Email notifications                        │
│  └── #36 PWA/Offline           → Mobile/offline features                    │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V10.md                                               │
│  ├── #37 Circuit Breaker       → External integrations                      │
│  ├── #38 Health Checks         → Service health                             │
│  └── #39 Data Archival         → Old data handling                          │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V11.md                                               │
│  ├── #40 Distributed Tracing   → Observability                              │
│  ├── #41 Secrets Management    → Credentials, API keys                      │
│  └── #42 Scheduled Tasks       → Cron jobs                                  │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V12.md                                               │
│  └── #43 Config Governance     → Configuration management                   │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V13.md                                               │
│  └── #44 Fraud Detection       → Security, audit                            │
│                                                                              │
│  DEVELOPMENT_STANDARDS_V14.md                                               │
│  └── #45 Collaboration Hub     → Internal tools                             │
│                                                                              │
│  OTHER STANDARDS                                                            │
│  ├── DATABASE_SCHEMA_PLATFORM.md      → Database schema reference           │
│  ├── API_CONTRACTS_PLATFORM.md        → API contract reference              │
│  ├── UI_DESIGN_SYSTEM.md              → UI design tokens                    │
│  ├── UI_COMPONENTS.md                 → Component specifications            │
│  ├── SECURITY_AUTH_REQUIREMENTS.md    → Security requirements               │
│  ├── TESTING_STRATEGY.md              → Testing approach                    │
│  ├── MODULE_DOCUMENTATION_STANDARD.md → Module docs format                  │
│  ├── BUSINESS_ACCOUNTING_STANDARDS.md → Business/accounting rules           │
│  ├── SHARED_CODE_STANDARDS.md         → Shared code patterns                │
│  ├── MODULE_ARCHITECTURE.md           → Module structure                    │
│  ├── INTEGRATION_SPECS.md             → External integrations               │
│  └── PUZZLE_ARCHITECTURE.md           → Modular architecture                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Legend

### Status Icons

| Icon | Meaning |
|------|---------|
| ☐ | Checklist item (belum selesai) |
| ☑ | Checklist item (sudah selesai) |
| ⚠️ | Warning - perhatian khusus |
| ❌ | Tidak boleh dilakukan |
| ✅ | Sudah valid/selesai |
| 📖 | Referensi ke dokumen standar |
| 📋 | Konteks/deskripsi |
| ➡️ | Langkah selanjutnya |
| 🔀 | Branching/kondisional |

### Priority Labels

| Label | Meaning |
|-------|---------|
| `[WAJIB]` | Harus dipenuhi, tidak bisa skip |
| `[JIKA ADA]` | Dipenuhi jika relevan dengan task |
| `[OPSIONAL]` | Nice to have, bisa skip jika tidak relevan |

---

# FLOWS

---

## Flow A1: Create API Endpoint

> Membuat endpoint API baru (GET, POST, PUT, DELETE, atau custom action)

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Module sudah ada (jika belum, gunakan Flow D1)
☐ Database table sudah ada (jika belum, gunakan Flow A2)
☐ Sudah jelas endpoint apa yang mau dibuat
```

---

### STEP A1.1: Naming & URL Design

📋 **Konteks:**
Tentukan URL path dan nama endpoint sesuai standar. URL harus konsisten, readable, dan mengikuti REST convention.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #1 Naming Conventions](./DEVELOPMENT_STANDARDS.md)
- [DEVELOPMENT_STANDARDS.md - #6 API Patterns](./DEVELOPMENT_STANDARDS.md)
- [API_CONTRACTS_PLATFORM.md - URL Conventions](./API_CONTRACTS_PLATFORM.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item | Contoh Benar | Contoh Salah |
|---|------|--------------|--------------|
| ☐ | URL menggunakan `kebab-case` | `/room-types` | `/roomTypes`, `/room_types` |
| ☐ | Resource menggunakan kata benda **jamak** | `/rooms` | `/room` |
| ☐ | Tidak ada kata kerja di URL (kecuali action) | `/rooms/{id}` | `/getRoom/{id}` |
| ☐ | Nested resource max 2 level | `/rooms/{id}/reservations` | `/hotels/{id}/floors/{id}/rooms/{id}` |
| ☐ | Custom action menggunakan kata kerja | `/reservations/{id}/check-in` | `/reservations/{id}/checkin-process` |
| ☐ | API prefix sesuai module | `/api/v1/pms/rooms` | `/api/rooms` |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.2](#step-a12-http-method--status-codes)
- Ada ✗ → Perbaiki naming sesuai acuan

---

### STEP A1.2: HTTP Method & Status Codes

📋 **Konteks:**
Tentukan HTTP method yang tepat dan status code yang akan dikembalikan.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #6 API Patterns](./DEVELOPMENT_STANDARDS.md)
- [API_CONTRACTS_PLATFORM.md - HTTP Methods](./API_CONTRACTS_PLATFORM.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | GET untuk read data (tidak mengubah state) |
| ☐ | POST untuk create resource baru |
| ☐ | PUT untuk update resource (full update) |
| ☐ | PATCH untuk partial update (jika dibutuhkan) |
| ☐ | DELETE untuk hapus resource (soft delete) |

**Status Code Reference:**

| Method | Success | Client Error | Server Error |
|--------|---------|--------------|--------------|
| GET | 200 OK | 400, 401, 403, 404 | 500 |
| POST | 201 Created | 400, 401, 403, 409 | 500 |
| PUT/PATCH | 200 OK | 400, 401, 403, 404 | 500 |
| DELETE | 200 OK / 204 No Content | 400, 401, 403, 404 | 500 |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.3](#step-a13-request-schema)
- Ada ✗ → Perbaiki method/status code sesuai acuan

---

### STEP A1.3: Request Schema

📋 **Konteks:**
Definisikan schema untuk request body (POST/PUT) dan query parameters (GET).

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #8 Validation](./DEVELOPMENT_STANDARDS_V2.md)
- [API_CONTRACTS_PLATFORM.md - Request Format](./API_CONTRACTS_PLATFORM.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Request body menggunakan Pydantic schema |
| ☐ | Field names menggunakan `snake_case` |
| ☐ | Required fields ditandai (tidak Optional) |
| ☐ | Field types sesuai (str, int, UUID, datetime, etc) |
| ☐ | Validation rules didefinisikan (min, max, regex, etc) |
| ☐ | Enum values menggunakan string (bukan integer) |

**Contoh Schema:**

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date

class ReservationCreateRequest(BaseModel):
    room_id: UUID = Field(..., description="ID of the room")
    guest_id: UUID = Field(..., description="ID of the guest")
    check_in_date: date = Field(..., description="Check-in date")
    check_out_date: date = Field(..., description="Check-out date")
    adults: int = Field(1, ge=1, le=10, description="Number of adults")
    children: int = Field(0, ge=0, le=10, description="Number of children")
    special_requests: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "room_id": "123e4567-e89b-12d3-a456-426614174000",
                "guest_id": "123e4567-e89b-12d3-a456-426614174001",
                "check_in_date": "2025-01-15",
                "check_out_date": "2025-01-17",
                "adults": 2,
                "children": 0
            }
        }
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.4](#step-a14-response-schema)
- Ada ✗ → Perbaiki schema sesuai acuan

---

### STEP A1.4: Response Schema

📋 **Konteks:**
Definisikan schema untuk response body. Semua response harus mengikuti format standar.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #6 API Patterns](./DEVELOPMENT_STANDARDS.md)
- [API_CONTRACTS_PLATFORM.md - Response Format](./API_CONTRACTS_PLATFORM.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Response menggunakan format standar `{ success, data, meta?, message? }` |
| ☐ | Error response menggunakan format `{ success: false, error: {...} }` |
| ☐ | List response menyertakan `meta` untuk pagination |
| ☐ | Tidak expose data sensitif (password, internal IDs jika tidak perlu) |
| ☐ | Datetime dalam format ISO 8601 dengan timezone |
| ☐ | UUID dalam format string standar |

**Format Response Standar:**

```python
# Success Response (Single)
{
    "success": True,
    "data": {
        "id": "uuid",
        "field_1": "value",
        ...
    },
    "message": "Resource created successfully"  # Optional
}

# Success Response (List)
{
    "success": True,
    "data": [...],
    "meta": {
        "page": 1,
        "limit": 20,
        "total": 100,
        "total_pages": 5
    }
}

# Error Response
{
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {"field": "email", "message": "Invalid email format"}
        ]
    }
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.5](#step-a15-authentication--authorization)
- Ada ✗ → Perbaiki response format sesuai acuan

---

### STEP A1.5: Authentication & Authorization

📋 **Konteks:**
Tentukan security requirements untuk endpoint ini.

📖 **Acuan:**
- [SECURITY_AUTH_REQUIREMENTS.md](./SECURITY_AUTH_REQUIREMENTS.md)
- [DEVELOPMENT_STANDARDS.md - #3 RBAC/Permission](./DEVELOPMENT_STANDARDS.md)
- [DEVELOPMENT_STANDARDS_V7.md - #29 Multi-tenancy](./DEVELOPMENT_STANDARDS_V7.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Endpoint memerlukan authentication? (JWT Bearer token) |
| ☐ | Permission yang diperlukan sudah didefinisikan |
| ☐ | Role yang boleh akses sudah ditentukan |
| ☐ | Tenant isolation diterapkan (filter by tenant_id) |
| ☐ | Resource ownership check (jika user hanya boleh akses miliknya) |

**Contoh Permission Definition:**

```python
# Permission format: {module}.{resource}.{action}
PERMISSIONS = {
    "pms.rooms.read": "Can view rooms",
    "pms.rooms.create": "Can create rooms",
    "pms.rooms.update": "Can update rooms",
    "pms.rooms.delete": "Can delete rooms",
}

# Role mapping
ROLE_PERMISSIONS = {
    "admin": ["pms.rooms.*"],
    "front_desk": ["pms.rooms.read", "pms.rooms.update"],
    "housekeeping": ["pms.rooms.read"],
}
```

☑️ **Checklist Security:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | SQL injection prevention (menggunakan ORM/parameterized queries) |
| ☐ | Tidak ada hardcoded credentials |
| ☐ | Input sanitization untuk string fields |
| ☐ | Rate limiting diterapkan |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.6](#step-a16-implementation)
- Ada ✗ → Perbaiki security sesuai acuan

---

### STEP A1.6: Implementation

📋 **Konteks:**
Implementasi actual code untuk endpoint.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #10 Code Structure](./DEVELOPMENT_STANDARDS_V2.md)
- [SHARED_CODE_STANDARDS.md](./SHARED_CODE_STANDARDS.md)

☑️ **Checklist Code Structure:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Route di file `api/routes/{resource}.py` |
| ☐ | Business logic di `services/{resource}_service.py` |
| ☐ | Schema di `schemas/{resource}.py` |
| ☐ | Tidak ada business logic di route handler |
| ☐ | Service menggunakan dependency injection |

☑️ **Checklist Error Handling:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Try-catch untuk operasi yang bisa fail |
| ☐ | Custom exception untuk business errors |
| ☐ | Error messages user-friendly (tidak expose internal details) |
| ☐ | Proper HTTP status code untuk setiap error type |

📖 **Acuan Error Handling:**
- [DEVELOPMENT_STANDARDS.md - #7 Error Handling](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist Logging:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Log request masuk (info level) |
| ☐ | Log error dengan stack trace (error level) |
| ☐ | Tidak log data sensitif (password, token, etc) |
| ☐ | Include correlation ID untuk tracing |

📖 **Acuan Logging:**
- [DEVELOPMENT_STANDARDS_V2.md - #15 Logging/Observability](./DEVELOPMENT_STANDARDS_V2.md)

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.7](#step-a17-audit-log)
- Ada ✗ → Perbaiki implementation sesuai acuan

---

### STEP A1.7: Audit Log

📋 **Konteks:**
Untuk operasi yang mengubah data (POST, PUT, DELETE), audit log wajib dicatat.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #4 Audit Log](./DEVELOPMENT_STANDARDS.md)

🔀 **Kondisi:**
- **Jika** endpoint adalah GET (read-only) → Skip ke [STEP A1.8](#step-a18-caching)
- **Jika** endpoint mengubah data (POST/PUT/DELETE) → Lanjutkan checklist

☑️ **Checklist:** `[JIKA ADA - untuk write operations]`

| # | Item |
|---|------|
| ☐ | Audit log mencatat: who, what, when, where, old_value, new_value |
| ☐ | Audit log disimpan ke tabel audit yang sesuai |
| ☐ | Sensitive data di-mask di audit log |
| ☐ | Audit log tidak bisa diubah/dihapus (append-only) |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.8](#step-a18-caching)
- Ada ✗ → Perbaiki audit log sesuai acuan

---

### STEP A1.8: Caching

📋 **Konteks:**
Untuk endpoint yang sering diakses, pertimbangkan caching.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #5 Caching](./DEVELOPMENT_STANDARDS.md)

🔀 **Kondisi:**
- **Jika** endpoint adalah GET dan data jarang berubah → Terapkan caching
- **Jika** endpoint adalah POST/PUT/DELETE → Invalidate cache terkait
- **Jika** tidak perlu caching → Skip ke [STEP A1.9](#step-a19-testing)

☑️ **Checklist:** `[JIKA ADA]`

| # | Item |
|---|------|
| ☐ | Cache key menggunakan format standar |
| ☐ | TTL sesuai dengan frekuensi perubahan data |
| ☐ | Cache invalidation saat data berubah |
| ☐ | Tenant-aware cache key (include tenant_id) |

**Cache Key Format:**

```
{tenant_id}:{module}:{resource}:{id}
{tenant_id}:{module}:{resource}:list:{hash_of_filters}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.9](#step-a19-testing)
- Tidak perlu caching → Lanjut ke [STEP A1.9](#step-a19-testing)

---

### STEP A1.9: Testing

📋 **Konteks:**
Tulis unit test dan integration test untuk endpoint.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)
- [DEVELOPMENT_STANDARDS_V2.md - #9 Testing](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Unit test untuk service layer |
| ☐ | Integration test untuk endpoint |
| ☐ | Test happy path (success case) |
| ☐ | Test error cases (validation, not found, unauthorized) |
| ☐ | Test edge cases |
| ☐ | Mock external dependencies |
| ☐ | Test coverage minimal 80% |

**Test File Location:**

```
tests/
├── unit/
│   └── services/
│       └── test_{resource}_service.py
└── integration/
    └── api/
        └── test_{resource}_api.py
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A1.10](#step-a110-documentation)
- Ada ✗ → Tulis test yang kurang

---

### STEP A1.10: Documentation

📋 **Konteks:**
Update dokumentasi untuk endpoint baru.

📖 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)
- Template: [API.md template](./MODULE_DOCUMENTATION_STANDARD.md#43-apimd-api-endpoints)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Endpoint ditambahkan ke `docs/modules/{module}/API.md` |
| ☐ | Request schema documented dengan contoh |
| ☐ | Response schema documented dengan contoh |
| ☐ | Error codes documented |
| ☐ | Permission requirements documented |
| ☐ | CHANGELOG.md diupdate |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW A1 SELESAI**
- Ada ✗ → Update dokumentasi yang kurang

---

### STEP A1.11: Final Checklist

Sebelum submit/merge, pastikan semua terpenuhi:

```
FINAL CHECKLIST - CREATE API ENDPOINT
═══════════════════════════════════════

Naming & Design
☐ URL sesuai convention (kebab-case, plural, REST)
☐ HTTP method benar
☐ Status codes benar

Schema
☐ Request schema dengan validasi
☐ Response schema format standar

Security
☐ Authentication diterapkan
☐ Authorization/permission diterapkan
☐ Tenant isolation diterapkan
☐ No SQL injection
☐ Rate limiting

Implementation
☐ Code structure sesuai standar
☐ Error handling proper
☐ Logging diterapkan
☐ Audit log (jika write operation)
☐ Caching (jika applicable)

Quality
☐ Unit tests written
☐ Integration tests written
☐ Test coverage >= 80%
☐ Documentation updated
☐ CHANGELOG updated
```

---

## Flow A2: Create Database Table

> Membuat table database baru dengan migration

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Module sudah ada
☐ Sudah jelas entity/table apa yang mau dibuat
☐ Sudah tahu relasi dengan table lain
```

---

### STEP A2.1: Table Design

📋 **Konteks:**
Design schema table sebelum membuat migration.

📖 **Acuan:**
- [DATABASE_SCHEMA_PLATFORM.md](./DATABASE_SCHEMA_PLATFORM.md)
- [DEVELOPMENT_STANDARDS.md - #2 Database Patterns](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist Naming:** `[WAJIB]`

| # | Item | Contoh Benar | Contoh Salah |
|---|------|--------------|--------------|
| ☐ | Table name `snake_case` plural | `room_types` | `RoomType`, `room-types` |
| ☐ | Column name `snake_case` | `check_in_date` | `checkInDate` |
| ☐ | Primary key bernama `id` | `id` | `room_id`, `pk_room` |
| ☐ | Foreign key format `{table_singular}_id` | `room_id` | `fk_room`, `room` |
| ☐ | Boolean prefix `is_` atau `has_` | `is_active` | `active`, `status` |
| ☐ | Timestamp suffix `_at` | `created_at` | `created`, `create_time` |

☑️ **Checklist Required Columns:** `[WAJIB]`

| # | Column | Type | Description |
|---|--------|------|-------------|
| ☐ | `id` | UUID | Primary key (gen_random_uuid) |
| ☐ | `tenant_id` | UUID | Foreign key to tenants (multi-tenancy) |
| ☐ | `created_at` | TIMESTAMPTZ | Record creation time |
| ☐ | `updated_at` | TIMESTAMPTZ | Last update time |
| ☐ | `deleted_at` | TIMESTAMPTZ | Soft delete (nullable) |
| ☐ | `created_by` | UUID | User who created (nullable) |
| ☐ | `updated_by` | UUID | User who last updated (nullable) |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A2.2](#step-a22-data-types)
- Ada ✗ → Perbaiki naming sesuai acuan

---

### STEP A2.2: Data Types

📋 **Konteks:**
Pilih data type yang tepat untuk setiap column.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #2 Database Patterns](./DEVELOPMENT_STANDARDS.md)
- [DATABASE_SCHEMA_PLATFORM.md - Data Types](./DATABASE_SCHEMA_PLATFORM.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | UUID untuk ID dan foreign keys |
| ☐ | VARCHAR dengan length limit untuk strings |
| ☐ | TEXT untuk long text tanpa limit |
| ☐ | DECIMAL(15,2) untuk monetary values |
| ☐ | TIMESTAMPTZ untuk datetime (dengan timezone) |
| ☐ | DATE untuk date-only |
| ☐ | BOOLEAN untuk true/false |
| ☐ | JSONB untuk flexible/nested data |
| ☐ | INTEGER untuk whole numbers |
| ☐ | SMALLINT untuk small enums (max 32767) |

**Type Reference:**

| Use Case | Recommended Type |
|----------|------------------|
| ID, Foreign Key | `UUID` |
| Name, Title | `VARCHAR(100-255)` |
| Code, Short Text | `VARCHAR(20-50)` |
| Description | `TEXT` |
| Email | `VARCHAR(255)` |
| Phone | `VARCHAR(20)` |
| Money/Currency | `DECIMAL(15,2)` |
| Percentage | `DECIMAL(5,2)` |
| Quantity | `INTEGER` |
| Status/Type (enum) | `VARCHAR(20)` or `SMALLINT` |
| Settings/Config | `JSONB` |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A2.3](#step-a23-constraints--indexes)
- Ada ✗ → Perbaiki data types

---

### STEP A2.3: Constraints & Indexes

📋 **Konteks:**
Definisikan constraints dan indexes untuk data integrity dan performance.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #2 Database Patterns](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist Constraints:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Primary key constraint pada `id` |
| ☐ | Foreign key constraints dengan ON DELETE action |
| ☐ | NOT NULL pada required fields |
| ☐ | UNIQUE constraint jika diperlukan |
| ☐ | CHECK constraint untuk validasi (enum, range) |
| ☐ | DEFAULT values untuk fields dengan default |

☑️ **Checklist Indexes:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Index pada `tenant_id` (semua table) |
| ☐ | Index pada foreign keys |
| ☐ | Index pada fields yang sering di-filter |
| ☐ | Index pada fields yang sering di-sort |
| ☐ | Composite index jika query sering kombinasi fields |
| ☐ | Partial index jika hanya subset data yang sering diquery |

**Index Naming Convention:**

```
idx_{table}_{column}              -- single column
idx_{table}_{col1}_{col2}         -- composite
idx_{table}_{column}_partial      -- partial index
uq_{table}_{column}               -- unique constraint
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A2.4](#step-a24-relationships)
- Ada ✗ → Perbaiki constraints/indexes

---

### STEP A2.4: Relationships

📋 **Konteks:**
Definisikan relasi dengan table lain.

📖 **Acuan:**
- [DATABASE_SCHEMA_PLATFORM.md - Relationships](./DATABASE_SCHEMA_PLATFORM.md)

☑️ **Checklist:** `[JIKA ADA relasi]`

| # | Item |
|---|------|
| ☐ | Foreign key column didefinisikan |
| ☐ | ON DELETE action sesuai (RESTRICT, CASCADE, SET NULL) |
| ☐ | ON UPDATE action sesuai (biasanya CASCADE) |
| ☐ | Index pada foreign key column |
| ☐ | Relationship type jelas (1:1, 1:N, N:M) |

**ON DELETE Reference:**

| Action | When to Use |
|--------|-------------|
| RESTRICT | Tidak boleh hapus parent jika ada child |
| CASCADE | Hapus child jika parent dihapus |
| SET NULL | Set FK ke NULL jika parent dihapus |
| SET DEFAULT | Set FK ke default value |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A2.5](#step-a25-migration-file)
- Tidak ada relasi → Lanjut ke [STEP A2.5](#step-a25-migration-file)

---

### STEP A2.5: Migration File

📋 **Konteks:**
Buat migration file menggunakan Alembic.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #2 Database Patterns](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Migration file dibuat dengan `alembic revision` |
| ☐ | File name descriptive: `{revision}_create_{table}_table.py` |
| ☐ | `upgrade()` function creates table |
| ☐ | `downgrade()` function drops table |
| ☐ | Schema prefix sesuai module (jika pakai schema per module) |
| ☐ | Migration tested locally |

**Migration File Template:**

```python
"""create rooms table

Revision ID: abc123
Revises: xyz789
Create Date: 2025-01-15 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('room_number', sa.String(20), nullable=False),
        sa.Column('room_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('floor', sa.Integer),
        sa.Column('status', sa.String(20), nullable=False, server_default='available'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'],
                                ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['room_type_id'], ['pms.room_types.id'],
                                ondelete='RESTRICT'),
        sa.UniqueConstraint('tenant_id', 'room_number', name='uq_rooms_tenant_number'),
        schema='pms'
    )

    op.create_index('idx_rooms_tenant_id', 'rooms', ['tenant_id'], schema='pms')
    op.create_index('idx_rooms_room_type_id', 'rooms', ['room_type_id'], schema='pms')
    op.create_index('idx_rooms_status', 'rooms', ['status'], schema='pms')

def downgrade():
    op.drop_table('rooms', schema='pms')
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A2.6](#step-a26-model-definition)
- Ada ✗ → Perbaiki migration file

---

### STEP A2.6: Model Definition

📋 **Konteks:**
Buat SQLAlchemy model yang mapping ke table.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #10 Code Structure](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Model class di `models/{entity}.py` |
| ☐ | Inherit dari Base model |
| ☐ | Table name sesuai migration |
| ☐ | Relationships didefinisikan |
| ☐ | `__repr__` method untuk debugging |

**Model Template:**

```python
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Room(Base):
    __tablename__ = 'rooms'
    __table_args__ = {'schema': 'pms'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('platform.tenants.id'), nullable=False)
    room_number = Column(String(20), nullable=False)
    room_type_id = Column(UUID(as_uuid=True), ForeignKey('pms.room_types.id'), nullable=False)
    floor = Column(Integer)
    status = Column(String(20), nullable=False, default='available')
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default='now()')
    updated_at = Column(DateTime(timezone=True), server_default='now()', onupdate='now()')
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    room_type = relationship("RoomType", back_populates="rooms")
    reservations = relationship("Reservation", back_populates="room")

    def __repr__(self):
        return f"<Room {self.room_number}>"
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A2.7](#step-a27-documentation)
- Ada ✗ → Perbaiki model

---

### STEP A2.7: Documentation

📋 **Konteks:**
Update dokumentasi database untuk table baru.

📖 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)
- Template: [DATABASE.md template](./MODULE_DOCUMENTATION_STANDARD.md#42-databasemd-erd--tables)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Table ditambahkan ke `docs/modules/{module}/DATABASE.md` |
| ☐ | Semua columns documented |
| ☐ | Indexes documented |
| ☐ | Foreign keys documented |
| ☐ | ERD diagram updated |
| ☐ | CHANGELOG.md diupdate |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW A2 SELESAI**
- Ada ✗ → Update dokumentasi

---

### STEP A2.8: Final Checklist

```
FINAL CHECKLIST - CREATE DATABASE TABLE
═══════════════════════════════════════════

Design
☐ Table name snake_case plural
☐ Column names snake_case
☐ Data types appropriate

Required Columns
☐ id (UUID, PK)
☐ tenant_id (UUID, FK)
☐ created_at (TIMESTAMPTZ)
☐ updated_at (TIMESTAMPTZ)
☐ deleted_at (TIMESTAMPTZ, nullable)

Constraints & Indexes
☐ Primary key
☐ Foreign keys with ON DELETE
☐ NOT NULL constraints
☐ Index on tenant_id
☐ Index on foreign keys

Implementation
☐ Migration file created
☐ Migration tested locally
☐ Model class created
☐ Relationships defined

Documentation
☐ DATABASE.md updated
☐ ERD updated
☐ CHANGELOG updated
```

---

---

## Flow A3: Create Service/Business Logic

> Membuat service layer yang berisi business logic

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Module sudah ada
☐ Database model sudah ada (jika perlu)
☐ Sudah jelas use case apa yang mau diimplementasi
```

---

### STEP A3.1: Service Design

📋 **Konteks:**
Design service class dan method yang akan dibuat.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #10 Code Structure](./DEVELOPMENT_STANDARDS_V2.md)
- [SHARED_CODE_STANDARDS.md](./SHARED_CODE_STANDARDS.md)

☑️ **Checklist Service Design:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Satu service per entity/domain |
| ☐ | Method names verb + noun (get_room, create_reservation) |
| ☐ | Service tidak depend ke HTTP layer (tidak import FastAPI) |
| ☐ | Service menerima primitive types/models, bukan Request objects |
| ☐ | Return types jelas (model, DTO, atau primitive) |

**Service Structure:**

```
services/
├── {entity}_service.py      # Main service
├── {domain}_validator.py    # Business validation
└── {domain}_calculator.py   # Complex calculations
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A3.2](#step-a32-dependency-injection)
- Ada ✗ → Perbaiki design

---

### STEP A3.2: Dependency Injection

📋 **Konteks:**
Setup dependencies yang dibutuhkan service (database, cache, external services).

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #10 Code Structure](./DEVELOPMENT_STANDARDS_V2.md)
- [SHARED_CODE_STANDARDS.md - Dependency Injection](./SHARED_CODE_STANDARDS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Dependencies di-inject via constructor |
| ☐ | Tidak ada global state dalam service |
| ☐ | Repository pattern untuk database access |
| ☐ | Interface/Protocol untuk external dependencies (mockable) |

**Service Template:**

```python
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate
from app.repositories.room_repository import RoomRepository

class RoomService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = RoomRepository(db)

    def get_by_id(self, room_id: UUID) -> Optional[Room]:
        return self.repository.get_by_id(room_id, self.tenant_id)

    def get_all(self, skip: int = 0, limit: int = 20) -> List[Room]:
        return self.repository.get_all(self.tenant_id, skip, limit)

    def create(self, data: RoomCreate) -> Room:
        # Business logic here
        self._validate_room_number(data.room_number)
        return self.repository.create(data, self.tenant_id)
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A3.3](#step-a33-business-rules)
- Ada ✗ → Perbaiki DI setup

---

### STEP A3.3: Business Rules

📋 **Konteks:**
Implementasi business rules dan validasi bisnis.

📖 **Acuan:**
- [BUSINESS_ACCOUNTING_STANDARDS.md](./BUSINESS_ACCOUNTING_STANDARDS.md)
- [BUSINESS_ACCOUNTING_STANDARDS_V2.md](./BUSINESS_ACCOUNTING_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Business rules terpisah dari validation input (Pydantic) |
| ☐ | Business rules bisa di-test secara independen |
| ☐ | Error messages jelas untuk business rule violations |
| ☐ | Business rules documented di module docs |

☑️ **Checklist State Machine (jika ada):** `[JIKA ADA]`

| # | Item |
|---|------|
| ☐ | State transitions didefinisikan di state machine |
| ☐ | Invalid transitions raise BusinessError |
| ☐ | Transition triggers (side effects) terpisah dari state change |

📖 **Acuan State Machine:**
- [DEVELOPMENT_STANDARDS_V7.md - #28 State Machine](./DEVELOPMENT_STANDARDS_V7.md)

**Business Error Example:**

```python
from app.core.exceptions import BusinessError

class RoomService:
    def check_in(self, reservation_id: UUID) -> Reservation:
        reservation = self.reservation_repo.get_by_id(reservation_id)

        # Business rule: Can only check-in on or after check-in date
        if reservation.check_in_date > date.today():
            raise BusinessError(
                code="CHECKIN_TOO_EARLY",
                message=f"Cannot check-in before {reservation.check_in_date}"
            )

        # Business rule: Room must be clean
        room = self.room_repo.get_by_id(reservation.room_id)
        if room.housekeeping_status != 'clean':
            raise BusinessError(
                code="ROOM_NOT_READY",
                message="Room is not ready for check-in"
            )

        # Proceed with check-in
        return self._process_check_in(reservation)
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A3.4](#step-a34-transaction-handling)
- Ada ✗ → Perbaiki business rules

---

### STEP A3.4: Transaction Handling

📋 **Konteks:**
Handle database transactions untuk konsistensi data.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #2 Database Patterns](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Operasi yang terkait dalam satu transaction |
| ☐ | Rollback jika ada error |
| ☐ | Tidak nested transactions tanpa savepoints |
| ☐ | Transaction scope seminimal mungkin |
| ☐ | Hindari long-running transactions |

**Transaction Pattern:**

```python
from app.core.database import get_db_transaction

class ReservationService:
    def create_with_payment(self, data: ReservationCreate) -> Reservation:
        with get_db_transaction(self.db) as session:
            # Create reservation
            reservation = self.reservation_repo.create(data)

            # Create initial folio
            folio = self.folio_repo.create(reservation.id)

            # Create payment record if deposit required
            if data.deposit_amount > 0:
                payment = self.payment_repo.create(
                    folio_id=folio.id,
                    amount=data.deposit_amount
                )

            # All committed together, or all rolled back
            return reservation
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A3.5](#step-a35-error-handling)
- Ada ✗ → Perbaiki transaction handling

---

### STEP A3.5: Error Handling

📋 **Konteks:**
Handle errors dengan proper exception types.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #7 Error Handling](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Custom exception untuk business errors |
| ☐ | Tidak catch generic Exception (kecuali di top level) |
| ☐ | Re-raise dengan context jika perlu |
| ☐ | Tidak suppress errors tanpa logging |
| ☐ | Error messages tidak expose internal details |

**Exception Hierarchy:**

```python
# app/core/exceptions.py

class AppException(Exception):
    """Base exception"""
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

class BusinessError(AppException):
    """Business rule violation"""
    pass

class ValidationError(AppException):
    """Input validation error"""
    pass

class NotFoundError(AppException):
    """Resource not found"""
    pass

class ConflictError(AppException):
    """Resource conflict (duplicate, etc)"""
    pass

class AuthorizationError(AppException):
    """Permission denied"""
    pass
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A3.6](#step-a36-logging)
- Ada ✗ → Perbaiki error handling

---

### STEP A3.6: Logging

📋 **Konteks:**
Tambahkan logging untuk observability.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #15 Logging/Observability](./DEVELOPMENT_STANDARDS_V2.md)
- [DEVELOPMENT_STANDARDS_V11.md - #40 Distributed Tracing](./DEVELOPMENT_STANDARDS_V11.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Log method entry (debug level) dengan parameters |
| ☐ | Log important business events (info level) |
| ☐ | Log errors dengan full context (error level) |
| ☐ | Tidak log sensitive data |
| ☐ | Include correlation ID untuk tracing |
| ☐ | Include tenant_id di semua logs |

**Logging Pattern:**

```python
import structlog
from app.core.context import get_correlation_id

logger = structlog.get_logger(__name__)

class ReservationService:
    def create(self, data: ReservationCreate) -> Reservation:
        logger.info(
            "Creating reservation",
            tenant_id=str(self.tenant_id),
            correlation_id=get_correlation_id(),
            room_id=str(data.room_id),
            check_in=str(data.check_in_date),
            check_out=str(data.check_out_date)
        )

        try:
            reservation = self._process_create(data)
            logger.info(
                "Reservation created successfully",
                reservation_id=str(reservation.id)
            )
            return reservation
        except Exception as e:
            logger.error(
                "Failed to create reservation",
                error=str(e),
                exc_info=True
            )
            raise
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A3.7](#step-a37-testing)
- Ada ✗ → Perbaiki logging

---

### STEP A3.7: Testing

📋 **Konteks:**
Tulis unit tests untuk service.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)
- [DEVELOPMENT_STANDARDS_V2.md - #9 Testing](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test setiap method di service |
| ☐ | Test happy path |
| ☐ | Test business rule violations |
| ☐ | Test edge cases |
| ☐ | Mock dependencies (repository, external services) |
| ☐ | Test coverage minimal 80% |

**Test File Location:**

```
tests/
└── unit/
    └── services/
        └── test_{entity}_service.py
```

**Test Example:**

```python
import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import date

from app.services.reservation_service import ReservationService
from app.core.exceptions import BusinessError

class TestReservationService:
    def setup_method(self):
        self.db = MagicMock()
        self.tenant_id = uuid4()
        self.service = ReservationService(self.db, self.tenant_id)

    def test_check_in_success(self):
        # Arrange
        reservation = Mock(check_in_date=date.today())
        room = Mock(housekeeping_status='clean')
        self.service.reservation_repo.get_by_id.return_value = reservation
        self.service.room_repo.get_by_id.return_value = room

        # Act
        result = self.service.check_in(reservation.id)

        # Assert
        assert result.status == 'checked_in'

    def test_check_in_fails_if_too_early(self):
        # Arrange
        reservation = Mock(check_in_date=date.today() + timedelta(days=1))
        self.service.reservation_repo.get_by_id.return_value = reservation

        # Act & Assert
        with pytest.raises(BusinessError) as exc:
            self.service.check_in(reservation.id)
        assert exc.value.code == "CHECKIN_TOO_EARLY"
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A3.8](#step-a38-documentation)
- Ada ✗ → Tulis tests yang kurang

---

### STEP A3.8: Documentation

📋 **Konteks:**
Document business logic dan rules di module documentation.

📖 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)
- Template: [BUSINESS_RULES.md](./MODULE_DOCUMENTATION_STANDARD.md#46-business_rulesmd-business-rules)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Service methods documented (docstrings) |
| ☐ | Business rules added to `docs/modules/{module}/BUSINESS_RULES.md` |
| ☐ | Workflows updated di `docs/modules/{module}/WORKFLOWS.md` |
| ☐ | CHANGELOG.md diupdate |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW A3 SELESAI**
- Ada ✗ → Update dokumentasi

---

### STEP A3.9: Final Checklist

```
FINAL CHECKLIST - CREATE SERVICE/BUSINESS LOGIC
══════════════════════════════════════════════════

Design
☐ One service per entity/domain
☐ Method names are verbs
☐ No HTTP layer dependencies
☐ Clear return types

Dependencies
☐ Dependencies injected via constructor
☐ No global state
☐ Repository pattern used
☐ External deps mockable

Business Rules
☐ Rules separate from input validation
☐ Rules are testable
☐ Error messages clear
☐ State machine defined (if applicable)

Implementation
☐ Proper transaction handling
☐ Custom exceptions used
☐ Proper error handling
☐ Logging implemented
☐ Correlation ID included

Quality
☐ Unit tests written
☐ Coverage >= 80%
☐ Documentation updated
☐ CHANGELOG updated
```

---

## Flow A4: Create Background Job

> Membuat Celery task untuk background processing

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Celery sudah ter-setup di project
☐ RabbitMQ/Redis sudah running untuk broker
☐ Sudah jelas job apa yang mau dibuat
```

---

### STEP A4.1: Job Design

📋 **Konteks:**
Design background job - tentukan tipe, queue, dan retry strategy.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #21 Background Jobs (Celery)](./DEVELOPMENT_STANDARDS_V4.md)

☑️ **Checklist Job Type:** `[WAJIB]`

| # | Item | Checklist |
|---|------|-----------|
| ☐ | Tentukan job type | One-time / Periodic / Triggered |
| ☐ | Tentukan priority | High / Normal / Low |
| ☐ | Tentukan queue | default / {module} / high_priority |
| ☐ | Estimasi execution time | < 1min / 1-10min / > 10min |

**Queue Mapping:**

| Queue | Use Case | Priority |
|-------|----------|----------|
| `high_priority` | Payment, critical ops | Urgent |
| `default` | General tasks | Normal |
| `reports` | Report generation | Low |
| `bulk` | Bulk operations | Low |
| `scheduled` | Periodic tasks | Normal |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A4.2](#step-a42-idempotency)
- Ada ✗ → Perbaiki design

---

### STEP A4.2: Idempotency

📋 **Konteks:**
Background jobs harus idempotent - bisa di-retry tanpa side effects.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #21 Background Jobs](./DEVELOPMENT_STANDARDS_V4.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Job bisa di-execute multiple times dengan hasil sama |
| ☐ | Check existing state sebelum proses |
| ☐ | Use idempotency key untuk operasi critical |
| ☐ | Tidak kirim email/notification multiple times |

**Idempotency Pattern:**

```python
from celery import shared_task
from app.models.job_execution import JobExecution

@shared_task(bind=True)
def send_welcome_email(self, guest_id: str, idempotency_key: str):
    # Check if already executed
    existing = JobExecution.query.filter_by(
        idempotency_key=idempotency_key,
        status='completed'
    ).first()

    if existing:
        logger.info(f"Job already executed: {idempotency_key}")
        return {"status": "skipped", "reason": "already_executed"}

    # Record job start
    execution = JobExecution.create(
        idempotency_key=idempotency_key,
        task_id=self.request.id,
        status='processing'
    )

    try:
        # Do the actual work
        _send_email(guest_id)
        execution.mark_completed()
        return {"status": "success"}
    except Exception as e:
        execution.mark_failed(str(e))
        raise
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A4.3](#step-a43-retry-strategy)
- Ada ✗ → Perbaiki idempotency

---

### STEP A4.3: Retry Strategy

📋 **Konteks:**
Configure retry behavior untuk handle transient failures.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #21 Background Jobs](./DEVELOPMENT_STANDARDS_V4.md)
- [DEVELOPMENT_STANDARDS_V10.md - #37 Circuit Breaker](./DEVELOPMENT_STANDARDS_V10.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Max retries ditentukan |
| ☐ | Retry delay dengan exponential backoff |
| ☐ | Define retryable vs non-retryable exceptions |
| ☐ | Dead letter queue untuk failed jobs |

**Retry Configuration:**

```python
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from app.core.exceptions import NonRetryableError

@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,  # max 10 minutes
    retry_kwargs={'max_retries': 5},
    retry_jitter=True
)
def process_payment(self, payment_id: str):
    try:
        _process(payment_id)
    except NonRetryableError as e:
        # Don't retry for business errors
        logger.error(f"Non-retryable error: {e}")
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        # Will be retried automatically
        raise
```

**Backoff Schedule:**

| Retry | Delay (approx) |
|-------|----------------|
| 1 | 1 second |
| 2 | 2 seconds |
| 3 | 4 seconds |
| 4 | 8 seconds |
| 5 | 16 seconds |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A4.4](#step-a44-task-implementation)
- Ada ✗ → Perbaiki retry strategy

---

### STEP A4.4: Task Implementation

📋 **Konteks:**
Implement the actual task.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #21 Background Jobs](./DEVELOPMENT_STANDARDS_V4.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Task di folder `tasks/{module}/` |
| ☐ | Task name descriptive |
| ☐ | Input parameters serializable (no complex objects) |
| ☐ | Database session di-create dalam task (not passed) |
| ☐ | Proper resource cleanup (connections, files) |
| ☐ | Progress tracking untuk long-running tasks |

**Task File Structure:**

```
tasks/
├── __init__.py
├── base.py           # Base task class
├── pms/
│   ├── __init__.py
│   ├── reservation_tasks.py
│   └── report_tasks.py
└── accounting/
    ├── __init__.py
    └── journal_tasks.py
```

**Task Template:**

```python
# tasks/pms/report_tasks.py

from celery import shared_task
from app.core.database import get_db_session
from app.services.report_service import ReportService
import structlog

logger = structlog.get_logger(__name__)

@shared_task(
    bind=True,
    name='pms.generate_occupancy_report',
    queue='reports',
    soft_time_limit=300,  # 5 minutes
    time_limit=360        # 6 minutes hard limit
)
def generate_occupancy_report(
    self,
    tenant_id: str,
    start_date: str,
    end_date: str,
    requested_by: str
):
    """Generate occupancy report for date range."""
    logger.info(
        "Starting occupancy report generation",
        task_id=self.request.id,
        tenant_id=tenant_id,
        date_range=f"{start_date} - {end_date}"
    )

    with get_db_session() as db:
        service = ReportService(db, tenant_id)

        try:
            # Update progress
            self.update_state(state='PROGRESS', meta={'progress': 10})

            # Generate report
            report = service.generate_occupancy_report(
                start_date=start_date,
                end_date=end_date
            )

            self.update_state(state='PROGRESS', meta={'progress': 80})

            # Save to storage
            file_url = service.save_report(report)

            # Notify requester
            _notify_report_ready(requested_by, file_url)

            logger.info("Report generated successfully", file_url=file_url)
            return {
                "status": "success",
                "file_url": file_url
            }

        except Exception as e:
            logger.error("Report generation failed", error=str(e))
            raise
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A4.5](#step-a45-monitoring)
- Ada ✗ → Perbaiki implementation

---

### STEP A4.5: Monitoring

📋 **Konteks:**
Setup monitoring dan alerting untuk jobs.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #15 Logging/Observability](./DEVELOPMENT_STANDARDS_V2.md)
- [DEVELOPMENT_STANDARDS_V11.md - #40 Distributed Tracing](./DEVELOPMENT_STANDARDS_V11.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Job start/complete/fail logged |
| ☐ | Execution time logged |
| ☐ | Metrics exported (Prometheus) |
| ☐ | Alert untuk failed jobs |
| ☐ | Dashboard untuk job monitoring |

**Metrics to Track:**

| Metric | Type | Description |
|--------|------|-------------|
| `celery_task_started_total` | Counter | Tasks started |
| `celery_task_succeeded_total` | Counter | Tasks succeeded |
| `celery_task_failed_total` | Counter | Tasks failed |
| `celery_task_duration_seconds` | Histogram | Task duration |
| `celery_queue_length` | Gauge | Queue size |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A4.6](#step-a46-scheduled-tasks)
- Ada ✗ → Setup monitoring

---

### STEP A4.6: Scheduled Tasks

📋 **Konteks:**
Untuk periodic tasks, setup schedule dengan Celery Beat.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V11.md - #42 Scheduled Tasks](./DEVELOPMENT_STANDARDS_V11.md)

🔀 **Kondisi:**
- **Jika** task adalah periodic → Lanjutkan checklist
- **Jika** task adalah one-time/triggered → Skip ke [STEP A4.7](#step-a47-testing)

☑️ **Checklist:** `[JIKA ADA - untuk periodic tasks]`

| # | Item |
|---|------|
| ☐ | Schedule didefinisikan di config |
| ☐ | Cron expression valid |
| ☐ | Timezone specified (UTC atau local) |
| ☐ | Overlap prevention (single instance) |
| ☐ | Schedule documented |

**Celery Beat Schedule:**

```python
# config/celery_schedule.py

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Run daily at 2 AM
    'generate-daily-report': {
        'task': 'pms.generate_daily_report',
        'schedule': crontab(hour=2, minute=0),
        'kwargs': {'report_type': 'daily_summary'},
        'options': {'queue': 'reports'}
    },

    # Run every hour
    'sync-channel-rates': {
        'task': 'channel.sync_rates',
        'schedule': crontab(minute=0),  # every hour at :00
        'options': {'queue': 'default'}
    },

    # Run every 5 minutes
    'check-pending-payments': {
        'task': 'payment.check_pending',
        'schedule': 300.0,  # 5 minutes in seconds
        'options': {'queue': 'high_priority'}
    },
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A4.7](#step-a47-testing)
- Tidak periodic → Lanjut ke [STEP A4.7](#step-a47-testing)

---

### STEP A4.7: Testing

📋 **Konteks:**
Test background jobs.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Unit test task logic (sync) |
| ☐ | Integration test dengan Celery eager mode |
| ☐ | Test retry behavior |
| ☐ | Test idempotency |
| ☐ | Test failure scenarios |

**Test Pattern:**

```python
import pytest
from unittest.mock import patch, MagicMock
from tasks.pms.report_tasks import generate_occupancy_report

class TestGenerateOccupancyReport:

    @pytest.fixture
    def celery_app(self, celery_app):
        celery_app.conf.task_always_eager = True
        return celery_app

    def test_generates_report_successfully(self):
        with patch('tasks.pms.report_tasks.ReportService') as mock_service:
            mock_service.return_value.generate_occupancy_report.return_value = Mock()
            mock_service.return_value.save_report.return_value = "https://..."

            result = generate_occupancy_report.delay(
                tenant_id="uuid",
                start_date="2025-01-01",
                end_date="2025-01-31",
                requested_by="user-uuid"
            )

            assert result.get()['status'] == 'success'

    def test_idempotent_execution(self):
        # Execute twice with same idempotency key
        # Second execution should skip
        pass
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A4.8](#step-a48-documentation)
- Ada ✗ → Tulis tests

---

### STEP A4.8: Documentation

📋 **Konteks:**
Document background job di module documentation.

📖 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Task documented di `docs/modules/{module}/FEATURES.md` |
| ☐ | Queue dan retry config documented |
| ☐ | Schedule documented (jika periodic) |
| ☐ | Input/output documented |
| ☐ | CHANGELOG.md diupdate |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW A4 SELESAI**
- Ada ✗ → Update dokumentasi

---

### STEP A4.9: Final Checklist

```
FINAL CHECKLIST - CREATE BACKGROUND JOB
═══════════════════════════════════════════

Design
☐ Job type determined (one-time/periodic/triggered)
☐ Queue assigned
☐ Priority set
☐ Execution time estimated

Reliability
☐ Idempotent design
☐ Retry strategy configured
☐ Max retries set
☐ Exponential backoff
☐ Dead letter queue

Implementation
☐ Task in correct folder
☐ Serializable parameters
☐ Proper resource cleanup
☐ Progress tracking (if long-running)

Monitoring
☐ Logging implemented
☐ Metrics exported
☐ Alerts configured

Schedule (if periodic)
☐ Cron expression valid
☐ Timezone specified
☐ Overlap prevention

Quality
☐ Unit tests written
☐ Integration tests written
☐ Documentation updated
☐ CHANGELOG updated
```

---

## Flow A5: Create Event/Message

> Membuat event publisher atau consumer untuk event-driven features

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ RabbitMQ sudah ter-setup
☐ Event schema registry sudah ada
☐ Sudah jelas event apa yang mau dibuat
```

---

### STEP A5.1: Event Design

📋 **Konteks:**
Design event - tentukan tipe, naming, dan payload structure.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V3.md - #18 Event/Message Schema](./DEVELOPMENT_STANDARDS_V3.md)

☑️ **Checklist Event Naming:** `[WAJIB]`

| # | Item | Format |
|---|------|--------|
| ☐ | Event name format | `{domain}.{entity}.{action}` |
| ☐ | Domain = module name | `pms`, `accounting`, `hrm` |
| ☐ | Entity = resource | `reservation`, `payment`, `guest` |
| ☐ | Action = past tense | `created`, `updated`, `cancelled` |

**Event Name Examples:**

| Event Name | Description |
|------------|-------------|
| `pms.reservation.created` | New reservation created |
| `pms.reservation.checked_in` | Guest checked in |
| `pms.reservation.cancelled` | Reservation cancelled |
| `accounting.payment.received` | Payment received |
| `accounting.invoice.generated` | Invoice generated |

☑️ **Checklist Event Type:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Event type ditentukan: Domain Event / Integration Event |
| ☐ | Exchange type ditentukan: Topic / Fanout / Direct |
| ☐ | Routing key pattern ditentukan |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A5.2](#step-a52-event-schema)
- Ada ✗ → Perbaiki naming

---

### STEP A5.2: Event Schema

📋 **Konteks:**
Define event schema dengan required fields.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V3.md - #18 Event/Message Schema](./DEVELOPMENT_STANDARDS_V3.md)

☑️ **Checklist Required Fields:** `[WAJIB]`

| # | Field | Type | Description |
|---|-------|------|-------------|
| ☐ | `event_id` | UUID | Unique event ID |
| ☐ | `event_type` | String | Event name |
| ☐ | `event_version` | String | Schema version (e.g., "1.0") |
| ☐ | `timestamp` | ISO 8601 | Event time |
| ☐ | `source` | String | Publisher service |
| ☐ | `tenant_id` | UUID | Tenant ID |
| ☐ | `correlation_id` | UUID | Request correlation ID |
| ☐ | `data` | Object | Event payload |

**Event Schema Template:**

```python
# schemas/events/{entity}_events.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class EventMetadata(BaseModel):
    event_id: UUID
    event_type: str
    event_version: str = "1.0"
    timestamp: datetime
    source: str
    tenant_id: UUID
    correlation_id: UUID
    causation_id: Optional[UUID] = None  # ID of event that caused this

class ReservationCreatedData(BaseModel):
    reservation_id: UUID
    room_id: UUID
    guest_id: UUID
    check_in_date: str
    check_out_date: str
    status: str
    total_amount: float

class ReservationCreatedEvent(BaseModel):
    metadata: EventMetadata
    data: ReservationCreatedData

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "event_id": "123e4567-e89b-12d3-a456-426614174000",
                    "event_type": "pms.reservation.created",
                    "event_version": "1.0",
                    "timestamp": "2025-01-15T10:30:00Z",
                    "source": "pms-service",
                    "tenant_id": "tenant-uuid",
                    "correlation_id": "request-uuid"
                },
                "data": {
                    "reservation_id": "res-uuid",
                    "room_id": "room-uuid",
                    "guest_id": "guest-uuid",
                    "check_in_date": "2025-01-20",
                    "check_out_date": "2025-01-22",
                    "status": "confirmed",
                    "total_amount": 500000
                }
            }
        }
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A5.3](#step-a53-publisher)
- Ada ✗ → Perbaiki schema

---

### STEP A5.3: Publisher

📋 **Konteks:**
Implement event publisher.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V3.md - #18 Event/Message Schema](./DEVELOPMENT_STANDARDS_V3.md)

🔀 **Kondisi:**
- **Jika** membuat publisher → Lanjutkan checklist
- **Jika** hanya consumer → Skip ke [STEP A5.4](#step-a54-consumer)

☑️ **Checklist Publisher:** `[WAJIB untuk publisher]`

| # | Item |
|---|------|
| ☐ | Publisher class menggunakan dependency injection |
| ☐ | Event di-publish setelah transaction commit |
| ☐ | Include all required metadata |
| ☐ | Serialization ke JSON |
| ☐ | Error handling jika publish fails |

**Publisher Pattern:**

```python
# events/publishers/pms_publisher.py

from uuid import uuid4
from datetime import datetime, timezone
from app.core.messaging import MessageBroker
from app.core.context import get_correlation_id
from schemas.events.reservation_events import ReservationCreatedEvent

class PMSEventPublisher:
    def __init__(self, broker: MessageBroker, tenant_id: str, source: str = "pms-service"):
        self.broker = broker
        self.tenant_id = tenant_id
        self.source = source

    def publish_reservation_created(self, reservation) -> None:
        event = ReservationCreatedEvent(
            metadata={
                "event_id": uuid4(),
                "event_type": "pms.reservation.created",
                "event_version": "1.0",
                "timestamp": datetime.now(timezone.utc),
                "source": self.source,
                "tenant_id": self.tenant_id,
                "correlation_id": get_correlation_id()
            },
            data={
                "reservation_id": reservation.id,
                "room_id": reservation.room_id,
                "guest_id": reservation.guest_id,
                "check_in_date": str(reservation.check_in_date),
                "check_out_date": str(reservation.check_out_date),
                "status": reservation.status,
                "total_amount": float(reservation.total_amount)
            }
        )

        self.broker.publish(
            exchange="pms.events",
            routing_key="pms.reservation.created",
            message=event.model_dump_json()
        )
```

**Integration with Service:**

```python
# services/reservation_service.py

class ReservationService:
    def __init__(self, db, tenant_id, event_publisher: PMSEventPublisher):
        self.db = db
        self.tenant_id = tenant_id
        self.event_publisher = event_publisher

    def create(self, data: ReservationCreate) -> Reservation:
        with self.db.begin():
            reservation = self._create_reservation(data)

        # Publish AFTER transaction commits
        self.event_publisher.publish_reservation_created(reservation)

        return reservation
```

➡️ **Selanjutnya:**
- Publisher done → Lanjut ke [STEP A5.4](#step-a54-consumer)
- Skip consumer → Lanjut ke [STEP A5.5](#step-a55-error-handling)

---

### STEP A5.4: Consumer

📋 **Konteks:**
Implement event consumer.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V3.md - #18 Event/Message Schema](./DEVELOPMENT_STANDARDS_V3.md)

🔀 **Kondisi:**
- **Jika** membuat consumer → Lanjutkan checklist
- **Jika** hanya publisher → Skip ke [STEP A5.5](#step-a55-error-handling)

☑️ **Checklist Consumer:** `[WAJIB untuk consumer]`

| # | Item |
|---|------|
| ☐ | Consumer idempotent (handle duplicate events) |
| ☐ | Event deserialization dengan schema validation |
| ☐ | Error handling untuk malformed events |
| ☐ | Dead letter queue untuk failed processing |
| ☐ | Manual acknowledgment setelah processing selesai |
| ☐ | Logging event received dan processed |

**Consumer Pattern:**

```python
# events/consumers/accounting_consumer.py

from app.core.messaging import MessageConsumer
from schemas.events.reservation_events import ReservationCreatedEvent
from services.folio_service import FolioService
import structlog

logger = structlog.get_logger(__name__)

class AccountingEventConsumer(MessageConsumer):
    def __init__(self, db_session_factory, folio_service_factory):
        self.db_session_factory = db_session_factory
        self.folio_service_factory = folio_service_factory

    def handle_reservation_created(self, body: bytes) -> None:
        """Create folio when reservation is created."""
        try:
            event = ReservationCreatedEvent.model_validate_json(body)

            logger.info(
                "Processing reservation.created event",
                event_id=str(event.metadata.event_id),
                reservation_id=str(event.data.reservation_id)
            )

            # Check idempotency
            if self._already_processed(event.metadata.event_id):
                logger.info("Event already processed, skipping")
                return

            # Process event
            with self.db_session_factory() as db:
                folio_service = self.folio_service_factory(
                    db,
                    event.metadata.tenant_id
                )
                folio_service.create_for_reservation(
                    event.data.reservation_id
                )

            # Mark as processed
            self._mark_processed(event.metadata.event_id)

            logger.info("Event processed successfully")

        except ValidationError as e:
            logger.error("Invalid event schema", error=str(e))
            # Send to dead letter queue
            self._send_to_dlq(body, str(e))
        except Exception as e:
            logger.error("Event processing failed", error=str(e))
            raise  # Will trigger retry/DLQ
```

➡️ **Selanjutnya:**
- Consumer done → Lanjut ke [STEP A5.5](#step-a55-error-handling)

---

### STEP A5.5: Error Handling

📋 **Konteks:**
Handle errors dalam event publishing dan consuming.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #7 Error Handling](./DEVELOPMENT_STANDARDS.md)
- [DEVELOPMENT_STANDARDS_V10.md - #37 Circuit Breaker](./DEVELOPMENT_STANDARDS_V10.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Publisher: Retry on transient failures |
| ☐ | Publisher: Log and alert on persistent failures |
| ☐ | Consumer: Dead letter queue configured |
| ☐ | Consumer: Max retry count configured |
| ☐ | Consumer: Alert on DLQ messages |
| ☐ | Circuit breaker untuk external dependencies |

**Error Handling Patterns:**

```python
# Publisher with retry
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientPublisher:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10)
    )
    def publish(self, event):
        try:
            self.broker.publish(event)
        except ConnectionError:
            logger.error("Failed to publish event, retrying...")
            raise

# Consumer with DLQ
class DLQConsumer:
    def process(self, message):
        try:
            self._handle(message)
            message.ack()
        except RetryableError:
            if message.retry_count < self.max_retries:
                message.nack(requeue=True)
            else:
                self._send_to_dlq(message)
                message.ack()
        except NonRetryableError:
            self._send_to_dlq(message)
            message.ack()
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A5.6](#step-a56-testing)
- Ada ✗ → Perbaiki error handling

---

### STEP A5.6: Testing

📋 **Konteks:**
Test events dengan unit dan integration tests.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Unit test schema validation |
| ☐ | Unit test publisher logic |
| ☐ | Unit test consumer logic |
| ☐ | Integration test publish → consume |
| ☐ | Test idempotency |
| ☐ | Test error scenarios |

**Test Pattern:**

```python
class TestReservationCreatedEvent:
    def test_event_schema_valid(self):
        event = ReservationCreatedEvent(
            metadata={...},
            data={...}
        )
        assert event.metadata.event_type == "pms.reservation.created"

    def test_publisher_sends_event(self):
        mock_broker = MagicMock()
        publisher = PMSEventPublisher(mock_broker, "tenant-id")

        publisher.publish_reservation_created(reservation)

        mock_broker.publish.assert_called_once()

    def test_consumer_creates_folio(self):
        consumer = AccountingEventConsumer(...)
        event_json = create_test_event_json()

        consumer.handle_reservation_created(event_json)

        assert Folio.query.filter_by(
            reservation_id=event_data['reservation_id']
        ).first() is not None
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A5.7](#step-a57-documentation)
- Ada ✗ → Tulis tests

---

### STEP A5.7: Documentation

📋 **Konteks:**
Document event di module documentation.

📖 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Event schema documented |
| ☐ | Publisher documented di FEATURES.md |
| ☐ | Consumer documented di FEATURES.md |
| ☐ | Event flow diagram di WORKFLOWS.md |
| ☐ | CHANGELOG.md diupdate |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW A5 SELESAI**
- Ada ✗ → Update dokumentasi

---

### STEP A5.8: Final Checklist

```
FINAL CHECKLIST - CREATE EVENT/MESSAGE
═══════════════════════════════════════════

Design
☐ Event name follows convention
☐ Event type determined
☐ Exchange/routing configured

Schema
☐ All required metadata fields
☐ Versioned schema
☐ Example payload documented

Publisher (if applicable)
☐ Publishes after transaction commit
☐ Includes all metadata
☐ Retry on transient failures

Consumer (if applicable)
☐ Idempotent processing
☐ Schema validation
☐ Dead letter queue
☐ Proper acknowledgment

Error Handling
☐ Retry strategy configured
☐ DLQ for failed messages
☐ Alerting on failures

Quality
☐ Unit tests written
☐ Integration tests written
☐ Documentation updated
☐ CHANGELOG updated
```

---

## Flow A6: Create Integration

> Integrasi dengan external API (payment gateway, channel manager, etc)

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ API documentation dari external service tersedia
☐ API credentials tersedia (sandbox/test)
☐ Network access ke external service
```

---

### STEP A6.1: Integration Design

📋 **Konteks:**
Design integration - tentukan scope dan interaction patterns.

📖 **Acuan:**
- [INTEGRATION_SPECS.md](./INTEGRATION_SPECS.md)
- [DEVELOPMENT_STANDARDS_V10.md - #37 Circuit Breaker](./DEVELOPMENT_STANDARDS_V10.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Integration scope jelas (what data, which operations) |
| ☐ | Sync vs Async determined |
| ☐ | Rate limits dari external service diketahui |
| ☐ | Error responses dari external service dipahami |
| ☐ | Retry strategy sesuai dengan external service guidelines |

**Integration Types:**

| Type | Use Case | Example |
|------|----------|---------|
| Request-Response (Sync) | Real-time operations | Payment authorization |
| Webhook (Async inbound) | External → Our system | Payment notification |
| Batch (Async outbound) | Our system → External | Rate sync to OTAs |
| Polling | Check status | Order status check |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A6.2](#step-a62-client-implementation)
- Ada ✗ → Perbaiki design

---

### STEP A6.2: Client Implementation

📋 **Konteks:**
Implement HTTP client untuk external API.

📖 **Acuan:**
- [SHARED_CODE_STANDARDS.md](./SHARED_CODE_STANDARDS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Client class terpisah (tidak inline di service) |
| ☐ | Base URL configurable (different for prod/sandbox) |
| ☐ | Timeout configured |
| ☐ | Retry with exponential backoff |
| ☐ | Request/response logging |
| ☐ | Credentials tidak hardcoded |

**Client Template:**

```python
# integrations/payment/xendit_client.py

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class XenditClient:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or settings.XENDIT_API_KEY
        self.base_url = base_url or settings.XENDIT_BASE_URL
        self.timeout = httpx.Timeout(30.0)

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Basic {self._encode_api_key()}",
            "Content-Type": "application/json"
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def create_invoice(self, data: dict) -> dict:
        """Create invoice in Xendit."""
        logger.info("Creating Xendit invoice", external_id=data.get('external_id'))

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v2/invoices",
                headers=self._get_headers(),
                json=data
            )

            logger.info(
                "Xendit response",
                status_code=response.status_code,
                external_id=data.get('external_id')
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                raise XenditValidationError(response.json())
            elif response.status_code == 401:
                raise XenditAuthError("Invalid API key")
            elif response.status_code >= 500:
                raise XenditServerError("Xendit server error")
            else:
                raise XenditError(f"Unexpected status: {response.status_code}")
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A6.3](#step-a63-circuit-breaker)
- Ada ✗ → Perbaiki client

---

### STEP A6.3: Circuit Breaker

📋 **Konteks:**
Implement circuit breaker untuk handle external service failures.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V10.md - #37 Circuit Breaker](./DEVELOPMENT_STANDARDS_V10.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Circuit breaker pattern implemented |
| ☐ | Failure threshold configured |
| ☐ | Recovery timeout configured |
| ☐ | Half-open state untuk gradual recovery |
| ☐ | Fallback behavior defined |
| ☐ | Circuit state logged |

**Circuit Breaker Pattern:**

```python
from circuitbreaker import circuit
from app.core.exceptions import ServiceUnavailableError

class XenditClient:
    @circuit(
        failure_threshold=5,
        recovery_timeout=30,
        expected_exception=XenditServerError
    )
    async def create_invoice(self, data: dict) -> dict:
        try:
            return await self._call_xendit(data)
        except CircuitBreakerError:
            logger.error("Circuit breaker open for Xendit")
            raise ServiceUnavailableError(
                "Payment service temporarily unavailable"
            )
```

**Circuit States:**

| State | Description | Action |
|-------|-------------|--------|
| Closed | Normal operation | Requests pass through |
| Open | Failures exceeded threshold | Requests fail fast |
| Half-Open | Testing recovery | Limited requests allowed |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A6.4](#step-a64-secrets-management)
- Ada ✗ → Implement circuit breaker

---

### STEP A6.4: Secrets Management

📋 **Konteks:**
Handle API credentials securely.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V11.md - #41 Secrets Management](./DEVELOPMENT_STANDARDS_V11.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Credentials stored in secrets manager (not env vars for prod) |
| ☐ | Different credentials for sandbox vs production |
| ☐ | Credentials per tenant (jika multi-tenant credentials) |
| ☐ | Credentials tidak di-log |
| ☐ | Credentials rotation plan documented |

**Secrets Pattern:**

```python
# config/secrets.py

from app.core.secrets_manager import SecretsManager

class IntegrationSecrets:
    def __init__(self, secrets_manager: SecretsManager, tenant_id: str):
        self.secrets_manager = secrets_manager
        self.tenant_id = tenant_id

    def get_xendit_api_key(self) -> str:
        return self.secrets_manager.get_secret(
            f"integrations/{self.tenant_id}/xendit/api_key"
        )

    def get_channel_manager_credentials(self) -> dict:
        return self.secrets_manager.get_secret(
            f"integrations/{self.tenant_id}/channel_manager/credentials"
        )
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A6.5](#step-a65-webhook-handling)
- Ada ✗ → Setup secrets management

---

### STEP A6.5: Webhook Handling

📋 **Konteks:**
Handle webhooks dari external services (jika ada).

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V8.md - #32 Webhook System](./DEVELOPMENT_STANDARDS_V8.md)

🔀 **Kondisi:**
- **Jika** integration menerima webhooks → Lanjutkan checklist
- **Jika** tidak ada webhooks → Skip ke [STEP A6.6](#step-a66-error-handling)

☑️ **Checklist:** `[JIKA ADA webhooks]`

| # | Item |
|---|------|
| ☐ | Webhook endpoint exposed |
| ☐ | Signature verification implemented |
| ☐ | Idempotent processing (handle duplicate webhooks) |
| ☐ | Async processing (respond 200 immediately) |
| ☐ | Webhook events logged |
| ☐ | Failed webhooks can be replayed |

**Webhook Handler Pattern:**

```python
# api/webhooks/xendit.py

from fastapi import APIRouter, Request, HTTPException
from app.core.webhook import verify_signature
from app.tasks.payment_tasks import process_xendit_webhook

router = APIRouter()

@router.post("/webhooks/xendit")
async def handle_xendit_webhook(request: Request):
    """Handle Xendit payment notifications."""
    body = await request.body()
    signature = request.headers.get("X-Callback-Token")

    # Verify signature
    if not verify_xendit_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse and validate
    payload = json.loads(body)
    event_id = payload.get("id")

    # Log webhook received
    logger.info("Xendit webhook received", event_id=event_id)

    # Process async (don't block response)
    process_xendit_webhook.delay(payload)

    # Respond immediately
    return {"status": "received"}
```

➡️ **Selanjutnya:**
- Webhooks handled → Lanjut ke [STEP A6.6](#step-a66-error-handling)
- No webhooks → Lanjut ke [STEP A6.6](#step-a66-error-handling)

---

### STEP A6.6: Error Handling

📋 **Konteks:**
Handle errors dari external service dengan proper user feedback.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #7 Error Handling](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Map external errors ke internal error codes |
| ☐ | User-friendly error messages (tidak expose technical details) |
| ☐ | Different handling untuk client vs server errors |
| ☐ | Alert untuk persistent external service failures |
| ☐ | Logging semua external interactions |

**Error Mapping:**

```python
# integrations/payment/errors.py

class PaymentIntegrationError(Exception):
    """Base exception for payment integration."""
    pass

class PaymentValidationError(PaymentIntegrationError):
    """Invalid payment data."""
    pass

class PaymentDeclinedError(PaymentIntegrationError):
    """Payment was declined."""
    pass

class PaymentServiceError(PaymentIntegrationError):
    """Payment service unavailable."""
    pass

def map_xendit_error(error: XenditError) -> PaymentIntegrationError:
    """Map Xendit errors to our domain errors."""
    error_mapping = {
        "INVALID_AMOUNT": PaymentValidationError("Invalid payment amount"),
        "CARD_DECLINED": PaymentDeclinedError("Card was declined"),
        "INSUFFICIENT_BALANCE": PaymentDeclinedError("Insufficient balance"),
    }

    return error_mapping.get(
        error.code,
        PaymentServiceError("Payment processing failed")
    )
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A6.7](#step-a67-testing)
- Ada ✗ → Perbaiki error handling

---

### STEP A6.7: Testing

📋 **Konteks:**
Test integration dengan mock external service.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Unit tests dengan mocked external calls |
| ☐ | Integration tests dengan sandbox API |
| ☐ | Test success scenarios |
| ☐ | Test error scenarios (400, 500, timeout) |
| ☐ | Test circuit breaker behavior |
| ☐ | Test webhook signature verification |

**Test Pattern:**

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestXenditClient:
    @pytest.mark.asyncio
    async def test_create_invoice_success(self):
        client = XenditClient(api_key="test_key")

        with patch.object(client, '_call_api', new_callable=AsyncMock) as mock:
            mock.return_value = {"id": "inv_123", "status": "PENDING"}

            result = await client.create_invoice({"amount": 100000})

            assert result["id"] == "inv_123"

    @pytest.mark.asyncio
    async def test_handles_server_error_with_retry(self):
        client = XenditClient()

        with patch.object(client, '_call_api', new_callable=AsyncMock) as mock:
            mock.side_effect = [
                XenditServerError(),
                XenditServerError(),
                {"id": "inv_123"}  # Success on 3rd try
            ]

            result = await client.create_invoice({"amount": 100000})

            assert result["id"] == "inv_123"
            assert mock.call_count == 3
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP A6.8](#step-a68-documentation)
- Ada ✗ → Tulis tests

---

### STEP A6.8: Documentation

📋 **Konteks:**
Document integration di module documentation.

📖 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)
- [INTEGRATION_SPECS.md](./INTEGRATION_SPECS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Integration overview documented |
| ☐ | Configuration requirements documented |
| ☐ | API endpoints used documented |
| ☐ | Error codes documented |
| ☐ | Webhook handling documented |
| ☐ | Troubleshooting guide |
| ☐ | CHANGELOG.md diupdate |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW A6 SELESAI**
- Ada ✗ → Update dokumentasi

---

### STEP A6.9: Final Checklist

```
FINAL CHECKLIST - CREATE INTEGRATION
═══════════════════════════════════════════

Design
☐ Integration scope defined
☐ Sync/async determined
☐ Rate limits known
☐ Error responses understood

Client
☐ Separate client class
☐ Configurable base URL
☐ Timeout configured
☐ Retry with backoff
☐ Request/response logging

Resilience
☐ Circuit breaker implemented
☐ Failure threshold set
☐ Recovery timeout set
☐ Fallback behavior defined

Security
☐ Credentials in secrets manager
☐ Environment-specific credentials
☐ Credentials not logged
☐ Webhook signature verification

Error Handling
☐ External errors mapped
☐ User-friendly messages
☐ Proper logging
☐ Alerting for failures

Quality
☐ Unit tests (mocked)
☐ Integration tests (sandbox)
☐ Error scenarios tested
☐ Documentation updated
☐ CHANGELOG updated
```

---

---

## Flow B1: Create UI Component

> Membuat reusable React component

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Component belum ada (cek existing components)
☐ Design/mockup tersedia atau requirement jelas
☐ Component benar-benar perlu reusable
```

---

### STEP B1.1: Component Design

📋 **Konteks:**
Design component - tentukan props, variants, dan states.

📖 **Acuan:**
- [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md)
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)
- [DEVELOPMENT_STANDARDS_V2.md - #11 Frontend Patterns](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist Design:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Component purpose jelas (single responsibility) |
| ☐ | Props minimal dan well-defined |
| ☐ | Variants ditentukan (jika ada) |
| ☐ | States ditentukan (default, hover, active, disabled, loading, error) |
| ☐ | Responsive behavior ditentukan |

**Component Design Template:**

```typescript
// Component: Button
// Purpose: Clickable action trigger
// Variants: primary, secondary, ghost, danger, success, warning
// Sizes: sm, md, lg
// States: default, hover, active, disabled, loading
// Props:
//   - variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'warning'
//   - size: 'sm' | 'md' | 'lg'
//   - disabled: boolean
//   - loading: boolean
//   - leftIcon: ReactNode
//   - rightIcon: ReactNode
//   - fullWidth: boolean
//   - onClick: () => void
//   - children: ReactNode
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B1.2](#step-b12-naming--file-structure)
- Ada ✗ → Perbaiki design

---

### STEP B1.2: Naming & File Structure

📋 **Konteks:**
Tentukan nama component dan lokasi file.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #1 Naming Conventions](./DEVELOPMENT_STANDARDS.md)
- [DEVELOPMENT_STANDARDS_V2.md - #10 Code Structure](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist Naming:** `[WAJIB]`

| # | Item | Contoh Benar | Contoh Salah |
|---|------|--------------|--------------|
| ☐ | Component name PascalCase | `RoomCard` | `roomCard`, `room-card` |
| ☐ | File name matches component | `RoomCard.tsx` | `roomCard.tsx` |
| ☐ | Props interface name | `RoomCardProps` | `Props`, `IRoomCard` |
| ☐ | Test file name | `RoomCard.test.tsx` | `roomcard.test.tsx` |

**File Structure:**

```
src/
├── components/
│   ├── common/              # Shared components
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   ├── Button.stories.tsx
│   │   │   └── index.ts
│   │   └── ...
│   └── {module}/            # Module-specific components
│       ├── RoomCard/
│       │   ├── RoomCard.tsx
│       │   ├── RoomCard.test.tsx
│       │   └── index.ts
│       └── ...
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B1.3](#step-b13-typescript-types)
- Ada ✗ → Perbaiki naming

---

### STEP B1.3: TypeScript Types

📋 **Konteks:**
Definisikan types untuk props dan internal state.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #11 Frontend Patterns](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Props interface exported |
| ☐ | All props typed (no `any`) |
| ☐ | Optional props marked dengan `?` |
| ☐ | Event handlers typed properly |
| ☐ | Union types untuk variants |
| ☐ | Generic types jika component flexible |

**Props Template:**

```typescript
import { ReactNode, ButtonHTMLAttributes } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button visual variant */
  variant?: ButtonVariant;
  /** Button size */
  size?: ButtonSize;
  /** Show loading spinner */
  loading?: boolean;
  /** Icon on the left */
  leftIcon?: ReactNode;
  /** Icon on the right */
  rightIcon?: ReactNode;
  /** Full width button */
  fullWidth?: boolean;
  /** Button content */
  children: ReactNode;
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B1.4](#step-b14-styling)
- Ada ✗ → Perbaiki types

---

### STEP B1.4: Styling

📋 **Konteks:**
Implement styling sesuai design system.

📖 **Acuan:**
- [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md)
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Gunakan design tokens (colors, spacing, typography) |
| ☐ | Gunakan CSS-in-JS atau Tailwind (sesuai project) |
| ☐ | Responsive styles |
| ☐ | State styles (hover, active, focus, disabled) |
| ☐ | Dark mode support (jika applicable) |
| ☐ | Tidak hardcode values |

**Styling Pattern (Tailwind):**

```typescript
const buttonVariants = {
  primary: 'bg-primary-600 hover:bg-primary-700 text-white',
  secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-900',
  ghost: 'bg-transparent hover:bg-gray-100 text-gray-700',
  danger: 'bg-danger-600 hover:bg-danger-700 text-white',
};

const buttonSizes = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-base',
  lg: 'h-12 px-6 text-lg',
};

const Button = ({ variant = 'primary', size = 'md', ...props }) => (
  <button
    className={cn(
      'inline-flex items-center justify-center rounded-md font-medium',
      'transition-colors duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      buttonVariants[variant],
      buttonSizes[size]
    )}
    {...props}
  />
);
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B1.5](#step-b15-accessibility)
- Ada ✗ → Perbaiki styling

---

### STEP B1.5: Accessibility

📋 **Konteks:**
Pastikan component accessible.

📖 **Acuan:**
- [UI_DESIGN_SYSTEM.md - Accessibility](./UI_DESIGN_SYSTEM.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Keyboard navigable (tab, enter, space, escape) |
| ☐ | Proper ARIA attributes |
| ☐ | Focus visible styles |
| ☐ | Screen reader friendly |
| ☐ | Color contrast meets WCAG AA |
| ☐ | Touch target min 44x44px |

**Accessibility Pattern:**

```typescript
const Button = ({ loading, disabled, children, ...props }) => (
  <button
    disabled={disabled || loading}
    aria-disabled={disabled || loading}
    aria-busy={loading}
    {...props}
  >
    {loading && <Spinner aria-hidden="true" />}
    <span className={loading ? 'opacity-0' : ''}>{children}</span>
    {loading && <span className="sr-only">Loading...</span>}
  </button>
);

// Dialog component
const Dialog = ({ open, onClose, title, children }) => (
  <div
    role="dialog"
    aria-modal="true"
    aria-labelledby="dialog-title"
    tabIndex={-1}
    onKeyDown={(e) => e.key === 'Escape' && onClose()}
  >
    <h2 id="dialog-title">{title}</h2>
    {children}
  </div>
);
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B1.6](#step-b16-implementation)
- Ada ✗ → Perbaiki accessibility

---

### STEP B1.6: Implementation

📋 **Konteks:**
Implement component dengan best practices.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #11 Frontend Patterns](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Functional component with hooks |
| ☐ | Destructure props dengan defaults |
| ☐ | Memoize jika expensive render |
| ☐ | forwardRef jika perlu DOM access |
| ☐ | Clean event handlers |
| ☐ | Proper cleanup (useEffect) |

**Implementation Pattern:**

```typescript
import { forwardRef, memo } from 'react';
import { cn } from '@/lib/utils';
import type { ButtonProps } from './Button.types';

export const Button = memo(forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && 'w-full',
          className
        )}
        {...props}
      >
        {loading && <Spinner size={size} />}
        {!loading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        <span className={loading ? 'opacity-0' : ''}>{children}</span>
        {!loading && rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    );
  }
));

Button.displayName = 'Button';
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B1.7](#step-b17-testing)
- Ada ✗ → Perbaiki implementation

---

### STEP B1.7: Testing

📋 **Konteks:**
Test component dengan unit tests.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test renders correctly |
| ☐ | Test all variants |
| ☐ | Test all states |
| ☐ | Test interactions (click, hover) |
| ☐ | Test accessibility |
| ☐ | Test edge cases |

**Test Pattern:**

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button loading>Submit</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
  });

  it('disables when disabled prop is true', () => {
    render(<Button disabled>Submit</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('applies variant styles correctly', () => {
    const { rerender } = render(<Button variant="primary">Test</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary-600');

    rerender(<Button variant="danger">Test</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-danger-600');
  });
});
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B1.8](#step-b18-storybook)
- Ada ✗ → Tulis tests

---

### STEP B1.8: Storybook

📋 **Konteks:**
Create Storybook stories untuk documentation dan visual testing.

📖 **Acuan:**
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[OPSIONAL - jika pakai Storybook]`

| # | Item |
|---|------|
| ☐ | Default story |
| ☐ | Story untuk setiap variant |
| ☐ | Story untuk setiap size |
| ☐ | Story untuk states (loading, disabled) |
| ☐ | Interactive controls |
| ☐ | Documentation |

**Storybook Pattern:**

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'ghost', 'danger'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Button',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Button',
  },
};

export const Loading: Story = {
  args: {
    loading: true,
    children: 'Loading...',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex gap-4">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="danger">Danger</Button>
    </div>
  ),
};
```

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW B1 SELESAI**
- Ada ✗ → Update storybook

---

### STEP B1.9: Final Checklist

```
FINAL CHECKLIST - CREATE UI COMPONENT
═══════════════════════════════════════════

Design
☐ Component purpose clear
☐ Props minimal and typed
☐ Variants defined
☐ States defined

Structure
☐ Proper naming (PascalCase)
☐ Correct file location
☐ Index export

Implementation
☐ TypeScript types complete
☐ Design system tokens used
☐ Accessible (keyboard, ARIA)
☐ Responsive
☐ State styles complete

Quality
☐ Unit tests written
☐ All variants tested
☐ All states tested
☐ Storybook stories (if applicable)
```

---

## Flow B2: Create Page/View

> Membuat halaman baru (route)

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Route path sudah ditentukan
☐ API endpoints sudah ada (jika perlu data)
☐ Permissions sudah didefinisikan
```

---

### STEP B2.1: Page Design

📋 **Konteks:**
Design page layout dan content structure.

📖 **Acuan:**
- [UIUX_WIREFRAMES_FLOWS.md](./UIUX_WIREFRAMES_FLOWS.md)
- [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Page purpose jelas |
| ☐ | Layout structure (header, content, sidebar?) |
| ☐ | Content sections identified |
| ☐ | Data requirements identified |
| ☐ | User actions identified |
| ☐ | Empty/loading/error states |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B2.2](#step-b22-routing)
- Ada ✗ → Perbaiki design

---

### STEP B2.2: Routing

📋 **Konteks:**
Setup route untuk page.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #11 Frontend Patterns](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item | Contoh Benar | Contoh Salah |
|---|------|--------------|--------------|
| ☐ | Route path kebab-case | `/room-types` | `/roomTypes` |
| ☐ | Dynamic segments dengan `:param` | `/rooms/:id` | `/rooms/[id]` |
| ☐ | Nested routes jika perlu | `/settings/profile` | - |
| ☐ | Route guard untuk protected pages | - | - |

**Route Structure:**

```typescript
// routes/index.tsx
const routes = [
  {
    path: '/pms',
    element: <PMSLayout />,
    children: [
      { path: 'rooms', element: <RoomsPage /> },
      { path: 'rooms/:id', element: <RoomDetailPage /> },
      { path: 'reservations', element: <ReservationsPage /> },
      { path: 'reservations/:id', element: <ReservationDetailPage /> },
    ],
  },
];

// With route guard
{
  path: '/settings',
  element: <RequireAuth permission="settings.view"><SettingsPage /></RequireAuth>,
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B2.3](#step-b23-data-fetching)
- Ada ✗ → Perbaiki routing

---

### STEP B2.3: Data Fetching

📋 **Konteks:**
Setup data fetching dengan React Query atau state management.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #11 Frontend Patterns](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Gunakan React Query untuk server state |
| ☐ | Query keys consistent dan typed |
| ☐ | Loading states handled |
| ☐ | Error states handled |
| ☐ | Caching configured |
| ☐ | Refetch strategy defined |

**Data Fetching Pattern:**

```typescript
// hooks/useRooms.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { roomApi } from '@/api/room';

export const roomKeys = {
  all: ['rooms'] as const,
  lists: () => [...roomKeys.all, 'list'] as const,
  list: (filters: RoomFilters) => [...roomKeys.lists(), filters] as const,
  details: () => [...roomKeys.all, 'detail'] as const,
  detail: (id: string) => [...roomKeys.details(), id] as const,
};

export function useRooms(filters: RoomFilters) {
  return useQuery({
    queryKey: roomKeys.list(filters),
    queryFn: () => roomApi.getAll(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useRoom(id: string) {
  return useQuery({
    queryKey: roomKeys.detail(id),
    queryFn: () => roomApi.getById(id),
    enabled: !!id,
  });
}

// Usage in page
function RoomsPage() {
  const [filters, setFilters] = useState<RoomFilters>({});
  const { data, isLoading, error } = useRooms(filters);

  if (isLoading) return <PageSkeleton />;
  if (error) return <ErrorState error={error} />;
  if (!data?.length) return <EmptyState />;

  return <RoomList rooms={data} />;
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B2.4](#step-b24-layout--structure)
- Ada ✗ → Perbaiki data fetching

---

### STEP B2.4: Layout & Structure

📋 **Konteks:**
Implement page layout dan component structure.

📖 **Acuan:**
- [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md)
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Page title dan breadcrumb |
| ☐ | Content layout (grid/flex) |
| ☐ | Responsive layout |
| ☐ | Loading skeleton |
| ☐ | Error boundary |
| ☐ | Empty state |

**Page Structure Pattern:**

```typescript
function RoomsPage() {
  const { data, isLoading, error } = useRooms();

  return (
    <PageContainer>
      {/* Header */}
      <PageHeader
        title="Rooms"
        breadcrumbs={[
          { label: 'PMS', href: '/pms' },
          { label: 'Rooms' },
        ]}
        actions={
          <Button onClick={() => navigate('/pms/rooms/new')}>
            Add Room
          </Button>
        }
      />

      {/* Filters */}
      <Card className="mb-6">
        <RoomFilters onFilter={setFilters} />
      </Card>

      {/* Content */}
      {isLoading ? (
        <RoomListSkeleton />
      ) : error ? (
        <ErrorState
          title="Failed to load rooms"
          message={error.message}
          onRetry={refetch}
        />
      ) : !data?.length ? (
        <EmptyState
          icon={<RoomIcon />}
          title="No rooms found"
          description="Get started by adding your first room"
          action={
            <Button onClick={() => navigate('/pms/rooms/new')}>
              Add Room
            </Button>
          }
        />
      ) : (
        <RoomList rooms={data} />
      )}
    </PageContainer>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B2.5](#step-b25-state-management)
- Ada ✗ → Perbaiki layout

---

### STEP B2.5: State Management

📋 **Konteks:**
Handle local state dan UI state.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #11 Frontend Patterns](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Local state dengan useState |
| ☐ | URL state untuk filters/pagination |
| ☐ | Global state hanya jika perlu sharing |
| ☐ | Form state dengan react-hook-form |
| ☐ | State tidak duplicated |

**State Pattern:**

```typescript
function RoomsPage() {
  // URL state for filters
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(() => ({
    status: searchParams.get('status') || undefined,
    floor: searchParams.get('floor') || undefined,
    page: parseInt(searchParams.get('page') || '1'),
  }), [searchParams]);

  // Local UI state
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  // Update filters
  const handleFilterChange = (newFilters: RoomFilters) => {
    setSearchParams(new URLSearchParams(newFilters));
  };

  // Server state
  const { data, isLoading } = useRooms(filters);

  // ...
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B2.6](#step-b26-navigation--actions)
- Ada ✗ → Perbaiki state management

---

### STEP B2.6: Navigation & Actions

📋 **Konteks:**
Handle user navigation dan actions.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #11 Frontend Patterns](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Navigation dengan useNavigate |
| ☐ | Confirmation dialogs untuk destructive actions |
| ☐ | Success/error feedback (toast) |
| ☐ | Loading states untuk actions |
| ☐ | Optimistic updates jika applicable |

**Actions Pattern:**

```typescript
function RoomsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const deleteMutation = useMutation({
    mutationFn: roomApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roomKeys.lists() });
      toast({ title: 'Room deleted successfully' });
      setIsDeleteModalOpen(false);
    },
    onError: (error) => {
      toast({ title: 'Failed to delete room', variant: 'error' });
    },
  });

  const handleDelete = (room: Room) => {
    setSelectedRoom(room);
    setIsDeleteModalOpen(true);
  };

  const confirmDelete = () => {
    if (selectedRoom) {
      deleteMutation.mutate(selectedRoom.id);
    }
  };

  return (
    <>
      {/* Page content */}
      <RoomList
        rooms={data}
        onEdit={(room) => navigate(`/pms/rooms/${room.id}/edit`)}
        onDelete={handleDelete}
      />

      {/* Delete confirmation */}
      <ConfirmDialog
        open={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        loading={deleteMutation.isPending}
        title="Delete Room"
        message={`Are you sure you want to delete ${selectedRoom?.room_number}?`}
        confirmLabel="Delete"
        variant="danger"
      />
    </>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B2.7](#step-b27-permissions)
- Ada ✗ → Perbaiki navigation/actions

---

### STEP B2.7: Permissions

📋 **Konteks:**
Handle permission checks untuk page access dan actions.

📖 **Acuan:**
- [SECURITY_AUTH_REQUIREMENTS.md](./SECURITY_AUTH_REQUIREMENTS.md)
- [DEVELOPMENT_STANDARDS.md - #3 RBAC/Permission](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Route protected dengan permission |
| ☐ | Actions hidden/disabled based on permission |
| ☐ | Permission checks consistent dengan backend |
| ☐ | Graceful handling untuk unauthorized |

**Permission Pattern:**

```typescript
// Route protection
<Route
  path="/pms/rooms"
  element={
    <RequirePermission permission="pms.rooms.view">
      <RoomsPage />
    </RequirePermission>
  }
/>

// Component-level permission
function RoomsPage() {
  const { can } = usePermissions();

  return (
    <PageContainer>
      <PageHeader
        actions={
          can('pms.rooms.create') && (
            <Button onClick={() => navigate('/pms/rooms/new')}>
              Add Room
            </Button>
          )
        }
      />

      <RoomList
        rooms={data}
        onEdit={can('pms.rooms.update') ? handleEdit : undefined}
        onDelete={can('pms.rooms.delete') ? handleDelete : undefined}
      />
    </PageContainer>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B2.8](#step-b28-testing)
- Ada ✗ → Perbaiki permissions

---

### STEP B2.8: Testing

📋 **Konteks:**
Test page dengan integration tests.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test renders correctly |
| ☐ | Test loading state |
| ☐ | Test error state |
| ☐ | Test empty state |
| ☐ | Test user interactions |
| ☐ | Test navigation |

**Test Pattern:**

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { RoomsPage } from './RoomsPage';

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <RoomsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('RoomsPage', () => {
  it('shows loading state initially', () => {
    renderPage();
    expect(screen.getByTestId('room-list-skeleton')).toBeInTheDocument();
  });

  it('shows rooms when data loads', async () => {
    server.use(
      rest.get('/api/v1/pms/rooms', (req, res, ctx) => {
        return res(ctx.json({ data: [mockRoom] }));
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(mockRoom.room_number)).toBeInTheDocument();
    });
  });

  it('shows error state on failure', async () => {
    server.use(
      rest.get('/api/v1/pms/rooms', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });
});
```

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW B2 SELESAI**
- Ada ✗ → Tulis tests

---

### STEP B2.9: Final Checklist

```
FINAL CHECKLIST - CREATE PAGE/VIEW
═══════════════════════════════════════════

Design
☐ Page purpose clear
☐ Layout structured
☐ States defined (loading, error, empty)

Routing
☐ Route path correct
☐ Route protection in place

Data
☐ React Query hooks created
☐ Query keys consistent
☐ Error handling

Implementation
☐ Layout components used
☐ Loading skeleton
☐ Error boundary
☐ Empty state
☐ Responsive

State & Actions
☐ State properly managed
☐ Actions with feedback
☐ Confirmation for destructive

Security
☐ Route protected
☐ Actions permission-based

Quality
☐ Tests written
☐ All states tested
```

---

## Flow B3: Create Form

> Membuat form dengan validasi

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Form fields sudah ditentukan
☐ Validation rules sudah ditentukan
☐ API endpoint untuk submit sudah ada
```

---

### STEP B3.1: Form Design

📋 **Konteks:**
Design form fields dan validation rules.

📖 **Acuan:**
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)
- [DEVELOPMENT_STANDARDS_V2.md - #8 Validation](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | All fields identified |
| ☐ | Required vs optional fields |
| ☐ | Field types (text, select, date, etc) |
| ☐ | Validation rules per field |
| ☐ | Default values |
| ☐ | Field dependencies (show/hide) |

**Form Design Template:**

```
Form: Create Room
├── room_number* (text, required, unique)
├── room_type_id* (select, required)
├── floor (number, optional)
├── description (textarea, optional, max 500)
├── amenities (multi-select, optional)
├── is_active (toggle, default: true)
└── Submit / Cancel buttons
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B3.2](#step-b32-schema-validation)
- Ada ✗ → Perbaiki design

---

### STEP B3.2: Schema Validation

📋 **Konteks:**
Define validation schema dengan Zod.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #8 Validation](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Zod schema untuk semua fields |
| ☐ | Custom error messages |
| ☐ | Schema matches backend validation |
| ☐ | Type inference dari schema |

**Validation Schema Pattern:**

```typescript
import { z } from 'zod';

export const roomFormSchema = z.object({
  room_number: z
    .string()
    .min(1, 'Room number is required')
    .max(20, 'Room number must be 20 characters or less'),
  room_type_id: z
    .string()
    .uuid('Invalid room type'),
  floor: z
    .number()
    .int()
    .min(1, 'Floor must be at least 1')
    .max(100, 'Floor must be 100 or less')
    .optional(),
  description: z
    .string()
    .max(500, 'Description must be 500 characters or less')
    .optional(),
  amenities: z
    .array(z.string().uuid())
    .optional(),
  is_active: z
    .boolean()
    .default(true),
});

export type RoomFormData = z.infer<typeof roomFormSchema>;
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B3.3](#step-b33-form-implementation)
- Ada ✗ → Perbaiki schema

---

### STEP B3.3: Form Implementation

📋 **Konteks:**
Implement form dengan react-hook-form.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md - #11 Frontend Patterns](./DEVELOPMENT_STANDARDS_V2.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | useForm dengan zodResolver |
| ☐ | Form components connected dengan Controller |
| ☐ | Error messages displayed |
| ☐ | Submit handler |
| ☐ | Reset on success |
| ☐ | Default values for edit mode |

**Form Implementation Pattern:**

```typescript
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { roomFormSchema, RoomFormData } from './schema';

interface RoomFormProps {
  defaultValues?: Partial<RoomFormData>;
  onSubmit: (data: RoomFormData) => void;
  isLoading?: boolean;
}

export function RoomForm({ defaultValues, onSubmit, isLoading }: RoomFormProps) {
  const {
    control,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<RoomFormData>({
    resolver: zodResolver(roomFormSchema),
    defaultValues: {
      room_number: '',
      room_type_id: '',
      floor: undefined,
      description: '',
      amenities: [],
      is_active: true,
      ...defaultValues,
    },
  });

  const handleFormSubmit = (data: RoomFormData) => {
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)}>
      <div className="space-y-6">
        {/* Room Number */}
        <Controller
          name="room_number"
          control={control}
          render={({ field }) => (
            <FormField
              label="Room Number"
              required
              error={errors.room_number?.message}
            >
              <Input {...field} placeholder="e.g., 101" />
            </FormField>
          )}
        />

        {/* Room Type */}
        <Controller
          name="room_type_id"
          control={control}
          render={({ field }) => (
            <FormField
              label="Room Type"
              required
              error={errors.room_type_id?.message}
            >
              <RoomTypeSelect
                value={field.value}
                onChange={field.onChange}
              />
            </FormField>
          )}
        />

        {/* Floor */}
        <Controller
          name="floor"
          control={control}
          render={({ field }) => (
            <FormField
              label="Floor"
              error={errors.floor?.message}
            >
              <NumberInput
                {...field}
                min={1}
                max={100}
              />
            </FormField>
          )}
        />

        {/* Is Active */}
        <Controller
          name="is_active"
          control={control}
          render={({ field }) => (
            <FormField label="Active">
              <Toggle
                checked={field.value}
                onChange={field.onChange}
              />
            </FormField>
          )}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-4 mt-8">
        <Button type="submit" loading={isLoading} disabled={!isDirty}>
          {defaultValues ? 'Update Room' : 'Create Room'}
        </Button>
        <Button type="button" variant="ghost" onClick={() => reset()}>
          Reset
        </Button>
      </div>
    </form>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B3.4](#step-b34-error-handling)
- Ada ✗ → Perbaiki implementation

---

### STEP B3.4: Error Handling

📋 **Konteks:**
Handle form errors (client & server).

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS.md - #7 Error Handling](./DEVELOPMENT_STANDARDS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Client validation errors displayed inline |
| ☐ | Server validation errors mapped to fields |
| ☐ | General errors shown in alert |
| ☐ | Network errors handled |

**Error Handling Pattern:**

```typescript
function CreateRoomPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const mutation = useMutation({
    mutationFn: roomApi.create,
    onSuccess: (room) => {
      toast({ title: 'Room created successfully' });
      navigate(`/pms/rooms/${room.id}`);
    },
    onError: (error: ApiError) => {
      // Handle validation errors from server
      if (error.code === 'VALIDATION_ERROR' && error.details) {
        // Map server errors to form fields
        error.details.forEach(({ field, message }) => {
          form.setError(field as keyof RoomFormData, {
            type: 'server',
            message,
          });
        });
      } else {
        // General error
        toast({
          title: 'Failed to create room',
          description: error.message,
          variant: 'error',
        });
      }
    },
  });

  return (
    <RoomForm
      onSubmit={mutation.mutate}
      isLoading={mutation.isPending}
    />
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B3.5](#step-b35-testing)
- Ada ✗ → Perbaiki error handling

---

### STEP B3.5: Testing

📋 **Konteks:**
Test form dengan unit dan integration tests.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test renders all fields |
| ☐ | Test validation errors |
| ☐ | Test successful submission |
| ☐ | Test server error handling |
| ☐ | Test edit mode with default values |

**Test Pattern:**

```typescript
describe('RoomForm', () => {
  it('shows validation errors for required fields', async () => {
    render(<RoomForm onSubmit={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText(/room number is required/i)).toBeInTheDocument();
    });
  });

  it('submits valid form data', async () => {
    const onSubmit = vi.fn();
    render(<RoomForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/room number/i), '101');
    await userEvent.click(screen.getByLabelText(/room type/i));
    await userEvent.click(screen.getByText('Standard'));
    fireEvent.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ room_number: '101' })
      );
    });
  });

  it('populates default values in edit mode', () => {
    render(
      <RoomForm
        defaultValues={{ room_number: '101', floor: 1 }}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByLabelText(/room number/i)).toHaveValue('101');
    expect(screen.getByLabelText(/floor/i)).toHaveValue(1);
  });
});
```

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW B3 SELESAI**
- Ada ✗ → Tulis tests

---

### STEP B3.6: Final Checklist

```
FINAL CHECKLIST - CREATE FORM
═══════════════════════════════════════════

Design
☐ All fields identified
☐ Validation rules defined
☐ Field types correct

Validation
☐ Zod schema complete
☐ Custom error messages
☐ Schema matches backend

Implementation
☐ react-hook-form setup
☐ Controller for each field
☐ Error display
☐ Loading state
☐ Default values (edit mode)

Error Handling
☐ Client validation errors
☐ Server validation errors
☐ General errors

Quality
☐ Tests written
☐ Validation tested
☐ Submission tested
```

---

## Flow B4: Create Data Table

> Membuat table dengan sorting, filtering, pagination

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Data API sudah ada
☐ Columns sudah ditentukan
☐ Actions per row sudah ditentukan
```

---

### STEP B4.1: Table Design

📋 **Konteks:**
Design table columns dan features.

📖 **Acuan:**
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Columns defined (label, key, sortable?) |
| ☐ | Column widths/responsive behavior |
| ☐ | Row actions (view, edit, delete) |
| ☐ | Bulk actions (if needed) |
| ☐ | Filters |
| ☐ | Sorting |
| ☐ | Pagination |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B4.2](#step-b42-column-definitions)
- Ada ✗ → Perbaiki design

---

### STEP B4.2: Column Definitions

📋 **Konteks:**
Define column configuration.

📖 **Acuan:**
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Header labels |
| ☐ | Cell renderers |
| ☐ | Sortable columns flagged |
| ☐ | Column widths |
| ☐ | Mobile visibility |

**Column Definition Pattern:**

```typescript
import { ColumnDef } from '@tanstack/react-table';

export const roomColumns: ColumnDef<Room>[] = [
  {
    accessorKey: 'room_number',
    header: 'Room Number',
    cell: ({ row }) => (
      <Link to={`/pms/rooms/${row.original.id}`}>
        {row.original.room_number}
      </Link>
    ),
    size: 120,
    enableSorting: true,
  },
  {
    accessorKey: 'room_type.name',
    header: 'Type',
    cell: ({ row }) => (
      <Badge variant={row.original.room_type.color}>
        {row.original.room_type.name}
      </Badge>
    ),
    enableSorting: true,
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => <RoomStatusBadge status={row.original.status} />,
    filterFn: 'equals',
  },
  {
    accessorKey: 'floor',
    header: 'Floor',
    size: 80,
    enableSorting: true,
  },
  {
    id: 'actions',
    header: '',
    cell: ({ row }) => <RoomRowActions room={row.original} />,
    size: 60,
  },
];
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B4.3](#step-b43-filtering)
- Ada ✗ → Perbaiki columns

---

### STEP B4.3: Filtering

📋 **Konteks:**
Implement table filters.

📖 **Acuan:**
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[JIKA ADA]`

| # | Item |
|---|------|
| ☐ | Filter fields identified |
| ☐ | Filter values synced with URL |
| ☐ | Reset filters button |
| ☐ | Applied filters indicator |

**Filtering Pattern:**

```typescript
function RoomTableFilters({ filters, onChange }) {
  return (
    <div className="flex gap-4 mb-4">
      {/* Status filter */}
      <Select
        value={filters.status || ''}
        onChange={(value) => onChange({ ...filters, status: value })}
        placeholder="All Status"
      >
        <SelectOption value="">All Status</SelectOption>
        <SelectOption value="available">Available</SelectOption>
        <SelectOption value="occupied">Occupied</SelectOption>
        <SelectOption value="maintenance">Maintenance</SelectOption>
      </Select>

      {/* Room type filter */}
      <RoomTypeSelect
        value={filters.room_type_id}
        onChange={(value) => onChange({ ...filters, room_type_id: value })}
        placeholder="All Types"
      />

      {/* Search */}
      <SearchInput
        value={filters.search}
        onChange={(value) => onChange({ ...filters, search: value })}
        placeholder="Search rooms..."
      />

      {/* Reset */}
      {hasActiveFilters(filters) && (
        <Button variant="ghost" onClick={() => onChange({})}>
          Clear filters
        </Button>
      )}
    </div>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B4.4](#step-b44-sorting)
- Tidak ada filters → Lanjut ke [STEP B4.4](#step-b44-sorting)

---

### STEP B4.4: Sorting

📋 **Konteks:**
Implement server-side sorting.

📖 **Acuan:**
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Sortable columns marked |
| ☐ | Sort state synced with URL |
| ☐ | Sort indicator in header |
| ☐ | Default sort |

**Sorting Pattern:**

```typescript
function useTableSort() {
  const [searchParams, setSearchParams] = useSearchParams();

  const sorting = useMemo(() => {
    const sortBy = searchParams.get('sortBy');
    const sortOrder = searchParams.get('sortOrder') || 'asc';
    return sortBy ? [{ id: sortBy, desc: sortOrder === 'desc' }] : [];
  }, [searchParams]);

  const onSortingChange = (updater) => {
    const newSorting = typeof updater === 'function' ? updater(sorting) : updater;
    if (newSorting.length > 0) {
      setSearchParams({
        ...Object.fromEntries(searchParams),
        sortBy: newSorting[0].id,
        sortOrder: newSorting[0].desc ? 'desc' : 'asc',
      });
    } else {
      searchParams.delete('sortBy');
      searchParams.delete('sortOrder');
      setSearchParams(searchParams);
    }
  };

  return { sorting, onSortingChange };
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B4.5](#step-b45-pagination)
- Ada ✗ → Perbaiki sorting

---

### STEP B4.5: Pagination

📋 **Konteks:**
Implement pagination.

📖 **Acuan:**
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Page state synced with URL |
| ☐ | Page size options |
| ☐ | Total count display |
| ☐ | Page navigation |
| ☐ | Keyboard navigation |

**Pagination Pattern:**

```typescript
function RoomTable() {
  const [searchParams, setSearchParams] = useSearchParams();

  const pagination = useMemo(() => ({
    page: parseInt(searchParams.get('page') || '1'),
    limit: parseInt(searchParams.get('limit') || '20'),
  }), [searchParams]);

  const { data, isLoading } = useRooms({
    ...filters,
    page: pagination.page,
    limit: pagination.limit,
    sortBy: sorting[0]?.id,
    sortOrder: sorting[0]?.desc ? 'desc' : 'asc',
  });

  return (
    <>
      <DataTable
        data={data?.data || []}
        columns={roomColumns}
        loading={isLoading}
      />

      <TablePagination
        page={pagination.page}
        limit={pagination.limit}
        total={data?.meta.total || 0}
        onPageChange={(page) => setSearchParams({ ...params, page: String(page) })}
        onLimitChange={(limit) => setSearchParams({ ...params, limit: String(limit), page: '1' })}
      />
    </>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B4.6](#step-b46-row-actions)
- Ada ✗ → Perbaiki pagination

---

### STEP B4.6: Row Actions

📋 **Konteks:**
Implement row-level actions.

📖 **Acuan:**
- [UI_COMPONENTS.md](./UI_COMPONENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Action menu or buttons |
| ☐ | Permission-based visibility |
| ☐ | Confirmation for destructive |
| ☐ | Loading state for actions |

**Row Actions Pattern:**

```typescript
function RoomRowActions({ room }: { room: Room }) {
  const { can } = usePermissions();
  const navigate = useNavigate();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm">
            <MoreHorizontalIcon className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem
            onClick={() => navigate(`/pms/rooms/${room.id}`)}
          >
            View
          </DropdownMenuItem>
          {can('pms.rooms.update') && (
            <DropdownMenuItem
              onClick={() => navigate(`/pms/rooms/${room.id}/edit`)}
            >
              Edit
            </DropdownMenuItem>
          )}
          {can('pms.rooms.delete') && (
            <DropdownMenuItem
              onClick={() => setShowDeleteDialog(true)}
              className="text-danger-600"
            >
              Delete
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <DeleteRoomDialog
        room={room}
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
      />
    </>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B4.7](#step-b47-testing)
- Ada ✗ → Perbaiki row actions

---

### STEP B4.7: Testing

📋 **Konteks:**
Test data table.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test renders data |
| ☐ | Test sorting |
| ☐ | Test filtering |
| ☐ | Test pagination |
| ☐ | Test row actions |
| ☐ | Test empty state |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW B4 SELESAI**
- Ada ✗ → Tulis tests

---

### STEP B4.8: Final Checklist

```
FINAL CHECKLIST - CREATE DATA TABLE
═══════════════════════════════════════════

Design
☐ Columns defined
☐ Actions defined
☐ Features identified

Implementation
☐ Column definitions complete
☐ Filtering works
☐ Sorting works
☐ Pagination works
☐ Row actions work

State
☐ URL sync for filters/sort/page
☐ Loading states
☐ Empty state

Quality
☐ Tests written
☐ All features tested
```

---

## Flow B5: Create Real-time Feature

> Membuat fitur dengan WebSocket/real-time updates

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Centrifugo sudah ter-setup
☐ Channel naming sudah ditentukan
☐ Event types sudah didefinisikan
```

---

### STEP B5.1: Real-time Design

📋 **Konteks:**
Design real-time feature - channels, events, dan UI updates.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #20 Real-time/WebSocket](./DEVELOPMENT_STANDARDS_V4.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Channel naming sesuai convention |
| ☐ | Event types didefinisikan |
| ☐ | Subscribe/unsubscribe lifecycle |
| ☐ | Reconnection strategy |
| ☐ | UI update pattern |

**Channel Naming:**

```
Format: {tenant}:{module}:{resource}:{scope}

Examples:
- tenant123:pms:rooms:all          # All room updates
- tenant123:pms:room:room-uuid     # Specific room
- tenant123:pms:reservations:all   # All reservation updates
- tenant123:notifications:user-uuid # User notifications
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B5.2](#step-b52-subscription-hook)
- Ada ✗ → Perbaiki design

---

### STEP B5.2: Subscription Hook

📋 **Konteks:**
Create React hook untuk WebSocket subscription.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #20 Real-time/WebSocket](./DEVELOPMENT_STANDARDS_V4.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Hook handles subscribe/unsubscribe |
| ☐ | Connection state exposed |
| ☐ | Error handling |
| ☐ | Cleanup on unmount |

**Subscription Hook Pattern:**

```typescript
// hooks/useRealtime.ts
import { useEffect, useState, useCallback } from 'react';
import { centrifuge } from '@/lib/centrifuge';

interface UseRealtimeOptions<T> {
  channel: string;
  onMessage?: (data: T) => void;
  enabled?: boolean;
}

export function useRealtime<T>({
  channel,
  onMessage,
  enabled = true,
}: UseRealtimeOptions<T>) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const sub = centrifuge.newSubscription(channel);

    sub.on('publication', (ctx) => {
      onMessage?.(ctx.data as T);
    });

    sub.on('subscribed', () => {
      setConnected(true);
      setError(null);
    });

    sub.on('error', (ctx) => {
      setError(new Error(ctx.error.message));
    });

    sub.subscribe();

    return () => {
      sub.unsubscribe();
    };
  }, [channel, enabled, onMessage]);

  return { connected, error };
}

// Usage
function RoomStatusPanel() {
  const queryClient = useQueryClient();
  const tenantId = useTenantId();

  useRealtime<RoomStatusUpdate>({
    channel: `${tenantId}:pms:rooms:all`,
    onMessage: (update) => {
      // Update React Query cache
      queryClient.setQueryData(
        roomKeys.detail(update.room_id),
        (old) => old ? { ...old, status: update.status } : old
      );

      // Or invalidate to refetch
      queryClient.invalidateQueries({ queryKey: roomKeys.lists() });
    },
  });

  // ...
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B5.3](#step-b53-ui-updates)
- Ada ✗ → Perbaiki hook

---

### STEP B5.3: UI Updates

📋 **Konteks:**
Handle UI updates dari real-time events.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #20 Real-time/WebSocket](./DEVELOPMENT_STANDARDS_V4.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Update React Query cache |
| ☐ | Visual feedback untuk updates |
| ☐ | Animation untuk transitions |
| ☐ | Notification untuk important updates |

**UI Update Pattern:**

```typescript
function RoomStatusBoard() {
  const { data: rooms } = useRooms();
  const tenantId = useTenantId();

  useRealtime<RoomStatusUpdate>({
    channel: `${tenantId}:pms:rooms:all`,
    onMessage: useCallback((update) => {
      // Flash animation on updated room
      const element = document.getElementById(`room-${update.room_id}`);
      if (element) {
        element.classList.add('flash-update');
        setTimeout(() => element.classList.remove('flash-update'), 1000);
      }
    }, []),
  });

  return (
    <div className="grid grid-cols-5 gap-4">
      {rooms?.map((room) => (
        <RoomStatusCard
          key={room.id}
          id={`room-${room.id}`}
          room={room}
        />
      ))}
    </div>
  );
}

// CSS
.flash-update {
  animation: flash 1s ease-in-out;
}

@keyframes flash {
  0%, 100% { background-color: transparent; }
  50% { background-color: var(--color-primary-100); }
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B5.4](#step-b54-connection-handling)
- Ada ✗ → Perbaiki UI updates

---

### STEP B5.4: Connection Handling

📋 **Konteks:**
Handle connection states dan reconnection.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #20 Real-time/WebSocket](./DEVELOPMENT_STANDARDS_V4.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Connection status indicator |
| ☐ | Reconnection dengan backoff |
| ☐ | Offline handling |
| ☐ | Token refresh |

**Connection Handling Pattern:**

```typescript
function RealtimeProvider({ children }) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const { getAccessToken } = useAuth();

  useEffect(() => {
    centrifuge.on('connected', () => setStatus('connected'));
    centrifuge.on('disconnected', () => setStatus('disconnected'));

    // Token refresh
    centrifuge.setToken(getAccessToken());

    centrifuge.connect();

    return () => {
      centrifuge.disconnect();
    };
  }, [getAccessToken]);

  return (
    <RealtimeContext.Provider value={{ status }}>
      {children}
      {status === 'disconnected' && (
        <ConnectionBanner>
          Connection lost. Reconnecting...
        </ConnectionBanner>
      )}
    </RealtimeContext.Provider>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP B5.5](#step-b55-testing)
- Ada ✗ → Perbaiki connection handling

---

### STEP B5.5: Testing

📋 **Konteks:**
Test real-time features.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Mock WebSocket connection |
| ☐ | Test message handling |
| ☐ | Test UI updates |
| ☐ | Test reconnection |

**Test Pattern:**

```typescript
import { vi } from 'vitest';

// Mock Centrifuge
vi.mock('@/lib/centrifuge', () => ({
  centrifuge: {
    newSubscription: vi.fn(() => ({
      on: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    })),
  },
}));

describe('RoomStatusBoard', () => {
  it('updates room status on realtime event', async () => {
    const mockSub = {
      on: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    centrifuge.newSubscription.mockReturnValue(mockSub);

    render(<RoomStatusBoard />);

    // Get the publication handler
    const publicationHandler = mockSub.on.mock.calls
      .find(([event]) => event === 'publication')?.[1];

    // Simulate event
    publicationHandler({ data: { room_id: 'room-1', status: 'occupied' } });

    await waitFor(() => {
      expect(screen.getByTestId('room-room-1')).toHaveClass('status-occupied');
    });
  });
});
```

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW B5 SELESAI**
- Ada ✗ → Tulis tests

---

### STEP B5.6: Final Checklist

```
FINAL CHECKLIST - CREATE REAL-TIME FEATURE
══════════════════════════════════════════════

Design
☐ Channels defined
☐ Events defined
☐ Update strategy defined

Implementation
☐ Subscription hook works
☐ UI updates smoothly
☐ Connection status shown
☐ Reconnection works

Quality
☐ Tests with mocked WebSocket
☐ UI updates tested
```

---

---

## Flow C1: Create CRUD Feature

> Membuat fitur CRUD lengkap (Backend + Frontend)

### Overview

Flow ini adalah **compound flow** yang menggabungkan beberapa flow dasar:
- Backend: A1 (API), A2 (Database), A3 (Service)
- Frontend: B2 (Page), B3 (Form), B4 (Table)

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Entity/resource sudah didefinisikan
☐ Fields dan validasi sudah ditentukan
☐ Permissions sudah ditentukan
```

---

### STEP C1.1: Feature Planning

📋 **Konteks:**
Plan the entire feature before implementing.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Resource name ditentukan (e.g., Room, RoomType, Guest) |
| ☐ | All fields identified |
| ☐ | Validation rules defined |
| ☐ | Permissions defined |
| ☐ | Relationships defined |
| ☐ | List view columns defined |
| ☐ | Form fields defined |
| ☐ | Filter options defined |

**Feature Planning Template:**

```markdown
# Feature: [Resource Name]

## Fields
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| name | string | yes | max 100 |
| ... | ... | ... | ... |

## Permissions
- {module}.{resource}.read
- {module}.{resource}.create
- {module}.{resource}.update
- {module}.{resource}.delete

## API Endpoints
- GET    /api/v1/{module}/{resources}
- GET    /api/v1/{module}/{resources}/:id
- POST   /api/v1/{module}/{resources}
- PUT    /api/v1/{module}/{resources}/:id
- DELETE /api/v1/{module}/{resources}/:id

## Pages
- List: /{module}/{resources}
- Detail: /{module}/{resources}/:id
- Create: /{module}/{resources}/new
- Edit: /{module}/{resources}/:id/edit
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C1.2](#step-c12-database-setup)

---

### STEP C1.2: Database Setup

📋 **Konteks:**
Create database table and model.

📖 **Acuan:**
- [Flow A2: Create Database Table](#flow-a2-create-database-table)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Table design complete (Flow A2.1) |
| ☐ | Data types appropriate (Flow A2.2) |
| ☐ | Constraints & indexes (Flow A2.3) |
| ☐ | Relationships defined (Flow A2.4) |
| ☐ | Migration file created (Flow A2.5) |
| ☐ | Model class created (Flow A2.6) |
| ☐ | DATABASE.md updated (Flow A2.7) |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C1.3](#step-c13-backend-api)

---

### STEP C1.3: Backend API

📋 **Konteks:**
Create all CRUD endpoints.

📖 **Acuan:**
- [Flow A1: Create API Endpoint](#flow-a1-create-api-endpoint)
- [Flow A3: Create Service](#flow-a3-create-servicebusiness-logic)

☑️ **Checklist - List Endpoint (GET /resources):** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | URL & naming (A1.1) |
| ☐ | Query params: page, limit, sort, filters |
| ☐ | Response dengan pagination |
| ☐ | Tenant isolation |
| ☐ | Permission check |
| ☐ | Caching (if applicable) |

☑️ **Checklist - Get Single (GET /resources/:id):** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Return 404 if not found |
| ☐ | Include related data if needed |
| ☐ | Tenant isolation |
| ☐ | Permission check |

☑️ **Checklist - Create (POST /resources):** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Request validation |
| ☐ | Business rule validation |
| ☐ | Return 201 Created |
| ☐ | Audit log |
| ☐ | Cache invalidation |

☑️ **Checklist - Update (PUT /resources/:id):** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Request validation |
| ☐ | Return 404 if not found |
| ☐ | Business rule validation |
| ☐ | Audit log dengan old/new values |
| ☐ | Cache invalidation |

☑️ **Checklist - Delete (DELETE /resources/:id):** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Soft delete (set deleted_at) |
| ☐ | Return 404 if not found |
| ☐ | Check dependencies before delete |
| ☐ | Audit log |
| ☐ | Cache invalidation |

☑️ **Checklist - Service Layer:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Service class created |
| ☐ | Business rules implemented |
| ☐ | Error handling proper |
| ☐ | Logging implemented |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C1.4](#step-c14-backend-testing)

---

### STEP C1.4: Backend Testing

📋 **Konteks:**
Test all API endpoints.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Unit tests untuk service |
| ☐ | Integration tests untuk semua endpoints |
| ☐ | Test happy path |
| ☐ | Test validation errors |
| ☐ | Test not found errors |
| ☐ | Test permission denied |
| ☐ | Test tenant isolation |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C1.5](#step-c15-frontend-list-page)

---

### STEP C1.5: Frontend - List Page

📋 **Konteks:**
Create list page dengan table.

📖 **Acuan:**
- [Flow B2: Create Page](#flow-b2-create-pageview)
- [Flow B4: Create Data Table](#flow-b4-create-data-table)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Page created (B2) |
| ☐ | Data table with columns (B4.2) |
| ☐ | Filters working (B4.3) |
| ☐ | Sorting working (B4.4) |
| ☐ | Pagination working (B4.5) |
| ☐ | Row actions (view, edit, delete) (B4.6) |
| ☐ | Loading/empty/error states |
| ☐ | Add button with permission check |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C1.6](#step-c16-frontend-form)

---

### STEP C1.6: Frontend - Form

📋 **Konteks:**
Create form untuk create dan edit.

📖 **Acuan:**
- [Flow B3: Create Form](#flow-b3-create-form)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Zod schema (B3.2) |
| ☐ | Form component (B3.3) |
| ☐ | All fields implemented |
| ☐ | Validation working |
| ☐ | Error handling (B3.4) |
| ☐ | Create page |
| ☐ | Edit page dengan default values |
| ☐ | Success redirect |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C1.7](#step-c17-frontend-detail-page)

---

### STEP C1.7: Frontend - Detail Page

📋 **Konteks:**
Create detail page (optional, bisa skip jika tidak perlu).

📖 **Acuan:**
- [Flow B2: Create Page](#flow-b2-create-pageview)

☑️ **Checklist:** `[OPSIONAL]`

| # | Item |
|---|------|
| ☐ | Detail page created |
| ☐ | All fields displayed |
| ☐ | Related data displayed |
| ☐ | Edit button with permission |
| ☐ | Delete button with permission |
| ☐ | Loading/error states |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C1.8](#step-c18-frontend-testing)

---

### STEP C1.8: Frontend Testing

📋 **Konteks:**
Test all frontend components.

📖 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | List page tests |
| ☐ | Form tests |
| ☐ | Detail page tests (if applicable) |
| ☐ | Test all states |
| ☐ | Test user interactions |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C1.9](#step-c19-documentation)

---

### STEP C1.9: Documentation

📋 **Konteks:**
Update all documentation.

📖 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | DATABASE.md updated |
| ☐ | API.md updated |
| ☐ | FEATURES.md updated |
| ☐ | CHANGELOG.md updated |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW C1 SELESAI**

---

### STEP C1.10: Final Checklist

```
FINAL CHECKLIST - CREATE CRUD FEATURE
══════════════════════════════════════════════

Database
☐ Table created with all required columns
☐ Indexes created
☐ Model class created
☐ Migration tested

Backend API
☐ List endpoint (GET)
☐ Get single endpoint (GET/:id)
☐ Create endpoint (POST)
☐ Update endpoint (PUT)
☐ Delete endpoint (DELETE)
☐ All with proper validation
☐ All with proper error handling
☐ All with tenant isolation
☐ All with permission check
☐ Audit logging

Frontend
☐ List page with table
☐ Filters, sorting, pagination
☐ Create form
☐ Edit form
☐ Detail page (if applicable)
☐ Delete confirmation
☐ All states handled

Testing
☐ Backend unit tests
☐ Backend integration tests
☐ Frontend tests
☐ Coverage >= 80%

Documentation
☐ DATABASE.md
☐ API.md
☐ FEATURES.md
☐ CHANGELOG.md
```

---

## Flow C2: Create Report Feature

> Membuat fitur report/export

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Report type sudah ditentukan (PDF, Excel, CSV)
☐ Data source sudah ada
☐ Report template/layout sudah didesign
```

---

### STEP C2.1: Report Design

📋 **Konteks:**
Design report structure dan format.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V8.md - #33 Report Generation](./DEVELOPMENT_STANDARDS_V8.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Report name dan purpose |
| ☐ | Output format(s): PDF / Excel / CSV |
| ☐ | Parameters (date range, filters) |
| ☐ | Data columns |
| ☐ | Grouping/subtotals |
| ☐ | Header/footer content |
| ☐ | File naming convention |

**Report Design Template:**

```markdown
# Report: Occupancy Report

## Parameters
- Date Range (start_date, end_date)
- Room Type (optional)
- Floor (optional)

## Columns
| Column | Source | Format |
|--------|--------|--------|
| Date | occupancy.date | YYYY-MM-DD |
| Room Type | room_type.name | string |
| Total Rooms | count | integer |
| Occupied | count | integer |
| Occupancy % | calculated | percentage |

## Output
- Format: PDF, Excel
- Filename: occupancy_report_{start}_{end}.{ext}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C2.2](#step-c22-backend-report-service)

---

### STEP C2.2: Backend Report Service

📋 **Konteks:**
Create report generation service.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V8.md - #33 Report Generation](./DEVELOPMENT_STANDARDS_V8.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Report service class |
| ☐ | Data query optimized |
| ☐ | PDF generator (WeasyPrint) |
| ☐ | Excel generator (openpyxl) |
| ☐ | CSV generator |
| ☐ | Template untuk PDF |

**Report Service Pattern:**

```python
class OccupancyReportService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def generate(
        self,
        start_date: date,
        end_date: date,
        format: str = 'pdf',
        room_type_id: UUID = None
    ) -> ReportResult:
        # Fetch data
        data = self._fetch_data(start_date, end_date, room_type_id)

        # Generate report
        if format == 'pdf':
            content = self._generate_pdf(data)
        elif format == 'excel':
            content = self._generate_excel(data)
        else:
            content = self._generate_csv(data)

        # Generate filename
        filename = f"occupancy_report_{start_date}_{end_date}.{format}"

        return ReportResult(
            filename=filename,
            content=content,
            content_type=CONTENT_TYPES[format]
        )
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C2.3](#step-c23-background-job)

---

### STEP C2.3: Background Job (for large reports)

📋 **Konteks:**
Create background job untuk large reports.

📖 **Acuan:**
- [Flow A4: Create Background Job](#flow-a4-create-background-job)

🔀 **Kondisi:**
- **Jika** report kecil (< 1000 rows) → Skip ke [STEP C2.4](#step-c24-api-endpoint)
- **Jika** report besar → Implement background job

☑️ **Checklist:** `[JIKA ADA - untuk large reports]`

| # | Item |
|---|------|
| ☐ | Celery task created |
| ☐ | Progress tracking |
| ☐ | File saved to storage (R2) |
| ☐ | Notification when done |
| ☐ | Download URL generated |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C2.4](#step-c24-api-endpoint)

---

### STEP C2.4: API Endpoint

📋 **Konteks:**
Create API endpoint untuk request report.

📖 **Acuan:**
- [Flow A1: Create API Endpoint](#flow-a1-create-api-endpoint)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Endpoint: POST /reports/{report_type} |
| ☐ | Request validation (parameters) |
| ☐ | Permission check |
| ☐ | For small: Return file directly |
| ☐ | For large: Return job ID, then poll/webhook |
| ☐ | Endpoint: GET /reports/download/{file_id} |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C2.5](#step-c25-frontend-ui)

---

### STEP C2.5: Frontend UI

📋 **Konteks:**
Create UI untuk request report.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Report page atau modal |
| ☐ | Parameter form (date range, filters) |
| ☐ | Format selection |
| ☐ | Generate button |
| ☐ | Loading state |
| ☐ | Download trigger |
| ☐ | Progress indicator (for async) |

**Frontend Pattern:**

```typescript
function ReportDialog({ reportType, open, onClose }) {
  const mutation = useMutation({
    mutationFn: (params) => reportApi.generate(reportType, params),
    onSuccess: (data) => {
      if (data.download_url) {
        // Small report - download directly
        window.open(data.download_url);
      } else {
        // Large report - show progress
        setJobId(data.job_id);
      }
    },
  });

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Generate {reportType} Report</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DateRangePicker
            value={dateRange}
            onChange={setDateRange}
          />
          <Select value={format} onChange={setFormat}>
            <SelectOption value="pdf">PDF</SelectOption>
            <SelectOption value="excel">Excel</SelectOption>
          </Select>
        </form>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={() => mutation.mutate({ ...dateRange, format })}
          loading={mutation.isPending}
        >
          Generate
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C2.6](#step-c26-testing)

---

### STEP C2.6: Testing

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Unit test report service |
| ☐ | Test PDF generation |
| ☐ | Test Excel generation |
| ☐ | Test CSV generation |
| ☐ | Integration test endpoint |
| ☐ | Frontend tests |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW C2 SELESAI**

---

## Flow C3: Create Search Feature

> Membuat fitur search dengan Meilisearch

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Meilisearch sudah ter-setup
☐ Index sudah ditentukan
☐ Searchable fields sudah ditentukan
```

---

### STEP C3.1: Search Design

📋 **Konteks:**
Design search index dan fields.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V4.md - #22 Search (Meilisearch)](./DEVELOPMENT_STANDARDS_V4.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Index name: `{tenant}_{entity}` |
| ☐ | Searchable fields identified |
| ☐ | Filterable fields identified |
| ☐ | Sortable fields identified |
| ☐ | Displayed fields identified |
| ☐ | Synonyms (if needed) |
| ☐ | Stop words (if needed) |

**Search Index Design:**

```python
INDEX_CONFIG = {
    "name": "{tenant}_rooms",
    "primary_key": "id",
    "searchable_attributes": [
        "room_number",
        "room_type_name",
        "description"
    ],
    "filterable_attributes": [
        "tenant_id",
        "status",
        "room_type_id",
        "floor",
        "is_active"
    ],
    "sortable_attributes": [
        "room_number",
        "floor",
        "created_at"
    ],
    "displayed_attributes": [
        "id",
        "room_number",
        "room_type_name",
        "status",
        "floor"
    ]
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C3.2](#step-c32-indexing-service)

---

### STEP C3.2: Indexing Service

📋 **Konteks:**
Create service untuk index management.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Index creation/setup |
| ☐ | Document indexing (add/update) |
| ☐ | Document deletion |
| ☐ | Bulk indexing |
| ☐ | Index rebuild |

**Indexing Service Pattern:**

```python
class RoomSearchService:
    def __init__(self, meili_client, tenant_id: str):
        self.client = meili_client
        self.index_name = f"{tenant_id}_rooms"
        self.index = self.client.index(self.index_name)

    def index_room(self, room: Room) -> None:
        document = {
            "id": str(room.id),
            "room_number": room.room_number,
            "room_type_name": room.room_type.name,
            "description": room.description,
            "status": room.status,
            "floor": room.floor,
            "is_active": room.is_active,
            "tenant_id": str(room.tenant_id),
        }
        self.index.add_documents([document])

    def delete_room(self, room_id: str) -> None:
        self.index.delete_document(room_id)

    def search(
        self,
        query: str,
        filters: dict = None,
        page: int = 1,
        limit: int = 20
    ) -> SearchResult:
        filter_str = self._build_filter(filters)
        return self.index.search(
            query,
            {
                "filter": filter_str,
                "offset": (page - 1) * limit,
                "limit": limit,
            }
        )
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C3.3](#step-c33-sync-mechanism)

---

### STEP C3.3: Sync Mechanism

📋 **Konteks:**
Keep search index in sync with database.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Index on create |
| ☐ | Update on update |
| ☐ | Delete on delete |
| ☐ | Use events/signals untuk sync |
| ☐ | Async indexing (background job) |

**Sync via Events:**

```python
# In service layer
class RoomService:
    def create(self, data: RoomCreate) -> Room:
        room = self._create_room(data)

        # Publish event for async indexing
        self.event_publisher.publish_room_created(room)

        return room

# Event consumer
class SearchIndexConsumer:
    def handle_room_created(self, event):
        room = self.room_repo.get_by_id(event.data.room_id)
        self.search_service.index_room(room)

    def handle_room_updated(self, event):
        room = self.room_repo.get_by_id(event.data.room_id)
        self.search_service.index_room(room)

    def handle_room_deleted(self, event):
        self.search_service.delete_room(event.data.room_id)
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C3.4](#step-c34-search-api)

---

### STEP C3.4: Search API

📋 **Konteks:**
Create search API endpoint.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Endpoint: GET /search?q={query}&type={entity} |
| ☐ | Or: GET /{resources}/search?q={query} |
| ☐ | Query parameter validation |
| ☐ | Tenant filter (automatic) |
| ☐ | Additional filters |
| ☐ | Pagination |
| ☐ | Highlighting (optional) |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C3.5](#step-c35-frontend-search)

---

### STEP C3.5: Frontend Search

📋 **Konteks:**
Create search UI.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Search input component |
| ☐ | Debounced input |
| ☐ | Loading state |
| ☐ | Results display |
| ☐ | Empty state |
| ☐ | Keyboard navigation |
| ☐ | Recent searches (optional) |

**Search Component Pattern:**

```typescript
function GlobalSearch() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);

  const { data, isLoading } = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchApi.search(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  return (
    <Command>
      <CommandInput
        placeholder="Search..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {isLoading && <CommandLoading />}
        {!isLoading && !data?.length && query.length >= 2 && (
          <CommandEmpty>No results found</CommandEmpty>
        )}
        {data?.map((result) => (
          <CommandItem
            key={result.id}
            onSelect={() => navigate(result.url)}
          >
            <result.icon className="mr-2" />
            {result.title}
          </CommandItem>
        ))}
      </CommandList>
    </Command>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C3.6](#step-c36-testing)

---

### STEP C3.6: Testing

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test indexing service |
| ☐ | Test search API |
| ☐ | Test sync mechanism |
| ☐ | Test frontend search |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW C3 SELESAI**

---

## Flow C4: Create Notification Feature

> Membuat fitur notifikasi

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Notification channels sudah ditentukan (in-app, email, push)
☐ Event triggers sudah ditentukan
☐ Templates sudah didesign
```

---

### STEP C4.1: Notification Design

📋 **Konteks:**
Design notification system.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V5.md - #23 Notification](./DEVELOPMENT_STANDARDS_V5.md)
- [DEVELOPMENT_STANDARDS_V9.md - #35 Email Templates](./DEVELOPMENT_STANDARDS_V9.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Notification types identified |
| ☐ | Channels per type (in-app, email, push, SMS) |
| ☐ | Trigger events identified |
| ☐ | Template content |
| ☐ | User preferences schema |

**Notification Design Template:**

```markdown
# Notification: Reservation Confirmed

## Trigger
Event: pms.reservation.confirmed

## Channels
- In-app: Yes (default)
- Email: Yes (if enabled)
- Push: Yes (if enabled)

## Template
Title: Reservation Confirmed - {{reservation.confirmation_number}}
Body: Your reservation at {{property.name}} has been confirmed.
      Check-in: {{reservation.check_in_date}}
      Check-out: {{reservation.check_out_date}}

## Recipients
- Guest (reservation.guest)
- Property owner (if configured)

## Actions
- View Reservation: /reservations/{{reservation.id}}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C4.2](#step-c42-notification-service)

---

### STEP C4.2: Notification Service

📋 **Konteks:**
Create notification service.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Notification service class |
| ☐ | Channel handlers (in-app, email, push) |
| ☐ | Template rendering |
| ☐ | User preference check |
| ☐ | Rate limiting |

**Notification Service Pattern:**

```python
class NotificationService:
    def __init__(self, channels: list[NotificationChannel]):
        self.channels = {c.name: c for c in channels}

    async def send(
        self,
        notification_type: str,
        recipients: list[User],
        data: dict,
        channels: list[str] = None
    ):
        template = self._get_template(notification_type)
        rendered = self._render_template(template, data)

        for recipient in recipients:
            # Check user preferences
            enabled_channels = self._get_enabled_channels(
                recipient, notification_type, channels
            )

            for channel_name in enabled_channels:
                channel = self.channels[channel_name]
                await channel.send(recipient, rendered)

                # Log notification
                self._log_notification(
                    recipient, notification_type, channel_name
                )
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C4.3](#step-c43-event-consumers)

---

### STEP C4.3: Event Consumers

📋 **Konteks:**
Create event consumers untuk trigger notifications.

📖 **Acuan:**
- [Flow A5: Create Event/Message](#flow-a5-create-eventmessage)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Event consumer created |
| ☐ | Map events to notification types |
| ☐ | Extract recipients dari event |
| ☐ | Extract data untuk template |

**Event Consumer Pattern:**

```python
class NotificationEventConsumer:
    def handle_reservation_confirmed(self, event: ReservationConfirmedEvent):
        # Get recipient
        guest = self.user_repo.get_by_id(event.data.guest_id)

        # Get context data
        reservation = self.reservation_repo.get_by_id(
            event.data.reservation_id
        )
        property = self.property_repo.get_by_id(reservation.property_id)

        # Send notification
        self.notification_service.send(
            notification_type="reservation.confirmed",
            recipients=[guest],
            data={
                "reservation": reservation,
                "property": property,
            }
        )
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C4.4](#step-c44-in-app-notifications)

---

### STEP C4.4: In-App Notifications

📋 **Konteks:**
Create in-app notification system.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Database table untuk notifications |
| ☐ | API: GET /notifications |
| ☐ | API: PUT /notifications/:id/read |
| ☐ | API: PUT /notifications/read-all |
| ☐ | Real-time via WebSocket |
| ☐ | Unread count |

**Database Schema:**

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    data JSONB,
    action_url VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C4.5](#step-c45-frontend-notification-ui)

---

### STEP C4.5: Frontend Notification UI

📋 **Konteks:**
Create notification UI.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Notification bell icon dengan badge |
| ☐ | Notification dropdown/panel |
| ☐ | Real-time updates |
| ☐ | Mark as read |
| ☐ | Mark all as read |
| ☐ | Notification preferences page |

**Notification UI Pattern:**

```typescript
function NotificationBell() {
  const { data: notifications, refetch } = useNotifications();
  const unreadCount = notifications?.filter(n => !n.is_read).length || 0;

  // Real-time updates
  useRealtime({
    channel: `notifications:${userId}`,
    onMessage: () => refetch(),
  });

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" className="relative">
          <BellIcon />
          {unreadCount > 0 && (
            <Badge className="absolute -top-1 -right-1">
              {unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <NotificationList notifications={notifications} />
      </PopoverContent>
    </Popover>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C4.6](#step-c46-testing)

---

### STEP C4.6: Testing

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test notification service |
| ☐ | Test event consumers |
| ☐ | Test channel handlers |
| ☐ | Test API endpoints |
| ☐ | Test frontend UI |
| ☐ | Test real-time updates |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW C4 SELESAI**

---

## Flow C5: Create File Upload Feature

> Membuat fitur upload file

### Pre-requisite Check

```
Sebelum mulai, pastikan:
☐ Cloudflare R2 sudah ter-setup
☐ File types dan size limits sudah ditentukan
☐ Access control sudah ditentukan
```

---

### STEP C5.1: File Upload Design

📋 **Konteks:**
Design file upload system.

📖 **Acuan:**
- [DEVELOPMENT_STANDARDS_V3.md - #19 File/Media Handling](./DEVELOPMENT_STANDARDS_V3.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Allowed file types |
| ☐ | Max file size |
| ☐ | Storage path structure |
| ☐ | Access control (public/private) |
| ☐ | Thumbnail generation (for images) |
| ☐ | Virus scanning requirement |

**File Upload Design:**

```markdown
# File Upload: Guest Documents

## Allowed Types
- Images: jpg, jpeg, png, gif (max 5MB)
- Documents: pdf (max 10MB)

## Storage Path
Format: {tenant_id}/{module}/{entity_type}/{entity_id}/{filename}
Example: tenant-uuid/pms/guests/guest-uuid/passport.jpg

## Access Control
- Type: Private (signed URLs)
- URL expiry: 1 hour

## Processing
- Images: Generate thumbnail (200x200)
- Documents: Virus scan
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C5.2](#step-c52-storage-service)

---

### STEP C5.2: Storage Service

📋 **Konteks:**
Create storage service untuk R2.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Storage service class |
| ☐ | Upload to R2 |
| ☐ | Download/get signed URL |
| ☐ | Delete file |
| ☐ | List files |
| ☐ | Presigned upload URL (for direct upload) |

**Storage Service Pattern:**

```python
class StorageService:
    def __init__(self, r2_client, bucket: str):
        self.client = r2_client
        self.bucket = bucket

    async def upload(
        self,
        file: UploadFile,
        path: str,
        public: bool = False
    ) -> FileInfo:
        # Validate file
        self._validate_file(file)

        # Generate unique filename
        filename = self._generate_filename(file.filename)
        full_path = f"{path}/{filename}"

        # Upload to R2
        await self.client.upload_fileobj(
            file.file,
            self.bucket,
            full_path,
            ExtraArgs={
                'ContentType': file.content_type,
                'ACL': 'public-read' if public else 'private'
            }
        )

        return FileInfo(
            filename=filename,
            path=full_path,
            size=file.size,
            content_type=file.content_type,
            url=self._get_url(full_path, public)
        )

    def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': path},
            ExpiresIn=expires_in
        )
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C5.3](#step-c53-api-endpoints)

---

### STEP C5.3: API Endpoints

📋 **Konteks:**
Create file upload API endpoints.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | POST /files/upload (multipart) |
| ☐ | POST /files/presigned-url (for direct upload) |
| ☐ | GET /files/:id (download/redirect) |
| ☐ | DELETE /files/:id |
| ☐ | File size validation |
| ☐ | File type validation |
| ☐ | Virus scanning (if required) |

**Upload Endpoint Pattern:**

```python
@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    # Validate file
    validate_file(file, allowed_types=ALLOWED_TYPES, max_size=MAX_SIZE)

    # Build path
    path = f"{current_user.tenant_id}/{entity_type}/{entity_id}"

    # Upload
    file_info = await storage_service.upload(file, path)

    # Save metadata to DB
    file_record = await file_repo.create({
        "tenant_id": current_user.tenant_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "filename": file_info.filename,
        "path": file_info.path,
        "size": file_info.size,
        "content_type": file_info.content_type,
        "uploaded_by": current_user.id,
    })

    return file_record
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C5.4](#step-c54-frontend-upload-component)

---

### STEP C5.4: Frontend Upload Component

📋 **Konteks:**
Create file upload UI component.

📖 **Acuan:**
- [UI_COMPONENTS.md - File Upload](./UI_COMPONENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Drag and drop zone |
| ☐ | File type validation (client side) |
| ☐ | File size validation |
| ☐ | Upload progress |
| ☐ | Preview (for images) |
| ☐ | Multiple files (if applicable) |
| ☐ | Error handling |
| ☐ | Remove/cancel upload |

**File Upload Component Pattern:**

```typescript
function FileUpload({
  accept,
  maxSize,
  multiple = false,
  onUpload,
}) {
  const [files, setFiles] = useState<UploadingFile[]>([]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept,
    maxSize,
    multiple,
    onDrop: async (acceptedFiles) => {
      for (const file of acceptedFiles) {
        const uploadingFile = {
          id: generateId(),
          file,
          progress: 0,
          status: 'uploading',
        };

        setFiles((prev) => [...prev, uploadingFile]);

        try {
          const result = await uploadFile(file, {
            onProgress: (progress) => {
              setFiles((prev) =>
                prev.map((f) =>
                  f.id === uploadingFile.id
                    ? { ...f, progress }
                    : f
                )
              );
            },
          });

          setFiles((prev) =>
            prev.map((f) =>
              f.id === uploadingFile.id
                ? { ...f, status: 'complete', result }
                : f
            )
          );

          onUpload?.(result);
        } catch (error) {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === uploadingFile.id
                ? { ...f, status: 'error', error }
                : f
            )
          );
        }
      }
    },
  });

  return (
    <div {...getRootProps()} className={cn(
      'border-2 border-dashed rounded-lg p-6 text-center',
      isDragActive && 'border-primary-500 bg-primary-50'
    )}>
      <input {...getInputProps()} />
      <UploadIcon className="mx-auto mb-2" />
      <p>Drag & drop files here, or click to select</p>
      <p className="text-sm text-gray-500">
        Max size: {formatBytes(maxSize)}
      </p>

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file) => (
            <FileUploadItem
              key={file.id}
              file={file}
              onRemove={() => handleRemove(file.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP C5.5](#step-c55-testing)

---

### STEP C5.5: Testing

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test storage service |
| ☐ | Test API endpoints |
| ☐ | Test file validation |
| ☐ | Test frontend component |
| ☐ | Test upload progress |
| ☐ | Test error scenarios |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW C5 SELESAI**

---

**PART 4 SELESAI**

Flow yang sudah dibuat:
- ✅ A1-A6: Backend Flows
- ✅ B1-B5: Frontend Flows
- ✅ C1: Create CRUD Feature
- ✅ C2: Create Report Feature
- ✅ C3: Create Search Feature
- ✅ C4: Create Notification Feature
- ✅ C5: Create File Upload Feature

Flow yang akan dibuat di Part 5:
- D1: Create New Module
- D2: Add Feature to Module
- E1-E4: Maintenance Flows
- F1-F2: Documentation Flows

---

# PART 5: MODULE & MAINTENANCE FLOWS

---

## D. MODULE FLOWS

---

## FLOW D1: CREATE NEW MODULE

**Kapan menggunakan flow ini:**
- Membuat module baru dalam system (e.g., PMS, POS, HRM)
- Module adalah unit deployment independen
- Module memiliki database schema, API, dan UI sendiri

**Compound Flow** - Menggabungkan multiple atomic flows

**Acuan Utama:**
- [MODULE_ARCHITECTURE.md](./MODULE_ARCHITECTURE.md)
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)
- [PUZZLE_ARCHITECTURE.md](./PUZZLE_ARCHITECTURE.md)
- [DATABASE_SCHEMA_PLATFORM.md](./DATABASE_SCHEMA_PLATFORM.md)
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #3 (RBAC)
- [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md) - Module Colors

---

### PRE-REQUISITE CHECK D1

Sebelum membuat module baru, pastikan:

| # | Item | Status |
|---|------|--------|
| ☐ | Module name sudah disetujui (sesuai daftar 14 modules) | |
| ☐ | Business requirements sudah didokumentasikan | |
| ☐ | Module dependencies sudah diidentifikasi | |
| ☐ | Integration points dengan module lain sudah jelas | |
| ☐ | RBAC roles untuk module sudah didefinisikan | |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.1](#step-d11-module-planning)

---

### STEP D1.1: Module Planning

📋 **Konteks:**
Merencanakan struktur dan scope module baru.

📚 **Acuan:**
- [MODULE_ARCHITECTURE.md](./MODULE_ARCHITECTURE.md) - Module structure
- [PUZZLE_ARCHITECTURE.md](./PUZZLE_ARCHITECTURE.md) - Module boundaries
- [PMS_DECISIONS.md](./PMS_DECISIONS.md) - Approved decisions

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Module name mengikuti naming convention | MODULE_ARCHITECTURE |
| ☐ | Module color sudah assigned | UI_DESIGN_SYSTEM |
| ☐ | Core entities sudah diidentifikasi | |
| ☐ | External integrations sudah diidentifikasi | |
| ☐ | Module boundaries jelas (tidak overlap dengan module lain) | PUZZLE_ARCHITECTURE |
| ☐ | Shared building blocks yang dibutuhkan sudah diidentifikasi | MODULE_ARCHITECTURE |

**Module Color Assignment:**

```typescript
// UI_DESIGN_SYSTEM.md - Module Colors
const MODULE_COLORS = {
  pms: { primary: '#2563EB', secondary: '#3B82F6' },      // Blue
  pos: { primary: '#EA580C', secondary: '#F97316' },      // Orange
  hrm: { primary: '#7C3AED', secondary: '#8B5CF6' },      // Violet
  accounting: { primary: '#059669', secondary: '#10B981' }, // Emerald
  inventory: { primary: '#0891B2', secondary: '#06B6D4' }, // Cyan
  procurement: { primary: '#CA8A04', secondary: '#EAB308' }, // Yellow
  asset: { primary: '#4F46E5', secondary: '#6366F1' },    // Indigo
  guest: { primary: '#DB2777', secondary: '#EC4899' },    // Pink
  channel: { primary: '#0D9488', secondary: '#14B8A6' },  // Teal
  signage: { primary: '#DC2626', secondary: '#EF4444' },  // Red
  supplier: { primary: '#65A30D', secondary: '#84CC16' }, // Lime
  iot: { primary: '#9333EA', secondary: '#A855F7' },      // Purple
  menu: { primary: '#C2410C', secondary: '#EA580C' },     // Orange Dark
  platform: { primary: '#475569', secondary: '#64748B' }  // Slate
};
```

**Module Structure Template:**

```
modules/
└── {module_name}/
    ├── backend/
    │   ├── app/
    │   │   ├── api/
    │   │   │   └── v1/
    │   │   │       ├── endpoints/
    │   │   │       └── router.py
    │   │   ├── core/
    │   │   │   ├── config.py
    │   │   │   └── security.py
    │   │   ├── models/
    │   │   │   └── __init__.py
    │   │   ├── schemas/
    │   │   │   └── __init__.py
    │   │   ├── services/
    │   │   │   └── __init__.py
    │   │   ├── repositories/
    │   │   │   └── __init__.py
    │   │   ├── events/
    │   │   │   ├── publishers/
    │   │   │   └── consumers/
    │   │   ├── jobs/
    │   │   │   └── __init__.py
    │   │   └── integrations/
    │   │       └── __init__.py
    │   ├── migrations/
    │   │   └── versions/
    │   ├── tests/
    │   │   ├── unit/
    │   │   ├── integration/
    │   │   └── conftest.py
    │   ├── alembic.ini
    │   ├── pyproject.toml
    │   └── Dockerfile
    │
    ├── frontend/
    │   ├── src/
    │   │   ├── components/
    │   │   │   ├── common/
    │   │   │   └── features/
    │   │   ├── pages/
    │   │   ├── hooks/
    │   │   ├── services/
    │   │   ├── stores/
    │   │   ├── types/
    │   │   ├── utils/
    │   │   └── routes.tsx
    │   ├── tests/
    │   ├── package.json
    │   └── vite.config.ts
    │
    └── docs/
        ├── README.md
        ├── ARCHITECTURE.md
        ├── API.md
        ├── DATABASE.md
        └── CHANGELOG.md
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.2](#step-d12-database-schema-setup)

---

### STEP D1.2: Database Schema Setup

📋 **Konteks:**
Membuat database schema untuk module baru.

📚 **Acuan:**
- [DATABASE_SCHEMA_PLATFORM.md](./DATABASE_SCHEMA_PLATFORM.md) - Schema patterns
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #2 (Database)
- [DEVELOPMENT_STANDARDS_V7.md](./DEVELOPMENT_STANDARDS_V7.md) - Standard #29 (Multi-tenancy)

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Module menggunakan dedicated schema atau shared schema | DATABASE_SCHEMA_PLATFORM |
| ☐ | Semua tables memiliki tenant_id untuk multi-tenancy | Standard #29 |
| ☐ | Base model fields ada (id, created_at, updated_at, deleted_at) | Standard #2 |
| ☐ | Audit fields ada jika required | Standard #4 |
| ☐ | Foreign keys ke platform tables menggunakan UUID | |
| ☐ | Indexes untuk query patterns sudah ditentukan | |

**Module Base Model:**

```python
# modules/{module}/backend/app/models/base.py
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base

class ModuleBaseModel(Base):
    """Base model untuk semua entities dalam module"""
    __abstract__ = True

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Multi-tenancy - WAJIB
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Audit
    created_by = Column(PGUUID(as_uuid=True), nullable=True)
    updated_by = Column(PGUUID(as_uuid=True), nullable=True)

    @declared_attr
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name"""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
```

**Initial Migration:**

```python
# modules/{module}/backend/migrations/versions/001_initial.py
"""Initial module schema

Revision ID: 001
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = ('{module_name}',)
depends_on = None

def upgrade():
    # Create module schema (optional - jika dedicated schema)
    # op.execute('CREATE SCHEMA IF NOT EXISTS {module_name}')

    # Create lookup tables first
    # Then create main tables
    pass

def downgrade():
    pass
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.3](#step-d13-core-backend-setup)

---

### STEP D1.3: Core Backend Setup

📋 **Konteks:**
Setup core backend structure untuk module.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md](./DEVELOPMENT_STANDARDS_V2.md) - Standard #10 (Code Structure)
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #7 (Error Handling)
- [DEVELOPMENT_STANDARDS_V2.md](./DEVELOPMENT_STANDARDS_V2.md) - Standard #15 (Logging)

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Config module setup dengan environment variables | Standard #10 |
| ☐ | Module-specific exception classes dibuat | Standard #7 |
| ☐ | Logger configured dengan module prefix | Standard #15 |
| ☐ | Dependency injection setup | Standard #10 |
| ☐ | Health check endpoint ada | Standard #38 |
| ☐ | API router structure ada | Standard #6 |

**Module Config:**

```python
# modules/{module}/backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class ModuleSettings(BaseSettings):
    """Module-specific settings"""

    # Module identity
    MODULE_NAME: str = "{module_name}"
    MODULE_VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Feature flags
    FEATURE_FLAGS: dict = {}

    class Config:
        env_prefix = "{MODULE_NAME}_"
        env_file = ".env"

@lru_cache()
def get_settings() -> ModuleSettings:
    return ModuleSettings()

settings = get_settings()
```

**Module Exceptions:**

```python
# modules/{module}/backend/app/core/exceptions.py
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class ModuleException(Exception):
    """Base exception untuk module"""
    def __init__(
        self,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = f"{MODULE_NAME}.{code}"
        self.details = details or {}
        super().__init__(message)

class EntityNotFoundError(ModuleException):
    """Entity tidak ditemukan"""
    def __init__(self, entity: str, id: str):
        super().__init__(
            message=f"{entity} with id {id} not found",
            code="ENTITY_NOT_FOUND",
            details={"entity": entity, "id": id}
        )

class BusinessRuleViolationError(ModuleException):
    """Business rule dilanggar"""
    def __init__(self, rule: str, message: str):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule}
        )

class ValidationError(ModuleException):
    """Validation error"""
    def __init__(self, errors: list):
        super().__init__(
            message="Validation failed",
            code="VALIDATION_ERROR",
            details={"errors": errors}
        )
```

**Module Main App:**

```python
# modules/{module}/backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.exceptions import ModuleException
from app.core.middleware import (
    TenantMiddleware,
    RequestIdMiddleware,
    LoggingMiddleware
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.MODULE_NAME} v{settings.MODULE_VERSION}")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.MODULE_NAME}")

app = FastAPI(
    title=f"{settings.MODULE_NAME.upper()} Module",
    version=settings.MODULE_VERSION,
    lifespan=lifespan
)

# Middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(ModuleException)
async def module_exception_handler(request, exc: ModuleException):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

# Routers
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "module": settings.MODULE_NAME,
        "version": settings.MODULE_VERSION
    }
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.4](#step-d14-rbac-setup)

---

### STEP D1.4: RBAC Setup

📋 **Konteks:**
Setup Role-Based Access Control untuk module.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #3 (RBAC)
- [SECURITY_AUTH_REQUIREMENTS.md](./SECURITY_AUTH_REQUIREMENTS.md) - Permission model
- [DATABASE_SCHEMA_PLATFORM.md](./DATABASE_SCHEMA_PLATFORM.md) - RBAC tables

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Module permissions didefinisikan | Standard #3 |
| ☐ | Default roles untuk module dibuat | |
| ☐ | Permission dependency graph jelas | |
| ☐ | Permission seeder script ada | |
| ☐ | Permission check middleware diterapkan | |

**Module Permissions Definition:**

```python
# modules/{module}/backend/app/core/permissions.py
from enum import Enum
from typing import List

class ModulePermission(str, Enum):
    """Permissions untuk {module_name} module"""

    # Resource permissions (CRUD)
    # Format: {module}.{resource}.{action}

    # Example for PMS:
    # RESERVATION_VIEW = "pms.reservation.view"
    # RESERVATION_CREATE = "pms.reservation.create"
    # RESERVATION_UPDATE = "pms.reservation.update"
    # RESERVATION_DELETE = "pms.reservation.delete"

    # Module-level permissions
    MODULE_ACCESS = "{module}.access"
    MODULE_ADMIN = "{module}.admin"
    MODULE_SETTINGS = "{module}.settings"

    # Report permissions
    REPORTS_VIEW = "{module}.reports.view"
    REPORTS_EXPORT = "{module}.reports.export"

# Permission dependencies
PERMISSION_DEPENDENCIES = {
    ModulePermission.MODULE_ADMIN: [
        ModulePermission.MODULE_ACCESS,
        ModulePermission.MODULE_SETTINGS,
    ],
    # RESERVATION_DELETE implies UPDATE implies VIEW
}

# Default roles
DEFAULT_ROLES = {
    "{module}_admin": {
        "name": "{Module} Administrator",
        "permissions": [p.value for p in ModulePermission],
    },
    "{module}_manager": {
        "name": "{Module} Manager",
        "permissions": [
            ModulePermission.MODULE_ACCESS.value,
            # Add relevant permissions
        ],
    },
    "{module}_staff": {
        "name": "{Module} Staff",
        "permissions": [
            ModulePermission.MODULE_ACCESS.value,
            # Add minimal permissions
        ],
    },
}
```

**Permission Seeder:**

```python
# modules/{module}/backend/app/core/seeders/permissions.py
from app.core.permissions import ModulePermission, DEFAULT_ROLES
from platform.services.rbac import RBACService

async def seed_module_permissions(rbac_service: RBACService):
    """Seed module permissions to platform"""

    # Register permissions
    for permission in ModulePermission:
        await rbac_service.register_permission(
            code=permission.value,
            name=permission.name.replace("_", " ").title(),
            module="{module_name}",
            description=f"Permission for {permission.name}"
        )

    # Create default roles
    for role_code, role_data in DEFAULT_ROLES.items():
        await rbac_service.create_role(
            code=role_code,
            name=role_data["name"],
            permissions=role_data["permissions"],
            module="{module_name}"
        )
```

**Permission Dependency:**

```python
# modules/{module}/backend/app/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from typing import List

from app.core.permissions import ModulePermission
from platform.auth.dependencies import get_current_user
from platform.models.user import User

def require_permissions(permissions: List[ModulePermission]):
    """Dependency untuk require specific permissions"""

    async def check_permissions(
        current_user: User = Depends(get_current_user)
    ) -> User:
        user_permissions = set(current_user.permissions)
        required = set(p.value for p in permissions)

        if not required.issubset(user_permissions):
            missing = required - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "Insufficient permissions",
                    "missing_permissions": list(missing)
                }
            )

        return current_user

    return check_permissions

# Usage in endpoint
@router.get("/reservations")
async def list_reservations(
    current_user: User = Depends(
        require_permissions([ModulePermission.RESERVATION_VIEW])
    )
):
    ...
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.5](#step-d15-frontend-setup)

---

### STEP D1.5: Frontend Setup

📋 **Konteks:**
Setup frontend structure untuk module.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md](./DEVELOPMENT_STANDARDS_V2.md) - Standard #11 (Frontend)
- [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md) - Design system
- [UI_COMPONENTS.md](./UI_COMPONENTS.md) - Component specs

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Vite project initialized dengan correct config | Standard #11 |
| ☐ | TypeScript strict mode enabled | |
| ☐ | Module theme dengan correct color | UI_DESIGN_SYSTEM |
| ☐ | Routing structure setup | |
| ☐ | API client configured | |
| ☐ | Auth integration dengan platform | |

**Frontend Project Structure:**

```typescript
// modules/{module}/frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';

import { ThemeProvider } from '@/providers/ThemeProvider';
import { AuthProvider } from '@/providers/AuthProvider';
import { router } from '@/routes';
import '@/styles/globals.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider module="{module_name}">
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
```

**Module Theme:**

```typescript
// modules/{module}/frontend/src/styles/theme.ts
import { moduleColors } from '@platform/ui-kit';

export const moduleTheme = {
  name: '{module_name}',
  colors: moduleColors.{module_name},

  // Override specific tokens if needed
  tokens: {
    // Semantic colors using module color
    primary: moduleColors.{module_name}.primary,
    primaryHover: moduleColors.{module_name}.secondary,

    // Keep neutral colors from platform
    // ...platformTheme.tokens
  }
};
```

**API Client:**

```typescript
// modules/{module}/frontend/src/services/api.ts
import { createApiClient } from '@platform/api-client';

export const api = createApiClient({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  module: '{module_name}',
});

// Auto-attach tenant header
api.interceptors.request.use((config) => {
  const tenantId = localStorage.getItem('tenant_id');
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  }
  return config;
});
```

**Routes Setup:**

```typescript
// modules/{module}/frontend/src/routes.tsx
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@platform/auth';

import { MainLayout } from '@/layouts/MainLayout';
import { DashboardPage } from '@/pages/Dashboard';
// Import other pages...

export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: (
          <ProtectedRoute permission="{module}.access">
            <DashboardPage />
          </ProtectedRoute>
        ),
      },
      // Add more routes...
    ],
  },
]);
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.6](#step-d16-event-integration)

---

### STEP D1.6: Event Integration

📋 **Konteks:**
Setup event publishing dan consuming untuk module.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS_V3.md](./DEVELOPMENT_STANDARDS_V3.md) - Standard #18 (Events)
- [SHARED_CODE_STANDARDS.md](./SHARED_CODE_STANDARDS.md) - Event bus

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Module event schemas didefinisikan | Standard #18 |
| ☐ | Event publisher setup | |
| ☐ | Event consumers untuk module events | |
| ☐ | Cross-module event subscriptions | |
| ☐ | Dead letter queue configured | |

**Module Events:**

```python
# modules/{module}/backend/app/events/schemas.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Literal

# Event types for this module
EVENT_PREFIX = "{module}"

class ModuleEventBase(BaseModel):
    """Base class untuk module events"""
    event_id: UUID
    event_type: str
    timestamp: datetime
    tenant_id: UUID
    actor_id: UUID | None = None

    # Metadata
    correlation_id: str | None = None
    causation_id: str | None = None

# Example events
class EntityCreatedEvent(ModuleEventBase):
    event_type: Literal[f"{EVENT_PREFIX}.entity.created"] = f"{EVENT_PREFIX}.entity.created"
    entity_id: UUID
    entity_type: str
    data: dict

class EntityUpdatedEvent(ModuleEventBase):
    event_type: Literal[f"{EVENT_PREFIX}.entity.updated"] = f"{EVENT_PREFIX}.entity.updated"
    entity_id: UUID
    entity_type: str
    changes: dict

class EntityDeletedEvent(ModuleEventBase):
    event_type: Literal[f"{EVENT_PREFIX}.entity.deleted"] = f"{EVENT_PREFIX}.entity.deleted"
    entity_id: UUID
    entity_type: str
```

**Event Publisher:**

```python
# modules/{module}/backend/app/events/publisher.py
from platform.events import EventPublisher, EventBus

class ModuleEventPublisher:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.publisher = EventPublisher(
            module="{module_name}",
            event_bus=event_bus
        )

    async def publish_entity_created(
        self,
        entity_id: UUID,
        entity_type: str,
        data: dict,
        tenant_id: UUID,
        actor_id: UUID | None = None
    ):
        event = EntityCreatedEvent(
            event_id=uuid4(),
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            actor_id=actor_id,
            entity_id=entity_id,
            entity_type=entity_type,
            data=data
        )
        await self.publisher.publish(event)
```

**Cross-Module Event Consumer:**

```python
# modules/{module}/backend/app/events/consumers/platform_events.py
from platform.events import EventConsumer, event_handler

class PlatformEventConsumer(EventConsumer):
    """Handle events dari platform dan module lain"""

    @event_handler("platform.tenant.settings_updated")
    async def handle_tenant_settings_updated(self, event: dict):
        """React to tenant settings changes"""
        tenant_id = event["tenant_id"]
        settings = event["settings"]

        # Update module-specific cache
        await self.cache.invalidate(f"tenant:{tenant_id}:settings")

    @event_handler("platform.user.role_changed")
    async def handle_user_role_changed(self, event: dict):
        """React to user role changes"""
        user_id = event["user_id"]

        # Invalidate user permissions cache
        await self.cache.invalidate(f"user:{user_id}:permissions")
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.7](#step-d17-testing-setup)

---

### STEP D1.7: Testing Setup

📋 **Konteks:**
Setup testing infrastructure untuk module.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md](./DEVELOPMENT_STANDARDS_V2.md) - Standard #9 (Testing)
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Test strategy

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | pytest configured dengan fixtures | Standard #9 |
| ☐ | Test database setup dengan transactions | |
| ☐ | Factory classes untuk test data | |
| ☐ | Vitest configured untuk frontend | |
| ☐ | E2E test setup (optional) | |
| ☐ | Coverage thresholds defined | TESTING_STRATEGY |

**Backend Test Config:**

```python
# modules/{module}/backend/tests/conftest.py
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.database import Base
from app.main import app

# Test database
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    settings.DATABASE_URL.split("/")[-1],
    f"test_{settings.MODULE_NAME}"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

@pytest.fixture
def authenticated_client(client, test_user):
    """Client dengan auth token"""
    token = create_access_token(test_user.id)
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

**Factory Classes:**

```python
# modules/{module}/backend/tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from uuid import uuid4

from app.models import Entity
from tests.conftest import TestingSessionLocal

class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = TestingSessionLocal()
        sqlalchemy_session_persistence = "commit"

class EntityFactory(BaseFactory):
    class Meta:
        model = Entity

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    name = factory.Faker("company")
    # Add other fields...
```

**Frontend Test Config:**

```typescript
// modules/{module}/frontend/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: ['node_modules/', 'tests/'],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.8](#step-d18-documentation)

---

### STEP D1.8: Documentation

📋 **Konteks:**
Membuat dokumentasi module sesuai standard.

📚 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md) - Documentation standard

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | README.md dengan overview module | |
| ☐ | ARCHITECTURE.md dengan design decisions | |
| ☐ | API.md dengan endpoint documentation | |
| ☐ | DATABASE.md dengan schema documentation | |
| ☐ | CHANGELOG.md initialized | |
| ☐ | DVL validation passed | MODULE_DOCUMENTATION_STANDARD |

**Module README Template:**

```markdown
# {Module Name} Module

## Overview
Brief description of module purpose and business domain.

## Quick Start
\`\`\`bash
# Backend
cd modules/{module}/backend
poetry install
poetry run uvicorn app.main:app --reload

# Frontend
cd modules/{module}/frontend
bun install
bun dev
\`\`\`

## Features
- Feature 1
- Feature 2
- ...

## Architecture
See [ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## API Reference
See [API.md](./docs/API.md)

## Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | Database connection | - |
| ...

## Dependencies
- Platform Auth Service
- Shared Building Blocks: ...
- External: ...
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D1.9](#step-d19-deployment-setup)

---

### STEP D1.9: Deployment Setup

📋 **Konteks:**
Setup deployment configuration untuk module.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS_V2.md](./DEVELOPMENT_STANDARDS_V2.md) - Standard #12 (DevOps)
- [DEVELOPMENT_STANDARDS_V10.md](./DEVELOPMENT_STANDARDS_V10.md) - Standard #38 (Health Checks)

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Dockerfile untuk backend | |
| ☐ | Dockerfile untuk frontend | |
| ☐ | Docker Compose untuk local dev | |
| ☐ | Kubernetes manifests (jika applicable) | |
| ☐ | CI/CD pipeline configured | Standard #12 |
| ☐ | Health check endpoints verified | Standard #38 |

**Backend Dockerfile:**

```dockerfile
# modules/{module}/backend/Dockerfile
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Production stage
FROM base as production

COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**

```dockerfile
# modules/{module}/frontend/Dockerfile
FROM oven/bun:1 as builder

WORKDIR /app

# Copy package files
COPY package.json bun.lockb ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source
COPY . .

# Build
RUN bun run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Docker Compose for Local Dev:**

```yaml
# modules/{module}/docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/{module}
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    depends_on:
      - db
      - redis
      - rabbitmq
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: {module}
    volumes:
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "15672:15672"

volumes:
  db_data:
  redis_data:
```

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW D1 SELESAI**

### Final Checklist D1

Sebelum menganggap module baru selesai:

| # | Category | Items |
|---|----------|-------|
| ☐ | Planning | Module boundaries defined, dependencies identified |
| ☐ | Database | Schema created, migrations ready, base models defined |
| ☐ | Backend | Core structure setup, config, exceptions, health check |
| ☐ | RBAC | Permissions defined, roles created, seeder ready |
| ☐ | Frontend | Project setup, theme configured, routes defined |
| ☐ | Events | Event schemas defined, publisher/consumer ready |
| ☐ | Testing | Test infrastructure ready, factories created |
| ☐ | Documentation | All docs created, DVL validated |
| ☐ | Deployment | Docker files ready, CI/CD configured |

---

## FLOW D2: ADD FEATURE TO MODULE

**Kapan menggunakan flow ini:**
- Menambahkan fitur baru ke module yang sudah ada
- Feature adalah unit fungsional dalam module
- Feature bisa simple (CRUD) atau complex (workflow)

**Acuan Utama:**
- Module-specific documentation di `/modules/{module}/docs/`
- [MODULE_ARCHITECTURE.md](./MODULE_ARCHITECTURE.md) - Feature structure
- Existing module patterns

---

### PRE-REQUISITE CHECK D2

Sebelum menambah feature:

| # | Item | Status |
|---|------|--------|
| ☐ | Module sudah ada dan operational | |
| ☐ | Feature requirements jelas | |
| ☐ | Feature tidak duplikasi dengan yang sudah ada | |
| ☐ | Integration points dengan features lain teridentifikasi | |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D2.1](#step-d21-feature-analysis)

---

### STEP D2.1: Feature Analysis

📋 **Konteks:**
Menganalisis feature yang akan ditambahkan.

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Feature type identified (CRUD, Report, Search, etc.) | |
| ☐ | Required atomic flows identified | See Flow C1-C5 |
| ☐ | Database changes identified | |
| ☐ | New permissions needed | |
| ☐ | Events to publish/consume | |

**Feature Type Decision Tree:**

```
Feature Analysis:
├── Involves data management (create, read, update, delete)?
│   └── YES → Use FLOW C1 (CRUD Feature)
├── Involves generating reports/exports?
│   └── YES → Use FLOW C2 (Report Feature)
├── Involves search functionality?
│   └── YES → Use FLOW C3 (Search Feature)
├── Involves notifications (email, push, in-app)?
│   └── YES → Use FLOW C4 (Notification Feature)
├── Involves file handling?
│   └── YES → Use FLOW C5 (File Upload Feature)
└── Complex workflow with multiple states?
    └── YES → Combine multiple flows + State Machine (Standard #28)
```

➡️ **Selanjutnya:**
- CRUD feature → Use [Flow C1](#flow-c1-create-crud-feature)
- Report feature → Use [Flow C2](#flow-c2-create-report-feature)
- Search feature → Use [Flow C3](#flow-c3-create-search-feature)
- Notification feature → Use [Flow C4](#flow-c4-create-notification-feature)
- File upload feature → Use [Flow C5](#flow-c5-create-file-upload-feature)
- Complex feature → Lanjut ke [STEP D2.2](#step-d22-complex-feature-planning)

---

### STEP D2.2: Complex Feature Planning

📋 **Konteks:**
Planning untuk feature yang kompleks (kombinasi multiple flows).

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Break down ke atomic flows | |
| ☐ | Determine execution order | |
| ☐ | Identify shared components | |
| ☐ | State machine design (if workflow) | Standard #28 |

**Complex Feature Example - Reservation:**

```
Reservation Feature Breakdown:
1. FLOW A1: Database Model (Reservation, Guest, Room)
2. FLOW A2: API Endpoints (CRUD + status changes)
3. FLOW A3: Business Logic (availability check, pricing)
4. FLOW A5: Events (reservation.created, reservation.confirmed)
5. FLOW B2: Pages (list, detail, form)
6. FLOW B3: Forms (create/edit reservation)
7. FLOW C4: Notifications (confirmation email)

State Machine:
draft → pending → confirmed → checked_in → checked_out
                ↘ cancelled
```

➡️ **Selanjutnya:**
- Execute identified flows sequentially
- After all flows complete → [STEP D2.3](#step-d23-feature-integration)

---

### STEP D2.3: Feature Integration

📋 **Konteks:**
Mengintegrasikan feature baru dengan module.

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Feature routes added to module router | |
| ☐ | Feature navigation added to sidebar | |
| ☐ | Feature permissions registered | |
| ☐ | Feature events integrated with module events | |
| ☐ | Feature documentation updated | |

**Add Feature to Module Router:**

```python
# modules/{module}/backend/app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.endpoints import (
    # existing...
    new_feature,  # Add new feature
)

api_router = APIRouter()

# Existing routes...
api_router.include_router(
    new_feature.router,
    prefix="/new-feature",
    tags=["new-feature"]
)
```

**Add Feature Navigation:**

```typescript
// modules/{module}/frontend/src/config/navigation.ts
export const moduleNavigation = [
  // existing...
  {
    name: 'New Feature',
    href: '/new-feature',
    icon: IconNewFeature,
    permission: '{module}.new_feature.view',
  },
];
```

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP D2.4](#step-d24-testing--documentation)

---

### STEP D2.4: Testing & Documentation

📋 **Konteks:**
Testing dan dokumentasi feature baru.

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Unit tests untuk feature | Standard #9 |
| ☐ | Integration tests untuk feature | |
| ☐ | API documentation updated | |
| ☐ | Module README updated | |
| ☐ | CHANGELOG updated | |

➡️ **Selanjutnya:**
- Semua ✓ → ✅ **FLOW D2 SELESAI**

---

## E. MAINTENANCE FLOWS

---

## FLOW E1: BUG FIX

**Kapan menggunakan flow ini:**
- Memperbaiki bug di existing code
- Bug fix harus tidak mengubah behavior yang benar
- Regression test wajib ditambahkan

**Acuan Utama:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Regression testing
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #7 (Error Handling)

---

### PRE-REQUISITE CHECK E1

| # | Item | Status |
|---|------|--------|
| ☐ | Bug sudah di-reproduce | |
| ☐ | Root cause sudah diidentifikasi | |
| ☐ | Scope impact sudah dianalisis | |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP E1.1](#step-e11-bug-reproduction)

---

### STEP E1.1: Bug Reproduction

📋 **Konteks:**
Reproduce bug dan document steps.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Steps to reproduce documented |
| ☐ | Expected behavior documented |
| ☐ | Actual behavior documented |
| ☐ | Environment details captured |
| ☐ | Screenshot/logs attached (jika applicable) |

**Bug Report Template:**

```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Module: {module}
- Version: x.x.x
- Browser: (if frontend)
- OS:

## Logs/Screenshots
[Attach relevant logs or screenshots]
```

➡️ **Selanjutnya:**
- Bug reproducible → Lanjut ke [STEP E1.2](#step-e12-root-cause-analysis)

---

### STEP E1.2: Root Cause Analysis

📋 **Konteks:**
Analisis akar masalah bug.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Root cause identified |
| ☐ | Affected code located |
| ☐ | Impact on other parts analyzed |
| ☐ | Fix approach determined |

**Root Cause Analysis Template:**

```markdown
## Root Cause
{Explain why the bug occurs}

## Affected Files
- `path/to/file1.py` - Line X
- `path/to/file2.tsx` - Component Y

## Impact Analysis
- Direct impact: {what's broken}
- Indirect impact: {what else might be affected}
- Data impact: {any data corruption risk}

## Fix Approach
{Describe the proposed fix}
```

➡️ **Selanjutnya:**
- Root cause found → Lanjut ke [STEP E1.3](#step-e13-write-failing-test)

---

### STEP E1.3: Write Failing Test

📋 **Konteks:**
Tulis test yang gagal karena bug (TDD approach).

📚 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Test patterns
- [DEVELOPMENT_STANDARDS_V2.md](./DEVELOPMENT_STANDARDS_V2.md) - Standard #9

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Test yang mereproduksi bug ditulis |
| ☐ | Test GAGAL dengan bug yang ada |
| ☐ | Test name descriptive (test_should_xxx_when_yyy) |

**Regression Test Example:**

```python
# tests/regression/test_bug_xxx.py
"""
Regression test for Bug #XXX
Issue: [link to issue]
Root cause: [brief description]
"""
import pytest

class TestBugXXX:
    """Regression tests for Bug #XXX"""

    def test_should_not_fail_when_input_is_empty(self, db_session):
        """
        Bug #XXX: System crashes when input is empty
        Expected: Should return empty result, not crash
        """
        # Arrange
        service = SomeService(db_session)

        # Act & Assert - This should NOT raise
        result = service.process(input=[])
        assert result == []
```

➡️ **Selanjutnya:**
- Test gagal → Lanjut ke [STEP E1.4](#step-e14-implement-fix)

---

### STEP E1.4: Implement Fix

📋 **Konteks:**
Implement fix untuk bug.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Fix implemented dengan minimal changes |
| ☐ | Tidak ada perubahan behavior lain |
| ☐ | Error handling proper | Standard #7 |
| ☐ | Logging ditambahkan jika perlu | Standard #15 |

**Fix Guidelines:**

```markdown
## Fix Guidelines
1. MINIMAL CHANGES - Only fix the bug, don't refactor
2. NO BEHAVIOR CHANGES - Don't change working behavior
3. DEFENSIVE CODING - Add guards to prevent recurrence
4. LOGGING - Add debug logs for future diagnosis
```

➡️ **Selanjutnya:**
- Fix implemented → Lanjut ke [STEP E1.5](#step-e15-verify-fix)

---

### STEP E1.5: Verify Fix

📋 **Konteks:**
Verify fix dengan menjalankan tests.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Regression test sekarang PASS |
| ☐ | Existing tests masih PASS |
| ☐ | Manual testing passed |
| ☐ | No new issues introduced |

➡️ **Selanjutnya:**
- All tests pass → ✅ **FLOW E1 SELESAI**

---

## FLOW E2: REFACTORING

**Kapan menggunakan flow ini:**
- Memperbaiki code quality tanpa mengubah behavior
- Mengurangi technical debt
- Meningkatkan maintainability

**Acuan Utama:**
- [DEVELOPMENT_STANDARDS_V2.md](./DEVELOPMENT_STANDARDS_V2.md) - Standard #10 (Code Structure)
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Test coverage

---

### PRE-REQUISITE CHECK E2

| # | Item | Status |
|---|------|--------|
| ☐ | Test coverage sudah cukup untuk refactor | |
| ☐ | Scope refactoring sudah jelas | |
| ☐ | Tidak ada deadline yang mendesak | |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP E2.1](#step-e21-code-analysis)

---

### STEP E2.1: Code Analysis

📋 **Konteks:**
Analisis code yang akan di-refactor.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Code smells identified |
| ☐ | Current test coverage checked |
| ☐ | Dependencies mapped |
| ☐ | Refactoring goals defined |

**Code Smell Checklist:**

```markdown
## Common Code Smells
- [ ] Long methods (> 20 lines)
- [ ] Large classes (> 200 lines)
- [ ] Deep nesting (> 3 levels)
- [ ] Duplicate code
- [ ] God classes (too many responsibilities)
- [ ] Feature envy (class using other class's data extensively)
- [ ] Primitive obsession (using primitives instead of objects)
- [ ] Long parameter lists (> 4 parameters)
```

➡️ **Selanjutnya:**
- Analysis complete → Lanjut ke [STEP E2.2](#step-e22-add-test-coverage)

---

### STEP E2.2: Add Test Coverage

📋 **Konteks:**
Pastikan test coverage cukup sebelum refactor.

📚 **Acuan:**
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Coverage requirements

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Current coverage measured |
| ☐ | Critical paths have tests |
| ☐ | Edge cases covered |
| ☐ | All tests PASS before refactor |

**Coverage Check:**

```bash
# Backend
pytest --cov=app --cov-report=html

# Frontend
bun test --coverage
```

➡️ **Selanjutnya:**
- Coverage sufficient → Lanjut ke [STEP E2.3](#step-e23-refactor-incrementally)

---

### STEP E2.3: Refactor Incrementally

📋 **Konteks:**
Refactor dalam small, safe steps.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Small, atomic changes |
| ☐ | Run tests after each change |
| ☐ | Commit setelah setiap step |
| ☐ | Tidak mengubah behavior |

**Refactoring Steps:**

```markdown
## Safe Refactoring Steps
1. Extract Method - Break large methods into smaller ones
2. Extract Class - Split god classes
3. Rename - Improve naming for clarity
4. Move - Relocate code to appropriate place
5. Inline - Remove unnecessary indirection
6. Replace Conditionals - Use polymorphism
```

➡️ **Selanjutnya:**
- Refactoring done → Lanjut ke [STEP E2.4](#step-e24-final-verification)

---

### STEP E2.4: Final Verification

📋 **Konteks:**
Verify refactoring tidak break anything.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | All tests still PASS |
| ☐ | Coverage tidak menurun |
| ☐ | Code quality metrics improved |
| ☐ | Manual testing passed |

➡️ **Selanjutnya:**
- All verified → ✅ **FLOW E2 SELESAI**

---

## FLOW E3: PERFORMANCE OPTIMIZATION

**Kapan menggunakan flow ini:**
- Response time melebihi SLA
- Database queries slow
- Memory usage tinggi
- Frontend rendering lambat

**Acuan Utama:**
- [DEVELOPMENT_STANDARDS_V5.md](./DEVELOPMENT_STANDARDS_V5.md) - Standard #26 (Performance SLA)
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #5 (Caching)
- [DEVELOPMENT_STANDARDS_V4.md](./DEVELOPMENT_STANDARDS_V4.md) - Standard #22 (Search)

---

### PRE-REQUISITE CHECK E3

| # | Item | Status |
|---|------|--------|
| ☐ | Performance issue sudah di-profile | |
| ☐ | Baseline metrics sudah ada | |
| ☐ | Target improvement sudah ditentukan | |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP E3.1](#step-e31-performance-profiling)

---

### STEP E3.1: Performance Profiling

📋 **Konteks:**
Profile aplikasi untuk identify bottlenecks.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS_V5.md](./DEVELOPMENT_STANDARDS_V5.md) - Standard #26

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Backend profiling done (cProfile, py-spy) |
| ☐ | Database queries analyzed (EXPLAIN ANALYZE) |
| ☐ | Frontend profiling done (React DevTools, Lighthouse) |
| ☐ | Network requests analyzed |
| ☐ | Bottlenecks identified |

**Backend Profiling:**

```python
# Using py-spy for live profiling
# py-spy record -o profile.svg --pid <PID>

# Using cProfile in code
import cProfile
import pstats

def profile_function(func):
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        return result
    return wrapper
```

**Database Query Analysis:**

```sql
-- Analyze slow queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM reservations
WHERE tenant_id = 'xxx' AND status = 'confirmed';

-- Check missing indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

**Frontend Profiling:**

```typescript
// React DevTools Profiler
// Record component render times

// Lighthouse CLI
// npx lighthouse http://localhost:3000 --view

// Bundle analysis
// npx vite-bundle-visualizer
```

➡️ **Selanjutnya:**
- Bottlenecks identified → Lanjut ke [STEP E3.2](#step-e32-optimization-strategy)

---

### STEP E3.2: Optimization Strategy

📋 **Konteks:**
Tentukan strategi optimization berdasarkan bottleneck.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Optimization strategy selected |
| ☐ | Expected improvement estimated |
| ☐ | Risk assessment done |
| ☐ | Rollback plan ready |

**Optimization Decision Tree:**

```
Bottleneck Type:
├── Database Query Slow
│   ├── Missing index → Add index
│   ├── N+1 query → Use eager loading
│   ├── Large result set → Add pagination
│   └── Complex joins → Consider denormalization or caching
│
├── API Response Slow
│   ├── Heavy computation → Add caching (Standard #5)
│   ├── External API calls → Add circuit breaker, cache responses
│   └── Large payload → Add pagination, compression
│
├── Frontend Slow
│   ├── Large bundle → Code splitting, lazy loading
│   ├── Too many re-renders → Memoization, React.memo
│   ├── Heavy computation → useMemo, web workers
│   └── Large lists → Virtualization
│
└── Memory Issues
    ├── Memory leak → Profile and fix
    └── Large data → Streaming, pagination
```

➡️ **Selanjutnya:**
- Strategy selected → Lanjut ke [STEP E3.3](#step-e33-implement-optimization)

---

### STEP E3.3: Implement Optimization

📋 **Konteks:**
Implement optimization sesuai strategy.

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Database indexes added (jika perlu) | Standard #2 |
| ☐ | Caching implemented (jika perlu) | Standard #5 |
| ☐ | Query optimized (jika perlu) | |
| ☐ | Frontend optimized (jika perlu) | Standard #11 |

**Common Optimizations:**

```python
# 1. Add Database Index
# migrations/versions/xxx_add_index.py
def upgrade():
    op.create_index(
        'ix_reservations_tenant_status',
        'reservations',
        ['tenant_id', 'status']
    )

# 2. Add Caching
from app.core.cache import cache

@cache.cached(ttl=300, key="reservation:{id}")
async def get_reservation(id: UUID) -> Reservation:
    return await repository.get(id)

# 3. Optimize Query with Eager Loading
async def get_reservations_with_guests(tenant_id: UUID):
    return await db.execute(
        select(Reservation)
        .options(selectinload(Reservation.guest))
        .where(Reservation.tenant_id == tenant_id)
    )
```

```typescript
// 4. Frontend Code Splitting
const HeavyComponent = lazy(() => import('./HeavyComponent'));

// 5. Memoization
const MemoizedList = memo(function ExpensiveList({ items }) {
  return items.map(item => <Item key={item.id} {...item} />);
});

// 6. Virtual List
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }) {
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map(virtualItem => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

➡️ **Selanjutnya:**
- Optimization done → Lanjut ke [STEP E3.4](#step-e34-measure-improvement)

---

### STEP E3.4: Measure Improvement

📋 **Konteks:**
Measure improvement dan verify SLA met.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS_V5.md](./DEVELOPMENT_STANDARDS_V5.md) - Standard #26 (Performance SLA)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | New metrics measured |
| ☐ | Improvement calculated |
| ☐ | SLA requirements met |
| ☐ | No regression in other areas |

**Performance SLA Targets:**

```markdown
## Performance SLA (Standard #26)
| Metric | Target | Measured |
|--------|--------|----------|
| API response (p95) | < 200ms | ___ ms |
| Database query (p95) | < 50ms | ___ ms |
| Page load (LCP) | < 2.5s | ___ s |
| Time to Interactive | < 3.8s | ___ s |
```

➡️ **Selanjutnya:**
- SLA met → ✅ **FLOW E3 SELESAI**
- SLA not met → Kembali ke [STEP E3.1](#step-e31-performance-profiling)

---

## FLOW E4: SECURITY FIX

**Kapan menggunakan flow ini:**
- Vulnerability ditemukan
- Security audit finding
- Dependency dengan CVE
- Authentication/authorization bug

**Acuan Utama:**
- [SECURITY_AUTH_REQUIREMENTS.md](./SECURITY_AUTH_REQUIREMENTS.md) - Security requirements
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #7 (Error Handling)
- [DEVELOPMENT_STANDARDS_V11.md](./DEVELOPMENT_STANDARDS_V11.md) - Standard #41 (Secrets)

---

### PRE-REQUISITE CHECK E4

| # | Item | Status |
|---|------|--------|
| ☐ | Vulnerability sudah di-verify | |
| ☐ | Severity sudah di-assess (Critical/High/Medium/Low) | |
| ☐ | Attack vector sudah dipahami | |
| ☐ | Affected scope sudah diidentifikasi | |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP E4.1](#step-e41-vulnerability-assessment)

---

### STEP E4.1: Vulnerability Assessment

📋 **Konteks:**
Assess vulnerability severity dan impact.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | CVSS score calculated (jika applicable) |
| ☐ | Attack complexity assessed |
| ☐ | Privileges required assessed |
| ☐ | User interaction required? |
| ☐ | Potential impact (CIA triad) |

**Security Assessment Template:**

```markdown
## Vulnerability Assessment

### Classification
- **Type**: [SQL Injection / XSS / CSRF / Auth Bypass / etc.]
- **Severity**: [Critical / High / Medium / Low]
- **CVSS Score**: X.X (if applicable)

### Attack Vector
- **Complexity**: [Low / High]
- **Privileges Required**: [None / Low / High]
- **User Interaction**: [None / Required]

### Impact
- **Confidentiality**: [None / Low / High]
- **Integrity**: [None / Low / High]
- **Availability**: [None / Low / High]

### Affected Components
- File: path/to/file.py
- Function: vulnerable_function()
- Endpoint: POST /api/v1/resource

### Exploitation Scenario
[Describe how an attacker could exploit this]
```

➡️ **Selanjutnya:**
- Assessment complete → Lanjut ke [STEP E4.2](#step-e42-implement-fix)

---

### STEP E4.2: Implement Fix

📋 **Konteks:**
Implement security fix dengan proper patterns.

📚 **Acuan:**
- [SECURITY_AUTH_REQUIREMENTS.md](./SECURITY_AUTH_REQUIREMENTS.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item | Referensi |
|---|------|-----------|
| ☐ | Fix mengikuti security best practices | OWASP Guidelines |
| ☐ | Input validation ditambahkan | Standard #8 |
| ☐ | Output encoding proper | |
| ☐ | Authentication/authorization proper | Standard #3 |
| ☐ | Secrets tidak hardcoded | Standard #41 |

**Common Security Fixes:**

```python
# 1. SQL Injection Prevention
# BAD
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD - Use parameterized queries
from sqlalchemy import select
result = await db.execute(
    select(User).where(User.id == user_id)
)

# 2. XSS Prevention (Backend)
from markupsafe import escape

def safe_output(user_input: str) -> str:
    return escape(user_input)

# 3. CSRF Protection
from fastapi_csrf_protect import CsrfProtect

@router.post("/action")
async def action(csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf()
    ...

# 4. Rate Limiting (Standard #30)
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login():
    ...

# 5. Secure Password Handling
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

```typescript
// Frontend XSS Prevention
// 1. React auto-escapes by default - DON'T use dangerouslySetInnerHTML

// 2. If must render HTML, sanitize first
import DOMPurify from 'dompurify';

function SafeHTML({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}

// 3. Validate URLs before using
function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}
```

➡️ **Selanjutnya:**
- Fix implemented → Lanjut ke [STEP E4.3](#step-e43-security-testing)

---

### STEP E4.3: Security Testing

📋 **Konteks:**
Test fix untuk memastikan vulnerability fixed.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Exploit attempt fails after fix |
| ☐ | Regression tests added |
| ☐ | Security scanner passes |
| ☐ | Penetration test (jika applicable) |

**Security Test Example:**

```python
# tests/security/test_sql_injection.py
import pytest

class TestSQLInjection:
    """Test SQL injection prevention"""

    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE users; --",
        "1 OR 1=1",
        "1; SELECT * FROM users",
        "1 UNION SELECT * FROM passwords",
    ])
    async def test_sql_injection_prevented(
        self,
        client,
        malicious_input
    ):
        """Ensure SQL injection attempts are blocked"""
        response = await client.get(
            f"/api/v1/users/{malicious_input}"
        )

        # Should return 400 or 404, not 500 (SQL error)
        assert response.status_code in [400, 404, 422]

        # Verify database intact
        users = await User.count()
        assert users > 0  # Table still exists
```

➡️ **Selanjutnya:**
- Tests pass → Lanjut ke [STEP E4.4](#step-e44-post-fix-actions)

---

### STEP E4.4: Post-Fix Actions

📋 **Konteks:**
Actions setelah security fix deployed.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Hotfix deployed ke production |
| ☐ | Affected users notified (jika perlu) |
| ☐ | Incident report created |
| ☐ | Security audit log updated |
| ☐ | Similar patterns checked in codebase |

**Incident Report Template:**

```markdown
## Security Incident Report

### Summary
- **Date Discovered**: YYYY-MM-DD
- **Date Fixed**: YYYY-MM-DD
- **Severity**: Critical/High/Medium/Low
- **Status**: Resolved

### Description
[Brief description of the vulnerability]

### Impact
- **Data Affected**: [None/Limited/Extensive]
- **Users Affected**: [Number or scope]
- **Systems Affected**: [List of systems]

### Timeline
- YYYY-MM-DD HH:MM - Vulnerability discovered
- YYYY-MM-DD HH:MM - Investigation started
- YYYY-MM-DD HH:MM - Fix developed
- YYYY-MM-DD HH:MM - Fix deployed
- YYYY-MM-DD HH:MM - Verified in production

### Root Cause
[Explain why this happened]

### Fix Applied
[Describe the fix]

### Preventive Measures
[What will prevent this in the future]
```

➡️ **Selanjutnya:**
- All complete → ✅ **FLOW E4 SELESAI**

---

## F. DOCUMENTATION FLOWS

---

## FLOW F1: UPDATE MODULE DOCUMENTATION

**Kapan menggunakan flow ini:**
- Setelah menambah feature baru
- Setelah major refactoring
- Setelah architecture changes
- Periodic documentation review

**Acuan Utama:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)
- Module-specific docs di `/modules/{module}/docs/`

---

### PRE-REQUISITE CHECK F1

| # | Item | Status |
|---|------|--------|
| ☐ | Changes yang perlu didokumentasikan sudah jelas | |
| ☐ | Existing documentation sudah direview | |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP F1.1](#step-f11-documentation-audit)

---

### STEP F1.1: Documentation Audit

📋 **Konteks:**
Audit existing documentation untuk identify gaps.

📚 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | README.md up to date |
| ☐ | ARCHITECTURE.md reflects current design |
| ☐ | API.md has all endpoints |
| ☐ | DATABASE.md has all tables/relationships |
| ☐ | CHANGELOG.md has recent changes |

**Documentation Audit Checklist:**

```markdown
## Documentation Audit

### README.md
- [ ] Overview accurate
- [ ] Quick start works
- [ ] Feature list complete
- [ ] Dependencies listed

### ARCHITECTURE.md
- [ ] System diagram current
- [ ] Component descriptions accurate
- [ ] Design decisions documented
- [ ] Integration points listed

### API.md
- [ ] All endpoints documented
- [ ] Request/response examples current
- [ ] Error codes listed
- [ ] Authentication requirements clear

### DATABASE.md
- [ ] All tables documented
- [ ] Relationships accurate
- [ ] Indexes listed
- [ ] Migration notes current

### CHANGELOG.md
- [ ] Recent changes listed
- [ ] Version numbers correct
- [ ] Breaking changes highlighted
```

➡️ **Selanjutnya:**
- Audit complete → Lanjut ke [STEP F1.2](#step-f12-update-documentation)

---

### STEP F1.2: Update Documentation

📋 **Konteks:**
Update documentation berdasarkan audit.

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Gaps filled |
| ☐ | Outdated info updated |
| ☐ | Code examples verified |
| ☐ | Links verified |

**Documentation Update Guidelines:**

```markdown
## Update Guidelines

1. **Be Concise**: Write clearly and briefly
2. **Use Examples**: Include code examples
3. **Keep Current**: Update with every change
4. **Link Related**: Cross-reference related docs
5. **Version Info**: Include version compatibility
```

➡️ **Selanjutnya:**
- Updates done → Lanjut ke [STEP F1.3](#step-f13-dvl-validation)

---

### STEP F1.3: DVL Validation

📋 **Konteks:**
Validate documentation dengan DVL tool.

📚 **Acuan:**
- [MODULE_DOCUMENTATION_STANDARD.md](./MODULE_DOCUMENTATION_STANDARD.md) - DVL Tool

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | DVL lint passed |
| ☐ | All required sections present |
| ☐ | Links valid |
| ☐ | Code examples compile/run |

**DVL Validation:**

```bash
# Run DVL validation
dvl lint modules/{module}/docs/

# Expected output:
# ✓ README.md - All checks passed
# ✓ ARCHITECTURE.md - All checks passed
# ✓ API.md - All checks passed
# ✓ DATABASE.md - All checks passed
# ✓ CHANGELOG.md - All checks passed
```

➡️ **Selanjutnya:**
- DVL passed → ✅ **FLOW F1 SELESAI**

---

## FLOW F2: UPDATE API DOCUMENTATION

**Kapan menggunakan flow ini:**
- Setelah menambah/mengubah API endpoint
- Breaking API changes
- New API version release

**Acuan Utama:**
- [API_CONTRACTS_PLATFORM.md](./API_CONTRACTS_PLATFORM.md)
- [DEVELOPMENT_STANDARDS_V5.md](./DEVELOPMENT_STANDARDS_V5.md) - Standard #24 (API Versioning)
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #6 (API Patterns)

---

### PRE-REQUISITE CHECK F2

| # | Item | Status |
|---|------|--------|
| ☐ | API changes sudah diimplementasikan | |
| ☐ | OpenAPI spec sudah di-generate | |

➡️ **Selanjutnya:**
- Semua ✓ → Lanjut ke [STEP F2.1](#step-f21-openapi-spec-update)

---

### STEP F2.1: OpenAPI Spec Update

📋 **Konteks:**
Update OpenAPI specification.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS.md](./DEVELOPMENT_STANDARDS.md) - Standard #6

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | OpenAPI spec generated/updated |
| ☐ | All endpoints documented |
| ☐ | Request/response schemas accurate |
| ☐ | Authentication requirements documented |
| ☐ | Error responses documented |

**OpenAPI Generation:**

```python
# FastAPI auto-generates OpenAPI
# Access at: http://localhost:8000/openapi.json

# For custom documentation
from fastapi import FastAPI

app = FastAPI(
    title="{Module} API",
    description="API for {module} module",
    version="1.0.0",
    openapi_tags=[
        {"name": "resources", "description": "Resource operations"},
    ]
)

# Endpoint documentation
@router.post(
    "/resources",
    response_model=ResourceResponse,
    responses={
        201: {"description": "Resource created"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
    },
    summary="Create a new resource",
    description="Creates a new resource with the provided data."
)
async def create_resource(
    data: ResourceCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new resource.

    - **name**: Resource name (required)
    - **description**: Resource description (optional)
    """
    ...
```

➡️ **Selanjutnya:**
- OpenAPI updated → Lanjut ke [STEP F2.2](#step-f22-api-documentation-update)

---

### STEP F2.2: API Documentation Update

📋 **Konteks:**
Update API documentation files.

📚 **Acuan:**
- [API_CONTRACTS_PLATFORM.md](./API_CONTRACTS_PLATFORM.md)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | Module API.md updated |
| ☐ | Platform API contracts updated (jika shared) |
| ☐ | Breaking changes documented |
| ☐ | Migration guide (jika breaking) |

**API Documentation Template:**

```markdown
## Endpoint: POST /api/v1/resources

### Description
Creates a new resource.

### Authentication
Required. Bearer token in Authorization header.

### Permissions
- `module.resource.create`

### Request

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer {token} |
| X-Tenant-ID | Yes | Tenant UUID |
| X-Request-ID | No | Request tracking ID |

**Body:**
\`\`\`json
{
  "name": "string",
  "description": "string | null"
}
\`\`\`

### Response

**201 Created:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "string",
    "description": "string | null",
    "created_at": "datetime"
  }
}
\`\`\`

**400 Bad Request:**
\`\`\`json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "errors": [...]
    }
  }
}
\`\`\`
```

➡️ **Selanjutnya:**
- Documentation updated → Lanjut ke [STEP F2.3](#step-f23-changelog-update)

---

### STEP F2.3: Changelog Update

📋 **Konteks:**
Update changelog untuk API changes.

📚 **Acuan:**
- [DEVELOPMENT_STANDARDS_V5.md](./DEVELOPMENT_STANDARDS_V5.md) - Standard #24 (API Versioning)

☑️ **Checklist:** `[WAJIB]`

| # | Item |
|---|------|
| ☐ | CHANGELOG.md updated |
| ☐ | Version number correct |
| ☐ | Breaking changes clearly marked |
| ☐ | Deprecations noted |

**Changelog Entry Template:**

```markdown
## [1.2.0] - 2024-01-15

### Added
- `POST /api/v1/resources` - Create resource endpoint
- `GET /api/v1/resources/{id}` - Get resource by ID

### Changed
- `GET /api/v1/resources` - Added pagination support

### Deprecated
- `GET /api/v1/resources/all` - Use paginated endpoint instead

### Breaking Changes
- `POST /api/v1/resources` now requires `tenant_id` in body

### Migration Guide
To migrate from 1.1.x to 1.2.0:
1. Update all calls to include `tenant_id`
2. Update to use paginated list endpoint
```

➡️ **Selanjutnya:**
- Changelog updated → ✅ **FLOW F2 SELESAI**

---

**PART 5 SELESAI**

Flow yang sudah dibuat:
- ✅ A1-A6: Backend Flows
- ✅ B1-B5: Frontend Flows
- ✅ C1-C5: Full Feature Flows
- ✅ D1: Create New Module
- ✅ D2: Add Feature to Module
- ✅ E1: Bug Fix
- ✅ E2: Refactoring
- ✅ E3: Performance Optimization
- ✅ E4: Security Fix
- ✅ F1: Update Module Documentation
- ✅ F2: Update API Documentation

Flow yang akan dibuat di Part 6 (Final):
- G1: Quick Reference / Cheat Sheet
- G2: Flow Decision Tree (Master Navigation)
- Appendix: Standards Quick Reference

---

# PART 6: QUICK REFERENCE & APPENDIX (FINAL)

---

## G. QUICK REFERENCE

---

## G1: FLOW QUICK REFERENCE (CHEAT SHEET)

### Backend Flows Summary

| Flow | Kapan Digunakan | Key Standards | Output |
|------|-----------------|---------------|--------|
| **A1** | Membuat table/model baru | #2 Database, #29 Multi-tenancy | Migration + Model |
| **A2** | Membuat API endpoint | #6 API, #8 Validation | Router + Schema |
| **A3** | Membuat business logic | #10 Code Structure | Service class |
| **A4** | Membuat background job | #21 Celery | Celery task |
| **A5** | Membuat event/message | #18 Events | Publisher + Consumer |
| **A6** | Integrasi external service | #37 Circuit Breaker | Integration client |

### Frontend Flows Summary

| Flow | Kapan Digunakan | Key Standards | Output |
|------|-----------------|---------------|--------|
| **B1** | Membuat UI component | #11 Frontend | Component + Test |
| **B2** | Membuat halaman | #11 Frontend | Page + Route |
| **B3** | Membuat form | #8 Validation | Form component |
| **B4** | Membuat data table | #11 Frontend | Table component |
| **B5** | Membuat real-time feature | #20 WebSocket | Real-time hook |

### Full Feature Flows Summary

| Flow | Kapan Digunakan | Combines Flows | Output |
|------|-----------------|----------------|--------|
| **C1** | CRUD feature | A1, A2, A3, B2, B3, B4 | Complete CRUD |
| **C2** | Report/export feature | A3, A4, B2 | Report system |
| **C3** | Search feature | A3, #22 Search | Search system |
| **C4** | Notification feature | A5, #23 Notification | Notification system |
| **C5** | File upload feature | A2, A3, #19 Files | Upload system |

### Module & Maintenance Flows Summary

| Flow | Kapan Digunakan | Key Focus | Output |
|------|-----------------|-----------|--------|
| **D1** | Membuat module baru | Module structure | Complete module |
| **D2** | Menambah feature ke module | Feature analysis | New feature |
| **E1** | Bug fix | Regression testing | Fix + test |
| **E2** | Refactoring | Test coverage | Cleaner code |
| **E3** | Performance optimization | SLA metrics | Faster code |
| **E4** | Security fix | OWASP, CVE | Secure code |
| **F1** | Update module docs | DVL validation | Updated docs |
| **F2** | Update API docs | OpenAPI | Updated API docs |

---

### Quick Command Reference

**Backend Commands:**

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Run migration
alembic upgrade head

# Run tests
pytest tests/ -v --cov=app

# Run specific test
pytest tests/unit/test_service.py -v

# Start dev server
uvicorn app.main:app --reload

# Start Celery worker
celery -A app.jobs.celery worker -l info

# Start Celery beat
celery -A app.jobs.celery beat -l info
```

**Frontend Commands:**

```bash
# Install dependencies
bun install

# Start dev server
bun dev

# Run tests
bun test

# Run tests with coverage
bun test --coverage

# Build for production
bun run build

# Type check
bun run typecheck

# Lint
bun run lint
```

**Docker Commands:**

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend

# Rebuild specific service
docker compose build backend

# Stop all services
docker compose down
```

---

### File Naming Quick Reference

**Backend:**
```
app/
├── models/
│   └── {entity}.py              # e.g., reservation.py
├── schemas/
│   └── {entity}.py              # e.g., reservation.py
├── services/
│   └── {entity}_service.py      # e.g., reservation_service.py
├── repositories/
│   └── {entity}_repository.py   # e.g., reservation_repository.py
├── api/v1/endpoints/
│   └── {entity}.py              # e.g., reservation.py
├── jobs/
│   └── {action}_{entity}.py     # e.g., sync_reservation.py
└── events/
    ├── publishers/
    │   └── {entity}_publisher.py
    └── consumers/
        └── {event_type}_consumer.py
```

**Frontend:**
```
src/
├── components/
│   └── {ComponentName}/
│       ├── {ComponentName}.tsx
│       ├── {ComponentName}.test.tsx
│       └── index.ts
├── pages/
│   └── {PageName}/
│       ├── {PageName}Page.tsx
│       └── index.ts
├── hooks/
│   └── use{HookName}.ts         # e.g., useReservations.ts
├── services/
│   └── {entity}.service.ts      # e.g., reservation.service.ts
└── types/
    └── {entity}.types.ts        # e.g., reservation.types.ts
```

---

### Validation Quick Reference

**Backend (Pydantic):**

```python
from pydantic import BaseModel, Field, validator
from datetime import date
from uuid import UUID

class EntityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., regex=r'^[A-Z]{3}-\d{3}$')
    amount: Decimal = Field(..., ge=0, le=999999.99)
    email: EmailStr
    date: date
    status: Literal["active", "inactive"]

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    class Config:
        str_strip_whitespace = True
```

**Frontend (Zod):**

```typescript
import { z } from 'zod';

export const entitySchema = z.object({
  name: z.string().min(1, 'Required').max(100),
  code: z.string().regex(/^[A-Z]{3}-\d{3}$/, 'Format: ABC-123'),
  amount: z.number().min(0).max(999999.99),
  email: z.string().email('Invalid email'),
  date: z.date(),
  status: z.enum(['active', 'inactive']),
});

export type EntityFormData = z.infer<typeof entitySchema>;
```

---

### API Response Format Quick Reference

**Success Response:**

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

**Error Response:**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "errors": [
        {
          "field": "email",
          "message": "Invalid email format"
        }
      ]
    }
  }
}
```

**Common Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Input validation failed |
| UNAUTHORIZED | 401 | Not authenticated |
| PERMISSION_DENIED | 403 | Not authorized |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

---

## G2: FLOW DECISION TREE (MASTER NAVIGATION)

### Starting Point: What Do You Want to Do?

```
┌─────────────────────────────────────────────────────────────┐
│                    WHAT DO YOU WANT TO DO?                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ CREATE        │    │ MAINTAIN      │    │ DOCUMENT      │
│ something new │    │ existing code │    │ the system    │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
   Go to A              Go to B               Go to C
```

---

### A. CREATE Something New

```
CREATE something new
        │
        ├── Creating a new MODULE?
        │   └── YES → FLOW D1: Create New Module
        │
        ├── Adding FEATURE to existing module?
        │   └── YES → FLOW D2: Add Feature to Module
        │       │
        │       └── What type of feature?
        │           ├── CRUD operations → FLOW C1
        │           ├── Reports/exports → FLOW C2
        │           ├── Search → FLOW C3
        │           ├── Notifications → FLOW C4
        │           └── File uploads → FLOW C5
        │
        ├── Creating BACKEND component only?
        │   └── YES → What component?
        │       ├── Database table/model → FLOW A1
        │       ├── API endpoint → FLOW A2
        │       ├── Service/business logic → FLOW A3
        │       ├── Background job → FLOW A4
        │       ├── Event/message → FLOW A5
        │       └── External integration → FLOW A6
        │
        └── Creating FRONTEND component only?
            └── YES → What component?
                ├── UI component → FLOW B1
                ├── Page/view → FLOW B2
                ├── Form → FLOW B3
                ├── Data table → FLOW B4
                └── Real-time feature → FLOW B5
```

---

### B. MAINTAIN Existing Code

```
MAINTAIN existing code
        │
        ├── Fixing a BUG?
        │   └── YES → FLOW E1: Bug Fix
        │       │
        │       └── Steps:
        │           1. Reproduce bug
        │           2. Root cause analysis
        │           3. Write failing test
        │           4. Implement fix
        │           5. Verify fix
        │
        ├── REFACTORING code?
        │   └── YES → FLOW E2: Refactoring
        │       │
        │       └── Prerequisites:
        │           - Sufficient test coverage
        │           - Clear scope
        │
        ├── PERFORMANCE issue?
        │   └── YES → FLOW E3: Performance Optimization
        │       │
        │       └── Check:
        │           - API response > 200ms?
        │           - Database query > 50ms?
        │           - LCP > 2.5s?
        │
        └── SECURITY vulnerability?
            └── YES → FLOW E4: Security Fix
                │
                └── Priority:
                    - Critical → Hotfix immediately
                    - High → Fix within 24h
                    - Medium → Fix within 1 week
                    - Low → Schedule for next sprint
```

---

### C. DOCUMENT the System

```
DOCUMENT the system
        │
        ├── Module documentation outdated?
        │   └── YES → FLOW F1: Update Module Documentation
        │       │
        │       └── Check:
        │           - README.md
        │           - ARCHITECTURE.md
        │           - DATABASE.md
        │           - CHANGELOG.md
        │
        └── API documentation needs update?
            └── YES → FLOW F2: Update API Documentation
                │
                └── Update:
                    - OpenAPI spec
                    - API.md
                    - CHANGELOG.md
```

---

### Quick Decision Matrix

| Situation | Primary Flow | Secondary Flows |
|-----------|--------------|-----------------|
| "I need to add a new entity" | C1 | A1, A2, A3, B2, B3, B4 |
| "I need to add a report" | C2 | A3, A4, B2 |
| "I need to add search" | C3 | A3 |
| "I need to send notifications" | C4 | A5 |
| "I need file upload" | C5 | A2, A3 |
| "I need to create a new module" | D1 | - |
| "There's a bug" | E1 | - |
| "Code is messy" | E2 | - |
| "System is slow" | E3 | - |
| "Security issue found" | E4 | - |
| "Docs are outdated" | F1 or F2 | - |

---

## APPENDIX: STANDARDS QUICK REFERENCE

### All 45 Development Standards

| # | Standard | Document | Key Points |
|---|----------|----------|------------|
| 1 | Naming Conventions | V1 | snake_case (Python), camelCase (JS), PascalCase (classes) |
| 2 | Database Patterns | V1 | UUID primary keys, soft delete, timestamps, indexes |
| 3 | RBAC / Permission | V1 | {module}.{resource}.{action} format |
| 4 | Audit Log | V1 | Who, what, when, where for sensitive operations |
| 5 | Caching | V1 | Redis, TTL strategy, cache invalidation |
| 6 | API Patterns | V1 | REST, consistent response format, versioning |
| 7 | Error Handling | V1 | Structured errors, error codes, no stack traces to client |
| 8 | Validation | V2 | Pydantic (backend), Zod (frontend), early validation |
| 9 | Testing | V2 | Unit/integration/e2e, 80% coverage minimum |
| 10 | Code Structure | V2 | Clean architecture, dependency injection |
| 11 | Frontend Patterns | V2 | React Query, component patterns, TypeScript |
| 12 | Infrastructure & DevOps | V2 | Docker, CI/CD, environment management |
| 13 | Payment & Licensing | V2 | Multi-tier subscription, payment integration |
| 14 | TimescaleDB & Operational | V2 | Hypertables for time-series data |
| 15 | Logging & Observability | V2 | Structured logs, correlation IDs, metrics |
| 16 | Internationalization (i18n) | V2 | Multi-language support, RTL, date/number formats |
| 17 | Centralized Registries | V3 | Service registry, feature registry |
| 18 | Event/Message Schema | V3 | Event envelope, versioning, dead letter queue |
| 19 | File/Media Handling | V3 | R2 storage, presigned URLs, virus scanning |
| 20 | Real-time/WebSocket | V4 | Centrifugo, channels, presence |
| 21 | Background Job (Celery) | V4 | Task queues, retry strategy, monitoring |
| 22 | Search (Meilisearch) | V4 | Indexing, facets, typo tolerance |
| 23 | Notification | V5 | Email, SMS, push, in-app, preferences |
| 24 | API Versioning | V5 | URL versioning, deprecation policy |
| 25 | Feature Flags | V5 | Gradual rollout, A/B testing |
| 26 | Performance SLA | V5 | API < 200ms, DB < 50ms, LCP < 2.5s |
| 27 | Lookup/Type Tables | V6 | Centralized lookup, caching, seeding |
| 28 | State Machine / Workflow | V7 | Transitions, guards, history |
| 29 | Multi-tenancy Deep Dive | V7 | tenant_id everywhere, RLS |
| 30 | Rate Limiting & Throttling | V7 | Per-user, per-tenant, per-endpoint |
| 31 | Backup & Disaster Recovery | V8 | RPO/RTO, automated backups, testing |
| 32 | Webhook System | V8 | Outbound webhooks, retry, signatures |
| 33 | Report Generation | V8 | Templates, async generation, exports |
| 34 | Data Import/Export | V9 | CSV/Excel, validation, progress tracking |
| 35 | Email Templates | V9 | MJML, localization, preview |
| 36 | Offline/PWA Support | V9 | Service worker, sync queue |
| 37 | Circuit Breaker & Resilience | V10 | Tenacity, fallbacks, health checks |
| 38 | Health Checks & Readiness | V10 | Liveness, readiness, dependencies |
| 39 | Data Archival & Retention | V10 | Policies, archival jobs, compliance |
| 40 | Distributed Tracing | V11 | OpenTelemetry, trace propagation |
| 41 | Secrets Management | V11 | Vault integration, rotation, no hardcoding |
| 42 | Scheduled Tasks & Cron | V11 | Celery beat, monitoring, alerting |
| 43 | Configuration Governance | V12 | Config validation, environment parity |
| 44 | Fraud Detection & Audit Intelligence | V13 | Anomaly detection, risk scoring |
| 45 | Internal Collaboration Hub | V14 | Team communication, task management |

---

### Standards by Category

**Database & Data:**
- #2 Database Patterns
- #14 TimescaleDB
- #27 Lookup Tables
- #29 Multi-tenancy
- #39 Data Archival

**API & Backend:**
- #6 API Patterns
- #7 Error Handling
- #8 Validation
- #10 Code Structure
- #24 API Versioning
- #30 Rate Limiting

**Security & Auth:**
- #3 RBAC
- #4 Audit Log
- #41 Secrets Management
- #44 Fraud Detection

**Frontend:**
- #11 Frontend Patterns
- #16 i18n
- #36 PWA/Offline

**Infrastructure:**
- #5 Caching
- #12 DevOps
- #15 Logging
- #31 Backup/DR
- #37 Circuit Breaker
- #38 Health Checks
- #40 Distributed Tracing
- #43 Config Governance

**Integration & Communication:**
- #17 Registries
- #18 Events/Messages
- #19 File Handling
- #20 WebSocket
- #21 Background Jobs
- #22 Search
- #23 Notifications
- #32 Webhooks
- #35 Email Templates

**Business & Payments:**
- #13 Payment & Licensing
- #28 State Machine
- #33 Reports
- #34 Import/Export

**Quality & Process:**
- #1 Naming Conventions
- #9 Testing
- #25 Feature Flags
- #26 Performance SLA
- #42 Scheduled Tasks
- #45 Collaboration Hub

---

### Documents Quick Reference

| Document | Purpose | Key Content |
|----------|---------|-------------|
| DEVELOPMENT_STANDARDS.md | Standards V1 (#1-7) | Core patterns |
| DEVELOPMENT_STANDARDS_V2.md | Standards V2 (#8-16) | Testing, Frontend, DevOps |
| DEVELOPMENT_STANDARDS_V3.md | Standards V3 (#17-19) | Registries, Events, Files |
| DEVELOPMENT_STANDARDS_V4.md | Standards V4 (#20-22) | Real-time, Jobs, Search |
| DEVELOPMENT_STANDARDS_V5.md | Standards V5 (#23-26) | Notification, API, Performance |
| DEVELOPMENT_STANDARDS_V6.md | Standards V6 (#27) | Lookup Tables |
| DEVELOPMENT_STANDARDS_V7.md | Standards V7 (#28-30) | State Machine, Multi-tenancy |
| DEVELOPMENT_STANDARDS_V8.md | Standards V8 (#31-33) | Backup, Webhooks, Reports |
| DEVELOPMENT_STANDARDS_V9.md | Standards V9 (#34-36) | Import/Export, Email, PWA |
| DEVELOPMENT_STANDARDS_V10.md | Standards V10 (#37-39) | Circuit Breaker, Health, Archival |
| DEVELOPMENT_STANDARDS_V11.md | Standards V11 (#40-42) | Tracing, Secrets, Cron |
| DEVELOPMENT_STANDARDS_V12.md | Standards V12 (#43) | Config Governance |
| DEVELOPMENT_STANDARDS_V13.md | Standards V13 (#44) | Fraud Detection |
| DEVELOPMENT_STANDARDS_V14.md | Standards V14 (#45) | Collaboration Hub |
| DATABASE_SCHEMA_PLATFORM.md | Database design | Platform & Community schemas |
| API_CONTRACTS_PLATFORM.md | API design | Endpoint contracts |
| SECURITY_AUTH_REQUIREMENTS.md | Security | Auth, RBAC, compliance |
| MODULE_ARCHITECTURE.md | Module design | Module structure, building blocks |
| UI_DESIGN_SYSTEM.md | UI design | Colors, typography, spacing |
| UI_COMPONENTS.md | UI components | Component specifications |
| TESTING_STRATEGY.md | Testing | Coverage, strategies, tools |
| MODULE_DOCUMENTATION_STANDARD.md | Documentation | DVL tool, templates |
| BUSINESS_ACCOUNTING_STANDARDS.md | Business logic | Accounting rules |
| PLATFORM_VISION.md | Vision | Platform architecture vision |
| PMS_DECISIONS.md | Decisions | 245 approved decisions |

---

### Module Colors Reference

| Module | Primary | Secondary | Usage |
|--------|---------|-----------|-------|
| PMS | #2563EB | #3B82F6 | Hotel operations |
| POS | #EA580C | #F97316 | Point of sale |
| HRM | #7C3AED | #8B5CF6 | Human resources |
| Accounting | #059669 | #10B981 | Financial |
| Inventory | #0891B2 | #06B6D4 | Stock management |
| Procurement | #CA8A04 | #EAB308 | Purchasing |
| Asset | #4F46E5 | #6366F1 | Asset management |
| Guest | #DB2777 | #EC4899 | Guest app |
| Channel | #0D9488 | #14B8A6 | Channel manager |
| Signage | #DC2626 | #EF4444 | Digital signage |
| Supplier | #65A30D | #84CC16 | Supplier portal |
| IoT | #9333EA | #A855F7 | Smart devices |
| Menu | #C2410C | #EA580C | Online menu |
| Platform | #475569 | #64748B | Platform core |

---

## DOCUMENT COMPLETE

**DEVELOPMENT_FLOW_GUIDE.md** - Version 1.0

### Summary

Dokumen ini berisi **22 flows** yang mencakup seluruh development lifecycle:

**Backend Flows (A1-A6):**
- A1: Create Database Model
- A2: Create API Endpoint
- A3: Create Service/Business Logic
- A4: Create Background Job
- A5: Create Event/Message
- A6: Create Integration

**Frontend Flows (B1-B5):**
- B1: Create UI Component
- B2: Create Page/View
- B3: Create Form
- B4: Create Data Table
- B5: Create Real-time Feature

**Full Feature Flows (C1-C5):**
- C1: Create CRUD Feature
- C2: Create Report Feature
- C3: Create Search Feature
- C4: Create Notification Feature
- C5: Create File Upload Feature

**Module Flows (D1-D2):**
- D1: Create New Module
- D2: Add Feature to Module

**Maintenance Flows (E1-E4):**
- E1: Bug Fix
- E2: Refactoring
- E3: Performance Optimization
- E4: Security Fix

**Documentation Flows (F1-F2):**
- F1: Update Module Documentation
- F2: Update API Documentation

### How to Use This Guide

1. **Starting a Task**: Go to [G2: Flow Decision Tree](#g2-flow-decision-tree-master-navigation) to find the right flow

2. **During Development**: Follow the flow step-by-step, checking off items as you complete them

3. **Quick Reference**: Use [G1: Cheat Sheet](#g1-flow-quick-reference-cheat-sheet) for common commands and patterns

4. **Standards Lookup**: Use the [Appendix](#appendix-standards-quick-reference) to find relevant standards

### Maintenance

This document should be updated when:
- New standards are added
- Flows need to be modified
- New patterns are established
- Tools or technologies change

---

*Last Updated: 2024-12-12*
*Document Version: 1.0*
*Total Flows: 22*
*References: 45 Standards across 14 documents*
