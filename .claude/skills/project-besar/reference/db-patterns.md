---
description: Database patterns for PROJECT_BESAR
---

# Database Patterns Reference

## Base Model (WAJIB)
```python
class BaseModel:
    id: UUID              # Primary key
    tenant_id: UUID       # Multi-tenancy (INDEXED)
    created_at: DateTime  # Auto
    updated_at: DateTime  # Auto on update
    is_deleted: Boolean   # Soft delete (default False)
    deleted_at: DateTime  # Nullable
    created_by: UUID      # Nullable
    updated_by: UUID      # Nullable
```

## SQLAlchemy Model
```python
from sqlalchemy import Column, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Entity fields
    name = Column(String(100), nullable=False)
```

## Query Patterns

### Always Filter by tenant_id
```python
# WRONG
select(Entity).where(Entity.id == id)

# RIGHT
select(Entity).where(
    Entity.id == id,
    Entity.tenant_id == tenant_id,
    Entity.is_deleted == False
)
```

### Soft Delete
```python
async def delete(self, id: UUID, tenant_id: UUID):
    entity = await self.get(id, tenant_id)
    entity.is_deleted = True
    entity.deleted_at = datetime.utcnow()
    await self.db.commit()
```

### Pagination
```python
async def list(self, tenant_id: UUID, page: int, per_page: int):
    query = (
        select(Entity)
        .where(Entity.tenant_id == tenant_id)
        .where(Entity.is_deleted == False)
        .order_by(Entity.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return await self.db.execute(query)
```

## Index Guidelines
```python
# Always index
Index('ix_entity_tenant', 'tenant_id')

# Common query patterns
Index('ix_entity_tenant_status', 'tenant_id', 'status')

# Foreign keys
Index('ix_entity_parent_id', 'parent_id')
```

## Migration Template
```python
def upgrade():
    op.create_table(
        'entities',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('tenant_id', UUID, nullable=False),
        sa.Column('created_at', sa.DateTime),
        sa.Column('is_deleted', sa.Boolean, default=False),
        # ... other columns
    )
    op.create_index('ix_entities_tenant', 'entities', ['tenant_id'])
```
