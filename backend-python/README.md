# Backend Python - Digital Signage API

Backend API untuk sistem Digital Signage menggunakan FastAPI dengan Clean Architecture.

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.109.0 |
| Database | PostgreSQL | 15 |
| ORM | SQLAlchemy | 2.0 |
| Connection Pool | PgBouncer | Latest |
| Cache & Broker | Redis | 7 |
| Task Queue | Celery | 5.x |
| Virus Scanner | ClamAV | Latest |
| Auth | JWT (PyJWT) | - |
| Validation | Pydantic | 2.x |

## Architecture

```
backend-python/
├── main.py                    # FastAPI application entry point
├── celery_app.py              # Celery configuration
├── services/                  # Domain services (Clean Architecture)
│   ├── auth/                  # Authentication & authorization
│   ├── device/                # Device management
│   ├── content/               # Content management
│   ├── playlist/              # Playlist management
│   ├── schedule/              # Schedule management
│   ├── organization/          # Organization management
│   ├── user/                  # User management
│   ├── role/                  # Role & permission management
│   ├── analytics/             # Analytics & reporting
│   ├── audit/                 # Audit logging
│   ├── notification/          # Notification system
│   ├── system/                # System settings
│   ├── dashboard/             # Dashboard statistics
│   ├── device_group/          # Device grouping
│   ├── emergency/             # Emergency alerts
│   ├── tag/                   # Content tagging
│   ├── display_zone/          # Display zone management
│   └── [service]/
│       ├── models.py          # SQLAlchemy models
│       ├── dtos.py            # Pydantic DTOs
│       ├── routes.py          # FastAPI routes
│       ├── repositories/      # Data access layer
│       └── use_cases/         # Business logic
├── shared/                    # Shared utilities
│   ├── config.py              # Environment configuration
│   ├── database.py            # Database connection
│   ├── cache.py               # Redis cache service
│   ├── virus_scanner.py       # ClamAV integration
│   ├── api_routes.py          # Centralized route definitions
│   ├── errors.py              # Custom exceptions
│   ├── responses.py           # Standardized API responses
│   ├── validators.py          # Common validations
│   └── logging.py             # Centralized logging
├── tasks/                     # Celery tasks
│   └── content_tasks.py       # Video transcoding, thumbnails
└── migrations/                # SQL migrations (001-050)
```

## Clean Architecture Flow

```
routes.py → use_cases/ → domain/
              ↓
          repositories/
```

- **domain/** - Pure business logic (no dependencies)
- **use_cases/** - Application logic (depends on domain interfaces)
- **repositories/** - Data access (implements domain interfaces)
- **routes.py** - HTTP endpoints (dependency injection)

## API Endpoints

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User login dengan JWT |
| POST | `/register` | User registration |
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Invalidate token |
| GET | `/me` | Get current user |

### Devices (`/api/v1/devices`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List devices (paginated) |
| POST | `/` | Register device |
| GET | `/{id}` | Get device detail |
| PUT | `/{id}` | Update device |
| DELETE | `/{id}` | Delete device |
| POST | `/activate` | Activate with 6-digit code |
| POST | `/{id}/heartbeat` | Device heartbeat |
| POST | `/{id}/command` | Send command to device |
| GET | `/{id}/status` | Get device status |

### Content (`/api/v1/contents`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List contents (paginated) |
| POST | `/upload` | Upload content (image/video) |
| GET | `/{id}` | Get content detail |
| PUT | `/{id}` | Update content metadata |
| DELETE | `/{id}` | Delete content |
| GET | `/{id}/download` | Download content file |

### Playlists (`/api/v1/playlists`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List playlists |
| POST | `/` | Create playlist |
| GET | `/{id}` | Get playlist with items |
| PUT | `/{id}` | Update playlist |
| DELETE | `/{id}` | Delete playlist |
| POST | `/{id}/items` | Add item to playlist |
| PUT | `/{id}/items/reorder` | Reorder items |
| DELETE | `/{id}/items/{item_id}` | Remove item |

### Schedules (`/api/v1/schedules`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List schedules |
| POST | `/` | Create schedule |
| GET | `/{id}` | Get schedule detail |
| PUT | `/{id}` | Update schedule |
| DELETE | `/{id}` | Delete schedule |
| GET | `/device/{device_id}` | Get device schedule |

### Organizations (`/api/v1/organizations`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List organizations |
| POST | `/` | Create organization |
| GET | `/{id}` | Get organization detail |
| PUT | `/{id}` | Update organization |
| DELETE | `/{id}` | Delete organization |

### Users (`/api/v1/users`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List users (org-scoped) |
| POST | `/` | Create user |
| GET | `/{id}` | Get user detail |
| PUT | `/{id}` | Update user |
| DELETE | `/{id}` | Delete user |
| PUT | `/{id}/password` | Change password |

### Roles & Permissions (`/api/v1/roles`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List roles |
| POST | `/` | Create role |
| GET | `/{id}` | Get role with permissions |
| PUT | `/{id}` | Update role |
| DELETE | `/{id}` | Delete role |
| GET | `/permissions` | List all permissions |

### Audit Logs (`/api/v1/audit-logs`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List audit logs (filtered) |
| GET | `/{id}` | Get audit log detail |

### WebSocket (`/ws`)
| Endpoint | Description |
|----------|-------------|
| `/ws/device/{device_id}` | Device real-time communication |
| `/ws/admin` | Admin broadcast channel |

## Database Schema

**Total Tables**: 29

### Core Tables
| Table | Description |
|-------|-------------|
| `users` | User accounts |
| `organizations` | Multi-tenant organizations |
| `devices` | Display devices |
| `contents` | Media content |
| `playlists` | Content playlists |
| `playlist_items` | Playlist content items |
| `schedules` | Playback schedules |
| `roles` | User roles |
| `permissions` | System permissions |
| `role_permissions` | Role-permission mapping |

### Supporting Tables
| Table | Description |
|-------|-------------|
| `device_groups` | Device grouping |
| `device_group_members` | Group membership |
| `device_commands` | Pending commands |
| `display_zones` | Screen zones |
| `tags` | Content tags |
| `content_tags` | Content-tag mapping |
| `audit_logs` | System audit trail |
| `notifications` | User notifications |
| `emergency_alerts` | Emergency broadcasts |
| `system_settings` | Global settings |

## Celery Tasks

### Configuration
```python
broker_url = "redis://signage-redis:6379/0"
result_backend = "redis://signage-redis:6379/0"
task_queues = ["celery", "video_processing", "image_processing"]
```

### Available Tasks
| Task | Queue | Description |
|------|-------|-------------|
| `transcode_to_hls` | video_processing | Convert video to HLS (360p-1080p) |
| `generate_thumbnail` | image_processing | Generate content thumbnails |
| `cleanup_old_task_results` | celery | Daily cleanup (3 AM) |

### Task Settings
```python
task_acks_late = True              # Safe acknowledgment
task_reject_on_worker_lost = True  # Requeue on crash
worker_prefetch_multiplier = 1     # No prefetch
worker_max_tasks_per_child = 50    # Prevent memory leak
```

## Redis Usage

| Purpose | Key Pattern | TTL |
|---------|-------------|-----|
| Celery Broker | `celery-task-*` | - |
| Celery Results | `celery-task-meta-*` | 1 hour |
| Content Cache | `content:{id}` | 5 min |
| Playlist Cache | `playlist:{id}` | 5 min |
| Device Cache | `device:{id}` | 5 min |
| List Cache | `org:{id}:*:list:page:*` | 5 min |
| WebSocket Pub/Sub | `ws:*` | - |

## ClamAV Integration

Virus scanning untuk uploaded content:

```
1. File saved to disk
2. ClamAV scans via INSTREAM (port 3310)
3. If virus detected → delete file, reject upload
4. If ClamAV down → WARNING log, allow upload
```

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@signage-pgbouncer:6432/signage_db

# Redis
REDIS_URL=redis://signage-redis:6379/0

# ClamAV
CLAMAV_HOST=signage-clamav
CLAMAV_PORT=3310

# Security
SECRET_KEY=<random-256-bit-key>
JWT_SECRET=<random-256-bit-key>
ENCRYPTION_KEY=<random-128-bit-key>

# URLs
PUBLIC_BASE_URL=https://api.zhmhotels.online
CMS_URL=https://admin.zhmhotels.online
PLAYER_URL=https://player.zhmhotels.online

# CORS
CORS_ORIGINS=https://admin.zhmhotels.online,https://player.zhmhotels.online

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
```

## Docker Services

```yaml
backend-api:
  container_name: signage-backend-python
  ports: 8001:8000
  healthcheck: GET /health

celery-worker:
  container_name: signage-celery-worker
  command: celery -A celery_app worker
  queues: celery,video_processing,image_processing

celery-beat:
  container_name: signage-celery-beat
  command: celery -A celery_app beat
```

## Health Checks

| Service | Check Method |
|---------|--------------|
| Backend | `GET /health` |
| Celery Worker | `celery inspect ping` |
| Database | PgBouncer healthcheck |
| Redis | `redis-cli ping` |
| ClamAV | `clamdscan --ping` |

## Content Storage

```
/data/signage/content/
├── originals/          # Original uploaded files
├── thumbnails/         # Generated thumbnails
└── hls/                # HLS transcoded videos
    └── {content_id}/
        ├── master.m3u8
        ├── 360p/
        ├── 480p/
        ├── 720p/
        └── 1080p/
```

## Security Features

- JWT authentication with refresh tokens
- Password hashing (bcrypt)
- Role-based access control (RBAC)
- Multi-tenant data isolation
- Content virus scanning
- Audit logging
- CORS protection

## API Documentation

- **Swagger UI**: https://api.zhmhotels.online/docs
- **ReDoc**: https://api.zhmhotels.online/redoc
- **OpenAPI JSON**: https://api.zhmhotels.online/openapi.json

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker
celery -A celery_app worker --loglevel=info -Q celery,video_processing,image_processing

# Run Celery beat
celery -A celery_app beat --loglevel=info
```
