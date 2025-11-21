# Device Logs Viewer - Testing Guide

## Quick Start

### 1. Start the Development Server
```bash
cd /mnt/g/khoirul/signate/cms-vite
npm run dev
```

### 2. Access the CMS
Open browser: `http://localhost:3000`
Login with admin credentials

### 3. Navigate to Device Logs
**Option A: From Device Table**
1. Go to Devices page
2. Find any active device
3. Click the "View Logs" button (Terminal icon)

**Option B: From Device Detail**
1. Go to Devices page
2. Click on a device row to open details
3. Click "View Logs" in Quick Actions section

## Manual Testing Checklist

### Basic Functionality
- [ ] **Open Logs Viewer**
  - From DeviceTable "View Logs" button
  - From DeviceDetailModal "View Logs" quick action
  - Modal appears with device name in header

- [ ] **View Console Logs**
  - Default tab shows "Console Logs"
  - Logs table displays with columns: Timestamp, Level, Message, Source, Actions
  - Logs are sorted by newest first
  - Empty state shows when no logs available

- [ ] **Close Modal**
  - Click X button in header
  - Click outside modal (on overlay)
  - Press ESC key
  - All methods close the modal

### Filtering
- [ ] **Log Level Filter**
  - Click log level dropdown
  - Select "All Logs" - shows all logs
  - Select "Error" - shows only error logs (red badge)
  - Select "Warn" - shows only warning logs (yellow badge)
  - Select "Info" - shows only info logs (cyan badge)
  - Select "Debug" - shows only debug logs (gray badge)
  - Select "Log" - shows only log logs (blue badge)
  - Filter persists when changing pages

- [ ] **Auto-refresh Toggle**
  - Toggle is ON by default
  - Checkbox is checked
  - When checked: Logs auto-refresh every 30 seconds
  - When unchecked: Auto-refresh stops
  - Toggle state persists during session

### Pagination
- [ ] **Navigate Pages**
  - Shows "Page 1 of X" indicator
  - Shows "Showing 1-50 of Z logs"
  - Click "Next" button - goes to page 2
  - Click "Previous" button - goes back to page 1
  - Previous disabled on page 1
  - Next disabled on last page
  - Page numbers update correctly

- [ ] **Page Size**
  - Each page shows up to 50 logs
  - Last page may have fewer logs
  - Total count is accurate

### Actions
- [ ] **Refresh Logs**
  - Click "Refresh" button
  - Button shows spinner while loading
  - Toast notification: "Logs refreshed"
  - Table updates with latest data
  - Button re-enables after load

- [ ] **Clear Logs**
  - Click "Clear Logs" button (red text)
  - Confirmation dialog appears: "Are you sure..."
  - Click Cancel - no action, modal stays
  - Click OK - logs are deleted
  - Toast notification: "Console logs cleared successfully"
  - Table shows empty state
  - Pagination resets to page 1

- [ ] **View Log Details**
  - Click "Details" button on any log row
  - Detail modal opens
  - Shows all log metadata:
    - Log ID
    - Device ID
    - Timestamp (formatted)
    - Level (badge)
    - Source (if available)
    - URL (if available)
    - User Agent (if available)
    - Full message (monospace)
    - Stack trace (if error, red background)

### Log Detail Modal
- [ ] **Display**
  - Modal opens centered
  - Header shows "Console Log Details"
  - Log level badge displayed
  - All fields formatted correctly
  - Monospace font for technical data

- [ ] **Copy to Clipboard**
  - Click "Copy" button
  - Button changes to "Copied!" with green checkmark
  - Returns to "Copy" after 2 seconds
  - Clipboard contains formatted log text
  - Paste in text editor to verify

- [ ] **Close Detail Modal**
  - Click "Close" button
  - Click X button
  - Press ESC key
  - Click outside modal
  - All methods return to logs viewer

### UI/UX
- [ ] **Log Level Colors**
  - Error: Red badge/icon
  - Warn: Yellow badge/icon
  - Info: Cyan badge/icon
  - Debug: Gray badge/icon
  - Log: Blue badge/icon

- [ ] **Icons**
  - Error: AlertCircle icon
  - Warn: AlertTriangle icon
  - Info: Info icon
  - Debug: Bug icon
  - Log: Terminal icon

- [ ] **Hover States**
  - Table rows highlight on hover
  - Buttons show hover effect
  - Truncated messages show full text in tooltip

- [ ] **Loading States**
  - Skeleton loaders show while loading
  - Refresh button shows spinner
  - No flash of content

- [ ] **Empty States**
  - "No Logs Found" when no logs
  - Different message when filtered
  - Terminal icon displayed
  - Helpful text

### Tabs
- [ ] **Console Logs Tab**
  - Active by default
  - Blue underline when active
  - Content displays correctly

- [ ] **Connection Logs Tab**
  - Shows "Coming Soon" badge
  - Disabled state
  - Click shows placeholder:
    - Network icon
    - "Connection Logs Coming Soon" title
    - Description text

### Responsive Design
- [ ] **Desktop (1920px)**
  - All columns visible
  - Filters in one row
  - No horizontal scroll

- [ ] **Tablet (768px)**
  - Layout adjusts
  - Filters may wrap
  - Table scrolls horizontally if needed

- [ ] **Mobile (375px)**
  - Modal fits screen
  - Filters stack vertically
  - Table scrolls horizontally
  - All features accessible

### Dark Mode
- [ ] **Toggle Dark Mode**
  - All components render correctly
  - Contrast is sufficient
  - Colors are readable
  - Borders visible

### Performance
- [ ] **Large Dataset**
  - Test with 500+ logs
  - Pagination works smoothly
  - No lag when scrolling
  - Filters apply quickly

- [ ] **Auto-refresh**
  - Doesn't interfere with user actions
  - No flashing/jumping
  - Current page maintained
  - Filter maintained

- [ ] **Memory**
  - No memory leaks
  - Modal cleanup on close
  - Query cache invalidation works

### Error Handling
- [ ] **API Errors**
  - Network error - shows toast error
  - 404 error - shows empty state
  - 500 error - shows error toast
  - Retry mechanism works

- [ ] **Invalid Data**
  - Missing fields handled gracefully
  - Null values show "N/A"
  - Malformed JSON doesn't crash

### Accessibility
- [ ] **Keyboard Navigation**
  - Tab through all controls
  - Enter to activate buttons
  - ESC to close modals
  - Arrow keys in dropdowns

- [ ] **Screen Reader**
  - ARIA labels present
  - Role attributes correct
  - Announcements on state change

- [ ] **Focus Management**
  - Focus trapped in modal
  - Focus returns on close
  - Visible focus indicators

## Automated Testing

### Unit Tests (Vitest)
```bash
npm run test
```

Test files to create:
- `src/features/devices/types/__tests__/logs.test.ts`
- `src/features/devices/api/__tests__/logsApi.test.ts`
- `src/features/devices/hooks/__tests__/useDeviceLogs.test.ts`
- `src/features/devices/components/__tests__/DeviceLogsViewer.test.tsx`

### Integration Tests
```bash
npm run test:integration
```

Test scenarios:
- Filter + Pagination combination
- Auto-refresh + Manual refresh
- Clear logs + Reload
- Multiple modal interactions

### E2E Tests (Playwright)
```bash
npx playwright test
```

Test files:
- `tests/e2e/device-logs-viewer.spec.ts`

## Test Data Setup

### Generate Test Logs
Use the player device to generate console logs:
1. Open player in browser
2. Open DevTools Console
3. Execute test commands:
```javascript
console.log('Test log message');
console.info('Test info message');
console.warn('Test warning message');
console.error('Test error message');
console.debug('Test debug message');
```

### Generate Error with Stack Trace
```javascript
try {
  throw new Error('Test error with stack trace');
} catch (e) {
  console.error(e);
}
```

### Send via API (if needed)
```bash
# Using curl to post a log
curl -X POST http://192.168.5.12:8001/api/v1/devices/{device_id}/logs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "log_level": "error",
    "message": "Test error message",
    "source": "test-script.js:42",
    "stack_trace": "Error: Test error\n    at testFunction (test-script.js:42:15)",
    "url": "http://localhost:3000/test"
  }'
```

## Known Issues / Limitations

### Current Limitations
- Connection Logs tab not yet functional (backend not implemented)
- No export functionality (CSV, JSON)
- No search/filter by text
- No date range filtering
- Maximum 500 logs per request (backend limit)

### Future Enhancements
- Real-time WebSocket streaming
- Virtual scrolling for large datasets
- Advanced search and filtering
- Log export
- Log analytics

## Debugging Tips

### Check Browser Console
Look for:
- `[LogsAPI]` prefixed logs - API calls
- React Query DevTools - cache state
- Network tab - API requests/responses

### Check React Query Cache
```javascript
// In browser console
window.queryClient.getQueryCache()
```

### Enable Verbose Logging
In `logsApi.ts`, all API calls are logged to console:
```javascript
console.log('[LogsAPI] Fetching device logs:', url);
console.log('[LogsAPI] Response:', response.data);
```

### Common Issues

**Issue: Auto-refresh not working**
- Check browser console for errors
- Verify `autoRefresh` state is true
- Check React Query DevTools for refetch interval

**Issue: Pagination stuck**
- Clear browser cache
- Check total count vs. page size
- Verify backend pagination logic

**Issue: Modal won't close**
- Check for JavaScript errors
- Verify ESC key listener
- Check z-index conflicts

**Issue: Logs not clearing**
- Check DELETE API response
- Verify cache invalidation
- Check backend permissions

## Success Criteria

All checklist items pass:
- ✅ All basic functionality works
- ✅ All filters work correctly
- ✅ Pagination works smoothly
- ✅ All actions complete successfully
- ✅ UI/UX is polished
- ✅ Responsive on all devices
- ✅ Dark mode works
- ✅ Accessibility requirements met
- ✅ Performance is acceptable
- ✅ Error handling is robust

## Support

For issues or questions:
1. Check browser console for errors
2. Check React Query DevTools
3. Check backend API logs
4. Review implementation documentation

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0
**Status:** Ready for Testing
