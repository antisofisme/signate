# Backend-Python File Paths Reference

Quick lookup guide for all important files in the backend-python project.

## Project Root Paths

```
/mnt/g/khoirul/signate/backend-python/

Main Configuration:
├── main.py                          # FastAPI app entry point + service registration
├── celery_app.py                    # Celery configuration for async tasks
├── Dockerfile                       # Docker image build
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (LOCAL)
└── .env.example                    # Environment variables (TEMPLATE)

Core Directories:
├── shared/                         # Centralized utilities (SEE BELOW)
├── services/                       # All microservices (SEE BELOW)
├── migrations/                     # Database migration files
├── tasks/                          # Celery tasks
└── cms-vite/                       # (Copy of frontend - can ignore)
```

## Shared Utilities Path

Location: `/mnt/g/khoirul/signate/backend-python/shared/`

```
shared/
├── __init__.py
├── api_routes.py                   # CRITICAL: All API endpoint definitions
├── auth.py                         # JWT token generation/validation
├── config.py                       # Settings from .env (database_url, etc)
├── database.py                     # SQLAlchemy engine + session management
├── errors.py                       # Custom exception classes
├── logging.py                      # RequestLogger, AuditLogger
├── middleware.py                   # FastAPI middleware (cors, auth, etc)
├── password_reset.py               # Password reset email logic
├── rate_limiter.py                 # Rate limiting for brute force protection
├── responses.py                    # success_response(), error_response()
└── validators.py                   # Input validation utilities
```

## Service Paths (All Services Follow Same Pattern)

### Auth Service
```
/mnt/g/khoirul/signate/backend-python/services/auth/

domain/
├── __init__.py
├── user.py                         # @dataclass User, @dataclass Credentials
└── interfaces.py                   # IUserRepository interface

repositories/
├── __init__.py
├── models.py                       # SQLAlchemy: UserModel, OrganizationModel, AuditLogModel
├── user_repo.py                    # UserRepository class
└── organization_repo.py            # OrganizationRepository class

├── dtos.py                         # LoginRequest, RegisterRequest, etc.
├── routes.py                       # FastAPI routes for auth
└── use_cases/
    ├── __init__.py
    ├── login.py                    # Login use case
    ├── register.py                 # Register use case
    ├── forgot_password.py          # Forgot password use case
    └── reset_password.py           # Reset password use case
```

### Device Service (Reference Implementation)
```
/mnt/g/khoirul/signate/backend-python/services/device/

domain/
├── __init__.py
├── device.py                       # @dataclass Device, @dataclass ActivationCode, @dataclass DeviceHeartbeat
└── interfaces.py                   # IDeviceRepository interface

repositories/
├── __init__.py
├── models.py                       # SQLAlchemy: DeviceModel
└── device_repo.py                  # DeviceRepository class

├── dtos.py                         # RequestActivationCodeRequest, ActivateDeviceRequest, etc.
├── routes.py                       # 5 FastAPI routes + dependency injection
└── use_cases/
    ├── __init__.py
    ├── request_activation_code.py  # Generate activation code
    ├── activate_device.py          # Activate with code
    ├── heartbeat.py                # Update last_seen
    ├── list_devices.py             # List by organization
    └── update_device.py            # Update device settings
```

### Content Service
```
/mnt/g/khoirul/signate/backend-python/services/content/

domain/
├── __init__.py
├── content.py                      # @dataclass Content
└── interfaces.py                   # IContentRepository interface

infrastructure/
└── storage/
    ├── __init__.py
    ├── interfaces.py               # Storage provider interface
    ├── local_storage.py            # Local filesystem storage
    └── metadata_extractor.py       # Extract video/image metadata

repositories/
├── __init__.py
├── models.py                       # SQLAlchemy: ContentModel
└── content_repo.py                 # ContentRepository class

├── dtos.py                         # Upload, List, Get response DTOs
├── routes.py                       # Upload, List, Delete routes
└── use_cases/
    ├── __init__.py
    ├── upload_content.py           # Upload file
    ├── list_content.py             # List by organization
    ├── get_content.py              # Get single content
    └── update_content.py           # Update metadata
```

### Playlist Service
```
/mnt/g/khoirul/signate/backend-python/services/playlist/

domain/
├── __init__.py
├── playlist.py                     # @dataclass Playlist
└── interfaces.py                   # IPlaylistRepository interface

repositories/
├── __init__.py
├── models.py                       # SQLAlchemy: PlaylistModel, PlaylistContentModel, PlaylistAssignmentModel
└── playlist_repo.py                # PlaylistRepository class

├── dtos.py                         # Create, List, Get response DTOs
├── routes.py                       # CRUD + assignment routes
└── use_cases/
    ├── __init__.py
    ├── create_playlist.py
    ├── delete_playlist.py
    ├── get_playlist.py
    ├── list_playlists.py
    ├── manage_playlist_content.py  # Add/remove content
    ├── manage_playlist_assignments.py  # Assign to devices/tags
    └── update_playlist.py
```

### Tag Service
```
/mnt/g/khoirul/signate/backend-python/services/tag/

domain/
├── __init__.py
├── tag.py                          # @dataclass Tag
├── tag_entity.py                   # Tag entity
└── interfaces.py                   # ITagRepository interface

repositories/
├── __init__.py
├── models.py                       # SQLAlchemy: TagModel
├── tag_repo.py                     # TagRepository class
└── content_tag_repo.py             # Content-Tag assignment repository

├── dtos.py                         # Create, List, Assign DTOs
├── routes.py                       # CRUD + assignment routes
└── use_cases/
    ├── __init__.py
    ├── create_tag.py
    ├── delete_tag.py
    ├── get_tag.py
    ├── list_tags.py
    ├── update_tag.py
    ├── assign_tag_to_content.py
    ├── assign_tag_to_contents.py
    ├── unassign_tag_from_content.py
    ├── unassign_tag_from_contents.py
    └── get_content_tags.py
```

### Organization Service
```
/mnt/g/khoirul/signate/backend-python/services/organization/

domain/
├── __init__.py
├── organization.py                 # @dataclass Organization
└── interfaces.py                   # IOrganizationRepository interface

repositories/
├── __init__.py
├── models.py                       # (Uses shared from auth)
└── organization_repo.py            # OrganizationRepository class

├── dtos.py                         # Create, List, Get DTOs
├── routes.py                       # CRUD routes
└── use_cases/
    ├── __init__.py
    ├── create_organization.py
    ├── delete_organization.py
    ├── get_organization.py
    ├── list_organizations.py
    └── update_organization.py
```

### User Service
```
/mnt/g/khoirul/signate/backend-python/services/user/

domain/
├── __init__.py
├── user.py                         # @dataclass User
└── interfaces.py                   # IUserRepository interface

repositories/
├── __init__.py
├── models.py                       # (Uses shared from auth)
└── user_repo.py                    # UserRepository class

├── dtos.py                         # Create, List, Get DTOs
├── routes.py                       # CRUD routes
└── use_cases/
    ├── __init__.py
    ├── create_user.py
    ├── delete_user.py
    ├── get_user.py
    ├── list_users.py
    ├── update_user.py
    └── change_password.py
```

### Audit Service
```
/mnt/g/khoirul/signate/backend-python/services/audit/

domain/
├── __init__.py
├── audit_log.py                    # @dataclass AuditLog
└── interfaces.py                   # IAuditLogRepository interface

repositories/
├── __init__.py
├── models.py                       # SQLAlchemy: AuditLogModel
└── audit_log_repo.py               # AuditLogRepository class

├── dtos.py                         # List, Get response DTOs
├── routes.py                       # List, Get routes
└── use_cases/
    ├── __init__.py
    ├── create_audit_log.py         # Internal: log actions
    ├── get_audit_log.py
    └── list_audit_logs.py
```

## Migration Files Path

Location: `/mnt/g/khoirul/signate/backend-python/migrations/`

```
migrations/
├── 002_add_organization_fields.sql      # Add org fields to users table
├── 003_create_contents_table.sql        # Create contents table
├── 004_create_tags_tables.sql           # Create tags + content_tags tables
├── 005_create_playlists_tables.sql      # Create playlists + junction tables
├── alter_organization_pin_to_8.sql      # Helper: fix PIN length
└── fix_organization_pins.sql            # Helper: fix PIN values
```

**Next migration:** `006_[description].sql`

## Critical Files to Know

### For API Route Definition
**File:** `/mnt/g/khoirul/signate/backend-python/shared/api_routes.py`
- Contains all route paths
- Classes: AuthRoutes, DeviceRoutes, ContentRoutes, PlaylistRoutes, etc.
- Add new routes HERE before implementing service

### For Environment Configuration
**File:** `/mnt/g/khoirul/signate/backend-python/shared/config.py`
- Reads from .env file
- Database URL, port, environment, etc.

**File:** `/mnt/g/khoirul/signate/backend-python/.env`
- Local development settings
- DATABASE_URL, SECRET_KEY, CORS_ORIGINS, etc.

### For Error Handling
**File:** `/mnt/g/khoirul/signate/backend-python/shared/errors.py`
- AppException, ValidationError, NotFoundError, etc.
- Use these in use_cases and routes

### For Standard Responses
**File:** `/mnt/g/khoirul/signate/backend-python/shared/responses.py`
- success_response(), error_response(), paginated_response()
- Use in all routes

### For Logging & Audit
**File:** `/mnt/g/khoirul/signate/backend-python/shared/logging.py`
- RequestLogger, AuditLogger
- Use in routes for request/action logging

## Common Import Patterns

### In routes.py
```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.api_routes import MyServiceRoutes
from shared.errors import handle_errors, NotFoundError
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger

from .repositories.my_repo import MyRepository
from .dtos import MyRequest, MyResponse
from .use_cases.my_use_case import MyUseCase
```

### In repositories/my_repo.py
```python
from typing import Optional, List
from sqlalchemy.orm import Session

from ..domain.my_entity import MyEntity
from ..domain.interfaces import IMyRepository
from .models import MyModel

class MyRepository(IMyRepository):
    def __init__(self, db: Session):
        self.db = db
```

### In use_cases/my_use_case.py
```python
from ..domain.my_entity import MyEntity
from ..domain.interfaces import IMyRepository

class MyUseCase:
    def __init__(self, repo: IMyRepository):
        self.repo = repo
    
    def execute(self, ...):
        # Business logic
        entity = self.repo.create(...)
        return entity
```

### In domain/my_entity.py
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MyEntity:
    id: Optional[int]
    name: str
    organization_id: int
    # ... rest of fields
```

### In dtos.py
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MyRequest(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None

class MyResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## Environment Variables (.env)

Path: `/mnt/g/khoirul/signate/backend-python/.env`

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/signage_db

# API
AUTH_SERVICE_PORT=8001
ENVIRONMENT=development
DEBUG=True

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ENABLE_CORS=True
CORS_ORIGINS=http://localhost:3000,http://192.168.5.12:8080

# Logging
LOG_LEVEL=INFO

# API Documentation
ENABLE_API_DOCS=True

# Rate Limiting
RATE_LIMIT_ENABLED=True
```

## File Organization Best Practices

1. **Models Always Go In:** `services/[name]/repositories/models.py`
2. **Routes Always Use:** `shared/api_routes.py`
3. **Shared Utilities:** `shared/` (don't duplicate)
4. **Domain Logic:** `domain/[entity].py` (pure business logic)
5. **API Contracts:** `dtos.py` (request/response)
6. **HTTP Handlers:** `routes.py` (FastAPI endpoints)
7. **Business Use Cases:** `use_cases/[action].py` (one per file)
8. **Data Access:** `repositories/[service]_repo.py`

## Verification Checklist

Before committing code:
- [ ] Models in `repositories/models.py`
- [ ] Routes in `shared/api_routes.py`
- [ ] Using `success_response()` for success
- [ ] Using custom exceptions from `shared.errors`
- [ ] Logging actions with RequestLogger/AuditLogger
- [ ] All DI functions in `routes.py`
- [ ] All use cases have execute() method
- [ ] DTOs have `from_attributes = True`
- [ ] Domain entities use @dataclass
- [ ] Repositories implement interface

