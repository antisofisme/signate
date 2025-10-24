# Database Migrations

## 📋 Overview

Folder ini berisi SQL migrations untuk **production database** yang sudah running.

**PENTING:**
- `init.sql` adalah untuk **fresh database** (database baru)
- `migrations/` adalah untuk **existing database** (database production yang sudah ada data)

## 🔄 Kapan Pakai Migrations?

### Scenario 1: Fresh Database (Development)
```bash
# Pakai init.sql (otomatis via Docker)
./reset-database.sh
```

### Scenario 2: Production Database (Ada Data)
```bash
# Pakai migrations (manual apply)
./apply-migration.sh 001_add_uuid_support.sql
```

## 📝 Migration File Naming Convention

```
[number]_[descriptive_name].sql

Examples:
001_add_uuid_support.sql
002_add_indexes.sql
003_add_new_table.sql
```

**Rules:**
- Prefix dengan nomor urut (001, 002, 003...)
- Descriptive name (snake_case)
- Extension `.sql`

## 🛠️ Cara Membuat Migration Baru

### Step 1: Buat File Migration

```bash
cd database/migrations
nano 002_your_migration_name.sql
```

### Step 2: Tulis Migration SQL

```sql
-- =============================================================================
-- Migration 002: Your Migration Description
-- =============================================================================
-- Created: YYYY-MM-DD
-- Purpose: Describe what this migration does
-- =============================================================================

BEGIN;

-- Your SQL changes here
ALTER TABLE content ADD COLUMN new_field VARCHAR(100);

-- Verify changes
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'content' AND column_name = 'new_field';

COMMIT;

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
```

### Step 3: Test di Development

```bash
# Test di local/dev first
docker exec -i signage-postgres psql -U signage_user -d signage_db < 002_your_migration_name.sql
```

### Step 4: Apply ke Production

```bash
# Di server
ssh gzjbbk@192.168.5.12
cd /home/gzjbbk/signage/database/migrations
./apply-migration.sh 002_your_migration_name.sql
```

## ⚠️ Best Practices

1. **Always Backup First**
   ```bash
   ./backup-database.sh
   ```

2. **Use Transactions (BEGIN/COMMIT)**
   - Rollback otomatis jika ada error
   - Database tetap konsisten

3. **Add Verification Queries**
   - Verify changes berhasil
   - Debugging lebih mudah

4. **Test di Development Dulu**
   - Jangan langsung apply ke production
   - Test dulu di local

5. **Keep Migrations Small**
   - One migration = one logical change
   - Easier to debug and rollback

## 📚 Migration Workflow

```
┌─────────────────────────────────────────────┐
│  DEVELOPMENT                                │
├─────────────────────────────────────────────┤
│  1. Update init.sql (untuk fresh DB)       │
│  2. Create migration file (untuk existing) │
│  3. Test both scenarios                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  COMMIT TO GIT                              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  PRODUCTION                                 │
├─────────────────────────────────────────────┤
│  1. Backup database                        │
│  2. Apply migration                        │
│  3. Verify changes                         │
└─────────────────────────────────────────────┘
```

## 🔍 Tracking Applied Migrations

**Option 1: Manual Tracking (Current)**
- Keep notes of applied migrations
- Check database columns/tables

**Option 2: Migration Table (Future)**
```sql
CREATE TABLE schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📁 Struktur Database

```
database/
├── init.sql                    # Fresh database schema
├── migrations/                 # Production migrations
│   ├── README.md              # This file
│   ├── 001_add_uuid_support.sql
│   ├── 002_future_migration.sql
│   └── apply-migration.sh     # Helper script
└── backups/                   # Database backups
    └── backup_YYYYMMDD_HHMMSS.sql.gz
```

## 🆘 Troubleshooting

### Error: "relation already exists"
```bash
# Migration sudah pernah di-apply
# Check database state:
docker exec signage-postgres psql -U signage_user -d signage_db -c "\d table_name"
```

### Error: "syntax error"
```bash
# Check SQL syntax
# Test query by query di psql:
docker exec -it signage-postgres psql -U signage_user -d signage_db
```

### Need to Rollback
```bash
# Restore from backup
gunzip backup_YYYYMMDD_HHMMSS.sql.gz
docker exec -i signage-postgres psql -U signage_user -d signage_db < backup_YYYYMMDD_HHMMSS.sql
```

## 📞 Support

Jika ada pertanyaan tentang migrations:
1. Check this README
2. Check `apply-migration.sh` script
3. Check database state dengan psql
4. Restore from backup jika perlu
