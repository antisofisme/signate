# REFACTORING PLAN - Backend Clean Architecture
**Smart TV Digital Signage System**

## 🎯 TUJUAN REFACTORING

### Problem Statement (Kenapa Perlu Refactoring?)

1. **Duplikasi Service** - Backend (port 8001) dan Anthias (port 8000) terpisah → 2 API sources
2. **No Repository Layer** - API endpoints langsung query ke database → sulit maintenance
3. **Scattered Queries** - Query SQL tersebar di 26 file endpoints → tidak centralized
4. **Build Time Lama** - 10-15 menit (2 Dockerfile terpisah untuk backend + anthias)
5. **Deploy Time Lama** - 5 menit restart semua service
6. **High Complexity** - 11 Docker services untuk 1 aplikasi
7. **Code Duplication** - Transcoding, streaming, websocket ada di 2 tempat

### Success Criteria (Hasil yang Diharapkan)

1. ✅ **1 Sumber API** - Semua endpoints di port 8001 (anthias merged)
2. ✅ **Repository Pattern** - Semua query database centralized
3. ✅ **Clean Architecture** - API → Service → Repository → Database
4. ✅ **Build Time < 5 menit** - 1 Dockerfile untuk semua services
5. ✅ **Deploy Time < 1 menit** - Restart cepat tanpa rebuild
6. ✅ **6 Docker Services** - Dari 11 jadi 6 (postgres, redis, backend, worker, beat, viewer)
7. ✅ **No Code Duplication** - Semua logic centralized

---

## 🏗️ ARSITEKTUR TARGET

### Struktur Folder Optimal

```
backend-new/
├── app/
│   ├── main.py                    # Entry point (1 API saja!)
│   │
│   ├── api/                      # 🚪 PINTU MASUK (HTTP handlers)
│   │   ├── auth.py               # Login, JWT, register
│   │   ├── devices.py            # Device CRUD
│   │   ├── content.py            # Content CRUD
│   │   ├── playlists.py          # Playlist CRUD
│   │   ├── storage.py            # ← ANTHIAS merged: File storage
│   │   ├── files.py              # ← ANTHIAS merged: Upload/download
│   │   ├── streaming.py          # ← ANTHIAS merged: HLS streaming
│   │   ├── activities.py         # Activity logs
│   │   ├── analytics.py          # Reports & analytics
│   │   ├── tags.py               # Tag management
│   │   ├── schedules.py          # Schedule management
│   │   ├── settings.py           # System settings
│   │   ├── websocket.py          # WebSocket handler (unified)
│   │   └── v1/
│   │       └── organizations.py  # Multi-tenant API
│   │
│   ├── services/                 # 🧠 LOGIKA BISNIS
│   │   ├── device_service.py     # Device business logic
│   │   ├── content_service.py    # Content business logic
│   │   ├── playlist_service.py   # Playlist business logic
│   │   ├── storage_service.py    # ← ANTHIAS: File storage logic
│   │   ├── file_service.py       # ← ANTHIAS: File processing
│   │   ├── transcoding_service.py # ← ANTHIAS: Video transcoding
│   │   ├── streaming_service.py  # ← ANTHIAS: HLS generation
│   │   ├── analytics_service.py  # Reports & analytics
│   │   ├── schedule_service.py   # Scheduling logic
│   │   ├── template_service.py   # Template engine
│   │   ├── translation_service.py # i18n
│   │   ├── firebird_service.py   # Firebird integration
│   │   └── websocket_service.py  # WebSocket broadcasting
│   │
│   ├── repositories/             # 🗄️ PINTU KELUAR (Database access)
│   │   ├── base.py               # Base repository pattern
│   │   ├── device_repository.py  # Device queries
│   │   ├── content_repository.py # Content queries
│   │   ├── playlist_repository.py # Playlist queries
│   │   ├── file_repository.py    # ← ANTHIAS: File metadata
│   │   ├── asset_repository.py   # ← ANTHIAS: Asset queries
│   │   ├── user_repository.py    # User queries
│   │   ├── tag_repository.py     # Tag queries
│   │   ├── activity_repository.py # Activity log queries
│   │   └── schedule_repository.py # Schedule queries
│   │
│   ├── tasks/                    # ⚡ CELERY BACKGROUND TASKS
│   │   ├── transcoding.py        # ← ANTHIAS: Video transcoding
│   │   ├── file_processing.py    # ← ANTHIAS: File conversion
│   │   ├── thumbnail.py          # ← ANTHIAS: Thumbnail generation
│   │   ├── cleanup.py            # Cleanup old files
│   │   ├── sync.py               # Device sync tasks
│   │   └── analytics.py          # Analytics computation
│   │
│   ├── storage/                  # ← ANTHIAS CODE MERGED MODULE
│   │   ├── file_manager.py       # File system operations
│   │   ├── processors.py         # Image/video processing
│   │   ├── validators.py         # File validation
│   │   └── converters.py         # Format conversion
│   │
│   ├── models/                   # Database models (SQLAlchemy)
│   │   ├── device.py
│   │   ├── content.py
│   │   ├── playlist.py
│   │   ├── asset.py              # ← ANTHIAS model
│   │   └── ...
│   │
│   ├── schemas/                  # Pydantic validation
│   ├── core/                     # Core utilities
│   ├── middleware/               # HTTP middleware
│   └── utils/                    # Helper functions
│
├── Dockerfile                    # SATU Dockerfile untuk semua
├── requirements.txt              # Python dependencies
└── docker-compose.yml            # 6 services optimal
```

### Flow Pattern (Clean Architecture)

```
REQUEST → API → SERVICE → REPOSITORY → DATABASE
          🚪    🧠         🗄️          💾
```

**Contoh:**
```
GET /api/devices/123

1. API (api/devices.py):
   - Terima HTTP request
   - Validasi input
   - Call service
   - Return response

2. Service (services/device_service.py):
   - Business logic
   - Validasi business rules
   - Call repository
   - Transform data

3. Repository (repositories/device_repository.py):
   - Execute SQL query
   - Return raw data

4. Database:
   - SELECT * FROM devices WHERE id=123
```

---

## 📋 MIGRATION STRATEGY

### FASE 1: Setup Repository Layer (PRIORITY 1)

**Target:** Buat foundation repository pattern

**Tasks:**
1. ✅ Buat `repositories/base.py` - Base CRUD operations
2. ✅ Buat contoh repositories:
   - `device_repository.py`
   - `content_repository.py`
   - `playlist_repository.py`
   - `user_repository.py`
3. ⏳ Copy models dari backend lama
4. ⏳ Test repositories dengan dummy data

**Output:** Repository layer yang bisa dipakai untuk query database

---

### FASE 2: Refactor Services (PRIORITY 2)

**Target:** Update services untuk pakai repositories

**Tasks:**
1. Copy services dari backend lama
2. Refactor services untuk call repository (bukan direct query)
3. Pindahkan semua query SQL ke repositories
4. Unit test untuk services

**Before (Bad):**
```python
# api/devices.py - Direct query ❌
def get_devices():
    devices = db.query(Device).filter(status="active").all()
    return devices
```

**After (Good):**
```python
# api/devices.py - Call service ✅
def get_devices():
    return device_service.get_all_devices(status="active")

# services/device_service.py - Call repository ✅
def get_all_devices(status):
    return device_repo.get_all(filters={"status": status})

# repositories/device_repository.py - Query ✅
def get_all(filters):
    return db.query(Device).filter_by(**filters).all()
```

---

### FASE 3: Merge Anthias (PRIORITY 3)

**Target:** Integrate anthias code ke backend

**Tasks:**
1. Copy anthias code ke `app/storage/` module
2. Buat `file_repository.py`, `asset_repository.py`
3. Buat `storage_service.py`, `file_service.py`, `transcoding_service.py`
4. Buat API endpoints: `api/storage.py`, `api/files.py`
5. Update tasks: `tasks/transcoding.py`, `tasks/file_processing.py`
6. Test file upload, download, transcoding

**Integration Points:**
- File storage endpoints: `/api/storage/upload`, `/api/files/{id}`
- Transcoding tasks: Celery background jobs
- Asset management: Linked to content table

---

### FASE 4: Refactor API Endpoints (PRIORITY 4)

**Target:** Clean up API layer, remove duplikasi

**Tasks:**
1. Merge duplikasi endpoints:
   - `websocket.py` + `websocket_v2.py` → `websocket.py`
   - `analytics.py` + `reports.py` → `analytics.py`
   - Delete `quickwins_demo.py` (demo only)
   - Move `speedtest.py` to utils
2. Standardize response format
3. Update all endpoints untuk pakai service layer
4. API documentation (OpenAPI)

**Endpoint Reduction:**
- From: 26 endpoint files
- To: 13 endpoint files

---

### FASE 5: Optimize Tasks & Workers (PRIORITY 5)

**Target:** Comprehensive background job coverage

**Tasks:**
1. Buat task modules:
   - `transcoding.py` - Video transcoding (from anthias)
   - `file_processing.py` - File upload processing (from anthias)
   - `thumbnail.py` - Thumbnail generation (from anthias)
   - `cleanup.py` - Cleanup old files
   - `sync.py` - Device sync
   - `analytics.py` - Analytics computation
2. Configure Celery queues: default, storage, analytics
3. Setup Celery beat schedule untuk periodic tasks

---

### FASE 6: Docker & Deployment (PRIORITY 6)

**Target:** Optimal docker compose configuration

**Tasks:**
1. Update `Dockerfile` - optimize build time
2. Update `docker-compose.yml` - reduce to 6 services:
   - postgres
   - redis
   - backend-api (port 8001)
   - celery-worker (unified)
   - celery-beat
   - viewer (port 8080)
3. Remove anthias services (merged)
4. Test build time < 5 menit
5. Test deployment

---

## 📊 METRICS & KPI

### Performance Targets

| Metric | BEFORE | TARGET | HOW |
|--------|--------|--------|-----|
| Build time | 10-15 min | < 5 min | 1 Dockerfile |
| Deploy time | 5 min | < 1 min | No rebuild |
| API latency (storage) | 50-100ms | 5-10ms | Direct call |
| Docker services | 11 | 6 | Merge anthias |
| API sources | 2 (8001+8000) | 1 (8001) | Unified |
| Endpoint files | 26 | 13 | Remove duplikat |
| Repository coverage | 0% | 100% | All queries |
| Code duplication | High | Low | Centralized |

### Code Quality Targets

- ✅ All database queries through repositories
- ✅ No direct DB access in API layer
- ✅ All business logic in services
- ✅ API layer only handles HTTP
- ✅ 100% repository test coverage
- ✅ Comprehensive error handling
- ✅ Structured logging

---

## 🚨 CRITICAL RULES

### DO (WAJIB)
1. ✅ **Semua query WAJIB via repository** - API tidak boleh query langsung
2. ✅ **1 API saja** - Semua endpoints di port 8001
3. ✅ **3-layer architecture** - API → Service → Repository
4. ✅ **Copy dulu, delete nanti** - Jangan hapus backend lama sampai sukses
5. ✅ **Test tiap fase** - Pastikan working sebelum lanjut

### DON'T (DILARANG)
1. ❌ **Direct DB query di API** - Harus via repository
2. ❌ **Business logic di API** - Harus di service layer
3. ❌ **SQL query di service** - Harus di repository
4. ❌ **Hapus backend lama** - Keep sampai migration 100%
5. ❌ **Deploy before testing** - Test lokal dulu

---

## 🎯 SUCCESS VALIDATION

### Checklist Sebelum Production

**Architecture:**
- [ ] All queries via repositories (0 direct queries in API)
- [ ] All business logic in services
- [ ] API layer clean (only HTTP handling)
- [ ] Anthias fully integrated (no separate API)

**Performance:**
- [ ] Build time < 5 minutes
- [ ] Deploy time < 1 minute
- [ ] API latency < 20ms (P95)
- [ ] 6 Docker services running

**Functionality:**
- [ ] All existing features working
- [ ] Device registration working
- [ ] Content upload working
- [ ] Video transcoding working
- [ ] Streaming working
- [ ] Dashboard data correct

**Testing:**
- [ ] Unit tests for repositories
- [ ] Unit tests for services
- [ ] Integration tests for APIs
- [ ] Load testing passed

---

## 📝 NOTES

- **Incremental Migration:** Migrate endpoint-by-endpoint, not big bang
- **Backward Compatible:** Old endpoints tetap work during migration
- **Database Unchanged:** No schema changes needed
- **Zero Downtime:** Deploy strategy allows rolling update
- **Documentation:** Update API docs after each phase

---

## 🔗 REFERENCES

- Backend lama: `/mnt/g/khoirul/signate/backend`
- Anthias: `/mnt/g/khoirul/signate/anthias`
- Backend baru: `/mnt/g/khoirul/signate/backend-new`
- Database schema: `DATABASE_SCHEMA_ANALYSIS.md`
- Fixes applied: `FIXES_APPLIED.md`
