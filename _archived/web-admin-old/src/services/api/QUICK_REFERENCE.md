# API Modules - Quick Reference Card

## Import Patterns

### Authentication (auth.js)
```javascript
import authAPI from './services/api/auth.js'

await authAPI.login({ username, password })
await authAPI.logout()
const user = await authAPI.me()
```

### Devices (devices.js)
```javascript
import devicesAPI from './services/api/devices.js'

// Device Management
const devices = await devicesAPI.list({ status: 'online' })
await devicesAPI.update(id, { name: 'New Name' })
await devicesAPI.delete(id)

// Registration
const code = await devicesAPI.generateMonitorCode({ name: 'Monitor 1' })
await devicesAPI.activateMonitor({ code: '123456' })

// Content Assignment
await devicesAPI.assignContent(deviceId, contentId, priority)
await devicesAPI.unassignContent(deviceId, contentId)

// Monitoring
await devicesAPI.heartbeat(id)
const logs = await devicesAPI.getLogs(id, { limit: 100 })
const speedTests = await devicesAPI.getSpeedTests(id, 20)
```

### Content (content.js)
```javascript
import contentAPI from './services/api/content.js'

// Upload
const formData = new FormData()
formData.append('file', file)
await contentAPI.upload(formData)

// Management
const content = await contentAPI.list()
await contentAPI.update(id, { title: 'New Title' })
await contentAPI.delete(id)

// Assignment
await contentAPI.assign(id, { device_ids: [1, 2, 3] })
const assignments = await contentAPI.getAssignments(id)
```

### Tags (tags.js)
```javascript
import tagsAPI from './services/api/tags.js'

// Tag Management
const tags = await tagsAPI.list()
await tagsAPI.create({ name: 'Lobby', color: '#3B82F6' })
await tagsAPI.update(id, { name: 'Updated Name' })

// Device Tagging
await tagsAPI.assign({ tag_id: 1, device_ids: [1, 2, 3] })
const devices = await tagsAPI.getDevices(tagId)

// Content Assignment
await tagsAPI.assignContent(tagId, { content_id: 1, priority: 0 })
const content = await tagsAPI.getContent(tagId)
```

### Playlists (playlists.js)
```javascript
import playlistsAPI from './services/api/playlists.js'

// Playlist Management
const playlists = await playlistsAPI.list()
await playlistsAPI.create({ name: 'Morning Loop', duration: 300 })
await playlistsAPI.update(id, { name: 'Updated Name' })

// Content Management
await playlistsAPI.assignContent(id, { content_id: 1, duration: 30 })
await playlistsAPI.removeContent(id, contentId)
await playlistsAPI.reorderContent(id, { order: [3, 1, 2] })

// Device/Tag Assignment
await playlistsAPI.assignToDevices(id, { device_ids: [1, 2, 3] })
await playlistsAPI.assignToTags(id, { tag_ids: [1, 2] })
const assignments = await playlistsAPI.getAssignments(id)
```

### Widgets (widgets.js)
```javascript
import widgetsAPI from './services/api/widgets.js'

const widgets = await widgetsAPI.list('clock')
await widgetsAPI.create({ type: 'weather', config: { city: 'Jakarta' } })
await widgetsAPI.assign(id, { device_ids: [1, 2] })
```

### Users (users.js)
```javascript
import usersAPI from './services/api/users.js'

const users = await usersAPI.list()
await usersAPI.create({ username: 'john', role: 'admin' })
await usersAPI.update(id, { email: 'new@email.com' })
await usersAPI.resetPassword(id, { new_password: 'secret' })
```

### Settings (settings.js)
```javascript
import settingsAPI from './services/api/settings.js'

const info = await settingsAPI.getSystemInfo()
const backup = await settingsAPI.backupDatabase() // Returns blob
await settingsAPI.clearCache()
```

### Activities (activities.js)
```javascript
import activitiesAPI from './services/api/activities.js'

const activities = await activitiesAPI.list({
  type: 'device_registered',
  limit: 50,
  offset: 0
})
const stats = await activitiesAPI.stats()
await activitiesAPI.cleanup(90) // Keep last 90 days
```

### Firebird (firebird.js)
```javascript
import firebirdAPI from './services/api/firebird.js'

// Configuration
const configs = await firebirdAPI.listConfigs()
await firebirdAPI.createConfig({
  host: '192.168.1.100',
  database: 'systempms.fdb'
})

// Connection
await firebirdAPI.testConnection(id)
const health = await firebirdAPI.getHealth(id)

// Query
const result = await firebirdAPI.executeQuery(id, 'SELECT * FROM guests')
```

### Client Testing (client.js)
```javascript
import clientAPI from './services/api/client.js'

const playlist = await clientAPI.getPlaylist(deviceId)
const status = await clientAPI.getStatus(deviceId)
```

## Multiple Imports

```javascript
// Import multiple modules
import authAPI from './services/api/auth.js'
import devicesAPI from './services/api/devices.js'
import contentAPI from './services/api/content.js'

// Or use main.js for convenience
import { authAPI, devicesAPI, contentAPI } from './services/api/main.js'

// Direct axios client for custom calls
import api from './services/api/index.js'
const response = await api.get('/api/custom/endpoint')
```

## Error Handling

```javascript
import devicesAPI from './services/api/devices.js'

try {
  await devicesAPI.update(id, data)
} catch (error) {
  console.error(error.response.data.detail)  // Error message
  console.error(error.response.data.code)    // Error code
  console.error(error.response.data.field)   // Field that caused error
}
```

## React Hook Examples

### With React Query
```javascript
import { useQuery, useMutation } from '@tanstack/react-query'
import devicesAPI from './services/api/devices.js'

// Fetch devices
const { data: devices, isLoading } = useQuery({
  queryKey: ['devices'],
  queryFn: () => devicesAPI.list()
})

// Mutate device
const updateMutation = useMutation({
  mutationFn: ({ id, data }) => devicesAPI.update(id, data),
  onSuccess: () => queryClient.invalidateQueries(['devices'])
})
```

### With useState/useEffect
```javascript
import { useState, useEffect } from 'react'
import devicesAPI from './services/api/devices.js'

const [devices, setDevices] = useState([])
const [loading, setLoading] = useState(true)

useEffect(() => {
  devicesAPI.list()
    .then(response => setDevices(response.devices))
    .catch(error => console.error(error))
    .finally(() => setLoading(false))
}, [])
```

## Common Patterns

### Pagination
```javascript
const devices = await devicesAPI.list({
  limit: 20,
  offset: 0,
  status: 'online'
})
```

### File Upload with Progress
```javascript
const formData = new FormData()
formData.append('file', file)

const config = {
  onUploadProgress: (progressEvent) => {
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    )
    setProgress(percentCompleted)
  }
}

await contentAPI.upload(formData, config)
```

### Batch Operations
```javascript
// Assign content to multiple devices
const deviceIds = [1, 2, 3, 4, 5]
await Promise.all(
  deviceIds.map(deviceId =>
    devicesAPI.assignContent(deviceId, contentId, 0)
  )
)

// Or use tag assignment for efficiency
await tagsAPI.assignContent(tagId, {
  content_id: contentId,
  priority: 0
})
```

### Polling for Updates
```javascript
import { useEffect } from 'react'
import devicesAPI from './services/api/devices.js'

useEffect(() => {
  const interval = setInterval(async () => {
    const devices = await devicesAPI.list()
    updateDeviceStatus(devices)
  }, 30000) // Every 30 seconds

  return () => clearInterval(interval)
}, [])
```

## Debug Mode

Enable detailed API logging:

```bash
# .env
VITE_DEBUG_API=true
```

This logs:
- All requests (method, URL, params)
- All responses (status, data, meta)
- All errors (code, message, details)
- Response unwrapping steps

## TypeScript Support (Future)

```typescript
// Type definitions will be added in the future
import type { Device, Content, Tag } from './services/api/types'
import devicesAPI from './services/api/devices.js'

const devices: Device[] = await devicesAPI.list()
const device: Device = await devicesAPI.update(id, data)
```

---

**Quick Tip**: Bookmark this page for fast reference during development!
