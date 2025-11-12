# Dashboard Implementation Roadmap

## Phase 1: Core Metrics (Week 1-2)

### Components to Build
1. **OverviewCards.tsx** - 6 metric cards in grid layout
   - Total Devices
   - Devices Online (with color indicator)
   - Total Content
   - Active Playlists
   - Watch Time (24h)
   - Completion Rate (24h)

2. **DeviceHealthSummary.tsx** - Organization health donut/bar chart
   - Shows: Healthy, Warning, Critical, Offline counts
   - Clickable to drill down into each status

### API Integration
- Create `dashboardApi.ts` with functions:
  - `getDevices()` - List devices
  - `getHealthSummary(orgId)` - Organization health
  - `getAnalyticsStats(dateRange)` - 24h playback stats
  - `getContentStats()` - Storage breakdown
  - `getPlaylists()` - Active playlists

### Data Hooks
- `useDashboard()` - Main dashboard hook using TanStack Query
  - Fetch all core data with stale times (30s-300s)
  - Handle errors gracefully
  - Provide loading states

### File Structure
```
cms-vite/src/features/dashboard/
├── api/
│   └── dashboardApi.ts
├── components/
│   ├── OverviewCards.tsx
│   └── DeviceHealthSummary.tsx
├── hooks/
│   └── useDashboard.ts
├── types/
│   └── dashboard.ts
└── pages/
    └── DashboardPage.tsx (update from current placeholder)
```

### Deliverables
- [ ] Update DashboardPage.tsx to use real API data
- [ ] Create 6 overview metric cards
- [ ] Create health summary donut chart
- [ ] Connect TanStack Query for caching
- [ ] Implement error boundaries
- [ ] Add loading skeletons

---

## Phase 2: Monitoring & Analytics (Week 3-4)

### Components to Build
1. **DeviceMonitoringList.tsx** - Device status grid/table
   - Columns: Name, Room, Status, Last Seen, Health, Playlist
   - Filtering: By status, location, health
   - Grouping: By device group
   - Quick actions: View logs, send command

2. **ContentAnalytics.tsx** - Top content table + storage chart
   - Top 5 content by plays
   - Completion rates
   - Device count
   - Pie/bar chart for storage by type

3. **ActivityFeed.tsx** - Recent audit logs
   - Time-grouped activity items
   - Human-readable action descriptions
   - Filtering: By action type, resource type, user

### API Functions to Add
- `getDevicesList()` - Enhanced with filters
- `getDeviceHealth(deviceId)` - Individual device health
- `getContentPerformance(dateRange)` - Top content
- `getAuditLogs(limit)` - Recent activities
- `getContentStats()` - Storage breakdown

### New Data Hooks
- `useDeviceMonitoring()` - Device list with polling
- `useContentPerformance()` - Top content analytics
- `useActivityFeed()` - Audit logs with refresh

### File Additions
```
cms-vite/src/features/dashboard/components/
├── DeviceMonitoringList.tsx
├── ContentAnalytics.tsx
├── ActivityFeed.tsx
└── ActivityFeedItem.tsx (utility component)
```

### Deliverables
- [ ] Create device monitoring grid with status colors
- [ ] Implement filtering and grouping
- [ ] Create top content table with performance metrics
- [ ] Add storage breakdown pie chart
- [ ] Build activity feed with time grouping
- [ ] Add filter controls for activity feed

---

## Phase 3: Advanced Insights (Week 5-6)

### Components to Build
1. **PlaybackTimeline.tsx** - Multi-line chart
   - Total plays, Completed plays, Unique devices, Unique content
   - Time range selector (7d, 30d, custom)
   - Interval selector (day, week, month)

2. **DeviceEngagement.tsx** - Device engagement table
   - Top devices by watch time
   - Unique content per device
   - Last playback timestamp

3. **QuickActions.tsx** - Shortcut panel
   - Upload Content
   - Create Playlist
   - Add Device
   - Send Command
   - View Offline Devices

4. **SystemHealth.tsx** - System indicators (optional)
   - Database status
   - Storage capacity
   - Error logs summary
   - Active sessions

### API Functions to Add
- `getPlaybackTimeline(dateRange, interval)` - Timeline chart data
- `getDeviceEngagement(dateRange, limit)` - Device engagement stats

### New Data Hooks
- `usePlaybackTimeline()` - Timeline data with date range handling
- `useDeviceEngagement()` - Device engagement metrics

### Chart Library
- Use **Recharts** or **Chart.js**
- Multi-axis chart for timeline
- Pie chart for storage
- Bar charts for engagement

### File Additions
```
cms-vite/src/features/dashboard/components/
├── PlaybackTimeline.tsx
├── DeviceEngagement.tsx
├── QuickActions.tsx
└── SystemHealth.tsx
```

### Deliverables
- [ ] Create playback timeline multi-line chart
- [ ] Add date range and interval selectors
- [ ] Create device engagement table
- [ ] Build quick actions panel
- [ ] Add system health indicators
- [ ] Implement refresh controls

---

## Phase 4: Real-time & Optimization (Week 7-8)

### Enhancements
1. **Real-time Updates**
   - Implement WebSocket connection for device status
   - Real-time health alerts
   - Live activity feed (5s refresh)

2. **Performance Optimization**
   - Implement data caching with TanStack Query
   - Lazy load non-critical components
   - Virtualize long lists
   - Image optimization for thumbnails

3. **Mobile Responsiveness**
   - Adapt grid layouts for mobile
   - Stack cards vertically
   - Collapse detailed tables
   - Touch-friendly buttons

4. **Accessibility**
   - ARIA labels on charts
   - Keyboard navigation
   - Color contrast compliance
   - Screen reader support

### Files to Update
- `dashboardApi.ts` - Add WebSocket hooks
- All components - Add responsiveness
- `useDashboard.ts` - Add stale times and refetch intervals

### Deliverables
- [ ] Add WebSocket for real-time device status
- [ ] Optimize bundle size
- [ ] Implement responsive design
- [ ] Add accessibility features
- [ ] Performance testing
- [ ] Load testing

---

## Implementation Checklist

### Setup
- [ ] Create `/features/dashboard` folder structure
- [ ] Install chart library (Recharts/Chart.js)
- [ ] Setup TanStack Query in dashboard hook
- [ ] Create TypeScript types for all responses

### Phase 1 (Core)
- [ ] Create `dashboardApi.ts` with core functions
- [ ] Create `useDashboard.ts` hook
- [ ] Create `OverviewCards.tsx` component
- [ ] Create `DeviceHealthSummary.tsx` component
- [ ] Update `DashboardPage.tsx` to use components
- [ ] Test all API integrations
- [ ] Add error handling and loading states

### Phase 2 (Monitoring)
- [ ] Create `DeviceMonitoringList.tsx`
- [ ] Add filtering and grouping logic
- [ ] Create `ContentAnalytics.tsx`
- [ ] Add storage breakdown chart
- [ ] Create `ActivityFeed.tsx`
- [ ] Add audit log parsing and formatting
- [ ] Implement activity filters

### Phase 3 (Advanced)
- [ ] Create `PlaybackTimeline.tsx`
- [ ] Implement date range picker
- [ ] Create `DeviceEngagement.tsx`
- [ ] Create `QuickActions.tsx`
- [ ] Add system health section
- [ ] Integrate charts library
- [ ] Test chart responsiveness

### Phase 4 (Optimization)
- [ ] Add WebSocket integration
- [ ] Optimize queries with limits
- [ ] Implement pagination
- [ ] Mobile responsive design
- [ ] Accessibility audit
- [ ] Performance profiling
- [ ] Load testing

---

## Code Examples

### Example 1: API Hook
```typescript
// useDashboard.ts
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/features/dashboard/api/dashboardApi'
import { useAuthStore } from '@/lib/stores/authStore'

export function useDashboard() {
  const { user } = useAuthStore()

  const devicesQuery = useQuery({
    queryKey: ['devices'],
    queryFn: () => dashboardApi.getDevices(),
    staleTime: 30 * 1000, // 30s
    refetchInterval: 60 * 1000, // poll every minute
  })

  const healthQuery = useQuery({
    queryKey: ['health-summary', user?.organization_id],
    queryFn: () => dashboardApi.getHealthSummary(user!.organization_id),
    staleTime: 60 * 1000, // 60s
  })

  const analyticsQuery = useQuery({
    queryKey: ['analytics-stats', 'last-24h'],
    queryFn: () => {
      const now = new Date()
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      return dashboardApi.getAnalyticsStats({
        startDate: yesterday.toISOString(),
        endDate: now.toISOString(),
      })
    },
    staleTime: 5 * 60 * 1000, // 5 min
  })

  return {
    devices: devicesQuery.data,
    devicesLoading: devicesQuery.isLoading,
    health: healthQuery.data,
    healthLoading: healthQuery.isLoading,
    analytics: analyticsQuery.data,
    analyticsLoading: analyticsQuery.isLoading,
  }
}
```

### Example 2: API Service
```typescript
// dashboardApi.ts
import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'

export const dashboardApi = {
  async getDevices() {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.LIST)
    return response.data
  },

  async getHealthSummary(organizationId: number) {
    const response = await apiClient.get(
      `/api/v1/organizations/${organizationId}/health/summary`
    )
    return response.data
  },

  async getAnalyticsStats(params: { startDate: string; endDate: string }) {
    const response = await apiClient.get(API_ENDPOINTS.ANALYTICS.DASHBOARD, {
      params: {
        start_date: params.startDate,
        end_date: params.endDate,
      },
    })
    return response.data
  },

  // ... more functions
}
```

### Example 3: Component Usage
```typescript
// OverviewCards.tsx
export function OverviewCards() {
  const { devices, health, analytics, analyticsLoading } = useDashboard()

  const totalDevices = devices?.length ?? 0
  const onlineDevices = devices?.filter(d => isOnline(d.last_seen)).length ?? 0
  const watchTime = analytics?.total_watch_time_hours ?? 0
  const completionRate = analytics?.completion_rate ?? 0

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatCard
        title="Total Devices"
        value={totalDevices}
        icon={<DevicesIcon />}
        loading={analyticsLoading}
      />
      <StatCard
        title="Online"
        value={onlineDevices}
        icon={<OnlineIcon />}
        color={getHealthColor(onlineDevices / totalDevices)}
        loading={analyticsLoading}
      />
      <StatCard
        title="Watch Time (24h)"
        value={`${watchTime.toFixed(1)} hrs`}
        icon={<ClockIcon />}
        loading={analyticsLoading}
      />
      {/* More cards... */}
    </div>
  )
}
```

---

## Testing Strategy

### Unit Tests
- Test API functions with mock data
- Test data transformations
- Test date calculations

### Integration Tests
- Test hook data fetching
- Test error handling
- Test caching behavior

### E2E Tests
- Test full dashboard load
- Test data updates
- Test filtering and grouping
- Test responsive layouts

### Performance Tests
- Lighthouse score > 90
- First paint < 2s
- TTI (Time to Interactive) < 3s
- No layout shifts

---

## Deployment Notes

### Staging Environment
1. Deploy dashboard feature to staging
2. Test with production data (if available)
3. Performance test with real device count
4. User acceptance testing

### Production Release
1. Monitor error logs in first 24h
2. Track performance metrics
3. Gather user feedback
4. Plan Phase 2 improvements

---

## Success Criteria

### Phase 1
- [ ] All 6 overview cards display correct data
- [ ] Health summary shows accurate counts
- [ ] No console errors
- [ ] Load time < 2 seconds
- [ ] Responsive on mobile

### Phase 2
- [ ] Device list loads 50+ devices without lag
- [ ] Content analytics chart renders correctly
- [ ] Activity feed shows 10+ items
- [ ] Filtering works smoothly
- [ ] Mobile responsive

### Phase 3
- [ ] Timeline chart displays multiple series
- [ ] Date range picker works correctly
- [ ] Device engagement table sortable
- [ ] Quick actions functional
- [ ] All components responsive

### Phase 4
- [ ] Real-time status updates working
- [ ] Performance score > 85
- [ ] Mobile metrics optimized
- [ ] Accessibility audit passed
- [ ] All keyboard navigation working

---

## Estimated Effort

| Phase | Duration | Components | Complexity |
|-------|----------|-----------|-----------|
| 1 | 2 weeks | 2 | Low-Medium |
| 2 | 2 weeks | 3 | Medium |
| 3 | 2 weeks | 4 | Medium-High |
| 4 | 2 weeks | - | High |
| **Total** | **8 weeks** | **9** | **Medium** |

---

## Dependencies

### Frontend
- React 18+
- TypeScript
- TanStack Query
- Zustand
- Recharts or Chart.js
- Tailwind CSS
- shadcn/ui

### Backend
- FastAPI endpoints (all already implemented)
- Database with proper indexes
- Authentication middleware

### Infrastructure
- CORS enabled for WebSocket
- WebSocket support
- Redis for caching (optional)

---

## Risk Mitigation

### High Data Volume
- **Risk**: Dashboard slow with many devices
- **Mitigation**: Implement pagination, lazy loading, virtual lists

### Real-time Sync Issues
- **Risk**: WebSocket connection drops
- **Mitigation**: Fallback to polling, retry logic, error boundaries

### Stale Data
- **Risk**: Cached data becomes outdated
- **Mitigation**: Configure appropriate stale times, implement refresh buttons

### Performance Degradation
- **Risk**: Too many queries impact backend
- **Mitigation**: Implement caching, reduce query frequency, batch requests

---

## Future Enhancements

### Phase 5 (Post-MVP)
- [ ] Scheduled reports (email, PDF)
- [ ] Data export (CSV, Excel)
- [ ] Custom dashboard layouts
- [ ] Alert configuration UI
- [ ] Dashboard sharing
- [ ] Mobile app
- [ ] Dark mode
- [ ] Internationalization

