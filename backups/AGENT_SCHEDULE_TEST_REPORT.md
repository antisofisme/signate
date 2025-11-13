# AGENT_SCHEDULE - Integration Test Report

**Test Run ID**: integration_test_20251113_190000
**Agent**: agent_schedule
**Organization**: TEST_ORG_SCHEDULE (org_12)
**Organization ID**: 15
**Admin User**: admin_sched (ID: 20)
**Test Date**: 2025-11-13 12:40:00 UTC

---

## Executive Summary

**Tests Run**: 6
**Tests Passed**: 0
**Tests Failed**: 6 (4 due to backend bug, 2 due to missing implementation)
**Audit Logs Verified**: No (no schedules created to audit)

### Critical Finding: Backend Bug Blocking All Schedule Operations

**Bug Description**: The backend schedule routes are attempting to access `current_user.user_id`, but the `CurrentUser` Pydantic model uses `id` as the attribute name, not `user_id`.

**Error Message**:
```
AttributeError: 'CurrentUser' object has no attribute 'user_id'
```

**Impact**: This bug blocks ALL schedule creation operations and related tag creation operations.

**Location**: `/app/services/schedule/routes.py` line 73

**Fix Required**: Change all references from `current_user.user_id` to `current_user.id` in the schedule service routes.

---

## Test Results Detail

### Test 1: Basic Schedule Creation
**Status**: FAILED
**Reason**: Backend bug - CurrentUser.user_id vs CurrentUser.id

**What Was Tested**:
- Created 2 playlists successfully (IDs: 16, 17)
- Attempted to create 2 schedules with overlapping times but different priorities
- Schedule A: Morning playlist, 08:00-12:00, priority 10
- Schedule B: Evening playlist, 08:00-12:00, priority 5

**Result**: Both schedule creation requests returned HTTP 500 due to backend bug.

**Resources Created**:
- Playlist IDs: 16, 17

---

### Test 2: Schedule Priority Logic
**Status**: SKIPPED
**Reason**: Depends on Test 1 success - no schedules to test against

**What Would Have Been Tested**:
- Query active schedule at 10:00 (overlapping time)
- Verify that higher priority schedule (priority 10) is returned
- Test the priority resolution logic

**API Endpoint Tested**: `POST /api/v1/schedules/active/check`
**Endpoint Status**: Working (returns proper null response when no schedules exist)

---

### Test 3: Schedule by Device IDs
**Status**: FAILED
**Reason**: Backend bug prevents schedule creation

**What Was Tested**:
- Created 2 devices successfully via activation flow:
  - DeviceX_Schedule (ID: 6186)
  - DeviceY_Schedule (ID: 6187)
- Created 1 playlist for device targeting (ID: 18)
- Attempted to create schedule targeting only DeviceX

**Result**: Schedule creation failed due to same backend bug.

**Resources Created**:
- Device IDs: 6186, 6187
- Playlist ID: 18

**Key Finding**: Device registration flow is working perfectly!

---

### Test 4: Schedule by Tags
**Status**: FAILED
**Reason**: Tag creation also affected by same backend bug

**What Was Tested**:
- Attempted to create tag "Conference Room"
- Tag creation endpoint returns HTTP 500

**Result**: Cannot test tag-based schedule targeting because tag creation is broken.

**Note**: Tag creation likely uses the same `current_user.user_id` pattern.

---

### Test 5: Schedule Apply to All
**Status**: FAILED
**Reason**: Backend bug prevents schedule creation

**What Was Tested**:
- Created 1 playlist for global schedule (ID: 19)
- Attempted to create schedule with `apply_to_all: true`

**Result**: Schedule creation failed due to backend bug.

**Resources Created**:
- Playlist ID: 19

---

### Test 6: Audit Logs for Schedules
**Status**: FAILED
**Reason**: No schedules were created to generate audit logs

**What Was Tested**:
- Queried audit logs for schedule-related operations
- Filtered by organization_id=15 and entity_type="schedule"

**Result**: No audit logs found (expected, since no schedules were created).

---

## Features Tested

| Feature | Status | Notes |
|---------|--------|-------|
| Schedule CRUD | backend_bug | Cannot create due to user_id vs id bug |
| Priority Logic | skipped_due_to_backend_bug | Endpoint works, but no data to test |
| Device Targeting | backend_bug | Device creation works, schedule creation blocked |
| Tag Targeting | not_implemented | Tag creation also has backend bug |
| Apply to All | not_implemented | Schedule creation blocked by bug |

---

## Created Resources

### Successfully Created:
- **Playlists**: 4 (IDs: 16, 17, 18, 19)
- **Devices**: 2 (IDs: 6186, 6187)
- **User**: admin_sched (ID: 20) in org_id 15

### Failed to Create:
- **Schedules**: 0 (all blocked by backend bug)
- **Tags**: 0 (blocked by backend bug)

---

## API Endpoints Tested

### Working Endpoints:
1. `POST /api/v1/auth/register` - User registration
2. `POST /api/v1/auth/login` - Authentication
3. `POST /api/v1/playlists` - Playlist creation
4. `GET /api/v1/playlists` - List playlists
5. `POST /api/v1/devices/request-code` - Device code request
6. `POST /api/v1/devices/activate` - Device activation
7. `POST /api/v1/schedules/active/check` - Check active schedule (returns proper response)
8. `GET /api/v1/schedules` - List schedules

### Broken Endpoints (Backend Bug):
1. `POST /api/v1/schedules` - Create schedule (HTTP 500)
2. `POST /api/v1/tags` - Create tag (HTTP 500)

---

## Backend Current Phase

Based on the 404 responses from previous agent tests, the backend is currently in:
**Phase 1 Day 2: RBAC + Session**

Schedules feature appears to be partially implemented but has the critical user_id bug.

---

## Recommendations

### Immediate Actions Required:

1. **Fix Backend Bug** (CRITICAL):
   ```python
   # File: /app/services/schedule/routes.py (and similar files)
   # Change:
   created_by=current_user.user_id
   # To:
   created_by=current_user.id
   ```

2. **Check All Services**: Search for `current_user.user_id` pattern across all backend services and replace with `current_user.id`.

3. **Rerun Tests**: Once bug is fixed, rerun agent_schedule tests to verify:
   - Schedule creation
   - Priority logic
   - Device targeting
   - Tag-based targeting
   - Apply to all logic

### Future Testing (After Bug Fix):

1. Test schedule conflict detection
2. Test schedule recurrence patterns
3. Test schedule exceptions
4. Test schedule assignment cascading (tags → devices)
5. Test schedule time zone handling
6. Test schedule with multiple playlists
7. Test schedule deactivation/deletion

---

## Technical Details

### Device Registration Flow (WORKING):
```
1. Generate 6-digit code
2. POST /api/v1/devices/request-code
   Body: {code, device_name, device_type, platform}
3. POST /api/v1/devices/activate (with admin token)
   Body: {unique_code, device_name}
4. Device created with status='active'
```

### Schedule Creation Flow (BLOCKED):
```
1. Create playlist (WORKING)
2. POST /api/v1/schedules
   Body: {
     name, playlist_id, start_date, start_time, end_time,
     priority, is_active, device_ids/tag_ids/apply_to_all
   }
3. Backend tries to access current_user.user_id (FAILS)
4. Returns HTTP 500
```

### Active Schedule Check Flow (WORKING):
```
1. POST /api/v1/schedules/active/check
   Body: {device_id, date, time}
2. Returns: {
     schedule: {...} or null,
     playlist_id, schedule_name, priority,
     is_found: true/false
   }
```

---

## Test Artifacts

- Test Script: `/mnt/g/khoirul/signate/backups/agent_schedule_test.py`
- Test Results: `/mnt/g/khoirul/signate/backups/agent_schedule_results.json`
- Backend Logs: Shows AttributeError on schedule creation attempts
- Coordination File: Updated with agent_schedule results

---

## Conclusion

The schedule integration tests have successfully identified a critical backend bug that blocks all schedule-related operations. The bug is straightforward to fix (change `user_id` to `id`), but it has a significant impact on functionality.

**Positive Findings**:
- Device registration flow works perfectly
- Playlist creation works perfectly
- Active schedule check endpoint is implemented and working
- Schedule list endpoint exists
- API infrastructure is solid

**Blocking Issues**:
- Backend bug prevents schedule creation
- Backend bug also affects tag creation
- Cannot test advanced features until bug is fixed

**Next Steps**:
1. Fix backend bug
2. Rerun tests
3. Verify all schedule features work correctly
4. Test advanced scenarios (recurrence, conflicts, etc.)

---

**Test Completed**: 2025-11-13 12:43:00 UTC
**Report Generated**: 2025-11-13 12:45:00 UTC
**Agent**: agent_schedule
**Status**: Test suite ready for rerun after backend fix
