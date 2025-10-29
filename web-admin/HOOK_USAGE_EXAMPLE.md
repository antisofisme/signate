# Custom Hooks Usage Guide

## useDashboardStats Hook

Custom hook untuk mengekstrak business logic dari Dashboard component.

### Location
`/mnt/g/khoirul/signate/web-admin/src/hooks/useDashboardStats.js`

### Purpose
Memisahkan business logic (stats calculation) dari presentation logic (UI rendering) di Dashboard component.

### Benefits
- ✅ Separation of Concerns
- ✅ Reusability - dapat digunakan di komponen lain
- ✅ Testability - mudah di-unit test
- ✅ Maintainability - logic terpusat di satu tempat
- ✅ Performance - menggunakan useMemo untuk optimasi

### Usage Example

**Before (Dashboard.jsx - Inline Logic):**
```javascript
export default function Dashboard() {
  const { data: devices } = useQuery({ ... })
  const { data: content } = useQuery({ ... })

  // 78 lines of business logic here...
  const isDeviceOnline = (lastSeen) => { ... }
  const devicesList = useMemo(() => ..., [])
  const pendingDevices = useMemo(() => ..., [])
  const stats = useMemo(() => {
    // Complex calculation...
  }, [...])

  return <div>...</div>
}
```

**After (Dashboard.jsx - Using Hook):**
```javascript
import { useDashboardStats } from '../hooks/useDashboardStats'

export default function Dashboard() {
  const { data: devices } = useQuery({ ... })
  const { data: content } = useQuery({ ... })
  const { data: tags } = useQuery({ ... })
  const { data: playlists } = useQuery({ ... })
  const { data: allAssignments } = useQuery({ ... })

  // Extract all business logic to custom hook
  const {
    isDeviceOnline,
    devicesList,
    pendingDevices,
    topTags,
    deviceStats,
    stats
  } = useDashboardStats({
    devices,
    content,
    tags,
    playlists,
    allAssignments
  })

  return <div>...</div>
}
```

### Hook API

**Parameters:**
```typescript
{
  devices: Object,        // Devices data from API
  content: Object,        // Content data from API
  tags: Object,           // Tags data from API
  playlists: Object,      // Playlists data from API
  allAssignments: Object  // Content assignments data
}
```

**Returns:**
```typescript
{
  // Helper functions
  isDeviceOnline: (lastSeen: string) => boolean,

  // Computed lists
  devicesList: Array,      // Memoized devices array
  pendingDevices: Array,   // Filtered pending devices
  topTags: Array,          // Top 5 tags by device count

  // Stats objects
  deviceStats: {
    tvDevices: number,
    monitorDevices: number,
    activeDevices: number,
    pendingDevices: number,
    onlineDevices: number
  },
  stats: Array<{           // 8 stat cards for dashboard
    name: string,
    value: number,
    subtitle: string,
    color: string
  }>
}
```

### Migration Steps

To migrate Dashboard.jsx to use this hook:

1. Import the hook:
   ```javascript
   import { useDashboardStats } from '../hooks/useDashboardStats'
   ```

2. Replace inline logic with hook call:
   ```javascript
   const dashboardData = useDashboardStats({
     devices,
     content,
     tags,
     playlists,
     allAssignments
   })
   ```

3. Remove old inline logic:
   - Delete `isDeviceOnline` function (lines 85-97)
   - Delete `devicesList` useMemo (line 100)
   - Delete `pendingDevices` useMemo (lines 103-106)
   - Delete `topTags` useMemo (lines 109-113)
   - Delete `deviceStats` useMemo (lines 116-124)
   - Delete `stats` useMemo (lines 126-203)

4. Use destructured values from hook:
   ```javascript
   const {
     isDeviceOnline,
     devicesList,
     pendingDevices,
     topTags,
     deviceStats,
     stats
   } = dashboardData
   ```

### Testing

The hook can be tested independently:

```javascript
import { renderHook } from '@testing-library/react'
import { useDashboardStats } from './useDashboardStats'

describe('useDashboardStats', () => {
  it('should calculate device stats correctly', () => {
    const mockData = {
      devices: { total: 10, devices: [...] },
      content: { total: 5, items: [...] },
      // ... other mock data
    }

    const { result } = renderHook(() => useDashboardStats(mockData))

    expect(result.current.stats).toHaveLength(8)
    expect(result.current.deviceStats.tvDevices).toBe(expected)
  })
})
```

### Notes

- Hook menggunakan `useMemo` untuk optimasi performa
- Semua calculations di-memoize dengan dependency arrays yang tepat
- Hook ini pure function - tidak ada side effects
- Dapat digunakan di komponen lain yang membutuhkan stats serupa
