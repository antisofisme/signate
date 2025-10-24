# Smart TV Digital Signage System

Sistem digital signage terintegrasi untuk Smart TV WebOS dan Monitor Browser dengan manajemen konten terpusat menggunakan Anthias sebagai file storage.

## 🎯 Overview

Project ini menyediakan solusi lengkap digital signage dengan komponen:
- **Backend API** (FastAPI + PostgreSQL) - Control plane & metadata management
- **Web Admin** (React + Vite) - Dashboard manajemen konten dan device
- **Browser Viewer** (HTML/JS) - Viewer untuk monitor browser (port 8080)
- **WebOS Viewer** (HTML/JS) - Viewer untuk WebOS TV (port 8081)
- **WebOS App** (IPK Package) - Hosted app untuk LG WebOS TV
- **Anthias Integration** - File storage & serving (port 8000)

## 📁 Struktur Project

```
signate/
├── backend/                    # Backend API (Python FastAPI)
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Business logic (Anthias integration)
│   │   ├── core/              # Config, security, database
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── web-admin/                  # Web Admin Dashboard (React + Vite)
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   └── services/          # API clients
│   └── package.json
│
├── browser-viewer/             # Monitor Browser Viewer (Port 8080)
│   ├── index.html
│   ├── js/                    # ES6 modules
│   │   ├── app.js             # Main app
│   │   ├── api.js             # API client
│   │   ├── player.js          # Content player
│   │   └── activation.js      # 6-digit code activation
│   └── css/
│
├── webos-viewer/               # WebOS TV Viewer (Port 8081)
│   ├── index.html
│   └── js/                    # ES6 modules (UUID-based identity)
│
├── webos-app/                  # WebOS IPK Package
│   ├── appinfo.json           # App metadata
│   ├── icon.png
│   └── index.html → ../webos-viewer/
│
├── anthias/                    # Anthias (Digital Signage Platform)
│   └── docker/nginx/          # Nginx config with CORS for /screenly_assets/
│
├── database/
│   └── migrations/
│
├── docs/
│   ├── archive/               # Outdated documentation
│   └── SISTEM_LAUNCHER_SMART_TV_SIGNAGE_DOCUMENTATION.md
│
├── docker-compose.yml
├── .env.example
├── CLAUDE.md                  # 🔴 IMPORTANT: Server info & project guidelines
├── REBUILD-GUIDE.md
└── SUPPORTED_FORMATS.md
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (untuk development)
- Python 3.12+ (untuk development)

### 1. Setup Environment

```bash
# Clone project
cd /path/to/signate

# Copy environment template
cp .env.example .env

# Edit .env sesuai environment Anda
# Lihat CLAUDE.md untuk server credentials
```

### 2. Start Services (All on Server 192.168.5.12)

```bash
# SSH ke server
ssh gzjbbk@192.168.5.12

# Start all services
cd /home/gzjbbk/signage
docker-compose up -d
```

### 3. Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Web Admin** | http://localhost:3000 | Admin dashboard (dev mode, proxy ke server) |
| **Backend API** | http://192.168.5.12:8001 | REST API server |
| **API Docs** | http://192.168.5.12:8001/docs | Swagger documentation |
| **Anthias** | http://192.168.5.12:8000 | File storage & management |
| **Browser Viewer** | http://192.168.5.12:8080 | Viewer untuk monitor browser |
| **WebOS Viewer** | http://192.168.5.12:8081 | Viewer untuk WebOS TV |
| **PostgreSQL** | 192.168.5.12:5433 | Database |

## 🏗️ Architecture

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         192.168.5.12 Server                              │
│                                                                          │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Anthias        │  │ Backend API  │  │ PostgreSQL  │  │ Redis      │ │
│  │ Port 8000      │  │ Port 8001    │  │ Port 5433   │  │ Port 6379  │ │
│  │                │  │              │  │             │  │            │ │
│  │ - File storage │◄─┤ - REST API   │◄─┤ - Metadata  │  │ - Cache    │ │
│  │ - /screenly_   │  │ - Playlist   │  │ - Devices   │  │            │ │
│  │   assets/      │  │   generator  │  │ - Content   │  │            │ │
│  │   (CORS ✓)     │  │ - Auth       │  │ - Tags      │  │            │ │
│  └────────────────┘  └──────────────┘  └─────────────┘  └────────────┘ │
│         ▲                    ▲                                          │
└─────────┼────────────────────┼──────────────────────────────────────────┘
          │                    │
          │                    │ Playlist API
          │ Direct             │ (returns direct URLs)
          │ Binary             │
          │ Files              │
          │                    │
    ┌─────┴────────┐    ┌─────┴──────┐    ┌──────────────┐
    │ Monitor      │    │ WebOS TV   │    │ Web Admin    │
    │ Browser      │    │ Viewer     │    │ Dashboard    │
    │ Port 8080    │    │ Port 8081  │    │ localhost:   │
    │              │    │            │    │ 3000         │
    │ 6-digit code │    │ UUID-based │    │              │
    │ activation   │    │ persistent │    │ Auth required│
    └──────────────┘    └────────────┘    └──────────────┘
```

### Content Serving Pattern

**Control Plane / Data Plane Separation:**

```
┌──────────────────────────────────────────────────────────────────┐
│ CONTROL PLANE (Backend API - Port 8001)                          │
│                                                                   │
│ - Device registration & activation                               │
│ - Playlist generation (smart logic, tags, priorities)            │
│ - Content metadata management                                    │
│ - Authentication & authorization                                 │
│ - Returns direct URLs to viewers                                 │
└──────────────────────────────────────────────────────────────────┘
                             │
                             │ GET /api/client/playlist?device_id=X
                             ▼
                    {
                      "playlist": [
                        {
                          "url": "http://192.168.5.12:8000/screenly_assets/51ef3ffb..."
                        }
                      ]
                    }
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ DATA PLANE (Anthias - Port 8000)                                 │
│                                                                   │
│ - Direct binary file serving                                     │
│ - CORS enabled for cross-origin access                          │
│ - Browser caching support                                       │
│ - High-performance static file delivery                         │
│ - No authentication required (files served directly)            │
└──────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ **Fast**: Direct binary streaming, no proxy overhead
- ✅ **Cacheable**: Browser can cache files directly
- ✅ **Scalable**: Control plane and data plane can scale independently
- ✅ **Simple**: Viewers just fetch URLs, no complex logic needed

## 🔧 Development

### Backend Development

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Web Admin Development

```bash
cd web-admin

# Install dependencies
npm install

# Run development server (proxies API to server)
npm run dev
# Access at http://localhost:3000
```

### Viewer Development

Viewers are static HTML/JS, served via simple HTTP server:

```bash
# Browser viewer (port 8080)
cd browser-viewer
python3 -m http.server 8080

# WebOS viewer (port 8081)
cd webos-viewer
python3 -m http.server 8081
```

## 📊 Database Schema

PostgreSQL stores metadata only (NOT media files):

**Core Tables:**
- `users` - Admin accounts (authentication)
- `devices` - TV/Monitor registry (status, last_seen)
- `content` - Media metadata (title, anthias_asset_id, duration, MIME type)
- `tags` - Device groups
- `device_tags` - Many-to-many: devices ↔ tags
- `content_assignments` - Content → Device/Tag mapping with priority
- `schedules` - Time-based content scheduling (future)
- `firebird_config` - External API configuration (hotel guest data)

**Media Files:** Stored in Anthias at `/data/screenly_assets/` (inside Docker container)

## 🔐 Security & Authentication

### Web Admin
- **JWT Authentication** required
- **Token-based** API calls
- **CORS** enabled for localhost:3000

### Viewers (Browser/WebOS)
- **No authentication** on playlist endpoints (public)
- **Activation required** before device can fetch playlist
  - Browser: 6-digit code activation
  - WebOS: UUID-based persistent identity
- **CORS** enabled on Anthias for direct file access

### Content Files
- Served **directly from Anthias** (no auth)
- **Network-restricted** (allow 192.168.x.x, 172.16.x.x, 10.x.x.x)
- CORS headers enabled for cross-origin access

## 📝 Key Configuration Files

### 1. CLAUDE.md (🔴 MOST IMPORTANT)
Contains:
- Server credentials (SSH, database)
- Port assignments
- Service URLs
- Important operational notes
- Code synchronization protocol

### 2. .env (Backend Configuration)
```env
# Database
DATABASE_URL=postgresql://signage_user:password@postgres:5433/signage_db

# Anthias
ANTHIAS_API_URL=http://192.168.5.12:8000
ANTHIAS_PUBLIC_URL=http://192.168.5.12:8000

# API
API_BASE_URL=http://192.168.5.12:8001

# Security
JWT_SECRET=your_super_secret_key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://192.168.5.12:8080,http://192.168.5.12:8081
```

### 3. docker-compose.yml
Orchestrates all services:
- `postgres` - PostgreSQL database (port 5433)
- `redis` - Cache server (port 6379)
- `backend-api` - FastAPI server (port 8001)
- `anthias-*` - Anthias digital signage (port 8000)

## 🎨 Supported Media Formats

**Images:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)

**Videos:**
- MP4 (.mp4)
- MPEG (.mpeg, .mpg)
- QuickTime (.mov)

See `SUPPORTED_FORMATS.md` for detailed codec information.

## 🔄 Deployment Workflow

### Local Development → Server Deployment

```bash
# 1. Develop & test locally
cd /mnt/g/khoirul/signate
# ... make changes ...

# 2. Test locally
npm run dev  # frontend
uvicorn app.main:app --reload  # backend

# 3. Sync to server
sshpass -p 'Password@2021' scp -r changed_files gzjbbk@192.168.5.12:/home/gzjbbk/signage/

# 4. Rebuild on server (if needed)
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "cd /home/gzjbbk/signage && docker-compose up -d --build backend-api"

# 5. Commit changes
git add .
git commit -m "Description of changes"
```

**⚠️ IMPORTANT:** Always sync local ↔ server to avoid conflicts. See CLAUDE.md for detailed protocol.

## 📚 Additional Documentation

- **CLAUDE.md** - Server credentials & operational guidelines (🔴 READ FIRST)
- **REBUILD-GUIDE.md** - Docker rebuild procedures
- **SUPPORTED_FORMATS.md** - Media format specifications
- **docs/archive/** - Historical documentation (reference only)
- **docs/SISTEM_LAUNCHER_SMART_TV_SIGNAGE_DOCUMENTATION.md** - Original system design

## 🆘 Troubleshooting

### Backend tidak bisa diakses
```bash
# Check container status
docker ps --filter name=backend

# Restart backend
docker-compose restart backend-api

# Check logs
docker logs signage-backend --tail 50
```

### Viewer tidak tampil content
```bash
# Check nginx CORS config
cat anthias/docker/nginx/nginx.development.conf | grep -A 5 screenly_assets

# Test direct file access
curl -I http://192.168.5.12:8000/screenly_assets/FILENAME

# Check playlist API
curl "http://192.168.5.12:8001/api/client/playlist?device_id=1"
```

### Database connection error
```bash
# Check PostgreSQL container
docker ps --filter name=postgres

# Test connection
docker exec signage-postgres psql -U signage_user -d signage_db -c "\dt"
```

## 📞 Support

**Credentials & Access:** See `CLAUDE.md`
**Development:** Check `docs/` folder
**Issues:** Git commit history & logs

---

**Version:** 2.0
**Last Updated:** October 24, 2025
**Architecture:** Control Plane / Data Plane Separation
**Status:** Production Ready ✅
