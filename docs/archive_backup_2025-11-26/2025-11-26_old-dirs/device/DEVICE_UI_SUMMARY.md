# Device Management UI - Quick Summary

## All Device UI Screens (8 screens + 1 page)

### Main Screens
1. **Devices List Page** - Device hub with status filtering, search, sort
2. **Device Detail Modal** - Comprehensive device management dashboard
3. **Device Edit Modal** - Settings, display config, device replacement
4. **Device Logs Modal** - Real-time WebSocket log streaming + filtering
5. **Pending Device Card** - Quick approval interface (in-page component)
6. **Speed History Modal** - Speed test metrics table with quality analysis
7. **Content Assignment Modal** - Two-column assign/unassign interface
8. **Device Preview Page** - Full-screen content playback preview

## Key Numbers & Metrics

| Metric | Value | Purpose |
|--------|-------|---------|
| Auto-refresh interval | 5 seconds | Devices list updates |
| Online timeout | 60 seconds | Heartbeat based |
| Speed test delay | 15-20 seconds | Result appearance |
| Speed history refresh | 60 seconds | Device Detail modal |
| Device heartbeat | 30 seconds | Status signal |
| Speed history limit | 10 (chart), 20 (table) | Data display |
| Activation code length | 6 digits | User-friendly code |
| Log levels | 4 (info, warn, error, log) | Filtering options |

## Core User Workflows

1. **Device Activation** (Pending → Active)
   - Admin approves pending device
   - Device moves to active table
   - Device status broadcasts to viewer

2. **Content Assignment** (Multiple methods)
   - Direct assignment (priority-based)
   - Via tags (bulk, inherited)
   - Via playlists (with priority)

3. **Device Monitoring**
   - View online/offline status
   - Access real-time logs (WebSocket)
   - Run speed tests manually
   - View speed history

4. **Device Settings**
   - Modify name, status, rotation, volume
   - Release device (reset with new code)
   - Replace with pending viewer

5. **Device Deletion**
   - Confirmation required
   - Removes assignments
   - Cleans up records

## Real-Time Features

- **Status updates:** 5-second auto-refresh
- **Online indicator:** Green/Red circle (60s timeout)
- **Logs:** WebSocket streaming with fallback
- **Speed test:** 15-20s result appearance
- **Content sync:** Immediate propagation

## Component Files

```
web-admin-old/src/components/devices/
├── DeviceTableRow.jsx          (memoized row component)
├── PendingDeviceCard.jsx       (memoized card component)
└── modals/
    ├── DeviceDetailModal.jsx   (comprehensive dashboard)
    ├── DeviceEditModal.jsx     (settings & display)
    ├── DeviceLogsModal.jsx     (real-time logs)
    ├── DeviceInfoModal.jsx     (information display)
    ├── SpeedHistoryModal.jsx   (speed test history)
    ├── AssignContentModal.jsx  (content assignment)
    └── TVRegisterModal.jsx     (TV registration form)

web-admin-old/src/pages/
├── Devices.jsx                 (main list page)
└── DevicePreview.jsx           (full-screen preview)
```

## Modal Sizes
- TV Register: lg (512px)
- Device Info: 2xl (672px)
- Device Detail: 2xl (672px)
- Device Edit: 4xl (896px)
- Speed History: 4xl (896px)
- Logs: 4xl (896px)
- Content Assign: full (100% screen)

## Data Displayed per Screen

### Devices List (Table Columns)
- ID, Device name, Platform, IP, Code, Status, Last Seen, Actions

### Device Detail Modal (Sections)
- Online status indicator
- Quick action buttons (5)
- Tags section
- Playlists section
- Content section (direct + inherited)
- Device info block
- Speed history chart + stats

### Device Edit Modal (Sections)
- Device info (editable + read-only)
- Replace pending device (browser only)
- Display settings (rotation, audio)
- Display info (read-only specs)

### Logs Modal (Elements)
- Connection status indicator
- Filter bar (5 levels)
- Log count badges
- Terminal view (dark bg)
- Export + Clear buttons

### Speed History Modal (Table)
- Tested date/time
- Download/Upload speeds
- Quality badge
- Latency/Jitter/Loss
- DNS server

## Error Handling & Feedback

**Toast notifications** (3-5 seconds):
- Success: Green toast, bottom-right
- Error: Red toast, bottom-right
- With specific error messages from API

**Confirmation dialogs**:
- Device deletion
- Device release
- Log clearing
- Multi-line with device details

**Validation**:
- IPv4 format checking (TV register)
- Required field validation
- Status dropdown constraints

## Integration Points

- **With Content module:** Direct assignment, tag inheritance, preview
- **With Tags module:** Color-coded, bulk assignment, content display
- **With Playlists module:** Priority-based, assignment tracking
- **With Dashboard:** Stats widgets, filters, real-time counts

## Performance Features

- Component memoization (DeviceTableRow, PendingDeviceCard)
- TanStack Query caching & auto-refresh
- Sticky header/footer (modals)
- Virtual scrolling (if large lists)
- WebSocket for logs (no polling)

## Browser Support

- Modern browsers (React 18 compatible)
- Dark mode full support
- Responsive (mobile, tablet, desktop)
- Keyboard navigation (Tab, Enter, Escape)

## State Management

- **Server state:** TanStack Query (devices, content, tags, playlists)
- **Auth state:** Zustand (global)
- **UI state:** Local useState (modals, selections, forms)
- **Cache invalidation:** On mutations (create, update, delete)

## Recommended Patterns for New Implementation

✓ Three-tier device categorization (Pending, Active, Inactive)
✓ Rich device detail modal with management sections
✓ Real-time status indicators (heartbeat-based)
✓ WebSocket for logs, REST for other data
✓ Content assignment flexibility (direct, playlist, tag)
✓ Speed test integration for network monitoring
✓ Device preview before content goes live
✓ Responsive modals with fixed header/footer
✓ Toast notifications for all operations
✓ Confirmation dialogs for destructive actions

