---
description: Database migration checklist for PROJECT_BESAR
---

# Migration Checklist

## Pre-Migration
- [ ] Backup database production (jika applicable)
- [ ] Test migration di development
- [ ] Test migration di staging
- [ ] Review migration script

## Migration Script Check
- [ ] Nama file: `{revision}_{description}.py`
- [ ] Revision ID unique
- [ ] downgrade() function ada dan benar
- [ ] Tidak ada data loss pada downgrade

## Schema Check
- [ ] UUID untuk primary key
- [ ] tenant_id column dengan index
- [ ] created_at, updated_at columns
- [ ] is_deleted, deleted_at columns
- [ ] Proper foreign key constraints
- [ ] Index pada columns yang sering di-query

## Data Migration (jika ada)
- [ ] Batch processing untuk large data
- [ ] Tidak blocking production
- [ ] Rollback plan ready

## Post-Migration
- [ ] Verify schema changes applied
- [ ] Test aplikasi dengan schema baru
- [ ] Monitor error logs
- [ ] Performance check

## Migration Commands
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Run migration
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current revision
alembic current

# Check history
alembic history
```

## Common Issues
1. **Constraint error**: Check existing data compatibility
2. **Timeout**: Batch large data migrations
3. **Lock contention**: Run during low traffic
4. **Missing index**: Add index dalam migration terpisah
