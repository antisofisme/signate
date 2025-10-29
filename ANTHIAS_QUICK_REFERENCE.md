# ANTHIAS QUICK REFERENCE

## What is Anthias?
**Digital Signage CMS** - Stores and serves image/video files for display on TV monitors.

## What We Use It For
- Upload images and videos
- Store asset metadata (name, duration, size)
- Serve files via REST API to our viewer application
- **That's it** - we use only 10% of Anthias features

## Integration Points

### Backend API
```
/backend/app/services/anthias_service.py (484 lines)
├── upload_asset(file, name, duration) → Returns {asset_id, uri}
├── get_asset(asset_id) → Returns asset metadata
├── delete_asset(asset_id) → Deletes from Anthias
├── update_asset(asset_id, name, duration)
├── get_asset_url(asset_id) → Returns public URL
├── get_asset_content(asset_id) → Returns file bytes
└── list_assets() → All assets
```

### REST Endpoints We Use
```
POST   /api/v1/file_asset         ← Upload file first
POST   /api/v1/assets             ← Create asset with URI
GET    /api/v1/assets             ← List all
GET    /api/v1/assets/{id}        ← Get one
PUT    /api/v1/assets/{id}        ← Update
DELETE /api/v1/assets/{id}        ← Delete
GET    /api/v1/assets/{id}/content ← Download file
```

## Configuration
```
.env:
  ANTHIAS_API_URL=http://192.168.5.12:8000
  ANTHIAS_INTERNAL_URL=http://anthias-nginx (for Docker)
  ANTHIAS_PUBLIC_URL=http://192.168.5.12:8000
```

## Database
- **Type**: SQLite (at `/data/.screenly/screenly.db`)
- **Table**: `assets` (only one!)
  ```
  asset_id → UUID (primary key)
  name → filename
  uri → file path
  duration → seconds
  mimetype → image/jpeg, video/mp4, etc
  is_enabled → 0/1
  md5 → file hash
  ```

## Docker Services
```
anthias-server      → Main application (port 8000)
anthias-celery      → Background tasks
anthias-websocket   → Real-time updates (NOT USED)
anthias-nginx       → Reverse proxy (port 8000)
redis               → Cache & message broker (port 6379)
```

## Features We DO Use
- Asset CRUD (Create, Read, Update, Delete)
- File upload with metadata
- Asset listing and filtering
- URL-based file serving

## Features We DON'T Use
- Device management (we use PostgreSQL)
- Scheduling (we use Playlists)
- Backup/recovery
- WebSocket real-time updates
- Built-in viewer (we have our own)
- Ansible deployment
- Raspberry Pi imager

## Code Statistics
- **Total Size**: 6.2 MB
- **Python Files**: 128 (~7,961 lines)
- **JavaScript Files**: 61 (~101 lines)
- **Critical Files**: ~20 (api/views/v1.py, models.py, docker configs)

## Where Anthias is Referenced
```
backend/
├── app/services/anthias_service.py ← Main integration
├── app/api/content.py ← Upload endpoint
├── app/core/config.py ← Config
└── app/models/content.py ← Stores anthias_url

web-admin/
├── src/components/content/* ← Preview video/image
└── src/types/api.ts ← API types

docker/
└── docker-compose.yml ← Service definitions
```

## Simple Workflow

```
User uploads file in Web Admin
  ↓
/backend/api/content/upload (POST)
  ↓
anthias_service.upload_asset(file)
  ↓
1. POST to /api/v1/file_asset (get URI)
2. POST to /api/v1/assets with URI
  ↓
Store anthias_url + anthias_asset_id in PostgreSQL
  ↓
Viewer fetches from backend
  ↓
Backend serves from Anthias (proxied via /content/{id}/image|video)
```

## Critical Dependencies

| Component | Why | Can Replace? |
|-----------|-----|--------------|
| Anthias API v1 | File upload/storage | Yes (use S3/MinIO) |
| SQLite DB | Asset metadata | Maybe (use our PostgreSQL) |
| Redis | Cache/messaging | No (needed by Celery) |
| Nginx | Reverse proxy | Maybe (use AWS ALB) |
| Celery | Background tasks | No (needed by Anthias) |

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Anthias crash | Medium | Has restart policies, but lost files |
| Single point of failure | High | Backup volumes, consider S3 |
| Complex for what we use | Medium | Create minimal fork |
| Tight coupling | Low | Already abstracted in service |

## What Can Be Safely Deleted

From `/anthias/`:
- `/webview/` - Qt desktop app (not used)
- `/static/src/` - React frontend (we have web-admin)
- `/viewer/` - Python viewer module (we have separate viewer)
- `/api/urls/v1_1.py, v1_2.py, v2.py` - Old API versions
- `/ansible/` - Not using for deployment
- `/raspberry_pi_imager/` - Not building custom images

**Potential savings**: ~30% codebase reduction, -40% build time

## Future Improvements

### Short-term (keep as-is)
- Currently working fine
- No changes needed

### Medium-term (evaluate alternatives)
1. **MinIO** - Lighter weight S3 clone
2. **Direct S3** - AWS S3 for files, PostgreSQL for metadata
3. **Minimal fork** - Keep only v1 API endpoints

### Long-term (if replacing)
Plan data migration:
1. Export all asset references from PostgreSQL
2. Migrate files to new storage (S3/MinIO)
3. Update database URIs
4. Update code to use new service

## Troubleshooting

### "Cannot connect to Anthias"
- Check `docker ps` - is `anthias-nginx` running?
- Check `/docker/docker-compose.yml` volumes mounted?
- Check `.env` - `ANTHIAS_API_URL` correct?

### "File upload fails"
- Check Anthias disk space: `docker exec anthias-server du -sh /data/screenly_assets`
- Check file size < max upload (usually 1-2 GB)
- Check file type is image or video

### "Asset shows in Anthias but not in our app"
- Database row exists but `anthias_asset_id` is NULL?
- Check upload process completed both steps
- Check API response in logs

## Commands Reference

```bash
# Check Anthias status
docker ps | grep anthias

# View Anthias logs
docker logs anthias-server -f

# List uploaded assets in Anthias
curl http://192.168.5.12:8000/api/v1/assets | jq

# Count assets in our DB
psql -c "SELECT COUNT(*) FROM content"

# Test Anthias API
curl -X GET http://192.168.5.12:8000/api/v1/assets?limit=1 | jq '.[] | {asset_id, name, uri}'

# Check disk space
docker exec anthias-server du -sh /data/screenly_assets
```

