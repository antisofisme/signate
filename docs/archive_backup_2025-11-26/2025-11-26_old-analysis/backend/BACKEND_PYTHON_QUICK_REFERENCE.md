# Backend-Python Quick Reference Guide

## Service Structure Template

When creating a new service, copy this structure:

```
services/[service_name]/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── [entity].py        # @dataclass entities (pure business logic)
│   └── interfaces.py       # Repository interfaces
├── repositories/
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy models HERE
│   └── [service]_repo.py   # Repository implementation
├── dtos.py                 # Pydantic models for API
├── routes.py               # FastAPI routes + DI
└── use_cases/
    ├── __init__.py
    └── [use_case].py       # One file per use case
```

## Database Models Checklist

When adding tables to `repositories/models.py`:

- [ ] Table name is plural, lowercase: `devices`, `contents`, `playlists`
- [ ] Column names are snake_case: `organization_id`, `device_uuid`, `last_seen`
- [ ] Has `id = Column(Integer, primary_key=True, index=True)`
- [ ] Has `organization_id` FK with `ondelete="CASCADE"` (for org-scoped data)
- [ ] Has timestamps:
  ```python
  created_at = Column(DateTime(timezone=True), server_default=func.now())
  updated_at = Column(DateTime(timezone=True), onupdate=func.now())
  deleted_at = Column(DateTime(timezone=True), nullable=True)  # if soft-delete
  ```
- [ ] Foreign keys use patterns:
  - Organization: `ForeignKey("organizations.id", ondelete="CASCADE")`
  - Users: `ForeignKey("users.id", ondelete="SET NULL")`
- [ ] Unique constraints where applicable: `unique=True` or `UNIQUE (org_id, name)`
- [ ] Important columns indexed: `index=True` on lookup fields

## Routes Checklist

In `shared/api_routes.py`:

- [ ] Add route class with BASE path
- [ ] Define CRUD operations: `LIST`, `CREATE`, `GET`, `UPDATE`, `DELETE`
- [ ] Define special actions if needed: `ACTIVATE`, `HEARTBEAT`, etc.
- [ ] Use consistent path pattern: `{service}/{id}` for detail routes

Example:
```python
class MyServiceRoutes:
    BASE = f"{API_V1}/my-service"
    LIST = BASE
    CREATE = BASE
    GET = f"{BASE}/{{id}}"
    UPDATE = f"{BASE}/{{id}}"
    DELETE = f"{BASE}/{{id}}"
    CUSTOM = f"{BASE}/{{id}}/custom-action"
```

## Routes Implementation Checklist

In `routes.py`:

- [ ] Import routes from `shared.api_routes`
- [ ] Create DI functions:
  ```python
  def get_my_repository(db: Session = Depends(get_db)) -> MyRepository:
      return MyRepository(db)
  
  def get_my_use_case(repo: MyRepository = Depends(get_my_repository)) -> MyUseCase:
      return MyUseCase(repo)
  ```
- [ ] Use `@router.post/get/put/delete(MyServiceRoutes.ACTION)`
- [ ] Add error handling: `@handle_errors` decorator
- [ ] Use standardized response: `success_response(data, message)`
- [ ] Log actions: `request_logger.log_request(...)` and `audit_logger.log_action(...)`

## Response Patterns

Success:
```python
return success_response(
    data=MyModel.model_validate(entity),
    message="Action completed successfully"
)
```

Error:
```python
from shared.errors import NotFoundError, ValidationError

raise NotFoundError(
    message="Resource not found",
    resource_type="my_service",
    resource_id=id
)
```

## DTOs Checklist

In `dtos.py`:

- [ ] Request DTOs: Input validation with Pydantic
  ```python
  class MyRequest(BaseModel):
      name: str = Field(..., max_length=200)
      description: Optional[str] = Field(None, max_length=1000)
  ```

- [ ] Response DTOs: Output models with timestamps
  ```python
  class MyResponse(BaseModel):
      id: int
      name: str
      created_at: datetime
      updated_at: Optional[datetime]
      
      class Config:
          from_attributes = True
  ```

## Domain Entities Checklist

In `domain/[entity].py`:

- [ ] Use `@dataclass` decorator
- [ ] Required fields (NO defaults) come FIRST
- [ ] Optional fields (NO defaults) come SECOND
- [ ] Fields WITH defaults come LAST
- [ ] Add validation in `__post_init__`
- [ ] Add helper methods: `is_active()`, `is_online()`, etc.
- [ ] Include value objects for complex values (immutable)

```python
@dataclass
class MyEntity:
    # Required (no defaults)
    id: Optional[int]
    name: str
    organization_id: int
    
    # Optional (no defaults)
    description: Optional[str]
    
    # With defaults (LAST)
    is_active: bool = True
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Name is required")
    
    def is_valid(self) -> bool:
        return len(self.name) > 0
```

## Repository Checklist

In `repositories/[service]_repo.py`:

- [ ] Implement interface: `class MyRepository(IMyRepository):`
- [ ] Implement all interface methods
- [ ] Add helper method: `_to_entity(model)` for mapping
- [ ] Use `self.db` for database access
- [ ] Follow pattern:
  ```python
  def find_by_id(self, id: int) -> Optional[MyEntity]:
      model = self.db.query(MyModel).filter(MyModel.id == id).first()
      return self._to_entity(model) if model else None
  ```

## Use Cases Checklist

In `use_cases/[action].py`:

- [ ] Single responsibility: one use case per file
- [ ] Constructor takes dependencies (repositories)
- [ ] Single `execute()` method with clear parameters
- [ ] Contains business logic (not just pass-through to repo)
- [ ] Raises appropriate exceptions on validation errors

```python
class MyUseCase:
    def __init__(self, repo: IMyRepository):
        self.repo = repo
    
    def execute(self, name: str, description: str = None) -> MyEntity:
        # Business logic here
        if not name:
            raise ValueError("Name is required")
        
        entity = MyEntity(
            id=None,
            name=name,
            description=description,
            organization_id=org_id
        )
        return self.repo.create(entity)
```

## Service Registration

In `main.py`:

- [ ] Import router: `from services.my_service.routes import router as my_router`
- [ ] Register with tag: `app.include_router(my_router, tags=["My Service"])`
- [ ] Routes will be available at paths from `shared/api_routes.py`

## Migrations

Next migration number: `006_[description].sql`

Template:
```sql
-- ============================================================================
-- Migration: [Description]
-- Created: 2025-11-XX
-- ============================================================================

CREATE TABLE IF NOT EXISTS [table] (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_[table]_organization ON [table](organization_id);
CREATE INDEX idx_[table]_key ON [table](organization_id, [unique_field]);

-- Run: docker exec -i signage-postgres psql -U signage_user -d signage_db < migration_file.sql
```

## Testing Local Changes

```bash
# Run backend locally
cd /mnt/g/khoirul/signate/backend-python
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Test endpoint
curl -X GET http://localhost:8001/api/v1/my-service
curl -X POST http://localhost:8001/api/v1/my-service \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
```

## Common Patterns

### Multi-tenant Query
```python
def list_by_organization(self, org_id: int) -> List[MyEntity]:
    models = self.db.query(MyModel).filter(
        MyModel.organization_id == org_id
    ).all()
    return [self._to_entity(m) for m in models]
```

### Soft Delete
```python
def soft_delete(self, id: int) -> bool:
    model = self.db.query(MyModel).filter(MyModel.id == id).first()
    if model:
        model.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    return False

def find_active(self, id: int) -> Optional[MyEntity]:
    model = self.db.query(MyModel).filter(
        MyModel.id == id,
        MyModel.deleted_at == None
    ).first()
    return self._to_entity(model) if model else None
```

### Pagination
```python
def list_paginated(self, org_id: int, page: int = 1, page_size: int = 10):
    skip = (page - 1) * page_size
    models = self.db.query(MyModel).filter(
        MyModel.organization_id == org_id
    ).offset(skip).limit(page_size).all()
    total = self.db.query(MyModel).filter(
        MyModel.organization_id == org_id
    ).count()
    return [self._to_entity(m) for m in models], total
```

## Troubleshooting

**Import Error: `from shared...`**
- Make sure you're importing from `shared`, not from parent directories
- Example: `from shared.database import get_db` (correct)

**ValidationError on creation**
- Check dataclass field order: required, optional, with defaults
- Check @post_init for validation logic

**Database IntegrityError**
- Check foreign key constraints
- Ensure organization_id exists for multi-tenant data
- Check unique constraints

**Route not found**
- Verify route is in shared/api_routes.py
- Check router is registered in main.py
- Verify import path is correct
