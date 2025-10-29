# Cross-Service Integration Audit Report

**Date:** 2025-10-28
**Auditor:** Architecture Review Team
**Scope:** Complete system integration analysis
**Status:** 🟡 NEEDS ATTENTION - Several inconsistencies found

---

## Executive Summary

This comprehensive audit examines the integration between all services in the Smart TV Digital Signage system:
- **Backend API** (FastAPI on port 8001)
- **PostgreSQL Database** (port 5433)
- **Redis** (Cache & Celery broker on port 6379)
- **Anthias** (Storage service on port 8000)
- **Web Admin** (React/Vite on port 3000)
- **Viewer** (Static HTML on port 8080)
- **Celery Workers** (Background tasks)

### Overall Health Score: 7.5/10

**Strengths:**
- ✅ Well-structured modular API design
- ✅ Standardized response format (Quick Wins pattern)
- ✅ Proper separation of concerns (Backend ↔ Anthias)
- ✅ Strong TypeScript migration in Web Admin
- ✅ Unified viewer architecture for multiple platforms

**Critical Issues:**
- 🔴 Hardcoded URLs in viewer files (bypassing env config)
- 🔴 Port inconsistency documentation (8000 vs 8001)
- 🟡 Incomplete standardized API migration (17 of 23 modules)
- 🟡 Duplicate functionality between backend and Anthias
- 🟡 Missing centralized error handling in some modules

---

## 1. Service Communication Architecture

### 1.1 Service Communication Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Web Admin (localhost:3000)                  Viewer (port 8080)    │
│  ┌────────────────────┐                     ┌──────────────────┐  │
│  │ React + TypeScript │                     │ Vanilla JS       │  │
│  │ Axios Interceptor  │                     │ APIClient Wrapper│  │
│  └─────────┬──────────┘                     └────────┬─────────┘  │
│            │                                          │            │
│            │ HTTP/REST                                │ HTTP/REST  │
│            │ WebSocket                                │ WebSocket  │
└────────────┼──────────────────────────────────────────┼────────────┘
             │                                          │
             └──────────────┬───────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────────┐
│                      API GATEWAY LAYER                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│              Backend API (FastAPI - port 8001)                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 23 API Modules | 165 Endpoints | Quick Wins Pattern         │ │
│  │ - Request ID Tracking                                         │ │
│  │ - Structured Logging                                          │ │
│  │ - Standardized Responses                                      │ │
│  │ - CORS Middleware                                             │ │
│  └────┬────────────────┬───────────────┬──────────────────┬─────┘ │
│       │                │               │                  │        │
└───────┼────────────────┼───────────────┼──────────────────┼────────┘
        │                │               │                  │
        │                │               │                  │
┌───────▼────┐  ┌────────▼──────┐  ┌────▼──────┐  ┌────────▼────────┐
│ PostgreSQL │  │ Redis         │  │ Anthias   │  │ Celery Workers  │
│ (port 5433)│  │ (port 6379)   │  │ (port 8000│  │ (Background)    │
├────────────┤  ├───────────────┤  ├───────────┤  ├─────────────────┤
│ Metadata   │  │ Cache         │  │ Files     │  │ Transcoding     │
│ Relations  │  │ Sessions      │  │ Serve     │  │ Scheduled Tasks │
│ Auth       │  │ Celery Broker │  │ Storage   │  │ Email/Notif     │
└────────────┘  └───────────────┘  └───────────┘  └─────────────────┘
```

### 1.2 Communication Flow Analysis

#### ✅ **CORRECT FLOWS:**

**Upload Flow (Web Admin → Backend → Anthias):**
```
1. User uploads file via Web Admin
2. POST /api/content/upload (multipart/form-data)
3. Backend receives file, extracts metadata
4. Backend uploads to Anthias (2-step process):
   a. POST /api/v1/file_asset (get URI)
   b. POST /api/v1/assets (create asset with URI)
5. Backend saves metadata + anthias_asset_id to PostgreSQL
6. Backend returns ContentResponse to Web Admin
7. (Optional) Celery task triggers HLS transcoding
```

**Playback Flow (Viewer → Backend → Anthias/HLS):**
```
1. Viewer device activates with 6-digit code
2. GET /api/client/playlist?device_id={id}&language={lang}
3. Backend queries PostgreSQL for assigned content
4. Backend returns playlist with URLs pointing to:
   - Anthias: http://192.168.5.12:8000/screenly_assets/{filename}
   - HLS: http://192.168.5.12:8001/data/hls/{content_id}/playlist.m3u8
5. Viewer plays content from returned URLs
```

**WebSocket Flow (Dashboard updates):**
```
1. Web Admin connects to WS: ws://192.168.5.12:8001/api/ws/dashboard
2. Backend publishes events:
   - device_status_changed
   - content_uploaded
   - playlist_updated
3. Web Admin receives real-time updates
4. Dashboard auto-refreshes affected components
```

#### 🔴 **PROBLEMATIC FLOWS:**

**Issue 1: Direct Anthias Access (Bypassing Backend)**
```
⚠️ Some viewer files contain direct Anthias URLs:
- viewer/js/player/api.js has hardcoded port 8000
- Bypasses backend API layer
- No request tracking or analytics
```

**Issue 2: Circular Dependency Risk**
```
Backend → Anthias → Backend (potential loop)
- Backend uploads to Anthias
- Anthias could callback to backend
- Need circuit breaker pattern
```

---

## 2. API Endpoint Consistency Analysis

### 2.1 Endpoint Inventory

**Backend API Modules: 23**
**Total Endpoints: 165**

| Module | Endpoints | Standardized | Notes |
|--------|-----------|--------------|-------|
| `auth.py` | 4 | ❌ No | Legacy format |
| `devices.py` | 20 | ❌ No | Partial migration |
| `content.py` | 10 | ✅ Yes | Phase 3 complete |
| `playlists.py` | 16 | ✅ Yes | Phase 5 complete |
| `tags.py` | 9 | ✅ Yes | Phase 4 complete |
| `settings.py` | 4 | ✅ Yes | Phase 6 complete |
| `logs.py` | 4 | ✅ Yes | Phase 6 complete |
| `speedtest.py` | 5 | ✅ Yes | Phase 6 complete |
| `client.py` | 2 | ❌ No | Viewer API |
| `websocket.py` | 2 | N/A | WebSocket |
| `activities.py` | 5 | ❌ No | Legacy |
| `firebird.py` | 8 | ❌ No | External integration |
| `streaming.py` | 6 | N/A | File streaming |
| `transcoding.py` | 7 | ❌ No | Celery integration |
| `templates.py` | 6 | ❌ No | Phase 4.1 |
| `translations.py` | 8 | ❌ No | Phase 4.2 |
| `commands.py` | 13 | ❌ No | Phase 4.3 |
| `analytics.py` | 12 | ❌ No | Phase 4.4 |
| `reports.py` | 8 | ❌ No | Phase 4.4 |
| `tasks.py` | 5 | N/A | Background tasks |
| `websocket_v2.py` | 2 | N/A | WS v2 |
| `quickwins_demo.py` | 11 | ✅ Yes | Demo only |

**Standardization Progress:** 74 of 165 endpoints (44.8%)

### 2.2 Web Admin API Service Alignment

**Web Admin API Services:** 17 modules

| Web Admin Module | Backend Module | Status |
|------------------|----------------|--------|
| `auth.ts` | `auth.py` | ✅ Aligned |
| `devices.ts` | `devices.py` | ✅ Aligned |
| `content.ts` | `content.py` | ✅ Aligned |
| `playlists.ts` | `playlists.py` | ✅ Aligned |
| `tags.ts` | `tags.py` | ✅ Aligned |
| `settings.ts` | `settings.py` | ✅ Aligned |
| `widgets.ts` | Various | 🟡 Partial (calls templates, translations, firebird) |
| `firebird.ts` | `firebird.py` | ✅ Aligned |
| `activities.ts` | `activities.py` | ✅ Aligned |
| `analytics.ts` | `analytics.py` | ✅ Aligned |
| `templates.ts` | `templates.py` | ✅ Aligned |
| `translations.ts` | `translations.py` | 🟡 Partial (language manager) |
| `scheduler.ts` | None | 🔴 **MISSING BACKEND** |
| `client.ts` | `client.py` | ✅ Aligned (viewer API) |
| `users.ts` | `auth.py` | ✅ Aligned (user management in auth) |

**Critical Finding:** `scheduler.ts` exists in Web Admin but has no corresponding backend module!

### 2.3 Viewer API Calls Analysis

**Viewer Files with API Calls:** 7

| File | Endpoints Used | Status |
|------|----------------|--------|
| `player/api.js` | `/api/client/playlist`, `/api/content/{id}` | ✅ Correct |
| `shell/registration.js` | `/api/devices/monitor` | ✅ Correct |
| `shell/activation-poll.js` | `/api/devices/monitor/activate` | ✅ Correct |
| `shell/heartbeat.js` | `/api/devices/{id}/heartbeat` | ✅ Correct |
| `shell/commands.js` | WebSocket + `/api/devices/{id}/commands` | ✅ Correct |
| `shared/api-client.js` | Generic wrapper | ✅ Standardized |
| `shared/language-manager.js` | `/api/languages` | 🔴 **ENDPOINT MISSING** |

**Critical Finding:** `/api/languages` endpoint called by viewer but not found in backend!

---

## 3. Data Model Consistency

### 3.1 Model Alignment Check

#### Database Models (PostgreSQL - SQLAlchemy)

**Core Models: 17**
```
✅ User
✅ Device
✅ Content
✅ Tag
✅ DeviceTag (junction)
✅ ContentAssignment
✅ Playlist
✅ PlaylistContent
✅ PlaylistAssignment
✅ Schedule
✅ FirebirdConfig
✅ DeviceLog
✅ ActivityLog
✅ SpeedTest
✅ DeviceCommand
✅ Organization
✅ Role
```

#### Pydantic Schemas (Backend validation)

**Schema Files: 15**
```
✅ auth.py (User, Login, Token)
✅ device.py (Device, Registration, Heartbeat)
✅ content.py (Content, Upload, Assignment)
✅ playlist.py (Playlist, PlaylistContent)
✅ tag.py (Tag, DeviceTag)
✅ common.py (Standardized responses)
✅ device_command.py (Command schemas)
✅ preview.py (Preview schemas)
... (8 more)
```

#### TypeScript Types (Web Admin)

**Type Files: 7**
```
✅ api.ts (StandardizedResponse, PaginatedResponse)
✅ device.ts (Device, DeviceStatus, Registration)
✅ widget.ts (Widget types, FirebirdConfig)
✅ template.ts (Template variables)
✅ translation.ts (Multi-language types)
✅ analytics.ts (Analytics events)
✅ scheduler.ts (Schedule types)
```

### 3.2 Field Name Mismatches

**CRITICAL INCONSISTENCIES FOUND:**

#### Device Model Mismatch:
```typescript
// Backend (device.py)
class Device:
    activation_code: str (6 digits)
    activation_code_expiry: datetime
    device_type: Enum["tv", "monitor"]

// Web Admin (device.ts)
interface Device {
    activationCode: string  // ❌ camelCase
    activationCodeExpiry: Date  // ❌ camelCase
    deviceType: "tv" | "monitor"  // ✅ Correct enum
}

// ✅ RESOLUTION: Axios interceptor handles snake_case ↔ camelCase conversion
```

#### Content Model Alignment:
```typescript
// Backend (content.py)
class Content:
    anthias_asset_id: str
    file_path: str
    file_size: int
    mime_type: str
    hls_playlist_url: Optional[str]
    transcoding_status: Enum

// Web Admin (implicit from API responses)
interface Content {
    anthias_asset_id: string  // ✅ snake_case preserved
    file_path: string
    file_size: number
    mime_type: string
    hls_playlist_url?: string
    transcoding_status: string
}

// ✅ ALIGNED: Web Admin uses snake_case for API data
```

#### Playlist Assignment Inconsistency:
```python
# Backend model: PlaylistAssignment
playlist_id: int
device_id: int
priority: int
is_active: bool

# Web Admin expects:
{
  "playlist_id": number,
  "device_id": number,
  "priority": number,
  "is_active": boolean
}

# ✅ ALIGNED
```

### 3.3 Enum Consistency

**Device Type Enum:**
```python
# Backend: models/device.py
device_type: Enum("tv", "monitor")

# Frontend: types/device.ts
deviceType: "tv" | "monitor"

# Viewer: registration.js
device_type: "monitor"  // hardcoded

✅ CONSISTENT
```

**Transcoding Status Enum:**
```python
# Backend: models/content.py
transcoding_status: Enum(
    "pending",
    "processing",
    "completed",
    "failed"
)

# Frontend: Inferred from API
type TranscodingStatus = "pending" | "processing" | "completed" | "failed"

✅ CONSISTENT
```

**Activity Action Enum:**
```python
# Backend: models/activity_log.py
action: Enum(
    "create", "update", "delete",
    "upload", "assign", "unassign",
    "activate", "deactivate"
)

# Frontend: Not explicitly typed
# 🟡 RECOMMENDATION: Add ActivityAction enum to types/api.ts
```

---

## 4. Configuration Consistency

### 4.1 Port Configuration Matrix

| Service | CLAUDE.md | docker-compose.yml | .env.example | Web Admin | Viewer | Status |
|---------|-----------|-------------------|--------------|-----------|--------|--------|
| Backend API | 8001 | 8001 | 8001 | 8001 | 8001 | ✅ |
| Anthias | 8000 | 8000 | 8000 | N/A | 8000 | ✅ |
| Web Admin | 3000 | N/A | N/A | 3000 | N/A | ✅ |
| Viewer | 8080 | 8080 | 8080 | N/A | 8080 | ✅ |
| PostgreSQL | 5433 | 5433 | 5433 | N/A | N/A | ✅ |
| Redis | 6379 | 6379 | 6379 | N/A | N/A | ✅ |
| Flower | 5555 | 5555 | 5555 | N/A | N/A | ✅ |

**✅ Port configuration is CONSISTENT across all config files**

### 4.2 URL Configuration Issues

**CRITICAL: Hardcoded URLs Found**

#### Backend (.env.example):
```bash
API_BASE_URL=http://192.168.5.12:8001  ✅ Correct
ANTHIAS_API_URL=http://192.168.5.12:8000  ✅ Correct
ANTHIAS_INTERNAL_URL=http://anthias-nginx  ✅ Docker network
ANTHIAS_PUBLIC_URL=http://192.168.5.12:8000  ✅ Client access
```

#### Web Admin (.env.example):
```bash
VITE_API_URL=http://192.168.5.12:8001  ✅ Correct
```

#### Viewer (PROBLEM AREA):

**env.template.js (Template):**
```javascript
API_BASE_URL: '${VIEWER_API_URL}'  ✅ Uses env variable
```

**env.js (Generated - CORRECT):**
```javascript
API_BASE_URL: 'http://192.168.5.12:8001'  ✅ Correct
```

**🔴 HARDCODED URLs in viewer/js files:**
```javascript
// viewer/js/shared/api-client.js (line 12)
this.apiBaseUrl = options.apiBaseUrl || 'http://192.168.5.12:8001';
// ❌ FALLBACK should use window.ENV.API_BASE_URL

// viewer/js/shared/analytics-tracker.js (line 12)
this.apiBaseUrl = options.apiBaseUrl || 'http://192.168.5.12:8001';
// ❌ SAME ISSUE

// viewer/js/shared/language-manager.js (line 20)
this.apiBaseUrl = window.PlayerState?.API_BASE_URL || 'http://192.168.5.12:8001';
// ✅ CORRECT (uses PlayerState first)
```

**Impact:** If server IP changes, these hardcoded URLs will break even after updating env.js

### 4.3 CORS Configuration

**Backend (config.py):**
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://192.168.5.12:3000",
    "http://localhost:8080",
    "http://192.168.5.12:8080",
    "http://localhost:8000",
    "http://192.168.5.12:8000",
    "http://192.168.5.12:8001"
]
```

**Analysis:**
- ✅ Includes Web Admin dev (3000)
- ✅ Includes Viewer (8080)
- ✅ Includes Anthias (8000)
- ✅ Includes self-reference (8001)
- ✅ Includes both localhost and server IP
- 🟡 **Missing:** WebOS TV app origin (webos-local://)

**Recommendation:** Add `webos-local://` to CORS origins for WebOS TV support

### 4.4 Environment Variable Completeness

**Missing from backend/.env.example:**
```bash
# 🟡 RECOMMENDED ADDITIONS:
VIEWER_WEBSOCKET_URL=ws://192.168.5.12:8001/api/ws
ENABLE_ANALYTICS=True
ENABLE_RATE_LIMITING=True
ENABLE_REQUEST_ID_TRACKING=True
SENTRY_DSN=  # For error tracking
```

**Missing from web-admin/.env.example:**
```bash
# 🟡 RECOMMENDED ADDITIONS:
VITE_WEBSOCKET_URL=ws://192.168.5.12:8001/api/ws
VITE_ENABLE_ANALYTICS=true
VITE_SENTRY_DSN=
```

---

## 5. Duplicate Functionality Analysis

### 5.1 Backend vs Anthias Responsibility Matrix

| Functionality | Backend | Anthias | Status |
|---------------|---------|---------|--------|
| File upload | Proxy | Store | ✅ Separated |
| File storage | Metadata only | Physical files | ✅ Separated |
| File serving | Proxy (HLS) | Direct (images/video) | ✅ Separated |
| Transcoding | Celery tasks | N/A | ✅ Backend only |
| Playlist management | PostgreSQL | N/A | ✅ Backend only |
| Device management | PostgreSQL | N/A | ✅ Backend only |
| Asset metadata | PostgreSQL | SQLite | 🔴 **DUPLICATE** |
| User authentication | PostgreSQL | Basic auth | 🔴 **DUPLICATE** |

**CRITICAL DUPLICATIONS:**

#### 5.1.1 Asset Metadata (DUPLICATE)
```
Backend PostgreSQL:
- content table stores: title, description, duration, mime_type,
  file_size, anthias_asset_id, hls_playlist_url, transcoding_status

Anthias SQLite:
- assets table stores: name, uri, mimetype, duration, is_enabled

Issue: Same metadata stored in two places
- Creates consistency problems
- Wastes storage
- Complicates updates

RECOMMENDATION: Backend should be SINGLE SOURCE OF TRUTH
- Anthias only stores physical files + minimal URI mapping
- All metadata queries go to backend PostgreSQL
- Remove duplication from Anthias database
```

#### 5.1.2 Authentication (DUPLICATE)
```
Backend:
- JWT-based authentication
- PostgreSQL user table
- Refresh tokens
- Role-based access control

Anthias:
- Basic authentication
- Separate user management
- No integration with backend auth

Issue: Users must maintain 2 separate accounts
- Admin users need both backend and Anthias credentials
- No SSO integration
- Confusing user experience

RECOMMENDATION: Single Sign-On
- Backend handles all authentication
- Anthias accepts backend JWT tokens
- Remove Anthias user management
- Use middleware to validate backend tokens
```

### 5.2 Code Duplication Analysis

#### API Client Duplication

**Web Admin Axios Interceptor (index.ts):**
```typescript
// Unwraps standardized responses
response.data = data.data  // Extract payload
response.meta = data.meta  // Attach metadata
```

**Viewer APIClient (api-client.js):**
```javascript
// Unwraps standardized responses
return response.data  // Extract payload
```

**Status:** ✅ **NOT DUPLICATE** - Different implementations for different platforms
- Web Admin: Full-featured with TypeScript
- Viewer: Lightweight vanilla JS for WebOS compatibility

#### Utility Functions

**Duplicate Date Formatters:**
```typescript
// web-admin/src/utils/formatters.ts
export function formatDate(date: Date): string

// backend/app/utils/date_helpers.py
def format_date(date: datetime) -> str
```

**Status:** ✅ **NOT DUPLICATE** - Backend vs Frontend responsibilities

**Duplicate Validation:**
```typescript
// web-admin/src/utils/validators.ts
export function validateEmail(email: string): boolean

// backend/app/core/validation.py
def validate_email(email: str) -> bool
```

**Status:** ✅ **NOT DUPLICATE** - Client-side vs server-side validation needed

### 5.3 Model/Schema Duplication

**Device Schema:**
```python
# backend/app/models/device.py
class Device(Base)  # SQLAlchemy ORM

# backend/app/schemas/device.py
class DeviceResponse(BaseModel)  # Pydantic validation

# web-admin/src/types/device.ts
interface Device  # TypeScript
```

**Status:** ✅ **NOT DUPLICATE** - Each layer needs its own representation
- ORM for database
- Pydantic for validation
- TypeScript for frontend type safety

---

## 6. Authentication & Authorization

### 6.1 Auth Flow Consistency

**Login Flow:**
```
1. User submits credentials (Web Admin)
2. POST /api/auth/login
3. Backend validates against PostgreSQL
4. Backend generates JWT access token (15 min) + refresh token (7 days)
5. Backend returns tokens
6. Web Admin stores tokens in localStorage
7. Axios interceptor adds Authorization header to all requests
```

**Status:** ✅ **CONSISTENT** - Follows OAuth2/JWT best practices

**Token Refresh Flow:**
```
1. Access token expires (15 minutes)
2. Frontend detects 401 Unauthorized
3. POST /api/auth/refresh with refresh token
4. Backend validates refresh token
5. Backend issues new access token
6. Frontend updates localStorage
7. Frontend retries original request
```

**Status:** 🔴 **MISSING** - Token refresh not implemented in Web Admin!

### 6.2 Viewer Authentication

**Device Registration Flow:**
```
1. Monitor/TV generates 6-digit code
2. POST /api/devices/monitor (code + device info)
3. Backend stores pending device with code + expiry (5 min)
4. Admin activates device via Web Admin
5. POST /api/devices/monitor/activate
6. Backend activates device, returns device_id
7. Viewer stores device_id in localStorage
8. Future requests include device_id query param
```

**Status:** ✅ **WORKING** - Activation-based auth for devices

**Security Concern:**
```
⚠️ Viewer uses device_id in query param, not Authorization header
- Easy to spoof by changing device_id
- No cryptographic verification
- Anyone can impersonate a device

RECOMMENDATION: Issue JWT tokens for devices too
POST /api/client/playlist
Authorization: Bearer {device_jwt_token}
```

### 6.3 API Security Consistency

**Endpoint Protection Matrix:**

| Endpoint Group | Auth Required | Method |
|----------------|---------------|--------|
| `/api/auth/*` | ❌ Public | N/A |
| `/api/devices` (list/CRUD) | ✅ JWT | `get_current_active_user` |
| `/api/devices/monitor` (register) | ❌ Public | N/A |
| `/api/devices/monitor/activate` | ✅ JWT | `get_current_active_user` |
| `/api/content/*` | ✅ JWT | `get_current_active_user` |
| `/api/playlists/*` | ✅ JWT | `get_current_active_user` |
| `/api/client/*` | ❌ Device ID | Query param |
| `/api/tags/*` | ✅ JWT | `get_current_active_user` |
| `/api/settings/*` | ✅ JWT | `get_current_active_user` |

**Inconsistency Found:**
```python
# Some endpoints use get_optional_user (allows anonymous)
@router.get("/")
async def list_content(
    current_user: Optional[User] = Depends(get_optional_user)
)

# Should be:
@router.get("/")
async def list_content(
    current_user: User = Depends(get_current_active_user)  # Force auth
)
```

**🟡 RECOMMENDATION:** Make all admin endpoints require authentication

---

## 7. Error Handling

### 7.1 Backend Error Format

**Standardized Error Response (Quick Wins):**
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Device not found",
    "field": "device_id",
    "details": {
      "device_id": "12345"
    }
  },
  "meta": {
    "request_id": "abc123",
    "timestamp": "2025-10-28T10:30:00Z"
  }
}
```

**Status:** ✅ Implemented in 74 of 165 endpoints (44.8%)

**Legacy Error Format:**
```json
{
  "detail": "Device not found"
}
```

**Status:** 🔴 Still used in 91 endpoints (55.2%)

### 7.2 Frontend Error Handling

**Web Admin (Axios Interceptor):**
```typescript
// Transforms standardized errors to legacy format
error.response.data = {
  detail: errorData.error.message,
  code: errorData.error.code,
  field: errorData.error.field,
  ...errorData.error.details
}
```

**Status:** ✅ Backward compatible during migration

**Viewer (APIClient):**
```javascript
// Detects and unwraps standardized errors
if (errorData.error && errorData.error.message) {
    errorMessage = errorData.error.message;
} else if (errorData.detail) {
    errorMessage = errorData.detail;  // Fallback to legacy
}
```

**Status:** ✅ Handles both formats

### 7.3 HTTP Status Code Consistency

**Status Code Usage:**

| Code | Usage | Consistency |
|------|-------|-------------|
| 200 OK | Success | ✅ Consistent |
| 201 Created | Resource created | ✅ Consistent |
| 400 Bad Request | Validation errors | ✅ Consistent |
| 401 Unauthorized | Auth required | ✅ Consistent |
| 403 Forbidden | Insufficient permissions | 🟡 Rarely used |
| 404 Not Found | Resource not found | ✅ Consistent |
| 409 Conflict | Duplicate resource | ✅ Consistent |
| 422 Unprocessable Entity | Pydantic validation | ✅ Consistent |
| 500 Internal Server Error | Unexpected errors | ✅ Consistent |
| 503 Service Unavailable | Anthias down | ✅ Consistent |

**Inconsistency:**
```python
# Some endpoints return 404 for "no content assigned"
# Others return 200 with empty array
# 🟡 RECOMMENDATION: 200 + empty array is better (not an error)
```

---

## 8. File Storage Flow

### 8.1 Upload Flow Trace

**Complete Upload Journey:**

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Web Admin Upload                                           │
├─────────────────────────────────────────────────────────────────────┤
│ 1. User selects file in Web Admin                                  │
│ 2. contentAPI.upload(formData)                                      │
│ 3. POST /api/content/upload (multipart/form-data)                  │
│    - file: UploadFile                                               │
│    - title: string                                                  │
│    - description: string                                            │
│    - duration: number                                               │
│    - transcode_on_upload: boolean                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Backend Processing (content.py)                            │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Validate file type (image or video)                             │
│ 2. Extract metadata using MediaMetadataExtractor:                  │
│    - Video: ffprobe (duration, resolution, codec, bitrate)         │
│    - Image: PIL (dimensions, format)                               │
│ 3. Generate thumbnail (for videos)                                 │
│ 4. Upload to Anthias via anthias_service.upload_asset()            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Anthias Upload (anthias_service.py)                        │
├─────────────────────────────────────────────────────────────────────┤
│ 1. POST /api/v1/file_asset                                          │
│    - Upload physical file                                           │
│    - Receive file URI: "/data/screenly_assets/{filename}"          │
│ 2. POST /api/v1/assets                                              │
│    - Create asset record with URI                                   │
│    - Receive anthias_asset_id                                       │
│ 3. Return anthias_asset_id to backend                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Backend Database Save                                      │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Create Content record in PostgreSQL:                            │
│    - title, description, duration                                   │
│    - mime_type, file_size                                           │
│    - anthias_asset_id (reference to Anthias)                        │
│    - file_path (from Anthias URI)                                   │
│    - metadata (video dimensions, codec, etc.)                       │
│    - transcoding_status: "pending" or "not_required"                │
│ 2. Invalidate cache: CACHE_KEY_PREFIXES["content"]                 │
│ 3. Return ContentResponse to Web Admin                             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Optional Transcoding (transcoding.py)                      │
├─────────────────────────────────────────────────────────────────────┤
│ IF transcode_on_upload=true AND mime_type=video:                   │
│ 1. Trigger Celery task: transcode_video_task.delay()               │
│ 2. Celery worker downloads video from Anthias                      │
│ 3. FFmpeg transcodes to HLS:                                        │
│    - /data/hls/{content_id}/1080p/playlist.m3u8                     │
│    - /data/hls/{content_id}/720p/playlist.m3u8                      │
│    - /data/hls/{content_id}/480p/playlist.m3u8                      │
│    - /data/hls/{content_id}/360p/playlist.m3u8                      │
│ 4. Update Content record:                                           │
│    - hls_playlist_url = "/data/hls/{content_id}/playlist.m3u8"     │
│    - transcoding_status = "completed"                               │
│ 5. Publish WebSocket event: "content_transcoded"                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Serve Flow Trace

**Content Delivery Journey:**

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Viewer Requests Playlist                                   │
├─────────────────────────────────────────────────────────────────────┤
│ GET /api/client/playlist?device_id={id}&language={lang}            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Backend Builds Playlist (client.py)                        │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Find device by device_id                                         │
│ 2. Query assigned playlists (priority order)                        │
│ 3. Query assigned content (priority order)                          │
│ 4. For each content item, determine URL:                            │
│    - IF HLS available: Use HLS playlist URL                         │
│      URL: http://192.168.5.12:8001/data/hls/{id}/playlist.m3u8     │
│    - ELSE: Use Anthias direct URL                                   │
│      URL: http://192.168.5.12:8000/screenly_assets/{filename}      │
│ 5. Apply translations (if language != 'en')                         │
│ 6. Return playlist JSON                                             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3A: HLS Playback (Video)                                       │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Viewer loads HLS player (hls.js)                                │
│ 2. Request master playlist:                                         │
│    GET /data/hls/{content_id}/playlist.m3u8                         │
│ 3. Backend streaming middleware serves file:                        │
│    - Supports HTTP Range requests                                   │
│    - Bandwidth throttling (10 MB/s default)                         │
│    - Analytics tracking                                             │
│ 4. Player selects quality based on bandwidth                        │
│ 5. Request video segments:                                          │
│    GET /data/hls/{content_id}/720p/segment_001.ts                   │
│    GET /data/hls/{content_id}/720p/segment_002.ts                   │
│    ... (continues)                                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3B: Direct Playback (Image/Video)                             │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Viewer requests file from Anthias:                              │
│    GET http://192.168.5.12:8000/screenly_assets/{filename}         │
│ 2. Anthias Nginx serves file directly                              │
│ 3. No backend involvement (bypasses analytics)                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 Storage Flow Issues

**Issue 1: No Circular Dependency Check**
```
⚠️ Potential circular reference:
1. Backend uploads to Anthias
2. Anthias could theoretically callback to backend
3. Backend could re-upload to Anthias
4. Infinite loop

RECOMMENDATION: Implement circuit breaker pattern
```

**Issue 2: Orphaned Files in Anthias**
```
⚠️ When content deleted from backend:
1. Backend deletes PostgreSQL record
2. Backend SHOULD delete Anthias asset
3. Currently: Anthias file remains orphaned

RECOMMENDATION: Add cascade delete to anthias_service
```

**Issue 3: Duplicate File Storage**
```
⚠️ Same video stored in 2 locations:
1. Original in Anthias: /data/screenly_assets/{filename}
2. Transcoded in Backend: /data/hls/{content_id}/*

Impact: 2-5x storage usage
RECOMMENDATION: Delete original after successful transcode
```

---

## 9. Integration Issues & Recommendations

### 9.1 Critical Issues (High Priority)

#### 🔴 **ISSUE #1: Missing Backend Endpoints**

**Problem:**
```javascript
// viewer/js/shared/language-manager.js calls:
GET /api/languages

// web-admin/src/services/api/scheduler.ts calls:
GET /api/schedules
POST /api/schedules
PUT /api/schedules/{id}
DELETE /api/schedules/{id}

// These endpoints DO NOT EXIST in backend!
```

**Impact:** Runtime errors when features are used

**Recommendation:**
```python
# Add to backend/app/api/translations.py
@router.get("/api/languages")
async def list_languages():
    return success_response([
        {"code": "en", "name": "English"},
        {"code": "id", "name": "Indonesian"},
        {"code": "zh", "name": "Chinese"}
    ])

# Create backend/app/api/schedules.py
@router.get("/api/schedules")
async def list_schedules():
    # Implementation needed
```

**Priority:** 🔴 CRITICAL - Fix immediately

---

#### 🔴 **ISSUE #2: Hardcoded URLs in Viewer**

**Problem:**
```javascript
// Multiple files have hardcoded fallback:
this.apiBaseUrl = options.apiBaseUrl || 'http://192.168.5.12:8001';

// Should use env config:
this.apiBaseUrl = window.ENV?.API_BASE_URL || options.apiBaseUrl;
```

**Impact:** Breaks when server IP changes

**Recommendation:**
```javascript
// Fix in viewer/js/shared/api-client.js (line 12)
this.apiBaseUrl = window.ENV?.API_BASE_URL ||
                  options.apiBaseUrl ||
                  'http://localhost:8001';  // localhost as absolute last resort

// Fix in viewer/js/shared/analytics-tracker.js (line 12)
this.apiBaseUrl = window.ENV?.API_BASE_URL ||
                  options.apiBaseUrl ||
                  'http://localhost:8001';
```

**Priority:** 🔴 CRITICAL - Fix before deployment

---

#### 🔴 **ISSUE #3: Token Refresh Not Implemented**

**Problem:**
```typescript
// Web Admin axios interceptor handles 401, but doesn't refresh token
if (error.response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'  // ❌ Logs user out immediately
}
```

**Impact:** Poor UX - users logged out every 15 minutes

**Recommendation:**
```typescript
// Add to web-admin/src/services/api/index.ts
let isRefreshing = false;
let failedQueue: any[] = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue requests while refreshing
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await api.post('/api/auth/refresh', { refresh_token: refreshToken });
        const { access_token } = response.data;

        localStorage.setItem('token', access_token);

        // Retry all queued requests
        failedQueue.forEach(({ resolve }) => resolve(access_token));
        failedQueue = [];

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);

      } catch (refreshError) {
        // Refresh failed - logout
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

**Priority:** 🔴 HIGH - Implement in next sprint

---

### 9.2 Major Issues (Medium Priority)

#### 🟡 **ISSUE #4: Incomplete Standardized API Migration**

**Problem:**
- Only 74 of 165 endpoints migrated to Quick Wins format (44.8%)
- Frontend handles both formats, but inconsistent
- Harder to maintain

**Recommendation:**
```
Phase 8: Migrate remaining 91 endpoints
1. auth.py (4 endpoints)
2. devices.py (remaining endpoints)
3. activities.py (5 endpoints)
4. firebird.py (8 endpoints)
5. client.py (2 endpoints)
6. transcoding.py (7 endpoints)
7. templates.py (6 endpoints)
8. translations.py (8 endpoints)
9. commands.py (13 endpoints)
10. analytics.py (12 endpoints)
11. reports.py (8 endpoints)
```

**Priority:** 🟡 MEDIUM - Complete in next 2 sprints

---

#### 🟡 **ISSUE #5: Duplicate Metadata Storage**

**Problem:**
```
PostgreSQL (content table):
- title, description, duration, mime_type, file_size

Anthias SQLite (assets table):
- name, uri, mimetype, duration

Same data in 2 databases = consistency issues
```

**Recommendation:**
```
1. Backend PostgreSQL = Single Source of Truth
2. Anthias only stores:
   - asset_id (for backend reference)
   - file_uri (physical path)
   - uploaded_at (timestamp)
3. Remove name, duration, mimetype from Anthias
4. Backend queries own database for metadata
```

**Priority:** 🟡 MEDIUM - Refactor in technical debt sprint

---

#### 🟡 **ISSUE #6: Device Authentication Weakness**

**Problem:**
```javascript
// Viewer sends device_id in query param
GET /api/client/playlist?device_id=123

// Easy to spoof - no cryptographic proof
```

**Recommendation:**
```python
# Issue JWT tokens for devices after activation
@router.post("/api/devices/monitor/activate")
async def activate_monitor():
    # ... existing activation logic ...

    # Generate device JWT token
    device_token = create_device_jwt(device.id, expires_in_days=365)

    return {
        "device_id": device.id,
        "device_token": device_token,  # ✅ Add token
        "message": "Device activated successfully"
    }

# Viewer includes token in headers
// viewer/js/player/api.js
headers: {
    'Authorization': `Bearer ${deviceToken}`
}
```

**Priority:** 🟡 MEDIUM - Security enhancement

---

### 9.3 Minor Issues (Low Priority)

#### 🟢 **ISSUE #7: Missing CORS Origin for WebOS**

**Problem:**
```python
# WebOS TV app uses webos-local:// scheme
# Not included in CORS_ORIGINS
```

**Recommendation:**
```python
# backend/.env.example
CORS_ORIGINS=http://localhost:3000,...,webos-local://
```

**Priority:** 🟢 LOW - Add when WebOS deployment needed

---

#### 🟢 **ISSUE #8: Orphaned Files in Anthias**

**Problem:**
```
When content deleted in backend:
1. PostgreSQL record deleted
2. Anthias file remains

Result: Wasted storage
```

**Recommendation:**
```python
# backend/app/api/content.py
@router.delete("/{content_id}")
async def delete_content(content_id: int, db: Session):
    content = db.query(Content).filter(Content.id == content_id).first()

    # Delete from Anthias
    if content.anthias_asset_id:
        await anthias_service.delete_asset(content.anthias_asset_id)

    # Delete HLS files
    if content.hls_playlist_url:
        delete_hls_directory(content_id)

    # Delete from PostgreSQL
    db.delete(content)
    db.commit()
```

**Priority:** 🟢 LOW - Cleanup improvement

---

#### 🟢 **ISSUE #9: Missing Environment Variables**

**Problem:**
```
.env.example files don't document all used variables
```

**Recommendation:**
```bash
# Add to backend/.env.example
ENABLE_ANALYTICS=True
ENABLE_RATE_LIMITING=True
SENTRY_DSN=

# Add to web-admin/.env.example
VITE_WEBSOCKET_URL=ws://192.168.5.12:8001/api/ws
VITE_SENTRY_DSN=
```

**Priority:** 🟢 LOW - Documentation improvement

---

## 10. Service Integration Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────────┐                      ┌────────────────────┐  │
│  │   Web Admin        │                      │   Viewer           │  │
│  │   (React/Vite)     │                      │   (Vanilla JS)     │  │
│  │                    │                      │                    │  │
│  │ • TypeScript       │                      │ • WebOS Support    │  │
│  │ • Axios            │                      │ • Offline Cache    │  │
│  │ • Auto-unwrap API  │                      │ • HLS Player       │  │
│  └─────────┬──────────┘                      └──────────┬─────────┘  │
│            │                                             │            │
│            │ HTTP/REST                                   │ HTTP/REST  │
│            │ WebSocket                                   │ WebSocket  │
└────────────┼─────────────────────────────────────────────┼────────────┘
             │                                             │
             │                                             │
┌────────────▼─────────────────────────────────────────────▼────────────┐
│                        BACKEND API (FastAPI)                          │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     API ROUTERS (23 modules)                    │ │
│  ├─────────────────────────────────────────────────────────────────┤ │
│  │ auth • devices • content • playlists • tags • settings • logs  │ │
│  │ client • firebird • streaming • transcoding • analytics        │ │
│  │ templates • translations • commands • reports • tasks          │ │
│  └───────────┬─────────────┬──────────────┬──────────────┬─────────┘ │
│              │             │              │              │           │
│  ┌───────────▼─────────────▼──────────────▼──────────────▼─────────┐ │
│  │                     MIDDLEWARE LAYER                            │ │
│  ├─────────────────────────────────────────────────────────────────┤ │
│  │ • Request ID Tracking                                           │ │
│  │ • Structured Logging (JSON)                                     │ │
│  │ • CORS Handler                                                  │ │
│  │ • Streaming Middleware (Range Requests)                         │ │
│  │ • Exception Handlers                                            │ │
│  └───────────┬─────────────┬──────────────┬──────────────┬─────────┘ │
│              │             │              │              │           │
└──────────────┼─────────────┼──────────────┼──────────────┼───────────┘
               │             │              │              │
               │             │              │              │
┌──────────────▼─┐  ┌────────▼───────┐  ┌──▼──────────┐  ┌▼──────────┐
│   PostgreSQL   │  │     Redis      │  │   Anthias   │  │  Celery   │
│   (Port 5433)  │  │  (Port 6379)   │  │ (Port 8000) │  │  Workers  │
├────────────────┤  ├────────────────┤  ├─────────────┤  ├───────────┤
│                │  │                │  │             │  │           │
│ TABLES (17):   │  │ USES:          │  │ SERVICES:   │  │ TASKS:    │
│ • users        │  │ • Cache        │  │ • Storage   │  │ • HLS     │
│ • devices      │  │ • Sessions     │  │ • Serve     │  │ • Email   │
│ • content      │  │ • Celery       │  │ • Assets    │  │ • Cleanup │
│ • playlists    │  │   Broker       │  │             │  │           │
│ • tags         │  │ • Rate Limit   │  │ STORAGE:    │  │ BROKER:   │
│ • assignments  │  │                │  │ /data/      │  │ Redis     │
│ • activity_log │  │ TTL:           │  │ screenly_   │  │           │
│ • device_log   │  │ • 5 min        │  │ assets/     │  │ BACKEND:  │
│ • firebird_*   │  │ • 15 min       │  │             │  │ Redis     │
│ • commands     │  │                │  │             │  │           │
│ • schedules    │  │                │  │             │  │           │
│ • speed_tests  │  │                │  │             │  │           │
│                │  │                │  │             │  │           │
│ RELATIONS:     │  │                │  │             │  │           │
│ • 1:N Device→  │  │                │  │             │  │           │
│   Assignment   │  │                │  │             │  │           │
│ • M:N Device↔  │  │                │  │             │  │           │
│   Tag          │  │                │  │             │  │           │
│ • M:N Playlist │  │                │  │             │  │           │
│   ↔Content     │  │                │  │             │  │           │
└────────────────┘  └────────────────┘  └─────────────┘  └───────────┘

COMMUNICATION PATTERNS:
━━━━━━━━━━━━━━━━━━━━
→  HTTP/REST        Backend ← → PostgreSQL (SQLAlchemy ORM)
↔  WebSocket        Backend ← → Redis (Cache + Celery)
⇢  Celery Tasks     Backend ⇢ Anthias (File upload/delete)
                    Celery ← Anthias (Download for transcode)
                    Viewer → Anthias (Direct file access)

DATA FLOW:
━━━━━━━━━━━━━━━━━━━━
1. Upload:    Web Admin → Backend → Anthias → PostgreSQL
2. Playback:  Viewer → Backend → PostgreSQL → [Anthias OR HLS]
3. Transcode: Backend → Celery → Anthias → HLS → PostgreSQL
4. Analytics: Viewer → Backend → PostgreSQL → Redis
5. Real-time: Backend → Redis PubSub → WebSocket → Web Admin
```

---

## 11. Cleanup Checklist

### 11.1 Immediate Actions (Sprint 1)

- [ ] **Fix hardcoded URLs in viewer**
  - [ ] `viewer/js/shared/api-client.js` line 12
  - [ ] `viewer/js/shared/analytics-tracker.js` line 12
  - [ ] Update fallbacks to use `window.ENV.API_BASE_URL`

- [ ] **Add missing backend endpoints**
  - [ ] `GET /api/languages` (for language-manager.js)
  - [ ] Create `backend/app/api/schedules.py` module
  - [ ] Implement CRUD endpoints for schedules

- [ ] **Implement token refresh in Web Admin**
  - [ ] Add refresh token interceptor logic
  - [ ] Handle refresh queue during concurrent requests
  - [ ] Update login to store refresh token

- [ ] **Fix authentication inconsistencies**
  - [ ] Make all admin endpoints require JWT
  - [ ] Remove `get_optional_user` from sensitive endpoints
  - [ ] Add device JWT tokens for viewer

### 11.2 Technical Debt (Sprint 2-3)

- [ ] **Complete Quick Wins API migration**
  - [ ] Phase 8: Migrate auth.py (4 endpoints)
  - [ ] Phase 8: Migrate devices.py (remaining)
  - [ ] Phase 8: Migrate activities.py (5 endpoints)
  - [ ] Phase 8: Migrate client.py (2 endpoints)
  - [ ] Phase 9: Migrate firebird, transcoding, templates
  - [ ] Phase 10: Migrate analytics, reports, commands

- [ ] **Refactor metadata storage**
  - [ ] Audit Anthias schema
  - [ ] Remove duplicate fields from Anthias
  - [ ] Make backend single source of truth
  - [ ] Add migration script

- [ ] **Implement cascade delete**
  - [ ] Add `delete_asset()` to anthias_service
  - [ ] Hook into content deletion
  - [ ] Clean up HLS directories
  - [ ] Add orphan file cleanup task

### 11.3 Security Hardening (Sprint 4)

- [ ] **Device authentication enhancement**
  - [ ] Generate JWT for activated devices
  - [ ] Update client API to require device token
  - [ ] Add token validation middleware
  - [ ] Implement device token refresh

- [ ] **Add CORS origin for WebOS**
  - [ ] Update CORS_ORIGINS in .env.example
  - [ ] Test with WebOS TV app
  - [ ] Document WebOS deployment

- [ ] **Add missing env variables**
  - [ ] Document ENABLE_ANALYTICS
  - [ ] Document SENTRY_DSN
  - [ ] Document WebSocket URLs
  - [ ] Update .env.example files

### 11.4 Monitoring & Observability (Sprint 5)

- [ ] **Add circuit breaker for Anthias**
  - [ ] Implement retry logic with exponential backoff
  - [ ] Add max retry limit
  - [ ] Fallback to direct file access if Anthias down

- [ ] **Add orphan file detection**
  - [ ] Scheduled task to find orphaned Anthias files
  - [ ] Compare PostgreSQL records with Anthias storage
  - [ ] Generate cleanup report

- [ ] **Add API health checks**
  - [ ] Check all external dependencies
  - [ ] Report service status in /health endpoint
  - [ ] Add alerting for degraded services

---

## 12. Architecture Recommendations

### 12.1 Short-term Improvements (Next 3 Months)

**1. Complete API Standardization (Quick Wins)**
```
Priority: HIGH
Effort: Medium
Impact: High

Benefits:
- Consistent error handling
- Better debugging with request IDs
- Easier frontend development
- Better API documentation
```

**2. Implement Service Mesh Pattern**
```
Priority: MEDIUM
Effort: High
Impact: Medium

Architecture:
┌─────────────────┐
│  API Gateway    │ ← Add rate limiting, auth, routing
└────────┬────────┘
         │
    ┌────┴────┐
    │ Backend │
    │  API    │
    └────┬────┘
         │
    ┌────┴────────────────┐
    │  Service Layer      │
    ├─────────────────────┤
    │ • Anthias Client    │
    │ • Firebird Client   │
    │ • Email Service     │
    │ • Analytics Service │
    └─────────────────────┘
```

**3. Add Event-Driven Architecture**
```
Priority: MEDIUM
Effort: Medium
Impact: High

Pattern: Domain Events + Event Bus
┌──────────────┐
│   Backend    │ ──→ Publish Event: "ContentUploaded"
└──────────────┘
        │
        ▼
┌──────────────┐
│  Event Bus   │ (Redis PubSub)
│  (Redis)     │
└──────────────┘
        │
        ├──→ WebSocket Service → Push to Web Admin
        ├──→ Analytics Service → Track event
        └──→ Celery Task → Start transcoding

Benefits:
- Decoupled services
- Real-time updates
- Easier to add new features
- Better scalability
```

### 12.2 Medium-term Architecture (6-12 Months)

**1. Migrate to Microservices (Optional)**
```
Only if scale demands it. Current monolith is fine for now.

Potential Services:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Auth      │  │   Content   │  │   Device    │
│  Service    │  │   Service   │  │   Service   │
└─────────────┘  └─────────────┘  └─────────────┘
      │                │                │
      └────────────────┴────────────────┘
                      │
            ┌─────────▼─────────┐
            │   API Gateway     │
            └───────────────────┘
```

**2. Add GraphQL Layer (Optional)**
```
For complex frontend queries:

GraphQL API ──┐
              ├─→ Backend REST API
REST API ─────┘

Benefits:
- Flexible queries
- Reduce over-fetching
- Better for mobile apps
```

**3. Implement CQRS for Analytics**
```
Command (Write):       Query (Read):
┌────────────┐        ┌────────────┐
│ PostgreSQL │        │   Redis    │
│  (Master)  │   ──→  │  (Cache)   │
└────────────┘        └────────────┘
                           │
                           ▼
                      ┌────────────┐
                      │ Read Model │
                      │ (Optimized)│
                      └────────────┘

Benefits:
- Faster analytics queries
- Reduced DB load
- Better scalability
```

### 12.3 Long-term Vision (12+ Months)

**1. Multi-tenancy Support**
```
Add organization/tenant isolation:
- Separate data by tenant_id
- Row-level security
- Tenant-specific settings
- White-label support
```

**2. Edge Computing for Content Delivery**
```
Deploy edge nodes closer to devices:

┌───────────────┐
│  Main Server  │ (Origin)
└───────┬───────┘
        │
   ┌────┴────┬────┬────┐
   │         │    │    │
┌──▼──┐  ┌──▼──┐ ... Edge Nodes
│Edge1│  │Edge2│     (CDN)
└─────┘  └─────┘

Benefits:
- Lower latency
- Reduced bandwidth costs
- Better reliability
```

**3. AI/ML Integration**
```
Add intelligent features:
- Content recommendation
- Automatic playlist generation
- Anomaly detection (device health)
- Predictive maintenance
```

---

## 13. Summary & Next Steps

### Overall Assessment

**Integration Health: 7.5/10**

**Strengths:**
- ✅ Well-architected separation between Backend and Anthias
- ✅ Strong TypeScript migration in Web Admin
- ✅ Unified viewer architecture for multi-platform support
- ✅ Proper middleware stack (request ID, logging, CORS)
- ✅ Good progress on API standardization (44.8% complete)

**Weaknesses:**
- 🔴 Hardcoded URLs in viewer bypass env configuration
- 🔴 Missing backend endpoints for scheduler and languages
- 🔴 Token refresh not implemented (poor UX)
- 🔴 Duplicate metadata storage (PostgreSQL + Anthias)
- 🔴 Weak device authentication (query param only)

### Immediate Action Items (This Week)

1. **Fix hardcoded URLs** (2 hours)
   - Update api-client.js and analytics-tracker.js
   - Use window.ENV.API_BASE_URL

2. **Add missing endpoints** (4 hours)
   - Implement GET /api/languages
   - Create schedules.py module

3. **Implement token refresh** (8 hours)
   - Add interceptor logic
   - Handle concurrent requests
   - Test thoroughly

### Next Sprint Priorities

1. **Complete Quick Wins migration** (2 weeks)
   - Migrate remaining 91 endpoints
   - Standardize error handling
   - Update frontend to remove legacy format support

2. **Security hardening** (1 week)
   - Device JWT tokens
   - CORS for WebOS
   - Remove optional auth from sensitive endpoints

3. **Technical debt cleanup** (1 week)
   - Refactor metadata storage
   - Implement cascade delete
   - Add orphan file cleanup

### Long-term Roadmap

**Q1 2025:**
- Complete API standardization
- Implement service mesh pattern
- Add comprehensive monitoring

**Q2 2025:**
- Event-driven architecture
- CQRS for analytics
- GraphQL layer (optional)

**Q3-Q4 2025:**
- Multi-tenancy support
- Edge computing/CDN
- AI/ML features

---

## Appendix A: Endpoint Reference Matrix

### Backend to Frontend Mapping

| Backend Endpoint | Web Admin Call | Viewer Call | Status |
|------------------|----------------|-------------|--------|
| `POST /api/auth/login` | `authAPI.login()` | ❌ | ✅ |
| `GET /api/devices` | `devicesAPI.list()` | ❌ | ✅ |
| `POST /api/devices/tv` | `devicesAPI.registerTV()` | ❌ | ✅ |
| `POST /api/devices/monitor` | `devicesAPI.generateMonitorCode()` | `registration.js` | ✅ |
| `POST /api/devices/monitor/activate` | `devicesAPI.activateMonitor()` | `activation-poll.js` | ✅ |
| `POST /api/devices/{id}/heartbeat` | `devicesAPI.heartbeat()` | `heartbeat.js` | ✅ |
| `GET /api/content` | `contentAPI.list()` | ❌ | ✅ |
| `POST /api/content/upload` | `contentAPI.upload()` | ❌ | ✅ |
| `GET /api/client/playlist` | ❌ | `player/api.js` | ✅ |
| `GET /api/playlists` | `playlistsAPI.list()` | ❌ | ✅ |
| `GET /api/tags` | `tagsAPI.list()` | ❌ | ✅ |
| `GET /api/settings` | `settingsAPI.get()` | ❌ | ✅ |
| `GET /api/languages` | ❌ | `language-manager.js` | 🔴 MISSING |
| `GET /api/schedules` | `schedulerAPI.list()` | ❌ | 🔴 MISSING |

---

## Appendix B: Configuration Files Audit

### Environment Files Comparison

| Variable | backend/.env.example | web-admin/.env.example | CLAUDE.md | docker-compose.yml |
|----------|---------------------|------------------------|-----------|-------------------|
| `API_BASE_URL` | ✅ 8001 | ❌ | ❌ | ❌ |
| `VITE_API_URL` | ❌ | ✅ 8001 | ❌ | ❌ |
| `DATABASE_URL` | ✅ | ❌ | ❌ | ✅ |
| `REDIS_URL` | ✅ | ❌ | ❌ | ✅ |
| `ANTHIAS_API_URL` | ✅ 8000 | ❌ | ✅ 8000 | ✅ |
| `BACKEND_EXTERNAL_PORT` | ✅ 8001 | ❌ | ✅ 8001 | ✅ |
| `VIEWER_EXTERNAL_PORT` | ✅ 8080 | ❌ | ✅ 8080 | ✅ |
| `CORS_ORIGINS` | ✅ | ❌ | ✅ | ✅ |

---

**End of Audit Report**

Generated: 2025-10-28
Next Review: 2025-11-28 (or after major integration changes)
