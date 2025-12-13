---
description: Create new module for PROJECT_BESAR
---

# Flow D1: Create New Module

## Pre-requisites
- [ ] Module name approved (from 14 modules list)
- [ ] Business requirements documented
- [ ] Dependencies identified

## Module Structure
```
modules/{module}/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   └── permissions.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── events/
│   │   └── jobs/
│   ├── migrations/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── routes.tsx
│   ├── package.json
│   └── vite.config.ts
└── docs/
    ├── README.md
    ├── ARCHITECTURE.md
    ├── API.md
    └── DATABASE.md
```

## Execution Steps

1. **Create folder structure** (above)
2. **Setup backend core**
   - config.py with module settings
   - exceptions.py with module errors
   - permissions.py with RBAC
3. **Setup database**
   - Base model with tenant_id
   - Initial migration
4. **Setup frontend**
   - Vite + React + TypeScript
   - Module theme color
   - Route structure
5. **Create documentation**
   - README.md
   - ARCHITECTURE.md

## Module Colors Reference
| Module | Primary |
|--------|---------|
| pms | #2563EB |
| pos | #EA580C |
| hrm | #7C3AED |
| accounting | #059669 |

## Checklist Before Complete
- [ ] Backend structure created
- [ ] Frontend structure created
- [ ] RBAC permissions defined
- [ ] Health check endpoint
- [ ] Docker files ready
- [ ] Documentation created
