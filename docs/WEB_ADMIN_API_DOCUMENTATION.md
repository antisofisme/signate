# Web-Admin Frontend - Complete API Calls Documentation

## Overview
This document provides a comprehensive reference of all API calls made by the web-admin React/Vite frontend application. The API client is configured with automatic response unwrapping and Bearer token authentication.

## Configuration

**File**: `/web-admin/src/services/api.js`

### API Base URL
- Configured via environment variable: `VITE_API_URL`
- Must be set in `.env` file (e.g., `http://192.168.5.12:8001`)

### Authentication
- Automatic Bearer token injection from `localStorage.getItem('token')`
- Token is set during login flow
- 401 responses automatically clear token and redirect to `/login`

### Response Format
- Backend returns standardized format: `{ success: true, data: {...}, meta: {...} }`
- Response interceptor automatically unwraps to just the data payload
- Backward compatible with legacy response formats

---

## API Modules & Endpoints

### 1. AUTH API (`authAPI`)

**Location**: `src/services/api.js` (lines 176-181)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **POST** | `/api/auth/login` | `{ username, password }` | `{ access_token, ... }` | User authentication in Login page |
| **POST** | `/api/auth/logout` | - | - | Logout flow in AuthContext |
| **GET** | `/api/auth/me` | - | `{ id, username, email, ... }` | Get current user info on app load & after login |

**Used By**:
- `src/pages/Login.tsx` - Login form submission
- `src/contexts/AuthContext.tsx` - Auth state initialization and user profile

---

### 2. DEVICES API (`devicesAPI`)

**Location**: `src/services/api.js` (lines 184-207)

#### Device List & Management

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/devices` | `{ params }` | `{ devices: [], total }` | Fetch all devices with pagination/filters |
| **POST** | `/api/devices/tv` | `{ device_name, platform, ... }` | `{ id, ... }` | Register new TV device |
| **POST** | `/api/devices/monitor` | `{ device_name, activation_code, ... }` | `{ id, ... }` | Generate monitor activation code |
| **POST** | `/api/devices/monitor/activate` | `{ activation_code, ... }` | `{ id, ... }` | Activate monitor device |
| **PUT** | `/api/devices/{id}` | `{ status, device_name, ... }` | `{ id, ... }` | Update device info (approve/rename/etc) |
| **DELETE** | `/api/devices/{id}` | - | - | Delete device |
| **POST** | `/api/devices/{id}/release` | - | - | Release device (mark inactive) |
| **POST** | `/api/devices/{id}/replace-with-pending/{pendingId}` | - | - | Replace active device with pending device |
| **POST** | `/api/devices/{id}/heartbeat` | - | - | Send device heartbeat (updates last_seen) |
| **GET** | `/api/devices/{id}/logs` | `{ params }` | `{ logs: [], total }` | Fetch device logs with pagination |
| **DELETE** | `/api/devices/{id}/logs` | `{ params }` | - | Delete device logs |
| **POST** | `/api/devices/{id}/commands` | `{ command_type, ... }` | - | Queue command for device |
| **GET** | `/api/devices/{id}/content` | `{ params }` | `[{ content_id, priority, ... }]` | Get content assigned to device |
| **POST** | `/api/content/{contentId}/assign` | `{ device_id, priority }` | - | Assign content to device |
| **DELETE** | `/api/devices/{deviceId}/content/{contentId}` | - | - | Unassign content from device |
| **GET** | `/api/devices/{id}/preview` | `{ params }` | Preview data | Get device preview/playlist |
| **GET** | `/api/speedtest/devices/{id}/speedtest` | `{ limit }` | `[{ speed, timestamp, ... }]` | Get speed test history |
| **GET** | `/api/speedtest/devices/{id}/speedtest/latest` | - | `{ speed, timestamp, ... }` | Get latest speed test result |

**Used By**:
- `src/pages/Dashboard.tsx` - Device list, approval mutations
- `src/pages/Devices.tsx` - Full device management page
- `src/components/devices/modals/DeviceDetailModal.tsx` - Device info and speed history
- `src/components/devices/modals/AssignContentModal.tsx` - Content assignment
- `src/components/devices/modals/DeviceLogsModal.tsx` - Device logs viewing

---

### 3. CONTENT API (`contentAPI`)

**Location**: `src/services/api.js` (lines 210-221)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/content` | - | `{ items: [], total }` | Fetch all content items |
| **POST** | `/api/content/upload` | FormData (multipart) | `{ id, file_path, ... }` | Upload content file |
| **GET** | `/api/content/{id}` | - | `{ id, title, ... }` | Get single content details |
| **PATCH** | `/api/content/{id}` | `{ title, description, ... }` | `{ id, ... }` | Update content metadata |
| **DELETE** | `/api/content/{id}` | - | - | Delete content |
| **POST** | `/api/content/{id}/assign` | `{ device_ids, tag_ids, ... }` | - | Assign content to devices/tags |
| **DELETE** | `/api/content/{id}/assign` | `{ device_ids, tag_ids }` in body | - | Unassign content from devices/tags |
| **GET** | `/api/content/{id}/assignments` | - | `[{ device_id, tag_id, priority, ... }]` | Get content assignments |

**Used By**:
- `src/pages/Dashboard.tsx` - Content list and assignments
- `src/pages/Contents.tsx` - Full content management page
- `src/components/content/modals/UploadModal.tsx` - File upload
- `src/components/content/modals/EditContentModal.tsx` - Content assignment
- `src/components/content/modals/BulkEditModal.tsx` - Bulk operations
- `src/components/devices/modals/AssignContentModal.tsx` - Device content assignment

---

### 4. TAGS API (`tagsAPI`)

**Location**: `src/services/api.js` (lines 224-241)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/tags` | `{ params }` | `{ items: [], total }` | Fetch all tags |
| **POST** | `/api/tags` | `{ tag_name, description, color }` | `{ id, ... }` | Create new tag |
| **GET** | `/api/tags/{id}` | - | `{ id, tag_name, ... }` | Get single tag |
| **PATCH** | `/api/tags/{id}` | `{ tag_name, description, color }` | `{ id, ... }` | Update tag |
| **DELETE** | `/api/tags/{id}` | - | - | Delete tag |
| **POST** | `/api/tags/assign` | `{ tag_id, device_ids, ... }` | - | Assign tag to devices |
| **DELETE** | `/api/tags/assign` | `{ tag_id, device_ids }` in body | - | Unassign tag from devices |
| **GET** | `/api/tags/{id}/devices` | - | `[{ id, device_name, ... }]` | Get devices with this tag |
| **GET** | `/api/tags/{id}/content` | `{ params }` | `[{ content_id, ... }]` | Get content assigned to tag |
| **POST** | `/api/tags/{id}/content` | `{ content_ids, ... }` | - | Assign content to tag |
| **DELETE** | `/api/tags/{id}/content/{contentId}` | - | - | Unassign content from tag |

**Used By**:
- `src/pages/Dashboard.tsx` - Top tags display
- `src/pages/Tags.tsx` - Full tag management page
- `src/components/tags/modals/TagFormModal.tsx` - Create/edit tags
- `src/components/tags/modals/TagDeviceManagementModal.tsx` - Device assignment
- `src/components/tags/modals/TagContentModal.tsx` - Content assignment
- `src/components/devices/modals/DeviceDetailModal.tsx` - View device tags

---

### 5. PLAYLISTS API (`playlistsAPI`)

**Location**: `src/services/api.js` (lines 244-260)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/playlists` | - | `{ items: [], total }` | Fetch all playlists |
| **POST** | `/api/playlists` | `{ name, description, is_active }` | `{ id, ... }` | Create playlist |
| **GET** | `/api/playlists/{id}` | - | `{ id, name, ... }` | Get playlist details |
| **PATCH** | `/api/playlists/{id}` | `{ name, description, is_active }` | `{ id, ... }` | Update playlist |
| **DELETE** | `/api/playlists/{id}` | - | - | Delete playlist |
| **GET** | `/api/playlists/{id}/content` | - | `[{ content_id, order, duration, ... }]` | Get playlist items |
| **POST** | `/api/playlists/{id}/content` | `{ content_ids, ... }` | - | Add content to playlist |
| **DELETE** | `/api/playlists/{id}/content/{contentId}` | - | - | Remove content from playlist |
| **PATCH** | `/api/playlists/{id}/reorder` | `{ items: [{ id, order }, ...] }` | - | Reorder playlist items |
| **GET** | `/api/playlists/{id}/assignments` | - | `{ devices: [], tags: [] }` | Get playlist assignments |
| **POST** | `/api/playlists/{id}/assign/devices` | `{ device_ids }` | - | Assign playlist to devices |
| **POST** | `/api/playlists/{id}/assign/tags` | `{ tag_ids }` | - | Assign playlist to tags |
| **DELETE** | `/api/playlists/{id}/assign/devices` | `{ device_ids }` in body | - | Unassign playlist from devices |
| **DELETE** | `/api/playlists/{id}/assign/tags` | `{ tag_ids }` in body | - | Unassign playlist from tags |

**Used By**:
- `src/pages/Dashboard.tsx` - Playlist stats
- `src/pages/Playlists.tsx` - Full playlist management page
- `src/components/playlists/modals/PlaylistFormModal.tsx` - Create/edit
- `src/components/playlists/modals/PlaylistContentModal.tsx` - Content management
- `src/components/playlists/modals/PlaylistAssignmentModal.tsx` - Device/tag assignment
- `src/components/playlists/modals/PlaylistPreviewModal.tsx` - Preview
- `src/components/playlists/modals/DuplicatePlaylistModal.tsx` - Duplication

---

### 6. WIDGETS API (`widgetsAPI`)

**Location**: `src/services/api.js` (lines 263-271)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/widgets` | `{ params: { type } }` | `{ items: [], total }` | Fetch widgets by type |
| **POST** | `/api/widgets` | `{ type, config, ... }` | `{ id, ... }` | Create widget |
| **GET** | `/api/widgets/{id}` | - | `{ id, type, config, ... }` | Get widget details |
| **PATCH** | `/api/widgets/{id}` | `{ type, config, ... }` | `{ id, ... }` | Update widget |
| **DELETE** | `/api/widgets/{id}` | - | - | Delete widget |
| **POST** | `/api/widgets/{id}/assign` | `{ device_ids, tag_ids, ... }` | - | Assign widget |
| **DELETE** | `/api/widgets/{id}/assign` | `{ device_ids, tag_ids }` | - | Unassign widget |

**Used By**:
- `src/pages/Widgets.tsx` - Widget management page
- Widget-specific tabs (Weather, Text, Calendar, etc.)

---

### 7. USERS API (`usersAPI`)

**Location**: `src/services/api.js` (lines 274-281)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/users` | - | `{ items: [], total }` | Fetch all users |
| **POST** | `/api/users` | `{ username, email, password, role, ... }` | `{ id, ... }` | Create user |
| **GET** | `/api/users/{id}` | - | `{ id, username, ... }` | Get user details |
| **PATCH** | `/api/users/{id}` | `{ username, email, role, ... }` | `{ id, ... }` | Update user |
| **DELETE** | `/api/users/{id}` | - | - | Delete user |
| **POST** | `/api/users/{id}/reset-password` | `{ new_password }` | - | Reset user password |

**Used By**:
- `src/components/settings/UsersTab.tsx` - User management in Settings

---

### 8. SETTINGS API (`settingsAPI`)

**Location**: `src/services/api.js` (lines 284-291)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/settings/system/info` | - | `{ version, database_uptime, ... }` | Get system information |
| **GET** | `/api/settings/system/backup` | `{ responseType: 'blob' }` | Blob data | Download database backup |
| **POST** | `/api/settings/system/clear-cache` | - | - | Clear system cache |

**Used By**:
- `src/components/settings/SystemTab.tsx` - System settings and maintenance

---

### 9. CLIENT API (`clientAPI`)

**Location**: `src/services/api.js` (lines 294-297)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/client/playlist` | `?device_id={id}` | `{ playlist: [...] }` | Get device's current playlist |
| **GET** | `/api/client/status` | `?device_id={id}` | Device status data | Get device status |

**Used By**:
- `src/components/devices/modals/AssignContentModal.tsx` - Get current playlist
- Device status monitoring

---

### 10. ACTIVITIES API (`activitiesAPI`)

**Location**: `src/services/api.js` (lines 300-306)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/activities` | `{ skip, limit, action_type, entity_type, user_id, start_date, end_date }` | `{ items: [], total }` | Fetch activity logs with filters |
| **GET** | `/api/activities/stats` | - | `{ today, this_week, this_month }` | Get activity statistics |
| **GET** | `/api/activities/{id}` | - | Activity log entry | Get single activity |
| **POST** | `/api/activities` | Activity data | `{ id, ... }` | Create activity log |
| **DELETE** | `/api/activities/cleanup` | `{ retention_days }` | - | Clean up old logs |

**Used By**:
- `src/pages/Activities.tsx` - Activity logs page
- `src/components/dashboard/ActivityTimeline.tsx` - Dashboard activity timeline

---

### 11. FIREBIRD API (`firebirdAPI`)

**Location**: `src/services/api.js` (lines 309-318)

| Method | Endpoint | Parameters | Returns | Usage |
|--------|----------|------------|---------|-------|
| **GET** | `/api/firebird/configs` | - | `{ items: [], total }` | List Firebird configs |
| **GET** | `/api/firebird/configs/{id}` | - | Config data | Get config details |
| **POST** | `/api/firebird/configs` | Config data | `{ id, ... }` | Create new config |
| **PUT** | `/api/firebird/configs/{id}` | Config data | `{ id, ... }` | Update config |
| **DELETE** | `/api/firebird/configs/{id}` | - | - | Delete config |
| **POST** | `/api/firebird/configs/{id}/test` | - | Test result | Test connection |
| **GET** | `/api/firebird/configs/{id}/health` | - | Health data | Get health status |
| **POST** | `/api/firebird/configs/{id}/query` | `{ query }` | Query result | Execute custom query |

**Used By**:
- `src/components/widgets/SystemPMSTab.tsx` - System PMS integration
- `src/components/widgets/modals/FirebirdConfigModal.tsx` - Config management
- `src/components/widgets/FirebirdConnectionStatus.tsx` - Connection status

---

## Page-by-Page API Usage Summary

### Dashboard (`src/pages/Dashboard.tsx`)
- **GET** `/api/devices` - List all devices
- **GET** `/api/content` - List all content
- **GET** `/api/tags` - List all tags
- **GET** `/api/playlists` - List all playlists
- **GET** `/api/content/{id}/assignments` - Content assignments
- **PUT** `/api/devices/{id}` - Approve/reject devices
- **DELETE** `/api/devices/{id}` - Reject devices

### Devices (`src/pages/Devices.tsx`)
- **GET** `/api/devices` - List devices (refreshes every 5s)
- **POST** `/api/devices/tv` - Register TV
- **PUT** `/api/devices/{id}` - Update device
- **DELETE** `/api/devices/{id}` - Delete device

### Contents (`src/pages/Contents.tsx`)
- **GET** `/api/content` - List content
- **GET** `/api/tags` - List tags
- **GET** `/api/devices` - List devices
- **GET** `/api/content/{id}/assignments` - Content assignments
- **POST** `/api/content/upload` - Upload content
- **POST** `/api/content/{id}/assign` - Assign content
- **DELETE** `/api/content/{id}` - Delete content

### Tags (`src/pages/Tags.tsx`)
- **GET** `/api/tags` - List tags (refreshes on sort change)
- **POST** `/api/tags` - Create tag
- **PATCH** `/api/tags/{id}` - Update tag
- **DELETE** `/api/tags/{id}` - Delete tag

### Playlists (`src/pages/Playlists.tsx`)
- **GET** `/api/playlists` - List playlists
- **POST** `/api/playlists` - Create playlist
- **PATCH** `/api/playlists/{id}` - Update playlist
- **DELETE** `/api/playlists/{id}` - Delete playlist

### Activities (`src/pages/Activities.tsx`)
- **GET** `/api/activities` - List activities (with pagination and filters)
- **GET** `/api/activities/stats` - Activity statistics (refreshes every 60s)

### Settings (`src/pages/Settings.tsx`)
- **System Tab**: `/api/settings/system/info`, `/api/settings/system/backup`, `/api/settings/system/clear-cache`
- **Users Tab**: `/api/users`, `/api/users/{id}`, `/api/users` (POST/PATCH/DELETE)

---

## Common Query Key Patterns

The application uses React Query with these queryKey patterns:

| Query Key | Endpoint(s) | Refresh Rate |
|-----------|----------|--------------|
| `['devices']` | `/api/devices` | Manual invalidation |
| `['content']` | `/api/content` | Manual invalidation |
| `['tags']` | `/api/tags` | Manual invalidation |
| `['playlists']` | `/api/playlists` | Manual invalidation |
| `['activities', 'list', ...]` | `/api/activities` | 60 seconds |
| `['activities', 'stats']` | `/api/activities/stats` | 60 seconds |
| `['system', 'info']` | `/api/settings/system/info` | 30 seconds |
| `['users']` | `/api/users` | Manual invalidation |

---

## Error Handling

All API calls use consistent error handling:

1. **Standardized Error Format** (from backend):
   ```json
   {
     "success": false,
     "error": {
       "code": "ERROR_CODE",
       "message": "Error description",
       "field": "field_name",
       "details": {...}
     },
     "meta": {...}
   }
   ```

2. **Client Error Access**:
   - Access via `error.response?.data?.detail` for error messages
   - 401 responses automatically clear token and redirect to login
   - Validation errors include field information

3. **Toast Notifications**:
   - Success: `showToast.success(message)`
   - Error: `showToast.error(message)`
   - Used in all mutations for user feedback

---

## Request Patterns

### Query Parameters
- Pagination: `{ skip: number, limit: number }`
- Sorting: `{ sort_by: 'newest' | 'oldest' | 'name_asc' | 'name_desc' }`
- Filtering: Various filter-specific params (action_type, entity_type, etc.)

### Request Body
- Content-Type: `application/json` (default)
- File uploads: `multipart/form-data` (Content API)
- DELETE with body: Uses `{ data: {...} }` pattern

### Response Handling
- Automatic Bearer token injection
- Standardized response unwrapping
- Automatic 401 handling with logout redirect

---

## Notes for Development

1. **Environment Setup**: Must set `VITE_API_URL` in `.env` before running
2. **Token Management**: Token stored in `localStorage` and automatically injected
3. **CORS**: API must include port 8080 (viewer) and 3000 (web-admin) in CORS config
4. **Response Format**: All endpoints should follow standardized response format for proper unwrapping
5. **Query Invalidation**: Used to trigger refetches after mutations
6. **WebSocket Integration**: Dashboard supports WebSocket for real-time updates (fallback to polling)

