---
description: Create database model/table for PROJECT_BESAR
---

# Flow A1: Create Database Model

## Pre-requisites
- [ ] Entity name defined
- [ ] Fields identified
- [ ] Relationships mapped

## Step 1: Design Model
**Standards**: #2 Database, #29 Multi-tenancy

Required fields:
```python
id: UUID (primary key)
tenant_id: UUID (WAJIB, indexed)
created_at: DateTime
updated_at: DateTime
is_deleted: Boolean (default False)
deleted_at: DateTime (nullable)
created_by: UUID (nullable)
updated_by: UUID (nullable)
```

## Step 2: Create SQLAlchemy Model
Location: `modules/{module}/backend/app/models/{entity}.py`

```python
from app.models.base import ModuleBaseModel
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

class {Entity}(ModuleBaseModel):
    __tablename__ = "{entities}"

    # Add entity-specific fields
    name = Column(String(100), nullable=False)
    # ... other fields
```

## Step 3: Create Migration
```bash
alembic revision --autogenerate -m "create_{entities}_table"
```

## Step 4: Verify Migration
- [ ] Table name is plural snake_case
- [ ] tenant_id column exists with index
- [ ] All required fields present
- [ ] Foreign keys defined correctly
- [ ] Indexes for common queries

## Step 5: Run Migration
```bash
alembic upgrade head
```

## Checklist Before Complete
- [ ] Model follows naming convention
- [ ] tenant_id present and indexed
- [ ] Soft delete fields present
- [ ] Audit fields present
- [ ] Migration tested
