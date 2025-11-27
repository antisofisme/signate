# Anthias Minimal Storage Service

## What is This?

This is a **minimized version** of Anthias (formerly Screenly OSE) that serves **ONLY** as a file storage service.

**All business logic** (scheduling, playlists, device management) has been **moved to the Backend** (FastAPI at port 8001).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Digital Signage System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │ Web Admin    │─────▶│   Backend    │─────▶│  Anthias  │ │
│  │ (React)      │      │   (FastAPI)  │      │  Storage  │ │
│  │ Port 3000    │      │   Port 8001  │      │  Service  │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│                               │                      │       │
│                               ▼                      ▼       │
│                        ┌──────────────┐      ┌───────────┐ │
│                        │  PostgreSQL  │      │   Files   │ │
│                        │  Port 5433   │      │   /data/  │ │
│                        └──────────────┘      └───────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## What Was Removed (95% of code)

### Removed Components
- ❌ **Viewer player** (we have separate viewer at `/viewer`)
- ❌ **Scheduler logic** (moved to Backend Phase 2)
- ❌ **Playlist management** (moved to Backend Phase 2)
- ❌ **Web UI** (using web-admin instead)
- ❌ **Background jobs** (Celery, Redis)
- ❌ **Platform-specific code** (Raspberry Pi, Balena, Ansible)
- ❌ **WebSocket server** (moved to Backend)
- ❌ **ZMQ messaging** (not needed)
- ❌ **Authentication system** (Backend handles this)
- ❌ **Admin panel** (Backend handles this)
- ❌ **API versioning** (v1, v1.1, v1.2, v2 - all removed)
- ❌ **Static files serving** (not needed)
- ❌ **Template rendering** (not needed)
- ❌ **Test infrastructure** (Backend has tests)

### Removed Dependencies
- celery, redis (background jobs)
- pyzmq (ZMQ messaging)
- gevent, gevent-websocket (WebSocket server)
- djangorestframework, drf-spectacular (API docs)
- django-dbbackup (backups)
- psutil, netifaces (system info)
- pydbus, cec (hardware control)
- yt-dlp (video download)
- And many more...

## What Remains (5% of code)

### Core Components
- ✅ **File upload API** - Upload files and calculate MD5
- ✅ **File serving API** - Serve files by asset ID
- ✅ **File deletion API** - Delete files from disk
- ✅ **Asset metadata storage** - Minimal Asset model in SQLite
- ✅ **Health check** - Service status endpoint

### Minimal Asset Model
Only stores essential file metadata:
- `asset_id` - Unique UUID
- `name` - Original filename
- `uri` - File path on disk
- `md5` - MD5 checksum
- `mimetype` - MIME type
- `created_at` - Upload timestamp
- `updated_at` - Last modified timestamp

**Removed fields** (Backend handles these):
- `start_date`, `end_date` - Scheduling
- `duration` - Content metadata
- `is_enabled`, `is_processing` - Status flags
- `play_order` - Playlist ordering
- `nocache`, `skip_asset_check` - Playback flags

## API Endpoints

### Base URL
```
http://192.168.5.12:8000/api/storage/
```

### 1. Upload File
```bash
POST /api/storage/upload
Content-Type: multipart/form-data

# Upload file
curl -X POST http://192.168.5.12:8000/api/storage/upload \
  -F "file=@video.mp4"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "asset_id": "a1b2c3d4e5f6...",
    "uri": "/data/screenly_assets/a1b2c3d4_video.mp4",
    "md5": "d41d8cd98f00b204e9800998ecf8427e",
    "size": 12345678,
    "mimetype": "video/mp4"
  }
}
```

### 2. Serve File
```bash
GET /api/storage/serve/{asset_id}

# Serve file
curl http://192.168.5.12:8000/api/storage/serve/a1b2c3d4e5f6...
```

**Returns:** File content with appropriate Content-Type

### 3. Get Asset Info
```bash
GET /api/storage/{asset_id}

# Get metadata
curl http://192.168.5.12:8000/api/storage/a1b2c3d4e5f6...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "asset_id": "a1b2c3d4e5f6...",
    "name": "video.mp4",
    "uri": "/data/screenly_assets/a1b2c3d4_video.mp4",
    "md5": "d41d8cd98f00b204e9800998ecf8427e",
    "mimetype": "video/mp4"
  }
}
```

### 4. Delete File
```bash
DELETE /api/storage/{asset_id}

# Delete file
curl -X DELETE http://192.168.5.12:8000/api/storage/a1b2c3d4e5f6...
```

**Response:**
```json
{
  "success": true
}
```

### 5. Health Check
```bash
GET /api/storage/health

# Check service status
curl http://192.168.5.12:8000/api/storage/health
```

**Response:**
```json
{
  "status": "ok",
  "mode": "minimal_storage",
  "version": "1.0",
  "storage_path": "/data/screenly_assets",
  "storage_exists": true
}
```

## Usage

### ⚠️ IMPORTANT
**This service should ONLY be called by the Backend API (port 8001), NOT directly by clients.**

The Backend handles all business logic and calls Anthias only for file operations.

### Typical Flow
```
1. Web Admin uploads file → Backend validates
2. Backend calls Anthias → Upload file to /data/screenly_assets
3. Anthias returns asset_id + MD5
4. Backend stores metadata in PostgreSQL (with scheduling, playlist info)
5. Viewer requests content → Backend decides what to play
6. Backend returns asset URLs → Viewer fetches from Anthias
```

## Installation

### 1. Install Dependencies
```bash
cd /mnt/g/khoirul/signate/anthias
pip install -r requirements/requirements.minimal.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Start Service
```bash
# Development
python manage.py runserver 0.0.0.0:8000

# Production (with Gunicorn)
gunicorn anthias_django.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120
```

### 4. Verify
```bash
curl http://localhost:8000/api/storage/health
```

## Configuration

### Environment Variables
```bash
# Django secret key (auto-generated if not set)
DJANGO_SECRET_KEY=your-secret-key

# Environment (development, production)
ENVIRONMENT=production

# Database path (SQLite)
# Default: /data/.screenly/screenly.db
```

### Storage Path
Files are stored at: `/data/screenly_assets/`

Format: `{asset_id}_{original_filename}`

Example: `a1b2c3d4e5f6_video.mp4`

## Code Reduction Summary

### Before Minimization
- **Total files**: 172 files
- **Python files**: 83 files
- **Python LOC**: 7,697 lines
- **Size**: 3.8 MB
- **Dependencies**: 38+ packages

### After Minimization
- **Total files**: ~30 files (82% reduction)
- **Python files**: ~15 files (82% reduction)
- **Python LOC**: ~500 lines (93% reduction)
- **Size**: ~200 KB (95% reduction)
- **Dependencies**: 3 packages (92% reduction)

## Migration from Full Anthias

If you were using full Anthias:

1. **Scheduling** → Use Backend's scheduler service
2. **Playlists** → Use Backend's playlist management
3. **Device management** → Use Backend's device API
4. **Web UI** → Use web-admin (React)
5. **API calls** → Update to use Backend API (port 8001)

## Development

### Project Structure
```
anthias/
├── anthias_app/              # Django app
│   ├── models.py            # Minimal Asset model
│   └── migrations/          # Database migrations
├── anthias_django/          # Django config
│   ├── settings.py          # Simplified settings
│   └── urls.py              # Minimal URLs
├── api/                     # Storage API
│   ├── storage.py           # API endpoints
│   └── urls/
│       └── storage.py       # URL routing
├── requirements/
│   └── requirements.minimal.txt  # 3 dependencies
├── manage.py                # Django management
└── MINIMAL_STORAGE_README.md     # This file
```

### Adding New Endpoints

1. Add function to `api/storage.py`
2. Add URL pattern to `api/urls/storage.py`
3. Test with curl
4. Update Backend to use new endpoint

### Database Schema

The Asset model uses SQLite with this schema:

```sql
CREATE TABLE assets (
    asset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    uri TEXT NOT NULL,
    md5 TEXT,
    mimetype TEXT DEFAULT 'application/octet-stream',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Troubleshooting

### Service won't start
```bash
# Check Python dependencies
pip list

# Check database
python manage.py migrate

# Check permissions
ls -la /data/screenly_assets
```

### Upload fails
```bash
# Check storage directory exists
mkdir -p /data/screenly_assets
chmod 777 /data/screenly_assets

# Check disk space
df -h /data
```

### File not found
```bash
# Verify file exists
ls -la /data/screenly_assets/

# Check database record
python manage.py shell
>>> from anthias_app.models import Asset
>>> Asset.objects.all()
```

## License

Same as original Anthias (formerly Screenly OSE)

## Related Documentation

- **Backend API**: `/mnt/g/khoirul/signate/backend/README.md`
- **Web Admin**: `/mnt/g/khoirul/signate/web-admin/README.md`
- **Viewer**: `/mnt/g/khoirul/signate/viewer/README.md`
- **Original Anthias**: `ANTHIAS_ORIGINAL_README.md`

## Version

**Minimal Storage Service v1.0**

Based on: Anthias (formerly Screenly OSE)
Minimized for: Digital Signage System by Signate
