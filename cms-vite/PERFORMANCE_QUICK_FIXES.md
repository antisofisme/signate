# Performance Quick Fixes - Action Checklist

**Last Updated:** November 26, 2025
**Priority:** CRITICAL - Start Today

---

## 🚨 CRITICAL: Fix Excessive API Polling (4-6 hours)

### Problem:
- 31 queries use `refetchInterval`
- Dashboard makes 8 API calls every 10-30 seconds
- **100-200 unnecessary requests per minute**

### Fix Locations:

#### 1. Device List Polling (CRITICAL)
**File:** `/src/features/devices/hooks/useDevices.ts` (Line 44-45)

```typescript
// ❌ REMOVE THIS:
export const useDeviceList = (filters?: {...}) => {
  return useQuery({
    queryKey: deviceKeys.list(filters),
    queryFn: () => deviceApi.list(filters),
    staleTime: 10000,
    refetchInterval: 10000, // ← DELETE THIS LINE
  });
};

// ✅ REPLACE WITH:
export const useDeviceList = (filters?: {...}) => {
  return useQuery({
    queryKey: deviceKeys.list(filters),
    queryFn: () => deviceApi.list(filters),
    staleTime: 30000, // 30 seconds (reasonable for device list)
    // No refetchInterval - let WebSocket handle updates
  });
};
```

#### 2. Dashboard Polling (8 queries)
**File:** `/src/features/dashboard/api/dashboard.api.ts` (Lines 169, 177, 185, 193, 201, 209, 217, 233)

```typescript
// ❌ REMOVE refetchInterval from ALL these hooks:

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.getStats,
    // refetchInterval: 30000, // ← DELETE
  });
};

export const useDeviceHealth = () => {
  return useQuery({
    queryKey: ['dashboard', 'device-health'],
    queryFn: dashboardApi.getDeviceHealth,
    // refetchInterval: 30000, // ← DELETE
  });
};

export const useLiveDevices = () => {
  return useQuery({
    queryKey: ['dashboard', 'live-devices'],
    queryFn: dashboardApi.getLiveDevices,
    // refetchInterval: 10000, // ← DELETE (most aggressive!)
  });
};

// ... repeat for remaining 5 hooks
```

#### 3. Analytics Polling (5 queries)
**File:** `/src/features/analytics/hooks/index.ts`

Search for: `refetchInterval: 30000`
Replace with: `// Manual refresh only`

### Add Manual Refresh Buttons:

**Dashboard Example:**
```tsx
// /src/pages/DashboardPage.tsx
import { RefreshCw } from 'lucide-react';

export default function DashboardPage() {
  const { refetch: refetchStats } = useDashboardStats();
  const { refetch: refetchHealth } = useDeviceHealth();
  // ... other hooks

  const handleRefreshAll = () => {
    refetchStats();
    refetchHealth();
    // ... refetch others
  };

  return (
    <>
      <PageHeader
        title={t('dashboard.title')}
        description={`${t('dashboard.welcome')}, ${user?.full_name}!`}
        action={
          <button
            onClick={handleRefreshAll}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh Dashboard
          </button>
        }
      />
      {/* ... rest of dashboard */}
    </>
  );
}
```

**Devices Page Example:**
```tsx
// /src/features/devices/components/DeviceTable.tsx (line 257)

<div className="flex items-center gap-2">
  {/* Add refresh button */}
  <button
    onClick={() => refetch()} // From useDeviceList hook
    className="flex items-center gap-2 px-4 py-2 border rounded-lg"
  >
    <RefreshCw className="w-4 h-4" />
    Refresh
  </button>

  {/* Existing buttons */}
  <button onClick={() => setTvRegisterModal(true)}>
    Register TV
  </button>
  {/* ... */}
</div>
```

### Keep ONLY Critical WebSocket Updates:

**Already Implemented:** `/src/features/devices/hooks/useDeviceWebSocket.ts`
**Status:** ✅ Good - Keep this for real-time device status

---

## 🚨 CRITICAL: Lazy Load Recharts (2-4 hours)

### Problem:
- Recharts is **311 KB** (94 KB gzipped)
- Loaded on every page, only used in 2-3 pages
- Blocks initial load by ~300ms

### Fix Option A: Lazy Load (Recommended)

**File:** `/src/features/dashboard/components/ContentPerformanceAnalytics.tsx`

```tsx
// ❌ CURRENT:
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// ✅ REPLACE WITH:
import { lazy, Suspense } from 'react';

const RechartsBarChart = lazy(() =>
  import('recharts').then(module => ({
    default: () => (
      <module.BarChart data={data}>
        <module.CartesianGrid strokeDasharray="3 3" />
        <module.XAxis dataKey="name" />
        <module.YAxis />
        <module.Tooltip />
        <module.Bar dataKey="value" fill="#3b82f6" />
      </module.BarChart>
    )
  }))
);

export function ContentPerformanceAnalytics({ data, isLoading }) {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <RechartsBarChart />
    </Suspense>
  );
}
```

### Fix Option B: Replace with Chart.js (150 KB)

```bash
npm install react-chartjs-2 chart.js
```

```tsx
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export function ContentPerformanceAnalytics({ data }) {
  const chartData = {
    labels: data.map(d => d.name),
    datasets: [{
      label: 'Performance',
      data: data.map(d => d.value),
      backgroundColor: '#3b82f6',
    }],
  };

  return <Bar data={chartData} />;
}
```

**Savings:** 311 KB → 150 KB (-161 KB / -52%)

---

## ⚡ HIGH: Lazy Load DeviceTable Modals (2-3 hours)

### Problem:
- 6 heavy modals loaded upfront (~100 KB)
- DevicesPage is 180 KB total

### Fix:

**File:** `/src/features/devices/components/DeviceTable.tsx` (Lines 36-42)

```tsx
// ❌ CURRENT:
import { TVRegisterModal } from './modals/TVRegisterModal';
import { MonitorRegisterModal } from './modals/MonitorRegisterModal';
import { ActivationCodeModal } from './modals/ActivationCodeModal';
import { DeviceManagementModal } from './modals/DeviceManagementModal';
import { DeviceSettingsModal } from './modals/DeviceSettingsModal';
import { UnifiedContentAssignmentModal } from './modals/UnifiedContentAssignmentModal';
import { DeviceLogsModal } from './modals/DeviceLogsModal';

// ✅ REPLACE WITH:
import { lazy, Suspense } from 'react';

const TVRegisterModal = lazy(() => import('./modals/TVRegisterModal').then(m => ({ default: m.TVRegisterModal })));
const MonitorRegisterModal = lazy(() => import('./modals/MonitorRegisterModal').then(m => ({ default: m.MonitorRegisterModal })));
const ActivationCodeModal = lazy(() => import('./modals/ActivationCodeModal').then(m => ({ default: m.ActivationCodeModal })));
const DeviceManagementModal = lazy(() => import('./modals/DeviceManagementModal').then(m => ({ default: m.DeviceManagementModal })));
const DeviceSettingsModal = lazy(() => import('./modals/DeviceSettingsModal').then(m => ({ default: m.DeviceSettingsModal })));
const UnifiedContentAssignmentModal = lazy(() => import('./modals/UnifiedContentAssignmentModal').then(m => ({ default: m.UnifiedContentAssignmentModal })));
const DeviceLogsModal = lazy(() => import('./modals/DeviceLogsModal').then(m => ({ default: m.DeviceLogsModal })));

// Reusable loading fallback
const ModalLoader = () => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
);
```

**Update Modal Renders (Lines 511-570):**

```tsx
// Wrap each modal in Suspense:

{/* TV Registration Modal */}
{tvRegisterModal && (
  <Suspense fallback={<ModalLoader />}>
    <TVRegisterModal
      isOpen={tvRegisterModal}
      onClose={() => setTvRegisterModal(false)}
      onSuccess={(device) => setActivationCodeModal({ isOpen: true, device })}
    />
  </Suspense>
)}

{/* Repeat for all 6 modals */}
```

**Expected:** DevicesPage bundle: 180 KB → 80 KB (-100 KB)

---

## ⚡ HIGH: Add Memoization to DeviceTable (3-4 hours)

### Problem:
- Status badge calculated for every device on every render
- Type icon rendered without memoization
- Filter operations inline without useMemo

### Fix 1: Memoize Status Badge Component

**File:** `/src/features/devices/components/DeviceTable.tsx` (Lines 182-216)

```tsx
// ❌ CURRENT:
const getStatusBadge = (device: Device) => {
  const isOnline = device.last_seen_at
    ? new Date().getTime() - new Date(device.last_seen_at).getTime() < 5 * 60 * 1000
    : false;
  // ... JSX
};

// ✅ REPLACE WITH MEMOIZED COMPONENT:
const StatusBadge = React.memo(({ device }: { device: Device }) => {
  const isOnline = useMemo(() => {
    if (!device.last_seen_at) return false;
    return new Date().getTime() - new Date(device.last_seen_at).getTime() < 5 * 60 * 1000;
  }, [device.last_seen_at]);

  if (device.status === 'pending') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
        <Circle className="w-2 h-2 fill-current" />
        {t('devices.status.pending')}
      </span>
    );
  }

  return isOnline ? (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
      <Circle className="w-2 h-2 fill-current" />
      {t('devices.online')}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
      <Circle className="w-2 h-2 fill-current" />
      {t('devices.offline')}
    </span>
  );
});

// UPDATE TABLE (Line 428):
<td className="px-6 py-4 whitespace-nowrap">
  <StatusBadge device={device} />
</td>
```

### Fix 2: Memoize Device Type Icon

```tsx
// ✅ CREATE MEMOIZED COMPONENT:
const DeviceTypeIcon = React.memo(({ type }: { type: DeviceType }) => {
  return type === 'tv' ? <Tv className="w-4 h-4" /> : <Monitor className="w-4 h-4" />;
});

// UPDATE TABLE (Line 422):
<td className="px-6 py-4 whitespace-nowrap">
  <div className="flex items-center gap-2">
    <DeviceTypeIcon type={device.device_type} />
    <span className="capitalize">{device.device_type}</span>
  </div>
</td>
```

### Fix 3: Memoize Filtered Devices

**Line 345-363:**

```tsx
// ❌ CURRENT:
{devices.filter((d) => d.status === 'pending').length > 0 && (
  <div>
    {devices
      .filter((d) => d.status === 'pending')
      .map((device) => <PendingDeviceCard key={device.id} device={device} />)}
  </div>
)}

// ✅ REPLACE WITH:
const pendingDevices = useMemo(
  () => devices.filter((d) => d.status === 'pending'),
  [devices]
);

{pendingDevices.length > 0 && (
  <div>
    {pendingDevices.map((device) => (
      <PendingDeviceCard key={device.id} device={device} />
    ))}
  </div>
)}
```

**Expected:** +30% faster renders on device list updates

---

## 📋 Quick Checklist

### Today (4-6 hours):
- [ ] Remove `refetchInterval` from `/src/features/devices/hooks/useDevices.ts` (Line 45)
- [ ] Remove `refetchInterval` from `/src/features/dashboard/api/dashboard.api.ts` (8 hooks)
- [ ] Remove `refetchInterval` from `/src/features/analytics/hooks/index.ts` (5 hooks)
- [ ] Add "Refresh" button to DashboardPage
- [ ] Add "Refresh" button to DeviceTable

### This Week (8-12 hours):
- [ ] Lazy load Recharts OR replace with Chart.js
- [ ] Lazy load 6 DeviceTable modals
- [ ] Add memoization: StatusBadge component
- [ ] Add memoization: DeviceTypeIcon component
- [ ] Add useMemo: pendingDevices filter

### Next Week (8-12 hours):
- [ ] Implement react-virtual for DeviceTable
- [ ] Implement react-virtual for ContentTable
- [ ] Priority-based Dashboard loading
- [ ] Verify Gzip/Brotli compression on production

---

## 🎯 Expected Results After Quick Fixes

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Network Requests** | 100-200/min | 10-20/min | **-90%** |
| **DevicesPage Bundle** | 180 KB | 80 KB | **-100 KB** |
| **Initial Load Time** | ~3s | ~1.8s | **-40%** |
| **Render Performance** | Baseline | +30% faster | **+30%** |

---

## 🚀 Commands to Run

```bash
# 1. Find all refetchInterval usage
grep -r "refetchInterval" /mnt/g/khoirul/signate/cms-vite/src --include="*.ts" --include="*.tsx"

# 2. Test build after changes
cd /mnt/g/khoirul/signate/cms-vite
npm run build

# 3. Verify bundle sizes
ls -lh dist/assets/*.js | sort -k5 -hr | head -10

# 4. Test in browser
npm run preview
```

---

## 📞 Need Help?

If stuck on any of these fixes:
1. Check `/mnt/g/khoirul/signate/cms-vite/PERFORMANCE_REVIEW_REPORT.md` for detailed explanations
2. Review TanStack Query docs: https://tanstack.com/query/latest/docs/react/guides/performance
3. Test incrementally - commit after each fix

**Start with API polling removal - biggest impact with least risk!**
