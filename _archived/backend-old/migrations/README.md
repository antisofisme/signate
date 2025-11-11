# Database Migrations

This directory contains SQL migration files that are automatically executed when the backend container starts.

## How It Works

The migration system automatically:
1. Waits for PostgreSQL to be ready
2. Creates a `schema_migrations` tracking table
3. Checks which migrations have been applied
4. Runs any pending migrations in order
5. Records migration status (success/failure)
6. Starts the FastAPI application

## Migration File Naming Convention

Migration files must follow this naming pattern:
```
XXX_descriptive_name.sql
```

Where:
- `XXX` = 3-digit version number (e.g., `001`, `002`, `003`)
- `descriptive_name` = Brief description of the migration
- `.sql` = SQL file extension

### Examples:
- `001_create_playlist_tables.sql`
- `002_enhance_content_assignment_system.sql`
- `003_hotel_integration_foundation.sql`

## Current Migrations

| Version | Filename | Description |
|---------|----------|-------------|
| 001 | create_playlist_tables.sql | Create playlists, playlist_content, and playlist_assignments tables |
| 002 | enhance_content_assignment_system.sql | Add content assignment enhancements |
| 003 | hotel_integration_foundation.sql | Add hotel-specific features (PMS integration, guest mapping, etc.) |
| 004 | create_activity_logs.sql | Create activity_logs table for audit logging |
| 005 | add_speed_test_history.sql | Create device_speed_tests table |
| 006 | create_firebird_config.sql | Create firebird_config table for external DB integration |
| 007 | rename_content_to_contents.sql | Rename content table to contents for consistency |

## Adding New Migrations

1. **Create a new migration file** with the next version number:
   ```bash
   touch migrations/008_your_migration_name.sql
   ```

2. **Write your SQL migration**:
   ```sql
   -- Migration: Your Migration Description
   -- Date: YYYY-MM-DD
   -- Description: Detailed explanation

   BEGIN;

   -- Your SQL statements here
   CREATE TABLE IF NOT EXISTS your_table (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100) NOT NULL
   );

   COMMIT;
   ```

3. **Test locally**:
   ```bash
   docker-compose down
   docker-compose up -d --build backend-api
   docker logs -f signage-backend
   ```

4. **Verify migration**:
   ```bash
   docker exec signage-postgres psql -U signage_user -d signage_db \
       -c "SELECT * FROM schema_migrations ORDER BY version;"
   ```

## Migration Tracking Table

The system creates a `schema_migrations` table to track applied migrations:

```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version INTEGER UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE
);
```

## Manual Migration Execution

If you need to run migrations manually:

```bash
# Inside the container
docker exec -it signage-backend python scripts/run_migrations.py

# Or directly via psql
docker exec -i signage-postgres psql -U signage_user -d signage_db < migrations/XXX_migration.sql
```

## Rollback Migrations

Rollback scripts should be created separately with naming:
```
XXX_rollback_your_migration_name.sql
```

Example:
- Forward: `007_rename_content_to_contents.sql`
- Rollback: `007_rollback_rename_contents_to_content.sql`

## Best Practices

1. **Always use transactions** (BEGIN/COMMIT)
2. **Use IF NOT EXISTS** for CREATE statements
3. **Test rollback scripts** before production
4. **Document complex migrations** with comments
5. **Keep migrations idempotent** (safe to run multiple times)
6. **Version control all migrations** in Git

## Troubleshooting

### Migration Failed

Check logs:
```bash
docker logs signage-backend | grep migration
```

Check migration status:
```bash
docker exec signage-postgres psql -U signage_user -d signage_db \
    -c "SELECT * FROM schema_migrations WHERE success = FALSE;"
```

### Reset All Migrations

⚠️ **DANGER**: This will drop and recreate the database!

```bash
# Stop backend
docker stop signage-backend

# Drop and recreate database
docker exec signage-postgres psql -U signage_user -d postgres -c "DROP DATABASE signage_db;"
docker exec signage-postgres psql -U signage_user -d postgres -c "CREATE DATABASE signage_db OWNER signage_user;"

# Restart backend (migrations will run automatically)
docker start signage-backend
```

## Environment Variables

The migration system uses these environment variables:
- `DATABASE_URL` - PostgreSQL connection string (from .env)
- `ENVIRONMENT` - Environment name (development/production)

## Files

- `migrations/*.sql` - Migration SQL files
- `scripts/run_migrations.py` - Migration runner script
- `scripts/docker-entrypoint.sh` - Container entrypoint that runs migrations
- `Dockerfile` - Includes migrations in container build
