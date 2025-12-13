# PROJECT_BESAR - Enterprise Hospitality Platform

> Dokumentasi dan referensi untuk pengembangan Enterprise Hospitality Platform (PMS, Accounting, HRM, dll).

---

## Folder Structure

```
PROJECT_BESAR/
├── docs/                                    # Dokumentasi proyek
│   │
│   ├── ARCH-01-platform-vision.md           # Visi platform & arsitektur
│   ├── ARCH-02-module-architecture.md       # Module Architecture & Building Blocks
│   ├── ARCH-03-puzzle-architecture.md       # Arsitektur modular puzzle-like
│   │
│   ├── STD-01-core-naming-db-rbac-api.md    # Standards #1-7 (Naming, DB, RBAC, Audit, Cache, API, Error)
│   ├── STD-02-validation-frontend-backend.md # Standards #8-16 (Validation, Testing, Code Structure, Frontend, Infrastructure)
│   ├── STD-03-registries-events-files.md    # Standards #17-19 (Registries, Events, Files)
│   ├── STD-04-realtime-jobs-search.md       # Standards #20-22 (Real-time, Jobs, Search)
│   ├── STD-05-notification-versioning-flags-sla.md # Standards #23-26 (Notification, API Versioning, Feature Flags, Performance SLA)
│   ├── STD-06-lookup-tables.md              # Standards #27 (Lookup Tables)
│   ├── STD-07-state-tenancy-ratelimit.md    # Standards #28-30 (State Machine, Multi-tenancy, Rate Limiting)
│   ├── STD-08-backup-webhook-reports.md     # Standards #31-33 (Backup & DR, Webhook, Reports)
│   ├── STD-09-import-email-pwa.md           # Standards #34-36 (Import/Export, Email Templates, PWA)
│   ├── STD-10-circuit-health-archival.md    # Standards #37-39 (Circuit Breaker, Health Checks, Data Archival)
│   ├── STD-11-tracing-secrets-tasks.md      # Standards #40-42 (Distributed Tracing, Secrets Management, Scheduled Tasks)
│   ├── STD-12-config-governance.md          # Standards #43 (Config Governance)
│   ├── STD-13-fraud-audit.md                # Standards #44 (Fraud Detection & Audit Intelligence)
│   ├── STD-14-collaboration-hub.md          # Standards #45 (Internal Collaboration Hub)
│   ├── STD-15-input-design-flow.md          # Standard #46 (Input Design Flow & Constraint-Based UI)
│   ├── STD-16-smart-suggestions-approval.md # Standard #47 (Smart Suggestions & Human-in-the-Loop)
│   │
│   ├── BIZ-01-accounting-core.md            # Business & Accounting (Section 1-10)
│   ├── BIZ-02-accounting-advanced.md        # Business & Accounting (Section 11-16)
│   ├── BIZ-03-accounting-reconciliation-controls.md # Reconciliation, Controls & Audit Trail
│   │
│   ├── SPEC-01-api-contracts.md             # API Contracts Platform & Community
│   ├── SPEC-02-database-schema.md           # Schema Platform DB & Community DB
│   ├── SPEC-03-integration.md               # Integration Specs (Payment, Tax, Email, Storage)
│   ├── SPEC-04-data-integration-ocr.md      # OCR Integration, Image Processing, Data Extraction
│   │
│   ├── SEC-01-security-auth.md              # Security & Auth Requirements (OWASP, WAF, Pentest)
│   │
│   ├── UI-01-design-system.md               # UI Design System (Colors, Typography, Components)
│   ├── UI-02-components.md                  # UI Components Specification (Detail)
│   ├── UI-03-wireframes-flows.md            # Wireframes & User Flows
│   │
│   ├── TEST-01-testing-strategy.md          # Testing Strategy
│   │
│   ├── GUIDE-01-development-flow.md         # Flow guide untuk AI-assisted development (22 flows)
│   ├── GUIDE-02-module-docs-template.md     # Standard dokumentasi per module & DVL Tool
│   │
│   ├── REF-01-decisions.md                  # 245 keputusan yang sudah disetujui
│   ├── REF-02-shared-code.md                # Shared/centralized code patterns
│   │
│   └── archive/                             # Archived documentation
│       ├── contradictions-resolution.md     # Resolusi kontradiksi (historical)
│       ├── analysis/                        # Audit & analysis reports (resolved)
│       └── legacy/                          # Legacy Firebird reference
│
└── database/                                # Database reference (Firebird legacy)
    ├── powerfo.gdb                          # Front Office database (1.4GB)
    ├── powerbo.gdb                          # Back Office database (914MB)
    ├── powerfo.sql                          # Front Office schema export
    ├── powerbo.sql                          # Back Office schema export
    └── analyze_database_schema.sql          # Script analisis schema
```

---

## Quick Links by Category

### Architecture (ARCH)
| File | Description |
|------|-------------|
| [ARCH-01-platform-vision](./docs/ARCH-01-platform-vision.md) | Visi platform & arsitektur |
| [ARCH-02-module-architecture](./docs/ARCH-02-module-architecture.md) | Module Architecture & Building Blocks |
| [ARCH-03-puzzle-architecture](./docs/ARCH-03-puzzle-architecture.md) | Arsitektur modular puzzle-like |

### Development Standards (STD)
| File | Standards | Topics |
|------|-----------|--------|
| [STD-01-core](./docs/STD-01-core-naming-db-rbac-api.md) | #1-7 | Naming, Database, RBAC, Audit, Cache, API, Error |
| [STD-02-validation](./docs/STD-02-validation-frontend-backend.md) | #8-16 | Validation, Testing, Code Structure, Frontend, Infrastructure |
| [STD-03-registries](./docs/STD-03-registries-events-files.md) | #17-19 | Registries, Events, Files |
| [STD-04-realtime](./docs/STD-04-realtime-jobs-search.md) | #20-22 | Real-time, Jobs, Search |
| [STD-05-notification](./docs/STD-05-notification-versioning-flags-sla.md) | #23-26 | Notification, API Versioning, Feature Flags, SLA |
| [STD-06-lookup](./docs/STD-06-lookup-tables.md) | #27 | Lookup Tables |
| [STD-07-state](./docs/STD-07-state-tenancy-ratelimit.md) | #28-30 | State Machine, Multi-tenancy, Rate Limiting |
| [STD-08-backup](./docs/STD-08-backup-webhook-reports.md) | #31-33 | Backup & DR, Webhook, Reports |
| [STD-09-import](./docs/STD-09-import-email-pwa.md) | #34-36 | Import/Export, Email Templates, PWA |
| [STD-10-circuit](./docs/STD-10-circuit-health-archival.md) | #37-39 | Circuit Breaker, Health Checks, Data Archival |
| [STD-11-tracing](./docs/STD-11-tracing-secrets-tasks.md) | #40-42 | Distributed Tracing, Secrets, Scheduled Tasks |
| [STD-12-config](./docs/STD-12-config-governance.md) | #43 | Config Governance |
| [STD-13-fraud](./docs/STD-13-fraud-audit.md) | #44 | Fraud Detection & Audit Intelligence |
| [STD-14-collab](./docs/STD-14-collaboration-hub.md) | #45 | Internal Collaboration Hub |
| [STD-15-input](./docs/STD-15-input-design-flow.md) | #46 | Input Design Flow & Constraint-Based UI |
| [STD-16-suggestions](./docs/STD-16-smart-suggestions-approval.md) | #47 | Smart Suggestions & Human-in-the-Loop |

### Business Standards (BIZ)
| File | Description |
|------|-------------|
| [BIZ-01-accounting-core](./docs/BIZ-01-accounting-core.md) | Business & Accounting (Section 1-10) |
| [BIZ-02-accounting-advanced](./docs/BIZ-02-accounting-advanced.md) | Business & Accounting (Section 11-16) |
| [BIZ-03-reconciliation](./docs/BIZ-03-accounting-reconciliation-controls.md) | Reconciliation, Controls & Audit Trail |

### Specifications (SPEC)
| File | Description |
|------|-------------|
| [SPEC-01-api-contracts](./docs/SPEC-01-api-contracts.md) | API Contracts Platform & Community |
| [SPEC-02-database-schema](./docs/SPEC-02-database-schema.md) | Schema Platform DB & Community DB |
| [SPEC-03-integration](./docs/SPEC-03-integration.md) | Integration Specs (Payment, Tax, Email, Storage) |
| [SPEC-04-ocr](./docs/SPEC-04-data-integration-ocr.md) | OCR Integration, Image Processing, Data Extraction |

### Security (SEC)
| File | Description |
|------|-------------|
| [SEC-01-security-auth](./docs/SEC-01-security-auth.md) | Security & Auth (OWASP, WAF, Pentest, Dependency Scan) |

### UI/UX (UI)
| File | Description |
|------|-------------|
| [UI-01-design-system](./docs/UI-01-design-system.md) | Design System (Colors, Typography, Components) |
| [UI-02-components](./docs/UI-02-components.md) | UI Components Specification (Detail) |
| [UI-03-wireframes-flows](./docs/UI-03-wireframes-flows.md) | Wireframes & User Flows |

### Testing (TEST)
| File | Description |
|------|-------------|
| [TEST-01-testing-strategy](./docs/TEST-01-testing-strategy.md) | Testing Strategy |

### Guides (GUIDE)
| File | Description |
|------|-------------|
| [GUIDE-01-development-flow](./docs/GUIDE-01-development-flow.md) | 22 Development Flows for AI-assisted Development |
| [GUIDE-02-module-docs-template](./docs/GUIDE-02-module-docs-template.md) | Module Documentation Standard & DVL Tool |

### Reference (REF)
| File | Description |
|------|-------------|
| [REF-01-decisions](./docs/REF-01-decisions.md) | 245 keputusan yang sudah disetujui |
| [REF-02-shared-code](./docs/REF-02-shared-code.md) | Shared/centralized code patterns |

### Archived
| File | Description |
|------|-------------|
| [archive/contradictions-resolution](./docs/archive/contradictions-resolution.md) | Resolusi kontradiksi (historical) |
| [archive/legacy/](./docs/archive/legacy/) | Legacy Firebird reference |
| [archive/analysis/](./docs/archive/analysis/) | Audit reports (resolved) |

---

## Standards Summary (45 Standards)

| # | Standard | File |
|---|----------|------|
| 1 | Naming Conventions | STD-01 |
| 2 | Database Patterns | STD-01 |
| 3 | RBAC / Permission | STD-01 |
| 4 | Audit Log | STD-01 |
| 5 | Caching | STD-01 |
| 6 | API Patterns | STD-01 |
| 7 | Error Handling | STD-01 |
| 8 | Validation | STD-02 |
| 9 | Testing | STD-02 |
| 10 | Code Structure | STD-02 |
| 11 | Frontend Patterns | STD-02 |
| 12 | Infrastructure & DevOps | STD-02 |
| 13 | Payment & Licensing | STD-02 |
| 14 | TimescaleDB & Operational | STD-02 |
| 15 | Logging & Observability | STD-02 |
| 16 | Internationalization (i18n) | STD-02 |
| 17 | Centralized Registries | STD-03 |
| 18 | Event/Message Schema | STD-03 |
| 19 | File/Media Handling | STD-03 |
| 20 | Real-time/WebSocket | STD-04 |
| 21 | Background Job (Celery) | STD-04 |
| 22 | Search (Meilisearch) | STD-04 |
| 23 | Notification | STD-05 |
| 24 | API Versioning | STD-05 |
| 25 | Feature Flags | STD-05 |
| 26 | Performance SLA | STD-05 |
| 27 | Lookup/Type Tables | STD-06 |
| 28 | State Machine / Workflow | STD-07 |
| 29 | Multi-tenancy Deep Dive | STD-07 |
| 30 | Rate Limiting & Throttling | STD-07 |
| 31 | Backup & Disaster Recovery | STD-08 |
| 32 | Webhook System | STD-08 |
| 33 | Report Generation | STD-08 |
| 34 | Data Import/Export | STD-09 |
| 35 | Email Templates | STD-09 |
| 36 | Offline/PWA Support | STD-09 |
| 37 | Circuit Breaker & Resilience | STD-10 |
| 38 | Health Checks & Readiness | STD-10 |
| 39 | Data Archival & Retention | STD-10 |
| 40 | Distributed Tracing (OpenTelemetry) | STD-11 |
| 41 | Secrets & Configuration Management | STD-11 |
| 42 | Scheduled Tasks & Cron Management | STD-11 |
| 43 | Configuration Governance | STD-12 |
| 44 | Fraud Detection & Audit Intelligence | STD-13 |
| 45 | Internal Collaboration Hub | STD-14 |
| 46 | Input Design Flow & Constraint-Based UI | STD-15 |
| 47 | Smart Suggestions & Human-in-the-Loop | STD-16 |

---

## Tech Stack Summary

### Core Stack
| Category | Technology |
|----------|------------|
| **Backend** | Python + FastAPI |
| **Frontend** | React + Vite + Bun + TypeScript |
| **Database** | TimescaleDB + PgBouncer |
| **Cache** | Redis |
| **Message Broker** | RabbitMQ |
| **Background Jobs** | Celery |
| **File Storage** | Cloudflare R2 |
| **Search** | Meilisearch |
| **Real-time** | Centrifugo |

### Infrastructure Stack
| Category | Technology |
|----------|------------|
| **API Gateway** | Traefik |
| **Orchestration** | Docker Swarm (→ Kubernetes later) |
| **CI/CD** | GitHub Actions |
| **Log Collector** | Fluent Bit |
| **Log Storage** | Loki (→ ELK optional) |
| **Monitoring** | Prometheus + Grafana + Jaeger |
| **Error Tracking** | Sentry |

### External Services
| Category | Technology |
|----------|------------|
| **Email** | AWS SES |
| **SMS/WhatsApp** | Modular (provider TBD) |
| **PDF Generator** | WeasyPrint + Puppeteer |
| **Guest App** | PWA (native optional later) |

---

## Applications (14+)

| # | Application | Status |
|---|-------------|--------|
| 1 | Digital Signage (CMS) | ✅ Done |
| 2 | PMS (Hotel Operations) | 🔄 Planning |
| 3 | Channel Manager | 📋 Planned |
| 4 | Guest App | 📋 Planned |
| 5 | POS (F&B) | 📋 Planned |
| 6 | Online Menu | 📋 Planned |
| 7 | HRM & Payroll | 📋 Planned |
| 8 | Procurement | 📋 Planned |
| 9 | Supplier Portal | 📋 Planned |
| 10 | Inventory | 📋 Planned |
| 11 | Asset Management | 📋 Planned |
| 12 | Accounting | 📋 Planned |
| 13 | IoT & Smart Devices | 📋 Planned |

---

## File Naming Convention

| Prefix | Category | Example |
|--------|----------|---------|
| `ARCH-` | Architecture | ARCH-01-platform-vision.md |
| `STD-` | Development Standards | STD-01-core-naming-db-rbac-api.md |
| `BIZ-` | Business Standards | BIZ-01-accounting-core.md |
| `SPEC-` | Specifications | SPEC-01-api-contracts.md |
| `SEC-` | Security | SEC-01-security-auth.md |
| `UI-` | UI/UX | UI-01-design-system.md |
| `TEST-` | Testing | TEST-01-testing-strategy.md |
| `GUIDE-` | Guides | GUIDE-01-development-flow.md |
| `REF-` | Reference | REF-01-decisions.md |

---

*Last Updated: 2025-12-13 (Documentation reorganized with prefix-based naming)*
