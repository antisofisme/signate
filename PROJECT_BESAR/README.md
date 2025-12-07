# PROJECT_BESAR - Enterprise Hospitality Platform

> Dokumentasi dan referensi untuk pengembangan Enterprise Hospitality Platform (PMS, Accounting, HRM, dll).

---

## Folder Structure

```
PROJECT_BESAR/
├── docs/                              # Dokumentasi proyek
│   ├── DEVELOPMENT_STANDARDS.md       # Standards V1 (#1-7)
│   ├── DEVELOPMENT_STANDARDS_V2.md    # Standards V2 (#8-16)
│   ├── BUSINESS_ACCOUNTING_STANDARDS.md    # Business & Accounting V1 (Section 1-9, 12)
│   ├── BUSINESS_ACCOUNTING_STANDARDS_V2.md # Business & Accounting V2 (Section 10-15)
│   ├── CONTRADICTIONS_RESOLUTION.md   # Resolusi kontradiksi standards (Decisions #79-99)
│   ├── PLATFORM_VISION.md             # Visi platform & arsitektur
│   ├── PMS_DECISIONS.md               # 245 keputusan yang sudah disetujui
│   ├── PMS_DATABASE_ANALYSIS.md       # Analisis database lama (Firebird)
│   ├── PMS_DATABASE_SCHEMA.md         # Schema lengkap dari Firebird
│   ├── PMS_REFERENCE_INDEX.md         # Index referensi cepat
│   ├── PMS_WEAKNESSES_ANALYSIS.md     # Analisis kekurangan sistem lama
│   ├── PMS_ARCHITECTURE_WEAKNESSES_REPORT.md  # Report kelemahan arsitektur
│   ├── PMS_PERFORMANCE_ANALYSIS.md    # Analisis performa sistem
│   └── METADATA_EXTRACTION_SUMMARY.md # Summary ekstraksi metadata
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
- **[BUSINESS_ACCOUNTING_STANDARDS.md](./docs/BUSINESS_ACCOUNTING_STANDARDS.md)** - Standar bisnis & akuntansi (Section 1-9, 12)
- **[BUSINESS_ACCOUNTING_STANDARDS_V2.md](./docs/BUSINESS_ACCOUNTING_STANDARDS_V2.md)** - Standar bisnis & akuntansi (Section 10-15)
- **[SHARED_CODE_STANDARDS.md](./docs/SHARED_CODE_STANDARDS.md)** - Standar shared/centralized code (Decisions #100-105)
- **[ACCOUNTING_RESEARCH_SUMMARY.md](./docs/ACCOUNTING_RESEARCH_SUMMARY.md)** - Kompilasi research standar akuntansi
- **[PLATFORM_VISION.md](./docs/PLATFORM_VISION.md)** - Visi platform & arsitektur

### Referensi Legacy (Firebird)
- **[PMS_DATABASE_ANALYSIS.md](./docs/PMS_DATABASE_ANALYSIS.md)** - Analisis business flow
- **[PMS_DATABASE_SCHEMA.md](./docs/PMS_DATABASE_SCHEMA.md)** - Schema lengkap
- **[PMS_WEAKNESSES_ANALYSIS.md](./docs/PMS_WEAKNESSES_ANALYSIS.md)** - Kekurangan sistem lama

### Analisis & Report
- **[CONTRADICTIONS_RESOLUTION.md](./docs/CONTRADICTIONS_RESOLUTION.md)** - Resolusi 21 kontradiksi Dev vs Business Standards (Decisions #79-99)
- **[STANDARDS_AUDIT_REPORT.md](./docs/STANDARDS_AUDIT_REPORT.md)** - Hasil audit multi-agent (Grade A- 92/100)
- **[PMS_ARCHITECTURE_WEAKNESSES_REPORT.md](./docs/PMS_ARCHITECTURE_WEAKNESSES_REPORT.md)** - Report detail kelemahan arsitektur
- **[PMS_PERFORMANCE_ANALYSIS.md](./docs/PMS_PERFORMANCE_ANALYSIS.md)** - Analisis performa & bottleneck
- **[METADATA_EXTRACTION_SUMMARY.md](./docs/METADATA_EXTRACTION_SUMMARY.md)** - Summary ekstraksi metadata

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

---

## Tech Stack Summary

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
| **Orchestration** | Docker Swarm |
| **Monitoring** | Prometheus + Grafana + Jaeger |

---

## Applications (12+)

| # | Application | Status |
|---|-------------|--------|
| 1 | Digital Signage (CMS) | ✅ Done |
| 2 | PMS (Hotel Operations) | 🔄 Planning |
| 3 | Guest App | 📋 Planned |
| 4 | POS (F&B) | 📋 Planned |
| 5 | Online Menu | 📋 Planned |
| 6 | HRM & Payroll | 📋 Planned |
| 7 | Procurement | 📋 Planned |
| 8 | Supplier Portal | 📋 Planned |
| 9 | Inventory | 📋 Planned |
| 10 | Asset Management | 📋 Planned |
| 11 | Accounting | 📋 Planned |

---

*Last Updated: 2025-12-07*
