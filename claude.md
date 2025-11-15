# Refactoring Concept

## Overview
Refactoring dari arsitektur lama ke arsitektur baru dengan Clean Architecture:
- **Dari**: `web-admin` (React/Next.js) + `backend` (Node.js/Express) + `viewer` (HTML/JS)
- **Ke**: `cms-vite` (React/Vite) + `backend-python` (FastAPI) + `player-vite` (Vite)
- **Acuan struktur**: Clean Architecture, max 3-level directory depth
- **Acuan fitur**: web-admin lama (sebagai referensi logika bisnis yang sudah ada)

## Architecture Principles

### Backend (Python - FastAPI)
```
backend-python/
├── services/          # Modular services (auth, device, content, playlist)
│   └── [service]/
│       ├── models.py        # SQLAlchemy models
│       ├── dtos.py          # Request/Response DTOs
│       ├── routes.py        # FastAPI routes
│       ├── repositories/    # Data access layer
│       └── use_cases/       # Business logic
└── shared/            # Shared utilities (config, database, api_routes)
```

**Prinsip**:
- Clean Architecture dengan dependency injection
- Phased database schema (tidak semua tabel dibuat sekaligus)
- Repository pattern untuk data access
- Use cases untuk business logic
- Centralized API routes definition di `shared/api_routes.py`

### Frontend (React - Vite)
```
cms-vite/
├── src/
│   ├── features/      # Feature modules (auth, devices, content, playlist)
│   │   └── [feature]/
│   │       ├── api/         # API calls
│   │       ├── components/  # Feature components
│   │       ├── hooks/       # Custom hooks
│   │       └── types/       # TypeScript types
│   ├── shared/        # Shared utilities, components, layouts
│   └── stores/        # Zustand global state
```

**Tech Stack**:
- Vite + React 18 + TypeScript
- TanStack Query (server state)
- Zustand (global state)
- React Hook Form + Zod (forms & validation)
- Tailwind CSS + shadcn/ui (styling)
- Axios (HTTP client)

**Prinsip**:
- Feature-based architecture
- Separation of concerns: API / Components / Hooks / Types
- Zustand untuk global state (auth, UI)
- TanStack Query untuk server state (data fetching, caching)
- Reusable components di shared/

## Phased Development

**Phase 1**: Authentication ✅
- Backend: Login/Register endpoints, JWT tokens, Organizations
- Frontend: Login page, Auth store, API integration
- Database: users, organizations tables only

**Phase 2**: Device Management (Next)
- Backend: Device registration, heartbeat, status
- Frontend: Device list, activation, monitoring
- Database: devices table

**Phase 3**: Content Management
- Backend: Upload, validation, storage integration
- Frontend: Content upload, preview, management
- Database: contents table

**Phase 4**: Playlist Management
- Backend: Playlist CRUD, scheduling
- Frontend: Playlist builder, assignment
- Database: playlists, playlist_items tables

## Key Differences from Old Architecture

| Aspect | Old (web-admin + backend) | New (cms-vite + backend-python) |
|--------|---------------------------|--------------------------------|
| Backend Framework | Express.js (Node) | FastAPI (Python) |
| Architecture | Monolithic routes | Clean Architecture + Use Cases |
| Frontend Build | Next.js | Vite |
| State Management | Redux | Zustand + TanStack Query |
| Forms | Formik | React Hook Form + Zod |
| UI Components | Custom CSS | Tailwind + shadcn/ui |
| Database Schema | All tables at once | Phased creation |
| API Routes | Scattered in files | Centralized in api_routes.py |

## Important Notes
- **Player sudah di-refactoring ke player-vite/** ✅ - Player menggunakan Vite, bukan vanilla JS lagi
- **Referensi logika dari web-admin lama**, tapi dengan struktur lebih baik
- **Bertahap** - Satu phase selesai baru lanjut phase berikutnya
- **Testing di local dulu**, baru deploy ke server

---

# Server Information

## Production Server
- **IP Address**: 192.168.5.12
- **SSH User**: gzjbbk
- **SSH Password**: Password@2021
- **Project Directory**: `/home/gzjbbk/signate/` (CHANGED from prototipe2)

## Directory Structure on Server
```
/home/gzjbbk/signate/
├── backend-python/          # FastAPI backend ✅
├── cms-vite/                # React + Vite CMS admin ✅
├── player-vite/             # Vite player/viewer ✅
├── docker/                  # Docker compose configs
│   └── docker-compose.yml
└── .env                     # Environment variables
```

## Service Ports (ALL ON SERVER)
- **Port 8001**: Backend API (FastAPI) ✅ RUNNING - Custom-built from scratch
- **Port 3000**: CMS Admin (cms-vite - React + Vite) ✅ - Development or production
- **Port 5433**: PostgreSQL Database ✅ RUNNING
- **Port 8080**: Player/Viewer (player-vite) ✅ RUNNING - For all display devices

## URLs
- **Player/Viewer**: http://192.168.5.12:8080/ - Untuk semua display devices (monitors, browsers, WebOS TV)
- **CMS Admin**: http://localhost:3000/ atau http://192.168.5.12:3000/ - Admin dashboard
- **Backend API**: http://192.168.5.12:8001/ - REST API
- **API Docs**: http://192.168.5.12:8001/docs - Swagger/OpenAPI docs

## Current Status
✅ **Backend API** (`backend-python`) - FastAPI running in Docker (port 8001) - Custom-built from scratch
✅ **CMS Admin** (`cms-vite`) - React + Vite admin dashboard (port 3000) - Ready for development/production
✅ **Player/Viewer** (`player-vite`) - Vite player (port 8080) - For all display devices
✅ **PostgreSQL Database** (v15.14) running in Docker (port 5433) - Grade A+ schema
✅ **Device Registration** working with 6-digit activation codes
✅ **CORS Configuration** properly set for all origins
✅ **Dockerfile** optimized with PYTHONDONTWRITEBYTECODE=1
✅ **WebOS IPK** packaging via webos-app folder
✅ **Database Migrations** 001-044 all deployed and verified

## Default Credentials
- **Username**: `admin`
- **Password**: `admin123`
- **Password Hash** (bcrypt): `$2b$12$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2`

## Architecture Notes

### System Components (Custom-Built, NOT Third-Party!)
- ✅ **Backend API** (`backend-python/`): Custom FastAPI application - Clean Architecture
- ✅ **CMS Admin** (`cms-vite/`): Custom React + Vite admin dashboard - Feature-based architecture
- ✅ **Player/Viewer** (`player-vite/`): Custom Vite player - For all display devices
- ✅ **Database**: PostgreSQL 15.14 with Grade A+ standardized schema (29 tables)
- ✅ **WebOS App** (`webos-app/`): IPK package built from player-vite codebase

**Penting**: Semua komponen adalah **custom-built from scratch**, BUKAN Anthias atau third-party CMS lainnya!

### Important Implementation Details
- ⚠️ **ALL services MUST run on SERVER (192.168.5.12), NOT localhost**
- ✅ **Backend** runs in Docker container `signage-backend-python` (port 8001)
- ✅ **CMS Admin** runs on port 3000 (development or production)
- ✅ **Player/Viewer** runs on port 8080:
  - Built with Vite (NOT vanilla JS)
  - Single codebase for all platforms (monitors, browsers, WebOS TV)
  - Uses 6-digit activation code for device registration
  - Sends heartbeat every 30 seconds after activation
- ✅ **Dashboard** shows online/offline status based on `last_seen_at` < 5 minutes
- ✅ **WebOS IPK** packaging via `webos-app/` folder (copies from `player-vite/`)

## 🔴 CRITICAL: Code & Config Synchronization Protocol
**SETIAP kali melakukan perubahan code atau konfigurasi, WAJIB update di KEDUA lokasi:**

### Files yang WAJIB Sinkron:
1. **Configuration Files:**
   - `.env` (local & server)
   - `.env.example` (local & server)
   - `backend/app/core/config.py` (local & server)

2. **Source Code:**
   - Semua file `.jsx`, `.js`, `.py`, `.ts`, `.tsx` yang diubah
   - CMS Admin: `cms-vite/src/**/*`
   - Backend: `backend-python/app/**/*`
   - Player/Viewer: `player-vite/**/*` (unified codebase for all platforms)
   - WebOS App: `webos-app/**/*` (IPK packaging - copies from player-vite)

### Workflow Update:
```bash
# 1. Update di LOCAL terlebih dahulu
# Edit file yang diperlukan di /mnt/g/khoirul/signate

# 2. PASTIKAN testing lokal berhasil
npm run dev  # untuk frontend
uvicorn app.main:app --reload  # untuk backend

# 3. Sync ke SERVER menggunakan scp/rsync
sshpass -p 'Password@2021' scp -r file_yang_diubah gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/

# 4. Rebuild container di server jika diperlukan
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "cd /home/gzjbbk/prototipe2 && docker-compose -f docker/docker-compose.yml up -d --build backend-api"
```

### ⚠️ Konsekuensi Jika TIDAK Sinkron:
- ❌ Reinstall dari local akan kehilangan perubahan yang ada di server
- ❌ Perubahan konfigurasi tidak konsisten
- ❌ Bug yang sudah diperbaiki bisa muncul lagi
- ❌ Development environment berbeda dengan production

### ✅ Best Practice:
- **SELALU update LOCAL dulu, baru ke SERVER**
- **COMMIT ke Git setelah update sukses di kedua lokasi**
- **Test di local sebelum deploy ke server**
- **Dokumentasikan perubahan di changelog atau commit message**

## 🚀 Docker Compose Best Practices

### ⚠️ CRITICAL: Run from Parent Directory
**SELALU jalankan docker-compose dari parent directory, BUKAN dari subdirectory docker/**

```bash
# ✅ CORRECT - Environment variables akan terload dengan benar
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml up -d

# ❌ WRONG - CORS_ORIGINS dan env vars lainnya TIDAK akan terload!
cd /home/gzjbbk/signate/docker
docker-compose up -d
```

**Kenapa?** Karena docker-compose mencari file `.env` di current directory. Kalau dijalankan dari `docker/`, file `../.env` tidak terbaca dengan benar, menyebabkan:
- CORS_ORIGINS kosong → CORS error di frontend
- Environment variables lain tidak terload
- Backend tidak bisa connect ke services lain

### 🔧 Common Issues & Solutions

#### 1. CORS Error - "No Access-Control-Allow-Origin header"
**Symptom**: Login di web admin gagal dengan CORS error
**Root Cause**: docker-compose dijalankan dari subdirectory docker/, sehingga CORS_ORIGINS tidak terload
**Solution**:
```bash
# Stop all containers
cd /home/gzjbbk/prototipe2
docker-compose -f docker/docker-compose.yml down

# Restart from parent directory
docker-compose -f docker/docker-compose.yml up -d

# Verify CORS loaded
docker logs signage-backend 2>&1 | grep "CORS enabled"
# Should show: "CORS enabled for origins: ['http://localhost:3000', ...]"
```

#### 2. Login Gagal - "Invalid salt" Error
**Symptom**: Login returns 500 error, backend logs shows "ValueError: Invalid salt"
**Root Cause**: Password hash di database korup (bash meng-interpret dollar signs)
**Solution**:
```bash
# Reset password menggunakan SQL file (hindari escaping issue)
echo "UPDATE users SET password_hash = '\$2b\$12\$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2' WHERE username='admin';" > /tmp/reset_pass.sql

docker exec -i signage-postgres psql -U signage_user -d signage_db < /tmp/reset_pass.sql

# Verify
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT username, password_hash FROM users WHERE username='admin';"
```

#### 3. Database Init - Fresh Install
**Jika perlu reset database dari awal:**
```bash
# Stop all services
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml down --volumes

# Remove all data (HATI-HATI! Data akan hilang)
docker volume rm signate_postgres-data signate_redis-data signate_anthias-data

# Start fresh - init.sql akan dijalankan otomatis
docker-compose -f docker/docker-compose.yml up -d

# Wait for database to initialize
sleep 10

# Verify admin user exists
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT username, role FROM users WHERE username='admin';"
```

### 📋 Quick Reference Commands

```bash
# Check all services status
docker-compose -f docker/docker-compose.yml ps

# View logs for specific service
docker logs signage-backend --tail 50
docker logs signage-postgres --tail 50

# Restart specific service
docker-compose -f docker/docker-compose.yml restart backend-api

# Rebuild and restart
docker-compose -f docker/docker-compose.yml up -d --build backend-api

# Access database
docker exec -it signage-postgres psql -U signage_user -d signage_db

# Check environment variables in container
docker exec signage-backend env | grep CORS_ORIGINS
```

---

# Database Guidelines

## Database Schema Standards

**Current Status**: Grade A+ (100/100) 🎉
**PostgreSQL Version**: 15.14
**Total Tables**: 29
**Total Migrations**: 045
**Documentation**: See `docs/DATABASE_CONVENTIONS.md` and `docs/DATABASE_ERD.md`

### Quick Reference

#### Naming Conventions (ALWAYS FOLLOW)

**Tables**: 
- ✅ Plural, snake_case: `users`, `devices`, `device_commands`
- ❌ Avoid: `user`, `DeviceCommands`, `tbl_devices`

**Primary Keys**:
- ✅ Always named `id`: `id INTEGER PRIMARY KEY`
- ❌ Avoid: `user_id`, `userId`, `pk_user`

**Foreign Keys**:
- ✅ Always suffix with `_id`: `user_id`, `organization_id`, `created_by_id`
- ❌ Avoid: `user`, `creator`, `created_by`

**Timestamps**:
- ✅ Always suffix with `_at`: `created_at`, `last_seen_at`, `recorded_at`
- ❌ Avoid: `created`, `last_seen`, `timestamp`

**Booleans**:
- ✅ Always prefix: `is_active`, `is_volume_enabled`, `has_audio`, `can_edit`
- ❌ Avoid: `active`, `enabled`, `volume_enabled`

**JSON Columns**:
- ✅ Descriptive plurals: `permissions`, `metadata`, `settings`
- ❌ Avoid: `data`, `config`, `info`

#### Audit Trail Standard

Every table with user actions MUST include:
```sql
created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
updated_at TIMESTAMP WITH TIME ZONE
```

Special cases: `uploaded_by_id`, `assigned_by_id`, `added_by_id`, `deleted_by_id`

#### Multi-Tenancy Pattern

All core entities MUST include:
```sql
organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE
```

Always filter by organization_id in queries to ensure data isolation.

### Migration Workflow

#### Creating Migrations

```bash
# Migration file naming: XXX_descriptive_name.sql
# Example: 045_add_notifications_table.sql

# Structure:
-- Migration: 045
-- Description: Add notifications table
-- Date: YYYY-MM-DD

BEGIN;

-- Your SQL here
CREATE TABLE notifications (...);

-- Add indexes
CREATE INDEX idx_notifications_user ON notifications(user_id);

-- Add comments
COMMENT ON TABLE notifications IS 'User notifications and alerts';

COMMIT;
```

#### Running Migrations

```bash
# 1. Backup database first
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db" \
  > backups/pre_migration_XXX_$(date +%Y%m%d_%H%M%S).sql

# 2. Stop backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml stop backend-api"

# 3. Upload migration
sshpass -p 'Password@2021' scp backend-python/migrations/XXX_*.sql \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/migrations/

# 4. Run migration
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/XXX_*.sql"

# 5. Sync code if needed
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
  backend-python/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/

# 6. Restart backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml start backend-api"
```

### Common Patterns

#### Adding a New Table

```sql
CREATE TABLE table_name (
  -- Primary key
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  
  -- Foreign keys
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Data columns
  name VARCHAR(200) NOT NULL,
  description TEXT,
  
  -- Booleans
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE,
  
  -- Audit trail
  created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_table_name_organization ON table_name(organization_id);
CREATE INDEX idx_table_name_user ON table_name(user_id);

-- Comments
COMMENT ON TABLE table_name IS 'Description of table purpose';
```

#### SQLAlchemy Model Template

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base

class TableNameModel(Base):
    """TableName database model"""
    __tablename__ = "table_name"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Data columns
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Booleans
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Audit trail
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    user = relationship("UserModel", foreign_keys=[user_id])
    creator = relationship("UserModel", foreign_keys=[created_by_id])
```

### Breaking Changes Checklist

When renaming columns:
1. Create migration file with ALTER TABLE statements
2. Update SQLAlchemy models (Column definitions)
3. Update model relationships (foreign_keys=[...])
4. Update DTOs (Pydantic models)
5. Update repositories (_to_entity methods, queries)
6. Update use cases (attribute access)
7. Update routes (response mappings)
8. Test all affected endpoints

### Database Quality Metrics

Current status after migrations 039-045:
- FK Consistency: 100% ✅
- Timestamp Naming: 100% ✅
- Boolean Naming: 100% ✅ (16/16 columns)
- Check Constraints: 18 added ✅
- Overall Grade: **A+ (100/100)** 🎉

### Useful Database Commands

```bash
# Connect to database
docker exec -it signage-postgres psql -U signage_user -d signage_db

# List all tables
\dt

# Describe table
\d+ table_name

# Check column types
\d table_name

# List all indexes
\di

# List all constraints
\d+ table_name

# Count rows
SELECT COUNT(*) FROM table_name;

# Check for specific column naming
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE column_name LIKE '%_id' 
  AND table_schema = 'public'
ORDER BY table_name, column_name;
```

### ERD Diagram

See `docs/DATABASE_ERD.md` for:
- Complete ER diagram (Mermaid format)
- Table relationships
- Entity groupings
- Constraint documentation

### Migration History

| Migration | Description | Date | Status |
|-----------|-------------|------|--------|
| 001-010 | Initial schema | 2025-01-09 | ✅ |
| 011-038 | RBAC & improvements | 2025-11-09 | ✅ |
| 039 | Standardize FK naming | 2025-11-13 | ✅ |
| 040 | Remove duplicate role column | 2025-11-13 | ✅ |
| 041 | Rename organization_pin | 2025-11-13 | ✅ |
| 042 | Timestamp standardization | 2025-11-13 | ✅ |
| 043 | Boolean prefix standardization | 2025-11-13 | ✅ |
| 044 | Add CHECK constraints | 2025-11-13 | ✅ |
| **045** | **Complete boolean standardization** | **2025-01-13** | **✅** |

### Important Notes

- **NEVER delete migrations** - They are immutable history
- **ALWAYS backup** before running migrations
- **TEST migrations** on local copy first
- **STOP backend** during schema changes
- **VERIFY** changes after deployment
- **DOCUMENT** breaking changes in migration comments

### Resources

- Full conventions: `docs/DATABASE_CONVENTIONS.md`
- ERD diagram: `docs/DATABASE_ERD.md`
- Deployment reports: `DEPLOYMENT_SUCCESS_REPORT.md`
- API documentation: `http://192.168.5.12:8001/docs`

---

# Testing & Debugging Tools

## Playwright - Automated Browser Testing

**Installed**: ✅ `/tmp/` (npm install playwright)
**Purpose**: Automated end-to-end testing untuk web applications
**Browser Support**: Chromium, Firefox, WebKit

### Use Cases:
- ✅ Automated UI testing
- ✅ Toast notification testing
- ✅ User interaction simulation
- ✅ Screenshot & video recording
- ⭐ Basic console log capture
- ⭐ Network request tracking (basic)

### How to Use:

```javascript
const { chromium } = require('playwright');

async function testApp() {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const page = await browser.newPage();

  // Console monitoring
  page.on('console', msg => console.log(`Console: ${msg.text()}`));

  // Navigate and test
  await page.goto('http://192.168.5.12:8080/');
  await page.waitForTimeout(5000);

  // Take screenshot
  await page.screenshot({ path: '/tmp/screenshot.png' });

  await browser.close();
}

testApp();
```

### Example Test Scripts:
- `/tmp/test-player-toast.js` - Toast notification testing
- Run: `cd /tmp && node test-player-toast.js`

### Strengths:
- ⭐⭐⭐⭐⭐ Fast test execution
- ⭐⭐⭐⭐⭐ Multi-browser support
- ⭐⭐⭐⭐⭐ Automated testing
- ⭐⭐⭐ Screenshot & video
- ⭐⭐ Console logs (manual filtering)

### Limitations:
- ⭐⭐ Performance profiling
- ⭐⭐ Network analysis (basic only)
- ⭐ Memory profiling (not available)
- ⭐ Real-time inspection (limited)

---

## Chrome DevTools MCP - Deep Debugging & Analysis

**Installed**: ✅ `/tmp/chrome-devtools-mcp/`
**Purpose**: AI-powered browser inspection dengan full Chrome DevTools access
**MCP Server**: Model Context Protocol for AI agents

### Use Cases:
- ⭐⭐⭐⭐⭐ Real-time console monitoring dengan categorization
- ⭐⭐⭐⭐⭐ Network waterfall analysis (timing, headers, responses)
- ⭐⭐⭐⭐⭐ Performance profiling (traces, metrics, memory)
- ⭐⭐⭐⭐⭐ Live DOM inspection
- ⭐⭐⭐⭐⭐ JavaScript execution & debugging
- ⭐⭐⭐⭐⭐ WebSocket monitoring

### Installation:

```bash
# Clone repository
cd /tmp
git clone https://github.com/ChromeDevTools/chrome-devtools-mcp.git
cd chrome-devtools-mcp

# Install dependencies
npm install

# Build (skip experimental-strip-types for Node 20)
npx tsc

# Run post-build script manually (create mocks)
# (See installation script in /tmp/run-postbuild.mjs)
```

### How to Use:

#### Method 1: As MCP Server (CLI)
```bash
cd /tmp/chrome-devtools-mcp
node build/src/index.js --help

# Launch with options
node build/src/index.js --headless=false --viewport=1920x1080
```

#### Method 2: With Playwright (Hybrid Approach)
```javascript
const { chromium } = require('playwright');

async function testWithDevTools() {
  // Launch with remote debugging
  const browser = await chromium.launch({
    headless: false,
    args: ['--remote-debugging-port=9222']
  });

  const page = await browser.newPage();

  // Categorized console monitoring
  const logs = { toast: [], errors: [], warnings: [] };

  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[Toast]')) logs.toast.push(text);
    if (msg.type() === 'error') logs.errors.push(text);
  });

  // Network monitoring
  page.on('response', async response => {
    const request = response.request();
    if (request.resourceType() === 'xhr') {
      console.log(`API: ${request.method()} ${request.url()} - ${response.status()}`);
    }
  });

  // Performance metrics
  const metrics = await page.evaluate(() => {
    const perf = performance.getEntriesByType('navigation')[0];
    return {
      domLoad: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
      totalTime: perf.loadEventEnd - perf.fetchStart
    };
  });

  // Memory usage
  const memory = await page.evaluate(() => ({
    usedHeap: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
    totalHeap: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB'
  }));

  console.log('Performance:', metrics);
  console.log('Memory:', memory);
  console.log('Console Logs:', logs);
}
```

### Example Test Scripts:
- `/tmp/test-player-devtools.js` - Comprehensive DevTools analysis
- Run: `cd /tmp && node test-player-devtools.js`

### Available Tools (26 total):
1. **Input Automation** (8 tools): click, type, scroll, etc.
2. **Navigation** (6 tools): goto, reload, back, forward
3. **Emulation** (2 tools): viewport, device emulation
4. **Performance** (3 tools): traces, metrics, profiling
5. **Network** (2 tools): requests, responses, timing
6. **Debugging** (5 tools): console, DOM inspection, JS execution

### Strengths:
- ⭐⭐⭐⭐⭐ Real-time console categorization
- ⭐⭐⭐⭐⭐ Network waterfall analysis
- ⭐⭐⭐⭐⭐ Performance profiling
- ⭐⭐⭐⭐⭐ Memory leak detection
- ⭐⭐⭐⭐⭐ Live DOM inspection
- ⭐⭐⭐⭐⭐ Understanding WHY (forensic debugging)

### Comparison: Playwright vs Chrome DevTools MCP

| Feature | Playwright | Chrome DevTools MCP |
|---------|-----------|---------------------|
| Automated Testing | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Console Debugging | ⭐⭐ (manual) | ⭐⭐⭐⭐⭐ (automatic) |
| Network Analysis | ⭐⭐ (basic) | ⭐⭐⭐⭐⭐ (detailed) |
| Performance Profiling | ⭐ | ⭐⭐⭐⭐⭐ |
| Memory Analysis | ❌ | ⭐⭐⭐⭐⭐ |
| Real-time Inspection | ⭐ | ⭐⭐⭐⭐⭐ |
| Multi-browser Support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ (Chromium only) |
| Understanding WHY | ⭐⭐ | ⭐⭐⭐⭐⭐ |

### When to Use What:

**Use Playwright when:**
- Running automated test suites
- Need multi-browser testing
- Simple UI interaction testing
- Screenshot/video recording
- Fast test execution needed

**Use Chrome DevTools MCP when:**
- Debugging complex issues
- Performance optimization needed
- Memory leak investigation
- Network timing analysis
- Need to understand WHY app behaves certain way
- Real-time inspection of running app
- WebSocket debugging

**Use Both (Hybrid) when:**
- Comprehensive testing with deep analysis
- Test automation + performance profiling
- Need both WHAT works and WHY it works

### Test Results Example (Player-Vite):

**From Chrome DevTools MCP Analysis:**
```
📊 Results Summary:
- Console Messages: 47 (categorized automatically)
  - Toast logs: 10
  - Clear Cache logs: 6
  - Errors: 1 (non-critical)
  - Warnings: 0

- Network Requests: 9 total
  - API calls: 6 (100% success rate)
  - Resources: 3

- Performance Metrics:
  - DOM Load: 96ms (excellent)
  - Memory: 3.07 MB (very light)
  - Clear Cache Flow: 3.5s total

- Architecture Validation:
  - Toast z-index: 200000 ✅
  - Shell/Player separation: ✅
  - Toast persistence during reload: ✅
```

### Files Generated:
- **Test scripts**: `/tmp/test-player-toast.js`, `/tmp/test-player-devtools.js`
- **Screenshots**: `/tmp/toast-test-screenshot.png`, `/tmp/devtools-test-screenshot.png`
- **Reports**: `/tmp/TOAST_TEST_REPORT.md`, `/tmp/CHROME_DEVTOOLS_ANALYSIS_REPORT.md`

### Best Practices:

1. **Use Playwright for CI/CD**
   - Fast automated tests
   - Multi-browser compatibility
   - Regression testing

2. **Use Chrome DevTools MCP for Development**
   - Deep debugging during development
   - Performance optimization
   - Understanding complex issues

3. **Combine Both for Quality Assurance**
   - Playwright: Verify WHAT works
   - DevTools MCP: Understand WHY it works
   - Comprehensive test coverage

4. **Console Log Categorization**
   ```javascript
   // Auto-categorize logs by prefix
   const logs = {
     toast: [],
     clearCache: [],
     hardReset: [],
     shell: [],
     player: [],
     errors: [],
     warnings: []
   };

   page.on('console', msg => {
     const text = msg.text();
     if (text.includes('[Toast]')) logs.toast.push(text);
     if (text.includes('[ClearCache]')) logs.clearCache.push(text);
     // etc...
   });
   ```

5. **Performance Monitoring**
   ```javascript
   // Track performance metrics
   const metrics = await page.evaluate(() => {
     const perf = performance.getEntriesByType('navigation')[0];
     return {
       domLoad: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
       totalTime: perf.loadEventEnd - perf.fetchStart,
       memory: {
         used: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
         total: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB'
       }
     };
   });
   ```

### Resources:
- Playwright Docs: https://playwright.dev/
- Chrome DevTools MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp
- Test Reports: `/tmp/TOAST_TEST_REPORT.md`, `/tmp/CHROME_DEVTOOLS_ANALYSIS_REPORT.md`

