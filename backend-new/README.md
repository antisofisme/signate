# Backend-New - Clean Architecture Template

**Status:** 🚧 TEMPLATE / BLUEPRINT (Belum Production Ready)

## ⚠️ PENTING: Ini Folder Template!

Folder `backend-new/` ini adalah **TEMPLATE** dan **BLUEPRINT** arsitektur optimal.
**BUKAN kode final!** Code yang ada di sini adalah contoh pattern, bukan copy paste dari backend lama.

### Next Steps:

1. **FASE 1**: Copy models dari `backend/` dan `anthias/` ke sini
2. **FASE 2**: Refactor services untuk pakai repository pattern
3. **FASE 3**: Merge anthias code ke storage module
4. **FASE 4**: Test dan validasi semua endpoint
5. **FASE 5**: Deploy ke production (ganti backend lama)

Baca `REFACTORING_PLAN.md` untuk detail lengkap strategi migrasi.

---

## 🎯 Tujuan Arsitektur Ini

### Problem Yang Diselesaikan:

1. ❌ **Backend + Anthias terpisah** → 2 API sources (port 8001 + 8000)
2. ❌ **No repository layer** → Query SQL scattered di 26 file
3. ❌ **Build time lama** → 10-15 menit (2 Dockerfile terpisah)
4. ❌ **Deploy time lama** → 5 menit restart
5. ❌ **11 Docker services** → Terlalu complex

### Solution:

1. ✅ **1 Unified API** → Semua endpoints di port 8001 (anthias merged)
2. ✅ **Repository pattern** → Semua query centralized
3. ✅ **Clean architecture** → API → Service → Repository → DB
4. ✅ **Build time < 5 min** → 1 Dockerfile
5. ✅ **6 Docker services** → Simplified

---

## 📁 Struktur Folder

```
backend-new/
├── REFACTORING_PLAN.md          # 📋 Master plan & strategi migrasi
├── README.md                     # 📖 File ini
│
└── app/
    ├── api/                      # 🚪 PINTU MASUK (HTTP handlers)
    │   ├── devices.py            # ✅ Contoh: Device CRUD
    │   ├── content.py            # ⏳ TODO: Copy dari backend lama
    │   ├── playlists.py          # ⏳ TODO: Copy dari backend lama
    │   ├── storage.py            # ⏳ TODO: Merge dari anthias
    │   └── files.py              # ⏳ TODO: Merge dari anthias
    │
    ├── services/                 # 🧠 LOGIKA BISNIS
    │   ├── device_service.py     # ✅ Contoh: Device business logic
    │   ├── content_service.py    # ⏳ TODO: Refactor dari backend lama
    │   └── storage_service.py    # ⏳ TODO: Merge dari anthias
    │
    ├── repositories/             # 🗄️ PINTU KELUAR (Database queries)
    │   ├── base.py               # ✅ Base repository pattern
    │   ├── device_repository.py  # ✅ Contoh: Device queries
    │   ├── content_repository.py # ✅ Contoh: Content queries
    │   └── file_repository.py    # ⏳ TODO: From anthias assets
    │
    ├── models/                   # ⏳ TODO: Copy dari backend lama
    ├── schemas/                  # ⏳ TODO: Copy dari backend lama
    ├── tasks/                    # ⏳ TODO: Merge backend + anthias
    ├── storage/                  # ⏳ TODO: Merge anthias code
    ├── core/                     # ⏳ TODO: Copy dari backend lama
    └── utils/                    # ⏳ TODO: Copy dari backend lama
```

**Legend:**
- ✅ = Template/contoh sudah ada
- ⏳ = Belum ada, perlu copy/refactor dari backend/anthias lama

---

## 🏗️ Clean Architecture Pattern

### Flow Diagram:

```
┌─────────────┐
│   REQUEST   │  HTTP Request dari client
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  API LAYER (api/devices.py)                 │
│  ✓ Parse HTTP request                       │
│  ✓ Validate input format                    │
│  ✓ Call service                             │
│  ✓ Return JSON response                     │
│  ❌ NO business logic                       │
│  ❌ NO database queries                     │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  SERVICE LAYER (services/device_service.py) │
│  ✓ Validate business rules                  │
│  ✓ Execute business logic                   │
│  ✓ Orchestrate multiple repos               │
│  ✓ Transform data                           │
│  ✓ Error handling                           │
│  ❌ NO HTTP handling                        │
│  ❌ NO SQL queries                          │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  REPOSITORY LAYER (repos/device_repo.py)    │
│  ✓ Execute SQL queries                      │
│  ✓ Return raw data                          │
│  ✓ CRUD operations                          │
│  ❌ NO business logic                       │
│  ❌ NO data transformation                  │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  DATABASE   │  PostgreSQL
└─────────────┘
```

### Contoh Konkrit:

**Request:** `GET /api/devices/123`

**1. API Layer** (`api/devices.py`):
```python
@router.get("/{device_id}")
async def get_device(device_id: int, service: DeviceService = Depends()):
    device = service.get_device(device_id)  # Call service
    return device  # Return JSON
```

**2. Service Layer** (`services/device_service.py`):
```python
def get_device(self, device_id: int) -> Dict:
    device = self.device_repo.get(device_id)  # Call repository

    # Business logic: enrich data
    device.is_online = self._check_online(device.last_seen)
    device.last_seen_human = self._format_time(device.last_seen)

    return device
```

**3. Repository Layer** (`repositories/device_repository.py`):
```python
def get(self, device_id: int):
    # SQL query
    return db.query(Device).filter(Device.id == device_id).first()
```

**4. Database:** Execute `SELECT * FROM devices WHERE id = 123`

---

## 🔧 Cara Pakai Template Ini

### JANGAN langsung deploy! Ini workflow yang benar:

### Step 1: Copy Models (Priority 1)

```bash
# Copy models dari backend lama
cp ../backend/app/models/*.py app/models/

# Update imports di repositories untuk pakai model yang real
# Edit: app/repositories/device_repository.py
# from app.models.device import Device
```

### Step 2: Refactor Services (Priority 2)

```bash
# Copy service dari backend lama
cp ../backend/app/services/device_service.py app/services/

# Refactor untuk pakai repository:
# BEFORE:
# device = db.query(Device).filter(id=1).first()  # ❌ Direct query

# AFTER:
# device = self.device_repo.get(1)  # ✅ Via repository
```

### Step 3: Merge Anthias (Priority 3)

```bash
# Copy anthias code ke storage module
cp -r ../anthias/anthias_app/file_handling.py app/storage/

# Buat file_repository.py untuk anthias assets
# Buat storage_service.py untuk business logic
# Buat api/storage.py untuk HTTP endpoints
```

### Step 4: Test Endpoint by Endpoint

```bash
# Test 1 endpoint dulu (misal: devices)
# Jangan test semua sekaligus!

# 1. Update models
# 2. Update repository
# 3. Update service
# 4. Update API
# 5. Test dengan curl/postman
# 6. Fix bugs
# 7. Lanjut endpoint berikutnya
```

### Step 5: Docker & Deploy

```bash
# Build image baru
docker-compose -f docker-compose.yml build

# Test lokal dulu
docker-compose up -d

# Test semua endpoint
# Fix bugs

# Deploy ke server (ganti backend lama)
```

---

## 📊 Comparison: Old vs New

### Architecture:

| Aspect | OLD (backend + anthias) | NEW (unified) |
|--------|-------------------------|---------------|
| API sources | 2 (port 8001 + 8000) | 1 (port 8001) |
| Repository layer | ❌ None | ✅ Yes |
| Query location | Scattered (26 files) | Centralized (repos/) |
| Services | 13 files (some good) | 15 files (all clean) |
| Docker services | 11 | 6 |
| Build time | 10-15 min | < 5 min |
| Deploy time | 5 min | < 1 min |

### Code Structure:

**OLD (Bad):**
```python
# api/devices.py - Direct query ❌
def get_devices():
    devices = db.query(Device).filter(status="active").all()
    return devices
```

**NEW (Good):**
```python
# api/devices.py - Call service ✅
def get_devices():
    return device_service.get_all(status="active")

# services/device_service.py - Call repository ✅
def get_all(status):
    return device_repo.get_all(filters={"status": status})

# repositories/device_repository.py - Query ✅
def get_all(filters):
    return db.query(Device).filter_by(**filters).all()
```

---

## 🚨 CRITICAL RULES

### DO (WAJIB):

1. ✅ **Semua query WAJIB via repository** - No exceptions!
2. ✅ **API hanya HTTP handling** - No business logic
3. ✅ **Service untuk business logic** - No SQL queries
4. ✅ **Test incrementally** - 1 endpoint at a time
5. ✅ **Copy real code** - Jangan ngarang asal!

### DON'T (DILARANG):

1. ❌ **Direct DB query di API** - MUST use repository
2. ❌ **Business logic di API** - MUST be in service
3. ❌ **SQL di service** - MUST be in repository
4. ❌ **Deploy before testing** - Test lokal dulu!
5. ❌ **Big bang migration** - Migrate incremental!

---

## 📚 Files Yang Sudah Ada (Template)

### 1. `REFACTORING_PLAN.md`
Master plan lengkap dengan:
- Problem statement
- Target architecture
- Migration strategy (6 phases)
- Success metrics

### 2. `SERVICES_BREAKDOWN.md` ⭐ NEW!
Detail breakdown 12 services optimal:
- Fungsi masing-masing service
- Priority & dependencies
- Estimasi lines of code
- Migration timeline

### 3. `app/repositories/base.py`
Base repository pattern dengan:
- CRUD operations (create, read, update, delete)
- Pagination support
- Search & filtering
- Generic typing support

### 4. `app/repositories/device_repository.py`
Contoh device repository dengan:
- Device-specific queries
- Online/offline detection
- Activation logic
- Stats & analytics

### 5. `app/repositories/content_repository.py`
Contoh content repository dengan:
- Content by type & organization
- Scheduled content queries
- File size & stats
- Search & tagging

### 6. `app/services/device_service.py`
Contoh device service dengan:
- CRUD with validation
- Activation business logic
- Heartbeat processing
- Dashboard analytics

### 7. `app/api/devices.py`
Contoh device API dengan:
- RESTful endpoints
- Pagination
- Search
- Heartbeat endpoint

---

## 🔗 References

- **Backend lama**: `/mnt/g/khoirul/signate/backend`
- **Anthias**: `/mnt/g/khoirul/signate/anthias`
- **Backend baru (template)**: `/mnt/g/khoirul/signate/backend-new`
- **Database schema**: `../DATABASE_SCHEMA_ANALYSIS.md`
- **Fixes applied**: `../FIXES_APPLIED.md`

---

## ❓ FAQ

### Q: Apakah backend-new ini sudah bisa di-run?
**A:** ❌ BELUM! Ini template/blueprint. Perlu copy models dan code dari backend lama dulu.

### Q: Kenapa tidak langsung copy semua code?
**A:** Karena kita mau refactor juga. Copy satu-satu sambil refactor ke pattern yang benar.

### Q: Apa yang perlu di-copy dari backend lama?
**A:** Models, schemas, core utilities, beberapa services (yang udah bagus). Tapi perlu refactor services yang masih query langsung.

### Q: Apa yang perlu di-merge dari anthias?
**A:** File handling, storage management, transcoding tasks, asset models.

### Q: Berapa lama estimasi refactoring?
**A:**
- FASE 1 (Models): 2-4 jam
- FASE 2 (Services): 1-2 hari
- FASE 3 (Anthias merge): 2-3 hari
- FASE 4 (API refactor): 1-2 hari
- FASE 5 (Tasks): 1 hari
- FASE 6 (Docker): 1 hari
- **Total**: 1-2 minggu (dengan testing)

### Q: Apakah database schema perlu diubah?
**A:** ❌ TIDAK! Schema tetap sama. Yang diubah hanya code architecture.

### Q: Bagaimana strategi deployment?
**A:** Incremental. Test lokal dulu, deploy endpoint by endpoint, backward compatible.

---

## 📞 Support

Baca `REFACTORING_PLAN.md` untuk detail lengkap. Jika ada pertanyaan, refer ke dokumentasi atau code comments.
