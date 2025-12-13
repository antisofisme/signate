# PROJECT_BESAR - Claude Context

## Project Overview
Enterprise Hospitality Platform dengan 14 modules:
PMS, POS, HRM, Accounting, Inventory, Procurement, Asset, Guest, Channel, Signage, Supplier, IoT, Menu, Platform

## Tech Stack
| Layer | Technology |
|-------|------------|
| Backend | Python 3.11 + FastAPI |
| Frontend | React 18 + TypeScript + Vite + Bun |
| Database | TimescaleDB (PostgreSQL) + PgBouncer |
| Cache | Redis |
| Queue | RabbitMQ + Celery |
| Search | Meilisearch |
| Real-time | Centrifugo |
| Storage | Cloudflare R2 |
| Gateway | Traefik |

## Critical Rules - WAJIB DIIKUTI

### Database
1. **SELALU** gunakan `tenant_id` di semua tables dan queries
2. **SELALU** soft delete (`is_deleted`, `deleted_at`)
3. **SELALU** UUID untuk primary key
4. **SELALU** ada `created_at`, `updated_at`
5. **SELALU** ada audit fields (`created_by`, `updated_by`) untuk sensitive data

### Code
1. **JANGAN** hardcode secrets - gunakan environment variables
2. **JANGAN** bypass permission checks
3. **JANGAN** commit langsung ke main branch
4. **JANGAN** edit files di `/docs/archive/`

### Naming Convention
| Type | Convention | Example |
|------|------------|---------|
| Python vars/functions | snake_case | `get_reservation()` |
| Python classes | PascalCase | `ReservationService` |
| TypeScript vars | camelCase | `reservationData` |
| TypeScript components | PascalCase | `ReservationCard` |
| Database tables | snake_case, plural | `reservations` |
| API endpoints | kebab-case | `/api/v1/room-types` |

## Documentation Reference

| Prefix | Category | Content |
|--------|----------|---------|
| `STD-01` to `STD-16` | Standards | 47 development standards |
| `ARCH-` | Architecture | platform-vision, module, puzzle |
| `SPEC-` | Specs | api-contracts, database-schema, integration |
| `SEC-01` | Security | OWASP, WAF, Pentest, Dependencies |
| `UI-` | UI/UX | design-system, components, wireframes |
| `BIZ-` | Business | accounting standards |
| `TEST-01` | Testing | testing strategy |
| `GUIDE-01` | Guide | 22 development flows |
| `REF-01` | Reference | 245 decisions |

## Key Standards Quick Reference
| File | # | Key Point |
|------|---|-----------|
| STD-01 | 2 | Database: UUID, soft delete, timestamps |
| STD-01 | 3 | RBAC: `{module}.{resource}.{action}` |
| STD-01 | 6 | API: Consistent response format |
| STD-02 | 8 | Validation: Pydantic + Zod |
| STD-07 | 29 | Multi-tenancy: tenant_id everywhere |
| STD-15 | 46 | Input Design: Prevent errors at UI level |
| STD-16 | 47 | Smart Suggestions: Semi-automatic with user confirmation |
| BIZ-03 | - | Reconciliation: Entry lifecycle, audit trail, controls |
| SPEC-04 | - | OCR: Image processing, data extraction, validation |
| SEC-01 | - | Security: CSP, XSS, CSRF, WAF |

## Before Any Code Change
1. Identify relevant flow dari `/skills/project-besar/flows/`
2. Follow checklist di flow tersebut
3. Verify standards compliance
4. Ensure tests exist atau dibuat

## Directory Structure
```
PROJECT_BESAR/
├── docs/                    # Documentation (prefix-based naming)
│   ├── STD-*.md            # Development standards
│   ├── ARCH-*.md           # Architecture docs
│   ├── SPEC-*.md           # Specifications
│   ├── SEC-*.md            # Security
│   ├── UI-*.md             # UI/UX docs
│   └── archive/            # Historical (DON'T EDIT)
├── database/               # Legacy Firebird reference
└── modules/                # Future: module implementations
    └── {module}/
        ├── backend/
        └── frontend/
```

## Module Colors (untuk UI)
| Module | Primary | Module | Primary |
|--------|---------|--------|---------|
| PMS | #2563EB | HRM | #7C3AED |
| POS | #EA580C | Accounting | #059669 |
| Inventory | #0891B2 | Asset | #4F46E5 |
| Guest | #DB2777 | Channel | #0D9488 |
| Signage | #DC2626 | IoT | #9333EA |

## API Response Format
```json
// Success
{ "success": true, "data": {...}, "meta": {...} }

// Error
{ "success": false, "error": { "code": "...", "message": "...", "details": {...} } }
```

## Quick Commands
- `/flow` - Navigate to appropriate development flow
- `/review` - Code review dengan checklist
- `/deploy` - Pre-deployment checklist
