# Services Layer Breakdown - Detail Lengkap

## 📊 TOTAL SERVICES: 13 Services Optimal

Setelah merge Backend + Anthias, inilah breakdown lengkap services yang diperlukan.
**⭐ INCLUDES MULTI-TENANT (organization_service)**

---

## 🎯 Core Services (WAJIB - 7 Services)

### 1. **organization_service.py** ⭐ MULTI-TENANT
**Source:** Backend existing (critical!)
**Fungsi:**
- Organization CRUD (create, read, update, delete)
- Organization PIN management (8-digit secure PIN)
- User organization membership
- Organization switching (user bisa akses multiple orgs)
- Organization settings management
- Organization statistics & quotas
- Invite users to organization

**Business Logic:**
```python
# Multi-tenant rules:
- Setiap user WAJIB punya organization_id
- User bisa member di multiple organizations
- Data isolation: devices, content, playlists per organization
- Super admin bisa akses semua organizations
- Regular user hanya bisa akses org mereka
- PIN untuk organization join (8 digit unique)
```

**Dependencies:**
- `OrganizationRepository` → Query organizations table
- `UserRepository` → Manage user-org relationships
- Middleware: OrganizationContext (enforce tenant isolation)

**Database Tables:**
- `organizations` - Organization data
- `user_organizations` - Many-to-many user <-> org
- `roles` - Role per organization

---

### 2. **device_service.py**
**Source:** Backend existing + new logic
**Fungsi:**
- Device registration & activation (6-digit code)
- Device CRUD operations
- Heartbeat processing (update last_seen)
- Online/offline status calculation
- Device statistics untuk dashboard
- Search devices by name/location

**Business Logic:**
```python
# Contoh business rules:
- Activation code harus unique & 6 digit
- Status otomatis jadi "active" setelah aktivasi
- Device dianggap online jika heartbeat < 5 menit
- Cannot change device_id setelah activated
```

**Dependencies:**
- `DeviceRepository` → Query devices table
- `ActivityRepository` → Log device activities
- `TagRepository` → Device tagging

---

### 2. **content_service.py**
**Source:** Backend existing + refactor
**Fungsi:**
- Content CRUD (images, videos, HTML, URLs)
- Content upload & validation
- Scheduled content filtering (start_date, end_date)
- Content by tags/playlists
- Content statistics (total size, by type)
- Soft delete dengan is_active flag

**Business Logic:**
```python
# Contoh business rules:
- File size validation (max 500MB untuk video)
- Content type validation (allowed: image, video, html, url)
- Start date tidak boleh > end date
- Auto-set processing_status: pending → processing → completed
- Scheduled content: hanya tampilkan yang aktif & dalam range waktu
```

**Dependencies:**
- `ContentRepository` → Query contents table
- `FileService` → File handling (jika upload)
- `StorageService` → Save file ke storage
- `TranscodingService` → Trigger transcoding untuk video

---

### 3. **playlist_service.py**
**Source:** Backend existing
**Fungsi:**
- Playlist CRUD
- Add/remove content ke playlist
- Reorder content (play_order)
- Assign playlist ke devices
- Get active playlist for device
- Playlist scheduling

**Business Logic:**
```python
# Contoh business rules:
- Playlist harus punya minimal 1 content
- play_order auto-increment saat add content
- Satu device bisa punya multiple playlists (weighted scheduling)
- Content bisa ada di multiple playlists
```

**Dependencies:**
- `PlaylistRepository` → Query playlists table
- `ContentRepository` → Get content data
- `DeviceRepository` → Assign playlist ke device

---

### 4. **storage_service.py**
**Source:** Anthias (MERGED)
**Fungsi:**
- File storage orchestration
- Path management (/data/screenly_assets/)
- File metadata tracking
- Cleanup old files
- Storage quota management
- Asset organization

**Business Logic:**
```python
# Contoh business rules:
- Files disimpan dengan hash filename untuk avoid collision
- Path structure: /data/screenly_assets/{org_id}/{year}/{month}/{filename}
- Auto cleanup files jika > 30 hari tidak digunakan
- Storage quota per organization (default 10GB)
```

**Dependencies:**
- `FileRepository` → Track file metadata (assets table)
- `ContentRepository` → Link to content
- File system operations

---

### 5. **file_service.py**
**Source:** Anthias (MERGED)
**Fungsi:**
- File upload processing
- File validation (type, size, format)
- Image/video optimization
- Thumbnail generation
- File format conversion
- Hash generation (MD5)

**Business Logic:**
```python
# Contoh business rules:
- Image: resize jika > 1920x1080, compress quality 85%
- Video: validate codec (H.264), container (MP4)
- Thumbnail: 320x180px untuk preview
- MD5 hash untuk detect duplicates
```

**Dependencies:**
- `StorageService` → Save to disk
- `TranscodingService` → Video processing
- PIL/Pillow untuk image
- FFmpeg untuk video

---

### 6. **transcoding_service.py**
**Source:** Anthias (MERGED)
**Fungsi:**
- Video transcoding H.264
- HLS variant generation (multiple bitrates)
- Audio normalization
- Subtitle extraction
- Transcoding progress tracking
- Error handling & retry

**Business Logic:**
```python
# Contoh business rules:
- Generate 3 HLS variants: 720p, 480p, 360p
- Target codec: H.264, AAC audio
- Max duration: 1 hour (server-side limit)
- Auto-retry 3x jika failed
- Status: pending → processing → completed/failed
```

**Dependencies:**
- `FileService` → Input file
- `StorageService` → Output files
- FFmpeg binary
- Celery tasks (background)

---

## 🎨 Feature Services (PENTING - 4 Services)

### 7. **analytics_service.py**
**Source:** Backend existing (merge reports + analytics)
**Fungsi:**
- Dashboard statistics
- Device analytics (online/offline trends)
- Content views tracking
- Playlist performance
- Report generation (PDF/Excel)
- Custom date range queries

**Business Logic:**
```python
# Metrics yang di-track:
- Total devices, online ratio, uptime percentage
- Content plays count, most played content
- Peak hours usage
- Device errors & logs
- Storage usage per organization
```

**Dependencies:**
- `DeviceRepository` → Device stats
- `ContentRepository` → Content stats
- `ActivityRepository` → Activity logs
- `LogRepository` → Device logs

---

### 8. **schedule_service.py**
**Source:** Backend existing
**Fungsi:**
- Content scheduling logic
- Playlist scheduling (time-based)
- Rotation management
- Priority handling
- Schedule conflict resolution

**Business Logic:**
```python
# Scheduling logic:
- Priority: scheduled content > playlist > default content
- Time-based: weekday/weekend, specific hours
- Rotation: round-robin vs weighted
- Conflict: higher priority wins
```

**Dependencies:**
- `ContentRepository` → Scheduled content
- `PlaylistRepository` → Playlist schedules
- `DeviceRepository` → Device assignments

---

### 9. **template_service.py**
**Source:** Backend existing
**Fungsi:**
- HTML template rendering
- Variable substitution (weather, date, etc.)
- Template validation
- Dynamic content generation

**Business Logic:**
```python
# Template variables:
- {{date}} - Current date
- {{time}} - Current time
- {{weather}} - Weather API integration
- {{device.name}} - Device info
- {{content.title}} - Content metadata
```

**Dependencies:**
- `ContentRepository` → Template data
- Jinja2 template engine
- External APIs (weather, etc.)

---

### 10. **translation_service.py**
**Source:** Backend existing
**Fungsi:**
- Multi-language support (Bahasa, English)
- Content translation management
- UI language switching
- Language rotation on devices

**Business Logic:**
```python
# i18n logic:
- Primary language: id (Bahasa Indonesia)
- Secondary language: en (English)
- Auto-rotation: switch every 30 seconds
- Fallback: if translation missing, use primary
```

**Dependencies:**
- Translation files (JSON/YAML)
- Content metadata
- Device language settings

---

## 🔧 Integration Services (OPSIONAL - 2 Services)

### 11. **firebird_service.py**
**Source:** Backend existing (optional integration)
**Fungsi:**
- Firebird database integration
- External data sync
- Legacy system adapter

**Catatan:** Optional, tergantung apakah masih dipakai atau tidak.

---

### 12. **websocket_service.py**
**Source:** Backend existing (merge websocket + websocket_v2)
**Fungsi:**
- Real-time device status broadcast
- Content update notifications
- Dashboard live updates
- Command broadcasting ke devices

**Business Logic:**
```python
# WebSocket events:
- device.online / device.offline
- content.updated
- playlist.changed
- command.execute (remote commands)
```

**Dependencies:**
- Redis pub/sub
- FastAPI WebSocket
- Device connections tracking

---

## 📊 SUMMARY: Services Matrix

| # | Service Name | Source | Priority | Lines of Code | Dependencies |
|---|-------------|--------|----------|---------------|--------------|
| 1 | **organization_service** | Backend | **CRITICAL** | ~400 | OrgRepo, UserRepo, Middleware |
| 2 | device_service | Backend | **HIGH** | ~300 | DeviceRepo, ActivityRepo |
| 3 | content_service | Backend | **HIGH** | ~400 | ContentRepo, FileService |
| 4 | playlist_service | Backend | **HIGH** | ~250 | PlaylistRepo, ContentRepo |
| 5 | storage_service | **Anthias** | **HIGH** | ~300 | FileRepo, Filesystem |
| 6 | file_service | **Anthias** | **HIGH** | ~350 | StorageService, PIL, FFmpeg |
| 7 | transcoding_service | **Anthias** | **HIGH** | ~400 | FileService, Celery |
| 8 | analytics_service | Backend | MEDIUM | ~300 | Multiple repos |
| 9 | schedule_service | Backend | MEDIUM | ~200 | ContentRepo, PlaylistRepo |
| 10 | template_service | Backend | MEDIUM | ~150 | Jinja2 |
| 11 | translation_service | Backend | MEDIUM | ~100 | i18n files |
| 12 | firebird_service | Backend | LOW | ~200 | Firebird DB (optional) |
| 13 | websocket_service | Backend | MEDIUM | ~150 | Redis, WebSocket |

**TOTAL ESTIMATED:** ~3,500 lines of service code

---

## 🎯 Migration Priority

### FASE 0: Multi-Tenant Foundation (CRITICAL - FIRST!)
1. ⏳ **organization_service.py** - WAJIB DI-IMPLEMENT PERTAMA!
   - Karena semua data terisolasi per organization
   - Semua service lain butuh organization_id

### FASE 1: Core Services (WAJIB)
2. ⏳ device_service.py
3. ⏳ content_service.py
4. ⏳ playlist_service.py

### FASE 2: Anthias Integration (CRITICAL)
4. ⏳ storage_service.py (merge dari anthias)
5. ⏳ file_service.py (merge dari anthias)
6. ⏳ transcoding_service.py (merge dari anthias)

### FASE 3: Feature Services (IMPORTANT)
7. ⏳ analytics_service.py
8. ⏳ schedule_service.py
9. ⏳ template_service.py
10. ⏳ translation_service.py

### FASE 4: Optional Services (NICE TO HAVE)
11. ⏳ firebird_service.py (jika masih dipakai)
12. ⏳ websocket_service.py

---

## 🔍 Services vs Repositories vs API

### Relationship Matrix:

```
API Endpoint → Service → Repository

/api/devices → DeviceService → DeviceRepository → devices table
/api/content → ContentService → ContentRepository → contents table
                                StorageService → filesystem
                                FileService → file processing
/api/playlists → PlaylistService → PlaylistRepository → playlists table
/api/storage → StorageService → FileRepository → assets table
/api/analytics → AnalyticsService → Multiple repositories
```

---

## 📝 Naming Convention

**Services:**
- Singular form: `device_service.py` (not devices_service)
- Suffix: `_service.py`
- Class name: PascalCase `DeviceService`

**Pattern:**
```python
# File: app/services/device_service.py
class DeviceService:
    def __init__(self, db: Session):
        self.device_repo = DeviceRepository(db)

    def get_device(self, id: int) -> Dict:
        # Business logic here
        pass
```

---

## ❓ FAQ

### Q: Kenapa 13 services? Kok banyak?
**A:** Ini sudah konsolidasi dari 13+ backend + anthias services. Sebenarnya sudah dikurangi duplikasi. Yang ke-13 adalah **organization_service** untuk multi-tenant (CRITICAL!).

### Q: Apakah semua 13 services WAJIB?
**A:** TIDAK. Priority CRITICAL (1 service: organization) + Priority HIGH (6 services) adalah WAJIB. Sisanya bisa incremental.

### Q: Berapa lama develop 13 services ini?
**A:**
- Core 6 services: 2-3 hari
- Anthias 3 services: 2-3 hari
- Feature 4 services: 2-3 hari
- **Total: 1-2 minggu**

### Q: Apakah services ini independent?
**A:** Ya! Tiap service punya tanggung jawab jelas. Bisa develop & test terpisah.

### Q: Bagaimana testing strategy?
**A:** Unit test per service → Integration test → E2E test API

---

## 🔗 References

- Detail implementation: Lihat file contoh `device_service.py`
- Repository patterns: Lihat folder `repositories/`
- API integration: Lihat folder `api/`
