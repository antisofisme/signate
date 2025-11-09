# Refactoring Audit - Digital Signage System

**Date:** 2025-11-02
**Purpose:** Inventarisasi existing code sebelum refactoring ke struktur baru

---

## 📁 Current Structure

```
/
├── backend/              # FastAPI backend (current production)
├── backend-new/          # Refactored backend (WIP)
├── web-admin/            # React admin dashboard (Vite)
├── viewer/               # Unified viewer (browser/WebOS)
└── webos/                # WebOS specific files
```

---

## 🗄️ Database Schema (Models)

### Core Models
- ✅ **User** - User management (admin, super admin)
- ✅ **Organization** - Multi-tenant organizations
- ✅ **UserOrganization** - User-organization mapping
- ✅ **Device** - TV/monitor devices
- ✅ **Content** - Media files (video, image, HTML)
- ✅ **Playlist** - Content playlists
- ✅ **PlaylistContent** - Playlist-content mapping
- ✅ **PlaylistAssignment** - Device-playlist assignment
- ✅ **Tag** - Device tags/grouping
- ✅ **DeviceTag** - Device-tag mapping (many-to-many)
- ✅ **Schedule** - Content scheduling

### Logging & Monitoring
- ✅ **ActivityLog** - User/system activity tracking
- ✅ **DeviceLog** - Device heartbeat & status logs
- ✅ **DeviceCommand** - Device command queue

### Integration
- ✅ **FirebirdConfig** - Firebird DB integration config
- ✅ **Hotel** - Hotel data from Firebird
- ✅ **SpeedTest** - Network speed test results

### Enums
- ✅ **Role** - User roles (ADMIN, SUPER_ADMIN, VIEWER)
- ✅ **ActivityAction** - Activity log actions
- ✅ **EntityType** - Entity types for logging

---

## 🛣️ API Endpoints

### Authentication & Users
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/register` - Register new user (super admin only)

### Organizations (Multi-tenant)
- `GET /api/organizations` - List organizations
- `POST /api/organizations` - Create organization
- `PUT /api/organizations/{id}` - Update organization
- `POST /api/organizations/{id}/validate-pin` - Validate org PIN

### Devices
- `GET /api/devices` - List devices (filtered by org)
- `POST /api/devices` - Create device
- `POST /api/devices/activate` - Activate device with code
- `POST /api/devices/{id}/heartbeat` - Device heartbeat
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device

### Content
- `GET /api/content` - List content (filtered by org)
- `POST /api/content/upload` - Upload content
- `PUT /api/content/{id}` - Update content metadata
- `DELETE /api/content/{id}` - Delete content
- `GET /api/content/{id}/preview` - Preview content

### Playlists
- `GET /api/playlists` - List playlists
- `POST /api/playlists` - Create playlist
- `PUT /api/playlists/{id}` - Update playlist
- `DELETE /api/playlists/{id}` - Delete playlist
- `POST /api/playlists/{id}/assign` - Assign to devices

### Tags
- `GET /api/tags` - List tags
- `POST /api/tags` - Create tag
- `PUT /api/tags/{id}` - Update tag
- `DELETE /api/tags/{id}` - Delete tag

### Client (Viewer API)
- `GET /api/client/playlist/{device_id}` - Get device playlist
- `GET /api/client/content/{content_id}` - Get content URL

### Settings & Templates
- `GET /api/settings` - Get system settings
- `PUT /api/settings` - Update settings
- `GET /api/templates` - List HTML templates
- `POST /api/templates` - Create template

### Monitoring & Logs
- `GET /api/activities` - Activity logs
- `GET /api/logs` - Device logs
- `GET /api/celery/tasks` - Celery task status

### Integrations
- `GET /api/firebird/hotels` - Fetch hotel data
- `POST /api/speedtest` - Run speed test

### WebSocket
- `WS /api/ws/{device_id}` - Device WebSocket connection
- `WS /api/ws/admin` - Admin dashboard updates

### Health & Utilities
- `GET /health` - Health check
- `GET /api/ping` - Ping

---

## 🏗️ Features & Modules

### Backend Services

#### Core Services
- ✅ **AuthService** - Authentication & authorization
- ✅ **DeviceService** - Device management
- ✅ **OrganizationService** - Multi-tenant org management
- ✅ **ContentService** - Content upload & management
- ✅ **PlaylistManager** - Playlist & assignment logic
- ✅ **SchedulerService** - Content scheduling

#### Background Tasks (Celery)
- ✅ **TranscodingService** - Video transcoding (FFmpeg)
- ✅ **ContentTasks** - Content processing tasks
- ✅ **SystemTasks** - Cleanup & maintenance
- ✅ **DeviceTasks** - Device monitoring

#### Integration Services
- ✅ **FirebirdService** - Firebird DB integration
- ✅ **AnthiasService** - Anthias CMS integration (port 8000)
- ✅ **TemplateService** - HTML template rendering
- ✅ **TranslationService** - Multi-language support

#### Utilities
- ✅ **ActivityLogger** - Activity logging utility
- ✅ **WebSocketService** - Real-time updates
- ✅ **CeleryMonitorService** - Task monitoring
- ✅ **PreviewService** - Content preview generation
- ✅ **ReportService** - Analytics & reports

### Frontend (Web Admin)

#### Pages
- ✅ Dashboard - Overview & statistics
- ✅ Devices - Device management
- ✅ Content - Media library
- ✅ Playlists - Playlist management
- ✅ Schedule - Content scheduling
- ✅ Analytics - Reports & insights
- ✅ Settings - System settings
- ⚠️ Super Admin - Global management (partially implemented)

#### Components
- ✅ Sidebar navigation
- ✅ Device cards & modals
- ✅ Content upload with drag-drop
- ✅ Playlist builder
- ✅ Activity logs viewer
- ✅ Organization management tab

### Viewer (Player)

#### Features
- ✅ 6-digit activation code
- ✅ Auto-play content from playlist
- ✅ Heartbeat to backend (30s)
- ✅ WebSocket for real-time updates
- ✅ Multi-platform support (browser, WebOS)
- ✅ Offline mode support

---

## 🔧 Tech Stack

### Backend
- **Framework:** FastAPI 0.109.0
- **Language:** Python 3.11+
- **Database:** PostgreSQL (via SQLAlchemy 2.0.25)
- **Cache:** Redis 4.6.0
- **Task Queue:** Celery 5.3.4
- **Auth:** JWT (python-jose)
- **Password:** bcrypt
- **Video Processing:** FFmpeg (via ffmpeg-python)
- **Logging:** Loguru + python-json-logger
- **HTTP Client:** httpx (async)
- **WebSocket:** websockets 12.0

### Frontend (Web Admin)
- **Framework:** React 18.3.1
- **Build Tool:** Vite 5.4.1
- **Styling:** Tailwind CSS 3.4.11
- **Routing:** React Router v6.26.0
- **State:** React Query (TanStack Query)
- **HTTP:** Axios 1.7.7
- **UI Icons:** Lucide React
- **Charts:** Recharts 3.3.0
- **Notifications:** React Hot Toast

### Viewer
- **Tech:** Vanilla HTML/CSS/JS
- **Target:** Browser, WebOS TV

### Infrastructure
- **Container:** Docker + Docker Compose
- **Database:** PostgreSQL 15 (port 5433)
- **Cache:** Redis (port 6379)
- **Backend:** Port 8001
- **Web Admin:** Port 3000 (dev)
- **Viewer:** Port 8080

---

## 📊 Code Quality Assessment

### ✅ Strengths
1. **Multi-tenancy** - Organization isolation sudah implemented
2. **Activity Logging** - Comprehensive audit trail
3. **Real-time Updates** - WebSocket for live data
4. **Background Processing** - Celery untuk heavy tasks
5. **API Documentation** - FastAPI auto-docs
6. **Type Safety** - Pydantic schemas
7. **Modern Frontend** - React + Vite + TailwindCSS

### ⚠️ Issues to Fix
1. **Folder Structure** - Tidak jelas (backend vs backend-new)
2. **Code Duplication** - backend vs backend-new ada overlap
3. **Hardcoded Values** - URLs di beberapa tempat
4. **No Centralized API Routes** - Endpoints scattered
5. **Mixed Concerns** - Business logic di API layer
6. **Inconsistent Naming** - Beberapa file pakai snake_case vs camelCase
7. **No Shared Types** - Frontend tidak sync dengan backend schemas
8. **Testing** - Minimal test coverage

### 🔴 Critical Issues
1. **Two Backends** - backend/ vs backend-new/ konflik
2. **No API Gateway** - Direct access ke microservices
3. **No Service Discovery** - Hardcoded service URLs
4. **Environment Variables** - Tidak consistent per service
5. **Scalability** - Monolith, sulit scale horizontal

---

## 🎯 Refactoring Priorities

### Phase 1: Structure (CRITICAL)
1. ✅ Create new folder structure (backend-python, cms-nextjs, player-flutter)
2. ✅ Write README per service (architecture, env, API endpoints)
3. ⏳ Consolidate backend/ + backend-new/ → backend-python/
4. ⏳ Move web-admin/ → cms-nextjs/
5. ⏳ Prepare player-flutter/ skeleton

### Phase 2: Centralization
1. Centralized API routes definition per service
2. Environment variables per service (.env files)
3. Shared utilities within each service (not cross-service)

### Phase 3: Microservices Split
1. Split backend into services (auth, tenant, device, content, analytics)
2. API Gateway (nginx/traefik)
3. Service-to-service communication (REST or gRPC)

### Phase 4: Code Quality
1. Remove hardcoded values
2. Add comprehensive tests
3. Improve error handling
4. Add request validation

### Phase 5: Infrastructure
1. Docker compose orchestration
2. CI/CD pipeline
3. Monitoring & logging (centralized)
4. Backup & disaster recovery

---

## 📝 Migration Strategy

### Approach: **Incremental Migration**

1. **Keep old code running** (backend/, web-admin/, viewer/)
2. **Build new structure** (backend-python/, cms-nextjs/, player-flutter/)
3. **Migrate module by module**:
   - Start with auth (smallest, critical)
   - Then device management
   - Then content management
   - Finally analytics & integrations
4. **Parallel running** - Old & new API berjalan bersamaan
5. **Feature flag** - Toggle between old/new implementation
6. **Gradual cutover** - Switch services one by one
7. **Rollback plan** - Keep old code until 100% verified

### First Module: Auth Service
- Small, isolated
- Critical for all other services
- Clear API boundaries
- Easy to test

---

## 🚀 Next Steps

1. ✅ Audit complete
2. ⏳ Consolidate backend + backend-new
3. ⏳ Setup skeleton for all 3 services
4. ⏳ Create centralized API routes files
5. ⏳ Setup .env per service
6. ⏳ Migrate auth service first
7. ⏳ Test & verify
8. ⏳ Repeat for other modules

---

**Status:** ✅ Audit Complete - Ready for Phase 1 (Structure)
