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

## Documentation Reference - Prefix Convention

### Scope Prefix (First Level)
| Prefix | Scope | Applies To |
|--------|-------|-----------|
| `CORE-` | **Foundational** | All modules (58 files) |
| `ACC-` | **Accounting Module** | Accounting-specific (5 files) |
| `PMS-` | **PMS Module** | PMS-specific (2 files) |
| `INV-` | **Inventory Module** | Inventory-specific (1 file) |
| `MULTI-` | **Cross-Module** | Multiple modules (1 file) |
| `EXTENSION-` | **Add-ons** | Optional extensions (1 file) |

### Category Suffix (Second Level)
| Category | Files | Purpose |
|----------|-------|---------|
| `ARCH-` | 12 | Architecture & Design Patterns |
| `SPEC-` | 9 | Specifications & Workflows |
| `REF-` | 9 | References & Data Models |
| `SEC-` | 3 | Security & Authorization |
| `STD-` | 20 | Standards & Guidelines |
| `GUIDE-` | 4 | Implementation Guides |
| `TEST-` | 1 | Testing Strategy |
| `UI-` | 3 | UI/UX Design |
| `BIZ-` | 3 | Business Logic |
| `DECISION-` | 1 | Architectural Decisions |

### Examples
| Old Name | New Name | Meaning |
|----------|----------|---------|
| `ARCH-01` | `CORE-ARCH-01-platform-vision` | Core arch doc |
| `REF-01` | `CORE-REF-01-identity-membership-model` | Core reference |
| `SPEC-09` | `PMS-SPEC-09-pms-core-process` | PMS-specific spec |
| `SPEC-10` | `ACC-SPEC-10-accounting-core-process` | Accounting-specific spec |
| `SPEC-11` | `MULTI-SPEC-11-inter-tenant-supplier-flow` | Cross-module spec |
| `ARCH-04` | `EXTENSION-ARCH-04-digital-signage-module` | Add-on module |
| `REF-01-decisions` | `CORE-DECISION-01-enterprise-platform-decisions` | Decision log |
| `STD-19` + `STD-19` (2 files) | `CORE-STD-19-event-model-and-principles` + `CORE-STD-20-event-contract-specifications` | Event docs (split) |

## Key Standards Quick Reference
| File | Key Point |
|------|-----------|
| `CORE-STD-01` | Database: UUID, soft delete, timestamps |
| `CORE-STD-01` | RBAC: `{module}.{resource}.{action}` |
| `CORE-STD-01` | API: Consistent response format |
| `CORE-STD-02` | Validation: Pydantic + Zod |
| `CORE-STD-07` | Multi-tenancy: tenant_id everywhere |
| `CORE-STD-15` | Input Design: Prevent errors at UI level |
| `CORE-STD-16` | Smart Suggestions: Semi-automatic with user confirmation |
| `ACC-BIZ-03` | Reconciliation: Entry lifecycle, audit trail, controls |
| `CORE-SPEC-04` | OCR: Image processing, data extraction, validation |
| `CORE-SEC-01` | Security: CSP, XSS, CSRF, WAF |
| `CORE-REF-01` | Identity & Membership: Global identity, tenant-scoped roles |
| `CORE-REF-04` | Subscription Model: Two-layer (subscription status + module status) |
| `PMS-SPEC-09` | PMS Workflow: Reservation → Check-in → Stay → Check-out → Invoice |
| `ACC-SPEC-10` | Accounting Workflow: Invoice → Payment → Journal → Reconciliation |

## Before Any Code Change
1. Identify relevant flow dari `/skills/project-besar/flows/`
2. Follow checklist di flow tersebut
3. Verify standards compliance
4. Ensure tests exist atau dibuat

## Directory Structure
```
PROJECT_BESAR/
├── docs/                    # Documentation (scope-category-based naming)
│   │
│   ├── CORE-*.md           # Foundational docs (58 files)
│   │   ├── CORE-ARCH-*.md     # Architecture (12 files)
│   │   ├── CORE-SPEC-*.md     # Specifications (9 files)
│   │   ├── CORE-REF-*.md      # References (9 files)
│   │   ├── CORE-SEC-*.md      # Security (3 files)
│   │   ├── CORE-STD-*.md      # Standards (20 files)
│   │   ├── CORE-GUIDE-*.md    # Guides (4 files)
│   │   ├── CORE-TEST-*.md     # Tests (1 file)
│   │   ├── CORE-UI-*.md       # UI/UX (3 files)
│   │   ├── CORE-DECISION-*.md # Decisions (1 file)
│   │   └── CORE-BIZ-*.md      # (NOTE: No BIZ files in CORE)
│   │
│   ├── ACC-*.md            # Accounting-specific (5 files)
│   │   ├── ACC-BIZ-*.md       # Accounting business logic
│   │   ├── ACC-REF-*.md       # Accounting data models
│   │   └── ACC-SPEC-*.md      # Accounting specs
│   │
│   ├── PMS-*.md            # PMS-specific (2 files)
│   │   ├── PMS-REF-*.md       # PMS data models
│   │   └── PMS-SPEC-*.md      # PMS specs
│   │
│   ├── INV-*.md            # Inventory-specific (1 file)
│   │   └── INV-REF-*.md       # Inventory data models
│   │
│   ├── MULTI-*.md          # Cross-module (1 file)
│   │   └── MULTI-SPEC-*.md    # Cross-module specs
│   │
│   ├── EXTENSION-*.md      # Add-on modules (1 file)
│   │   └── EXTENSION-ARCH-*.md
│   │
│   └── archive/            # Historical/deprecated (DON'T EDIT)
│
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

## How to Find Documentation

### By Scope (First Prefix)
- **Need foundational concept?** Look for `CORE-*` files
- **Need Accounting-specific?** Look for `ACC-*` files
- **Need PMS-specific?** Look for `PMS-*` files
- **Need Cross-module?** Look for `MULTI-*` files

### By Category (Second Prefix)
- **Need architecture?** Look for `*-ARCH-*` files
- **Need workflow specs?** Look for `*-SPEC-*` files
- **Need data models?** Look for `*-REF-*` files
- **Need standards?** Look for `*-STD-*` files
- **Need implementation guide?** Look for `*-GUIDE-*` files

### Examples
```
Looking for PMS workflow?
→ PMS-SPEC-09-pms-core-process.md

Looking for Accounting data model?
→ ACC-REF-10-accounting-domain-erd-detailed.md

Looking for general event architecture?
→ CORE-ARCH-10-event-driven-architecture.md

Looking for authorization rules?
→ CORE-SEC-03-authorization-approval-audit.md
```

## Quick Commands
- `/flow` - Navigate to appropriate development flow
- `/review` - Code review dengan checklist
- `/deploy` - Pre-deployment checklist
- **`docs/CORE-`** - Read foundational standards before implementation
- **`docs/[MODULE]-`** - Read module-specific specs before adding module features
