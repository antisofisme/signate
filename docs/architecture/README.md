# Architecture Documentation

Dokumentasi untuk system architecture, design decisions, dan integration patterns.

## Files

### Architecture Reviews & Audits
- **ARCHITECTURE_AUDIT_2025-11-12.md** - Architecture audit report (Nov 12, 2025)
- **ARCHITECTURE_AUDIT_REPORT.md** - Comprehensive architecture audit
- **INTEGRATION_ANALYSIS.md** - Integration analysis dan patterns

### Implementation Analysis
- **IMPLEMENTATION_GAPS_ANALYSIS.md** - Implementation gaps analysis
- **MAPPING_INDEX.md** - Architecture mapping index
- **TODO_PHASE3_USER_ORG.md** - Phase 3 TODO (User & Organization features)

### Deployment
- **DEPLOYMENT_GUIDE.md** - Deployment guide dan procedures

## Architecture Principles

### Backend (Python - FastAPI)
- **Clean Architecture** dengan dependency injection
- **Repository Pattern** untuk data access
- **Use Cases** untuk business logic
- **Phased database schema** (not all tables at once)
- **Centralized API routes** definition

### Frontend (React - Vite)
- **Feature-based architecture**
- **Separation of concerns**: API / Components / Hooks / Types
- **Zustand** untuk global state (auth, UI)
- **TanStack Query** untuk server state (data fetching, caching)
- **Reusable components** di shared/

### Player (Vite)
- **Shell/Player separation**
- **Service-based architecture**
- **Widget system** untuk modular content
- **WebSocket** untuk real-time updates

## System Components
- **Backend API** (FastAPI) - Port 8001
- **CMS Admin** (React + Vite) - Port 3000
- **Player/Viewer** (Vite) - Port 8080
- **Database** (PostgreSQL 15.14) - Port 5433

## Related Documentation
- Backend: `/docs/backend-docs/ARCHITECTURE.md`
- Database: `/docs/database/`
- API: `/docs/api/`
- Features: `/docs/features/`

---

Last updated: 2025-11-26
