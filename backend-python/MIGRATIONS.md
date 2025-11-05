# Database Migrations with Alembic

## Overview

This document explains how to set up and use database migrations with Alembic for this project.

## Why Use Migrations?

1. **Version Control**: Track all database schema changes in code
2. **Reproducibility**: Ensure consistent database schema across environments (dev, staging, production)
3. **Rollback**: Ability to undo schema changes if needed
4. **Team Collaboration**: Share schema changes through version control
5. **Documentation**: Migrations serve as a history of database changes

## Setup (First Time Only)

### 1. Install Dependencies

```bash
# In Docker container or virtual environment
pip install -r requirements.txt  # Alembic is already in requirements.txt
```

### 2. Initialize Alembic

```bash
cd backend-python
alembic init alembic
```

This creates:
- `alembic/` directory with migration scripts
- `alembic.ini` configuration file

### 3. Configure Alembic

Edit `alembic.ini`:

```ini
# Set database URL (or use environment variable)
sqlalchemy.url = postgresql://user:password@localhost:5433/signage_db
```

**Better approach**: Use environment variable (already configured in `.env`):

Edit `alembic/env.py`:

```python
# Add at the top
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import settings
from shared.database import Base

# Import all models so Alembic can detect them
from services.auth.repositories.models import User, Organization
from services.device.repositories.models import Device
from services.audit.repositories.models import AuditLog
# Add other model imports as they are created

# Update config
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

# Set target_metadata to our Base
target_metadata = Base.metadata
```

### 4. Create Initial Migration

For an existing database, create a migration that matches current schema:

```bash
# Generate migration from current models
alembic revision --autogenerate -m "Initial schema"

# Review the generated migration file in alembic/versions/
# Edit if necessary to match existing database exactly
```

### 5. Mark as Applied (For Existing Database)

If the database already exists and matches the models:

```bash
# Mark migration as applied without running it
alembic stamp head
```

This tells Alembic that the database is already at the latest version.

## Creating New Migrations

### 1. Modify Models

Make changes to your SQLAlchemy models (in `services/*/repositories/models.py`):

```python
# Example: Add new column to User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    # NEW COLUMN:
    phone_number = Column(String(20), nullable=True)
```

### 2. Generate Migration

```bash
alembic revision --autogenerate -m "Add phone number to users"
```

This creates a new migration file in `alembic/versions/` with:
- `upgrade()` function: applies the change
- `downgrade()` function: reverts the change

### 3. Review Migration

**IMPORTANT**: Always review auto-generated migrations!

```bash
# Open the generated file
cat alembic/versions/xxxx_add_phone_number_to_users.py
```

Check:
- Correct table and column names
- Proper data types
- Indexes and constraints
- Default values
- Nullable settings

### 4. Apply Migration

```bash
# Upgrade to latest version
alembic upgrade head

# Or upgrade one step at a time
alembic upgrade +1
```

### 5. Rollback if Needed

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## Common Migration Scenarios

### Adding a Column

```python
# In migration file
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
```

### Removing a Column

```python
def upgrade():
    op.drop_column('users', 'old_column')

def downgrade():
    op.add_column('users', sa.Column('old_column', sa.String(50), nullable=True))
```

### Renaming a Column

```python
def upgrade():
    op.alter_column('users', 'old_name', new_column_name='new_name')

def downgrade():
    op.alter_column('users', 'new_name', new_column_name='old_name')
```

### Adding an Index

```python
def upgrade():
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email', table_name='users')
```

### Adding a Foreign Key

```python
def upgrade():
    op.create_foreign_key(
        'fk_device_organization',
        'devices', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    op.drop_constraint('fk_device_organization', 'devices', type_='foreignkey')
```

### Data Migration

For migrations that require data changes:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Add new column
    op.add_column('users', sa.Column('role', sa.String(20), nullable=True))

    # Migrate data
    users_table = table('users',
        column('id', sa.Integer),
        column('role', sa.String)
    )
    op.execute(
        users_table.update().values(role='user')
    )

    # Make column non-nullable after data migration
    op.alter_column('users', 'role', nullable=False)

def downgrade():
    op.drop_column('users', 'role')
```

## Useful Commands

```bash
# Show current migration version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose

# Upgrade to specific version
alembic upgrade <revision_id>

# Show SQL without executing
alembic upgrade head --sql

# Create empty migration (for custom SQL)
alembic revision -m "custom changes"
```

## Integration with Docker

Add to `docker-compose.yml`:

```yaml
services:
  backend-api:
    build: ./backend
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

This runs migrations automatically when the container starts.

## Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations** on a copy of production data
3. **Never edit applied migrations** - create a new one instead
4. **Write reversible migrations** when possible
5. **Backup database** before applying migrations in production
6. **Use descriptive migration messages**: "Add user phone number" not "Update users"
7. **One migration per logical change** - don't bundle unrelated changes
8. **Test downgrade** as well as upgrade
9. **Commit migrations to version control** immediately
10. **Document complex migrations** with comments

## Production Deployment Workflow

```bash
# 1. On development machine
git pull
alembic upgrade head  # Test locally first

# 2. Commit and push
git add alembic/versions/
git commit -m "Add migration: user phone number"
git push

# 3. On production server
git pull

# 4. Backup database
docker exec signage-postgres pg_dump -U signage_user signage_db > backup.sql

# 5. Run migration
docker exec signage-backend alembic upgrade head

# 6. Verify
docker exec signage-backend alembic current

# 7. If something goes wrong, rollback
docker exec signage-backend alembic downgrade -1
```

## Troubleshooting

### Migration Conflicts

If multiple developers create migrations simultaneously:

```bash
# Merge migrations
alembic merge <rev1> <rev2> -m "merge migrations"
```

### Migration Out of Sync

If database is out of sync with migrations:

```bash
# Check current database schema
docker exec signage-postgres psql -U signage_user -d signage_db -c "\d users"

# Check what Alembic thinks is current
alembic current

# Manually set to correct version if needed
alembic stamp <revision_id>
```

### Failed Migration

```bash
# Rollback
alembic downgrade -1

# Fix the migration file
# Re-run
alembic upgrade head
```

## Security Considerations

1. **Sensitive Data**: Never log sensitive data in migrations
2. **Access Control**: Migrations run with database admin privileges - be careful
3. **Validation**: Validate data before and after migrations
4. **Audit Trail**: Log all production migrations
5. **Testing**: Always test migrations on staging before production

## Related Files

- `shared/database.py` - SQLAlchemy Base and engine configuration
- `services/*/repositories/models.py` - Model definitions
- `alembic/versions/` - Migration files
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Alembic environment setup

## Future Improvements

- [ ] Automated migration testing in CI/CD
- [ ] Migration rollback scripts for production
- [ ] Data validation before/after migrations
- [ ] Automated database backups before migrations
- [ ] Migration preview/diff tool
