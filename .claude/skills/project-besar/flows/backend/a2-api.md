---
description: Create API endpoint for PROJECT_BESAR
---

# Flow A2: Create API Endpoint

## Pre-requisites
- [ ] Model exists (Flow A1)
- [ ] Endpoint path defined
- [ ] HTTP methods identified

## Step 1: Create Pydantic Schemas
Location: `modules/{module}/backend/app/schemas/{entity}.py`

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class {Entity}Base(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class {Entity}Create({Entity}Base):
    pass

class {Entity}Update({Entity}Base):
    name: str | None = None

class {Entity}Response({Entity}Base):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
```

## Step 2: Create Router
Location: `modules/{module}/backend/app/api/v1/endpoints/{entity}.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.{entity} import {Entity}Create, {Entity}Response
from app.services.{entity}_service import {Entity}Service

router = APIRouter()

@router.post("/", response_model={Entity}Response, status_code=201)
async def create_{entity}(
    data: {Entity}Create,
    service: {Entity}Service = Depends()
):
    return await service.create(data)

@router.get("/{id}", response_model={Entity}Response)
async def get_{entity}(id: UUID, service: {Entity}Service = Depends()):
    result = await service.get(id)
    if not result:
        raise HTTPException(404, "Not found")
    return result
```

## Step 3: Register Router
Location: `modules/{module}/backend/app/api/v1/router.py`

```python
from app.api.v1.endpoints import {entity}
api_router.include_router({entity}.router, prefix="/{entities}", tags=["{entities}"])
```

## Step 4: Add Permission Checks
```python
from app.core.permissions import require_permissions, ModulePermission

@router.post("/")
async def create_{entity}(
    current_user = Depends(require_permissions([ModulePermission.{ENTITY}_CREATE]))
):
    ...
```

## Checklist Before Complete
- [ ] Schemas follow Pydantic patterns
- [ ] All CRUD endpoints created
- [ ] Permission checks added
- [ ] Response format consistent
- [ ] Error handling proper
