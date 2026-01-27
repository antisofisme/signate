# ATLASHUB - Multi-Project Repository

Repository ini berisi beberapa project ATLAS dengan domain berbeda.

---

## Projects Overview

| Project | Domain | Status | Description |
|---------|--------|--------|-------------|
| **ATLAS_PANDAWA** | Enterprise Hospitality | 📋 Planning | Full-stack hospitality platform (14 modules) |
| **ATLAS_PUGUH** | Decision Engine | 🚧 Active | Constitutional law system for AI decisions |
| **ATLAS_MANTRA** | Decision Visibility | 🚧 Active | MANTRA constitutional law dashboard |
| **ATLAS_SEMAR** | Voice Assistant | 📋 Planning | Jarvis-like voice control for Claude CLI |
| **Signage (Legacy)** | Digital Signage | ✅ Production | Digital signage CMS + Player |

---

## Project Details

### ATLAS_PANDAWA
Enterprise Hospitality Platform dengan 14 modules:
- PMS, POS, HRM, Accounting, Inventory, Procurement
- Asset, Guest, Channel, Signage, Supplier, IoT, Menu, Platform

**Tech**: FastAPI + React + TimescaleDB + Redis + RabbitMQ
**Docs**: `ATLAS_PANDAWA/docs/`

### ATLAS_PUGUH
Decision Engine dengan constitutional law enforcement:
- Phase A+: Decision visibility dashboard
- Nomad-based deployment

**Tech**: FastAPI + React + PostgreSQL + Nomad
**Docs**: `ATLAS_PUGUH/docs/`

### ATLAS_MANTRA
MANTRA Constitutional Law System:
- Layer 0: Core principles (immutable)
- Layer 1: Decisions (append-only)
- Layer 2: Implementations (mutable)

**Tech**: FastAPI + React + PostgreSQL
**Docs**: `ATLAS_MANTRA/docs/`

### ATLAS_SEMAR
Voice Assistant untuk Claude CLI:
- Hotkey-triggered voice input
- Speech-to-text integration

**Tech**: Python + Cloud STT
**Docs**: `ATLAS_SEMAR/docs/`

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
├── ATLAS_PANDAWA/       # Enterprise hospitality platform
├── ATLAS_PUGUH/         # Decision engine
├── ATLAS_MANTRA/        # MANTRA constitutional law
├── ATLAS_SEMAR/         # Voice assistant
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
- ✅ Use Clean Architecture patterns
- ✅ Use `organization_id` / `tenant_id` for multi-tenancy
- ✅ Use soft delete (`is_deleted`, `deleted_at`)
- ✅ Use timestamps (`created_at`, `updated_at`)
- ✅ Test locally before deploy

### DON'T
- ❌ Hardcode credentials (use `.env`)
- ❌ Bypass permission checks
- ❌ Commit directly to main branch
- ❌ Edit files in `/docs/archive/`

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
| VPS Production | 31.97.111.175 | ATLAS_PUGUH, ATLAS_MANTRA |
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
| ATLAS_PANDAWA | `ATLAS_PANDAWA/README.md` |
| ATLAS_PUGUH | `ATLAS_PUGUH/README.md` |
| ATLAS_MANTRA | `ATLAS_MANTRA/README.md` |
| ATLAS_SEMAR | `ATLAS_SEMAR/README.md` |

---

## Working on Specific Project

Saat bekerja pada project tertentu, baca dulu:

1. **ATLAS_PANDAWA**: `.claude/CLAUDE.md` (detail standards)
2. **ATLAS_PUGUH**: `ATLAS_PUGUH/docs/` folder
3. **ATLAS_MANTRA**: `ATLAS_MANTRA/docs/` folder
4. **ATLAS_SEMAR**: `ATLAS_SEMAR/README.md`
5. **Legacy Signage**: `docs/` folder (root level)
