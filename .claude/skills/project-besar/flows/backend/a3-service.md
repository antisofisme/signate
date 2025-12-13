---
description: Create service/business logic for PROJECT_BESAR
---

# Flow A3: Create Service/Business Logic

## Pre-requisites
- [ ] Model exists (Flow A1)
- [ ] Business rules defined

## Step 1: Create Repository
Location: `modules/{module}/backend/app/repositories/{entity}_repository.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.{entity} import {Entity}

class {Entity}Repository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> {Entity} | None:
        result = await self.db.execute(
            select({Entity})
            .where({Entity}.id == id)
            .where({Entity}.tenant_id == tenant_id)
            .where({Entity}.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def create(self, entity: {Entity}) -> {Entity}:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
```

## Step 2: Create Service
Location: `modules/{module}/backend/app/services/{entity}_service.py`

```python
from app.repositories.{entity}_repository import {Entity}Repository
from app.core.exceptions import EntityNotFoundError, BusinessRuleViolationError

class {Entity}Service:
    def __init__(self, repository: {Entity}Repository):
        self.repository = repository

    async def create(self, data: {Entity}Create, tenant_id: UUID) -> {Entity}:
        # Validate business rules
        await self._validate_business_rules(data)

        entity = {Entity}(**data.dict(), tenant_id=tenant_id)
        return await self.repository.create(entity)

    async def _validate_business_rules(self, data):
        # Add business rule validations
        pass
```

## Step 3: Dependency Injection
```python
from fastapi import Depends
from app.core.database import get_db

def get_{entity}_service(db: AsyncSession = Depends(get_db)) -> {Entity}Service:
    repository = {Entity}Repository(db)
    return {Entity}Service(repository)
```

## Checklist Before Complete
- [ ] Repository handles data access only
- [ ] Service contains business logic
- [ ] tenant_id in all queries
- [ ] Proper error handling
- [ ] DI configured
