# Web-Admin Frontend - API Calls Quick Reference

## API Endpoint Summary

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout  
- `GET /api/auth/me` - Get current user

### Devices
- `GET /api/devices` - List all devices
- `POST /api/devices/tv` - Register TV device
- `POST /api/devices/monitor` - Generate monitor code
- `POST /api/devices/monitor/activate` - Activate monitor
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device
- `POST /api/devices/{id}/release` - Release device
- `POST /api/devices/{id}/replace-with-pending/{pendingId}` - Replace device
- `POST /api/devices/{id}/heartbeat` - Send heartbeat
- `GET /api/devices/{id}/logs` - Get device logs
- `DELETE /api/devices/{id}/logs` - Delete logs
- `POST /api/devices/{id}/commands` - Queue command
- `GET /api/devices/{id}/content` - Get device content
- `POST /api/content/{contentId}/assign` - Assign content to device
- `DELETE /api/devices/{deviceId}/content/{contentId}` - Unassign content
- `GET /api/devices/{id}/preview` - Get device preview
- `GET /api/speedtest/devices/{id}/speedtest` - Speed test history
- `GET /api/speedtest/devices/{id}/speedtest/latest` - Latest speed test

### Content
- `GET /api/content` - List content
- `POST /api/content/upload` - Upload content (multipart/form-data)
- `GET /api/content/{id}` - Get content details
- `PATCH /api/content/{id}` - Update content
- `DELETE /api/content/{id}` - Delete content
- `POST /api/content/{id}/assign` - Assign content
- `DELETE /api/content/{id}/assign` - Unassign content
- `GET /api/content/{id}/assignments` - Get content assignments

### Tags
- `GET /api/tags` - List tags
- `POST /api/tags` - Create tag
- `GET /api/tags/{id}` - Get tag details
- `PATCH /api/tags/{id}` - Update tag
- `DELETE /api/tags/{id}` - Delete tag
- `POST /api/tags/assign` - Assign tag to devices
- `DELETE /api/tags/assign` - Unassign tag from devices
- `GET /api/tags/{id}/devices` - Get tagged devices
- `GET /api/tags/{id}/content` - Get tag content
- `POST /api/tags/{id}/content` - Assign content to tag
- `DELETE /api/tags/{id}/content/{contentId}` - Unassign content from tag

### Playlists
- `GET /api/playlists` - List playlists
- `POST /api/playlists` - Create playlist
- `GET /api/playlists/{id}` - Get playlist details
- `PATCH /api/playlists/{id}` - Update playlist
- `DELETE /api/playlists/{id}` - Delete playlist
- `GET /api/playlists/{id}/content` - Get playlist items
- `POST /api/playlists/{id}/content` - Add content to playlist
- `DELETE /api/playlists/{id}/content/{contentId}` - Remove content from playlist
- `PATCH /api/playlists/{id}/reorder` - Reorder playlist items
- `GET /api/playlists/{id}/assignments` - Get playlist assignments
- `POST /api/playlists/{id}/assign/devices` - Assign playlist to devices
- `POST /api/playlists/{id}/assign/tags` - Assign playlist to tags
- `DELETE /api/playlists/{id}/assign/devices` - Unassign playlist from devices
- `DELETE /api/playlists/{id}/assign/tags` - Unassign playlist from tags

### Widgets
- `GET /api/widgets` - List widgets
- `POST /api/widgets` - Create widget
- `GET /api/widgets/{id}` - Get widget details
- `PATCH /api/widgets/{id}` - Update widget
- `DELETE /api/widgets/{id}` - Delete widget
- `POST /api/widgets/{id}/assign` - Assign widget
- `DELETE /api/widgets/{id}/assign` - Unassign widget

### Users
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user details
- `PATCH /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user
- `POST /api/users/{id}/reset-password` - Reset password

### Settings
- `GET /api/settings/system/info` - System information
- `GET /api/settings/system/backup` - Download database backup
- `POST /api/settings/system/clear-cache` - Clear cache

### Activities
- `GET /api/activities` - List activity logs
- `GET /api/activities/stats` - Activity statistics
- `GET /api/activities/{id}` - Get activity details
- `POST /api/activities` - Create activity log
- `DELETE /api/activities/cleanup` - Cleanup old logs

### Client
- `GET /api/client/playlist` - Get device playlist
- `GET /api/client/status` - Get device status

### Firebird
- `GET /api/firebird/configs` - List configs
- `GET /api/firebird/configs/{id}` - Get config
- `POST /api/firebird/configs` - Create config
- `PUT /api/firebird/configs/{id}` - Update config
- `DELETE /api/firebird/configs/{id}` - Delete config
- `POST /api/firebird/configs/{id}/test` - Test connection
- `GET /api/firebird/configs/{id}/health` - Health status
- `POST /api/firebird/configs/{id}/query` - Execute query

---

## Total Endpoints by Module

| Module | Count | Description |
|--------|-------|-------------|
| Auth | 3 | User authentication |
| Devices | 18 | Device management & monitoring |
| Content | 8 | Content upload & management |
| Tags | 11 | Device grouping |
| Playlists | 14 | Content scheduling |
| Widgets | 7 | Widget management |
| Users | 6 | User management |
| Settings | 3 | System settings |
| Activities | 5 | Activity logging |
| Client | 2 | Device client integration |
| Firebird | 8 | SystemPMS integration |
| **TOTAL** | **85** | Complete API surface |

---

## Most Frequently Used Endpoints

1. `GET /api/devices` - Dashboard, Devices page (10s refresh)
2. `GET /api/content` - Dashboard, Contents page
3. `GET /api/tags` - Dashboard, Tags page
4. `GET /api/playlists` - Dashboard, Playlists page
5. `PUT /api/devices/{id}` - Device approval/update
6. `GET /api/activities` - Activities page (60s refresh)
7. `POST /api/content/upload` - File upload
8. `GET /api/content/{id}/assignments` - Content assignment display
9. `GET /api/users` - Settings/Users tab
10. `GET /api/settings/system/info` - Settings/System tab (30s refresh)

---

## API Client Classes

All APIs are exported from `src/services/api.js`:

```javascript
export { authAPI, devicesAPI, contentAPI, tagsAPI, playlistsAPI }
export { widgetsAPI, usersAPI, settingsAPI, clientAPI, activitiesAPI }
export { firebirdAPI }
```

---

## Usage Example

```javascript
// Fetch devices
import { devicesAPI } from '../services/api'

const { data } = await devicesAPI.list()
// data = { devices: [...], total: 10 }

// Create device
const newDevice = await devicesAPI.registerTV({
  device_name: 'Living Room TV',
  platform: 'webOS'
})

// Assign content
await contentAPI.assign(contentId, {
  device_id: deviceId,
  priority: 0
})
```

---

## Important Notes

1. **Authentication Required**: All endpoints except `/api/auth/login` require Bearer token
2. **Automatic Unwrapping**: Response interceptor unwraps `{ success, data, meta }` to just `data`
3. **Error Handling**: 401 errors clear token and redirect to `/login`
4. **Query Invalidation**: Mutations invalidate related query keys to trigger refetches
5. **Refresh Rates**:
   - Devices: Manual (10s with refetchInterval)
   - Activities: 60 seconds
   - System Info: 30 seconds
   - Others: Manual invalidation after mutations

---

## Environment Configuration

```bash
# .env file
VITE_API_URL=http://192.168.5.12:8001
VITE_DEBUG_API=false  # Set to 'true' for debug logging
```

---

*Last Updated: 2025-10-28*
*Documentation covers all 11 API modules with 85+ total endpoints*
