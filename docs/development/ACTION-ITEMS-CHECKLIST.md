# 📋 Action Items Checklist

**Created:** 2025-11-12
**Status:** In Progress
**Overall Progress:** 0/45 tasks (0%)

---

## 🔴 Priority 1: URGENT (Week 1)

### Day 1: Critical API Path Fixes

- [ ] **FIX-001:** Fix Widgets API path
  - File: `cms-vite/src/features/widgets/api/widgetApi.ts`
  - Change: `'/widgets'` → `'/api/v1/widgets'`
  - Estimated: 5 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **FIX-002:** Fix Templates API path
  - File: `cms-vite/src/features/templates/api/templateApi.ts`
  - Change: `'/templates'` → `'/api/v1/templates'`
  - Estimated: 5 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **TEST-001:** Test Widgets CRUD operations
  - Verify create, read, update, delete
  - Check browser DevTools network tab
  - Estimated: 15 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **TEST-002:** Test Templates CRUD operations
  - Verify create, read, update, delete
  - Test template rendering
  - Estimated: 15 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

**Day 1 Progress:** 0/4 tasks (0%)

---

### Day 2-3: Standardize API Client

- [ ] **REFACTOR-001:** Convert Widgets to use apiClient
  - Replace `api` with `apiClient`
  - Use `API_ENDPOINTS` constants
  - Add proper error handling
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **REFACTOR-002:** Convert Schedules to use apiClient
  - Replace raw `axios` with `apiClient`
  - Use `API_ENDPOINTS` constants
  - Add proper error handling
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **REFACTOR-003:** Convert Translations to use apiClient
  - Replace raw `axios` with `apiClient`
  - Use `API_ENDPOINTS` constants
  - Add proper error handling
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **TEST-003:** Test all refactored API calls
  - Verify auth token injection works
  - Verify org ID header works
  - Test error handling
  - Estimated: 30 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

**Day 2-3 Progress:** 0/4 tasks (0%)

---

### Day 4-5: Backend Verification

- [ ] **VERIFY-001:** Document all backend endpoints
  - Parse all `routes.py` files
  - Create master endpoint list
  - Include method, path, description
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **VERIFY-002:** Cross-check CMS API calls
  - Compare CMS calls vs backend endpoints
  - Identify mismatches
  - Document findings
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **VERIFY-003:** Create endpoint coverage report
  - List used endpoints
  - List unused endpoints
  - Calculate coverage percentage
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

**Day 4-5 Progress:** 0/3 tasks (0%)

**Week 1 Total Progress:** 0/11 tasks (0%)

---

## 🔴 Priority 2: HIGH (Week 2-3)

### Week 2: WebSocket Implementation

- [ ] **WS-001:** Create WebSocketClient class
  - File: `cms-vite/src/lib/websocket/WebSocketClient.ts`
  - Implement connection, reconnection, error handling
  - Add message queue for offline messages
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **WS-002:** Create useWebSocket React hook
  - File: `cms-vite/src/lib/websocket/useWebSocket.ts`
  - Implement connection state
  - Implement message handlers
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **WS-003:** Create WebSocketProvider context
  - File: `cms-vite/src/lib/websocket/WebSocketProvider.tsx`
  - Wrap app with provider
  - Provide WS instance to all components
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **WS-004:** Connect to admin WebSocket endpoint
  - Connect to `/api/ws/admin`
  - Send auth token
  - Handle connection events
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **WS-005:** Handle device status messages
  - Listen for `device:status` events
  - Update device list in real-time
  - Show online/offline indicators
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **WS-006:** Handle playback update messages
  - Listen for `playback:update` events
  - Update analytics dashboard
  - Show current playing content
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **WS-007:** Handle command response messages
  - Listen for `command:response` events
  - Show instant feedback to user
  - Update command status
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **WS-008:** Add real-time UI indicators
  - Green/red dots for device status
  - Live playback preview
  - Command execution feedback
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **TEST-004:** Test WebSocket functionality
  - Test connection/disconnection
  - Test reconnection after network loss
  - Test message handling
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

**Week 2 Progress:** 0/9 tasks (0%)

---

### Week 3: RBAC Module

- [ ] **RBAC-001:** Create RolesPage
  - File: `cms-vite/src/features/rbac/pages/RolesPage.tsx`
  - List all roles
  - Add create role button
  - Add edit/delete actions
  - Estimated: 3 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **RBAC-002:** Create RoleForm component
  - File: `cms-vite/src/features/rbac/components/RoleForm.tsx`
  - Role name input
  - Description textarea
  - System role checkbox
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **RBAC-003:** Create PermissionMatrix component
  - File: `cms-vite/src/features/rbac/components/PermissionMatrix.tsx`
  - Show all permissions in grid
  - Checkboxes for each permission
  - Save/cancel actions
  - Estimated: 3 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **RBAC-004:** Create rbacApi service
  - File: `cms-vite/src/features/rbac/api/rbacApi.ts`
  - Implement all RBAC endpoints
  - Use apiClient
  - Add error handling
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **RBAC-005:** Create useRoles hook
  - File: `cms-vite/src/features/rbac/hooks/useRoles.ts`
  - Fetch roles with TanStack Query
  - Handle loading/error states
  - Implement mutations
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **RBAC-006:** Create usePermissions hook
  - File: `cms-vite/src/features/rbac/hooks/usePermissions.ts`
  - Fetch permissions
  - Check user permissions
  - Cache permission data
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **RBAC-007:** Add RBAC routes to app
  - File: `cms-vite/src/routes/index.tsx`
  - Add `/roles` route
  - Add `/permissions` route
  - Protect with admin permission
  - Estimated: 30 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **RBAC-008:** Add RBAC menu items
  - File: `cms-vite/src/shared/components/layout/Sidebar.tsx`
  - Add "Roles" menu item
  - Add "Permissions" menu item
  - Show only to admins
  - Estimated: 30 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **RBAC-009:** Implement permission checks in UI
  - Hide/disable features based on permissions
  - Add `useHasPermission` hook
  - Apply to buttons, menu items
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **TEST-005:** Test RBAC functionality
  - Test role CRUD
  - Test permission assignment
  - Test UI permission checks
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

**Week 3 Progress:** 0/10 tasks (0%)

**Week 2-3 Total Progress:** 0/19 tasks (0%)

---

## 🟡 Priority 3: MEDIUM (Week 4-6)

### Week 4: Shared UI System

- [ ] **UI-001:** Create shared-ui-system package
  - Directory: `packages/shared-ui-system/`
  - Setup package.json
  - Setup TypeScript config
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **UI-002:** Extract color tokens
  - File: `packages/shared-ui-system/tokens/colors.ts`
  - Define brand colors
  - Define semantic colors
  - Define neutral palette
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **UI-003:** Extract typography tokens
  - File: `packages/shared-ui-system/tokens/typography.ts`
  - Define font families
  - Define font sizes
  - Define line heights
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **UI-004:** Extract spacing tokens
  - File: `packages/shared-ui-system/tokens/spacing.ts`
  - Define spacing scale
  - Define border radius
  - Define shadows
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **UI-005:** Create Tailwind preset
  - File: `packages/shared-ui-system/tailwind-preset.ts`
  - Import all tokens
  - Configure theme
  - Export preset
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **UI-006:** Apply preset to CMS
  - File: `cms-vite/tailwind.config.ts`
  - Import shared preset
  - Remove duplicate tokens
  - Test build
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **UI-007:** Apply preset to Player
  - File: `player-vite/tailwind.config.js`
  - Import shared preset
  - Remove hardcoded colors
  - Test build
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **TEST-006:** Visual regression testing
  - Compare screenshots before/after
  - Verify colors match
  - Verify spacing consistent
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

**Week 4 Progress:** 0/8 tasks (0%)

---

### Week 5: Session Management

- [ ] **SESSION-001:** Create SessionsPage
  - File: `cms-vite/src/features/sessions/pages/SessionsPage.tsx`
  - List active sessions
  - Show session details
  - Add revoke actions
  - Estimated: 3 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **SESSION-002:** Create SessionCard component
  - File: `cms-vite/src/features/sessions/components/SessionCard.tsx`
  - Show device info
  - Show location (IP, city)
  - Show last active time
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **SESSION-003:** Create sessionApi service
  - File: `cms-vite/src/features/sessions/api/sessionApi.ts`
  - Implement all session endpoints
  - Add error handling
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **SESSION-004:** Add "Revoke All" feature
  - Add button to revoke all sessions
  - Show confirmation modal
  - Logout user after revoke
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **SESSION-005:** Add to user menu
  - Add "Active Sessions" menu item
  - Show session count badge
  - Link to SessionsPage
  - Estimated: 30 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **TEST-007:** Test session management
  - Test session list
  - Test revoke single session
  - Test revoke all sessions
  - Estimated: 30 minutes
  - Assignee: ___________
  - Status: ⬜ Not Started

**Week 5 Progress:** 0/6 tasks (0%)

---

### Week 6: PMS Configuration

- [ ] **PMS-001:** Create PMSConfigPage
  - File: `cms-vite/src/features/pms/pages/PMSConfigPage.tsx`
  - Provider selection dropdown
  - Connection form
  - Test connection button
  - Estimated: 3 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **PMS-002:** Create PMSConnectionForm
  - File: `cms-vite/src/features/pms/components/PMSConnectionForm.tsx`
  - Host, port, credentials fields
  - Validation with Zod
  - Save/cancel actions
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **PMS-003:** Create RoomMappingTable
  - File: `cms-vite/src/features/pms/components/RoomMappingTable.tsx`
  - List PMS rooms
  - Map to devices
  - Bulk mapping actions
  - Estimated: 3 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **PMS-004:** Create pmsApi service
  - File: `cms-vite/src/features/pms/api/pmsApi.ts`
  - Implement all PMS endpoints
  - Add error handling
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **PMS-005:** Add PMS sync status dashboard
  - Show last sync time
  - Show sync status (success/error)
  - Show guest count, room count
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **TEST-008:** Test PMS integration
  - Test connection
  - Test room mapping
  - Test sync trigger
  - Estimated: 1 hour
  - Assignee: ___________
  - Status: ⬜ Not Started

**Week 6 Progress:** 0/6 tasks (0%)

**Week 4-6 Total Progress:** 0/20 tasks (0%)

---

## 🟢 Priority 4: LOW (Month 2)

### Enhancement: Schedule UI

- [ ] **SCHEDULE-001:** Add FullCalendar integration
  - Install `@fullcalendar/react`
  - Create ScheduleCalendar component
  - Render schedules on calendar
  - Estimated: 4 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **SCHEDULE-002:** Add drag-and-drop scheduling
  - Enable dragging events on calendar
  - Update backend on drop
  - Show conflict warnings
  - Estimated: 4 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **SCHEDULE-003:** Add recurrence pattern builder
  - Visual recurrence selector
  - Preview recurrence dates
  - Custom recurrence rules
  - Estimated: 3 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

**Schedule Enhancement Progress:** 0/3 tasks (0%)

---

### Enhancement: Device Commands

- [ ] **COMMAND-001:** Create CommandHistory component
  - Show all past commands
  - Filter by device, type, status
  - Sortable table
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **COMMAND-002:** Create BulkCommandModal
  - Select multiple devices
  - Choose command type
  - Send to all selected
  - Estimated: 2 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

- [ ] **COMMAND-003:** Create CommandTemplates feature
  - Save command sets
  - Quick apply templates
  - Share templates
  - Estimated: 3 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

**Command Enhancement Progress:** 0/3 tasks (0%)

---

### Enhancement: Weather Configuration

- [ ] **WEATHER-001:** Create WeatherConfigPage
  - Location management
  - API key configuration
  - Weather preview
  - Estimated: 3 hours
  - Assignee: ___________
  - Status: ⬜ Not Started

**Weather Enhancement Progress:** 0/1 tasks (0%)

---

## 📊 Progress Summary

### By Priority

| Priority | Total Tasks | Completed | In Progress | Not Started | Percentage |
|----------|-------------|-----------|-------------|-------------|------------|
| 🔴 P1 (Week 1) | 11 | 0 | 0 | 11 | 0% |
| 🔴 P2 (Week 2-3) | 19 | 0 | 0 | 19 | 0% |
| 🟡 P3 (Week 4-6) | 20 | 0 | 0 | 20 | 0% |
| 🟢 P4 (Month 2) | 7 | 0 | 0 | 7 | 0% |
| **TOTAL** | **57** | **0** | **0** | **57** | **0%** |

### By Category

| Category | Tasks | Status |
|----------|-------|--------|
| 🐛 Bug Fixes | 2 | 0% |
| 🔧 Refactoring | 3 | 0% |
| ✅ Testing | 8 | 0% |
| 🔌 WebSocket | 9 | 0% |
| 🔐 RBAC | 10 | 0% |
| 🎨 UI System | 8 | 0% |
| 👤 Sessions | 6 | 0% |
| 🏨 PMS | 6 | 0% |
| 📅 Schedule | 3 | 0% |
| 💻 Commands | 3 | 0% |
| 🌤️ Weather | 1 | 0% |

---

## 🎯 Quick Start Guide

### For Week 1 (Day 1)

1. Open `cms-vite/src/features/widgets/api/widgetApi.ts`
2. Change line with `const BASE_URL = '/widgets'`
3. Replace with `const BASE_URL = '/api/v1/widgets'`
4. Save file
5. Repeat for templates
6. Test in browser

**Estimated time:** 30 minutes total

### For Week 2 (WebSocket)

1. Create directory `cms-vite/src/lib/websocket/`
2. Copy WebSocket implementation from player
3. Adapt for CMS admin endpoint
4. Add to React context
5. Test connection

**Estimated time:** 1-2 days total

---

## 📝 Notes

- Check off tasks as you complete them: `- [ ]` → `- [x]`
- Update assignee names
- Update status: ⬜ Not Started → 🔄 In Progress → ✅ Completed
- Add notes for any blockers
- Review progress weekly
- Adjust estimates based on actual time

---

**Last Updated:** 2025-11-12
**Next Review:** 2025-11-13
