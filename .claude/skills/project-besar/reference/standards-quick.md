---
description: Quick reference for 47 development standards
---

# Standards Quick Reference

> Full docs: `PROJECT_BESAR/docs/STD-{num}-{topic}.md`

## STD-01: Core (#1-7)
| # | Standard | Key Point |
|---|----------|-----------|
| 1 | Naming | snake_case (Py), camelCase (JS), PascalCase (class) |
| 2 | Database | UUID, soft delete, timestamps, tenant_id index |
| 3 | RBAC | `{module}.{resource}.{action}` |
| 4 | Audit | Who, what, when, where |
| 5 | Caching | Redis, TTL strategy |
| 6 | API | Consistent response format |
| 7 | Error | Structured errors, codes |

## STD-02: Validation & Frontend (#8-16)
| # | Standard | Key Point |
|---|----------|-----------|
| 8 | Validation | Pydantic (BE) + Zod (FE) |
| 9 | Testing | 80% coverage target |
| 10 | Code Structure | Clean architecture layers |
| 11 | Frontend | React Query, TypeScript strict |
| 12 | DevOps | Docker, CI/CD pipeline |
| 15 | Logging | Structured, correlation ID |
| 16 | i18n | Multi-language support |

## STD-03: Registries & Events (#17-19)
| # | Standard | Key Point |
|---|----------|-----------|
| 17 | Registries | Service/feature registry |
| 18 | Events | Envelope, versioning, DLQ |
| 19 | Files | R2 storage, presigned URLs |

## STD-04: Realtime & Jobs (#20-22)
| # | Standard | Key Point |
|---|----------|-----------|
| 20 | WebSocket | Centrifugo |
| 21 | Jobs | Celery, retry strategy |
| 22 | Search | Meilisearch |

## STD-05: Notification & SLA (#23-26)
| # | Standard | Key Point |
|---|----------|-----------|
| 23 | Notification | Multi-channel (email, push, WA) |
| 24 | API Versioning | v1, v2 with deprecation |
| 25 | Feature Flags | Gradual rollout |
| 26 | Performance | API<200ms, DB<50ms |

## STD-06 to STD-10: Infrastructure (#27-39)
| File | # | Topics |
|------|---|--------|
| STD-06 | 27 | Lookup/Type Tables |
| STD-07 | 28-30 | State Machine, Multi-tenancy, Rate Limit |
| STD-08 | 31-33 | Backup/DR, Webhook, Reports |
| STD-09 | 34-36 | Import/Export, Email Templates, PWA |
| STD-10 | 37-39 | Circuit Breaker, Health Checks, Data Archival |

## STD-11 to STD-16: Advanced (#40-47)
| File | # | Topics |
|------|---|--------|
| STD-11 | 40-42 | Tracing (OpenTelemetry), Secrets, Scheduled Tasks |
| STD-12 | 43 | Config Governance |
| STD-13 | 44 | Fraud Detection & Audit Intelligence |
| STD-14 | 45 | Internal Collaboration Hub |
| STD-15 | 46 | Input Design Flow & Constraint-Based UI |
| STD-16 | 47 | Smart Suggestions & Human-in-the-Loop |

## Business Standards (BIZ)
| File | Topics |
|------|--------|
| BIZ-01 | Sections 1-10: Core accounting principles |
| BIZ-02 | Sections 11-16 + 17-20: Advanced + New concepts |
| BIZ-03 | Reconciliation, Controls, Entry Lifecycle, Audit Trail |

## Specification Standards (SPEC)
| File | Topics |
|------|--------|
| SPEC-01 | API Contracts |
| SPEC-02 | Database Schema |
| SPEC-03 | Integration (Payment, Tax, Email, Storage) |
| SPEC-04 | OCR, Image Processing, Data Extraction |

## Critical Rules (WAJIB)

### Database
```python
# SELALU filter tenant_id
select(Entity).where(Entity.tenant_id == tenant_id)

# SELALU soft delete
entity.is_deleted = True
entity.deleted_at = datetime.utcnow()

# SELALU UUID primary key
id = Column(UUID, primary_key=True, default=uuid4)
```

### API Response
```json
{"success": true, "data": {...}, "meta": {...}}
{"success": false, "error": {"code": "...", "message": "..."}}
```

### Permission Format
```
{module}.{resource}.{action}
pms.reservation.create
pos.order.view
```
