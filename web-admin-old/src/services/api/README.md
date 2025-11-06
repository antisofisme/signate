# API Services - Modular Architecture

This directory contains the modularized API service layer for the Web Admin application.

## Structure

```
api/
├── index.js        - Core axios client with interceptors
├── auth.js         - Authentication endpoints
├── devices.js      - Device management & monitoring
├── content.js      - Media content management
├── tags.js         - Device tagging & tag-based content
├── playlists.js    - Playlist management & scheduling
├── widgets.js      - Widget management & overlays
├── users.js        - User management
├── settings.js     - System settings & maintenance
├── client.js       - Client-side testing endpoints
├── activities.js   - Activity logging & audit trails
├── firebird.js     - SystemPMS integration
├── main.js         - Unified exports for backward compatibility
└── README.md       - This file
```

## Usage

### New Modular Approach (Recommended)

Import only the API modules you need:

```javascript
// Import specific API modules
import authAPI from './services/api/auth.js'
import devicesAPI from './services/api/devices.js'
import contentAPI from './services/api/content.js'

// Use in components
const LoginPage = () => {
  const handleLogin = async (credentials) => {
    const response = await authAPI.login(credentials)
    // ...
  }
}

const DevicesPage = () => {
  const { data: devices } = useQuery('devices', () => devicesAPI.list())
  // ...
}
```

### Backward Compatible Approach

Import multiple modules from main.js:

```javascript
// Import from main.js for convenience
import { authAPI, devicesAPI, contentAPI } from './services/api/main.js'

// Usage remains the same
await authAPI.login(credentials)
await devicesAPI.list()
```

### Direct Axios Client

For custom API calls not covered by the modules:

```javascript
import api from './services/api/index.js'

// Make custom API calls
const response = await api.get('/api/custom/endpoint')
const data = await api.post('/api/custom/action', { payload })
```

## API Modules Reference

### authAPI (auth.js)
Authentication and authorization endpoints.

**Methods:**
- `login(credentials)` - Authenticate user
- `logout()` - End user session
- `me()` - Get current user info

**Example:**
```javascript
import authAPI from './services/api/auth.js'

await authAPI.login({ username: 'admin', password: 'secret' })
const user = await authAPI.me()
```

### devicesAPI (devices.js)
Device management, registration, content assignment, and monitoring.

**Methods:**
- `list(params)` - List all devices with filters
- `registerTV(data)` - Register new WebOS TV
- `generateMonitorCode(data)` - Generate activation code for monitor
- `activateMonitor(data)` - Activate monitor with code
- `update(id, data)` - Update device settings
- `delete(id)` - Delete device
- `release(id)` - Release device for re-registration
- `replaceWithPending(deviceId, pendingDeviceId)` - Replace device
- `heartbeat(id)` - Send device heartbeat
- `getLogs(id, params)` - Get device logs
- `deleteLogs(id, params)` - Delete device logs
- `queueCommand(id, data)` - Queue command for device
- `getContent(id, params)` - Get assigned content
- `assignContent(deviceId, contentId, priority)` - Assign content to device
- `unassignContent(deviceId, contentId)` - Unassign content
- `preview(id, params)` - Preview device display
- `getSpeedTests(id, limit)` - Get speed test history
- `getLatestSpeedTest(id)` - Get latest speed test result

**Example:**
```javascript
import devicesAPI from './services/api/devices.js'

const devices = await devicesAPI.list({ status: 'online' })
await devicesAPI.assignContent(deviceId, contentId, 1)
const speedTests = await devicesAPI.getSpeedTests(deviceId, 20)
```

### contentAPI (content.js)
Media content management, upload, and assignment.

**Methods:**
- `list()` - List all content
- `upload(formData)` - Upload new content
- `get(id)` - Get content details
- `update(id, data)` - Update content metadata
- `delete(id)` - Delete content
- `assign(id, data)` - Assign content to devices/tags
- `unassign(id, data)` - Unassign content
- `getAssignments(id)` - Get content assignments

**Example:**
```javascript
import contentAPI from './services/api/content.js'

const formData = new FormData()
formData.append('file', file)
await contentAPI.upload(formData)

const content = await contentAPI.list()
```

### tagsAPI (tags.js)
Device tagging and tag-based content assignment.

**Methods:**
- `list(params)` - List all tags
- `create(data)` - Create new tag
- `get(id)` - Get tag details
- `update(id, data)` - Update tag
- `delete(id)` - Delete tag
- `assign(data)` - Assign tag to devices
- `unassign(data)` - Unassign tag from devices
- `getDevices(id)` - Get devices with tag
- `getContent(id, params)` - Get tag-assigned content
- `assignContent(id, data)` - Assign content to tag
- `unassignContent(id, contentId)` - Unassign content from tag

**Example:**
```javascript
import tagsAPI from './services/api/tags.js'

await tagsAPI.create({ name: 'Lobby Displays', color: '#3B82F6' })
await tagsAPI.assign({ tag_id: 1, device_ids: [1, 2, 3] })
```

### playlistsAPI (playlists.js)
Playlist management, content scheduling, and device/tag assignment.

**Methods:**
- `list()` - List all playlists
- `create(data)` - Create new playlist
- `get(id)` - Get playlist details
- `update(id, data)` - Update playlist
- `delete(id)` - Delete playlist
- `getContent(id)` - Get playlist content
- `assignContent(id, data)` - Add content to playlist
- `removeContent(id, contentId)` - Remove content from playlist
- `reorderContent(id, data)` - Reorder playlist items
- `getAssignments(id)` - Get playlist assignments
- `assignToDevices(id, data)` - Assign playlist to devices
- `assignToTags(id, data)` - Assign playlist to tags
- `unassignFromDevices(id, data)` - Unassign from devices
- `unassignFromTags(id, data)` - Unassign from tags

**Example:**
```javascript
import playlistsAPI from './services/api/playlists.js'

const playlist = await playlistsAPI.create({ name: 'Morning Loop' })
await playlistsAPI.assignContent(playlist.id, { content_id: 1, duration: 30 })
await playlistsAPI.assignToDevices(playlist.id, { device_ids: [1, 2, 3] })
```

### widgetsAPI (widgets.js)
Widget management and assignment for overlays and dynamic content.

**Methods:**
- `list(type)` - List widgets by type
- `create(data)` - Create new widget
- `get(id)` - Get widget details
- `update(id, data)` - Update widget
- `delete(id)` - Delete widget
- `assign(id, data)` - Assign widget to devices/tags
- `unassign(id, data)` - Unassign widget

**Example:**
```javascript
import widgetsAPI from './services/api/widgets.js'

const widgets = await widgetsAPI.list('clock')
await widgetsAPI.create({ type: 'weather', config: { city: 'Jakarta' } })
```

### usersAPI (users.js)
User management and authentication.

**Methods:**
- `list()` - List all users
- `create(data)` - Create new user
- `get(id)` - Get user details
- `update(id, data)` - Update user
- `delete(id)` - Delete user
- `resetPassword(id, data)` - Reset user password

**Example:**
```javascript
import usersAPI from './services/api/users.js'

await usersAPI.create({ username: 'john', email: 'john@example.com', role: 'admin' })
await usersAPI.resetPassword(userId, { new_password: 'newpass' })
```

### settingsAPI (settings.js)
System settings, configuration, and maintenance.

**Methods:**
- `getSystemInfo()` - Get system information
- `backupDatabase()` - Download database backup
- `clearCache()` - Clear system cache

**Example:**
```javascript
import settingsAPI from './services/api/settings.js'

const systemInfo = await settingsAPI.getSystemInfo()
const backup = await settingsAPI.backupDatabase() // Returns blob
```

### clientAPI (client.js)
Client-side testing and monitoring endpoints.

**Methods:**
- `getPlaylist(deviceId)` - Get playlist for device
- `getStatus(deviceId)` - Get device status

**Example:**
```javascript
import clientAPI from './services/api/client.js'

const playlist = await clientAPI.getPlaylist(deviceId)
const status = await clientAPI.getStatus(deviceId)
```

### activitiesAPI (activities.js)
Activity logging, audit trails, and system event tracking.

**Methods:**
- `list(params)` - List activities with filters
- `stats()` - Get activity statistics
- `get(id)` - Get activity details
- `create(data)` - Log new activity
- `cleanup(retentionDays)` - Clean up old activity logs

**Example:**
```javascript
import activitiesAPI from './services/api/activities.js'

const activities = await activitiesAPI.list({
  type: 'device_registered',
  limit: 50
})
const stats = await activitiesAPI.stats()
```

### firebirdAPI (firebird.js)
SystemPMS integration and Firebird database connections.

**Methods:**
- `listConfigs()` - List all Firebird configurations
- `getConfig(id)` - Get configuration details
- `createConfig(data)` - Create new configuration
- `updateConfig(id, data)` - Update configuration
- `deleteConfig(id)` - Delete configuration
- `testConnection(id)` - Test database connection
- `getHealth(id)` - Get connection health status
- `executeQuery(id, query)` - Execute custom SQL query

**Example:**
```javascript
import firebirdAPI from './services/api/firebird.js'

await firebirdAPI.createConfig({
  host: '192.168.1.100',
  database: 'systempms.fdb',
  username: 'SYSDBA',
  password: 'masterkey'
})

const health = await firebirdAPI.getHealth(configId)
```

## Features

### Automatic Response Unwrapping
All API responses are automatically unwrapped from the standardized format:

```javascript
// Backend returns:
{
  success: true,
  data: { devices: [...] },
  meta: { timestamp, request_id }
}

// You receive (automatically unwrapped):
{ devices: [...] }
```

### Error Handling
Errors are automatically transformed to a consistent format:

```javascript
try {
  await devicesAPI.update(id, data)
} catch (error) {
  console.error(error.response.data.detail) // Error message
  console.error(error.response.data.code)   // Error code
  console.error(error.response.data.field)  // Field that caused error
}
```

### Authentication
JWT tokens are automatically added to all requests via interceptors:

```javascript
// Token is automatically read from localStorage
// and added to Authorization header
```

### Debug Mode
Enable debug logging by setting environment variable:

```env
VITE_DEBUG_API=true
```

This will log all requests, responses, and errors to the console.

## Migration Guide

To migrate from the old `api.js` to the new modular structure:

### Before:
```javascript
import { devicesAPI, contentAPI, authAPI } from './services/api.js'
```

### After (Option 1 - Recommended):
```javascript
import devicesAPI from './services/api/devices.js'
import contentAPI from './services/api/content.js'
import authAPI from './services/api/auth.js'
```

### After (Option 2 - Minimal changes):
```javascript
import { devicesAPI, contentAPI, authAPI } from './services/api/main.js'
```

## Benefits of Modular Structure

1. **Code Organization**: Related API methods are grouped together
2. **Tree Shaking**: Import only what you need, reduce bundle size
3. **Maintainability**: Easier to find and update specific API methods
4. **Type Safety**: Better IDE autocomplete and type inference
5. **Testing**: Test individual modules in isolation
6. **Documentation**: Each module has clear, focused documentation
7. **Performance**: Smaller initial bundle, faster load times

## Best Practices

1. **Import only what you need** - Use individual module imports instead of main.js
2. **Use TypeScript** - Add type definitions for better type safety
3. **Handle errors consistently** - Use try/catch with proper error messages
4. **Cache responses** - Use React Query or SWR for data caching
5. **Document usage** - Add JSDoc comments when extending modules

## Testing

Test individual modules:

```javascript
import devicesAPI from './services/api/devices.js'
import { vi } from 'vitest'

// Mock axios
vi.mock('./services/api/index.js', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  }
}))

// Test API methods
describe('devicesAPI', () => {
  it('should list devices', async () => {
    const devices = await devicesAPI.list()
    expect(devices).toBeDefined()
  })
})
```

## Troubleshooting

### Import errors
If you get import errors, ensure you're using the correct path:
- ✅ `'./services/api/devices.js'`
- ❌ `'./services/api/devices'` (missing .js extension)

### CORS errors
Check that `VITE_API_URL` is correctly set in your `.env` file:
```env
VITE_API_URL=http://192.168.5.12:8001
```

### 401 Unauthorized
User will be automatically redirected to `/login` when token expires.

## Contributing

When adding new API endpoints:

1. Add method to appropriate module (e.g., `devices.js`)
2. Add JSDoc comment describing the method
3. Update this README with the new method
4. Test the new endpoint
5. Update TypeScript types if applicable

Example:
```javascript
/**
 * Get device thumbnail
 * @param {number} id - Device ID
 * @returns {Promise<Blob>} - Thumbnail image
 */
getThumbnail: (id) => api.get(`/api/devices/${id}/thumbnail`, {
  responseType: 'blob'
}),
```
