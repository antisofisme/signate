# CMS Frontend Feature Implementation Checklist

**Quick reference for tracking implementation progress**

---

## 🔴 P0 - Critical Features (Week 1-2)

### 1. Device Groups Management UI
**Backend**: ✅ Complete (11 endpoints)
**Frontend**: 🔴 30% (API only, no UI)
**Effort**: 5-7 days

#### Components to Create
- [ ] `GroupTreeView.tsx` - Hierarchical tree display
- [ ] `GroupForm.tsx` - Create/edit modal
- [ ] `GroupDeviceList.tsx` - Device assignment view
- [ ] `GroupStatsCard.tsx` - Statistics display
- [ ] `GroupTreeNode.tsx` - Individual tree node (recursive)

#### Hooks to Create
- [ ] `useDeviceGroups.ts` - Fetch & mutate groups
- [ ] `useGroupDevices.ts` - Device assignment operations
- [ ] `useGroupStats.ts` - Statistics fetching

#### Pages to Update
- [ ] `DeviceGroupsPage.tsx` - Main page (currently empty)

#### Integration Points
- [ ] Add "Assign to Group" in device list
- [ ] Show group in device detail modal
- [ ] Add group filter to device list

#### API Endpoints to Integrate
```typescript
✅ GET    /devices/groups              // List groups
✅ GET    /devices/groups/roots        // Root groups
✅ GET    /devices/groups/{id}         // Get single
✅ GET    /devices/groups/{id}/children // Get children
✅ GET    /devices/groups/{id}/devices  // Get devices
✅ GET    /devices/groups/{id}/stats    // Get stats
✅ POST   /devices/groups              // Create
✅ PUT    /devices/groups/{id}         // Update
✅ DELETE /devices/groups/{id}         // Delete
✅ POST   /devices/groups/{id}/devices // Add device
✅ DELETE /devices/groups/{id}/devices/{did} // Remove device
```

#### Testing Checklist
- [ ] Can create root group
- [ ] Can create child group
- [ ] Can assign device to group
- [ ] Can remove device from group
- [ ] Can view group statistics
- [ ] Can delete empty group
- [ ] Cannot delete group with children (validation)
- [ ] Recursive device listing works

---

### 2. Organization Quota Management UI
**Backend**: ✅ Complete (8 endpoints)
**Frontend**: 🟡 60% (Display only, no management)
**Effort**: 3-5 days

#### Components to Create
- [ ] `QuotaSettingsForm.tsx` - Admin quota management
- [ ] `QuotaHistoryChart.tsx` - Usage over time
- [ ] `QuotaCheckWarning.tsx` - Pre-operation warning

#### Components to Enhance
- [ ] `QuotaUsageCard.tsx` - Add edit button (admin)
- [ ] `QuotaAlertBanner.tsx` - Make dismissible

#### Hooks to Create
- [ ] `useQuotaManagement.ts` - Admin quota operations
- [ ] `useQuotaCheck.ts` - Pre-operation validation

#### Integration Points
- [ ] Add quota check before device registration
- [ ] Add quota check before user creation
- [ ] Add quota check before content upload
- [ ] Show quota status in dashboard
- [ ] Add quota tab to settings page

#### API Endpoints to Integrate
```typescript
✅ GET /organizations/{id}/quota              // Get status
✅ PUT /organizations/{id}/quota              // Update limits (admin)
✅ GET /organizations/{id}/quota/check/device  // Check before device add
✅ GET /organizations/{id}/quota/check/user    // Check before user add
✅ GET /organizations/{id}/quota/check/content // Check before content upload
```

#### Quota Check Pattern
```typescript
// Before creating device
const quotaCheck = await checkDeviceQuota(orgId);
if (!quotaCheck.allowed) {
  toast.error(quotaCheck.message);
  return; // Block operation
}
// Proceed with creation
```

#### Testing Checklist
- [ ] Admin can update quota limits
- [ ] User can view quota usage
- [ ] Device creation blocked when at limit
- [ ] User creation blocked when at limit
- [ ] Content upload blocked when at limit
- [ ] Warning shown when near limit (>80%)
- [ ] Quota usage updates after operations

---

### 3. Connection Logs Viewer
**Backend**: ✅ Complete (Hybrid storage)
**Frontend**: 🔴 0% (No UI)
**Effort**: 2-3 days

#### Components to Create
- [ ] `ConnectionLogsTable.tsx` - Log list with filters
- [ ] `ConnectionTimeline.tsx` - Visual timeline
- [ ] `ConnectionLogFilters.tsx` - Filter controls
- [ ] `ConnectionEventBadge.tsx` - Event type badge

#### API Integration to Create
- [ ] `connectionLogsApi.ts` - API client methods

#### Hooks to Create
- [ ] `useConnectionLogs.ts` - Fetch & filter logs

#### Integration Points
- [ ] Add "Connection Logs" tab to DeviceDetailModal
- [ ] Add connection status indicator in device list
- [ ] Show recent connection events in dashboard

#### API Endpoint to Integrate
```typescript
✅ GET /devices/{id}/connection-logs?start_date=&end_date=&event_type=
```

#### Log Event Types
- `connected` - Device connected
- `disconnected` - Device disconnected
- `heartbeat_missed` - Heartbeat timeout
- `reconnected` - Device reconnected after issue

#### Testing Checklist
- [ ] Can view all connection logs
- [ ] Can filter by date range
- [ ] Can filter by event type
- [ ] Timeline shows correct order
- [ ] Real-time updates work (WebSocket)
- [ ] Export to CSV works
- [ ] Pagination works for large log sets

---

## 🟡 P1 - Important Enhancements (Week 3-4)

### 4. Enhanced Device Assignments
**Backend**: ✅ Complete
**Frontend**: 🟡 50% (Basic modals exist)
**Effort**: 3-4 days

#### Enhancements Needed
- [ ] Bulk device selection in modals
- [ ] Assignment history table
- [ ] Expiry date picker for content assignments
- [ ] Priority slider for content
- [ ] Schedule builder for assignments
- [ ] "Copy assignments from device" feature

#### Components to Enhance
- [ ] `TagAssignmentModal.tsx` - Add bulk mode
- [ ] `ContentAssignmentModal.tsx` - Add expiry/priority
- [ ] `PlaylistAssignmentModal.tsx` - Add schedule

#### Components to Create
- [ ] `AssignmentHistoryTable.tsx` - Show assignment changes
- [ ] `BulkAssignmentSelector.tsx` - Multi-device picker

#### Testing Checklist
- [ ] Can assign to multiple devices at once
- [ ] Can set content expiry date
- [ ] Can set content priority
- [ ] Can view assignment history
- [ ] Can copy assignments between devices

---

### 5. Advanced Schedule Features
**Backend**: ✅ Complete (9 endpoints)
**Frontend**: 🟡 70% (Basic UI exists)
**Effort**: 3-4 days

#### Components to Create
- [ ] `ScheduleConflictDetector.tsx` - Show conflicts
- [ ] `ScheduleOccurrencePreview.tsx` - Show next runs
- [ ] `ActiveScheduleBadge.tsx` - "Active now" indicator

#### Components to Enhance
- [ ] `ScheduleForm.tsx` - Add conflict check
- [ ] `FullCalendarView.tsx` - Show conflict overlays

#### API Endpoints to Integrate
```typescript
✅ POST /schedules/check-conflicts     // Conflict detection
✅ GET  /schedules/occurrences         // Calculate occurrences
✅ POST /schedules/{id}/calculate-next // Next run time
✅ GET  /schedules/active/now          // Currently active
✅ POST /schedules/refresh             // Refresh cache
```

#### Testing Checklist
- [ ] Conflict detection shows overlaps
- [ ] Occurrence preview shows next 5 runs
- [ ] Active schedule badge shows when running
- [ ] Cannot create conflicting high-priority schedules
- [ ] Calendar shows visual conflict indicators

---

### 6. Organization Switching UX
**Backend**: ✅ Complete (Multi-tenancy)
**Frontend**: 🟡 60% (Basic switching exists)
**Effort**: 2-3 days

#### Components to Create
- [ ] `OrganizationSwitcher.tsx` - Dropdown in topbar
- [ ] `OrganizationContextIndicator.tsx` - Show current org
- [ ] `DefaultOrgSetting.tsx` - User preference

#### Components to Enhance
- [ ] `Topbar.tsx` - Add org switcher
- [ ] `PageHeader.tsx` - Show org context

#### State Management
- [ ] Add org preference to localStorage
- [ ] Add seamless switching (no page reload)
- [ ] Update query cache on org switch

#### Testing Checklist
- [ ] Can switch organization from dropdown
- [ ] Data updates without reload
- [ ] Preference persists across sessions
- [ ] Quota shows for selected org
- [ ] Context clear on all pages

---

## 🟢 P2 - Nice-to-Have (Sprint 3+)

### 7. HLS Video Integration
- [ ] HLS status badge on content cards
- [ ] Quality variant display
- [ ] HLS preview button
- [ ] Bandwidth requirements display

### 8. Advanced Analytics
- [ ] Custom report builder
- [ ] Scheduled reports
- [ ] Export to PDF/Excel
- [ ] Comparative analytics

### 9. Bulk Operations
- [ ] Bulk device commands UI
- [ ] Bulk schedule creation
- [ ] Bulk user invitations

### 10. Global Search
- [ ] Search across all entities
- [ ] Advanced filter builder
- [ ] Saved filter presets

### 11. Notifications
- [ ] Notification center
- [ ] Device offline alerts
- [ ] Quota threshold warnings

### 12. Dashboard Customization
- [ ] Widget layout customization
- [ ] Role-based dashboards
- [ ] Quick actions menu

---

## Progress Tracking

### Overall Feature Coverage
- **Current**: 78%
- **After P0**: 88%
- **After P1**: 95%
- **After P2**: 98%+

### Sprint Progress

**Sprint 1 (Week 1-2)** - P0 Features
- [ ] Device Groups: 0% → 100%
- [ ] Quota Management: 60% → 100%
- [ ] Connection Logs: 0% → 100%

**Sprint 2 (Week 3-4)** - P1 Features
- [ ] Device Assignments: 50% → 100%
- [ ] Schedule Features: 70% → 100%
- [ ] Org Switching: 60% → 100%

---

## Definition of Done

### Feature Complete When:
- ✅ All components implemented
- ✅ All API endpoints integrated
- ✅ Unit tests written
- ✅ E2E tests passing
- ✅ No TypeScript errors
- ✅ Code reviewed
- ✅ Documentation updated
- ✅ Manual testing completed

### Code Quality:
- ✅ Follows existing patterns
- ✅ Proper error handling
- ✅ Loading states implemented
- ✅ Responsive design
- ✅ Accessibility considered

### User Experience:
- ✅ Clear feedback on actions
- ✅ Intuitive navigation
- ✅ Fast performance (< 2s)
- ✅ No breaking changes

---

## Quick Commands

### Development
```bash
# Start CMS dev server
cd cms-vite
npm run dev

# Run tests
npm run test

# Type check
npm run type-check

# Build
npm run build
```

### Testing
```bash
# Unit tests
npm run test:unit

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

---

**Last Updated**: 2025-01-20
**Next Review**: After Sprint 1 completion
