# Database Migrations

This directory contains the database migration files for the Digital Signage System.

## Migration Files

### Complete Schema
- `001_complete_schema.sql` - Original complete database schema with 29 tables
- `001_complete_schema_updated.sql` - Updated complete schema with 33 tables (includes analytics tables)

### Incremental Migrations
The following files are incremental migrations that were applied during development:

| File | Description | Status |
|------|-------------|--------|
| `002_add_organization_fields.sql` | Add fields to organizations table | Applied |
| `003_create_contents_table.sql` | Create contents table | Applied |
| `004_create_tags_tables.sql` | Create tags and content_tags tables | Applied |
| `005_create_playlists_tables.sql` | Create playlists and related tables | Applied |
| `006_create_devices_table.sql` | Create devices table | Applied |
| `007_create_content_assignments_table.sql` | Create content assignments table | Applied |
| `008_create_device_support_tables.sql` | Create device support tables | Applied |
| `009_add_roles_and_sessions.sql` | Add roles and user sessions tables | Applied |
| `010_add_device_logs_and_speed_tests.sql` | Add device logs and speed tests | Applied |
| `011_add_content_playback_logs.sql` | Add content playback logs | Applied |
| `012_add_device_groups.sql` | Add device groups | Applied |
| `013_add_device_commands.sql` | Add device commands | Applied |
| `014_add_device_health_metrics.sql` | Add device health metrics | Applied |
| `015_add_pms_integration.sql` | Add PMS integration tables | Applied |
| `016_add_templates.sql` | Add templates table | Applied |
| `017_add_translations.sql` | Add translations table | Applied |
| `018_add_schedules.sql` | Add advanced scheduling | Applied |
| `019_add_widgets.sql` | Add widgets tables | Applied |
| `020_add_audit_logs.sql` | Add audit logs table | Applied |
| `021_add_analytics_tables.sql` | Add analytics tables | Applied |
| `022_add_device_group_enhancements.sql` | Add device group hierarchy and stats | Applied |

### Archived Migrations
The following files have been archived as they are duplicates or were superseded:
- Files in `_archived/` directory

## Running Migrations

### Fresh Installation
For a fresh installation, run the complete schema:
```bash
docker exec -i signage-postgres psql -U signage_user -d signage_db < migrations/001_complete_schema.sql
```

### Incremental Updates
For existing installations, run only the migrations newer than your current version.

## Migration Conventions

1. **Naming**: `XXX_description.sql` where XXX is a 3-digit sequence number
2. **Content**: Each migration should be idempotent using `IF NOT EXISTS` clauses
3. **Rollback**: Complex migrations should include rollback instructions in comments
4. **Dependencies**: Migrations must be runnable in sequence order

## Current Schema Version

The complete schema includes:
- Original: `001_complete_schema.sql` - 29 tables (up to migration 020)
- Updated: `001_complete_schema_updated.sql` - 33 tables (includes analytics, up to migration 022)

## Tables Overview

1. **Core Tables** (11 tables)
   - organizations, roles, users, user_sessions
   - devices, device_groups, device_group_members
   - contents, tags, content_tags, device_tags

2. **Playlist System** (4 tables)
   - playlists, playlist_contents, playlist_assignments, playlist_widgets

3. **Assignment & Scheduling** (3 tables)
   - content_assignments, schedules, device_commands

4. **Monitoring & Logs** (5 tables)
   - device_logs, device_speed_tests, device_health_metrics
   - content_playback_logs, audit_logs

5. **Advanced Features** (6 tables)
   - templates, translations, widgets
   - pms_configurations, pms_rooms, pms_guests

6. **Analytics Tables** (4 tables)
   - content_performance, device_engagement
   - device_group_hierarchy, device_group_stats

Total: 33 tables with proper indexes and constraints.