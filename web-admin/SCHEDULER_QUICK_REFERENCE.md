# Scheduler UI - Quick Reference Guide

## File Locations

### Types
```
/mnt/g/khoirul/signate/web-admin/src/types/scheduler.ts
```

### API Module
```
/mnt/g/khoirul/signate/web-admin/src/services/api/scheduler.ts
```

### Components
```
/mnt/g/khoirul/signate/web-admin/src/components/scheduler/
├── SchedulerStatus.tsx          # Main scheduler dashboard
├── DeviceScheduleCard.tsx       # Individual device card with countdown
└── index.ts                     # Component exports
```

### Integration
```
/mnt/g/khoirul/signate/web-admin/src/pages/Devices.tsx
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scheduler/status` | Get scheduler service status |
| GET | `/api/scheduler/devices/schedules` | Get all device schedules |
| GET | `/api/scheduler/devices/{id}/schedule` | Get specific device schedule |
| POST | `/api/scheduler/devices/{id}/refresh` | Refresh single device |
| POST | `/api/scheduler/refresh-all` | Refresh all active devices |

## Component Usage

### SchedulerStatus
```typescript
import { SchedulerStatus } from '@/components/scheduler'

// In your page/component
<SchedulerStatus />
```

**Features:**
- Auto-refresh every 30 seconds
- Service status monitoring
- Device schedules grid
- Manual refresh all button

### DeviceScheduleCard
```typescript
import { DeviceScheduleCard } from '@/components/scheduler'

<DeviceScheduleCard
  schedule={deviceSchedule}
  onRefresh={() => handleRefresh()}
/>
```

**Props:**
- `schedule`: DeviceSchedule object
- `onRefresh`: Callback function (optional)

## Type Imports

```typescript
import type {
  SchedulerStatus,
  DeviceSchedule,
  DeviceRefreshResult,
  BulkRefreshResult,
  CountdownState,
} from '@/types/scheduler'
```

## API Usage

```typescript
import { schedulerAPI } from '@/services/api'

// Get status
const { data } = await schedulerAPI.getStatus()

// Get all schedules
const { data } = await schedulerAPI.getAllDeviceSchedules()

// Get device schedule
const { data } = await schedulerAPI.getDeviceSchedule(deviceId)

// Refresh device
const { data } = await schedulerAPI.refreshDevice(deviceId)

// Refresh all
const { data } = await schedulerAPI.refreshAll()
```

## React Query Hooks

```typescript
// Fetch scheduler status
const { data, isLoading } = useQuery({
  queryKey: ['scheduler-status'],
  queryFn: () => schedulerAPI.getStatus(),
  refetchInterval: 30000, // 30 seconds
})

// Fetch device schedules
const { data, isLoading } = useQuery({
  queryKey: ['device-schedules'],
  queryFn: () => schedulerAPI.getAllDeviceSchedules(),
  refetchInterval: 30000,
})

// Refresh device mutation
const refreshMutation = useMutation({
  mutationFn: (deviceId: number) => schedulerAPI.refreshDevice(deviceId),
  onSuccess: (response) => {
    toast.success('Device refreshed successfully')
    queryClient.invalidateQueries({ queryKey: ['device-schedules'] })
  },
})

// Refresh all mutation
const refreshAllMutation = useMutation({
  mutationFn: () => schedulerAPI.refreshAll(),
  onSuccess: (response) => {
    const result = response.data
    toast.success(`Refreshed ${result.successful} of ${result.total_devices} devices`)
  },
})
```

## Color Coding Reference

### Status Colors
```typescript
// Service Status
'running'  → Green (green-600)
'stopped'  → Gray (gray-600)
'error'    → Red (red-600)

// Device Status
Online     → Green border (border-green-300)
Offline    → Gray border (border-gray-300)

// Countdown Colors
> 5 min    → Green (text-green-600)
< 5 min    → Orange (text-orange-600)
Expired    → Red (text-red-600)
```

### Border Colors by State
```typescript
const getBorderColor = (): string => {
  if (!schedule.is_online) return 'border-gray-300'
  if (countdown.isExpired) return 'border-red-300'
  if (countdown.totalSeconds < 300) return 'border-orange-300'
  return 'border-green-300'
}
```

## Countdown Calculation

```typescript
// Calculate countdown from deadline
function calculateCountdown(deadline: string | null): CountdownState {
  if (!deadline) {
    return {
      days: 0, hours: 0, minutes: 0, seconds: 0,
      totalSeconds: 0, isExpired: true
    }
  }

  const now = new Date().getTime()
  const deadlineTime = new Date(deadline).getTime()
  const diff = Math.floor((deadlineTime - now) / 1000)

  if (diff <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, totalSeconds: 0, isExpired: true }
  }

  return {
    days: Math.floor(diff / 86400),
    hours: Math.floor((diff % 86400) / 3600),
    minutes: Math.floor((diff % 3600) / 60),
    seconds: diff % 60,
    totalSeconds: diff,
    isExpired: false,
  }
}

// Format countdown for display
function formatCountdown(countdown: CountdownState): string {
  if (countdown.isExpired) return 'Expired'

  const parts: string[] = []
  if (countdown.days > 0) parts.push(`${countdown.days}d`)
  if (countdown.hours > 0 || countdown.days > 0) parts.push(`${countdown.hours}h`)
  if (countdown.minutes > 0 || countdown.hours > 0 || countdown.days > 0) {
    parts.push(`${countdown.minutes}m`)
  }
  parts.push(`${countdown.seconds}s`)

  return parts.join(' ')
}
```

## Icons Used (Lucide React)

```typescript
import {
  Clock,         // Scheduler tab, deadlines
  RefreshCw,     // Refresh buttons
  CheckCircle,   // Running, online, success
  XCircle,       // Stopped, offline, error
  AlertCircle,   // Errors, expired
  Activity,      // Service status, activity
  Server,        // Devices, empty state
  PlayCircle,    // Currently playing
} from 'lucide-react'
```

## Responsive Breakpoints

```typescript
// Grid columns
grid-cols-1              // Mobile (< 640px)
md:grid-cols-2          // Tablet (640px - 1024px)
lg:grid-cols-3          // Desktop (> 1024px)

// Statistics grid
grid-cols-1              // Mobile
sm:grid-cols-2          // Tablet
lg:grid-cols-4          // Desktop
```

## Auto-Refresh Configuration

```typescript
// Component level
refetchInterval: 30000  // 30 seconds (React Query)

// Countdown timer
setInterval(() => {
  setCountdown(calculateCountdown(deadline))
}, 1000)  // Update every 1 second
```

## Navigation Integration

```typescript
// In Devices page
const [activeTab, setActiveTab] = useState<'devices' | 'scheduler'>('devices')

// Tab buttons
<button onClick={() => setActiveTab('scheduler')}>
  <Clock className="w-4 h-4" />
  Scheduler
</button>

// Conditional rendering
{activeTab === 'scheduler' ? (
  <SchedulerStatus />
) : (
  <DevicesList />
)}
```

## Toast Notifications

```typescript
import toast from 'react-hot-toast'

// Success
toast.success('Device refreshed successfully', {
  duration: 3000,
  position: 'bottom-right',
})

// Error
toast.error('Failed to refresh device', {
  duration: 4000,
  position: 'bottom-right',
})

// With details
toast.success(
  `Refreshed ${result.successful} of ${result.total_devices} devices`,
  { duration: 4000, position: 'bottom-right' }
)
```

## Backend Response Format

### Scheduler Status Response
```json
{
  "success": true,
  "data": {
    "status": "running",
    "last_run": "2025-10-28T10:30:00Z",
    "next_run": "2025-10-28T10:35:00Z",
    "devices_count": 15,
    "total_refreshes": 342,
    "uptime_seconds": 86400,
    "error_message": null
  },
  "meta": {
    "timestamp": "2025-10-28T10:45:00Z",
    "request_id": "req_abc123"
  }
}
```

### Device Schedule Response
```json
{
  "success": true,
  "data": [
    {
      "device_id": 1,
      "device_name": "TV-001",
      "device_status": "active",
      "next_deadline": "2025-10-28T11:00:00Z",
      "seconds_until_deadline": 1800,
      "current_content": {
        "id": 5,
        "title": "Promo Video",
        "type": "video"
      },
      "current_playlist": null,
      "last_refresh": "2025-10-28T10:30:00Z",
      "is_online": true
    }
  ],
  "meta": {
    "timestamp": "2025-10-28T10:45:00Z",
    "request_id": "req_def456"
  }
}
```

### Refresh Result Response
```json
{
  "success": true,
  "data": {
    "device_id": 1,
    "device_name": "TV-001",
    "success": true,
    "items_refreshed": 5,
    "error_message": null,
    "refreshed_at": "2025-10-28T10:45:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T10:45:00Z",
    "request_id": "req_ghi789"
  }
}
```

### Bulk Refresh Response
```json
{
  "success": true,
  "data": {
    "total_devices": 15,
    "successful": 14,
    "failed": 1,
    "results": [
      {
        "device_id": 1,
        "device_name": "TV-001",
        "success": true,
        "items_refreshed": 5,
        "refreshed_at": "2025-10-28T10:45:00Z"
      }
    ],
    "refreshed_at": "2025-10-28T10:45:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T10:45:00Z",
    "request_id": "req_jkl012"
  }
}
```

## Testing Checklist

### Unit Tests
- [ ] Countdown calculation logic
- [ ] Countdown formatting
- [ ] Status color determination
- [ ] Border color logic
- [ ] Error state handling

### Integration Tests
- [ ] Auto-refresh mechanism
- [ ] Manual device refresh
- [ ] Bulk refresh all
- [ ] Query cache invalidation
- [ ] Toast notifications

### E2E Tests
- [ ] Navigate to Scheduler tab
- [ ] Verify service status
- [ ] Verify device cards render
- [ ] Click refresh button
- [ ] Wait for auto-refresh
- [ ] Verify countdown updates

## Common Issues & Solutions

### Issue: Countdown not updating
**Solution:** Ensure useEffect cleanup function clears interval
```typescript
useEffect(() => {
  const interval = setInterval(() => {
    setCountdown(calculateCountdown(deadline))
  }, 1000)

  return () => clearInterval(interval) // Cleanup!
}, [deadline])
```

### Issue: API not refreshing
**Solution:** Check refetchInterval and query key
```typescript
refetchInterval: 30000, // Must be set
queryKey: ['device-schedules'], // Must be unique
```

### Issue: Mutations not updating UI
**Solution:** Invalidate queries after mutation
```typescript
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ['device-schedules'] })
}
```

### Issue: TypeScript errors
**Solution:** Import types from correct path
```typescript
import type { DeviceSchedule } from '@/types/scheduler'
```

## Development Commands

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

## Environment Variables

```env
VITE_API_URL=http://192.168.5.12:8001
VITE_DEBUG_API=false
```

## Browser Support

- Chrome/Edge: ✅ Latest 2 versions
- Firefox: ✅ Latest 2 versions
- Safari: ✅ Latest 2 versions
- Mobile browsers: ✅ iOS Safari, Chrome Android

## Performance Tips

1. Use React.memo for DeviceScheduleCard
2. Use useCallback for stable function references
3. Implement virtual scrolling for > 100 devices
4. Optimize countdown calculations
5. Debounce manual refresh buttons

## Accessibility

- Semantic HTML (sections, headings)
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast WCAG AA compliant
- Screen reader friendly

---

**Phase 2 Scheduler UI: 100% Complete** ✅
