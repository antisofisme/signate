# Backend Python - Digital Signage API

## Architecture

Multi-tenant microservices architecture dengan shared resources.

## Structure (Clean Architecture - Flattened)

```
backend-python/
├── .env                     # SATU untuk semua services (DB, Redis, Secret, CORS)
├── requirements.txt
├── services/
│   ├── auth/               # Authentication Service
│   │   ├── domain/         # 📦 CORE - Business Logic (No dependencies)
│   │   │   ├── user.py            # User entity + Credentials value object
│   │   │   └── interfaces.py      # IUserRepository contract
│   │   ├── use_cases/      # 🎯 USE CASES - Application Logic (1 file = 1 use case)
│   │   │   ├── login.py           # Login use case
│   │   │   └── register.py        # Register use case
│   │   ├── repositories/   # 🔧 INFRASTRUCTURE - Database
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   └── user_repo.py       # Repository implementation
│   │   ├── dtos.py         # Request/Response DTOs
│   │   └── routes.py       # 🌐 HTTP - FastAPI endpoints
│   ├── tenant/             # Organization Service (same structure)
│   ├── device/             # Device Service
│   ├── content/            # Content Service
│   └── analytics/          # Analytics Service
└── shared/                 # 📦 CENTRALIZED UTILITIES (stable patterns)
    ├── api_routes.py      # ⚠️ API routes definition (Single Source of Truth)
    ├── config.py          # Settings from .env
    ├── database.py        # SQLAlchemy setup
    ├── errors.py          # ✅ Custom exceptions & error handling
    ├── responses.py       # ✅ Standardized API response formatters
    ├── validators.py      # ✅ Common validation functions
    └── logging.py         # ✅ Centralized logging infrastructure
```

**Dependency Flow (Clean Architecture):**
```
routes.py → use_cases/ → domain/
              ↓
          repositories/
```
- **domain/** depends on NOTHING (pure business logic)
- **use_cases/** depends on domain/ interfaces
- **repositories/** implements domain/ interfaces
- **routes.py** coordinates use cases (DI)

## Environment Variables

### .env (Root)
**SATU file untuk semua microservices backend:**
- `DATABASE_URL` - Shared database
- `REDIS_URL` - Shared cache
- `SECRET_KEY` - JWT signing
- `CORS_ORIGINS` - Allowed origins
- Service ports (jika berbeda per service)
- Feature flags

**Semua services dalam backend-python menggunakan .env yang sama.**

## API Routes (Centralized)

**File:** `shared/api_routes.py`

Semua route definitions harus di sini:
```python
# ⚠️ SINGLE SOURCE OF TRUTH untuk API endpoints
API_V1 = "/api/v1"

class AuthRoutes:
    LOGIN = f"{API_V1}/auth/login"
    REGISTER = f"{API_V1}/auth/register"

class DeviceRoutes:
    LIST = f"{API_V1}/devices"
    ACTIVATE = f"{API_V1}/devices/activate"
```

**Keuntungan:**
- Perubahan endpoint cukup 1 tempat
- Mudah review semua API yang tersedia
- Bisa compare dengan CMS/Player endpoints

## Layer Explanation

### 1. **domain/** - Core Business Logic
- **Tidak boleh** depend ke framework, database, atau library eksternal
- **Pure Python** objects saja
- **Business rules** & validasi
- File: `user.py` (entity), `interfaces.py` (contracts)

### 2. **use_cases/** - Application Logic
- **1 file = 1 use case** (login.py, register.py, logout.py, dll)
- Depends **hanya** ke `domain/` interfaces
- Coordinates business logic
- Max ~150 lines per file

### 3. **repositories/** - Infrastructure
- Implements `domain/interfaces.py`
- Database access (SQLAlchemy)
- File: `models.py` (SQLAlchemy models), `user_repo.py` (implementation)

### 4. **routes.py** - HTTP Layer
- FastAPI endpoints
- Dependency Injection (DI)
- **TIDAK ada** business logic (delegate ke use_cases)

### 5. **dtos.py** - Data Transfer Objects
- Pydantic models untuk Request/Response
- Validation schema

---

## Flow Example: Login

```
1. HTTP POST /api/v1/auth/login
   ↓
2. routes.py
   - Validate LoginRequest DTO
   - Inject LoginUseCase
   ↓
3. use_cases/login.py
   - Call user_repo.find_by_username()
   - Verify password
   - Generate JWT token
   ↓
4. repositories/user_repo.py
   - Query database via SQLAlchemy
   - Convert UserModel → User entity
   ↓
5. Return TokenResponse
```

---

## Best Practices

### ✅ DO:
- 1 file = 1 responsibility
- Keep files < 200 lines
- Domain entities pure Python (no SQLAlchemy)
- Use interfaces for repositories
- Use dependency injection in routes

### ❌ DON'T:
- Business logic in routes.py
- Domain depends on infrastructure
- God classes (1 file dengan 20+ methods)
- Hardcode URLs/configs
- Direct DB access in use_cases

---

## Delete Strategy

### Hard Delete vs Active/Inactive Toggle

**Strategy Adopted**: Hybrid approach with clear separation

#### 1. **DELETE Endpoint** = Hard Delete (Permanent Removal)
```python
# DELETE /organizations/{id}
# DELETE /users/{id}
# → Permanently removes from database
# → Cannot be recovered
# → Use for: cleanup, test data removal
```

**Validation**:
- Organization: Cannot delete if has users or devices
- User: No restrictions (force delete)

#### 2. **UPDATE Endpoint with is_active** = Soft Archive (Reversible)
```python
# PUT /organizations/{id} with {"is_active": false}
# PUT /users/{id} with {"is_active": false}
# → Disables/archives without deleting
# → Data remains in database
# → Can be restored with is_active=true
# → Use for: temporary suspension, archiving
```

**Use Cases**:
- Disable user temporarily: `PUT /users/{id}` → `{"is_active": false}`
- Restore user: `PUT /users/{id}` → `{"is_active": true}`
- Permanent removal: `DELETE /users/{id}`

**List Filtering**:
- By default, list endpoints show ALL records (active + inactive)
- Use `?active_only=true` to filter active records only

**Example**:
```bash
# Archive organization (soft)
curl -X PUT /api/v1/organizations/1 -d '{"name":"...", "is_active":false}'

# Delete organization permanently (hard)
curl -X DELETE /api/v1/organizations/1
```

---

## Creating New Feature

**Example: Add "Delete User" feature**

1. **Update interface** (`domain/interfaces.py`):
   ```python
   def delete(self, user_id: int) -> bool
   ```

2. **Implement repository** (`repositories/user_repo.py`):
   ```python
   def delete(self, user_id: int) -> bool:
       # DB delete logic
   ```

3. **Create use case** (`use_cases/delete_user.py`):
   ```python
   class DeleteUserUseCase:
       def execute(self, user_id: int) -> bool:
           # Business logic
   ```

4. **Add endpoint** (`routes.py`):
   ```python
   @router.delete("/users/{user_id}")
   def delete_user(user_id: int, use_case: DeleteUserUseCase = Depends(...)):
       ...
   ```

---

## Creating New Service

**Template:**
```bash
mkdir -p services/new_service/{domain,use_cases,repositories}
touch services/new_service/{dtos.py,routes.py}
```

Copy struktur dari `services/auth/` dan sesuaikan.

---

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run specific service (TODO: belum ada main.py)
# cd services/auth
# uvicorn main:app --reload --port 8001
```

---

## Architecture Consistency Status

### ✅ **ALL SERVICES NOW 100% COMPLIANT!**

**Fully Compliant Services (✅ Clean Architecture):**
- ✅ **Organization Service** - Repository pattern, domain layer, proper DI
- ✅ **Auth Service** - Clean Architecture principles
- ✅ **User Service** - ✨ **MIGRATED!** Now uses Repository pattern (2025-01-05)
- ✅ **Audit Service** - ✨ **NEW!** Complete audit logging system with DB persistence (2025-01-05)

**Incomplete Services (⚠️ Not Fully Implemented):**
- **Device Service** - Missing routes.py and some use cases

### 🎉 User Service Migration Complete!

**User Service Structure (NOW CORRECT):**
```
services/user/
├── domain/                  # ✅ Core business logic
│   ├── user.py             # User entity (pure Python)
│   ├── interfaces.py       # IUserRepository contract
│   └── __init__.py
├── repositories/            # ✅ Infrastructure layer
│   ├── user_repo.py        # UserRepository implementation
│   └── __init__.py
├── use_cases/              # ✅ Application logic (all 6 refactored)
│   ├── create_user.py
│   ├── list_users.py
│   ├── get_user.py
│   ├── update_user.py
│   ├── delete_user.py
│   └── change_password.py
├── dtos.py
└── routes.py               # ✅ Updated DI to use repositories
```

**Migration Details:**
1. ✅ Created `domain/user.py` with User entity & business logic
2. ✅ Created `domain/interfaces.py` with IUserRepository contract
3. ✅ Created `repositories/user_repo.py` implementing IUserRepository
4. ✅ Refactored all 6 use cases to use repository instead of Session
5. ✅ Updated routes.py dependency injection

**Benefits Achieved:**
- ✅ Dependency inversion principle followed
- ✅ Loose coupling (can swap SQLAlchemy for MongoDB)
- ✅ Testable (easy to mock repository)
- ✅ Consistent with Organization service
- ✅ True Clean Architecture

### 🎉 Audit Service - Complete Audit Logging System!

**Audit Service Structure (CLEAN ARCHITECTURE):**
```
services/audit/
├── domain/                     # ✅ Core business logic
│   ├── audit_log.py           # AuditLog entity (pure Python)
│   ├── interfaces.py          # IAuditLogRepository contract
│   └── __init__.py
├── repositories/              # ✅ Infrastructure layer
│   ├── audit_log_repo.py     # AuditLogRepository implementation
│   └── __init__.py
├── use_cases/                 # ✅ Application logic
│   ├── create_audit_log.py   # Create audit log entry
│   ├── list_audit_logs.py    # List with filters & pagination
│   └── get_audit_log.py       # Get single log
├── dtos.py                    # Request/Response DTOs
└── routes.py                  # ✅ FastAPI endpoints (GET /api/v1/audit-logs)
```

**Database Table:**
- `audit_logs` table in `services/auth/repositories/models.py` (centralized)
- Tracks: user_id, organization_id, action, resource_type, resource_id, details (JSON), ip_address, user_agent, created_at
- Foreign keys with ON DELETE SET NULL for data integrity

**Features:**
1. ✅ **Database Persistence** - All audit logs saved to PostgreSQL
2. ✅ **Enhanced AuditLogger** - Updated `shared/logging.py` to optionally persist via use case
3. ✅ **Query API** - List audit logs with filters (user, org, action, resource, dates)
4. ✅ **Pagination** - Supports limit/offset for large result sets
5. ✅ **Enriched Responses** - Includes username and organization_name in responses
6. ✅ **Clean Architecture** - Repository pattern, domain layer, dependency injection

**API Endpoints:**
- `GET /api/v1/audit-logs` - List audit logs with filters
- `GET /api/v1/audit-logs/{log_id}` - Get single audit log

**Usage in Other Services:**
```python
# In routes.py - Inject CreateAuditLogUseCase via DI
def get_create_audit_log_use_case(
    audit_log_repo = Depends(get_audit_log_repository)
) -> CreateAuditLogUseCase:
    return CreateAuditLogUseCase(audit_log_repo)

# Create AuditLogger with database persistence
audit_logger = AuditLogger(
    create_audit_log_use_case=create_audit_log_use_case
)

# Log action (saves to console AND database)
audit_logger.log_action(
    user_id=user.id,
    organization_id=user.organization_id,
    action="user.create",
    resource_type="user",
    resource_id=user.id,
    details={"username": user.username, "role": user.role},
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

**Migration Details:**
1. ✅ Created complete audit service with Clean Architecture
2. ✅ Added AuditLogModel to centralized models.py
3. ✅ Updated shared/logging.py AuditLogger to persist to DB
4. ✅ Registered audit routes in main.py
5. ✅ Added audit endpoints to shared/api_routes.py

---

## Documentation

- `ARCHITECTURE.md` - Panduan lengkap Clean Architecture
- `REFACTORING_AUDIT.md` - Audit existing code

