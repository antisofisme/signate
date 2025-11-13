# Database Backup Information

**Date**: 2025-11-13 18:52:52
**Database**: signage_db (PostgreSQL 15.14)
**Server**: 192.168.5.12
**Container**: signage-postgres

---

## Backup Files

### Main Backup (SQL)
- **File**: `signage_db_backup_20251113_185252.sql`
- **Size**: 222 KB
- **Format**: Plain SQL with DROP/CREATE statements
- **Options**: `--clean --if-exists`

### Compressed Backup
- **File**: `signage_db_backup_20251113_185252.tar.gz`
- **Size**: 31 KB (86% compression)
- **Format**: Gzip compressed tar archive

---

## Database Contents

### Total Tables: 29

1. audit_logs
2. content_assignments
3. content_playback_logs
4. content_tags
5. contents
6. device_commands
7. device_group_members
8. device_groups
9. device_health_metrics
10. device_logs
11. device_speed_tests
12. device_tags
13. devices
14. organizations
15. playlist_assignments
16. playlist_contents
17. playlist_widgets
18. playlists
19. pms_configurations
20. pms_guests
21. pms_rooms
22. roles
23. schedules
24. tags
25. templates
26. translations
27. user_sessions
28. users
29. widgets

---

## Backup Command Used

```bash
docker exec signage-postgres pg_dump \
  -U signage_user \
  -d signage_db \
  --clean \
  --if-exists \
  > signage_db_backup_20251113_185252.sql
```

---

## Restore Instructions

### Full Restore (Clean Database)
```bash
# Stop backend service first
cd /home/gzjbbk/signage
docker-compose -f docker/docker-compose.yml stop backend-api

# Restore database
cat signage_db_backup_20251113_185252.sql | \
  docker exec -i signage-postgres psql -U signage_user -d signage_db

# Start backend service
docker-compose -f docker/docker-compose.yml start backend-api
```

### Restore from Compressed Backup
```bash
# Extract and restore
tar -xzf signage_db_backup_20251113_185252.tar.gz
cat signage_db_backup_20251113_185252.sql | \
  docker exec -i signage-postgres psql -U signage_user -d signage_db
```

### Restore from Local Machine to Server
```bash
# Upload backup to server
sshpass -p 'Password@2021' scp \
  signage_db_backup_20251113_185252.sql \
  gzjbbk@192.168.5.12:/tmp/

# SSH to server and restore
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cat /tmp/signage_db_backup_20251113_185252.sql | \
   docker exec -i signage-postgres psql -U signage_user -d signage_db"
```

---

## Backup Contains

### Schema
- All table definitions (CREATE TABLE)
- All indexes (CREATE INDEX)
- All foreign keys (ALTER TABLE ADD CONSTRAINT)
- All sequences (CREATE SEQUENCE)
- Row-level security policies (CREATE POLICY)

### Data
- All table data (INSERT statements)
- Default roles (super_admin, admin, user)
- Admin user credentials
- Organization data
- Device data
- Content data
- Playlist data
- All configuration data

---

## Important Notes

1. **Backup includes `--clean --if-exists`**
   - Drops existing objects before creating
   - Safe for fresh restore
   - Use with caution on production

2. **No pg_dump warnings** - Clean backup without errors

3. **Size**: 222 KB uncompressed, 31 KB compressed
   - Indicates moderate amount of data
   - Fast backup/restore times

4. **PostgreSQL Version**: 15.14
   - Compatible with PostgreSQL 15.x and newer
   - May need adjustment for older versions

5. **Credentials in Backup**
   - Admin password hash included
   - Keep backup file secure
   - Don't commit to public repositories

---

## Backup Schedule Recommendation

### Daily Backups
```bash
# Add to crontab on server
0 2 * * * /home/gzjbbk/signate/scripts/backup_database.sh
```

### Retention Policy
- Daily backups: Keep last 7 days
- Weekly backups: Keep last 4 weeks
- Monthly backups: Keep last 6 months

---

## Verification

Backup integrity verified:
- ✅ Valid SQL syntax
- ✅ All 29 tables present
- ✅ DROP/CREATE statements correct
- ✅ No pg_dump errors
- ✅ Compressed successfully

**Backup Status**: ✅ GOOD - Ready for restore if needed
