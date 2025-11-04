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
└── shared/                 # Shared utilities (NO business logic!)
    ├── api_routes.py      # ⚠️ CENTRALIZED API ROUTES DEFINITION
    ├── config.py          # Settings from .env
    └── database.py        # SQLAlchemy setup
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

## Documentation

- `ARCHITECTURE.md` - Panduan lengkap Clean Architecture
- `REFACTORING_AUDIT.md` - Audit existing code

