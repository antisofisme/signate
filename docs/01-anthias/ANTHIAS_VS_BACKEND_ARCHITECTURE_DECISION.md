# Anthias vs Backend - Architecture Decision

**Date**: October 28, 2025
**Context**: Setelah Backend Upgrade Phase 1-4.4 selesai
**Question**: Apakah masih perlu Anthias atau cukup Backend saja?

---

## TL;DR - Rekomendasi

**🎯 REKOMENDASI: OPTION 2 - Keep Anthias as Minimal Storage Service**

- ✅ **Backend** = Control plane (scheduling, playlists, device management, analytics)
- ✅ **Anthias** = File storage only (upload, serve, checksum)
- ❌ **Hapus** = Semua UI, scheduler, playlist logic dari Anthias

**Why?** Backend sudah punya semua fitur, Anthias hanya perlu sebagai storage layer yang proven & stable.

---

## Feature Comparison: Backend vs Anthias (After Upgrade)

### Features Anthias HAD (Before Upgrade)

| Feature | Anthias | Backend (After Upgrade) | Status |
|---------|---------|------------------------|--------|
| **Asset Storage** | ✅ Yes | ⚠️ Via Anthias API | Keep in Anthias |
| **MD5 Checksums** | ✅ Yes | ✅ **PORTED (Phase 1)** | ✅ Duplicate |
| **Play Order** | ✅ Yes | ✅ **PORTED (Phase 1)** | ✅ Duplicate |
| **Start/End Date** | ✅ Yes | ✅ **PORTED (Phase 1)** | ✅ Duplicate |
| **Deadline Scheduler** | ✅ Yes (GENIUS!) | ✅ **PORTED (Phase 2)** | ✅ Duplicate |
| **Playlist Management** | ✅ Yes | ✅ **PORTED (Phase 2)** | ✅ Duplicate |
| **Shuffle Mode** | ✅ Yes | ✅ **PORTED (Phase 1)** | ✅ Duplicate |
| **is_enabled Flag** | ✅ Yes | ✅ **PORTED (Phase 1)** | ✅ Duplicate |
| **REST API v1/v2** | ✅ Yes | ✅ Yes (FastAPI) | ✅ Duplicate |

### Features Backend HAS (That Anthias DOESN'T)

| Feature | Backend | Anthias | Winner |
|---------|---------|---------|--------|
| **Device Management** | ✅ Yes | ❌ No | Backend Only |
| **Tag System** | ✅ Yes | ❌ No | Backend Only |
| **WebOS TV Support** | ✅ Yes | ❌ No | Backend Only |
| **Activity Logging** | ✅ Yes | ❌ No | Backend Only |
| **Template Variables** | ✅ Yes (Phase 4.1) | ❌ No | Backend Only |
| **Multi-Language** | ✅ Yes (Phase 4.2) | ❌ No | Backend Only |
| **Device Commands** | ✅ Yes (Phase 4.3) | ❌ No | Backend Only |
| **Analytics Dashboard** | ✅ Yes (Phase 4.4) | ❌ No | Backend Only |
| **HLS Streaming** | ✅ Yes (Phase 3) | ❌ No | Backend Only |
| **H.265 Transcoding** | ✅ Yes (Phase 3) | ❌ No | Backend Only |

---

## Architecture Options

### Option 1: Hapus Anthias Sepenuhnya ❌ NOT RECOMMENDED

```
┌─────────────────────────────────────────┐
│           BACKEND ONLY                  │
│  ┌──────────────────────────────────┐   │
│  │ FastAPI Backend                  │   │
│  │  • All APIs                      │   │
│  │  • Scheduling                    │   │
│  │  • File Storage (NEW!)           │   │
│  │  • Device Management             │   │
│  │  • Analytics                     │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │ PostgreSQL Database              │   │
│  │  • Content metadata              │   │
│  │  • File paths                    │   │
│  │  • All data                      │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │ File Storage                     │   │
│  │  /data/content/                  │   │
│  │  • images/                       │   │
│  │  • videos/                       │   │
│  │  • hls/                          │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Pros:**
- ✅ Single source of truth
- ✅ No duplication
- ✅ Simpler architecture
- ✅ One codebase to maintain

**Cons:**
- ❌ Need to implement file storage in backend
- ❌ Need to migrate existing files
- ❌ Lose Anthias proven file management
- ❌ More development time (2-3 weeks)

**Effort:** 🔴 HIGH (2-3 weeks)

---

### Option 2: Keep Anthias as Minimal Storage Service ✅ RECOMMENDED

```
┌───────────────────────────────────────────────────────────┐
│                      BACKEND                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │ FastAPI Backend (Control Plane)                    │   │
│  │  • All APIs                                        │   │
│  │  • Scheduling (NEW - Phase 2)                     │   │
│  │  • Playlist Management (NEW - Phase 2)            │   │
│  │  • Device Management                              │   │
│  │  • Templates (NEW - Phase 4.1)                    │   │
│  │  • Multi-language (NEW - Phase 4.2)               │   │
│  │  • Commands (NEW - Phase 4.3)                     │   │
│  │  • Analytics (NEW - Phase 4.4)                    │   │
│  │                                                    │   │
│  │  File Operations via Anthias API:                 │   │
│  │  • POST /anthias/api/assets (upload)              │   │
│  │  • GET  /anthias/api/assets/{id} (download)       │   │
│  │  • GET  /anthias/assets/{filename} (serve)        │   │
│  └────────────────────────────────────────────────────┘   │
│                          │                                 │
│                          │ HTTP API Calls                  │
│                          ▼                                 │
└──────────────────────────┼─────────────────────────────────┘
                           │
┌──────────────────────────┼─────────────────────────────────┐
│                   ANTHIAS (Storage Layer)                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Minimal Anthias (File Storage ONLY)               │   │
│  │                                                    │   │
│  │ KEEP:                                              │   │
│  │  ✅ File upload/download API                      │   │
│  │  ✅ File serving                                  │   │
│  │  ✅ MD5 checksum calculation                      │   │
│  │  ✅ Basic asset model (id, uri, md5)              │   │
│  │  ✅ File validation                               │   │
│  │                                                    │   │
│  │ REMOVE:                                            │   │
│  │  ❌ Scheduler logic                               │   │
│  │  ❌ Playlist management                           │   │
│  │  ❌ Web UI (static/)                              │   │
│  │  ❌ Django templates                              │   │
│  │  ❌ Celery background jobs                        │   │
│  │  ❌ Viewer player                                 │   │
│  │  ❌ Device detection                              │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ File Storage                                       │   │
│  │  /data/screenly_assets/                            │   │
│  │  • original files                                  │   │
│  │  • checksums                                       │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Backend handles all business logic
- ✅ Anthias proven file storage (stable, tested)
- ✅ Clear separation of concerns
- ✅ No file migration needed
- ✅ Quick to implement (1-2 days)

**Cons:**
- ⚠️ Two services to maintain (but Anthias is minimal)
- ⚠️ Network latency (backend → Anthias API calls)

**Effort:** 🟢 LOW (1-2 days)

---

### Option 3: Keep Both Full Systems ❌ NOT RECOMMENDED

```
┌────────────────────────┐    ┌────────────────────────┐
│   BACKEND (Full)       │    │  ANTHIAS (Full)        │
│  • Everything          │    │  • Everything          │
│  • Duplicate logic     │    │  • Duplicate logic     │
└────────────────────────┘    └────────────────────────┘
           ↓                              ↓
        CONFUSION & DUPLICATION
```

**Pros:**
- ✅ Both work independently

**Cons:**
- ❌ Massive duplication
- ❌ Confusion: which system to use?
- ❌ Maintenance nightmare
- ❌ Data inconsistency risk

**Effort:** 🔴 MAINTENANCE HELL

---

## Detailed Analysis: What to Keep/Remove

### From Anthias - Files to KEEP

```
anthias/
├── anthias_app/
│   └── models.py                    ← KEEP (Asset model for storage)
├── api/
│   └── views/
│       └── v2.py                    ← KEEP (File upload/download only)
├── manage.py                        ← KEEP (Django management)
├── settings.py                      ← KEEP (Minimal config)
├── docker/
│   └── Dockerfile                   ← KEEP (Minimal container)
└── requirements/
    └── base.txt                     ← KEEP (Minimal deps)
```

**Total:** ~500 lines (down from ~10,000 lines)

---

### From Anthias - Files to REMOVE

```
anthias/
├── viewer/
│   ├── scheduling.py                ❌ REMOVE (Backend has Phase 2)
│   ├── playback.py                  ❌ REMOVE (Not needed)
│   ├── media_player.py              ❌ REMOVE (Not needed)
│   └── __init__.py                  ❌ REMOVE (Full player)
├── static/
│   └── (entire web UI)              ❌ REMOVE (Use web-admin)
├── templates/
│   └── (Django HTML)                ❌ REMOVE (Use web-admin)
├── celery_tasks.py                  ❌ REMOVE (No background jobs)
├── ansible/                         ❌ REMOVE (Pi provisioning)
├── raspberry_pi_imager/             ❌ REMOVE (Pi tools)
├── webview/                         ❌ REMOVE (Mobile wrapper)
├── websocket_server_layer.py        ❌ REMOVE (Not needed)
└── website/                         ❌ REMOVE (Documentation)
```

**Remove:** ~9,500 lines (95% of Anthias!)

---

## Implementation Plan for Option 2 (Recommended)

### Phase 1: Create Minimal Anthias (1 day)

**Step 1.1: Create new branch**
```bash
cd /mnt/g/khoirul/signate/anthias
git checkout -b minimal-storage-service
```

**Step 1.2: Remove unnecessary files**
```bash
# Remove viewer player
rm -rf viewer/

# Remove web UI
rm -rf static/ templates/ website/

# Remove platform-specific
rm -rf ansible/ raspberry_pi_imager/ webview/

# Remove background jobs
rm celery_tasks.py websocket_server_layer.py

# Remove dev tools
rm -rf webpack*.js package*.json tsconfig*.json
```

**Step 1.3: Create minimal API (anthias/api/views/storage.py)**
```python
"""
Minimal Storage API
Only handles file upload/download/serve
"""

from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from anthias_app.models import Asset
import hashlib
import os

@require_http_methods(["POST"])
def upload_file(request):
    """Upload file and return asset info"""
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    # Calculate MD5
    md5_hash = hashlib.md5(file.read()).hexdigest()
    file.seek(0)  # Reset file pointer

    # Save file
    asset_id = generate_unique_id()
    file_path = f'/data/screenly_assets/{asset_id}_{file.name}'

    with open(file_path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)

    # Create asset record
    asset = Asset.objects.create(
        asset_id=asset_id,
        name=file.name,
        uri=file_path,
        md5=md5_hash,
        mimetype=file.content_type
    )

    return JsonResponse({
        'asset_id': asset_id,
        'uri': file_path,
        'md5': md5_hash,
        'size': file.size
    })

@require_http_methods(["GET"])
def serve_file(request, asset_id):
    """Serve file by asset ID"""
    try:
        asset = Asset.objects.get(asset_id=asset_id)
        return FileResponse(open(asset.uri, 'rb'))
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)

@require_http_methods(["DELETE"])
def delete_file(request, asset_id):
    """Delete file"""
    try:
        asset = Asset.objects.get(asset_id=asset_id)
        os.remove(asset.uri)
        asset.delete()
        return JsonResponse({'success': True})
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)
```

**Step 1.4: Update Dockerfile (minimal)**
```dockerfile
FROM python:3.9-slim

# Minimal dependencies
RUN pip install django==4.2 psycopg2-binary gunicorn

WORKDIR /app
COPY anthias_app/ /app/anthias_app/
COPY api/ /app/api/
COPY manage.py settings.py /app/

# Storage volume
VOLUME /data/screenly_assets

EXPOSE 8000
CMD ["gunicorn", "anthias.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

### Phase 2: Update Backend to Use Minimal Anthias (4 hours)

**Step 2.1: Update backend content.py**
```python
# backend/app/api/content.py

import aiohttp
from app.core.config import settings

ANTHIAS_URL = settings.ANTHIAS_URL  # http://anthias:8000

@router.post("/upload")
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    duration: int = Form(10)
):
    """Upload content via Anthias storage API"""

    # Upload to Anthias
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('file', file.file, filename=file.filename)

        async with session.post(f"{ANTHIAS_URL}/api/storage/upload", data=data) as resp:
            anthias_response = await resp.json()

    # Create content record in our database
    content = Content(
        title=title,
        asset_id=anthias_response['asset_id'],  # Reference to Anthias
        file_path=anthias_response['uri'],
        md5_checksum=anthias_response['md5'],
        duration=duration,
        # ... other fields from Phase 1
    )
    db.add(content)
    await db.commit()

    return {"id": content.id, "asset_id": anthias_response['asset_id']}

@router.get("/{content_id}/file")
async def serve_content_file(content_id: int):
    """Serve file via Anthias"""
    content = await db.get(Content, content_id)

    # Proxy to Anthias
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{ANTHIAS_URL}/api/storage/serve/{content.asset_id}") as resp:
            return StreamingResponse(
                resp.content.iter_chunked(8192),
                media_type=content.content_type
            )
```

**Step 2.2: Update docker-compose.yml**
```yaml
version: '3.8'

services:
  backend-api:
    build: ./backend
    ports:
      - "8001:8000"
    environment:
      - ANTHIAS_URL=http://anthias:8000
    depends_on:
      - postgres
      - anthias

  anthias:
    build: ./anthias
    ports:
      - "8000:8000"
    volumes:
      - ./data/screenly_assets:/data/screenly_assets
    environment:
      - MINIMAL_MODE=true

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

---

### Phase 3: Testing (2 hours)

**Test Cases:**
```bash
# 1. Upload file via backend
curl -X POST http://localhost:8001/api/content/upload \
  -F "file=@test.mp4" \
  -F "title=Test Video" \
  -F "duration=30"

# Response:
# {
#   "id": 123,
#   "asset_id": "abc-def-ghi",
#   "file_path": "/data/screenly_assets/abc-def-ghi_test.mp4"
# }

# 2. Serve file via backend
curl http://localhost:8001/api/content/123/file

# 3. Verify Anthias only has minimal API
curl http://localhost:8000/api/storage/health
# Should return: {"status": "ok", "mode": "minimal"}

# 4. Verify web-admin works
# Open http://localhost:3000
# Upload content → Should work via backend → Anthias
```

---

## Data Migration (If Needed)

If you have existing Anthias data to migrate:

```python
# migration_script.py

"""
Migrate existing Anthias assets to Backend
"""

import requests
from app.models import Content
from anthias_app.models import Asset

def migrate_assets():
    """Migrate all Anthias assets to Backend content table"""

    anthias_assets = Asset.objects.all()

    for asset in anthias_assets:
        # Create corresponding content in backend
        content = Content(
            title=asset.name,
            asset_id=asset.asset_id,
            file_path=asset.uri,
            md5_checksum=asset.md5,
            content_type=asset.mimetype,
            duration=asset.duration or 10,
            is_active=asset.is_enabled,
            # Map other fields
        )
        db.add(content)

    db.commit()
    print(f"Migrated {len(anthias_assets)} assets")

if __name__ == "__main__":
    migrate_assets()
```

---

## Final Architecture Diagram (Option 2)

```
┌─────────────────────────────────────────────────────────────┐
│                         VIEWER                              │
│  (Browser/WebOS TV on port 8080)                            │
│                                                             │
│  Gets playlist from Backend API                             │
│  Downloads media files from Anthias                         │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ API Calls
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    WEB-ADMIN                                │
│  (React App on port 3000)                                   │
│                                                             │
│  • Upload content → Backend API → Anthias                   │
│  • Manage schedules → Backend API                           │
│  • Device management → Backend API                          │
│  • Templates, translations → Backend API                    │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ REST API
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              BACKEND API (FastAPI - Port 8001)              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Business Logic Layer                                │   │
│  │  • Content management                               │   │
│  │  • Scheduler (Phase 2)                              │   │
│  │  • Playlist manager (Phase 2)                       │   │
│  │  • Device management                                │   │
│  │  • Templates (Phase 4.1)                            │   │
│  │  • Multi-language (Phase 4.2)                       │   │
│  │  • Commands (Phase 4.3)                             │   │
│  │  • Analytics (Phase 4.4)                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          │ HTTP API Calls                   │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Anthias Client                                      │   │
│  │  • POST /api/storage/upload (file)                  │   │
│  │  • GET  /api/storage/serve/{id} (file)              │   │
│  │  • DELETE /api/storage/{id} (file)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PostgreSQL Database                                 │   │
│  │  • contents (with asset_id reference)               │   │
│  │  • devices                                          │   │
│  │  • playlists                                        │   │
│  │  • assignments                                      │   │
│  │  • templates                                        │   │
│  │  • translations                                     │   │
│  │  • analytics                                        │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ HTTP API
                    ▼
┌─────────────────────────────────────────────────────────────┐
│           ANTHIAS (Minimal Storage - Port 8000)             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Minimal Storage API                                 │   │
│  │  ✅ /api/storage/upload   (file upload)            │   │
│  │  ✅ /api/storage/serve/{id} (file serving)         │   │
│  │  ✅ /api/storage/{id}     (delete file)            │   │
│  │  ✅ /api/storage/health   (health check)           │   │
│  │                                                     │   │
│  │  ❌ NO scheduler logic                             │   │
│  │  ❌ NO playlist management                         │   │
│  │  ❌ NO web UI                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Minimal Asset Model                                 │   │
│  │  • asset_id (reference only)                        │   │
│  │  • file_path                                        │   │
│  │  • md5_checksum                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ File Storage                                        │   │
│  │  /data/screenly_assets/                             │   │
│  │  • abc-123_video1.mp4                               │   │
│  │  • def-456_image1.jpg                               │   │
│  │  • ghi-789_video2.mp4                               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Decision Matrix

| Criteria | Option 1: No Anthias | Option 2: Minimal Anthias | Option 3: Both Full |
|----------|---------------------|---------------------------|---------------------|
| **Development Time** | 🔴 2-3 weeks | 🟢 1-2 days | 🟡 0 days |
| **Maintenance** | 🟢 One codebase | 🟡 Two services | 🔴 Two full systems |
| **Stability** | 🔴 New file storage | 🟢 Proven storage | 🟢 Both proven |
| **Migration Needed** | 🔴 Yes, complex | 🟢 No | 🟢 No |
| **Duplication** | 🟢 None | 🟡 Minimal | 🔴 Massive |
| **Performance** | 🟢 Direct | 🟡 HTTP overhead | 🟡 Confusing |
| **Clarity** | 🟢 Very clear | 🟢 Clear | 🔴 Confusing |

**Winner:** 🏆 **Option 2 - Minimal Anthias**

---

## Recommendation Summary

### ✅ DO THIS (Option 2)

1. **Keep Anthias** as minimal file storage service:
   - Only 4 API endpoints (upload, serve, delete, health)
   - ~500 lines of code (95% reduction)
   - Proven file storage
   - No migration needed

2. **Remove from Anthias:**
   - ❌ Scheduler logic → Backend has Phase 2
   - ❌ Playlist management → Backend has Phase 2
   - ❌ Web UI → Use web-admin
   - ❌ Celery jobs → Not needed
   - ❌ Viewer player → Have own viewer
   - ❌ All platform-specific code

3. **Backend becomes** the single control plane:
   - ✅ All business logic
   - ✅ All APIs for web-admin
   - ✅ Scheduling (Phase 2)
   - ✅ Templates (Phase 4.1)
   - ✅ Multi-language (Phase 4.2)
   - ✅ Commands (Phase 4.3)
   - ✅ Analytics (Phase 4.4)
   - ✅ Calls Anthias only for file ops

### ❌ DON'T DO THIS

- ❌ Option 1: Too much work, risky migration
- ❌ Option 3: Duplication hell, maintenance nightmare

---

## Implementation Timeline

| Phase | Task | Effort | Status |
|-------|------|--------|--------|
| **Phase 1** | Create minimal Anthias | 1 day | ⏳ Pending |
| **Phase 2** | Update backend integration | 4 hours | ⏳ Pending |
| **Phase 3** | Testing | 2 hours | ⏳ Pending |
| **Phase 4** | Deploy to production | 2 hours | ⏳ Pending |
| **TOTAL** | | **2 days** | ⏳ Ready to start |

---

## Conclusion

**🎯 Final Answer:**

**Dari Anthias, HAPUS 95% (9,500 baris), KEEP 5% (500 baris)**

**KEEP:**
- ✅ File upload/download API (4 endpoints)
- ✅ Basic Asset model (id, uri, md5)
- ✅ File storage directory

**REMOVE:**
- ❌ viewer/ (entire player)
- ❌ static/ (web UI)
- ❌ templates/ (Django HTML)
- ❌ celery_tasks.py (background jobs)
- ❌ ansible/, raspberry_pi_imager/ (platform-specific)
- ❌ webview/ (mobile wrapper)
- ❌ websocket_server_layer.py

**Backend menjadi:**
- ✅ Single source of truth untuk business logic
- ✅ All features dari Phase 1-4.4
- ✅ Calls Anthias HANYA untuk file storage

**Arsitektur akhir:**
```
Backend (Control Plane) → Anthias (Storage Only) → Files
        ↑                                            ↓
   Web-Admin                                      Viewer
```

Clean, simple, maintainable! 🚀

---

**Created:** October 28, 2025
**Decision:** Option 2 - Minimal Anthias Storage Service
**Status:** Ready for Implementation
