# Clean Architecture Guide

## 🎯 Prinsip Utama

1. **Separation of Concerns** - Setiap layer punya tanggung jawab jelas
2. **Dependency Inversion** - Core tidak depend ke infrastructure
3. **1 File = 1 Responsibility** - Tidak ada code bloat
4. **Testability** - Easy to test, easy to mock

---

## 📂 Layer Structure

### 1. **domain/** - Core Business Logic

**Aturan:**
- ✅ NO dependencies (framework, database, external libs)
- ✅ Pure Python objects
- ✅ Business rules & validation

**Contains:**
- **user.py** - User entity + Credentials value object
- **interfaces.py** - IUserRepository contract

**Example:**
```python
# domain/user.py
@dataclass
class User:
    id: int
    username: str

    def is_admin(self) -> bool:
        return self.role == "ADMIN"

@dataclass(frozen=True)
class Credentials:
    username: str
    password: str
```

---

### 2. **use_cases/** - Application Logic

**Aturan:**
- ✅ 1 file = 1 use case
- ✅ Depends ONLY on domain/ interfaces
- ✅ Coordinates business logic

**Contains:**
- **login.py** - Login use case
- **register.py** - Register use case
- **logout.py** - Logout use case (kalau ada)

**Example:**
```python
# use_cases/login.py
class LoginUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, username, password) -> str:
        user = self.user_repo.find_by_username(username)
        # Business logic here
        return token
```

**Why 1 file = 1 use case?**
- Easy to find (login.py vs services.py dengan 50 methods)
- Easy to test (test satu use case saja)
- Easy to change (ubah login tidak affect register)

---

### 3. **repositories/** - Infrastructure Layer

**Aturan:**
- ✅ Implements domain/ interfaces
- ✅ Database access only
- ✅ Framework-specific code (SQLAlchemy)

**Contains:**
- **models.py** - SQLAlchemy models (UserModel)
- **user_repo.py** - Repository implementation

**Example:**
```python
# repositories/user_repo.py
class UserRepository(IUserRepository):
    def find_by_username(self, username: str) -> User:
        model = db.query(UserModel).filter(...).first()
        return self._to_entity(model)  # Convert to domain entity
```

---

### 4. **routes.py** - HTTP Layer

**Aturan:**
- ✅ HTTP endpoints only
- ✅ Dependency injection
- ✅ NO business logic (delegate to use cases)

**Contains:**
- **routes.py** - FastAPI endpoints
- **dtos.py** - Request/Response DTOs

**Example:**
```python
# routes.py
@router.post("/login")
def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case)
):
    result = use_case.execute(request.username, request.password)
    return {"token": result}
```

---

## 🔄 Data Flow Example: Login

```
1. HTTP Request
   ↓
2. api/routes.py (Validate input, create LoginRequest DTO)
   ↓
3. application/use_cases/login.py (Business logic)
   ↓
4. domain/interfaces/user_repository.py (Call interface)
   ↓
5. infrastructure/repositories/user_repository.py (Query DB)
   ↓
6. domain/entities/user.py (Return User entity)
   ↓
7. application/use_cases/login.py (Create JWT token)
   ↓
8. api/routes.py (Return TokenResponse)
```

---

## 🎯 Benefits

### ✅ Easy to Change
**Ganti DB (Postgres → MongoDB):**
- ❌ Flat: Ubah 50 files
- ✅ Clean: Ubah `infrastructure/repositories/` saja

**Tambah validasi bisnis:**
- ❌ Flat: Edit di tengah API route
- ✅ Clean: Edit `application/use_cases/` saja

**Ganti framework (FastAPI → Django):**
- ❌ Flat: Rewrite semua
- ✅ Clean: Ubah `api/routes.py` saja, domain tetap sama

### ✅ Easy to Test
```python
# Test use case WITHOUT database
def test_login():
    # Mock repository
    mock_repo = MockUserRepository()
    use_case = LoginUseCase(mock_repo)

    # Test business logic
    result = use_case.execute("admin", "password")
    assert result["token"] is not None
```

### ✅ Easy to Find
- Cari logic login? → `application/use_cases/login.py`
- Cari DB query? → `infrastructure/repositories/`
- Cari User entity? → `domain/entities/user.py`

---

## 📏 File Size Rules

**Kapan harus split file?**
- **> 200 lines** → Pertimbangkan split
- **> 500 lines** → MUST split
- **> 10 methods** dalam 1 class → Split by responsibility

**Contoh split:**
```
# BEFORE
services.py  # 800 lines, 15 methods

# AFTER
use_cases/
├── login.py           # 80 lines
├── register.py        # 120 lines
├── logout.py          # 50 lines
├── reset_password.py  # 100 lines
└── change_password.py # 90 lines
```

---

## 🚀 Creating New Feature

**Steps:**
1. **Define entity** (domain/entities/)
2. **Create repository interface** (domain/interfaces/)
3. **Implement repository** (infrastructure/repositories/)
4. **Create use case** (application/use_cases/ - 1 file!)
5. **Create DTO** (application/dtos/)
6. **Add HTTP route** (api/routes.py)

**Example: Add "Delete User" feature**
```bash
# Already exists:
domain/entities/user.py
domain/interfaces/user_repository.py (add delete method)

# Create new:
infrastructure/repositories/user_repository.py (implement delete)
application/use_cases/delete_user.py  # NEW FILE - 1 use case
application/dtos/user_dtos.py (add DeleteUserRequest)
api/routes.py (add DELETE /users/{id} endpoint)
```

---

## ⚠️ Anti-Patterns (AVOID!)

❌ **Business logic in routes:**
```python
@router.post("/login")
def login(username, password):
    user = db.query(User).filter(...)  # ❌ DB in route
    if not verify_password(...):  # ❌ Business logic in route
```

❌ **Domain depends on infrastructure:**
```python
# domain/entities/user.py
from infrastructure.models import UserModel  # ❌ WRONG!
```

❌ **God class (1 file banyak method):**
```python
# services.py
class AuthService:
    def login(): ...
    def register(): ...
    def logout(): ...
    # ... 20 more methods ❌
```

✅ **Correct:**
```python
# application/use_cases/login.py
class LoginUseCase:
    def execute(): ...  # ONLY login logic

# application/use_cases/register.py
class RegisterUseCase:
    def execute(): ...  # ONLY register logic
```

---

## 📚 Summary

| Layer | Purpose | Dependencies | Example |
|-------|---------|--------------|---------|
| **domain/** | Business logic | NONE | User entity, IUserRepository |
| **application/** | Use cases | domain/ only | login.py, register.py |
| **infrastructure/** | DB, External | domain/ interfaces | UserRepository, UserModel |
| **api/** | HTTP endpoints | application/ | FastAPI routes |

**Key principle:** Dependencies point INWARD (api → application → domain)
