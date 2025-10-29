# API Interceptor Testing Guide

## Quick Testing Steps

### 1. Enable Debug Logging

Edit `/mnt/g/khoirul/signate/web-admin/.env`:
```env
VITE_DEBUG_API=true
```

Restart dev server:
```bash
npm run dev
```

### 2. Open Browser Console

Navigate to Web Admin: `http://localhost:3000`

Open DevTools (F12) → Console tab

### 3. Test Each Page

#### Dashboard (`/`)
**Expected Console Logs:**
```
[API] Unwrapping standardized response: {url: "/api/devices", success: true, ...}
[API] Unwrapping standardized response: {url: "/api/content", success: true, ...}
[API] Unwrapping standardized response: {url: "/api/tags", success: true, ...}
[API] Unwrapping standardized response: {url: "/api/playlists", success: true, ...}
```

**Visual Check:**
- [ ] Stats cards show correct numbers
- [ ] Device list displays
- [ ] Pending devices section works
- [ ] Activity timeline loads

#### Devices Page (`/devices`)
**Expected Console Logs:**
```
[API] Unwrapping standardized response: {url: "/api/devices", success: true, ...}
```

**Visual Check:**
- [ ] Device table populates
- [ ] Search works
- [ ] Filter by status works
- [ ] Click device → modal opens with details
- [ ] Speed test history loads

**Actions to Test:**
- [ ] Register new TV device
- [ ] Approve pending device
- [ ] Reject pending device
- [ ] Edit device details
- [ ] Delete device

#### Content Page (`/content`)
**Expected Console Logs:**
```
[API] Unwrapping standardized response: {url: "/api/content", success: true, ...}
```

**Visual Check:**
- [ ] Content grid displays
- [ ] Thumbnails load
- [ ] Upload button works

**Actions to Test:**
- [ ] Upload new content
- [ ] Edit content metadata
- [ ] Delete content
- [ ] Assign to device
- [ ] Unassign from device

#### Tags Page (`/tags`)
**Expected Console Logs:**
```
[API] Unwrapping standardized response: {url: "/api/tags", success: true, ...}
```

**Actions to Test:**
- [ ] Create new tag
- [ ] Edit tag
- [ ] Delete tag
- [ ] Assign tag to device

#### Playlists Page (`/playlists`)
**Expected Console Logs:**
```
[API] Unwrapping standardized response: {url: "/api/playlists", success: true, ...}
```

**Actions to Test:**
- [ ] Create playlist
- [ ] Add content to playlist
- [ ] Reorder content
- [ ] Assign to devices
- [ ] Delete playlist

#### Activities Page (`/activities`)
**Expected Console Logs:**
```
[API] Unwrapping standardized response: {url: "/api/activities", success: true, ...}
[API] Unwrapping standardized response: {url: "/api/activities/stats", success: true, ...}
```

**Visual Check:**
- [ ] Activity log table loads
- [ ] Stats cards show numbers
- [ ] Filters work
- [ ] Pagination works

#### Settings Page (`/settings`)

**System Tab:**
```
[API] Unwrapping standardized response: {url: "/api/settings/system/info", ...}
```

**Actions to Test:**
- [ ] View system info
- [ ] Download database backup (should see `[API] Blob response - skipping unwrap`)
- [ ] Clear cache

**Users Tab:**
```
[API] Unwrapping standardized response: {url: "/api/users", success: true, ...}
```

**Actions to Test:**
- [ ] List users
- [ ] Create user
- [ ] Edit user
- [ ] Delete user

**Firebird Integration Tab:**
```
[API] Unwrapping standardized response: {url: "/api/firebird/configs", ...}
```

**Actions to Test:**
- [ ] List configs
- [ ] Create config
- [ ] Test connection
- [ ] Delete config

### 4. Error Testing

#### Test 404 Error
1. Manually edit a device ID in URL to invalid ID
2. Open DevTools Console

**Expected:**
```
[API] Standardized error response: {
  url: "/api/devices/99999",
  code: "NOT_FOUND",
  message: "Device not found",
  ...
}
```

**Visual:**
- [ ] Toast shows "Device not found"

#### Test Validation Error
1. Try creating a tag with empty name
2. Check console

**Expected:**
```
[API] Standardized error response: {
  code: "VALIDATION_ERROR",
  message: "Tag name is required",
  field: "tag_name",
  ...
}
```

**Visual:**
- [ ] Error message displays
- [ ] Form field highlighted

#### Test 401 Unauthorized
1. Clear localStorage token: `localStorage.removeItem('token')`
2. Try any API action

**Expected:**
- [ ] Redirects to `/login`

### 5. Network Tab Verification

Open DevTools → Network tab

Filter: `Fetch/XHR`

**For each request, verify:**

1. **Request Headers:**
   - `Content-Type: application/json`
   - `Authorization: Bearer <token>` (if logged in)

2. **Response (Raw):**
   ```json
   {
     "success": true,
     "data": { ... },
     "meta": {
       "timestamp": "2025-10-27T...",
       "request_id": "...",
       "version": "1.0.0"
     }
   }
   ```

3. **Console Log Shows:**
   ```
   [API] Unwrapping standardized response: ...
   ```

4. **Component Receives:**
   - Check React DevTools Props
   - Should show unwrapped data

### 6. Performance Testing

#### Check Interceptor Overhead

1. Open DevTools → Performance tab
2. Start recording
3. Navigate to Dashboard
4. Stop recording
5. Find `Response Interceptor` calls
6. Verify execution time <1ms

#### Memory Leak Test

1. Navigate between pages 10 times
2. Open DevTools → Memory tab
3. Take heap snapshot
4. Check for retained objects
5. Verify no memory leaks from interceptor

### 7. Edge Cases

#### Empty Response
```javascript
// Backend returns: { success: true, data: [], meta: {...} }
// Component should receive: []
```

**Test:** Navigate to page with no data (empty playlists, no devices, etc.)

#### Null Data
```javascript
// Backend returns: { success: true, data: null, meta: {...} }
// Component should receive: null
```

**Test:** Request non-existent resource (returns null instead of error)

#### Nested Data
```javascript
// Backend returns:
{
  success: true,
  data: {
    devices: [...],
    total: 10,
    page: 1,
    nested: {
      more: "data"
    }
  },
  meta: {...}
}

// Component should receive full nested structure
```

**Test:** Paginated endpoints (devices, activities, etc.)

#### File Download (Blob)
```javascript
// Should NOT unwrap blob responses
// responseType: 'blob' should pass through unchanged
```

**Test:**
1. Go to Settings → System
2. Click "Backup Database"
3. Check console: `[API] Blob response - skipping unwrap`
4. Verify file downloads correctly

### 8. Concurrent Requests

**Test:** Multiple parallel API calls

1. Open Dashboard (loads 4+ endpoints simultaneously)
2. Check console - should see multiple unwrapping logs
3. Verify all data loads correctly
4. No race conditions or data corruption

### 9. Cleanup

After testing, disable debug logging:

```env
VITE_DEBUG_API=false
```

Restart dev server:
```bash
npm run dev
```

## Expected Results Summary

### Success Criteria
✅ All pages load without errors
✅ All CRUD operations work
✅ Error messages display correctly
✅ File downloads work (backups)
✅ Console shows unwrapping logs (when debug enabled)
✅ No console errors
✅ No memory leaks
✅ Performance impact <1ms per request

### If Tests Fail

#### Data shows as undefined
**Cause:** Interceptor not unwrapping correctly
**Fix:** Check backend response structure matches expected format

#### Errors not showing
**Cause:** Error transformation not working
**Fix:** Verify error response has `error.response.data.detail`

#### Blob downloads broken
**Cause:** Blob responses being unwrapped
**Fix:** Ensure `responseType: 'blob'` is set in API call

#### Console flooded with logs
**Cause:** Debug mode enabled in production
**Fix:** Set `VITE_DEBUG_API=false`

## Automated Testing (Future)

### Unit Tests for Interceptor

```javascript
// tests/api-interceptor.test.js
describe('API Response Interceptor', () => {
  it('unwraps standardized response', () => {
    const mockResponse = {
      data: {
        success: true,
        data: { id: 1, name: 'Test' },
        meta: { timestamp: '2025-10-27T10:30:00Z' }
      }
    }

    // Test unwrapping logic
    expect(unwrappedData).toEqual({ id: 1, name: 'Test' })
  })

  it('passes through legacy response', () => {
    const mockResponse = {
      data: { id: 1, name: 'Test' }
    }

    // Should not modify
    expect(result).toEqual(mockResponse)
  })

  it('transforms standardized error', () => {
    const mockError = {
      response: {
        data: {
          success: false,
          error: {
            code: 'NOT_FOUND',
            message: 'Not found'
          }
        }
      }
    }

    // Should transform
    expect(error.response.data.detail).toBe('Not found')
  })
})
```

### E2E Tests

```javascript
// e2e/api-integration.spec.js
test('Dashboard loads with unwrapped API responses', async ({ page }) => {
  await page.goto('/')

  // Check console for unwrapping logs
  page.on('console', msg => {
    if (msg.text().includes('[API] Unwrapping')) {
      console.log('✓ Unwrapping detected')
    }
  })

  // Verify data displays
  await expect(page.locator('.device-count')).toBeVisible()
})
```

## Monitoring in Production

### Add Sentry/Error Tracking

```javascript
// Log interceptor issues to error tracking
if (error.response?.data?.success === false) {
  Sentry.captureMessage('Standardized API Error', {
    extra: {
      code: error.response.data.error.code,
      requestId: error.response.meta.request_id
    }
  })
}
```

### Add Analytics

```javascript
// Track API performance
if (isStandardizedFormat) {
  analytics.track('API Response Unwrapped', {
    endpoint: response.config.url,
    duration: response.meta.timestamp
  })
}
```

## Support Contacts

**Frontend Issues:**
- Check `/mnt/g/khoirul/signate/web-admin/src/services/api.js`
- Review console logs with `VITE_DEBUG_API=true`

**Backend Issues:**
- Check `/mnt/g/khoirul/signate/backend/app/schemas/common.py`
- Verify response format matches schema

**Integration Issues:**
- Review API_INTEGRATION_FIX.md
- Check network tab in browser DevTools
- Verify request_id in logs for correlation
