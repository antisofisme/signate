# Migration Status - Backend Testing Fixes

**Date**: 2025-11-13
**Purpose**: Track which fixes from backend testing have corresponding migration files

---

## Summary of Fixes During Testing (Nov 12-13)

### Database Schema Changes Made:

1. **Organizations Table** - Quota Management
   - Added: `max_devices INTEGER DEFAULT 10`
   - Added: `max_users INTEGER DEFAULT 5`
   - Added: `settings JSONB DEFAULT '{}'`

2. **Playlists Table** - Flags
   - Added: `is_default BOOLEAN DEFAULT FALSE`
   - Added: `is_pms_template BOOLEAN DEFAULT FALSE`

3. **Schedules Table** - Targeting
   - Added: `device_ids JSONB`
   - Added: `tag_ids JSONB`
   - Added: `apply_to_all BOOLEAN DEFAULT FALSE`

---

## Migration Files Status

| Fix | Migration File | Status | Notes |
|-----|---------------|--------|-------|
| Organization Quota | `038_add_organization_quota_fields.sql` | ✅ CREATED | Just created today |
| Playlist Flags | `031_add_playlist_flags.sql` | ✅ EXISTS | Created Nov 11 |
| Schedule Targeting | `028_add_schedule_targeting.sql` | ✅ EXISTS | Created Nov 11 |

---

## Code Fixes (No Migration Required)

These fixes were code changes only, no database schema changes:

1. **WIDGET Service** - CurrentUser object access
   - File: `backend-python/services/widget/routes.py`
   - Fix: Changed `current_user["field"]` to `current_user.field`
   - Migration: ❌ NOT NEEDED (code fix only)

2. **SCHEDULE Service** - CurrentUser object access
   - File: `backend-python/services/schedule/routes.py`
   - Fix: Changed `current_user["field"]` to `current_user.field`
   - Migration: ❌ NOT NEEDED (code fix only)

3. **TEMPLATE Service** - CurrentUser object access
   - File: `backend-python/services/template/routes.py`
   - Fix: Changed `current_user["field"]` to `current_user.field`
   - Migration: ❌ NOT NEEDED (code fix only)

4. **TRANSLATION Service** - CurrentUser + Route Order
   - File: `backend-python/services/translation/routes.py`
   - Fix: Changed `current_user["field"]` to `current_user.field` + reordered routes
   - Migration: ❌ NOT NEEDED (code fix only)

5. **Schedule Model** - Uncommented Relationship
   - File: `backend-python/services/schedule/repositories/models.py`
   - Fix: Uncommented `playlist = relationship("PlaylistModel", ...)`
   - Migration: ❌ NOT NEEDED (code fix only)

6. **Import Path Fixes**
   - Files: `backend-python/services/organization/use_cases/quota_service.py`, `routes.py`
   - Fix: Changed imports from `services.organization.repositories.models` to `services.auth.repositories.models`
   - Migration: ❌ NOT NEEDED (code fix only)

---

## Migration Files in `/backend-python/migrations/`

### Complete List (38 files):

```
001_complete_schema.sql
001_complete_schema_updated.sql (⭐ Has all columns in organizations table)
002_add_organization_fields.sql
003_create_contents_table.sql
004_create_tags_tables.sql
005_create_playlists_tables.sql
006_create_devices_table.sql
007_create_content_assignments_table.sql
008_create_device_support_tables.sql
009_add_roles_and_sessions.sql
010_add_device_logs_and_speed_tests.sql
011_add_content_playback_logs.sql
012_add_device_groups.sql
013_add_device_commands.sql
014_add_device_health_metrics.sql
015_add_pms_integration.sql
016_add_templates.sql
017_add_translations.sql
018_add_schedules.sql
019_add_widgets.sql
020_add_audit_logs.sql
021_add_analytics_tables.sql
022_add_device_group_enhancements.sql
028_add_schedule_targeting.sql (✅ Schedule targeting columns)
029_add_tag_playlist_assignment.sql
030_add_device_playlist_assignment.sql
031_add_playlist_flags.sql (✅ Playlist flags)
032_performance_indexes.sql
033_fix_device_tag_relationships.sql
034_fix_tags_multi_tenant.sql
035_add_device_playlist_assignment.sql
036_fix_device_commands_schema.sql
037_fix_device_health_metrics_schema.sql
038_add_organization_quota_fields.sql (✅ NEW - Organization quotas)
```

---

## Verification Commands

### Check if migrations exist on server:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "ls -la /home/gzjbbk/signate/backend-python/migrations/ | tail -10"
```

### Sync new migration to server:
```bash
sshpass -p 'Password@2021' scp backend-python/migrations/038_add_organization_quota_fields.sql \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/migrations/
```

### Run migrations on server (if needed):
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "cd /home/gzjbbk/signate/backend-python/migrations && python3 run_migrations.py"
```

### Or run migration directly in database:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/038_add_organization_quota_fields.sql"
```

---

## Important Notes

1. **Migration 038** just created - needs to be synced to server
2. **Migrations 028 & 031** already exist from Nov 11 - should already be on server
3. **001_complete_schema_updated.sql** already has all columns defined correctly
4. Most fixes were **code-only** (no schema changes needed)
5. All database schema changes now have corresponding migration files

---

## Action Items

### ✅ COMPLETED:
- Created migration file for organization quota fields (038)
- Verified existing migrations for schedule targeting (028)
- Verified existing migrations for playlist flags (031)

### 🔄 TO DO:
- [ ] Sync migration 038 to production server
- [ ] Run migration 038 on server (or verify columns already exist)
- [ ] Document that code fixes don't need migrations

---

## Conclusion

**All database schema fixes from backend testing now have migration files:**
- ✅ Organization quota: `038_add_organization_quota_fields.sql` (NEW)
- ✅ Schedule targeting: `028_add_schedule_targeting.sql` (EXISTS)
- ✅ Playlist flags: `031_add_playlist_flags.sql` (EXISTS)

**Code fixes** (6 fixes) don't need migrations - they're code-only changes.

**Status**: ✅ COMPLETE - All fixes documented and migration files created
