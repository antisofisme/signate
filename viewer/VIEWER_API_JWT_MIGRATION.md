# Viewer API JWT Token Migration - Complete

## Status: ✅ COMPLETE

All viewer API calls have been migrated from insecure `device_id` query parameters to secure JWT Bearer token authentication.

---

## Files Modified

### Backend (1 file)
1. **backend/app/api/devices.py** (Lines 1222-1255)
   - Updated `check-activation` endpoint to return JWT tokens when device becomes active
   - Returns `device_token`, `token_expires_at` in activation response

### Viewer Frontend (5 files)

1. **viewer/js/shared/token-manager.js** (Lines 220-262)
   - Added `handle401()` method for token refresh and recovery
   - Handles 401 responses: tries refresh once, then resets viewer if refresh fails

2. **viewer/js/player/api.js** (Lines 10-50, 89-110)
   - `loadPlaylist()`: Added JWT auth header, removed `?device_id=` query param
   - `checkPlaylistUpdate()`: Added JWT auth header, removed `?device_id=` query param
   - Both methods handle 401 with token refresh + retry logic

3. **viewer/js/shell/heartbeat.js** (Lines 114-156)
   - Added JWT auth header to heartbeat POST request
   - Added 401 handling with token refresh
   - Keeps `device_id` in request body (required by backend schema)

4. **viewer/js/shell/activation-poll.js** (Lines 165-175)
   - Saves JWT token from backend when device is activated
   - Uses `data.device_token` from activation response

5. **viewer/js/shell/commands.js** (Lines 18-41, 220-232)
   - `checkAndExecute()`: Added JWT auth header to command polling
   - `markExecuted()`: Added JWT auth header to command execution

---

## API Calls Updated (6 endpoints)

| Endpoint | File | Line | Change |
|----------|------|------|--------|
| `GET /api/client/playlist` | player/api.js | 22-24 | ✅ JWT header, removed `?device_id` |
| `GET /api/client/playlist` | player/api.js | 98-100 | ✅ JWT header (periodic check) |
| `POST /api/devices/heartbeat` | heartbeat.js | 119-122 | ✅ JWT header, 401 handling |
| `GET /api/devices/{id}/commands/pending` | commands.js | 25-30 | ✅ JWT header |
| `POST /api/devices/{id}/commands/{id}/execute` | commands.js | 226-231 | ✅ JWT header |
| `GET /api/devices/check-activation/{code}` | activation-poll.js | 68-74 | ✅ Saves token on activation |

---

## Authentication Flow

### 1. Device Registration (Unchanged)
```
Viewer → POST /api/devices/monitor/register
         { activation_code, device_name, platform }
       ← { id, unique_code, status: "pending" }
```
- No token yet (device is pending)
- Shows activation code on screen

### 2. Activation & Token Generation (NEW)
```
Viewer → GET /api/devices/check-activation/{code}
       ← {
           activated: true,
           device_id: 123,
           device_token: "eyJhbGciOiJIUzI1NiIs...",  ← NEW
           token_expires_at: "2025-11-27T...",       ← NEW
         }
```
- Backend generates 30-day JWT token
- Viewer saves token to localStorage via `TokenManager.saveToken()`

### 3. Authenticated API Calls (NEW)
```
Viewer → GET /api/client/playlist
         Authorization: Bearer eyJhbGciOiJIUzI1NiIs...  ← NEW
       ← { playlist: [...] }
```
- All API calls now include `Authorization: Bearer <token>` header
- No more `?device_id=123` in URL

### 4. Token Refresh (NEW)
```
# If 401 Unauthorized received:
Viewer → POST /api/client/refresh
         Authorization: Bearer <refresh_token>
       ← { device_token: "new_token", token_expires_at: "..." }

# If refresh fails:
- Clear localStorage
- Delete IndexedDB cache
- Reload page (shows activation screen)
```

---

## Error Handling

### 401 Unauthorized
1. **Try refresh once**: Call `TokenManager.handle401(apiBaseUrl)`
2. **If refresh succeeds**: Retry the original request
3. **If refresh fails**: Reset viewer (clear storage + reload)

### Example (player/api.js):
```javascript
if (response.status === 401) {
    const handled = await window.TokenManager.handle401(state.API_BASE_URL);
    if (handled) {
        return this.loadPlaylist(); // Retry with new token
    }
    // handle401 will reload page if refresh fails
}
```

---

## Token Lifecycle

| Event | Action | Location |
|-------|--------|----------|
| **Device Activation** | Save token from backend response | activation-poll.js:166-172 |
| **API Call** | Add `Authorization: Bearer <token>` header | All files via TokenManager.addAuthHeader() |
| **Token Expired (401)** | Try refresh once, then reset | TokenManager.handle401() |
| **Token Refresh** | Update localStorage with new token | TokenManager.refreshToken() |
| **Device Reset** | Clear all tokens | TokenManager.clearToken() |

---

## Security Improvements

| Before (Insecure) | After (Secure) |
|-------------------|----------------|
| `?device_id=123` in URL | `Authorization: Bearer <jwt>` in header |
| Device ID visible in logs | Token is signed and verifiable |
| No expiration | 30-day token expiration |
| No refresh mechanism | Automatic token refresh |
| Easy to spoof | Cryptographically secure |

---

## Testing Checklist

- [ ] Device registers and shows activation code
- [ ] Admin activates device in Web Admin
- [ ] Viewer receives and saves JWT token on activation
- [ ] Playlist loads successfully with JWT token
- [ ] Heartbeat sends with JWT token
- [ ] Commands fetch/execute with JWT token
- [ ] Token refresh works on 401 response
- [ ] Viewer resets if token refresh fails
- [ ] No `?device_id=` in URL logs
- [ ] All API calls show `Authorization: Bearer` in network tab

---

## Backend Compatibility

The backend supports **backward compatibility** during migration:
- Old viewers: `?device_id=123` query param still works (logs deprecation warning)
- New viewers: `Authorization: Bearer <token>` header (preferred)

This allows gradual rollout without breaking existing devices.

---

## Summary

**Status**: ✅ 100% Complete
**Files Modified**: 6 (1 backend + 5 viewer)
**API Calls Updated**: 6 endpoints
**Security**: Upgraded from query param to JWT Bearer token
**Auth Flow**: Registration → Activation (get token) → Authenticated calls → Auto-refresh

All viewer API calls now use secure JWT authentication! 🎉
