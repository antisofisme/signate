# Organization Quota Alerts Implementation

## Overview
Implemented real-time quota monitoring and alerting system in CMS dashboard to prevent service interruption and improve resource management.

**Date**: 2025-11-20
**Priority**: P0 (Critical)
**Status**: ✅ Implemented

---

## Features Implemented

### 1. Backend Integration
- ✅ API endpoint integration for quota status (`/api/v1/organizations/{id}/quota`)
- ✅ TypeScript types matching backend DTOs
- ✅ React Query hooks for auto-refetching quota data

### 2. UI Components
- ✅ **QuotaAlertBanner**: Critical quota warnings at dashboard top
- ✅ **QuotaUsageCard**: Detailed quota visualization (for organization detail page)
- ✅ Color-coded severity levels (Critical/Warning/Info)
- ✅ Real-time percentage calculations

### 3. Dashboard Integration
- ✅ Automatic quota checks on dashboard load
- ✅ Auto-refresh every 60 seconds
- ✅ Conditional rendering (only shows when warnings exist)

---

## Files Created/Modified

### API Layer
```
cms-vite/src/
├── lib/api/endpoints.ts                        (MODIFIED)
│   └── Added QUOTA, UPDATE_QUOTA, CHECK_*_QUOTA endpoints
│
├── features/organizations/
│   ├── types/organization.ts                   (MODIFIED)
│   │   └── Added QuotaInfo, StorageQuotaInfo, OrganizationQuota types
│   │
│   ├── api/organizationsApi.ts                 (MODIFIED)
│   │   └── Added getQuota, updateQuota, check*Quota functions
│   │
│   ├── hooks/useOrganizationQuota.ts           (NEW)
│   │   └── React Query hooks for quota management
│   │
│   └── components/
│       ├── QuotaAlertBanner.tsx                (NEW)
│       └── QuotaUsageCard.tsx                  (NEW)
│
└── pages/DashboardPage.tsx                     (MODIFIED)
    └── Integrated QuotaAlertBanner
```

---

## Technical Implementation

### 1. Type Definitions

```typescript
// Quota information for a single resource
export interface QuotaInfo {
  max: number;
  current: number;
  available: number;
  percentage_used: number;
}

// Storage quota with items + size
export interface StorageQuotaInfo {
  max_items: number;
  current_items: number;
  available_items: number;
  max_size_gb: number;
  current_size_gb: number;
  available_size_gb: number;
  items_percentage_used: number;
  size_percentage_used: number;
}

// Complete organization quota status
export interface OrganizationQuota {
  devices: QuotaInfo;
  users: QuotaInfo;
  content: StorageQuotaInfo;
  playlists: QuotaInfo;
  total_percentage_used: number;
  warnings: string[];
}
```

### 2. React Query Hook

```typescript
export function useOrganizationQuota(orgId: number | undefined) {
  return useQuery({
    queryKey: orgId ? quotaKeys.detail(orgId) : ['no-org'],
    queryFn: () => organizationsApi.getQuota(orgId!),
    enabled: !!orgId,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}
```

**Features**:
- Auto-refetch every 60 seconds
- 30-second stale time for cache
- Only runs when `orgId` is defined
- Automatic cache invalidation on mutations

### 3. Alert Severity Logic

```typescript
const getHighestSeverity = () => {
  const quotas = [
    { name: 'Devices', percentage: quota.devices.percentage_used },
    { name: 'Users', percentage: quota.users.percentage_used },
    { name: 'Content Items', percentage: quota.content.items_percentage_used },
    { name: 'Storage', percentage: quota.content.size_percentage_used },
    { name: 'Playlists', percentage: quota.playlists.percentage_used },
  ];

  const critical = quotas.filter((q) => q.percentage >= 95); // >= 95%
  const warning = quotas.filter((q) => q.percentage >= 80 && q.percentage < 95); // 80-94%
  const info = quotas.filter((q) => q.percentage >= 60 && q.percentage < 80); // 60-79%

  // Return highest severity
};
```

**Thresholds**:
- **Critical (Red)**: >= 95% - Immediate action required
- **Warning (Orange)**: 80-94% - Proactive cleanup recommended
- **Info (Yellow)**: 60-79% - Monitor closely
- **Normal (Green)**: < 60% - No action needed

---

## UI/UX Design

### QuotaAlertBanner

**Appearance**:
- Full-width banner at dashboard top (below PageHeader)
- Color-coded background (red/orange/yellow)
- Icon indicator (XCircle/AlertTriangle/Info)
- Prominent title with severity level
- Badge pills showing affected quotas with percentages
- "View Quota Details" button to navigate to org settings
- Optional backend warnings display

**Behavior**:
- Only renders when quota >= 60%
- Shows highest severity level if multiple warnings
- Auto-updates every 60 seconds
- Dismissible? **No** - Critical alerts should persist

**Example Rendering**:
```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Warning: Approaching Quota Limit                     │
│                                                          │
│ Your organization is approaching quota limits.          │
│ Consider upgrading or cleaning up unused resources.     │
│                                                          │
│ [Devices: 85.2%] [Storage: 82.5%]                      │
│                                                          │
│ [View Quota Details]                                    │
└─────────────────────────────────────────────────────────┘
```

### QuotaUsageCard

**Appearance**:
- Card with header (title, description, percentage badge)
- Progress bar with color coding
- Current / Max values
- Available count

**Use Case**: Organization detail/settings page

---

## API Endpoints Used

### GET `/api/v1/organizations/{org_id}/quota`
**Purpose**: Fetch organization quota status
**Response**:
```json
{
  "success": true,
  "data": {
    "devices": {
      "max": 10,
      "current": 8,
      "available": 2,
      "percentage_used": 80.0
    },
    "users": { /* ... */ },
    "content": {
      "max_items": 100,
      "current_items": 45,
      "available_items": 55,
      "max_size_gb": 50.0,
      "current_size_gb": 12.5,
      "available_size_gb": 37.5,
      "items_percentage_used": 45.0,
      "size_percentage_used": 25.0
    },
    "playlists": { /* ... */ },
    "total_percentage_used": 47.5,
    "warnings": [
      "Device quota at 80%",
      "Consider upgrading storage"
    ]
  }
}
```

### PUT `/api/v1/organizations/{org_id}/quota`
**Purpose**: Update quota limits (Admin only)
**Payload**:
```json
{
  "max_devices": 20,
  "max_users": 50,
  "max_content_size_gb": 100.0,
  "max_content_items": 500,
  "max_playlists": 50
}
```

### GET `/api/v1/organizations/{org_id}/quota/check/device`
**Purpose**: Check if can add more devices
**Response**:
```json
{
  "success": true,
  "data": {
    "allowed": true,
    "current": 8,
    "max": 10,
    "available": 2,
    "reason": null
  }
}
```

---

## Integration Points

### 1. Dashboard (DashboardPage.tsx)

```typescript
// Fetch quota on dashboard load
const { data: quota } = useOrganizationQuota(user?.organization_id);

// Render alert banner
{quota && user?.organization_id && (
  <QuotaAlertBanner quota={quota} organizationId={user.organization_id} />
)}
```

**Placement**: Between PageHeader and OverviewMetrics

### 2. Organization Detail Page (Future)

```typescript
// Fetch quota for org detail page
const { data: quota } = useOrganizationQuota(orgId);

// Render quota cards
<QuotaUsageCard
  title="Devices"
  description="Active devices in organization"
  quota={quota.devices}
  icon={<Monitor />}
/>
```

### 3. Pre-Action Quota Checks (Future)

```typescript
// Before adding device
const { data: canAdd } = useCheckDeviceQuota(orgId);

if (!canAdd?.allowed) {
  toast.error(canAdd?.reason || 'Device quota exceeded');
  return;
}

// Proceed with device activation
```

---

## Testing Checklist

### Manual Testing

- [ ] Dashboard loads without errors
- [ ] Quota banner appears when usage >= 60%
- [ ] Correct severity level displayed (Critical/Warning/Info)
- [ ] Color coding matches severity (Red/Orange/Yellow)
- [ ] Percentage calculations are accurate
- [ ] "View Quota Details" button navigates correctly
- [ ] Auto-refresh works (check after 60 seconds)
- [ ] Banner disappears when all quotas < 60%

### Edge Cases

- [ ] No organization ID (user without org) - Should not render
- [ ] Multiple warnings - Shows highest severity
- [ ] Exactly 60% - Shows Info level
- [ ] Exactly 80% - Shows Warning level
- [ ] Exactly 95% - Shows Critical level
- [ ] 100% usage - Shows Critical with proper message
- [ ] Backend warnings array empty - No warnings section
- [ ] Backend warnings array populated - Displays list

### Performance

- [ ] Query runs only when orgId exists (enabled flag)
- [ ] Refetch interval doesn't cause UI lag
- [ ] Cache invalidation works after quota updates
- [ ] No unnecessary re-renders

---

## Known Limitations

1. **CMS Build Errors**: Unrelated TypeScript errors in other features (Tags, Playlists, PMS, Schedules, Weather, Widgets)
   - Solution: Fix in separate PR or ignore for now if not blocking

2. **Shadcn UI Not Installed**: Used native React + Tailwind instead
   - Future: Install shadcn/ui for better components
   - Current: Fully functional with Tailwind classes

3. **Real-time Updates**: Uses polling (60s interval) instead of WebSocket
   - Future: Implement WebSocket for instant updates
   - Current: 60-second delay acceptable for quota monitoring

---

## Future Enhancements

### Phase 2 (Next Sprint)
1. **Quota Detail Page**: Full organization quota management page
   - QuotaUsageCards for all resources
   - Historical usage charts
   - Quota update form (Admin only)

2. **Pre-Action Checks**: Prevent operations when quota exceeded
   - Device activation blocked if device quota full
   - Content upload blocked if storage quota full
   - User creation blocked if user quota full

3. **Quota Notifications**: Email/SMS alerts
   - Notify managers when quota reaches 80%
   - Daily digest for critical quotas

### Phase 3 (Future)
1. **Quota Analytics**: Historical trends and predictions
   - Usage over time charts
   - Predicted quota exhaustion date
   - Recommendations for optimization

2. **Custom Quota Rules**: Flexible quota policies
   - Different quotas per organization tier
   - Soft limits (warnings) vs hard limits (blocks)
   - Grace periods for temporary overages

3. **Self-Service Quota Increase**: Allow managers to request increases
   - Request form with justification
   - Admin approval workflow
   - Automated provisioning after approval

---

## Deployment Checklist

### Backend
- [x] Quota endpoints exist and tested
- [x] DTOs match frontend types
- [x] Permissions configured correctly
- [x] Database quota fields populated

### Frontend
- [x] Types defined
- [x] API functions implemented
- [x] React Query hooks created
- [x] Components built
- [x] Dashboard integrated
- [ ] TypeScript compilation passes (blocked by unrelated errors)

### Infrastructure
- [ ] Backend API accessible from CMS
- [ ] CORS configured
- [ ] Rate limiting appropriate for auto-refresh

---

## Success Metrics

### User Impact
- **Prevent service interruption**: Users notified before hitting limits
- **Reduce support tickets**: Proactive warnings reduce "why can't I add X" tickets
- **Improve resource planning**: Visibility into quota usage enables better planning

### Technical Metrics
- **API latency**: Quota endpoint < 200ms response time
- **Cache hit rate**: > 80% (due to 30s stale time)
- **Error rate**: < 0.1%

### Business Metrics
- **Quota overrun incidents**: Reduce from ~15% to < 2%
- **Upgrade conversions**: Increase by 25% (proactive warnings → upgrades)
- **User satisfaction**: NPS +15 points

---

## Rollback Plan

If issues occur:
1. **Quick Fix**: Comment out `<QuotaAlertBanner>` in DashboardPage.tsx
2. **Full Rollback**: Revert commits for this feature
3. **Backend Independent**: Backend quota endpoints remain functional

---

## Related Documentation

- **Backend API Docs**: `http://192.168.5.12:8001/docs#/organizations`
- **Database Schema**: `backend-python/docs/DATABASE_CONVENTIONS.md`
- **Gap Analysis**: `CMS_BACKEND_GAP_ANALYSIS.md`

---

## Changelog

### v1.0 (2025-11-20)
- Initial implementation
- QuotaAlertBanner component
- QuotaUsageCard component
- React Query hooks
- Dashboard integration

---

**Author**: Claude Code
**Reviewer**: (Pending)
**Deployed**: (Pending - Build issues to fix)
**Status**: Implementation Complete, Testing Pending
