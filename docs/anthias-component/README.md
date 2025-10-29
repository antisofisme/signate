# Anthias Digital Signage - Full Source Code

Folder ini berisi **full source code Anthias** (formerly Screenly OSE) - open-source digital signage platform yang digunakan untuk serve konten (image/video) ke TV dan Monitor.

## Status

**Origin:** Fork "Signate Core" dari project lama (sedang dalam development untuk rebranding Anthias → Signate)

**Usage di Project Ini:**
- ✓ **Backup** full source code Anthias
- ✓ **Reference** untuk deploy Anthias dari scratch
- ✓ **Integration** dengan Backend API (FastAPI) untuk upload/manage konten

**Anthias di Server:**
- Server: 192.168.5.12
- Location: `/home/gzjbbk/Anthias/`
- Status: **Running** ✓
- Access: http://192.168.5.12:8000

---

## Isi Folder

```
anthias/
├── README.md                           ← File ini
├── ANTHIAS_ORIGINAL_README.md          ← README asli dari Anthias
├── SIGNATE_README.md                   ← README fork "Signate Core"
│
├── anthias_app/                        ← Main Django app
├── anthias_django/                     ← Django config & settings
├── api/                                ← REST API endpoints
├── static/src/                         ← React frontend source
├── templates/                          ← Django templates
├── viewer/                             ← HTML viewer untuk display
├── webview/                            ← WebView components
│
├── docker/                             ← Docker config files
│   ├── nginx/                          ← Nginx config
│   ├── Dockerfile.*                    ← Docker build files
│   └── ...
│
├── requirements/                       ← Python dependencies
│   ├── requirements.txt                ← Main requirements
│   └── requirements.dev.txt            ← Dev dependencies
│
├── docker-compose.dev.yml              ← Docker compose (development)
├── docker-compose.test.yml             ← Docker compose (testing)
├── docker-compose.yml.tmpl             ← Template docker compose
│
├── manage.py                           ← Django management
├── settings.py                         ← Django settings
├── package.json                        ← NPM dependencies
├── poetry.lock                         ← Python poetry lock
└── ...
```

---

## Tech Stack

**Backend:**
- Django 4.2
- Django REST Framework
- Celery (task queue)
- Redis (cache & message broker)
- SQLite/PostgreSQL

**Frontend:**
- React 19 + TypeScript
- Redux Toolkit
- Webpack
- Jest (testing)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- Supervisor (process manager)

---

## Cara Deploy Anthias

### Opsi 1: Pakai Anthias yang Sudah Running di Server (Recommended)

Backend API project ini akan **connect ke Anthias yang sudah jalan** via HTTP API.

**Setup di `.env`:**
```env
# Connect ke Anthias di server
ANTHIAS_API_URL=http://192.168.5.12:8000
ANTHIAS_API_KEY=
```

**Tidak perlu deploy Anthias baru!**

---

### Opsi 2: Deploy Anthias Baru (Development/Testing)

Jika ingin deploy Anthias baru untuk testing/development:

#### A. Deploy dengan Docker Compose

```bash
# 1. Masuk ke folder anthias
cd anthias/

# 2. Build & run dengan docker-compose
docker-compose -f docker-compose.dev.yml up -d

# 3. Check status
docker-compose ps

# 4. Access Anthias
# Browser: http://localhost:8080
# Default login: admin / screenly
```

#### B. Deploy Manual (Development)

```bash
# 1. Install Python dependencies
pip install -r requirements/requirements.txt

# 2. Install Node.js dependencies
npm install

# 3. Setup database
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Build frontend
npm run build

# 6. Run Django server
python manage.py runserver 0.0.0.0:8000

# 7. Run Celery worker (separate terminal)
celery -A anthias_app worker -l info

# 8. Access
# http://localhost:8000
```

---

## Integration dengan Backend API (FastAPI)

Backend API project ini (FastAPI) akan **integrate** dengan Anthias untuk:
1. Upload konten (image/video)
2. List konten yang tersedia
3. Delete konten
4. Get konten URL untuk TV/Monitor

### Flow Integration

```
┌─────────────────┐
│   Web Admin     │  Upload image via Web UI
│   (React/Vue)   │
└────────┬────────┘
         │ POST /api/content
         ▼
┌─────────────────┐
│  Backend API    │  1. Receive file
│   (FastAPI)     │  2. Upload ke Anthias API
└────────┬────────┘  3. Save metadata ke PostgreSQL
         │
         │ POST /api/assets
         ▼
┌─────────────────┐
│    ANTHIAS      │  1. Save file
│ Digital Signage │  2. Return asset URL
└────────┬────────┘  3. http://anthias:8080/asset/xxx.jpg
         │
         ▼
┌─────────────────┐
│  TV / Monitor   │  Display content dari Anthias URL
│                 │
└─────────────────┘
```

### Backend API Code Example

```python
# backend/app/services/anthias_service.py

import httpx
from fastapi import UploadFile

class AnthiasService:
    def __init__(self):
        self.base_url = os.getenv("ANTHIAS_API_URL")
        self.api_key = os.getenv("ANTHIAS_API_KEY")

    async def upload_asset(self, file: UploadFile):
        """Upload file ke Anthias"""
        async with httpx.AsyncClient() as client:
            files = {"file": (file.filename, file.file, file.content_type)}
            response = await client.post(
                f"{self.base_url}/api/assets",
                files=files,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()

    async def list_assets(self):
        """List semua assets di Anthias"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/assets",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()

    async def delete_asset(self, asset_id: str):
        """Delete asset dari Anthias"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/assets/{asset_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.status_code == 204
```

---

## Anthias API Endpoints

Endpoints yang digunakan untuk integration:

### 1. Upload Asset
```http
POST /api/assets
Content-Type: multipart/form-data

file: <binary>
```

**Response:**
```json
{
  "asset_id": "abc123xyz",
  "name": "banner1.jpg",
  "uri": "http://anthias:8080/asset/abc123xyz.jpg",
  "mimetype": "image/jpeg",
  "duration": 10,
  "is_enabled": true
}
```

### 2. List Assets
```http
GET /api/assets
```

**Response:**
```json
[
  {
    "asset_id": "abc123",
    "name": "banner1.jpg",
    "uri": "http://anthias:8080/asset/abc123.jpg",
    "mimetype": "image/jpeg"
  },
  ...
]
```

### 3. Delete Asset
```http
DELETE /api/assets/{asset_id}
```

**Response:** 204 No Content

### 4. Get Asset Info
```http
GET /api/assets/{asset_id}
```

---

## File Penting

### 1. `docker-compose.dev.yml`
Docker compose config untuk development/production.

**Services:**
- `anthias-server` - Django backend
- `anthias-celery` - Task queue
- `anthias-nginx` - Web server
- `anthias-websocket` - WebSocket server
- `redis` - Cache & broker

### 2. `settings.py`
Django settings - konfigurasi:
- Database connection
- Secret keys
- Allowed hosts
- Static files
- CORS settings

### 3. `viewer/`
HTML viewer files untuk display konten di TV/Monitor.

**Cara pakai:**
```html
<!-- Buka di TV browser -->
http://anthias:8080/viewer
```

### 4. `api/`
Django REST API endpoints:
- `/api/assets` - Manage assets
- `/api/playlists` - Manage playlists
- `/api/screens` - Manage screens

---

## Development

### Run Development Server

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery
celery -A anthias_app worker -l info

# Terminal 3: Frontend
npm run dev
```

### Run Tests

```bash
# Python tests
pytest

# JavaScript tests
npm test

# Coverage
pytest --cov=anthias_app
```

### Build Frontend

```bash
# Development
npm run dev

# Production
npm run build
```

---

## Fork "Signate Core"

Folder ini berasal dari fork Anthias yang sedang dalam development untuk **rebranding** menjadi "Signate Platform".

**Progress Fork (lihat SIGNATE_README.md):**
- ✓ Core files copied
- ⏳ Rebranding (Anthias → Signate)
- ⏳ Module renaming
- ⏳ Multi-tenant architecture
- ⏳ Cloud management features

**Note:** Untuk project **Smart TV Digital Signage** ini, kita **tidak pakai fork**, tapi pakai **Anthias original** sebagai content server.

---

## Backup & Restore

### Backup Data

```bash
# Backup database
docker exec anthias-server python manage.py dumpdata > backup.json

# Backup assets
docker cp anthias-server:/data ./anthias_data_backup

# Backup volumes
docker run --rm -v anthias-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/anthias_data.tar.gz /data
```

### Restore Data

```bash
# Restore database
docker exec -i anthias-server python manage.py loaddata < backup.json

# Restore assets
docker cp ./anthias_data_backup anthias-server:/data
```

---

## Troubleshooting

### Container Tidak Start

```bash
# Check logs
docker-compose logs anthias-server

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Cannot Upload Assets

```bash
# Check disk space
df -h

# Check permissions
docker exec anthias-server ls -la /data

# Fix permissions
docker exec anthias-server chown -R www-data:www-data /data
```

### Port Already in Use

Edit `docker-compose.dev.yml`:
```yaml
ports:
  - "8081:80"  # Ganti dari 8080 ke 8081
```

---

## Monitoring

### Check Status

```bash
# Container status
docker-compose ps

# Logs (real-time)
docker-compose logs -f

# Resource usage
docker stats
```

### Health Check

```bash
# Ping Anthias
curl http://localhost:8080/api/ping

# List assets
curl http://localhost:8080/api/assets
```

---

## Resources

- **Original Anthias Docs:** https://anthias.screenly.io/
- **GitHub Repo:** https://github.com/Screenly/Anthias
- **API Docs:** https://anthias.screenly.io/api-docs
- **Community Forum:** https://forums.screenly.io/

---

## Notes

- Folder ini adalah **backup & reference** full source code Anthias
- **Anthias sudah running** di server 192.168.5.12
- Backend API akan **connect via HTTP API** ke Anthias yang sudah ada
- **Tidak perlu deploy** Anthias baru kecuali untuk testing/development
- File konten (image/video) **disimpan di Anthias**, bukan di PostgreSQL
- PostgreSQL hanya simpan **metadata** (URL, title, duration, dll)

---

**Server Info:**
- IP: 192.168.5.12
- User: gzjbbk
- Location: /home/gzjbbk/Anthias/
- Status: Running ✓
- Access: http://192.168.5.12:8000

**Last Updated:** October 21, 2025
