# Database Backups

## Latest Backups

### Schema Only
- `schema_YYYYMMDD_HHMMSS.sql` - Database schema (structure only, no data)
- Used for: Schema analysis, migration planning, structure documentation

### Full Backup
- `full_backup_YYYYMMDD_HHMMSS.sql` - Complete database dump (schema + data)
- Used for: Full restoration, data recovery, migration to new server

## Backup Policy

- Backups created: Daily or before major changes
- Old backups removed: After 7 days (keeping only latest)
- Location: G:\khoirul\signate\backups

## Restore Instructions

### Restore Schema Only
```bash
docker exec -i signage-postgres psql -U signage_user -d signage_db < schema_YYYYMMDD_HHMMSS.sql
```

### Restore Full Database
```bash
# Drop existing database (WARNING: Data loss!)
docker exec signage-postgres psql -U signage_user -c "DROP DATABASE signage_db;"
docker exec signage-postgres psql -U signage_user -c "CREATE DATABASE signage_db;"

# Restore
docker exec -i signage-postgres psql -U signage_user -d signage_db < full_backup_YYYYMMDD_HHMMSS.sql
```

## Database Info

- Database: signage_db
- User: signage_user
- Container: signage-postgres
- Port: 5433 (host) -> 5432 (container)
- PostgreSQL: 15.14

Last updated: $(date +%Y-%m-%d)
