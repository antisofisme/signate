---
description: Run code review for PROJECT_BESAR changes
---

# Code Review Command

Review perubahan code sebelum commit/PR.

## Automated Checks

1. **Linting**
   ```bash
   # Backend
   cd PROJECT_BESAR/backend
   ruff check .
   mypy app

   # Frontend
   cd PROJECT_BESAR/frontend
   bun lint
   bun typecheck
   ```

2. **Tests**
   ```bash
   # Backend
   pytest --cov=app --cov-report=term-missing

   # Frontend
   bun test
   ```

3. **Security Scan**
   ```bash
   # Dependencies
   pip-audit
   bun audit

   # Code
   bandit -r app
   ```

## Manual Checklist

### Backend
- [ ] tenant_id filter di semua queries
- [ ] Soft delete implementation
- [ ] Type hints lengkap
- [ ] Error handling proper
- [ ] Unit tests added

### Frontend
- [ ] TypeScript strict compliance
- [ ] No console.log
- [ ] Loading/error states handled
- [ ] Component tests added

### Database
- [ ] Migration reversible
- [ ] Indexes proper
- [ ] No breaking changes

## Output
Generate summary dengan:
- Files changed
- Issues found
- Recommendations
- Approval status
