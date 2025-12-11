# PROJECT_BESAR - Enterprise Hospitality Platform

> Dokumentasi dan referensi untuk pengembangan Enterprise Hospitality Platform (PMS, Accounting, HRM, dll).

---

## Folder Structure

```
PROJECT_BESAR/
├── docs/                              # Dokumentasi proyek
│   ├── DEVELOPMENT_STANDARDS.md       # Standards V1 (#1-7)
│   ├── DEVELOPMENT_STANDARDS_V2.md    # Standards V2 (#8-16)
│   ├── DEVELOPMENT_STANDARDS_V3.md    # Standards V3 (#17-19)
│   ├── DEVELOPMENT_STANDARDS_V4.md    # Standards V4 (#20-22)
│   ├── DEVELOPMENT_STANDARDS_V5.md    # Standards V5 (#23-26)
│   ├── DEVELOPMENT_STANDARDS_V6.md    # Standards V6 (#27)
│   ├── DEVELOPMENT_STANDARDS_V7.md    # Standards V7 (#28-30)
│   ├── DEVELOPMENT_STANDARDS_V8.md    # Standards V8 (#31-33)
│   ├── DEVELOPMENT_STANDARDS_V9.md    # Standards V9 (#34-36)
│   ├── DEVELOPMENT_STANDARDS_V10.md   # Standards V10 (#37-39)
│   ├── DEVELOPMENT_STANDARDS_V11.md   # Standards V11 (#40-42)
│   ├── DEVELOPMENT_STANDARDS_V12.md   # Standards V12 (#43)
│   ├── DEVELOPMENT_STANDARDS_V13.md   # Standards V13 (#44)
│   ├── DEVELOPMENT_STANDARDS_V14.md   # Standards V14 (#45)
│   ├── BUSINESS_ACCOUNTING_STANDARDS.md    # Business & Accounting V1 (Section 1-10)
│   ├── BUSINESS_ACCOUNTING_STANDARDS_V2.md # Business & Accounting V2 (Section 11-16)
│   ├── CONTRADICTIONS_RESOLUTION.md   # Resolusi kontradiksi (Decisions #79-99)
│   ├── DATABASE_SCHEMA_PLATFORM.md    # Schema Platform DB & Community DB
│   ├── API_CONTRACTS_PLATFORM.md      # API Contracts Platform & Community
│   ├── SECURITY_AUTH_REQUIREMENTS.md  # Security & Auth Requirements
│   ├── SHARED_CODE_STANDARDS.md       # Shared/centralized code patterns
│   ├── PUZZLE_ARCHITECTURE.md         # Arsitektur modular puzzle-like
│   ├── MODULE_ARCHITECTURE.md         # Module Architecture & Building Blocks
│   ├── INTEGRATION_SPECS.md           # Integration Specs (Payment, Tax)
│   ├── UIUX_WIREFRAMES_FLOWS.md       # Wireframes & User Flows
│   ├── TESTING_STRATEGY.md            # Testing strategy
│   ├── PLATFORM_VISION.md             # Visi platform & arsitektur
│   ├── PMS_DECISIONS.md               # 245 keputusan yang sudah disetujui
│   │
│   └── archive/                       # Archived documentation
│       ├── analysis/                  # Audit & analysis reports (resolved)
│       │   ├── API_BACKEND_CONTRADICTIONS_REPORT.md
│       │   ├── DATABASE_CONTRADICTIONS_REPORT.md
│       │   ├── SECURITY_COMPLIANCE_GAP_ANALYSIS.md
│       │   └── STANDARDS_AUDIT_REPORT.md
│       │
│       └── legacy/                    # Legacy Firebird reference
│           ├── PMS_DATABASE_ANALYSIS.md
│           ├── PMS_DATABASE_SCHEMA.md
│           └── PMS_WEAKNESSES_ANALYSIS.md
│
└── database/                          # Database reference (Firebird legacy)
    ├── powerfo.gdb                    # Front Office database (1.4GB)
    ├── powerbo.gdb                    # Back Office database (914MB)
    ├── powerfo.sql                    # Front Office schema export
    ├── powerbo.sql                    # Back Office schema export
    └── analyze_database_schema.sql    # Script analisis schema
```

---

## Quick Links

### Dokumentasi Utama
- **[PMS_DECISIONS.md](./docs/PMS_DECISIONS.md)** - 245 keputusan yang sudah disetujui
- **[DEVELOPMENT_STANDARDS.md](./docs/DEVELOPMENT_STANDARDS.md)** - Standards #1-7
- **[DEVELOPMENT_STANDARDS_V2.md](./docs/DEVELOPMENT_STANDARDS_V2.md)** - Standards #8-16
- **[DEVELOPMENT_STANDARDS_V3.md](./docs/DEVELOPMENT_STANDARDS_V3.md)** - Standards #17-19 (Registries, Events, Files)
- **[DEVELOPMENT_STANDARDS_V4.md](./docs/DEVELOPMENT_STANDARDS_V4.md)** - Standards #20-22 (Real-time, Jobs, Search)
- **[DEVELOPMENT_STANDARDS_V5.md](./docs/DEVELOPMENT_STANDARDS_V5.md)** - Standards #23-26 (Notification, API Versioning, Feature Flags, Performance SLA)
- **[DEVELOPMENT_STANDARDS_V6.md](./docs/DEVELOPMENT_STANDARDS_V6.md)** - Standards #27 (Lookup Tables)
- **[DEVELOPMENT_STANDARDS_V7.md](./docs/DEVELOPMENT_STANDARDS_V7.md)** - Standards #28-30 (State Machine, Multi-tenancy, Rate Limiting)
- **[DEVELOPMENT_STANDARDS_V8.md](./docs/DEVELOPMENT_STANDARDS_V8.md)** - Standards #31-33 (Backup & DR, Webhook, Reports)
- **[DEVELOPMENT_STANDARDS_V9.md](./docs/DEVELOPMENT_STANDARDS_V9.md)** - Standards #34-36 (Import/Export, Email Templates, PWA)
- **[DEVELOPMENT_STANDARDS_V10.md](./docs/DEVELOPMENT_STANDARDS_V10.md)** - Standards #37-39 (Circuit Breaker, Health Checks, Data Archival)
- **[DEVELOPMENT_STANDARDS_V11.md](./docs/DEVELOPMENT_STANDARDS_V11.md)** - Standards #40-42 (Distributed Tracing, Secrets Management, Scheduled Tasks)
- **[DEVELOPMENT_STANDARDS_V12.md](./docs/DEVELOPMENT_STANDARDS_V12.md)** - Standards #43 (Config Governance)
- **[DEVELOPMENT_STANDARDS_V13.md](./docs/DEVELOPMENT_STANDARDS_V13.md)** - Standards #44 (Fraud Detection & Audit Intelligence)
- **[DEVELOPMENT_STANDARDS_V14.md](./docs/DEVELOPMENT_STANDARDS_V14.md)** - Standards #45 (Internal Collaboration Hub)
- **[BUSINESS_ACCOUNTING_STANDARDS.md](./docs/BUSINESS_ACCOUNTING_STANDARDS.md)** - Standar bisnis & akuntansi (Section 1-10)
- **[BUSINESS_ACCOUNTING_STANDARDS_V2.md](./docs/BUSINESS_ACCOUNTING_STANDARDS_V2.md)** - Standar bisnis & akuntansi (Section 11-16)
- **[SHARED_CODE_STANDARDS.md](./docs/SHARED_CODE_STANDARDS.md)** - Standar shared/centralized code
- **[DATABASE_SCHEMA_PLATFORM.md](./docs/DATABASE_SCHEMA_PLATFORM.md)** - Schema Platform DB & Community DB
- **[API_CONTRACTS_PLATFORM.md](./docs/API_CONTRACTS_PLATFORM.md)** - API Contracts Platform & Community
- **[SECURITY_AUTH_REQUIREMENTS.md](./docs/SECURITY_AUTH_REQUIREMENTS.md)** - Security & Authentication Requirements
- **[PUZZLE_ARCHITECTURE.md](./docs/PUZZLE_ARCHITECTURE.md)** - Arsitektur modular puzzle-like
- **[MODULE_ARCHITECTURE.md](./docs/MODULE_ARCHITECTURE.md)** - Module Architecture & Shared Building Blocks
- **[INTEGRATION_SPECS.md](./docs/INTEGRATION_SPECS.md)** - Integration Specs (Payment, Tax, Email, Storage)
- **[UIUX_WIREFRAMES_FLOWS.md](./docs/UIUX_WIREFRAMES_FLOWS.md)** - Wireframes & User Flows
- **[TESTING_STRATEGY.md](./docs/TESTING_STRATEGY.md)** - Testing Strategy
- **[PLATFORM_VISION.md](./docs/PLATFORM_VISION.md)** - Visi platform & arsitektur
- **[CONTRADICTIONS_RESOLUTION.md](./docs/CONTRADICTIONS_RESOLUTION.md)** - Resolusi kontradiksi (Decisions #79-99)

### Archived Documentation
- **[archive/legacy/](./docs/archive/legacy/)** - Legacy Firebird reference (PMS database analysis, schema, weaknesses)
- **[archive/analysis/](./docs/archive/analysis/)** - Audit reports & analysis (resolved issues)

---

## Standards Summary

| # | Standard | Status |
|---|----------|--------|
| 1 | Naming Conventions | ✅ V1 |
| 2 | Database Patterns | ✅ V1 |
| 3 | RBAC / Permission | ✅ V1 |
| 4 | Audit Log | ✅ V1 |
| 5 | Caching | ✅ V1 |
| 6 | API Patterns | ✅ V1 |
| 7 | Error Handling | ✅ V1 |
| 8 | Validation | ✅ V2 |
| 9 | Testing | ✅ V2 |
| 10 | Code Structure | ✅ V2 |
| 11 | Frontend Patterns | ✅ V2 |
| 12 | Infrastructure & DevOps | ✅ V2 |
| 13 | Payment & Licensing | ✅ V2 |
| 14 | TimescaleDB & Operational | ✅ V2 |
| 15 | Logging & Observability | ✅ V2 |
| 16 | Internationalization (i18n) | ✅ V2 |
| 17 | Centralized Registries | ✅ V3 |
| 18 | Event/Message Schema | ✅ V3 |
| 19 | File/Media Handling | ✅ V3 |
| 20 | Real-time/WebSocket | ✅ V4 |
| 21 | Background Job (Celery) | ✅ V4 |
| 22 | Search (Meilisearch) | ✅ V4 |
| 23 | Notification | ✅ V5 |
| 24 | API Versioning | 📋 V5 |
| 25 | Feature Flags | 📋 V5 |
| 26 | Performance SLA | ✅ V5 |
| 27 | Lookup/Type Tables | ✅ V6 |
| 28 | State Machine / Workflow | ✅ V7 |
| 29 | Multi-tenancy Deep Dive | ✅ V7 |
| 30 | Rate Limiting & Throttling | ✅ V7 |
| 31 | Backup & Disaster Recovery | ✅ V8 |
| 32 | Webhook System | ✅ V8 |
| 33 | Report Generation | ✅ V8 |
| 34 | Data Import/Export | ✅ V9 |
| 35 | Email Templates | ✅ V9 |
| 36 | Offline/PWA Support | ✅ V9 |
| 37 | Circuit Breaker & Resilience | ✅ V10 |
| 38 | Health Checks & Readiness | ✅ V10 |
| 39 | Data Archival & Retention | ✅ V10 |
| 40 | Distributed Tracing (OpenTelemetry) | ✅ V11 |
| 41 | Secrets & Configuration Management | ✅ V11 |
| 42 | Scheduled Tasks & Cron Management | ✅ V11 |
| 43 | Configuration Governance | ✅ V12 |
| 44 | Fraud Detection & Audit Intelligence | ✅ V13 |
| 45 | Internal Collaboration Hub | ✅ V14 |

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

*Last Updated: 2025-12-11 (IoT Module added)*
