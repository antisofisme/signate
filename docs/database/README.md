# Database Documentation

Dokumentasi untuk database schema, migrations, dan conventions.

## Files

### Standards & Conventions
- **DATABASE_CONVENTIONS.md** - Database naming conventions dan best practices (Grade A+)
- **DATABASE_ERD.md** - Entity Relationship Diagram (ERD) lengkap
- **DATABASE_SCHEMA_REVIEW.md** - Database schema review dan analysis
- **DATABASE_VERIFICATION_REPORT.md** - Database verification report

## Key Standards

### Naming Conventions
- **Tables**: Plural, snake_case (e.g., `users`, `device_commands`)
- **Primary Keys**: Always named `id`
- **Foreign Keys**: Always suffix `_id` (e.g., `user_id`, `organization_id`)
- **Timestamps**: Always suffix `_at` (e.g., `created_at`, `last_seen_at`)
- **Booleans**: Always prefix (e.g., `is_active`, `has_audio`, `can_edit`)
- **JSON Columns**: Descriptive plurals (e.g., `permissions`, `metadata`, `settings`)

### Audit Trail Standard
Every table with user actions includes:
```sql
created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
updated_at TIMESTAMP WITH TIME ZONE
```

### Multi-Tenancy Pattern
All core entities include:
```sql
organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE
```

## Database Schema
- **PostgreSQL 15.14**
- **29 tables**
- **45+ migrations**
- **Grade: A+ (100/100)**

## Related Documentation
- Backend Migrations: `/docs/backend-docs/MIGRATIONS.md`
- Backend Architecture: `/docs/backend-docs/ARCHITECTURE.md`
- API Documentation: `/docs/api/`

## Migration Files
Located in: `/backend-python/migrations/`

---

Last updated: 2025-11-26
