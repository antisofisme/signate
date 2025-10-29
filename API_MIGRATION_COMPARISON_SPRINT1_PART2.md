# API Migration Comparison - Sprint 1 Part 2

**Date:** October 28, 2025
**Endpoints Migrated:** 30 (devices.py: 20, client.py: 2, firebird.py: 8)

---

## 1. Devices API (backend/app/api/devices.py)

### Endpoint: GET /devices

#### BEFORE
```python
@router.get("/")
def list_devices(
    request: Request,
    skip: int = 0,  # ❌ skip parameter
    limit: int = 100,
    device_type: str = None,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    # ...
    devices = query.offset(skip).limit(limit).all()

    # Calculate page from skip
    page = (skip // limit) + 1 if limit > 0 else 1

    return paginated_response(
        data=[...],
        total=total,
        page=page,
        page_size=limit,
        request_id=request_id
    )
```

**Request Example:**
```
GET /api/devices?skip=20&limit=10
```

**Response:**
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "total": 150,
    "page": 3,        // Calculated from skip
    "page_size": 10,
    "total_pages": 15
  }
}
```

#### AFTER
```python
@router.get("/")
def list_devices(
    request: Request,
    page: int = 1,  # ✅ page parameter (1-indexed)
    limit: int = 100,
    device_type: str = None,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    # Calculate offset from page
    offset = (page - 1) * limit

    devices = query.offset(offset).limit(limit).all()

    # Calculate total pages
    import math
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return paginated_response(
        data=[...],
        total=total,
        page=page,
        page_size=limit,
        request_id=request_id
    )
```

**Request Example:**
```
GET /api/devices?page=3&limit=10
```

**Response:**
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "total": 150,
    "page": 3,        // Direct from parameter
    "page_size": 10,
    "total_pages": 15
  }
}
```

**Changes:**
- ✅ Replaced `skip` with `page` parameter
- ✅ Page is now 1-indexed (not 0-based offset)
- ✅ Calculate `offset` from `page` instead of using `skip` directly
- ✅ Calculate `total_pages` explicitly for better UX

---

## 2. Client API (backend/app/api/client.py)

### Endpoint: GET /client/playlist

#### BEFORE
```python
@router.get("/playlist", response_model=PlaylistResponse)  # ❌ Direct model
def get_device_playlist(
    request: Request,
    device_id: int,
    db: Session = Depends(get_db)
):
    # ... logic ...

    return PlaylistResponse(  # ❌ Direct return
        device_id=device.id,
        device_name=device.device_name,
        device_type=device.device_type,
        total_items=len(playlist_items),
        playlist=playlist_items
    )
```

**Response:**
```json
{
  "device_id": 1,
  "device_name": "TV-001",
  "device_type": "tv",
  "total_items": 5,
  "playlist": [
    {
      "content_id": 1,
      "title": "Video 1",
      "content_type": "video",
      "url": "http://...",
      "duration": 30,
      "mime_type": "video/mp4"
    }
  ]
}
```

#### AFTER
```python
@router.get("/playlist")  # ✅ No response_model
def get_device_playlist(
    request: Request,
    device_id: int,
    db: Session = Depends(get_db)
):
    # ... logic ...

    playlist_data = {  # ✅ Build dict
        "device_id": device.id,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "total_items": len(playlist_items),
        "playlist": [item.model_dump() for item in playlist_items]
    }

    return success_response(  # ✅ Wrapped response
        data=playlist_data,
        request_id=request_id
    )
```

**Response:**
```json
{
  "success": true,
  "data": {
    "device_id": 1,
    "device_name": "TV-001",
    "device_type": "tv",
    "total_items": 5,
    "playlist": [
      {
        "content_id": 1,
        "title": "Video 1",
        "content_type": "video",
        "url": "http://...",
        "duration": 30,
        "mime_type": "video/mp4"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00.123Z",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "version": "1.0.0"
  }
}
```

**Changes:**
- ✅ Removed `response_model` decorator
- ✅ Wrapped response in `success_response()`
- ✅ Added `meta` with `timestamp`, `request_id`, `version`
- ⚠️ **Breaking:** Viewer needs to access `response.data` instead of root

---

### Endpoint: GET /client/status

#### BEFORE
```python
@router.get("/status", response_model=DeviceStatusResponse)  # ❌ Direct model
def check_device_status(
    request: Request,
    device_id: int,
    db: Session = Depends(get_db)
):
    # ... logic ...

    return DeviceStatusResponse(  # ❌ Direct return
        device_id=device.id,
        status=device.status,
        is_active=is_active,
        message=message
    )
```

**Response:**
```json
{
  "device_id": 1,
  "status": "active",
  "is_active": true,
  "message": "Device is active and authorized"
}
```

#### AFTER
```python
@router.get("/status")  # ✅ No response_model
def check_device_status(
    request: Request,
    device_id: int,
    db: Session = Depends(get_db)
):
    # ... logic ...

    status_data = {  # ✅ Build dict
        "device_id": device.id,
        "status": device.status,
        "is_active": is_active,
        "message": message
    }

    return success_response(  # ✅ Wrapped response
        data=status_data,
        request_id=request_id
    )
```

**Response:**
```json
{
  "success": true,
  "data": {
    "device_id": 1,
    "status": "active",
    "is_active": true,
    "message": "Device is active and authorized"
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00.123Z",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "version": "1.0.0"
  }
}
```

**Changes:**
- ✅ Removed `response_model` decorator
- ✅ Wrapped response in `success_response()`
- ✅ Added `meta` with `timestamp`, `request_id`, `version`
- ⚠️ **Breaking:** Viewer needs to access `response.data` instead of root

---

## 3. Firebird API (backend/app/api/firebird.py)

### Endpoint: GET /api/firebird/configs

#### BEFORE
```python
@router.get("/api/firebird/configs")
async def list_firebird_configs(
    request: Request,
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),  # ❌ skip parameter
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # ...
    configs = query.order_by(FirebirdConfig.id).offset(skip).limit(limit).all()

    return success_response(
        data={
            "total": total,  # ❌ Flat structure
            "configs": [config.model_dump() for config in config_list]
        },
        request_id=request_id
    )
```

**Request Example:**
```
GET /api/firebird/configs?skip=10&limit=5
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 15,
    "configs": [...]
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00.123Z",
    "request_id": "...",
    "version": "1.0.0"
  }
}
```

#### AFTER
```python
@router.get("/api/firebird/configs")
async def list_firebird_configs(
    request: Request,
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),  # ✅ page parameter (1-indexed)
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Calculate offset from page
    offset = (page - 1) * limit

    configs = query.order_by(FirebirdConfig.id).offset(offset).limit(limit).all()

    # Calculate total pages
    import math
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return success_response(
        data={
            "items": [config.model_dump() for config in config_list],  # ✅ items
            "pagination": {  # ✅ Nested pagination metadata
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        },
        request_id=request_id
    )
```

**Request Example:**
```
GET /api/firebird/configs?page=3&limit=5
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 3,
      "limit": 5,
      "total": 15,
      "total_pages": 3
    }
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00.123Z",
    "request_id": "...",
    "version": "1.0.0"
  }
}
```

**Changes:**
- ✅ Replaced `skip` with `page` parameter
- ✅ Page is now 1-indexed (not 0-based offset)
- ✅ Calculate `offset` from `page` instead of using `skip` directly
- ✅ Changed `data.configs` to `data.items` for consistency
- ✅ Added nested `pagination` object with `page`, `limit`, `total`, `total_pages`
- ⚠️ **Breaking:** Frontend needs to access `response.data.items` instead of `response.data.configs`
- ⚠️ **Breaking:** Frontend needs to read `response.data.pagination` for metadata

---

## Migration Summary

### Pattern Changes

| Aspect | Before | After |
|--------|--------|-------|
| **Pagination Parameter** | `skip=0` (0-based offset) | `page=1` (1-indexed) |
| **Offset Calculation** | Direct `skip` | `offset = (page - 1) * limit` |
| **Total Pages** | Not calculated | `math.ceil(total / limit)` |
| **Response Wrapping** | Direct model return | `success_response(data=...)` |
| **Response Model** | `response_model=XxxResponse` | No decorator (wrapped) |
| **Meta Information** | Missing | `timestamp`, `request_id`, `version` |

### Breaking Changes Summary

#### 1. Devices API
- **Parameter Change:** `skip` → `page`
- **Impact:** Web Admin needs to update from `?skip=20` to `?page=3`
- **Status:** Frontend already uses `page`, **no breaking change expected** ✅

#### 2. Client API
- **Response Structure:** Root data → `response.data`
- **Impact:** Viewer needs to access `response.data.playlist` instead of `response.playlist`
- **Action Required:** Update viewer API calls ⚠️

#### 3. Firebird API
- **Parameter Change:** `skip` → `page`
- **Data Structure:** `data.configs` → `data.items`, added `data.pagination`
- **Impact:** Web Admin Firebird config page needs updates
- **Action Required:** Update frontend to use new structure ⚠️

---

## Frontend Migration Guide

### For Web Admin (Devices List)

**Before:**
```javascript
const response = await fetch('/api/devices?skip=20&limit=10');
const data = await response.json();
const devices = data.data;  // Works (already wrapped)
const total = data.meta.total;
```

**After:**
```javascript
const response = await fetch('/api/devices?page=3&limit=10');
const data = await response.json();
const devices = data.data;  // Same (no change) ✅
const total = data.meta.total;
const currentPage = data.meta.page;
const totalPages = data.meta.total_pages;
```

**Changes:**
- ✅ Change URL parameter from `skip=20` to `page=3`
- ✅ Access `meta.page` and `meta.total_pages` for UI

---

### For Viewer (Playlist)

**Before:**
```javascript
const response = await fetch(`/api/client/playlist?device_id=${deviceId}`);
const playlist = await response.json();
console.log(playlist.device_name);  // Direct access
console.log(playlist.playlist);     // Direct access
```

**After:**
```javascript
const response = await fetch(`/api/client/playlist?device_id=${deviceId}`);
const result = await response.json();
const playlist = result.data;  // ⚠️ Access via .data
console.log(playlist.device_name);  // Now works
console.log(playlist.playlist);     // Now works
```

**Changes:**
- ⚠️ Add `.data` to access payload
- ✅ Access `result.meta.request_id` for debugging

---

### For Web Admin (Firebird Config List)

**Before:**
```javascript
const response = await fetch('/api/firebird/configs?skip=0&limit=100');
const result = await response.json();
const configs = result.data.configs;  // ⚠️ Old structure
const total = result.data.total;       // ⚠️ Old structure
```

**After:**
```javascript
const response = await fetch('/api/firebird/configs?page=1&limit=100');
const result = await response.json();
const configs = result.data.items;          // ✅ New structure
const pagination = result.data.pagination;  // ✅ New structure
const total = pagination.total;
const currentPage = pagination.page;
const totalPages = pagination.total_pages;
```

**Changes:**
- ⚠️ Change URL parameter from `skip=0` to `page=1`
- ⚠️ Access `data.items` instead of `data.configs`
- ⚠️ Read pagination from `data.pagination` instead of flat structure

---

## Testing Checklist

### Backend Tests
- [x] Syntax validation passed (py_compile)
- [ ] Unit tests for paginated endpoints
- [ ] Integration tests for wrapped responses
- [ ] Test request_id propagation
- [ ] Test exception handling

### Frontend Tests
- [ ] Web Admin devices list works with `page` parameter
- [ ] Viewer can access `response.data.playlist`
- [ ] Viewer can access `response.data` for status
- [ ] Web Admin Firebird config list uses new structure
- [ ] Pagination UI displays correct page numbers

### Manual Tests
- [ ] Web Admin: Navigate devices list (page 1, 2, 3...)
- [ ] Viewer: Load playlist from backend
- [ ] Viewer: Check device status
- [ ] Web Admin: List Firebird configs with pagination
- [ ] Check browser console for errors
- [ ] Verify request_id in network tab

---

## Rollback Plan

If issues occur after deployment:

### Option 1: Frontend-Only Fix (Recommended)
- Update frontend to use new structure
- No backend rollback needed
- Gradual rollout possible

### Option 2: Backend Rollback
```bash
# Revert to previous commit
git revert <commit-hash>

# Rebuild Docker container
docker-compose up -d --build backend-api

# Verify rollback
curl http://192.168.5.12:8001/api/devices?skip=0&limit=10
```

### Option 3: Compatibility Layer
Add backward compatibility endpoints:
```python
@router.get("/devices-legacy")
def list_devices_legacy(skip: int = 0, limit: int = 100, ...):
    # Old implementation with skip/limit
    pass
```

---

**Generated:** October 28, 2025
**Status:** ✅ Migration Complete
**Next Action:** Update frontend for breaking changes
