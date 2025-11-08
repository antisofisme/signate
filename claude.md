# Refactoring Concept

## Overview
Refactoring dari arsitektur lama ke arsitektur baru dengan Clean Architecture:
- **Dari**: `web-admin` (React/Next.js) + `backend` (Node.js/Express)
- **Ke**: `cms-vite` (React/Vite) + `backend-python` (FastAPI)
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
- **Player sudah di-refactoring ke player-vanillajs/** ✅ - Sudah Clean Architecture, jangan diubah lagi
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
├── backend-python/          # FastAPI backend
├── cms-vite/                # React frontend (future)
├── player-vanillajs/        # Vanilla JS player/viewer
├── docker/                  # Docker compose configs
│   └── docker-compose.yml
└── .env                     # Environment variables
```

## Service Ports (ALL ON SERVER)
- **Port 8000**: Anthias (Digital Signage CMS)
- **Port 8001**: Backend API (FastAPI in Docker) ✅ RUNNING
- **Port 3000**: Web Admin (React/Vite Dev Mode) - Run locally, proxies API to server
- **Port 5433**: PostgreSQL Database ✅ RUNNING
- **Port 8080**: Viewer (Static HTML) ✅ RUNNING - For monitors, browsers, and WebOS TV

## URLs
- **Viewer**: http://192.168.5.12:8080/ (untuk monitor, browser, dan WebOS TV)
- **Web Admin**: http://localhost:3000/ (development - proxies to server)
- **Backend API**: http://192.168.5.12:8001/
- **API Docs**: http://192.168.5.12:8001/docs

## Current Status (ALL FIXED!)
✅ Backend API running in Docker on server (port 8001) - REBUILT with CORS fix!
✅ PostgreSQL database running in Docker on server (port 5433)
✅ Viewer running on server (port 8080) - Unified viewer for monitors, browsers, and WebOS TV
✅ Viewer configured to use correct backend (port 8001, NOT 8000!)
✅ CORS configuration includes port 8080 - Registration working!
✅ Web Admin can run locally and proxy API calls to server
✅ Dockerfile optimized with PYTHONDONTWRITEBYTECODE=1 to prevent build failures
✅ WebOS IPK packaging via webos-app folder (copies from viewer)

## Default Credentials
- **Username**: `admin`
- **Password**: `admin123`
- **Password Hash** (bcrypt): `$2b$12$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2`

## Important Notes
- ⚠️ **ALL services MUST run on SERVER (192.168.5.12), NOT localhost**
- ✅ Backend API is running in Docker container (signage-backend)
- ✅ **Unified Viewer Architecture:**
  - **viewer/** (port 8080) → Single codebase for all platforms (monitors, browsers, WebOS TV)
  - **webos-app/** → Packaging folder for WebOS IPK (copies from viewer + adds appinfo.json)
  - Uses 6-digit activation code for device registration
- ✅ Viewer points to correct backend (8001) - device registration working!
- Viewer has heartbeat mechanism (sends every 30s after activation)
- Dashboard shows online/offline based on last_seen < 5 minutes
- Web Admin development server (localhost:3000) proxies /api requests to server backend

## 🔴 CRITICAL: Code & Config Synchronization Protocol
**SETIAP kali melakukan perubahan code atau konfigurasi, WAJIB update di KEDUA lokasi:**

### Files yang WAJIB Sinkron:
1. **Configuration Files:**
   - `.env` (local & server)
   - `.env.example` (local & server)
   - `backend/app/core/config.py` (local & server)

2. **Source Code:**
   - Semua file `.jsx`, `.js`, `.py` yang diubah
   - Frontend: `web-admin/src/**/*`
   - Backend: `backend/app/**/*`
   - Viewer: `viewer/**/*` (unified codebase for all platforms)
   - WebOS App: `webos-app/**/*` (IPK packaging - copies from viewer)

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
