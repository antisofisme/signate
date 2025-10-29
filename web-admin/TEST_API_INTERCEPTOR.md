# Token Refresh Interceptor - Test Plan

## Implementation Summary

Automatic token refresh interceptor has been implemented in the web-admin application with the following features:

### Changes Made:
1. **api.js (lines 26-116)**: Complete token refresh logic with queue-based pattern
2. **Login.jsx (lines 23-26)**: Store both access_token and refresh_token on login
3. **Layout.jsx (lines 24-25)**: Clear both tokens on logout

### Key Features:
- **Automatic Token Refresh**: When 401 error occurs, automatically attempts to refresh token
- **Queue Pattern**: Handles concurrent requests during token refresh (prevents multiple refresh calls)
- **Retry Logic**: Automatically retries failed request with new token
- **Infinite Loop Prevention**: Uses `_retry` flag to prevent circular refresh attempts
- **Graceful Fallback**: Redirects to login only after refresh token expires

### Architecture:
```
401 Error → Check if refreshing
  ↓ No → Start refresh process
  ↓ Yes → Queue request
  ↓
Refresh Token → Success?
  ↓ Yes → Update tokens + Retry original request + Process queue
  ↓ No → Clear tokens + Redirect to login
```

---

## Test Plan

### Test 1: Normal Token Refresh Flow
**Objective**: Verify automatic token refresh works when access token expires

**Steps:**
1. Login to web-admin (admin/admin123)
2. Wait for access token to expire (default: 30 minutes, but can be shortened in backend config)
   - OR manually expire token: `localStorage.setItem('token', 'expired_token')`
3. Navigate to any page (e.g., Devices, Contents)
4. Observe browser Network tab (F12 → Network)

**Expected Result:**
- First request fails with 401
- `/api/auth/refresh` is called automatically
- Original request is retried with new token
- Page loads successfully without redirect to login
- No user interaction required

**Verification:**
```javascript
// Check tokens were updated in browser console
console.log(localStorage.getItem('token')); // Should be new token
console.log(localStorage.getItem('refresh_token')); // Should be new refresh token
```

---

### Test 2: Concurrent Requests During Refresh
**Objective**: Verify queue pattern prevents multiple refresh calls

**Steps:**
1. Login to web-admin
2. Manually expire token: `localStorage.setItem('token', 'expired_token')`
3. Trigger multiple API calls simultaneously:
   - Navigate to Dashboard (triggers multiple API calls for stats, devices, etc.)
4. Monitor Network tab

**Expected Result:**
- Only ONE `/api/auth/refresh` call is made
- All other 401 requests are queued
- After refresh succeeds, all queued requests are retried
- All requests complete successfully

**Verification:**
- Network tab shows only 1 refresh call despite multiple 401s
- Dashboard loads completely with all data

---

### Test 3: Refresh Token Expiration
**Objective**: Verify graceful fallback when refresh token expires

**Steps:**
1. Login to web-admin
2. Manually expire BOTH tokens:
   ```javascript
   localStorage.setItem('token', 'expired_token');
   localStorage.setItem('refresh_token', 'expired_refresh_token');
   ```
3. Navigate to any page

**Expected Result:**
- First request fails with 401
- Refresh attempt fails (refresh token invalid)
- Both tokens are cleared from localStorage
- User is redirected to /login
- Login page shows (no error, clean state)

**Verification:**
```javascript
// In browser console after redirect
console.log(localStorage.getItem('token')); // Should be null
console.log(localStorage.getItem('refresh_token')); // Should be null
```

---

### Test 4: Logout Cleanup
**Objective**: Verify logout clears both tokens

**Steps:**
1. Login to web-admin
2. Click logout button in navigation
3. Check localStorage

**Expected Result:**
- User redirected to /login
- Both `token` and `refresh_token` removed from localStorage

**Verification:**
```javascript
// In browser console after logout
console.log(localStorage.getItem('token')); // Should be null
console.log(localStorage.getItem('refresh_token')); // Should be null
```

---

## Manual Testing Shortcuts

### Expire Access Token Only:
```javascript
// In browser console
localStorage.setItem('token', 'expired_token');
// Then navigate to any page
```

### Expire Both Tokens:
```javascript
// In browser console
localStorage.setItem('token', 'expired_token');
localStorage.setItem('refresh_token', 'expired_refresh_token');
// Then navigate to any page
```

### Check Current Tokens:
```javascript
// In browser console
console.log({
  access_token: localStorage.getItem('token'),
  refresh_token: localStorage.getItem('refresh_token')
});
```

### Monitor Refresh Attempts:
```javascript
// Open Network tab (F12 → Network)
// Filter by "refresh" to see refresh calls
// Check request/response payload
```

---

## Edge Cases Handled

1. **No Refresh Token**: If refresh_token missing, immediately redirects to login
2. **Network Errors**: Refresh failure treated as expired token → redirect to login
3. **Concurrent Requests**: Queue pattern prevents race conditions
4. **Infinite Loops**: `_retry` flag prevents circular refresh attempts
5. **Non-401 Errors**: Other errors (404, 500, etc.) pass through normally

---

## Configuration

### Backend Token Lifetimes:
```python
# backend/app/core/config.py
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Access token lifetime
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7     # Refresh token lifetime
```

To test faster, temporarily reduce access token lifetime:
```python
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 1  # 1 minute for testing
```

---

## Troubleshooting

### Issue: Refresh loop (multiple refresh calls)
- **Cause**: `_retry` flag not working
- **Check**: `originalRequest._retry` should be set to `true`

### Issue: Tokens not updating
- **Cause**: Response structure mismatch
- **Check**: Backend returns `response.data.data.access_token` (not `response.data.access_token`)

### Issue: Still redirecting immediately on 401
- **Cause**: Refresh token missing
- **Check**: Login stores both tokens in localStorage

### Issue: Queue not processing
- **Cause**: `processQueue` not called after refresh
- **Check**: Both success and error paths call `processQueue`

---

## Success Criteria

✅ Token refreshes automatically on 401 without user intervention
✅ Multiple concurrent requests handled efficiently (single refresh call)
✅ Failed refresh redirects to login cleanly
✅ Logout clears both tokens
✅ No infinite refresh loops
✅ Original requests retry successfully after refresh

---

## Next Steps (Optional Enhancements)

1. **Proactive Refresh**: Refresh token before it expires (check expiry in JWT)
2. **Refresh Token Rotation**: Backend rotates refresh token on each use (already implemented!)
3. **Session Timeout Warning**: Show modal before redirecting to login
4. **Analytics**: Track refresh success/failure rates
5. **Retry Strategy**: Add exponential backoff for network errors

---

## Related Files

- `/mnt/g/khoirul/signate/web-admin/src/services/api.js` - Token refresh logic
- `/mnt/g/khoirul/signate/web-admin/src/pages/Login.jsx` - Store tokens on login
- `/mnt/g/khoirul/signate/web-admin/src/components/Layout.jsx` - Clear tokens on logout
- `/mnt/g/khoirul/signate/backend/app/api/auth.py` - Backend refresh endpoint
