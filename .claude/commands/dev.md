---
description: Start development workflow for PROJECT_BESAR
---

# Development Command

Memulai development workflow.

## Langkah:

1. **Check Environment**
   ```bash
   # Verify Docker running
   docker ps

   # Verify PostgreSQL
   docker exec -it postgres pg_isready

   # Verify Redis
   docker exec -it redis redis-cli ping
   ```

2. **Start Services**
   ```bash
   # Backend
   cd PROJECT_BESAR/backend
   source venv/bin/activate
   uvicorn app.main:app --reload

   # Frontend
   cd PROJECT_BESAR/frontend
   bun dev
   ```

3. **Run Migrations**
   ```bash
   cd PROJECT_BESAR/backend
   alembic upgrade head
   ```

4. **Verify Health**
   - Backend: http://localhost:8000/health
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

## Quick Start
```bash
# All-in-one dengan docker-compose
cd PROJECT_BESAR
docker-compose up -d
```

## Troubleshooting
- Port conflict: Check `lsof -i :8000` atau `:3000`
- DB connection: Verify `.env` settings
- Migration error: Check `alembic history`
