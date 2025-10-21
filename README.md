# Smart TV Digital Signage System

Sistem digital signage terintegrasi untuk Smart TV WebOS dan Monitor Browser dengan manajemen konten terpusat.

## Overview

Project ini terdiri dari:
- **Smart TV WebOS App** - Aplikasi launcher custom untuk TV LG WebOS
- **Monitor Browser Viewer** - Web viewer untuk monitor biasa
- **Backend API** - REST API server (Python FastAPI)
- **Web Admin Panel** - Dashboard manajemen konten dan device
- **Database** - PostgreSQL untuk metadata dan konfigurasi
- **Anthias Integration** - Platform digital signage untuk serve konten

## Struktur Folder

```
signate/
├── backend/                    # Backend API (FastAPI + Python)
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── models/            # Database models (SQLAlchemy)
│   │   ├── services/          # Business logic
│   │   ├── core/              # Config, security, dependencies
│   │   └── main.py            # Entry point
│   ├── Dockerfile
│   └── requirements.txt
│
├── web-admin/                  # Web Admin Frontend (React/Vue)
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── pages/             # Pages/views
│   │   └── services/          # API client services
│   ├── Dockerfile
│   └── package.json
│
├── webos-app/                  # Smart TV WebOS Application
│   ├── src/
│   │   ├── components/        # React/JS components
│   │   └── services/          # API client, player logic
│   ├── appinfo.json           # WebOS app metadata
│   └── package.json
│
├── monitor-viewer/             # Monitor Browser Viewer
│   ├── index.html             # Main viewer page
│   ├── viewer.js              # Content player logic
│   └── styles.css
│
├── database/                   # Database
│   └── init.sql               # Schema & initial data
│
├── nginx/                      # Reverse Proxy
│   └── nginx.conf             # Nginx configuration
│
├── docs/                       # Documentation
│   └── SISTEM_LAUNCHER_SMART_TV_SIGNAGE_DOCUMENTATION.md
│
├── docker-compose.yml          # Docker orchestration
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Fungsi Setiap Folder

### 1. `backend/` - Backend API Server
**Untuk apa:** Server utama yang handle semua logic bisnis

**Fungsi:**
- REST API untuk Web Admin (CRUD device, content, schedule)
- REST API untuk TV/Monitor (get playlist, guest info)
- Integrasi dengan Anthias API (upload konten)
- Integrasi dengan Firebird API (data tamu hotel)
- WebSocket untuk real-time updates
- Authentication & authorization (JWT)
- Database operations (PostgreSQL)

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Redis

---

### 2. `web-admin/` - Web Admin Dashboard
**Untuk apa:** Dashboard untuk admin manage semua

**Fungsi:**
- Upload konten (image/video) ke Anthias
- Manage devices (register TV, activate monitor)
- Manage tags/groups (grouping devices)
- Assign konten ke device/tag
- Schedule konten (jam, hari, tanggal)
- Monitor status device (online/offline)
- User management (admin accounts)
- Settings (Firebird API config, dll)

**Tech Stack:** React/Vue, Tailwind CSS, Axios

---

### 3. `webos-app/` - Smart TV Application
**Untuk apa:** App yang di-install di TV LG WebOS

**Fungsi:**
- Display konten (image/video) dari Anthias
- Fetch playlist dari Backend API
- Display info tamu dari Firebird API
- Smooth transitions antar konten (inspired by Anthias)
- Auto-register ke server (pairing dengan IP + passphrase)
- Real-time update via WebSocket
- Heartbeat ke server (monitoring)

**Tech Stack:** React, Ares CLI (WebOS dev tools)

**File penting:**
- `appinfo.json` - Metadata app (app ID, version, icon)
- Package menjadi `.ipk` file untuk install ke TV

---

### 4. `monitor-viewer/` - Monitor Browser Viewer
**Untuk apa:** Web page sederhana untuk monitor biasa

**Fungsi:**
- Display konten full screen
- Generate unique code untuk aktivasi
- Polling ke server untuk check activation
- Fetch & display playlist setelah activated
- Auto-refresh content
- Smooth transitions

**Tech Stack:** Pure HTML/CSS/JavaScript (no framework, lightweight)

---

### 5. `database/` - Database Scripts
**Untuk apa:** Inisialisasi database schema

**Isi:**
- `init.sql` - CREATE TABLE statements untuk:
  - `devices` - Daftar TV & Monitor
  - `content` - Metadata konten (title, URL, duration)
  - `tags` - Groups untuk device
  - `device_tags` - Many-to-many relationship
  - `content_assignments` - Content → Device/Tag
  - `schedules` - Jadwal tampil konten
  - `users` - Admin accounts
  - `firebird_config` - Setting Firebird API

**Note:** File konten asli (image/video) **TIDAK disimpan di database**, tapi di Anthias. Database hanya simpan **metadata** (URL, title, duration, dll).

---

### 6. `nginx/` - Reverse Proxy
**Untuk apa:** Routing & load balancing

**Fungsi:**
- Route `/api/*` → Backend API
- Route `/ws/*` → WebSocket
- Route `/anthias/*` → Anthias service
- Route `/*` → Web Admin
- HTTPS/SSL termination
- CORS handling
- Rate limiting (optional)

---

### 7. `docs/` - Documentation
**Untuk apa:** Dokumentasi teknis project

**Isi:**
- Architecture diagram
- Database schema
- API endpoints reference
- Development workflow
- Deployment guide
- Testing guide

---

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- (Untuk WebOS dev) Ares CLI installed
- Git

### 1. Clone & Setup
```bash
cd /path/to/signate
cp .env.example .env
# Edit .env sesuai environment Anda
```

### 2. Start Services (Development)
```bash
docker-compose up -d
```

### 3. Access Services
- **Web Admin:** http://localhost:3000
- **Backend API Docs:** http://localhost:8000/docs
- **Anthias:** http://localhost:8080
- **PostgreSQL:** localhost:5432

### 4. Development Workflow

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Web Admin:**
```bash
cd web-admin
npm install
npm run dev
```

**WebOS App:**
```bash
cd webos-app
npm install
npm run dev
# Build & package for TV
npm run build
ares-package dist/
ares-install --device tv *.ipk
```

---

## Database - Apa yang Disimpan?

PostgreSQL digunakan untuk **metadata & konfigurasi**, BUKAN untuk file konten.

**Yang disimpan di database:**
1. **Device registry** - Info TV/Monitor (nama, IP, status, last seen)
2. **Content metadata** - Info konten (title, type, URL ke Anthias, duration)
3. **Tags/Groups** - Grouping devices
4. **Assignments** - Konten mana untuk device/tag mana
5. **Schedules** - Jadwal tampil konten (jam, hari, tanggal)
6. **Users** - Admin accounts
7. **Firebird config** - Setting API external

**Yang TIDAK disimpan di database:**
- ❌ File gambar/video asli
- ❌ Binary data konten

**File konten disimpan di:** Anthias (digital signage platform)

**Flow upload konten:**
```
Admin upload gambar via Web Admin
  ↓
Backend terima file → Upload ke Anthias API
  ↓
Anthias simpan file & return URL
  ↓
Backend simpan metadata ke PostgreSQL:
  - title: "Banner Promo"
  - type: "image"
  - anthias_url: "http://anthias:8080/asset/abc123.jpg"
  - duration: 10
```

**Flow device fetch konten:**
```
TV/Monitor request playlist
  ↓
Backend query PostgreSQL (metadata)
  ↓
Return playlist dengan URL Anthias
  ↓
TV/Monitor fetch & display dari Anthias URL
```

---

## Environment Variables

Copy `.env.example` ke `.env` dan sesuaikan:

```env
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/signage_db

# Anthias
ANTHIAS_API_URL=http://anthias:8080
ANTHIAS_API_KEY=your-key

# Firebird (External API)
FIREBIRD_API_URL=https://your-hotel-api.com
FIREBIRD_API_KEY=your-key
FIREBIRD_REFRESH_INTERVAL=300

# Security
JWT_SECRET=your-super-secret-key

# Redis
REDIS_URL=redis://redis:6379
```

---

## Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

Lihat dokumentasi lengkap di: `docs/SISTEM_LAUNCHER_SMART_TV_SIGNAGE_DOCUMENTATION.md`

---

## Tech Stack Summary

| Component | Technology |
|-----------|-----------|
| Backend API | Python 3.11+, FastAPI, SQLAlchemy |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Web Admin | React/Vue, Tailwind CSS |
| WebOS App | React, Ares CLI |
| Monitor Viewer | HTML/CSS/JavaScript |
| Reverse Proxy | Nginx |
| Digital Signage | Anthias (Screenly OSE) |
| Container | Docker, Docker Compose |

---

## Development Timeline

Estimasi development: **16 minggu (4 bulan)**

1. **Week 1-4:** Backend API & Database
2. **Week 5-8:** Web Admin Frontend
3. **Week 9-12:** WebOS TV App
4. **Week 13-14:** Monitor Viewer
5. **Week 15-16:** Integration & Testing

---

## Support

- **Documentation:** `docs/`
- **Issues:** GitHub Issues (jika ada repo)
- **WebOS Dev:** https://webostv.developer.lge.com/
- **Anthias:** https://anthias.screenly.io/

---

## License

[Specify your license here]

---

**Version:** 1.0
**Last Updated:** October 21, 2025
