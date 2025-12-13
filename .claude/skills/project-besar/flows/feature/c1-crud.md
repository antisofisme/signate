---
description: Create complete CRUD feature for PROJECT_BESAR
---

# Flow C1: Create CRUD Feature

**Compound Flow** - Combines: A1, A2, A3, B2, B3, B4

## Pre-requisites
- [ ] Entity name defined
- [ ] Module identified
- [ ] Fields/relationships defined
- [ ] Permissions defined

## Execution Order

### Phase 1: Backend
1. **A1 - Database**: Create model and migration
2. **A3 - Service**: Create repository and service
3. **A2 - API**: Create schemas and endpoints

### Phase 2: Frontend
4. **B3 - Form**: Create form component
5. **B4 - Table**: Create list table
6. **B2 - Page**: Create list/detail/form pages

## Quick Implementation

### Backend (10 files)
```
modules/{module}/backend/app/
├── models/{entity}.py          # Model
├── schemas/{entity}.py         # Pydantic schemas
├── repositories/{entity}_repository.py
├── services/{entity}_service.py
├── api/v1/endpoints/{entity}.py
└── migrations/versions/xxx_{entity}.py
```

### Frontend (8 files)
```
modules/{module}/frontend/src/
├── types/{entity}.ts
├── schemas/{entity}.schema.ts
├── hooks/use{Entity}.ts
├── components/{Entity}Form/
├── components/{Entity}Table/
└── pages/{Entity}/
    ├── {Entity}ListPage.tsx
    ├── {Entity}DetailPage.tsx
    └── {Entity}FormPage.tsx
```

## Final Checklist
- [ ] CRUD API working (POST, GET, PUT, DELETE)
- [ ] Permissions enforced
- [ ] List page with pagination, filter, sort
- [ ] Detail page shows all data
- [ ] Create/Edit forms validated
- [ ] Delete confirmation
- [ ] Tests written
