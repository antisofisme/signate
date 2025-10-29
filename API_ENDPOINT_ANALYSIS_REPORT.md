# API Endpoint Analysis Report
**Smart TV Digital Signage System**
**Generated:** 2025-10-28
**Analysis Type:** Backend vs Frontend Endpoint Comparison

---

## Executive Summary

This report analyzes all backend API endpoints and compares them with frontend API calls to identify mismatches, inconsistencies, and potential issues.

**Key Findings:**
- ✅ **Total Backend Endpoints:** 82 endpoints across 12 router modules
- ✅ **Total Frontend API Calls:** 67 API functions in api.js
- ⚠️ **Critical Mismatches:** 3 issues found
- ⚠️ **Medium Issues:** 4 deprecated/unused endpoints
- ℹ️ **Low Priority:** 2 naming inconsistencies

---

## 1. Backend Endpoints Inventory

### 1.1 Authentication (`/api/auth`) - 4 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| POST | `/api/auth/login` | ✅ `authAPI.login()` |
| POST | `/api/auth/refresh` | ❌ Not used |
| GET | `/api/auth/me` | ✅ `authAPI.me()` |
| POST | `/api/auth/logout` | ✅ `authAPI.logout()` |

### 1.2 Devices (`/api/devices`) - 25 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| GET | `/api/devices/` | ✅ `devicesAPI.list()` |
| GET | `/api/devices/{device_id}` | ✅ Used in modals |
| GET | `/api/devices/{device_id}/preview` | ✅ `devicesAPI.preview()` |
| POST | `/api/devices/tv` | ✅ `devicesAPI.registerTV()` |
| POST | `/api/devices/monitor` | ✅ `devicesAPI.generateMonitorCode()` |
| POST | `/api/devices/monitor/register` | ❌ Viewer only (no auth) |
| POST | `/api/devices/monitor/activate` | ✅ `devicesAPI.activateMonitor()` |
| PUT | `/api/devices/{device_id}` | ✅ `devicesAPI.update()` |
| DELETE | `/api/devices/{device_id}` | ✅ `devicesAPI.delete()` |
| POST | `/api/devices/{device_id}/release` | ✅ `devicesAPI.release()` |
| POST | `/api/devices/{device_id}/replace-with-pending/{pending_id}` | ✅ `devicesAPI.replaceWithPending()` |
| GET | `/api/devices/check-activation/{code}` | ❌ Viewer only (polling) |
| POST | `/api/devices/heartbeat` | ✅ `devicesAPI.heartbeat()` |
| POST | `/api/devices/{device_id}/commands` | ✅ `devicesAPI.queueCommand()` |
| POST | `/api/devices/{device_id}/commands/reset` | ❌ Not exposed to frontend |
| GET | `/api/devices/{device_id}/commands/pending` | ❌ Viewer only |
| POST | `/api/devices/{device_id}/commands/{cmd_id}/execute` | ❌ Viewer only |
| GET | `/api/devices/{device_id}/content` | ✅ `devicesAPI.getContent()` |
| POST | `/api/devices/{device_id}/content` | ⚠️ Wrong - uses contentAPI |
| DELETE | `/api/devices/{device_id}/content/{content_id}` | ✅ `devicesAPI.unassignContent()` |

### 1.3 Content (`/api/content`) - 10 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| POST | `/api/content/upload` | ✅ `contentAPI.upload()` |
| GET | `/api/content/` | ✅ `contentAPI.list()` |
| GET | `/api/content/{content_id}` | ✅ `contentAPI.get()` |
| PATCH | `/api/content/{content_id}` | ✅ `contentAPI.update()` |
| DELETE | `/api/content/{content_id}` | ✅ `contentAPI.delete()` |
| POST | `/api/content/{content_id}/assign` | ✅ `contentAPI.assign()` |
| DELETE | `/api/content/{content_id}/assign` | ✅ `contentAPI.unassign()` |
| GET | `/api/content/{content_id}/assignments` | ✅ `contentAPI.getAssignments()` |
| GET | `/api/content/{content_id}/image` | ❌ Not used (proxy endpoint) |
| GET | `/api/content/{content_id}/video` | ❌ Not used (proxy endpoint) |

### 1.4 Playlists (`/api/playlists`) - 14 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| GET | `/api/playlists` | ✅ `playlistsAPI.list()` |
| POST | `/api/playlists` | ✅ `playlistsAPI.create()` |
| GET | `/api/playlists/{playlist_id}` | ✅ `playlistsAPI.get()` |
| PATCH | `/api/playlists/{playlist_id}` | ✅ `playlistsAPI.update()` |
| DELETE | `/api/playlists/{playlist_id}` | ✅ `playlistsAPI.delete()` |
| GET | `/api/playlists/{playlist_id}/content` | ✅ `playlistsAPI.getContent()` |
| POST | `/api/playlists/{playlist_id}/content` | ✅ `playlistsAPI.assignContent()` |
| DELETE | `/api/playlists/{playlist_id}/content/{item_id}` | ✅ `playlistsAPI.removeContent()` |
| PATCH | `/api/playlists/{playlist_id}/reorder` | ✅ `playlistsAPI.reorderContent()` |
| GET | `/api/playlists/{playlist_id}/assignments` | ✅ `playlistsAPI.getAssignments()` |
| POST | `/api/playlists/{playlist_id}/assign/devices` | ✅ `playlistsAPI.assignToDevices()` |
| POST | `/api/playlists/{playlist_id}/assign/tags` | ✅ `playlistsAPI.assignToTags()` |
| DELETE | `/api/playlists/{playlist_id}/assign/devices` | ✅ `playlistsAPI.unassignFromDevices()` |
| DELETE | `/api/playlists/{playlist_id}/assign/tags` | ✅ `playlistsAPI.unassignFromTags()` |

### 1.5 Tags (`/api/tags`) - 9 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| GET | `/api/tags` | ✅ `tagsAPI.list()` |
| POST | `/api/tags` | ✅ `tagsAPI.create()` |
| GET | `/api/tags/{tag_id}` | ✅ `tagsAPI.get()` |
| PATCH | `/api/tags/{tag_id}` | ✅ `tagsAPI.update()` |
| DELETE | `/api/tags/{tag_id}` | ✅ `tagsAPI.delete()` |
| POST | `/api/tags/assign` | ✅ `tagsAPI.assign()` |
| DELETE | `/api/tags/assign` | ✅ `tagsAPI.unassign()` |
| GET | `/api/tags/{tag_id}/devices` | ✅ `tagsAPI.getDevices()` |
| GET | `/api/tags/{tag_id}/content` | ✅ `tagsAPI.getContent()` |

### 1.6 Client API (`/api/client`) - 2 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| GET | `/api/client/playlist` | ✅ `clientAPI.getPlaylist()` (testing) |
| GET | `/api/client/status` | ✅ `clientAPI.getStatus()` (testing) |

### 1.7 Device Logs (`/api`) - 4 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| POST | `/api/client/logs` | ❌ Viewer only (no auth) |
| POST | `/api/client/logs/batch` | ❌ Viewer only (no auth) |
| GET | `/api/devices/{device_id}/logs` | ✅ `devicesAPI.getLogs()` |
| DELETE | `/api/devices/{device_id}/logs` | ✅ `devicesAPI.deleteLogs()` |

### 1.8 Speed Test (`/api/speedtest`) - 5 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| POST | `/api/speedtest/upload` | ❌ Viewer only (testing) |
| GET | `/api/speedtest/download` | ❌ Viewer only (testing) |
| POST | `/api/speedtest/devices/{device_id}/speedtest` | ❌ Viewer only (store) |
| GET | `/api/speedtest/devices/{device_id}/speedtest` | ✅ `devicesAPI.getSpeedTests()` |
| GET | `/api/speedtest/devices/{device_id}/speedtest/latest` | ✅ `devicesAPI.getLatestSpeedTest()` |

### 1.9 Activities (`/api/activities`) - 4 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| GET | `/api/activities` | ✅ `activitiesAPI.list()` |
| GET | `/api/activities/stats` | ✅ `activitiesAPI.stats()` |
| GET | `/api/activities/{activity_id}` | ✅ `activitiesAPI.get()` |
| POST | `/api/activities` | ✅ `activitiesAPI.create()` |
| DELETE | `/api/activities/cleanup` | ✅ `activitiesAPI.cleanup()` |

### 1.10 Settings (`/api/settings`) - 4 endpoints
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| GET | `/api/settings/system/info` | ✅ `settingsAPI.getSystemInfo()` |
| GET | `/api/settings/system/backup` | ✅ `settingsAPI.backupDatabase()` |
| POST | `/api/settings/system/clear-cache` | ✅ `settingsAPI.clearCache()` |
| GET | `/api/settings/system/database-stats` | ❌ Not exposed to frontend |

### 1.11 Firebird (`/api/firebird`) - NOT IMPLEMENTED
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| GET | `/api/firebird/configs` | ✅ `firebirdAPI.listConfigs()` |
| Various | (Other endpoints) | ✅ Defined but backend not ready |

### 1.12 WebSocket (`/api`) - 1 endpoint
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| WebSocket | `/api/ws/logs/{device_id}` | ❌ Not used yet |

### 1.13 Widgets API - NOT IMPLEMENTED
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| Various | `/api/widgets/*` | ⚠️ Frontend defined, backend missing |

### 1.14 Users API - NOT IMPLEMENTED
| Method | Endpoint | Frontend Usage |
|--------|----------|----------------|
| Various | `/api/users/*` | ⚠️ Frontend defined, backend missing |

---

## 2. Critical Mismatches (Must Fix)

### 🔴 CRITICAL #1: Device Content Assignment Endpoint Mismatch
**Issue:** Frontend uses wrong endpoint for assigning content to devices

**Backend Endpoint:**
```python
# devices.py line 1599-1682
@router.post("/{device_id}/content")
def assign_content_to_device(device_id: int, assignment_data: ContentAssignRequest, ...)
```

**Frontend Call (WRONG):**
```javascript
// api.js line 200
assignContent: (deviceId, contentId, priority = 0) =>
  api.post(`/api/content/${contentId}/assign`, { device_id: deviceId, priority }),
```

**Problem:** Frontend calls `/api/content/{contentId}/assign` which accepts BOTH device_id and tag_id, but backend also has a dedicated `/api/devices/{deviceId}/content` endpoint specifically for device assignments.

**Impact:** Works but inconsistent. Should use the dedicated device endpoint.

**Recommended Fix:**
```javascript
// Update api.js line 200
assignContent: (deviceId, contentId, priority = 0, displayOrder = 0, isActive = true) =>
  api.post(`/api/devices/${deviceId}/content`, {
    content_id: contentId,
    priority,
    display_order: displayOrder,
    is_active: isActive
  }),
```

---

### 🔴 CRITICAL #2: Widgets API Not Implemented
**Issue:** Frontend defines widgets API but backend has NO implementation

**Frontend Calls:**
```javascript
// api.js lines 262-271
export const widgetsAPI = {
  list: (type) => api.get('/api/widgets', { params: { type } }),
  create: (data) => api.post('/api/widgets', data),
  get: (id) => api.get(`/api/widgets/${id}`),
  update: (id, data) => api.patch(`/api/widgets/${id}`, data),
  delete: (id) => api.delete(`/api/widgets/${id}`),
  assign: (id, data) => api.post(`/api/widgets/${id}/assign`, data),
  unassign: (id, data) => api.delete(`/api/widgets/${id}/assign`, { data }),
}
```

**Backend:** No `/api/widgets` router exists in `main.py`

**Impact:** Any frontend call to widgets API will result in 404 errors

**Recommended Fix:** Either:
1. Implement backend widgets API router, or
2. Remove widgets API from frontend (if not needed)

---

### 🔴 CRITICAL #3: Users API Not Implemented
**Issue:** Frontend defines users API but backend has NO implementation

**Frontend Calls:**
```javascript
// api.js lines 273-281
export const usersAPI = {
  list: () => api.get('/api/users'),
  create: (data) => api.post('/api/users', data),
  get: (id) => api.get(`/api/users/${id}`),
  update: (id, data) => api.patch(`/api/users/${id}`, data),
  delete: (id) => api.delete(`/api/users/${id}`),
  resetPassword: (id, data) => api.post(`/api/users/${id}/reset-password`, data),
}
```

**Backend:** No `/api/users` router exists in `main.py`

**Impact:** Any frontend call to users API will result in 404 errors

**Recommended Fix:** Either:
1. Implement backend users management API, or
2. Remove users API from frontend (if user management not needed)

---

## 3. Medium Priority Issues

### ⚠️ MEDIUM #1: Auth Refresh Token Not Used
**Issue:** Backend implements token refresh but frontend never calls it

**Backend Endpoint:**
```python
# auth.py line 109-189
@router.post("/refresh")
def refresh_token(refresh_data: RefreshTokenRequest, ...)
```

**Frontend:** No usage found in api.js

**Impact:** Users need to re-login when access token expires (no silent refresh)

**Recommendation:** Implement token refresh logic in axios interceptor for better UX

---

### ⚠️ MEDIUM #2: Content Proxy Endpoints Not Used
**Issue:** Backend provides image/video proxy endpoints but frontend doesn't use them

**Backend Endpoints:**
```python
# content.py lines 1034-1147
@router.get("/{content_id}/image")
@router.get("/{content_id}/video")
```

**Frontend:** Not used (direct Anthias URLs used instead)

**Impact:** No impact if Anthias CORS is configured. These are fallback proxies.

**Recommendation:** Keep for backward compatibility, but document that direct Anthias URLs are preferred

---

### ⚠️ MEDIUM #3: Database Stats Endpoint Not Exposed
**Issue:** Backend implements database stats but frontend doesn't call it

**Backend Endpoint:**
```python
# settings.py line 434-509
@router.get("/settings/system/database-stats")
```

**Frontend:** Not defined in settingsAPI

**Impact:** Admin cannot view detailed database statistics from UI

**Recommendation:** Add to frontend if database monitoring is needed

---

### ⚠️ MEDIUM #4: WebSocket Endpoint Not Used
**Issue:** Backend implements WebSocket for real-time logs but frontend doesn't connect

**Backend Endpoint:**
```python
# websocket.py (from main.py line 74)
# WebSocket endpoint for real-time device logs
```

**Frontend:** Not used (polling used instead)

**Impact:** Real-time log streaming not available (less efficient polling used)

**Recommendation:** Implement WebSocket connection for real-time logs if performance matters

---

## 4. Low Priority Issues

### ℹ️ LOW #1: Inconsistent Parameter Naming
**Issue:** Some endpoints use `device_id` in path vs query parameter

**Examples:**
- `GET /api/devices/{device_id}` (path param) ✅
- `GET /api/client/playlist?device_id={id}` (query param) ✅

**Impact:** No functional issue, just inconsistency

**Recommendation:** Keep current implementation (both are valid patterns)

---

### ℹ️ LOW #2: Missing Pagination on Activities
**Issue:** Activities list endpoint supports pagination but frontend doesn't use skip/limit

**Backend:**
```python
# activities.py line 72-176
async def list_activities(skip: int = 0, limit: int = 50, ...)
```

**Frontend:**
```javascript
// api.js line 301
list: (params) => api.get('/api/activities', { params }),
```

**Impact:** Frontend can pass params but may not be using them correctly

**Recommendation:** Verify frontend pagination implementation for large activity logs

---

## 5. Endpoint Usage Summary

### 5.1 Backend Endpoints by Status
| Status | Count | Description |
|--------|-------|-------------|
| ✅ Used | 57 | Actively called by frontend |
| ❌ Viewer Only | 10 | No auth, used by viewer devices |
| ⚠️ Unused | 8 | Backend exists but frontend doesn't call |
| 🔴 Missing | 13 | Frontend calls but backend missing |

### 5.2 Frontend API Definitions by Status
| Status | Count | Description |
|--------|-------|-------------|
| ✅ Working | 54 | Correctly mapped to backend |
| ⚠️ Mismatch | 1 | Wrong endpoint used (content assignment) |
| 🔴 404 Error | 13 | Backend not implemented (widgets, users) |

---

## 6. Recommendations

### 6.1 Immediate Actions (Critical)
1. **Fix Device Content Assignment** - Update frontend to use `/api/devices/{id}/content` endpoint
2. **Remove or Implement Widgets API** - Either implement backend or remove from frontend
3. **Remove or Implement Users API** - Either implement backend or remove from frontend

### 6.2 Short-term Improvements (Medium)
1. **Implement Token Refresh** - Add axios interceptor for automatic token refresh
2. **Add Database Stats to Frontend** - Expose database statistics endpoint in UI
3. **Document Proxy Endpoints** - Clarify when to use content proxy vs direct URLs

### 6.3 Long-term Enhancements (Low)
1. **Implement WebSocket** - Replace polling with WebSocket for real-time logs
2. **Standardize Pagination** - Ensure consistent pagination across all list endpoints
3. **API Versioning** - Consider adding `/api/v1` prefix for future API changes

---

## 7. Testing Checklist

- [ ] Test device content assignment with corrected endpoint
- [ ] Verify widgets API calls don't break UI (should handle 404 gracefully)
- [ ] Verify users API calls don't break UI (should handle 404 gracefully)
- [ ] Test all activity log endpoints with pagination
- [ ] Verify speed test endpoints work for both viewer and admin
- [ ] Test database backup download functionality
- [ ] Verify all device command endpoints work correctly
- [ ] Test playlist assignment to devices and tags

---

## 8. Migration Checklist

### Phase 1: Fix Critical Issues
- [ ] Update frontend device content assignment to use correct endpoint
- [ ] Decide on widgets API: implement or remove
- [ ] Decide on users API: implement or remove
- [ ] Test all updated endpoints

### Phase 2: Implement Medium Priority
- [ ] Add token refresh logic to axios interceptor
- [ ] Add database stats to System Settings page
- [ ] Document content proxy usage

### Phase 3: Future Enhancements
- [ ] Implement WebSocket for real-time logs
- [ ] Add comprehensive pagination to all list views
- [ ] Consider API versioning strategy

---

## Appendix A: Complete Endpoint Matrix

### Backend Endpoints (82 total)
```
Authentication (4):
  POST   /api/auth/login
  POST   /api/auth/refresh
  GET    /api/auth/me
  POST   /api/auth/logout

Devices (25):
  GET    /api/devices/
  GET    /api/devices/{device_id}
  GET    /api/devices/{device_id}/preview
  POST   /api/devices/tv
  POST   /api/devices/monitor
  POST   /api/devices/monitor/register
  POST   /api/devices/monitor/activate
  PUT    /api/devices/{device_id}
  DELETE /api/devices/{device_id}
  POST   /api/devices/{device_id}/release
  POST   /api/devices/{device_id}/replace-with-pending/{pending_id}
  GET    /api/devices/check-activation/{code}
  POST   /api/devices/heartbeat
  POST   /api/devices/{device_id}/commands
  POST   /api/devices/{device_id}/commands/reset
  GET    /api/devices/{device_id}/commands/pending
  POST   /api/devices/{device_id}/commands/{cmd_id}/execute
  GET    /api/devices/{device_id}/content
  POST   /api/devices/{device_id}/content
  DELETE /api/devices/{device_id}/content/{content_id}

Content (10):
  POST   /api/content/upload
  GET    /api/content/
  GET    /api/content/{content_id}
  PATCH  /api/content/{content_id}
  DELETE /api/content/{content_id}
  POST   /api/content/{content_id}/assign
  DELETE /api/content/{content_id}/assign
  GET    /api/content/{content_id}/assignments
  GET    /api/content/{content_id}/image
  GET    /api/content/{content_id}/video

Playlists (14):
  GET    /api/playlists
  POST   /api/playlists
  GET    /api/playlists/{playlist_id}
  PATCH  /api/playlists/{playlist_id}
  DELETE /api/playlists/{playlist_id}
  GET    /api/playlists/{playlist_id}/content
  POST   /api/playlists/{playlist_id}/content
  DELETE /api/playlists/{playlist_id}/content/{item_id}
  PATCH  /api/playlists/{playlist_id}/reorder
  GET    /api/playlists/{playlist_id}/assignments
  POST   /api/playlists/{playlist_id}/assign/devices
  POST   /api/playlists/{playlist_id}/assign/tags
  DELETE /api/playlists/{playlist_id}/assign/devices
  DELETE /api/playlists/{playlist_id}/assign/tags

Tags (9):
  GET    /api/tags
  POST   /api/tags
  GET    /api/tags/{tag_id}
  PATCH  /api/tags/{tag_id}
  DELETE /api/tags/{tag_id}
  POST   /api/tags/assign
  DELETE /api/tags/assign
  GET    /api/tags/{tag_id}/devices
  GET    /api/tags/{tag_id}/content

Client (2):
  GET    /api/client/playlist
  GET    /api/client/status

Logs (4):
  POST   /api/client/logs
  POST   /api/client/logs/batch
  GET    /api/devices/{device_id}/logs
  DELETE /api/devices/{device_id}/logs

Speed Test (5):
  POST   /api/speedtest/upload
  GET    /api/speedtest/download
  POST   /api/speedtest/devices/{device_id}/speedtest
  GET    /api/speedtest/devices/{device_id}/speedtest
  GET    /api/speedtest/devices/{device_id}/speedtest/latest

Activities (5):
  GET    /api/activities
  GET    /api/activities/stats
  GET    /api/activities/{activity_id}
  POST   /api/activities
  DELETE /api/activities/cleanup

Settings (4):
  GET    /api/settings/system/info
  GET    /api/settings/system/backup
  POST   /api/settings/system/clear-cache
  GET    /api/settings/system/database-stats

WebSocket (1):
  WS     /api/ws/logs/{device_id}
```

### Frontend API Calls (67 total)
See api.js for complete frontend API definitions.

---

**Report End**
