# Device Routes Consolidation Plan

## Current State
- **10 files** with **4,518 lines** of route code
- Fragmented organization making it hard to maintain
- Multiple routers require careful prefix management in main.py

## Target State
- **3 files** with same functionality
- Clear separation of concerns
- Simpler router registration

---

## File 1: `routes.py` (~450 lines) - Core CRUD

**STATUS**: ✅ Created as `routes_new.py`

### Endpoints Included:
- POST /request-code - Request activation code (player)
- POST /heartbeat - Device heartbeat (player)
- GET /check-activation - Check activation status (player)
- GET /check-activation-by-uuid - Check by UUID (player)
- GET /verify-fingerprint - Verify fingerprint (player)
- POST /validate-reset-password - Validate reset password (player)
- POST /hard-reset - Hard reset device (player)
- POST /activate - Activate device (CMS)
- GET /list - List devices (CMS)
- GET /{device_id} - Get device (CMS)
- GET /me - Get my device info (player)
- PUT /{device_id} - Update device (CMS)
- DELETE /{device_id} - Delete device (CMS)
- POST /{device_id}/release - Release device (CMS)

**Line count**: 1,225 lines → ~450 lines (removed extended features)

---

## File 2: `management_routes.py` (~900 lines) - Assignments & Groups

**Sources**:
- `assignment_routes.py` (727 lines)
- `group_routes.py` (370 lines)

### Sections:

#### Device Assignments (from assignment_routes.py):
- GET /devices/{device_id}/tags
- POST /devices/{device_id}/tags
- DELETE /devices/{device_id}/tags/{tag_id}
- GET /devices/{device_id}/contents
- POST /devices/{device_id}/contents
- DELETE /devices/{device_id}/contents/{content_id}
- GET /devices/{device_id}/playlists
- POST /devices/{device_id}/playlists
- DELETE /devices/{device_id}/playlists/{playlist_id}

#### Device Groups (from group_routes.py):
- POST /groups - Create group
- GET /groups - List groups
- GET /groups/roots - Get root groups
- GET /groups/{group_id} - Get group
- GET /groups/{group_id}/children - Get children
- GET /groups/{group_id}/devices - Get devices in group
- GET /groups/{group_id}/stats - Get group stats
- PUT/PATCH /groups/{group_id} - Update group
- POST /groups/{group_id}/devices - Add device to group
- DELETE /groups/{group_id}/devices/{device_id} - Remove from group
- DELETE /groups/{group_id} - Delete group

**Router prefix**: `/api/v1/devices`
**Tags**: ["Device Management"]

---

## File 3: `monitoring_routes.py` (~1100 lines) - Monitoring & Control

**Sources**:
- `extended_routes.py` (591 lines) - TV/Monitor registration, content resolution, speed tests
- `health_routes.py` (262 lines) - Health metrics
- `log_routes.py` (479 lines) - Device logs & connection logs
- `command_routes.py` (298 lines) - Device commands
- `console_control_routes.py` (376 lines) - WebSocket control
- `console_routes.py` (147 lines) - Console streaming
- `connection_log_routes.py` (43 lines) - Connection logs (MERGED into log_routes.py)

### Sections:

#### Extended Operations (from extended_routes.py):
- POST /tv/register - Register TV device
- POST /monitor/register - Register monitor device
- GET /devices/{device_id}/content/resolved - Get resolved content (3-tier priority)
- POST /devices/{device_id}/speed-test - Record speed test
- GET /devices/{device_id}/speed-tests - Get speed test history

#### Health Monitoring (from health_routes.py):
- POST /devices/{device_id}/health - Record health metrics (player)
- GET /devices/{device_id}/health - Get health with alerts (CMS)
- GET /devices/{device_id}/health/history - Get health history (CMS)
- GET /devices/{device_id}/health/latest - Get latest health (CMS)
- GET /devices/{device_id}/health/alerts - Get health alerts (CMS)
- GET /organizations/{org_id}/health/summary - Get org health summary (CMS)

#### Device Logs (from log_routes.py):
- POST /devices/{device_id}/logs - Create log entry (player)
- GET /devices/{device_id}/logs - Get logs (CMS)
- DELETE /devices/{device_id}/logs - Clear logs (CMS)
- GET /devices/{device_id}/logs/latest - Get latest logs (CMS)
- POST /devices/{device_id}/logs/batch - Batch console logs (player)
- GET /devices/{device_id}/connection-logs - Get connection logs (CMS)
- POST /devices/{device_id}/connection-logs - Save connection logs (player)

#### Device Commands (from command_routes.py):
- POST /devices/{device_id}/commands - Send command (CMS)
- GET /devices/{device_id}/commands/pending - Get pending commands (player)
- POST /devices/{device_id}/commands/{command_id}/execute - Mark executed (player)
- GET /devices/{device_id}/commands - Get command history (CMS)
- POST /devices/{device_id}/commands/reset - Quick reset command (CMS)

#### Console Streaming (from console_control_routes.py + console_routes.py):
- WebSocket /devices/{device_id}/console/control - Player control WebSocket
- WebSocket /devices/{device_id}/console/stream - Admin stream WebSocket

**Router prefix**: `/api/v1`
**Tags**: ["Device Monitoring"]

---

## Implementation Steps

### Step 1: Create `management_routes.py` ✅ NEXT
```python
# Merge assignment_routes.py + group_routes.py
# Keep all endpoints, just reorganize sections
```

### Step 2: Create `monitoring_routes.py`
```python
# Merge extended_routes.py + health_routes.py + log_routes.py +
# command_routes.py + console_control_routes.py + console_routes.py
```

### Step 3: Rename `routes_new.py` → `routes.py`
```bash
mv routes_new.py routes.py
```

### Step 4: Update `__init__.py`
```python
"""
Device Service
Device management, registration, and monitoring
"""

from .routes import router
from .management_routes import router as management_router
from .monitoring_routes import router as monitoring_router

__all__ = ["router", "management_router", "monitoring_router"]
```

### Step 5: Update `main.py`
```python
# OLD (10 routers):
from services.device.routes import router as device_router
from services.device.assignment_routes import router as device_assignment_router
from services.device.command_routes import router as device_command_router
from services.device.health_routes import router as device_health_router
from services.device.log_routes import router as device_log_router
from services.device.connection_log_routes import router as device_connection_log_router
from services.device.console_routes import router as device_console_router
from services.device.console_control_routes import router as device_console_control_router
from services.device.extended_routes import router as device_extended_router
from services.device.group_routes import router as device_group_router

app.include_router(device_group_router, prefix="/api/v1/devices", tags=["Device Groups"])
app.include_router(device_log_router, prefix="/api/v1", tags=["Device Logs"])
app.include_router(device_connection_log_router, prefix="/api/v1", tags=["Device Connection Logs"])
app.include_router(device_console_router, prefix="/api/v1", tags=["Device Console Logs"])
app.include_router(device_console_control_router, prefix="/api/v1", tags=["Device Console Control"])
app.include_router(device_router, tags=["Device Management"])
app.include_router(device_assignment_router, prefix="/api/v1", tags=["Device Assignments"])
app.include_router(device_command_router, prefix="/api/v1", tags=["Device Commands"])
app.include_router(device_health_router, prefix="/api/v1", tags=["Device Health"])
app.include_router(device_extended_router, tags=["Device Extended"])

# NEW (3 routers):
from services.device import router as device_router, management_router as device_management_router, monitoring_router as device_monitoring_router

app.include_router(device_router, tags=["Device Core"])
app.include_router(device_management_router, prefix="/api/v1/devices", tags=["Device Management"])
app.include_router(device_monitoring_router, prefix="/api/v1", tags=["Device Monitoring"])
```

### Step 6: Remove old files
```bash
rm assignment_routes.py
rm group_routes.py
rm extended_routes.py
rm health_routes.py
rm log_routes.py
rm command_routes.py
rm console_control_routes.py
rm console_routes.py
rm connection_log_routes.py
```

### Step 7: Test all endpoints
```bash
# Verify endpoints still work
curl http://localhost:8001/docs  # Check Swagger
```

---

## Verification Checklist

- [ ] All 10 old route files removed
- [ ] 3 new route files created
- [ ] __init__.py exports 3 routers
- [ ] main.py registers 3 routers (not 10)
- [ ] All endpoints accessible at same URLs
- [ ] Swagger docs show correct grouping
- [ ] No duplicate endpoint errors
- [ ] All imports resolve correctly
- [ ] Backend starts without errors

---

## Benefits

1. **Reduced Complexity**: 10 files → 3 files (70% reduction)
2. **Clear Organization**: Core / Management / Monitoring
3. **Easier Navigation**: Related endpoints grouped together
4. **Simpler Imports**: 3 routers instead of 10
5. **Better Maintainability**: Logical separation of concerns
6. **Same Functionality**: ALL endpoints preserved

---

## Next Steps

Run this command to complete consolidation:

```bash
cd /mnt/g/khoirul/signate/backend-python/services/device

# Create management_routes.py and monitoring_routes.py following the plan
# Then rename routes_new.py to routes.py
# Update __init__.py and main.py
# Remove old files
# Test
```
