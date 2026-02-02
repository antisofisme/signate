# ARSAKAHUB - Multi-Project Repository

Repository ini berisi beberapa project ARSAKA dengan domain berbeda.

---

## Projects Overview

| Project | Domain | Status | Description |
|---------|--------|--------|-------------|
| **ARSAKA_PANDAWA** | Enterprise Hospitality | Planning | Full-stack hospitality platform (14 modules) |
| **ARSAKA_PUGUH** | Decision Engine | Active | Constitutional law system for AI decisions |
| **ARSAKA_MANTRA** | Decision Visibility | Active | MANTRA constitutional law dashboard |
| **ARSAKA_SWARA** | Voice Assistant | Planning | Jarvis-like voice control for Claude CLI |
| **ARSAKA_TUTUR** | Chat AI | Active | AI Chat service with RAG |
| **Signage (Legacy)** | Digital Signage | Production | Digital signage CMS + Player |

---

## Project Details

### ARSAKA_PANDAWA
Enterprise Hospitality Platform dengan 14 modules:
- PMS, POS, HRM, Accounting, Inventory, Procurement
- Asset, Guest, Channel, Signage, Supplier, IoT, Menu, Platform

**Tech**: FastAPI + React + TimescaleDB + Redis + RabbitMQ
**Docs**: `ARSAKA_PANDAWA/docs/`

### ARSAKA_PUGUH
Decision Engine dengan constitutional law enforcement:
- Phase A+: Decision visibility dashboard
- Nomad-based deployment

**Tech**: FastAPI + React + PostgreSQL + Nomad
**Docs**: `ARSAKA_PUGUH/docs/`

### ARSAKA_MANTRA
MANTRA Constitutional Law System:
- Layer 0: Core principles (immutable)
- Layer 1: Decisions (append-only)
- Layer 2: Implementations (mutable)

**Tech**: FastAPI + React + PostgreSQL
**Docs**: `ARSAKA_MANTRA/docs/`

### ARSAKA_SWARA
Voice Assistant untuk Claude CLI:
- Hotkey-triggered voice input
- Speech-to-text integration

**Tech**: Python + Cloud STT
**Docs**: `ARSAKA_SWARA/docs/`

### ARSAKA_TUTUR
AI Chat Service dengan RAG:
- Multi-provider AI (OpenAI, DeepSeek, Groq)
- Vector search dengan Qdrant
- Conversation memory

**Tech**: FastAPI + React + PostgreSQL + Qdrant
**Docs**: `ARSAKA_TUTUR/docs/`

### Signage (Legacy)
Digital Signage Platform:
- CMS Admin untuk manage content
- Player untuk display devices
- WebOS IPK packaging

**Tech**: FastAPI + React + Vite + PostgreSQL
**Docs**: `docs/` (root level)

---

## Repository Structure

```
signate/
├── ARSAKA_PANDAWA/      # Enterprise hospitality platform
├── ARSAKA_PUGUH/        # Decision engine
├── ARSAKA_MANTRA/       # MANTRA constitutional law
├── ARSAKA_SWARA/        # Voice assistant
├── ARSAKA_TUTUR/        # AI Chat service
│
├── backend-python/      # Legacy signage backend
├── cms-vite/            # Legacy signage CMS
├── player-vite/         # Legacy signage player
│
├── docs/                # Shared & legacy docs
│   ├── operations/      # Server, Docker, Deployment
│   ├── database/        # DB conventions
│   └── testing/         # Testing tools
│
└── docker/              # Docker compose configs
```

---

## Common Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11 + FastAPI |
| Frontend | React 18 + TypeScript + Vite |
| Database | PostgreSQL / TimescaleDB |
| State | Zustand + TanStack Query |
| Forms | React Hook Form + Zod |
| UI | Tailwind CSS + shadcn/ui |

---

## Critical Rules (All Projects)

### DO
- Use Clean Architecture patterns
- Use `organization_id` / `tenant_id` for multi-tenancy
- Use soft delete (`is_deleted`, `deleted_at`)
- Use timestamps (`created_at`, `updated_at`)
- Test locally before deploy

### DON'T
- Hardcode credentials (use `.env`)
- Bypass permission checks
- Commit directly to main branch
- Edit files in `/docs/archive/`

---

## Naming Conventions

### Python (Backend)
| Type | Convention | Example |
|------|------------|---------|
| Variables/functions | snake_case | `get_device()` |
| Classes | PascalCase | `DeviceService` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |

### TypeScript (Frontend)
| Type | Convention | Example |
|------|------------|---------|
| Variables/functions | camelCase | `getDevice()` |
| Components | PascalCase | `DeviceCard` |
| Types/Interfaces | PascalCase | `DeviceType` |

### Database
| Type | Convention | Example |
|------|------------|---------|
| Tables | snake_case, plural | `devices` |
| Primary keys | `id` | `id INTEGER` |
| Foreign keys | `*_id` suffix | `user_id` |
| Timestamps | `*_at` suffix | `created_at` |
| Booleans | `is_*`, `has_*`, `can_*` | `is_active` |

---

## API Response Format

```json
// Success
{ "success": true, "data": {...}, "meta": {...} }

// Error
{ "success": false, "error": { "code": "...", "message": "..." } }
```

---

## Server Information

| Server | IP | Purpose |
|--------|----|---------|
| VPS Production | 72.61.209.224 | ARSAKA_PUGUH, ARSAKA_MANTRA, ARSAKA_TUTUR |
| Local Network | 192.168.5.12 | Legacy Signage development |

**Details**: See `docs/operations/SERVER_ACCESS.md`

---

## Quick Links

### Operations
| Topic | File |
|-------|------|
| Server Access | `docs/operations/SERVER_ACCESS.md` |
| Docker Commands | `docs/operations/DOCKER_RUNBOOK.md` |
| Deployment | `docs/operations/DEPLOYMENT.md` |
| Cloudflare Setup | `docs/CLOUDFLARE-SETUP-GUIDE.md` |

### Database
| Topic | File |
|-------|------|
| Conventions | `docs/database/DATABASE_CONVENTIONS.md` |
| ERD | `docs/database/DATABASE_ERD.md` |

### Testing
| Topic | File |
|-------|------|
| Tools | `docs/testing/TOOLS.md` |

### Project-Specific
| Project | Main Doc |
|---------|----------|
| ARSAKA_PANDAWA | `ARSAKA_PANDAWA/README.md` |
| ARSAKA_PUGUH | `ARSAKA_PUGUH/README.md` |
| ARSAKA_MANTRA | `ARSAKA_MANTRA/README.md` |
| ARSAKA_SWARA | `ARSAKA_SWARA/README.md` |
| ARSAKA_TUTUR | `ARSAKA_TUTUR/README.md` |

---

## Working on Specific Project

Saat bekerja pada project tertentu, baca dulu:

1. **ARSAKA_PANDAWA**: `.claude/CLAUDE.md` (detail standards)
2. **ARSAKA_PUGUH**: `ARSAKA_PUGUH/docs/` folder
3. **ARSAKA_MANTRA**: `ARSAKA_MANTRA/docs/` folder
4. **ARSAKA_SWARA**: `ARSAKA_SWARA/README.md`
5. **ARSAKA_TUTUR**: `ARSAKA_TUTUR/README.md`
6. **Legacy Signage**: `docs/` folder (root level)
