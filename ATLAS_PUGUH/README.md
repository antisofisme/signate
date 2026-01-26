# ATLAS_PUGUH - Constitutional Law System for AI Decisions

**Enterprise SaaS Platform for Decision Engine & Workflow Orchestration**

---

## Overview

ATLAS_PUGUH is a multi-tenant SaaS platform that provides:

- **Decision Engine**: Create and manage decision rules with version control
- **Workflow Orchestration**: Approval workflows with escalation support
- **Constitutional Law**: Layered governance for AI decisions
- **Multi-tenant Architecture**: Organizations with project isolation
- **Payment Integration**: Midtrans subscription billing (IDR)

---

## Features

### Authentication & Authorization
- Email/password registration with verification
- OAuth support (Google, GitHub)
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)

### Multi-Tenant Management
- Organization management with invitations
- Member roles: Owner, Admin, Member, Viewer
- Project-level resource isolation
- Cross-project rule sharing

### Billing & Subscriptions
- Subscription plans: Free, Starter, Pro, Enterprise
- Midtrans payment gateway (GoPay, OVO, Bank Transfer, Cards)
- Usage metering and limit enforcement
- Invoice history and management

### Core Domains
1. **IAM**: Users, Roles, Permissions, Service Accounts
2. **Tenant**: Organizations, Members, Isolation
3. **Decision**: Rules, Versions, Types, History
4. **Workflow**: Approvals, Escalations, Status
5. **Control**: Audit Trail, Events, Metrics

---

## Quick Start

### Prerequisites
- Node.js 18+ or Bun 1.0+
- Python 3.11+
- PostgreSQL 15+

### Installation

```bash
# Clone and setup
cd ATLAS_PUGUH

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
bun install
```

### Configuration

Create `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/atlas_puguh
JWT_SECRET_KEY=your-secret-key
MIDTRANS_SERVER_KEY=SB-xxx
MIDTRANS_CLIENT_KEY=SB-xxx
```

### Run

```bash
# Backend (port 8001)
uvicorn core.app:app --reload --port 8001

# Frontend (port 5173)
bun run dev
```

### Access

- Frontend: http://localhost:5173
- API Docs: http://localhost:8001/api/docs

See [Quick Start Guide](./docs/QUICKSTART.md) for detailed instructions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ATLAS_PUGUH PLATFORM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Landing    │  │    Auth      │  │   Billing    │           │
│  │    Page      │  │   Module     │  │   Module     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                  TENANT CONTEXT                       │       │
│  │  ┌────────────────────────────────────────────────┐  │       │
│  │  │               PROJECT CONTEXT                   │  │       │
│  │  │                                                 │  │       │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │  │       │
│  │  │  │   IAM   │ │Decision │ │Workflow │          │  │       │
│  │  │  └─────────┘ └─────────┘ └─────────┘          │  │       │
│  │  │                                                 │  │       │
│  │  │  ┌─────────┐ ┌─────────┐                       │  │       │
│  │  │  │ Control │ │  Audit  │                       │  │       │
│  │  │  └─────────┘ └─────────┘                       │  │       │
│  │  └────────────────────────────────────────────────┘  │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Clean Architecture

```
core/
├── auth/               # Authentication module
│   ├── domain/         # Entities, events
│   ├── interfaces/     # Repository contracts
│   ├── adapters/       # PostgreSQL implementations
│   ├── use_cases/      # Business logic
│   └── api/            # FastAPI routes
│
├── tenant/             # Tenant management
├── project/            # Project isolation
├── billing/            # Payment & subscriptions
├── decision/           # Decision engine
├── workflow/           # Workflow orchestration
├── control/            # Audit & monitoring
└── shared/             # Security, health, utils
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](./docs/QUICKSTART.md) | Get running in 5 minutes |
| [User Guide](./docs/USER_GUIDE.md) | Complete user documentation |
| [API Overview](./docs/API_OVERVIEW.md) | API reference |
| [Deployment Checklist](./docs/DEPLOYMENT_CHECKLIST.md) | Production deployment |

### Layer Documentation (Constitutional Law)

| Layer | Documents |
|-------|-----------|
| Layer 0 | Core principles (immutable) |
| Layer 1 | Architectural decisions (append-only) |
| Layer 2 | Implementation specs (mutable) |

---

## Subscription Plans

| Plan | Price (IDR/mo) | Projects | Decisions/mo | Team |
|------|----------------|----------|--------------|------|
| Free | 0 | 1 | 1,000 | 3 |
| Starter | 290,000 | 5 | 10,000 | 10 |
| Pro | 990,000 | Unlimited | 100,000 | Unlimited |
| Enterprise | Custom | Custom | Custom | Custom |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11 + FastAPI |
| Frontend | React 18 + TypeScript + Vite |
| Database | PostgreSQL 15 |
| State | Zustand + TanStack Query |
| Forms | React Hook Form + Zod |
| UI | Tailwind CSS + shadcn/ui |
| Payment | Midtrans |
| Deployment | Nomad + Consul + Traefik |

---

## Development Status

### Completed Phases

- [x] **Phase 0**: Layer 0 Documentation
- [x] **Phase 1A**: Backend Auth (registration, login, OAuth)
- [x] **Phase 1B**: Frontend Auth + Landing Page
- [x] **Phase 2**: Multi-Tenant Management
- [x] **Phase 3**: Payment & Billing (Midtrans)
- [x] **Phase 4**: Project Support
- [x] **Phase 5**: Migration & Polish

### Production Ready
- ✅ Authentication (email + OAuth)
- ✅ Multi-tenant isolation
- ✅ Project-level scoping
- ✅ Subscription billing
- ✅ Security hardening
- ✅ Documentation complete

---

## Contributing

1. Read the [Contributing Guide](./CONTRIBUTING.md)
2. Follow the coding standards in [CLAUDE.md](../.claude/CLAUDE.md)
3. Submit PRs with tests

---

## License

Proprietary - ATLAS Hub

---

## Support

- **Documentation**: [docs/](./docs/)
- **API Status**: `/health`
- **Support**: support@atlashub.com
- **Issues**: [GitHub Issues](https://github.com/atlashub/signate/issues)

---

**Version**: 1.0.0 (SaaS)
**Last Updated**: January 2026
