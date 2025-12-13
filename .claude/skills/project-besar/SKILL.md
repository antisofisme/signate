# PROJECT_BESAR Skills

Enterprise Hospitality Platform development skills.

## Documentation Reference

| Prefix | Category | Files |
|--------|----------|-------|
| `STD-` | Development Standards | STD-01 to STD-16 (47 standards) |
| `ARCH-` | Architecture | platform-vision, module, puzzle |
| `SPEC-` | Specifications | api-contracts, database-schema, integration, ocr |
| `SEC-` | Security | security-auth (OWASP, WAF, Pentest) |
| `UI-` | UI/UX | design-system, components, wireframes |
| `BIZ-` | Business | accounting-core, accounting-advanced, reconciliation-controls |
| `TEST-` | Testing | testing-strategy |
| `GUIDE-` | Guides | development-flow, module-docs-template |
| `REF-` | Reference | decisions, shared-code |

## Available Skills

### Flow Skills (`flows/`)
Development workflow guides with checklists:

| Category | Skills | Doc Reference |
|----------|--------|---------------|
| **Backend** | a1-database, a2-api, a3-service, a4-job, a5-event, a6-integration | STD-01, STD-02, SPEC-02 |
| **Frontend** | b1-component, b2-page, b3-form, b4-table, b5-realtime | STD-02, STD-15, STD-16, UI-01, UI-02 |
| **Feature** | c1-crud, c2-report, c3-search, c4-notification, c5-upload | STD-03 to STD-09, BIZ-03 (if accounting) |
| **Module** | d1-new-module, d2-add-feature | ARCH-02, GUIDE-02 |
| **Maintenance** | e1-bugfix, e2-refactor, e3-performance, e4-security | SEC-01, TEST-01 |
| **Docs** | f1-module-docs, f2-api-docs | GUIDE-02, SPEC-01 |

### Reference Skills (`reference/`)
| Skill | Description | Doc Reference |
|-------|-------------|---------------|
| standards-quick | 47 standards summary | STD-01 to STD-16 + BIZ-03 + SPEC-04 |
| naming-convention | Naming rules | STD-01 |
| api-patterns | Response format, errors | STD-01, SPEC-01 |
| validation-patterns | Pydantic + Zod | STD-02 |
| db-patterns | Multi-tenancy, soft delete | STD-01, SPEC-02 |
| test-patterns | pytest + vitest | TEST-01, STD-02 |
| security-patterns | CSP, XSS, CSRF, WAF | SEC-01 |

### Utility Skills (`utils/`)
| Skill | Description |
|-------|-------------|
| code-review | Code review checklist |
| pr-template | Pull request template |
| migration-check | Database migration checklist |
| deploy-check | Deployment checklist |
| security-check | Security audit checklist |

## Usage
- Invoke specific skill based on task
- Use flow-router for navigation
- Reference docs: `PROJECT_BESAR/docs/{PREFIX}-{NUM}-{name}.md`
