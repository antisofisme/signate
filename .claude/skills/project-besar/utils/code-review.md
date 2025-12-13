---
description: Code review checklist for PROJECT_BESAR
---

# Code Review Checklist

## Backend (Python/FastAPI)

### Security (CRITICAL)
- [ ] **tenant_id**: Filter di SEMUA queries
- [ ] **SQL Injection**: Parameterized queries only (no f-string)
- [ ] **Permission**: Check di setiap endpoint
- [ ] **Input Validation**: Pydantic untuk semua input
- [ ] **No Sensitive Logs**: Password, token tidak di-log
- [ ] **Rate Limiting**: Endpoint kritis dibatasi

### Authentication
- [ ] JWT RS256 algorithm
- [ ] Token expiry proper
- [ ] httpOnly cookie untuk refresh token

### Code Quality
- [ ] Naming convention: snake_case
- [ ] Type hints lengkap
- [ ] Docstring untuk public functions
- [ ] Error handling proper
- [ ] Logging untuk debugging

### Database
- [ ] UUID untuk primary key
- [ ] Soft delete (is_deleted, deleted_at)
- [ ] Index pada tenant_id dan FK
- [ ] Migration reversible
- [ ] No N+1 queries

### Testing
- [ ] Unit test untuk logic
- [ ] Integration test untuk API
- [ ] Coverage >= 80%

---

## Frontend (React/TypeScript)

### Security (CRITICAL)
- [ ] **XSS**: No dangerouslySetInnerHTML
- [ ] **Sanitization**: DOMPurify untuk user content
- [ ] **Token Storage**: Memory only (bukan localStorage)
- [ ] **CSRF**: X-CSRF-Token di API client
- [ ] **CSP**: Headers configured

### Code Quality
- [ ] TypeScript strict mode
- [ ] No `any` types
- [ ] Component naming: PascalCase
- [ ] Hooks naming: camelCase

### Performance
- [ ] Lazy loading untuk routes
- [ ] Memoization untuk expensive ops
- [ ] Optimistic updates

### Testing
- [ ] Component tests dengan Testing Library
- [ ] Coverage >= 80%

---

## Dependencies

### Security Scan
- [ ] `pip-audit`: No critical/high
- [ ] `npm audit`: No critical/high
- [ ] No banned packages (event-stream, etc.)
- [ ] Licenses approved (MIT, Apache-2.0, BSD)

### Updates
- [ ] Critical vuln: Fix dalam 24h
- [ ] High vuln: Fix dalam 7 days
- [ ] Dependencies < 30 days old

---

## Infrastructure

### Security
- [ ] WAF rules active
- [ ] Rate limiting enabled
- [ ] Security headers set
- [ ] TLS 1.3 only

---

## Common

### Git
- [ ] Commit message descriptive
- [ ] No sensitive data committed
- [ ] Branch naming sesuai convention
- [ ] No secrets in code (use vault)

### Documentation
- [ ] README updated jika perlu
- [ ] API docs updated
- [ ] Breaking changes documented

---

## Quick Security Checks

```bash
# Backend
grep -r "f\"SELECT\|f\"INSERT" app/          # SQL injection
grep -r "tenant_id" app/routers/             # Must be in every query
bandit -r app/ -ll                           # Security linter

# Frontend
grep -r "dangerouslySetInnerHTML" src/       # XSS risk
grep -r "localStorage.*token" src/           # Token exposure
grep -r "eval(" src/                         # Code injection

# Dependencies
pip-audit --strict
npm audit --audit-level=high
```
