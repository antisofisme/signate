# COMPREHENSIVE ANTHIAS ANALYSIS REPORT

## Executive Summary

Anthias is the **open-source digital signage platform** that serves as the **primary asset storage and delivery system** for the Smart TV Digital Signage project. The system is divided into multiple specialized components, with our project currently using Anthias **primarily for file upload and asset delivery via REST API**.

**Current Status**: Anthias is running on the production server (192.168.5.12:8000) and provides essential file storage/delivery for our backend API.

---

## 1. DIRECTORY STRUCTURE

```
anthias/ (6.2 MB total)
├── Core Application
│   ├── anthias_app/              ← Main Django app (web UI, models)
│   │   ├── admin.py              ← Django admin configuration
│   │   ├── apps.py               ← Django app config
│   │   ├── models.py             ← Database models (Asset)
│   │   ├── views.py              ← Web views (login, splash page)
│   │   ├── urls.py               ← Web routing
│   │   ├── helpers.py            ← Helper functions
│   │   ├── management/commands/  ← Django management commands
│   │   └── migrations/           ← Database migration files
│   │
│   ├── anthias_django/           ← Django project settings
│   │   ├── settings.py           ← Django configuration
│   │   ├── urls.py               ← URL routing (combines anthias_app + api)
│   │   ├── wsgi.py               ← WSGI entry point
│   │   └── asgi.py               ← ASGI entry point
│   │
│   ├── api/                      ← REST API (USED BY OUR BACKEND)
│   │   ├── views/                ← API endpoint handlers
│   │   │   ├── v1.py             ← Version 1 endpoints
│   │   │   ├── v1_1.py           ← Version 1.1 endpoints
│   │   │   ├── v1_2.py           ← Version 1.2 endpoints
│   │   │   ├── v2.py             ← Version 2 endpoints
│   │   │   └── mixins.py         ← Reusable view mixins
│   │   ├── urls/                 ← URL routing per version
│   │   │   ├── v1.py
│   │   │   ├── v1_1.py
│   │   │   ├── v1_2.py
│   │   │   └── v2.py
│   │   ├── serializers/          ← Data serialization
│   │   │   ├── v1_1.py
│   │   │   ├── v1_2.py
│   │   │   ├── v2.py
│   │   │   └── mixins.py
│   │   ├── tests/                ← API tests
│   │   ├── admin.py              ← Django admin
│   │   ├── apps.py               ← Django app config
│   │   ├── errors.py             ← Error definitions
│   │   └── helpers.py            ← Helper functions
│   │
│   ├── viewer/                   ← HTML/JS Viewer (LEGACY - we use /viewer in root)
│   │   ├── __init__.py           ← Python module
│   │   ├── media_player.py       ← Media playback logic
│   │   ├── scheduling.py         ← Scheduling logic
│   │   ├── playback.py
│   │   ├── zmq.py                ← ZeroMQ messaging
│   │   ├── constants.py
│   │   └── utils.py
│   │
│   ├── webview/                  ← Qt-based WebView application (for Raspberry Pi)
│   │   ├── src/                  ← C++ source code
│   │   ├── Dockerfile            ← Container build
│   │   ├── build_qt5.sh           ← Build scripts
│   │   └── README.md
│   │
│   ├── static/src/               ← React Frontend Components
│   │   ├── components/           ← React components (61 JS/TS files)
│   │   ├── store/                ← Redux store
│   │   ├── types.ts              ← TypeScript type definitions
│   │   ├── constants.ts
│   │   └── tests/                ← Jest tests
│   │
│   ├── templates/                ← Django HTML templates
│   │
│   ├── lib/                      ← Utility libraries
│   │   ├── auth.py               ← Authentication
│   │   ├── backup_helper.py      ← Backup/restore
│   │   ├── device_helper.py      ← Device management
│   │   ├── diagnostics.py        ← System diagnostics
│   │   ├── github.py             ← GitHub integration
│   │   ├── utils.py              ← Utility functions
│   │   └── errors.py             ← Error classes
│   │
│   ├── docker/                   ← Docker configuration
│   │   ├── Dockerfile.base       ← Base image
│   │   ├── Dockerfile.server     ← Main server
│   │   ├── Dockerfile.celery     ← Celery worker
│   │   ├── Dockerfile.nginx      ← Nginx reverse proxy
│   │   ├── Dockerfile.websocket  ← WebSocket server
│   │   ├── Dockerfile.viewer     ← Viewer application
│   │   ├── nginx/                ← Nginx configuration
│   │   └── ...
│   │
│   ├── requirements/             ← Python dependencies
│   │   ├── requirements.txt
│   │   └── requirements.dev.txt
│   │
│   ├── tests/                    ← Test suite
│   │   ├── test_app.py
│   │   ├── test_backup_helper.py
│   │   ├── test_celery_tasks.py
│   │   ├── test_scheduler.py
│   │   ├── test_settings.py
│   │   ├── test_updates.py
│   │   ├── test_utils.py
│   │   └── assets/               ← Test fixtures
│   │
│   ├── tools/                    ← Utility tools
│   │   └── image_builder/        ← Image building tools for Raspberry Pi
│   │
│   ├── ansible/                  ← Ansible playbooks (deployment)
│   │   └── roles/                ← Ansible roles
│   │
│   ├── raspberry_pi_imager/      ← Raspberry Pi image builder
│   │
│   ├── website/                  ← Marketing website assets
│   │   └── assets/
│   │
├── Configuration Files
│   ├── manage.py                 ← Django management interface
│   ├── settings.py               ← Device settings (separate from Django)
│   ├── celery_tasks.py           ← Celery task definitions
│   ├── host_agent.py             ← Host agent script
│   ├── run_gunicorn.py           ← Gunicorn runner
│   ├── send_zmq_message.py       ← ZMQ messaging utility
│   │
│   ├── package.json              ← NPM dependencies (React/Webpack)
│   ├── pyproject.toml            ← Python project config
│   ├── docker-compose.yml.tmpl   ← Docker compose template
│   ├── docker-compose.dev.yml    ← Development compose
│   ├── docker-compose.test.yml   ← Test compose
│   ├── balena.yml                ← Balena cloud config
│   │
│   └── README files
│       ├── README.md
│       ├── ANTHIAS_ORIGINAL_README.md
│       ├── SIGNATE_README.md
│       ├── LICENSE
│       └── CONTRIBUTING.md
```

---

## 2. BUILD CONFIGURATION

### Python Build System
- **Package Manager**: Poetry (pyproject.toml)
- **Dependencies**: ~15-20 main packages (Flask, Celery, etc.)
- **Python Version**: 3.9+
- **Entry Points**: 
  - `manage.py` (Django CLI)
  - `run_gunicorn.py` (Web server)
  - `celery_tasks.py` (Async tasks)

### JavaScript Build System
- **Package Manager**: npm/webpack
- **Framework**: React 19 + Redux Toolkit
- **Build Tool**: Webpack with TypeScript support
- **Testing**: Jest
- **Linting**: ESLint + Prettier
- **Compiled to**: `/data/screenly/staticfiles/` in container

### Docker Build System
- **Base Image**: 12 different Dockerfiles for different components
- **Components**:
  1. `Dockerfile.base` - Base image with dependencies
  2. `Dockerfile.server` - Main Django/Gunicorn server
  3. `Dockerfile.celery` - Celery worker for background tasks
  4. `Dockerfile.nginx` - Nginx reverse proxy/load balancer
  5. `Dockerfile.websocket` - WebSocket server
  6. `Dockerfile.viewer` - HTML viewer application
  7. `Dockerfile.redis` - Redis cache
  8. And 5 more variant Dockerfiles
- **Orchestration**: Docker Compose (4 compose files + templates)

---

## 3. SERVICE ARCHITECTURE

Anthias runs as a **multi-container system**:

### Deployed Services (in our docker-compose.yml)

| Service | Image | Port | Purpose | Status |
|---------|-------|------|---------|--------|
| `anthias-server` | Dockerfile.server | 8000 | Main Django app | Running |
| `anthias-celery` | Dockerfile.celery | N/A | Background tasks | Running |
| `anthias-websocket` | Dockerfile.websocket | 8080 | Real-time updates | Running |
| `anthias-nginx` | Dockerfile.nginx | 8000 (external) | Reverse proxy + CORS | Running |
| `redis` | redis:7-alpine | 6379 | Cache & message broker | Running |

### Service Dependencies

```
nginx (port 8000)
├── → anthias-server (internal)
│   └── → redis
├── → anthias-websocket
│   └── → redis
└── → anthias-celery
    └── → redis
```

---

## 4. DATABASE SCHEMA

### Single Database Model

Anthias uses **SQLite by default** (production uses SQLite at `/data/.screenly/screenly.db`):

```
Asset (TABLE: assets)
├── asset_id (UUID, primary key)
├── name (text)
├── uri (text) - file path/URL
├── md5 (text) - file hash
├── start_date (datetime)
├── end_date (datetime)
├── duration (bigint) - seconds
├── mimetype (text)
├── is_enabled (boolean)
├── is_processing (boolean)
├── nocache (boolean)
├── play_order (integer)
└── skip_asset_check (boolean)
```

**Migrations**: 2 migrations exist in `/api/migrations/`

---

## 5. REST API ENDPOINTS (PROVIDED BY ANTHIAS)

### API Versions Supported
- **v1** (Basic) - USED BY OUR BACKEND
- **v1.1** (Improved)
- **v1.2** (Enhanced)
- **v2** (Latest)

### Key Endpoints Used by Our Backend

| Endpoint | Method | Purpose | Used |
|----------|--------|---------|------|
| `/api/v1/assets` | GET | List all assets | YES |
| `/api/v1/assets` | POST | Create asset | YES |
| `/api/v1/assets/{id}` | GET | Get asset details | YES |
| `/api/v1/assets/{id}` | PUT | Update asset | YES |
| `/api/v1/assets/{id}` | DELETE | Delete asset | YES |
| `/api/v1/assets/{id}/content` | GET | Get asset file content | YES |
| `/api/v1/file_asset` | POST | Upload file | YES |
| `/api/v1/backup` | POST/GET | Backup system | NO |
| `/api/v1/recover` | POST | Recover from backup | NO |
| `/api/v1/reboot` | POST | Reboot device | NO |
| `/api/v1/shutdown` | POST | Shutdown device | NO |
| `/api/v1/info` | GET | System information | NO |
| `/api/v1/viewer_current_asset` | GET | Current playing asset | NO |
| `/api/v1/assets/order` | GET/PUT | Playlist order | NO |
| `/api/v1/assets/control/{cmd}` | POST | Asset control commands | NO |

---

## 6. INTEGRATION WITH OUR CODEBASE

### Where Anthias is Used

#### Backend API (`/backend`)
- **Service**: `/backend/app/services/anthias_service.py` (484 lines)
  - `AnthiasService` class with methods:
    - `upload_asset()` - Upload image/video files
    - `list_assets()` - Get all assets
    - `get_asset()` - Get asset by ID
    - `delete_asset()` - Delete asset
    - `update_asset()` - Update asset metadata
    - `get_asset_url()` - Get public URL for asset
    - `get_asset_content()` - Get file content
    - `check_connection()` - Health check

- **Configuration**: `/backend/app/core/config.py`
  - `ANTHIAS_API_URL` = http://192.168.5.12:8000
  - `ANTHIAS_INTERNAL_URL` = http://anthias-nginx (for Docker)
  - `ANTHIAS_PUBLIC_URL` = http://192.168.5.12:8000
  - `ANTHIAS_API_KEY` = "" (not used)

- **Content API**: `/backend/app/api/content.py` (1147 lines)
  - Uploads files to Anthias first
  - Stores Anthias URL + asset_id in PostgreSQL
  - Uses `anthias_service.upload_asset()` for file upload
  - Proxies image/video via `/content/{id}/image` and `/content/{id}/video`

#### Web Admin (`/web-admin`)
- **Preview Modal**: `src/components/content/modals/PreviewModal.tsx`
- **Preview Player**: `src/components/preview/PreviewPlayer.tsx`
- **Content Pages**: `src/pages/Contents.tsx`
- **Type Definitions**: `src/types/api.ts`

**Note**: Web Admin doesn't directly upload to Anthias - it uses our Backend API which handles Anthias integration.

#### Database Migrations
- `/backend/scripts/backfill_metadata.py` - Downloads content from `content.anthias_url`

### Referenced in Configuration
- `/docker/docker-compose.yml` - Defines Anthias services
- `/.env` - Anthias URL configuration

---

## 7. CODE STATISTICS

### Anthias Source Code

| Type | Count | Lines of Code |
|------|-------|---------------|
| Python files | 128 | ~7,961 |
| JavaScript files | 61 | ~101+ |
| Total files | 189+ | ~8,062+ |
| Total size | 6.2 MB | - |

### Breakdown by Component

| Component | Purpose | Size |
|-----------|---------|------|
| API (views, serializers, URLs) | REST endpoints | ~2-3 KB |
| anthias_app | Web UI, models | ~1-2 KB |
| lib | Utilities, auth, backup | ~1-2 KB |
| Frontend (React) | Web interface | ~61 JS files |
| Docker | Build & orchestration | ~1 MB |
| Tests | Test suite | ~5 test files |
| Documentation | READMEs, guides | ~50+ KB |

---

## 8. FEATURES INVENTORY

### Actively Used Features

1. **Asset Management** ✓ USED
   - Upload images/videos
   - Store asset metadata (name, duration, size)
   - Delete assets
   - Update asset properties

2. **File Serving** ✓ USED
   - Serve uploaded files via HTTP
   - Support for images (JPG, PNG, GIF)
   - Support for videos (MP4, MPEG)
   - Base64 encoding for API delivery

3. **Metadata Storage** ✓ USED
   - Asset ID
   - File name
   - File URI
   - Mimetype
   - Duration
   - Play order

### Unused Features (NOT integrated)

1. **Device Management**
   - Device registration
   - Device status monitoring
   - Device control (reboot, shutdown)
   - **Status**: We use our own Device model in PostgreSQL

2. **Scheduling**
   - Schedule assets by date/time
   - Start/end date constraints
   - **Status**: We use our own Playlist scheduling

3. **Viewer Application**
   - Built-in HTML/JS viewer
   - Media player with controls
   - ZMQ-based messaging
   - **Status**: We use separate viewer in `/viewer` directory

4. **WebView (Qt-based)**
   - Desktop/kiosk application
   - Raspberry Pi support
   - **Status**: Alternative to web-based viewer

5. **Backup/Recovery**
   - System backup to file
   - Restore from backup
   - **Status**: Not integrated

6. **Real-time Monitoring**
   - WebSocket push updates
   - Live device status
   - **Status**: Not currently used

7. **Content Moderation**
   - URL verification
   - Asset checking
   - **Status**: `skip_asset_check=1` used in uploads

8. **Ansible Deployment**
   - Infrastructure as code
   - Automated device setup
   - **Status**: Not used (using Docker Compose)

9. **Raspberry Pi Imager**
   - Custom image builder
   - Pre-configured OS images
   - **Status**: Not used

10. **Frontend React UI**
    - Asset management dashboard
    - Device dashboard
    - Playlist editor
    - **Status**: Not used (we have our own web-admin)

---

## 9. DEPENDENCIES AND REQUIREMENTS

### Python Dependencies (from requirements.txt)

```
Core:
- Django 4.2+
- Django REST Framework
- Celery (task queue)
- Redis (cache)
- Pillow (image processing)
- psycopg2-binary (PostgreSQL)
- gunicorn (WSGI server)
- drf-spectacular (API docs)

Optional:
- boto3 (AWS S3)
- slack-sdk (Slack integration)
- requests (HTTP client)
- pyyaml
- pytest (testing)
```

### JavaScript Dependencies

```
Core:
- React 19
- Redux Toolkit
- React Router
- Webpack
- Babel

Dev:
- TypeScript
- Jest
- ESLint
- Prettier
```

### External Services

1. **Redis** - Message broker & cache
2. **PostgreSQL** - Optional database backend
3. **AWS S3** - Optional asset storage
4. **Slack** - Optional notifications

---

## 10. PERFORMANCE CHARACTERISTICS

### File Upload Performance
- **Max file size**: Depends on Anthias config (typically 1-2 GB)
- **Upload method**: 2-step process
  1. Upload file to `/api/v1/file_asset` → returns URI
  2. Create asset with URI → `/api/v1/assets`
- **Content types**: Images, videos, web pages
- **Storage**: Files stored at `/data/screenly_assets/` in Anthias container

### Asset Delivery
- **Method**: Served via Nginx reverse proxy (port 8000)
- **Caching**: Redis cache for metadata
- **Response format**: JSON API + raw file content

### Scalability
- **Stateless server**: Can scale horizontally
- **Celery workers**: Background task processing
- **Redis**: Shared state management
- **Asset storage**: Single volume (can use external storage)

---

## 11. RECOMMENDATIONS

### What Can Be Safely Removed

1. **WebView (Qt-based)** - Not used
   - `/anthias/webview/` - Can remove entirely
   - Saves build time and complexity

2. **Frontend React UI** - We have web-admin
   - `/anthias/static/src/` - Can remove or minimize
   - Our web-admin provides better UX

3. **Viewer Module** - Alternative implementation
   - `/anthias/viewer/` Python module - Not used (we have separate viewer)
   - Keep only for reference

4. **Ansible Playbooks** - Not using for deployment
   - `/anthias/ansible/` - Remove if not needed
   - We use Docker Compose

5. **Raspberry Pi Imager Tools** - Not building custom images
   - `/anthias/raspberry_pi_imager/` - Remove
   - Not part of our deployment pipeline

6. **Optional API Versions** - We only use v1
   - `/anthias/api/urls/v1_1.py`, `v1_2.py`, `v2.py` - Consider removing
   - Could reduce complexity

### What Must Be Kept

1. **Core API (v1)**
   - `/anthias/api/views/v1.py`
   - `/anthias/api/urls/v1.py`
   - `/anthias/api/serializers/v1_1.py`
   - **Critical**: Asset upload, retrieval, deletion

2. **Database Model**
   - `/anthias/anthias_app/models.py`
   - **Critical**: Asset storage

3. **Docker Infrastructure**
   - All Dockerfile.* files
   - `/anthias/docker/nginx/`
   - **Critical**: Container orchestration

4. **Celery Tasks**
   - `/anthias/celery_tasks.py`
   - **Important**: Background processing

5. **Authentication**
   - `/anthias/lib/auth.py`
   - **Important**: Security

### Optimization Suggestions

1. **Fork Anthias Minimally**
   - Keep only core API endpoints (v1)
   - Remove alternative API versions (v1.1, v1.2, v2)
   - Remove frontend UI (we have web-admin)
   - **Potential savings**: -30% codebase size

2. **Optimize Docker Images**
   - Consolidate related Dockerfiles
   - Use multi-stage builds
   - Remove development dependencies
   - **Potential savings**: -40% image size

3. **Replace File Upload with S3**
   - Use boto3 to upload directly to AWS S3
   - Reduce Anthias dependency to just metadata management
   - More scalable for large files
   - **Impact**: Simplify architecture

4. **Implement Simplified Fork**
   - Create "signate-assets" - minimal fork
   - Keep only Asset CRUD API
   - Remove non-essential features
   - **Impact**: Faster build, easier maintenance

5. **Consider Direct PostgreSQL Storage**
   - Store files in PostgreSQL using BYTEA
   - Eliminate Anthias file storage layer
   - Simpler deployment
   - **Trade-off**: PostgreSQL performance vs flexibility

---

## 12. DEPLOYMENT CHECKLIST

### Current Deployment Status

- **Server**: 192.168.5.12:8000
- **Status**: Running ✓
- **Container**: `anthias-server`, `anthias-celery`, `anthias-nginx`, `anthias-websocket`
- **Database**: SQLite at `/data/.screenly/screenly.db`
- **Storage**: `/data/screenly_assets/`
- **Cache**: Redis on shared container

### Key Configuration Files

1. **Docker Compose**
   - `/docker/docker-compose.yml` - Production setup
   - Services: anthias-server, anthias-celery, anthias-websocket, anthias-nginx

2. **.env Variables**
   ```
   ANTHIAS_API_URL=http://192.168.5.12:8000
   ANTHIAS_INTERNAL_URL=http://anthias-nginx
   ANTHIAS_PUBLIC_URL=http://192.168.5.12:8000
   ANTHIAS_API_KEY="" (not used)
   ANTHIAS_HOME=/data
   ANTHIAS_LISTEN=0.0.0.0
   ANTHIAS_EXTERNAL_PORT=8000
   ```

3. **Volumes to Persist**
   - `anthias-data:/data` - Database, settings
   - `../anthias-assets:/data/screenly_assets` - Uploaded files
   - `../anthias/staticfiles:/data/screenly/staticfiles` - Compiled frontend

---

## 13. RISKS AND CONSIDERATIONS

### Dependency Risks

1. **Tight Coupling**
   - Backend API depends on Anthias v1 API
   - Anthias database schema changes could break uploads
   - **Mitigation**: API versioning, abstract service layer (already in place)

2. **Single Point of Failure**
   - File storage only in Anthias (no replication)
   - **Mitigation**: Regular backups, consider external storage (S3)

3. **Technology Stack Complexity**
   - Anthias is full-featured but we only use 10% of features
   - Adds maintenance burden
   - **Mitigation**: Fork minimal version or replace with simpler solution

### Integration Risks

1. **File Upload Complexity**
   - 2-step upload process (file first, then asset)
   - Potential race conditions
   - **Current**: Implemented correctly in `anthias_service.py`

2. **Metadata Consistency**
   - File in Anthias, metadata in PostgreSQL
   - Risk of desynchronization
   - **Current**: Handled by service layer

3. **CORS and Network**
   - Viewer needs access to Anthias files
   - CORS configuration critical
   - **Current**: Configured in nginx

---

## 14. CONCLUSION

### Current State

Anthias serves as the **primary asset storage and delivery system** for the Smart TV Digital Signage project. Our integration is:

- **Minimal**: Only using asset upload/download/delete
- **Well-abstracted**: Isolated in `anthias_service.py`
- **Functional**: No known issues or missing features
- **Sustainable**: Can be maintained or replaced as needed

### Future Recommendations

**Short-term** (next 3-6 months):
1. Keep current Anthias integration as-is
2. Monitor stability and performance
3. Document any issues or quirks

**Medium-term** (6-12 months):
1. Evaluate fork vs maintained version vs replacement
2. Consider simpler alternatives:
   - MinIO (S3-compatible, lightweight)
   - Minio + PostgreSQL for metadata
   - Direct S3 + PostgreSQL
3. Plan gradual migration if needed

**Long-term** (1+ year):
1. If staying with Anthias: Create minimal fork
   - Keep only API v1
   - Remove unused features
   - Optimize Docker images
2. If migrating: Plan extraction of asset references from DB

### Files Critical to Keep

```
Essential (cannot remove):
✓ /anthias/api/views/v1.py
✓ /anthias/api/urls/v1.py
✓ /anthias/api/serializers/
✓ /anthias/anthias_app/models.py
✓ /anthias/docker/Dockerfile.server
✓ /anthias/docker/Dockerfile.celery
✓ /anthias/docker/Dockerfile.nginx
✓ /anthias/celery_tasks.py
✓ /anthias/lib/auth.py
✓ /anthias/requirements/

Optional (can remove):
✗ /anthias/static/src/ (React frontend)
✗ /anthias/webview/ (Qt viewer)
✗ /anthias/viewer/ (Python viewer)
✗ /anthias/api/urls/v1_1.py, v1_2.py, v2.py (if not needed)
✗ /anthias/ansible/ (not using)
✗ /anthias/raspberry_pi_imager/ (not using)
```

