# Backend API - Smart TV Digital Signage

FastAPI backend providing REST API for content management, device registration, and playlist generation.

## Architecture Role

**Control Plane** - Manages metadata, generates playlists, and provides device/content management APIs.

- Does NOT serve media files (handled by Anthias on port 8000)
- Returns direct Anthias URLs in playlists for optimal performance
- Handles authentication, authorization, and business logic

## Tech Stack

- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Cache**: Redis
- **Authentication**: JWT tokens
- **Deployment**: Docker container

## Project Structure

```
backend/
├── app/
│   ├── api/               # REST API endpoints
│   │   ├── auth.py        # Login, token management
│   │   ├── client.py      # Device playlist & status (no auth)
│   │   ├── content.py     # Content CRUD
│   │   ├── device.py      # Device management
│   │   └── tags.py        # Tag & assignment management
│   │
│   ├── models/            # SQLAlchemy models
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── content.py
│   │   ├── tag.py
│   │   └── assignment.py
│   │
│   ├── services/          # Business logic
│   │   └── anthias.py     # Anthias API integration
│   │
│   ├── core/              # Core configuration
│   │   ├── config.py      # Settings (environment variables)
│   │   ├── database.py    # Database session management
│   │   └── security.py    # JWT token handling
│   │
│   └── main.py            # FastAPI app entry point
│
├── Dockerfile
├── requirements.txt
└── README.md (this file)
```

## Environment Variables

Configure via `.env` file (see `.env.example` in project root):

```env
# Database
DATABASE_URL=postgresql://signage_user:password@postgres:5433/signage_db

# Anthias Integration
ANTHIAS_API_URL=http://192.168.5.12:8000
ANTHIAS_PUBLIC_URL=http://192.168.5.12:8000

# API Configuration
API_BASE_URL=http://192.168.5.12:8001

# Security
JWT_SECRET=your_super_secret_key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# CORS
CORS_ORIGINS=http://localhost:3000,http://192.168.5.12:8080,http://192.168.5.12:8081
```

## API Endpoints

### Authentication (Requires JWT)

- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/logout` - Logout (invalidate token)
- `GET /api/auth/me` - Get current user info

### Content Management (Requires JWT)

- `GET /api/content/` - List all content
- `POST /api/content/` - Upload new content (creates asset in Anthias)
- `GET /api/content/{id}` - Get content details
- `PATCH /api/content/{id}` - Update content metadata
- `DELETE /api/content/{id}` - Delete content
- `GET /api/content/{id}/image` - Get image (for web admin preview)
- `GET /api/content/{id}/video` - Get video (for web admin preview)

### Device Management (Requires JWT)

- `GET /api/devices/` - List all devices
- `POST /api/devices/register` - Register new device
- `POST /api/devices/{id}/activate` - Activate pending device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device

### Tags & Assignments (Requires JWT)

- `GET /api/tags/` - List all tags
- `POST /api/tags/` - Create tag
- `GET /api/tags/{id}/devices` - Get devices with tag
- `POST /api/assignments/` - Assign content to device/tag
- `DELETE /api/assignments/{id}` - Remove assignment

### Client Endpoints (No Authentication)

- `GET /api/client/playlist?device_id={id}` - Get playlist for device
- `GET /api/client/status?device_id={id}` - Check device status

## Key Features

### 1. Control Plane / Data Plane Separation

Backend API generates playlists with **direct Anthias URLs**:

```python
# Example playlist response
{
  "device_id": 1,
  "playlist": [
    {
      "content_id": 42,
      "title": "Welcome Video",
      "url": "http://192.168.5.12:8000/screenly_assets/51ef3ffb-abc123.mp4",
      "duration": 10,
      "mime_type": "video/mp4"
    }
  ]
}
```

Viewers fetch files **directly from Anthias** (no proxy through backend).

### 2. Smart Playlist Generation

Located in `backend/app/api/client.py:get_device_playlist()`:

1. Get device info
2. Get device's tags
3. Query content assignments for:
   - Content assigned directly to device, OR
   - Content assigned to any of device's tags
4. Filter only active content
5. Sort by priority (highest first)
6. Return playlist with direct Anthias URLs

### 3. Anthias Integration

Service layer (`backend/app/services/anthias.py`) handles:

- Asset upload (multipart file upload)
- Asset metadata sync (title, duration, is_active)
- Asset deletion
- **Note**: Anthias updates are **optional** - database is source of truth

### 4. Database-First Updates

Since commit `468d8fa`, content updates commit to database **first**, then sync to Anthias:

```python
# Update database (viewers use this)
db.commit()
db.refresh(content)

# Try to sync to Anthias (optional - for consistency only)
try:
    await anthias_service.update_asset(...)
except Exception as e:
    logger.warning(f"Anthias sync failed (non-critical): {e}")
    # Request still succeeds!
```

This prevents Anthias API errors from breaking content management.

## Development

### Local Development (without Docker)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://signage_user:password@192.168.5.12:5433/signage_db"
export ANTHIAS_API_URL="http://192.168.5.12:8000"
# ... (see .env.example for full list)

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Docker Development

```bash
# From project root
docker-compose up -d backend-api

# View logs
docker logs signage-backend --tail 50 -f

# Rebuild after code changes
docker-compose up -d --build backend-api
```

## API Documentation

Interactive API docs available at:

- **Swagger UI**: http://192.168.5.12:8001/docs
- **ReDoc**: http://192.168.5.12:8001/redoc

## Database Schema

### Core Tables

- `users` - Admin accounts (authentication)
- `devices` - TV/Monitor registry (status, last_seen)
- `content` - Media metadata (title, anthias_asset_id, duration, MIME type)
- `tags` - Device groups (e.g., "Lobby TVs", "Floor 2")
- `device_tags` - Many-to-many: devices ↔ tags
- `content_assignments` - Content → Device/Tag mapping with priority
- `schedules` - Time-based content scheduling (future feature)
- `firebird_config` - External API configuration (hotel guest data)

**Media Files**: NOT stored in PostgreSQL - stored in Anthias at `/data/screenly_assets/`

## Troubleshooting

### Backend not accessible

```bash
# Check container status
docker ps --filter name=backend

# Restart backend
docker-compose restart backend-api

# Check logs
docker logs signage-backend --tail 50
```

### Database connection error

```bash
# Check PostgreSQL container
docker ps --filter name=postgres

# Test connection
docker exec signage-postgres psql -U signage_user -d signage_db -c "\dt"
```

### CORS issues

Check `backend/app/core/config.py` - CORS origins must include viewer URLs:

```python
CORS_ORIGINS = [
    "http://localhost:3000",        # Web Admin dev
    "http://192.168.5.12:8080",     # Browser Viewer
    "http://192.168.5.12:8081",     # WebOS Viewer
]
```

### Anthias sync failures

If bulk edit or content updates fail with Anthias errors, check:

1. Is Anthias running? `curl http://192.168.5.12:8000/api/v1/assets`
2. Database updates should still succeed (Anthias sync is optional)
3. Check logs: `docker logs signage-backend | grep -i anthias`

## Sync to Server

After making changes locally:

```bash
# Sync backend code to server
sshpass -p 'Password@2021' scp -r backend/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/

# Rebuild backend container on server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "cd /home/gzjbbk/signage && docker-compose up -d --build backend-api"

# Verify
curl http://192.168.5.12:8001/docs
```

## Testing

```bash
# Run tests (when implemented)
pytest

# Test specific endpoint
curl -X GET "http://192.168.5.12:8001/api/client/playlist?device_id=1"

# Test with authentication
curl -X POST "http://192.168.5.12:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

## Security Notes

- JWT tokens expire after 15 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)
- Client endpoints (`/api/client/*`) do NOT require authentication (devices need playlist access)
- Content files served from Anthias are network-restricted (192.168.x.x, 172.16.x.x, 10.x.x.x)
- Passwords hashed with bcrypt

## Important Links

- Root README: `../README.md` - Project overview
- Anthias README: `../anthias/README.md` - File storage configuration
- Web Admin README: `../web-admin/README.md` - Frontend development
- CLAUDE.md: Server credentials and deployment workflow
