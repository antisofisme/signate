# API Breaking Changes Documentation
## Database Standardization Migrations 039-044

**Date**: 2025-11-13
**Affected API Version**: v1
**Impact Level**: HIGH - Breaking changes in response schemas

---

## Overview

Migrations 039-044 standardized database column naming, resulting in changes to API response schemas. All endpoints returning affected entities now use new column names.

### Migration Summary

| Migration | Type | Columns Affected | API Impact |
|-----------|------|------------------|------------|
| 039 | FK naming | 13 columns | Response field names changed |
| 040 | Data cleanup | 1 column removed | users.role removed from responses |
| 041 | Column rename | 1 column | organizations.pin renamed |
| 042 | Timestamp naming | 6 columns | Timestamp field names changed |
| 043 | Boolean naming | 3 columns | Boolean field names changed |
| 044 | Constraints | 0 columns | No API changes (validation only) |

---

## Breaking Changes by Endpoint

### 1. Authentication Endpoints

#### POST `/api/v1/auth/login`

**Changed Response Fields**:
```json
// OLD
{
  "user": {
    "role": "ADMIN"  // ❌ Removed
  }
}

// NEW
{
  "user": {
    "role": "ADMIN"  // ✅ Still present (from role join)
  }
}
```

**Note**: `role` field is now populated by joining with `roles` table using `role_id` FK. Frontend sees no difference, but backend implementation changed.

**Migration**: 040

---

### 2. Device Endpoints

#### GET `/api/v1/devices`
#### GET `/api/v1/devices/{id}`

**Changed Response Fields**:
```json
// OLD Response
{
  "id": 1,
  "created_by": 9,              // ❌ Changed
  "updated_by": 9,              // ❌ Changed
  "last_seen": "2025-11-13...", // ❌ Changed
  "volume_enabled": true,       // ❌ Changed
  "supports_personalization": false  // ❌ Changed
}

// NEW Response
{
  "id": 1,
  "created_by_id": 9,                    // ✅ Added _id suffix
  "updated_by_id": 9,                    // ✅ Added _id suffix
  "last_seen_at": "2025-11-13...",      // ✅ Added _at suffix
  "is_volume_enabled": true,             // ✅ Added is_ prefix
  "is_personalization_supported": false  // ✅ Added is_ prefix
}
```

**Migrations**: 039 (FK), 042 (timestamp), 043 (boolean)

**Frontend Updates Required**:
```typescript
// OLD
device.created_by
device.last_seen
device.volume_enabled
device.supports_personalization

// NEW
device.created_by_id
device.last_seen_at
device.is_volume_enabled
device.is_personalization_supported
```

---

#### GET `/api/v1/devices/{id}/health`

**Changed Response Fields**:
```json
// OLD
{
  "device_id": 1,
  "alert_triggered": false  // ❌ Changed
}

// NEW
{
  "device_id": 1,
  "is_alert_triggered": false  // ✅ Added is_ prefix
}
```

**Migration**: 043

---

#### GET `/api/v1/devices/{id}/logs`

**Changed Response Fields**:
```json
// OLD
{
  "logs": [
    {
      "timestamp": "2025-11-13...",  // ❌ Changed
      "message": "Device started"
    }
  ]
}

// NEW
{
  "logs": [
    {
      "recorded_at": "2025-11-13...",  // ✅ More descriptive
      "message": "Device started"
    }
  ]
}
```

**Migration**: 042

---

### 3. Content Endpoints

#### GET `/api/v1/contents`
#### GET `/api/v1/contents/{id}`

**Changed Response Fields**:
```json
// OLD
{
  "id": 1,
  "uploaded_by": 9,          // ❌ Changed
  "created_by": 9,           // ❌ Changed
  "last_updated": "2025..."  // ❌ Changed (was already updated_at in some places)
}

// NEW
{
  "id": 1,
  "uploaded_by_id": 9,       // ✅ Added _id suffix
  "created_by_id": 9,        // ✅ Added _id suffix
  "updated_at": "2025..."    // ✅ Consistent with other tables
}
```

**Migrations**: 039, 042

---

### 4. Playlist Endpoints

#### GET `/api/v1/playlists`
#### GET `/api/v1/playlists/{id}`

**Changed Response Fields**:
```json
// OLD
{
  "id": 1,
  "created_by": 9  // ❌ Changed
}

// NEW
{
  "id": 1,
  "created_by_id": 9  // ✅ Added _id suffix
}
```

**Migration**: 039

---

### 5. Schedule Endpoints

#### GET `/api/v1/schedules`
#### GET `/api/v1/schedules/{id}`

**Changed Response Fields**:
```json
// OLD
{
  "id": 1,
  "created_by": 9  // ❌ Changed
}

// NEW
{
  "id": 1,
  "created_by_id": 9  // ✅ Added _id suffix
}
```

**Migration**: 039

---

### 6. User Session Endpoints

#### GET `/api/v1/sessions`
#### GET `/api/v1/sessions/{id}`

**Changed Response Fields**:
```json
// OLD
{
  "id": 1,
  "last_activity": "2025-11-13..."  // ❌ Changed
}

// NEW
{
  "id": 1,
  "last_activity_at": "2025-11-13..."  // ✅ Added _at suffix
}
```

**Migration**: 042

---

### 7. Organization Endpoints

#### GET `/api/v1/organizations`
#### GET `/api/v1/organizations/{id}`

**Changed Response Fields**:
```json
// OLD
{
  "id": 1,
  "organization_pin": "ABC123"  // ❌ Changed
}

// NEW
{
  "id": 1,
  "pin": "ABC123"  // ✅ Simplified name
}
```

**Migration**: 041

---

### 8. PMS Endpoints

#### GET `/api/v1/pms/guests`
#### GET `/api/v1/pms/stats`

**Changed Response Fields**:
```json
// OLD
{
  "last_sync": "2025-11-13..."  // ❌ Changed
}

// NEW
{
  "last_synced_at": "2025-11-13..."  // ✅ Added _at suffix
}
```

**Migration**: 042

---

### 9. Device Commands Endpoints

#### GET `/api/v1/devices/{id}/commands`
#### POST `/api/v1/devices/{id}/commands`

**Changed Response Fields**:
```json
// OLD
{
  "id": 1,
  "created_by": 9  // ❌ Changed
}

// NEW
{
  "id": 1,
  "created_by_id": 9  // ✅ Added _id suffix
}
```

**Migration**: 039

---

### 10. Tag Assignment Endpoints

#### POST `/api/v1/devices/{id}/tags`
#### POST `/api/v1/contents/{id}/tags`

**Changed Response Fields**:
```json
// OLD
{
  "assigned_by": 9  // ❌ Changed
}

// NEW
{
  "assigned_by_id": 9  // ✅ Added _id suffix
}
```

**Migration**: 039

---

## Complete Field Name Mapping

### Foreign Keys (Migration 039)

| Old Field Name | New Field Name | Affected Endpoints |
|----------------|----------------|--------------------|
| `created_by` | `created_by_id` | devices, contents, playlists, schedules, templates, widgets, device_groups, device_commands, pms_configurations |
| `updated_by` | `updated_by_id` | devices |
| `assigned_by` | `assigned_by_id` | device_tags, content_assignments |
| `uploaded_by` | `uploaded_by_id` | contents |
| `added_by` | `added_by_id` | device_group_members |

### Timestamps (Migration 042)

| Old Field Name | New Field Name | Affected Endpoints |
|----------------|----------------|--------------------|
| `last_seen` | `last_seen_at` | devices |
| `last_activity` | `last_activity_at` | user_sessions |
| `timestamp` | `recorded_at` | device_logs |
| `last_sync` | `last_synced_at` | pms_configurations, pms_stats |

### Booleans (Migration 043)

| Old Field Name | New Field Name | Affected Endpoints |
|----------------|----------------|--------------------|
| `volume_enabled` | `is_volume_enabled` | devices |
| `supports_personalization` | `is_personalization_supported` | devices |
| `alert_triggered` | `is_alert_triggered` | device_health_metrics |

### Other (Migration 041)

| Old Field Name | New Field Name | Affected Endpoints |
|----------------|----------------|--------------------|
| `organization_pin` | `pin` | organizations |

---

## Frontend Migration Guide

### TypeScript Type Updates

```typescript
// OLD types
interface Device {
  id: number;
  created_by: number;
  updated_by: number;
  last_seen: string;
  volume_enabled: boolean;
  supports_personalization: boolean;
}

// NEW types
interface Device {
  id: number;
  created_by_id: number;
  updated_by_id: number;
  last_seen_at: string;
  is_volume_enabled: boolean;
  is_personalization_supported: boolean;
}
```

### React Query Updates

```typescript
// Update your API response types
import { Device } from '@/types/device';

// The API will automatically return new field names
const { data: devices } = useQuery<Device[]>({
  queryKey: ['devices'],
  queryFn: fetchDevices
});

// Access with new names
console.log(devices[0].last_seen_at);  // ✅
console.log(devices[0].last_seen);     // ❌ Will be undefined
```

### Form Submission Updates

```typescript
// OLD - POST /api/v1/devices
const createDevice = {
  volume_enabled: true,
  supports_personalization: false
};

// NEW - POST /api/v1/devices
const createDevice = {
  is_volume_enabled: true,
  is_personalization_supported: false
};
```

---

## Mobile App Migration Guide

### Swift/iOS Updates

```swift
// OLD model
struct Device: Codable {
    let id: Int
    let createdBy: Int
    let lastSeen: String
    let volumeEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case createdBy = "created_by"      // ❌ Old
        case lastSeen = "last_seen"        // ❌ Old
        case volumeEnabled = "volume_enabled"  // ❌ Old
    }
}

// NEW model
struct Device: Codable {
    let id: Int
    let createdById: Int
    let lastSeenAt: String
    let isVolumeEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case createdById = "created_by_id"          // ✅ New
        case lastSeenAt = "last_seen_at"            // ✅ New
        case isVolumeEnabled = "is_volume_enabled"  // ✅ New
    }
}
```

### Kotlin/Android Updates

```kotlin
// OLD model
data class Device(
    val id: Int,
    @SerializedName("created_by") val createdBy: Int,      // ❌ Old
    @SerializedName("last_seen") val lastSeen: String,      // ❌ Old
    @SerializedName("volume_enabled") val volumeEnabled: Boolean  // ❌ Old
)

// NEW model
data class Device(
    val id: Int,
    @SerializedName("created_by_id") val createdById: Int,              // ✅ New
    @SerializedName("last_seen_at") val lastSeenAt: String,            // ✅ New
    @SerializedName("is_volume_enabled") val isVolumeEnabled: Boolean  // ✅ New
)
```

---

## Testing Checklist

### Backend Verification
- [ ] All endpoints return 200 OK
- [ ] Response schemas match new field names
- [ ] No references to old field names in responses
- [ ] Database queries use new column names
- [ ] Foreign key relationships still work

### Frontend Verification
- [ ] TypeScript types updated
- [ ] All API calls use new field names
- [ ] Forms submit with new field names
- [ ] Display components use new field names
- [ ] No console errors for undefined fields

### Integration Testing
- [ ] Login flow works
- [ ] Device registration works
- [ ] Content upload works
- [ ] Playlist creation works
- [ ] Tag assignment works
- [ ] Real-time updates work (WebSocket)

---

## Rollback Procedure

If issues arise, you can rollback using the database backup:

```bash
# 1. Stop backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml stop backend-api"

# 2. Restore backup
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db" \
  < backups/pre_migration_039_YYYYMMDD_HHMMSS.sql

# 3. Revert code
git checkout backend-python/

# 4. Restart backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml start backend-api"
```

---

## API Versioning Consideration

For future major schema changes, consider:

1. **API Versioning**: Create `/api/v2/` with new schema
2. **Deprecation Notices**: Add deprecation warnings to old endpoints
3. **Dual Support**: Temporarily support both old and new field names
4. **Migration Period**: Give clients time to migrate (e.g., 3 months)

Example dual support:
```python
@router.get("/devices")
def get_devices():
    devices = device_repo.get_all()
    return {
        "items": [
            {
                # New names (preferred)
                "created_by_id": d.created_by_id,
                "last_seen_at": d.last_seen_at,

                # Old names (deprecated - for backward compatibility)
                "created_by": d.created_by_id,  # Duplicate
                "last_seen": d.last_seen_at,    # Duplicate

                # Deprecation warning in header
            }
            for d in devices
        ],
        "deprecation_notice": "Fields 'created_by' and 'last_seen' are deprecated. Use '*_id' and '*_at' versions."
    }
```

---

## Support & Questions

- **API Documentation**: http://192.168.5.12:8001/docs
- **Database ERD**: `docs/DATABASE_ERD.md`
- **Naming Conventions**: `docs/DATABASE_CONVENTIONS.md`
- **Deployment Report**: `DEPLOYMENT_SUCCESS_REPORT.md`

---

**Last Updated**: 2025-11-13
**Deployment Status**: ✅ DEPLOYED TO PRODUCTION
**Backend Version**: 3.0 (with standardized naming)
