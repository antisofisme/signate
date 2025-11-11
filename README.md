# Digital Signage System

Enterprise-grade digital signage platform with advanced features and multi-device support.

## Overview

Complete digital signage solution with:
- **Backend API** (FastAPI + PostgreSQL) - RESTful API with Clean Architecture
- **CMS** (React + Vite + TypeScript) - Admin dashboard  
- **Player** (TypeScript + Vite) - Advanced digital signage player
- **Database** (PostgreSQL 15 + PgBouncer) - High-performance data storage
- **Cache** (Redis) - Session and API caching
- **Monitoring** (Prometheus + Grafana) - Production monitoring

## Project Structure

```
signate/
├── backend-python/        # FastAPI backend with Clean Architecture
│   ├── services/         # Modular services (auth, device, content)
│   ├── shared/          # Shared utilities and configurations
│   └── migrations/      # Database migrations
│
├── cms-vite/            # React + TypeScript admin dashboard
│   ├── src/
│   │   ├── features/    # Feature-based modules
│   │   ├── shared/      # Shared components and utilities
│   │   └── stores/      # Zustand state management
│   └── dist/            # Production build
│
├── player-vite/         # TypeScript digital signage player
│   ├── src/
│   │   ├── player/      # Video playback engine
│   │   ├── shell/       # Device activation & management
│   │   └── shared/      # Core services
│   └── dist/            # Production build
│
├── database/            # Database schemas and migrations
├── docker/              # Docker configurations
├── scripts/             # Utility and maintenance scripts
├── firebird-bridge-agent/  # PMS integration service
└── docs/                # Documentation
```

## Quick Start

### Production Deployment
```bash
cd docker
docker-compose up -d
```

### Development Setup

**Backend:**
```bash
cd backend-python
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd cms-vite
npm install
npm run dev
```

**Player:**
```bash
cd player-vite
npm install
npm run dev
```

### Access URLs

| Service | URL |
|---------|-----|
| **CMS** | http://localhost:3000 |
| **API** | http://localhost:8001 |
| **API Docs** | http://localhost:8001/docs |
| **Player** | http://localhost:8080 |
| **Prometheus** | http://localhost:9091 |
| **Grafana** | http://localhost:3001 |

## Key Features

- **Multi-tenant Architecture** - Organization-based data isolation
- **Real-time Updates** - WebSocket for instant content changes
- **Advanced Scheduling** - Recurring schedules with priorities
- **Multi-language Support** - 6 languages (EN, ID, ZH, JA, KO, AR)
- **Template Engine** - Dynamic content with variables
- **Widget System** - Clock, Weather, Text, Calendar, etc.
- **PMS Integration** - Firebird database connectivity
- **Comprehensive Analytics** - Usage tracking and reporting
- **Role-based Access Control** - Super Admin, Admin, User roles
- **High Performance** - PgBouncer pooling, Redis caching

## Default Credentials

- Username: `admin`  
- Password: `admin123`

## Documentation

All documentation has been organized in `/docs` folder:

- `/docs/phases/` - Implementation phase documentation
- `/docs/01-anthias/` - Anthias integration docs
- `/docs/02-api/` - API documentation
- `/docs/03-sprints/` - Sprint documentation
- `/docs/04-architecture/` - Architecture decisions
- `/docs/05-deployment/` - Deployment guides
- `/docs/06-features/` - Feature documentation
- `/docs/07-development/` - Development guides
- `/docs/08-operations/` - Operational procedures

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic, Celery
- **Frontend**: React 18, TypeScript, Vite, TanStack Query, Zustand
- **Player**: TypeScript, HLS.js, Service Worker, IndexedDB
- **Database**: PostgreSQL 15, PgBouncer, Redis
- **Infrastructure**: Docker, Nginx, Prometheus, Grafana
- **UI**: Tailwind CSS, shadcn/ui, Radix UI

## License

Proprietary - All rights reserved

