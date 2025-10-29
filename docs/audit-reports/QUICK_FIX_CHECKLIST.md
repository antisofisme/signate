# Quick Fix Checklist - Integration Issues

**Priority-ordered tasks to fix integration issues**

---

## 🔴 CRITICAL FIXES (Do First - This Week)

### ✅ Task 1: Fix Hardcoded URLs in Viewer
**Estimated Time:** 2 hours
**Impact:** High - Breaks when IP changes
**Files to Edit:**

```bash
# Fix file 1
File: viewer/js/shared/api-client.js
Line: 12

# BEFORE:
this.apiBaseUrl = options.apiBaseUrl || 'http://192.168.5.12:8001';

# AFTER:
this.apiBaseUrl = window.ENV?.API_BASE_URL ||
                  options.apiBaseUrl ||
                  'http://localhost:8001';
```

```bash
# Fix file 2
File: viewer/js/shared/analytics-tracker.js
Line: 12

# BEFORE:
this.apiBaseUrl = options.apiBaseUrl || 'http://192.168.5.12:8001';

# AFTER:
this.apiBaseUrl = window.ENV?.API_BASE_URL ||
                  options.apiBaseUrl ||
                  'http://localhost:8001';
```

**Testing:**
```bash
# 1. Update env.js with different IP
echo "window.ENV = { API_BASE_URL: 'http://10.0.0.1:8001' }" > viewer/js/config/env.js

# 2. Open viewer in browser
# 3. Check console - should show correct API URL
# 4. Test registration flow
```

**Done When:**
- [ ] Both files updated
- [ ] Tested with different IP
- [ ] No more hardcoded IPs in viewer JS files
- [ ] Committed to Git

---

### ✅ Task 2: Add Missing GET /api/languages Endpoint
**Estimated Time:** 2 hours
**Impact:** High - Viewer language switching broken
**Files to Edit:**

```bash
File: backend/app/api/translations.py
Location: Add new endpoint at top of file
```

**Code to Add:**
```python
@router.get("/api/languages")
async def list_languages(
    request: Request,
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    List available languages for content

    Returns:
        APIResponse: List of language codes and names
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing available languages",
        request_id=request_id
    )

    languages = [
        {"code": "en", "name": "English", "native_name": "English"},
        {"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia"},
        {"code": "zh", "name": "Chinese", "native_name": "中文"},
    ]

    return success_response(
        data=languages,
        message="Languages retrieved successfully"
    )
```

**Update main.py:**
```python
# Add import at top
from app.api import translations

# Add router (already exists, just verify)
app.include_router(translations.router, tags=["Translations"])
```

**Testing:**
```bash
# 1. Start backend
cd backend && uvicorn app.main:app --reload

# 2. Test endpoint
curl http://localhost:8001/api/languages

# Expected response:
{
  "success": true,
  "data": [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia"},
    {"code": "zh", "name": "Chinese", "native_name": "中文"}
  ],
  "meta": {...}
}

# 3. Test from viewer
# Open viewer, check language selector works
```

**Done When:**
- [ ] Endpoint added and tested
- [ ] Returns standardized response format
- [ ] Viewer language selector works
- [ ] API docs updated (/docs)
- [ ] Committed to Git

---

### ✅ Task 3: Create Schedules API Module
**Estimated Time:** 4 hours
**Impact:** High - Web Admin scheduler broken
**Files to Create:**

```bash
# Create new file
File: backend/app/api/schedules.py
```

**Full Implementation:**
```python
"""
Schedule Management API endpoints
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.core.cache import invalidate_by_prefix, CACHE_KEY_PREFIXES
from app.schemas.common import success_response, APIResponse
from app.middleware.request_id import get_request_id
from app.models.user import User
from app.models.schedule import Schedule

logger = StructuredLogger(__name__)
router = APIRouter()


@router.get("/api/schedules")
async def list_schedules(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse:
    """List all schedules"""
    request_id = get_request_id(request)

    logger.info("Listing schedules", request_id=request_id, user_id=current_user.id)

    schedules = db.query(Schedule).all()

    return success_response(
        data=[{
            "id": s.id,
            "name": s.name,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "days_of_week": s.days_of_week,
            "is_active": s.is_active
        } for s in schedules],
        message=f"Found {len(schedules)} schedules"
    )


@router.post("/api/schedules")
async def create_schedule(
    request: Request,
    schedule_data: dict,  # TODO: Create proper Pydantic schema
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse:
    """Create new schedule"""
    request_id = get_request_id(request)

    logger.info("Creating schedule", request_id=request_id, user_id=current_user.id)

    schedule = Schedule(**schedule_data)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    invalidate_by_prefix(CACHE_KEY_PREFIXES["schedule"])

    return success_response(
        data={"id": schedule.id, "name": schedule.name},
        message="Schedule created successfully"
    )


@router.put("/api/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: int,
    request: Request,
    schedule_data: dict,  # TODO: Create proper Pydantic schema
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse:
    """Update existing schedule"""
    request_id = get_request_id(request)

    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise NotFoundException(
            message="Schedule not found",
            details={"schedule_id": schedule_id}
        )

    logger.info("Updating schedule", request_id=request_id, schedule_id=schedule_id)

    for key, value in schedule_data.items():
        setattr(schedule, key, value)

    db.commit()
    db.refresh(schedule)

    invalidate_by_prefix(CACHE_KEY_PREFIXES["schedule"])

    return success_response(
        data={"id": schedule.id, "name": schedule.name},
        message="Schedule updated successfully"
    )


@router.delete("/api/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> APIResponse:
    """Delete schedule"""
    request_id = get_request_id(request)

    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise NotFoundException(
            message="Schedule not found",
            details={"schedule_id": schedule_id}
        )

    logger.info("Deleting schedule", request_id=request_id, schedule_id=schedule_id)

    db.delete(schedule)
    db.commit()

    invalidate_by_prefix(CACHE_KEY_PREFIXES["schedule"])

    return success_response(
        message="Schedule deleted successfully"
    )
```

**Update main.py:**
```python
# Add import
from app.api import schedules

# Add router
app.include_router(schedules.router, tags=["Schedules"])
```

**Testing:**
```bash
# Test CRUD operations
curl -X GET http://localhost:8001/api/schedules \
  -H "Authorization: Bearer {token}"

curl -X POST http://localhost:8001/api/schedules \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Morning Playlist", "start_time": "08:00", "end_time": "12:00"}'
```

**Done When:**
- [ ] Module created and imported
- [ ] All CRUD endpoints working
- [ ] Proper Pydantic schemas (TODO after testing)
- [ ] Web Admin scheduler UI functional
- [ ] Committed to Git

---

### ✅ Task 4: Implement Token Refresh
**Estimated Time:** 8 hours
**Impact:** High - Better UX (no forced logout)
**Files to Edit:**

```typescript
File: web-admin/src/services/api/index.ts
Location: Add after existing interceptors
```

**Code to Add:**
```typescript
// Token refresh state
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(promise => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token!);
    }
  });

  failedQueue = [];
};

// Enhanced response interceptor with token refresh
api.interceptors.response.use(
  (response) => {
    // ... existing success logic ...
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {

      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');

        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Call refresh endpoint
        const response = await axios.post(
          `${API_BASE_URL}/api/auth/refresh`,
          { refresh_token: refreshToken },
          {
            headers: { 'Content-Type': 'application/json' }
          }
        );

        const { access_token } = response.data;

        // Store new token
        localStorage.setItem('token', access_token);

        // Update axios default header
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

        // Update original request
        originalRequest.headers.Authorization = `Bearer ${access_token}`;

        // Process queued requests
        processQueue(null, access_token);

        // Retry original request
        return api(originalRequest);

      } catch (refreshError) {
        // Refresh failed - logout user
        processQueue(refreshError, null);

        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');

        // Redirect to login
        window.location.href = '/login';

        return Promise.reject(refreshError);

      } finally {
        isRefreshing = false;
      }
    }

    // ... existing error handling logic ...
    return Promise.reject(error);
  }
);
```

**Update Login Component:**
```typescript
File: web-admin/src/services/api/auth.ts

// Update login response interface
interface LoginResponse {
  access_token: string;
  refresh_token: string;  // Add this
  token_type: string;
  expires_in: number;
}

const authAPI = {
  login: async (username: string, password: string) => {
    const response = await api.post('/api/auth/login', {
      username,
      password
    });

    // Store both tokens
    localStorage.setItem('token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);

    return response;
  },

  // ... existing methods ...
}
```

**Backend Verification:**
```python
# Verify refresh endpoint exists in backend/app/api/auth.py

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    # ... implementation should exist ...
    pass
```

**Testing:**
```bash
# Manual testing steps:
1. Login to Web Admin
2. Wait 16 minutes (access token expires in 15 min)
3. Perform any action (e.g., view devices)
4. Should NOT be logged out
5. Check Network tab - should see /api/auth/refresh call
6. Action should complete successfully

# Automated test (future):
# Create test that:
# - Logs in
# - Sets token expiry to past
# - Makes API call
# - Verifies token refresh happened
# - Verifies original call succeeded
```

**Done When:**
- [ ] Interceptor implemented
- [ ] Queue mechanism working
- [ ] Tested with multiple concurrent requests
- [ ] Tested token expiry scenario
- [ ] No more forced logouts
- [ ] Committed to Git

---

## 🟡 HIGH PRIORITY (Next Sprint - 2 Weeks)

### Task 5: Complete Quick Wins API Migration - Phase 8
**Estimated Time:** 3 days
**Impact:** Medium - Consistency
**Modules to Migrate:**
- [ ] `auth.py` (4 endpoints)
- [ ] `devices.py` (remaining endpoints)
- [ ] `activities.py` (5 endpoints)
- [ ] `client.py` (2 endpoints)

**Pattern to Follow:**
```python
# Use Quick Wins standardized response
from app.schemas.common import success_response, APIResponse
from app.core.exceptions import NotFoundException, BadRequestException

@router.get("/{id}")
async def get_item(
    id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> APIResponse:
    request_id = get_request_id(request)

    logger.info("Getting item", request_id=request_id, id=id)

    item = db.query(Model).filter(Model.id == id).first()
    if not item:
        raise NotFoundException(
            message="Item not found",
            details={"id": id}
        )

    return success_response(
        data=item_to_dict(item),
        message="Item retrieved successfully"
    )
```

---

### Task 6: Implement Device JWT Tokens
**Estimated Time:** 1 week
**Impact:** High - Security
**Implementation:**

1. **Update activation endpoint:**
```python
# backend/app/api/devices.py

from app.core.security import create_device_jwt

@router.post("/monitor/activate")
async def activate_monitor():
    # ... existing activation logic ...

    # Generate device JWT (expires in 1 year)
    device_token = create_device_jwt(
        device_id=device.id,
        expires_in_days=365
    )

    return success_response(
        data={
            "device_id": device.id,
            "device_token": device_token,  # NEW
            "message": "Device activated successfully"
        }
    )
```

2. **Update viewer to use token:**
```javascript
// viewer/js/shell/activation-poll.js

// After activation success:
localStorage.setItem('device_token', response.device_token);

// viewer/js/player/api.js
const deviceToken = localStorage.getItem('device_token');

const data = await window.APIClient.get(
    `${state.API_BASE_URL}/api/client/playlist?device_id=${state.deviceId}`,
    {
        headers: {
            'Authorization': `Bearer ${deviceToken}`
        }
    }
);
```

3. **Update client API to validate token:**
```python
# backend/app/api/client.py

from app.core.deps import get_current_device

@router.get("/playlist")
async def get_playlist(
    device_id: int,
    language: str = "en",
    current_device: Device = Depends(get_current_device)  # NEW
):
    # Verify device_id matches token
    if current_device.id != device_id:
        raise UnauthorizedException(
            message="Device ID mismatch"
        )

    # ... rest of logic ...
```

---

### Task 7: Refactor Metadata Storage
**Estimated Time:** 1 week
**Impact:** Medium - Consistency
**Strategy:**

1. **Audit what Anthias stores:**
```sql
-- Check Anthias SQLite schema
SELECT * FROM assets LIMIT 1;
```

2. **Remove duplicates from Anthias:**
   - Keep only: `asset_id`, `file_uri`, `uploaded_at`
   - Remove: `name`, `duration`, `mimetype` (stored in PostgreSQL)

3. **Update backend to never query Anthias for metadata:**
   - All metadata from PostgreSQL only
   - Anthias only for file serving

---

## 🟢 MEDIUM PRIORITY (Backlog)

### Task 8: Add CORS for WebOS
```python
# backend/.env.example
CORS_ORIGINS=http://localhost:3000,...,webos-local://
```

### Task 9: Implement Cascade Delete
```python
# backend/app/api/content.py

@router.delete("/{content_id}")
async def delete_content(content_id: int):
    # Delete from Anthias
    await anthias_service.delete_asset(content.anthias_asset_id)

    # Delete HLS files
    delete_hls_directory(content_id)

    # Delete from PostgreSQL
    db.delete(content)
```

### Task 10: Add Missing Env Vars
Update `.env.example` files with documented variables.

---

## Progress Tracking

**Sprint 1 (This Week):**
- [ ] Task 1: Fix hardcoded URLs ✅
- [ ] Task 2: Add /api/languages ✅
- [ ] Task 3: Create schedules API ✅
- [ ] Task 4: Token refresh ✅

**Sprint 2 (Next 2 Weeks):**
- [ ] Task 5: Quick Wins Phase 8
- [ ] Task 6: Device JWT tokens
- [ ] Task 7: Metadata refactor

**Backlog:**
- [ ] Task 8: WebOS CORS
- [ ] Task 9: Cascade delete
- [ ] Task 10: Env vars cleanup

---

## Testing Checklist

After each task:
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing in Web Admin
- [ ] Manual testing in Viewer
- [ ] API docs updated (/docs)
- [ ] Code reviewed
- [ ] Committed to Git
- [ ] Deployed to server
- [ ] Smoke tested in production

---

**Keep this checklist updated as tasks are completed!**
