# 🚧 ARSAKA_PUGUH — STAGED DEPLOYMENT IMPLEMENTATION PLAN

**Date:** 2026-01-08
**Based On:** Staged Deployment Plan (Visible System First)
**Approach:** Pragmatic, functional, security-aware (NOT production-ready)

---

## 🎯 PHILOSOPHY

> **"Make it VISIBLE and CORRECT, not PERFECT"**

- ✅ Sistem bisa dilihat & dipakai
- ✅ Flow correctness dijaga
- ✅ Security minimal WAJIB
- ❌ BUKAN production-ready
- ❌ BUKAN scalable/HA
- ❌ BUKAN beautifully designed

**Banner Everywhere:**
```
⚠️ INTERNAL USE ONLY — NON-PRODUCTION ENVIRONMENT
⚠️ DATA MAY BE DELETED WITHOUT NOTICE
⚠️ DO NOT USE FOR REAL BUSINESS DATA
```

---

## 🟢 PHASE A — VISIBLE SYSTEM (LOCAL/STAGING)

**Goal:** Sistem hidup, bisa login, create decision, approve, lihat audit trail

**Timeline:** 2-3 weeks
**Environment:** Local development + staging VPS

---

### 📋 TASK BREAKDOWN - PHASE A

#### A1. SECURITY FOUNDATION (WEEK 1 - Priority 🔴 CRITICAL)

##### A1.1: Remove Hardcoded Credentials
**Effort:** 2 hours
**Files:**
- `backend/core/app.py`
- `backend/core/app_v2.py`

**Changes:**
```python
# BEFORE (INSECURE):
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://signage_user:signage_password@localhost:5433/signage_db"
)

# AFTER (SECURE):
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "❌ DATABASE_URL is required. Set it in .env file.\n"
        "Example: DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db"
    )
```

**Checklist:**
- [ ] Remove hardcoded password from app.py
- [ ] Remove hardcoded password from app_v2.py
- [ ] Add fail-fast validation for DATABASE_URL
- [ ] Test: Application fails to start without DATABASE_URL
- [ ] Git commit with message: "security: remove hardcoded database credentials"

---

##### A1.2: Centralized Configuration
**Effort:** 4 hours
**Files:**
- Create `backend/shared/config.py`
- Create `backend/.env.example`
- Update `backend/requirements.txt`

**Implementation:**

**File: `backend/shared/config.py`**
```python
"""
Centralized Configuration

Phase A: Minimal config for visible system
"""
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn, validator


class Settings(BaseSettings):
    """Application configuration with validation"""

    # ===== Environment =====
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )

    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    # ===== Database (REQUIRED) =====
    database_url: PostgresDsn = Field(
        ...,  # Required, no default
        description="PostgreSQL connection URL"
    )

    # ===== Redis (Optional for Phase A) =====
    redis_enabled: bool = Field(default=False)
    redis_url: Optional[RedisDsn] = Field(default=None)

    # ===== Authentication (REQUIRED for Phase A) =====
    jwt_secret_key: str = Field(
        ...,  # Required
        min_length=32,
        description="JWT secret key (min 32 characters)"
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)

    # ===== CORS =====
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ===== Tenant Whitelist (Phase A: Hardcoded) =====
    allowed_tenant_ids: List[str] = Field(
        default=[
            "550e8400-e29b-41d4-a716-446655440000",  # Demo Tenant 1
            "550e8400-e29b-41d4-a716-446655440001",  # Demo Tenant 2
        ],
        description="Hardcoded tenant whitelist for Phase A"
    )

    # ===== Logging =====
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    @validator("log_level")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v

    # ===== Application =====
    app_name: str = Field(default="ARSAKA_PUGUH Core Service")
    app_version: str = Field(default="0.1.0-alpha")

    # ===== Rate Limiting (Phase A: Strict) =====
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(
        default=30,  # Strict for Phase A
        description="Max requests per minute per tenant"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience alias
settings = get_settings()
```

**File: `backend/.env.example`**
```bash
# ===== ARSAKA_PUGUH Configuration — Phase A =====
# Copy this file to .env and fill in your values
# DO NOT commit .env to git!

# Environment
ENVIRONMENT=development  # development | staging | production

# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/dbname

# Redis (Optional in Phase A, enable in Phase B)
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379

# JWT Authentication (REQUIRED)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Tenant Whitelist (Phase A: Hardcoded)
# Format: comma-separated UUIDs
ALLOWED_TENANT_IDS=550e8400-e29b-41d4-a716-446655440000,550e8400-e29b-41d4-a716-446655440001

# Logging
LOG_LEVEL=INFO

# Rate Limiting (Strict in Phase A)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=30

# ===== WARNINGS =====
# ⚠️ This is a NON-PRODUCTION environment
# ⚠️ Data may be deleted without notice
# ⚠️ Do not use for real business data
```

**Add to `backend/requirements.txt`:**
```
pydantic-settings==2.1.0
```

**Checklist:**
- [ ] Create `shared/config.py` with Settings class
- [ ] Create `.env.example` with all variables
- [ ] Add pydantic-settings to requirements.txt
- [ ] Update app.py to use `settings.database_url`
- [ ] Update app_v2.py to use `settings.database_url`
- [ ] Test: Application fails with clear error if JWT_SECRET_KEY missing
- [ ] Test: Environment validation works (invalid env → error)
- [ ] Git commit: "feat: centralized configuration with validation"

---

##### A1.3: JWT Authentication (Basic)
**Effort:** 1 day (8 hours)
**Files:**
- Create `backend/shared/auth.py`
- Create `backend/shared/dependencies.py`
- Update `backend/core/api/routers.py`

**Implementation:**

**File: `backend/shared/auth.py`**
```python
"""
JWT Authentication — Phase A (Basic)

Features:
- Login with username/password
- JWT token generation
- Token validation
- User model (minimal)

NOT included in Phase A:
- Password reset
- Email verification
- OAuth
- Session management
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from shared.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    """User model (minimal for Phase A)"""
    user_id: str
    username: str
    tenant_id: str
    role: str  # "admin" or "approver" for Phase A


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: str
    username: str
    tenant_id: str
    role: str


class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(user: User) -> str:
    """
    Create JWT access token

    Phase A: Simple token with user data
    """
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": user.user_id,
        "username": user.username,
        "tenant_id": user.tenant_id,
        "role": user.role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate JWT token

    Returns TokenData if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        tenant_id: str = payload.get("tenant_id")
        role: str = payload.get("role")

        if user_id is None or tenant_id is None:
            return None

        return TokenData(
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            role=role
        )
    except JWTError:
        return None
```

**File: `backend/shared/dependencies.py`**
```python
"""
FastAPI Dependencies — Authentication & Authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.auth import User, decode_access_token, TokenData
from shared.config import settings


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency: Extract and validate current user from JWT token

    Raises:
        401 Unauthorized if token invalid
        403 Forbidden if tenant not in whitelist
    """
    token = credentials.credentials

    # Decode token
    token_data: TokenData = decode_access_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Phase A: Verify tenant in whitelist
    if token_data.tenant_id not in settings.allowed_tenant_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant {token_data.tenant_id} not allowed in Phase A"
        )

    return User(
        user_id=token_data.user_id,
        username=token_data.username,
        tenant_id=token_data.tenant_id,
        role=token_data.role
    )


async def require_role(required_role: str):
    """
    Dependency factory: Require specific role

    Usage:
        @router.post("/admin-only", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {required_role}"
            )
        return user
    return role_checker
```

**Add Authentication Endpoints to `backend/core/api/routers.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from shared.auth import User, create_access_token, verify_password, Token
from shared.dependencies import get_current_user

router = APIRouter(prefix="/api/v1", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


# Hardcoded users for Phase A (WILL BE REPLACED IN PHASE B)
PHASE_A_USERS = {
    "admin": {
        "user_id": "user-001",
        "username": "admin",
        "password_hash": "$2b$12$KIX.6GdXj8L0hXH6Zf4tYe5LqYvJ8K9Z1...",  # "admin123"
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "role": "admin"
    },
    "approver": {
        "user_id": "user-002",
        "username": "approver",
        "password_hash": "$2b$12$KIX.6GdXj8L0hXH6Zf4tYe5LqYvJ8K9Z2...",  # "approver123"
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "role": "approver"
    }
}


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint (Phase A: Hardcoded users)

    Phase A: Uses hardcoded user dict
    Phase B: Will query database
    """
    user_data = PHASE_A_USERS.get(request.username)

    # Verify user exists
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Verify password
    if not verify_password(request.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Create user object
    user = User(
        user_id=user_data["user_id"],
        username=user_data["username"],
        tenant_id=user_data["tenant_id"],
        role=user_data["role"]
    )

    # Generate JWT token
    access_token = create_access_token(user)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "user_id": user.user_id,
            "username": user.username,
            "tenant_id": user.tenant_id,
            "role": user.role
        }
    )


@router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "user_id": user.user_id,
        "username": user.username,
        "tenant_id": user.tenant_id,
        "role": user.role
    }
```

**Add to `backend/requirements.txt`:**
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

**Checklist:**
- [ ] Create `shared/auth.py` with JWT functions
- [ ] Create `shared/dependencies.py` with auth dependencies
- [ ] Add login endpoint to routers.py
- [ ] Add "me" endpoint to routers.py
- [ ] Generate password hashes for hardcoded users
- [ ] Add python-jose and passlib to requirements.txt
- [ ] Test: Login with valid credentials returns token
- [ ] Test: Login with invalid credentials returns 401
- [ ] Test: /auth/me with valid token returns user info
- [ ] Test: /auth/me without token returns 401
- [ ] Test: Token from non-whitelisted tenant returns 403
- [ ] Git commit: "feat: JWT authentication (Phase A - basic)"

---

##### A1.4: Protect Decision Endpoints
**Effort:** 2 hours
**Files:**
- Update `backend/core/api/routers.py`

**Changes:**
```python
from shared.dependencies import get_current_user
from shared.auth import User

# Add user dependency to ALL decision endpoints
@router.post("/decisions")
async def create_decision(
    request: CreateDecisionRequest,
    user: User = Depends(get_current_user),  # ✅ AUTH REQUIRED
    use_case: CreateDecisionUseCase = Depends(get_create_decision_use_case)
):
    """Create decision (authenticated)"""

    # Verify tenant match
    if request.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot create decision for different tenant"
        )

    # Pass user_id to use case
    input_dto = CreateDecisionInput(
        tenant_id=request.tenant_id,
        decision_type=request.decision_type,
        context=request.context,
        idempotency_key=request.idempotency_key,
        trace_id=request.trace_id,
        requester_user_id=user.user_id  # ✅ FROM JWT TOKEN
    )

    output = await use_case.execute(input_dto)
    return CreateDecisionResponse(...)


@router.post("/workflows/{workflow_id}/approve")
async def approve_workflow(
    workflow_id: UUID,
    request: ApproveWorkflowRequest,
    user: User = Depends(get_current_user),  # ✅ AUTH REQUIRED
    use_case: ApproveWorkflowUseCase = Depends(get_approve_workflow_use_case)
):
    """Approve workflow (authenticated, role-based)"""

    # Phase A: Only approvers can approve
    if user.role not in ["admin", "approver"]:
        raise HTTPException(
            status_code=403,
            detail="Only admins and approvers can approve workflows"
        )

    # Verify tenant match
    if request.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot approve workflow from different tenant"
        )

    input_dto = ApproveWorkflowInput(
        workflow_id=workflow_id,
        tenant_id=request.tenant_id,
        approver_role=user.role,
        acted_by_user_id=user.user_id,  # ✅ FROM JWT TOKEN
        comment=request.comment,
        trace_id=request.trace_id
    )

    output = await use_case.execute(input_dto)
    return ApproveWorkflowResponse(...)
```

**Checklist:**
- [ ] Add `user: User = Depends(get_current_user)` to all decision endpoints
- [ ] Add `user: User = Depends(get_current_user)` to all workflow endpoints
- [ ] Verify tenant_id in request matches user.tenant_id
- [ ] Pass user.user_id as requester_user_id/acted_by_user_id
- [ ] Test: Endpoints without token return 401
- [ ] Test: Endpoints with invalid token return 401
- [ ] Test: Cross-tenant requests return 403
- [ ] Test: Non-approver cannot approve workflows
- [ ] Git commit: "feat: protect decision endpoints with JWT auth"

---

##### A1.5: Health Endpoints
**Effort:** 1 hour
**Files:**
- Update `backend/core/app.py`
- Update `backend/core/app_v2.py`

**Implementation:**
```python
from datetime import datetime
from fastapi import status
from sqlalchemy import text
from shared.config import settings

@app.get("/health", status_code=status.HTTP_200_OK, tags=["monitoring"])
async def health_check(db: AsyncSession = Depends(get_session)):
    """
    Health check endpoint

    Returns service health including database connectivity.
    Used by monitoring and load balancers.
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {}
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health["checks"]["database"] = "connected"
    except Exception as e:
        health["status"] = "unhealthy"
        health["checks"]["database"] = f"error: {str(e)}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health
        )

    # Phase A warning banner
    health["warnings"] = [
        "⚠️ NON-PRODUCTION ENVIRONMENT",
        "⚠️ DATA MAY BE DELETED WITHOUT NOTICE",
        "⚠️ DO NOT USE FOR REAL BUSINESS DATA"
    ]

    return health


@app.get("/ready", status_code=status.HTTP_200_OK, tags=["monitoring"])
async def readiness_check(db: AsyncSession = Depends(get_session)):
    """
    Readiness check endpoint

    Returns whether service is ready to accept traffic.
    Used by Kubernetes readiness probes.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False}
        )
```

**Checklist:**
- [ ] Add /health endpoint to app.py
- [ ] Add /health endpoint to app_v2.py
- [ ] Add /ready endpoint to app.py
- [ ] Add /ready endpoint to app_v2.py
- [ ] Include Phase A warning in /health response
- [ ] Test: /health returns 200 when database up
- [ ] Test: /health returns 503 when database down
- [ ] Test: /ready returns 200 when database up
- [ ] Git commit: "feat: add health and readiness endpoints"

---

#### A2. MINIMAL ADAPTER (WEEK 1 - Priority 🟠 HIGH)

##### A2.1: User→Role Resolution
**Effort:** 2 hours
**Files:**
- Create `backend/core/adapters/user_adapter.py`

**Implementation:**
```python
"""
User Adapter — Phase A (Minimal)

Resolves:
- User ID → User details
- Role → Approver list

Phase A: Hardcoded mappings
Phase B: Database queries
"""
from typing import List, Optional
from pydantic import BaseModel


class UserInfo(BaseModel):
    user_id: str
    username: str
    role: str
    tenant_id: str


class ApproverInfo(BaseModel):
    user_id: str
    username: str
    role: str


# Phase A: Hardcoded user database
PHASE_A_USERS_DB = {
    "user-001": UserInfo(
        user_id="user-001",
        username="admin",
        role="admin",
        tenant_id="550e8400-e29b-41d4-a716-446655440000"
    ),
    "user-002": UserInfo(
        user_id="user-002",
        username="approver",
        role="approver",
        tenant_id="550e8400-e29b-41d4-a716-446655440000"
    ),
    "user-003": UserInfo(
        user_id="user-003",
        username="admin2",
        role="admin",
        tenant_id="550e8400-e29b-41d4-a716-446655440001"
    )
}


class UserAdapter:
    """
    User Adapter — Phase A

    Minimal implementation for visible system.
    """

    async def get_user(self, user_id: str) -> Optional[UserInfo]:
        """Get user by ID"""
        return PHASE_A_USERS_DB.get(user_id)

    async def get_approvers_for_role(
        self,
        tenant_id: str,
        role: str
    ) -> List[ApproverInfo]:
        """
        Get list of users who can approve for given role

        Phase A: Returns all users with "approver" or "admin" role in tenant
        """
        approvers = []

        for user_id, user in PHASE_A_USERS_DB.items():
            if user.tenant_id == tenant_id:
                if user.role in ["admin", "approver"]:
                    approvers.append(ApproverInfo(
                        user_id=user.user_id,
                        username=user.username,
                        role=user.role
                    ))

        return approvers

    async def resolve_role_to_users(
        self,
        tenant_id: str,
        role: str
    ) -> List[str]:
        """
        Resolve role name to list of user IDs

        Phase A: Simple role matching
        """
        approvers = await self.get_approvers_for_role(tenant_id, role)
        return [a.user_id for a in approvers]
```

**Checklist:**
- [ ] Create `core/adapters/user_adapter.py`
- [ ] Implement get_user() method
- [ ] Implement get_approvers_for_role() method
- [ ] Implement resolve_role_to_users() method
- [ ] Add 2-3 hardcoded users per tenant
- [ ] Test: Can resolve user by ID
- [ ] Test: Can get approvers for tenant
- [ ] Test: Cross-tenant users not returned
- [ ] Git commit: "feat: minimal user adapter (Phase A)"

---

#### A3. DOCKER CONFIGURATION (WEEK 1 - Priority 🔴 CRITICAL)

##### A3.1: Create Dockerfile
**Effort:** 2 hours
**Files:**
- Create `docker/Dockerfile`

**Implementation:**
```dockerfile
# ARSAKA_PUGUH Backend — Phase A Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Run application
CMD ["uvicorn", "core.app_v2:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Checklist:**
- [ ] Create `docker/Dockerfile`
- [ ] Use Python 3.11 slim base image
- [ ] Install system dependencies (gcc, postgresql-client)
- [ ] Copy requirements.txt first (caching)
- [ ] Create non-root user (appuser)
- [ ] Add health check
- [ ] Test: Docker build succeeds
- [ ] Test: Container starts successfully
- [ ] Git commit: "feat: Dockerfile for backend (Phase A)"

---

##### A3.2: Create docker-compose.yml
**Effort:** 3 hours
**Files:**
- Create `docker/docker-compose.yml`
- Create `docker/.env.example`

**Implementation:**
```yaml
# ARSAKA_PUGUH — Phase A Docker Compose
# NON-PRODUCTION ENVIRONMENT

version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: atlas-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-arsaka_puguh}
      POSTGRES_USER: ${DB_USER:-atlas_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD required}
    ports:
      - "${DB_PORT:-5433}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../backend/migrations:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-atlas_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (Optional in Phase A)
  redis:
    image: redis:7-alpine
    container_name: atlas-redis
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    profiles:
      - with-redis  # Optional, start with: docker-compose --profile with-redis up

  # Backend API
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: atlas-backend
    restart: unless-stopped
    environment:
      # Environment
      ENVIRONMENT: ${ENVIRONMENT:-development}

      # Database
      DATABASE_URL: postgresql+asyncpg://${DB_USER:-atlas_user}:${DB_PASSWORD}@postgres:5432/${DB_NAME:-arsaka_puguh}

      # Redis
      REDIS_ENABLED: ${REDIS_ENABLED:-false}
      REDIS_URL: ${REDIS_URL:-redis://redis:6379}

      # JWT
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:?JWT_SECRET_KEY required}
      JWT_ALGORITHM: HS256
      JWT_ACCESS_TOKEN_EXPIRE_MINUTES: 30

      # CORS
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000}

      # Tenant Whitelist
      ALLOWED_TENANT_IDS: ${ALLOWED_TENANT_IDS}

      # Logging
      LOG_LEVEL: ${LOG_LEVEL:-INFO}

      # Rate Limiting
      RATE_LIMIT_ENABLED: ${RATE_LIMIT_ENABLED:-true}
      RATE_LIMIT_REQUESTS_PER_MINUTE: ${RATE_LIMIT_REQUESTS_PER_MINUTE:-30}

    ports:
      - "${API_PORT:-8001}:8001"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    labels:
      - "com.atlas.environment=${ENVIRONMENT:-development}"
      - "com.atlas.warning=NON-PRODUCTION"

volumes:
  postgres_data:
    name: atlas_postgres_data
  redis_data:
    name: atlas_redis_data

networks:
  default:
    name: atlas_network
```

**File: `docker/.env.example`**
```bash
# ===== ARSAKA_PUGUH — Phase A Docker Environment =====
# Copy to .env and fill in your values

# ===== WARNING =====
# ⚠️ NON-PRODUCTION ENVIRONMENT
# ⚠️ DATA MAY BE DELETED WITHOUT NOTICE
# ⚠️ DO NOT USE FOR REAL BUSINESS DATA

# Environment
ENVIRONMENT=development

# Database
DB_NAME=arsaka_puguh
DB_USER=atlas_user
DB_PASSWORD=your_secure_password_here  # CHANGE THIS!
DB_PORT=5433

# Redis (Optional in Phase A)
REDIS_ENABLED=false
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# JWT Authentication (REQUIRED)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your_jwt_secret_key_here_min_32_chars  # CHANGE THIS!

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Tenant Whitelist (Phase A)
ALLOWED_TENANT_IDS=550e8400-e29b-41d4-a716-446655440000,550e8400-e29b-41d4-a716-446655440001

# Backend API
API_PORT=8001

# Logging
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=30
```

**Checklist:**
- [ ] Create `docker/docker-compose.yml`
- [ ] Add PostgreSQL service with health check
- [ ] Add Redis service (optional profile)
- [ ] Add backend service with environment variables
- [ ] Create `docker/.env.example`
- [ ] Add volume mounts for data persistence
- [ ] Add health checks for all services
- [ ] Test: `docker-compose up -d` starts all services
- [ ] Test: Backend connects to PostgreSQL
- [ ] Test: Health check accessible at http://localhost:8001/health
- [ ] Git commit: "feat: docker-compose for Phase A deployment"

---

#### A4. FRONTEND MINIMAL (WEEK 2 - Priority 🟠 HIGH)

**Note:** Frontend akan dibuat sebagai **React + Vite project** yang sangat minimal.

**Tech Stack:**
- React 18
- TypeScript
- Vite
- TanStack Query (server state)
- Axios (HTTP client)
- React Hook Form (forms)
- Tailwind CSS (styling - minimal)

##### A4.1: Frontend Bootstrap
**Effort:** 4 hours
**Files:**
- Create frontend project structure
- Setup dependencies

**Steps:**
```bash
# Create Vite + React + TypeScript project
cd ARSAKA_PUGUH/frontend
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
npm install axios @tanstack/react-query react-hook-form
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**File: `frontend/package.json`**
```json
{
  "name": "arsaka-puguh-frontend",
  "version": "0.1.0-alpha",
  "description": "ARSAKA_PUGUH Frontend — Phase A (Minimal)",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0",
    "react-hook-form": "^7.48.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.2.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

**File: `frontend/tailwind.config.js`**
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**File: `frontend/src/index.css`**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Phase A Warning Banner */
.phase-a-warning {
  background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
  color: white;
  padding: 0.5rem;
  text-align: center;
  font-weight: 600;
  font-size: 0.875rem;
  position: sticky;
  top: 0;
  z-index: 9999;
}
```

**Checklist:**
- [ ] Create Vite + React + TypeScript project
- [ ] Install dependencies (axios, react-query, react-hook-form)
- [ ] Setup Tailwind CSS
- [ ] Create basic file structure
- [ ] Test: `npm run dev` starts dev server
- [ ] Git commit: "feat: frontend bootstrap (Phase A)"

---

##### A4.2: API Client & Auth
**Effort:** 4 hours
**Files:**
- Create `frontend/src/lib/api.ts`
- Create `frontend/src/lib/auth.ts`

**File: `frontend/src/lib/api.ts`**
```typescript
/**
 * API Client — Phase A
 */
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle 401 responses
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth
  async login(username: string, password: string) {
    const response = await this.client.post('/api/v1/auth/login', {
      username,
      password,
    });
    return response.data;
  }

  async getMe() {
    const response = await this.client.get('/api/v1/auth/me');
    return response.data;
  }

  // Decisions
  async createDecision(data: any) {
    const response = await this.client.post('/api/v1/decisions', data);
    return response.data;
  }

  async getDecisions(tenantId: string) {
    const response = await this.client.get('/api/v1/decisions', {
      params: { tenant_id: tenantId },
    });
    return response.data;
  }

  // Workflows
  async getWorkflows(tenantId: string, status?: string) {
    const response = await this.client.get('/api/v1/workflows', {
      params: { tenant_id: tenantId, status },
    });
    return response.data;
  }

  async approveWorkflow(workflowId: string, data: any) {
    const response = await this.client.post(
      `/api/v1/workflows/${workflowId}/approve`,
      data
    );
    return response.data;
  }

  async rejectWorkflow(workflowId: string, data: any) {
    const response = await this.client.post(
      `/api/v1/workflows/${workflowId}/reject`,
      data
    );
    return response.data;
  }

  // Health
  async getHealth() {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const apiClient = new ApiClient();
```

**File: `frontend/src/lib/auth.ts`**
```typescript
/**
 * Auth Helper — Phase A
 */

export interface User {
  user_id: string;
  username: string;
  tenant_id: string;
  role: string;
}

export function saveAuth(accessToken: string, user: User) {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('user', JSON.stringify(user));
}

export function getUser(): User | null {
  const userJson = localStorage.getItem('user');
  if (!userJson) return null;
  return JSON.parse(userJson);
}

export function getToken(): string | null {
  return localStorage.getItem('access_token');
}

export function clearAuth() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
```

**Checklist:**
- [ ] Create `lib/api.ts` with API client
- [ ] Create `lib/auth.ts` with auth helpers
- [ ] Add interceptors for auth token
- [ ] Add 401 response handling
- [ ] Implement login, getMe methods
- [ ] Implement decision methods
- [ ] Implement workflow methods
- [ ] Test: API client can make requests
- [ ] Git commit: "feat: API client and auth helpers (Phase A)"

---

##### A4.3: Login Page
**Effort:** 4 hours
**Files:**
- Create `frontend/src/pages/LoginPage.tsx`
- Create `frontend/src/App.tsx`

**File: `frontend/src/pages/LoginPage.tsx`**
```typescript
/**
 * Login Page — Phase A
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api';
import { saveAuth } from '../lib/auth';

interface LoginForm {
  username: string;
  password: string;
}

export function LoginPage() {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onSubmit = async (data: LoginForm) => {
    setError(null);
    setLoading(true);

    try {
      const response = await apiClient.login(data.username, data.password);
      saveAuth(response.access_token, response.user);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      {/* Phase A Warning Banner */}
      <div className="phase-a-warning fixed top-0 left-0 right-0">
        ⚠️ NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED WITHOUT NOTICE
      </div>

      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md mt-12">
        <h1 className="text-2xl font-bold mb-6 text-center">
          ARSAKA_PUGUH
        </h1>

        <p className="text-sm text-gray-600 mb-6 text-center">
          Phase A — Internal Testing Only
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              {...register('username', { required: 'Username required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="admin"
            />
            {errors.username && (
              <p className="text-red-500 text-sm mt-1">{errors.username.message}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              {...register('password', { required: 'Password required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
            />
            {errors.password && (
              <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        {/* Phase A Credentials */}
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded text-sm">
          <p className="font-medium text-yellow-800 mb-2">Phase A Test Credentials:</p>
          <ul className="text-yellow-700 space-y-1">
            <li>• Username: <code>admin</code> / Password: <code>admin123</code></li>
            <li>• Username: <code>approver</code> / Password: <code>approver123</code></li>
          </ul>
        </div>
      </div>
    </div>
  );
}
```

**Checklist:**
- [ ] Create `pages/LoginPage.tsx`
- [ ] Add Phase A warning banner
- [ ] Add login form with validation
- [ ] Handle login errors
- [ ] Show test credentials (Phase A only)
- [ ] Redirect to dashboard after successful login
- [ ] Test: Can login with hardcoded credentials
- [ ] Test: Invalid credentials show error
- [ ] Git commit: "feat: login page (Phase A)"

---

##### A4.4: Dashboard & Navigation
**Effort:** 4 hours
**Files:**
- Create `frontend/src/pages/DashboardPage.tsx`
- Create `frontend/src/components/Layout.tsx`

**File: `frontend/src/pages/DashboardPage.tsx`**
```typescript
/**
 * Dashboard — Phase A
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { getUser } from '../lib/auth';

export function DashboardPage() {
  const user = getUser();

  // Fetch health (demo query)
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* User Info */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-lg font-semibold mb-4">Current User</h2>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-gray-600">Username</dt>
            <dd className="font-medium">{user?.username}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-600">Role</dt>
            <dd className="font-medium">{user?.role}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-600">Tenant ID</dt>
            <dd className="font-mono text-sm">{user?.tenant_id}</dd>
          </div>
        </dl>
      </div>

      {/* System Status */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">System Status</h2>
        {health && (
          <div>
            <p className="text-sm text-gray-600">Status: <span className="text-green-600 font-medium">{health.status}</span></p>
            <p className="text-sm text-gray-600 mt-2">Environment: <span className="font-medium">{health.environment}</span></p>
            <p className="text-sm text-gray-600 mt-2">Version: <span className="font-medium">{health.version}</span></p>

            {/* Warnings */}
            {health.warnings && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
                <p className="text-sm font-medium text-yellow-800 mb-2">⚠️ System Warnings:</p>
                <ul className="text-sm text-yellow-700 space-y-1">
                  {health.warnings.map((warning: string, idx: number) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

**File: `frontend/src/components/Layout.tsx`**
```typescript
/**
 * Layout Component — Phase A
 */
import { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getUser, clearAuth } from '../lib/auth';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const user = getUser();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuth();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Phase A Warning Banner */}
      <div className="phase-a-warning">
        ⚠️ NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED WITHOUT NOTICE
      </div>

      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <Link to="/" className="flex items-center px-3 py-2 text-gray-700 hover:text-gray-900">
                Dashboard
              </Link>
              <Link to="/decisions" className="flex items-center px-3 py-2 text-gray-700 hover:text-gray-900">
                Decisions
              </Link>
              <Link to="/workflows" className="flex items-center px-3 py-2 text-gray-700 hover:text-gray-900">
                Workflows
              </Link>
              <Link to="/audit" className="flex items-center px-3 py-2 text-gray-700 hover:text-gray-900">
                Audit Trail
              </Link>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {user?.username} ({user?.role})
              </span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}
```

**Checklist:**
- [ ] Create `pages/DashboardPage.tsx`
- [ ] Create `components/Layout.tsx`
- [ ] Add navigation with Phase A warning
- [ ] Show current user info
- [ ] Show system health status
- [ ] Add logout button
- [ ] Test: Dashboard loads after login
- [ ] Test: Logout clears auth and redirects
- [ ] Git commit: "feat: dashboard and layout (Phase A)"

---

##### A4.5: Create Decision Form
**Effort:** 6 hours
**Files:**
- Create `frontend/src/pages/DecisionsPage.tsx`
- Create `frontend/src/components/CreateDecisionForm.tsx`

**File: `frontend/src/components/CreateDecisionForm.tsx`**
```typescript
/**
 * Create Decision Form — Phase A
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { getUser } from '../lib/auth';

interface DecisionFormData {
  decision_type: string;
  amount: number;
  customer_id: string;
  idempotency_key: string;
}

export function CreateDecisionForm() {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<DecisionFormData>();
  const [success, setSuccess] = useState<any>(null);
  const user = getUser();
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: any) => apiClient.createDecision(data),
    onSuccess: (data) => {
      setSuccess(data);
      reset();
      queryClient.invalidateQueries({ queryKey: ['decisions'] });

      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000);
    },
  });

  const onSubmit = (data: DecisionFormData) => {
    const payload = {
      tenant_id: user?.tenant_id,
      decision_type: data.decision_type,
      context: {
        amount: parseFloat(data.amount.toString()),
        customer_id: data.customer_id,
      },
      idempotency_key: data.idempotency_key || `decision-${Date.now()}`,
      trace_id: `trace-${Date.now()}`,
      requester_user_id: user?.user_id,
    };

    createMutation.mutate(payload);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Create Decision</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Decision Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Decision Type
          </label>
          <select
            {...register('decision_type', { required: 'Decision type required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">Select type...</option>
            <option value="credit_approval">Credit Approval</option>
            <option value="kyc_verification">KYC Verification</option>
            <option value="transaction_review">Transaction Review</option>
          </select>
          {errors.decision_type && (
            <p className="text-red-500 text-sm mt-1">{errors.decision_type.message}</p>
          )}
        </div>

        {/* Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Amount
          </label>
          <input
            type="number"
            step="0.01"
            {...register('amount', { required: 'Amount required', min: 0 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="1000.00"
          />
          {errors.amount && (
            <p className="text-red-500 text-sm mt-1">{errors.amount.message}</p>
          )}
        </div>

        {/* Customer ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Customer ID
          </label>
          <input
            type="text"
            {...register('customer_id', { required: 'Customer ID required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="CUST-001"
          />
          {errors.customer_id && (
            <p className="text-red-500 text-sm mt-1">{errors.customer_id.message}</p>
          )}
        </div>

        {/* Idempotency Key (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Idempotency Key (Optional)
          </label>
          <input
            type="text"
            {...register('idempotency_key')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="Auto-generated if empty"
          />
        </div>

        {/* Error */}
        {createMutation.error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {(createMutation.error as any).response?.data?.detail || 'Failed to create decision'}
          </div>
        )}

        {/* Success */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
            <p className="font-medium">Decision created successfully!</p>
            <p className="text-sm mt-1">Decision ID: {success.decision_id}</p>
            <p className="text-sm">Outcome: <span className="font-medium">{success.outcome}</span></p>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {createMutation.isPending ? 'Creating...' : 'Create Decision'}
        </button>
      </form>
    </div>
  );
}
```

**Checklist:**
- [ ] Create `components/CreateDecisionForm.tsx`
- [ ] Add form fields (decision_type, amount, customer_id)
- [ ] Add validation
- [ ] Integrate with API
- [ ] Show success message with decision ID and outcome
- [ ] Show error messages
- [ ] Auto-generate idempotency_key if empty
- [ ] Test: Can create decision with valid data
- [ ] Test: Form validation works
- [ ] Git commit: "feat: create decision form (Phase A)"

---

##### A4.6: Decision List & Audit Trail
**Effort:** 4 hours
**Files:**
- Create `frontend/src/pages/DecisionsPage.tsx`
- Create `frontend/src/pages/AuditPage.tsx`

**File: `frontend/src/pages/DecisionsPage.tsx`**
```typescript
/**
 * Decisions List — Phase A
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { getUser } from '../lib/auth';
import { CreateDecisionForm } from '../components/CreateDecisionForm';

export function DecisionsPage() {
  const user = getUser();

  const { data: decisions, isLoading } = useQuery({
    queryKey: ['decisions', user?.tenant_id],
    queryFn: () => apiClient.getDecisions(user?.tenant_id!),
    enabled: !!user?.tenant_id,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Decisions</h1>

      {/* Create Form */}
      <CreateDecisionForm />

      {/* Decision List */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Recent Decisions</h2>

        {isLoading ? (
          <p className="text-gray-600">Loading...</p>
        ) : decisions && decisions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Decision ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Outcome
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Created At
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {decisions.map((decision: any) => (
                  <tr key={decision.decision_id}>
                    <td className="px-6 py-4 text-sm font-mono">
                      {decision.decision_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {decision.decision_type}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        decision.outcome === 'APPROVE' ? 'bg-green-100 text-green-800' :
                        decision.outcome === 'REJECT' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {decision.outcome}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(decision.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600">No decisions found.</p>
        )}
      </div>
    </div>
  );
}
```

**Checklist:**
- [ ] Create `pages/DecisionsPage.tsx`
- [ ] Include CreateDecisionForm
- [ ] Show decision list in table
- [ ] Color-code outcomes (APPROVE=green, REJECT=red, MANUAL_REVIEW=yellow)
- [ ] Format dates nicely
- [ ] Test: Can view decision list
- [ ] Test: New decision appears in list after creation
- [ ] Git commit: "feat: decision list page (Phase A)"

---

##### A4.7: Workflow Approval Inbox
**Effort:** 6 hours
**Files:**
- Create `frontend/src/pages/WorkflowsPage.tsx`
- Create `frontend/src/components/WorkflowActionModal.tsx`

**File: `frontend/src/pages/WorkflowsPage.tsx`**
```typescript
/**
 * Workflows Page — Phase A
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { getUser } from '../lib/auth';

export function WorkflowsPage() {
  const user = getUser();
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null);
  const [actionType, setActionType] = useState<'approve' | 'reject' | null>(null);
  const [comment, setComment] = useState('');
  const queryClient = useQueryClient();

  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows', user?.tenant_id, 'PENDING_APPROVAL'],
    queryFn: () => apiClient.getWorkflows(user?.tenant_id!, 'PENDING_APPROVAL'),
    enabled: !!user?.tenant_id,
  });

  const approveMutation = useMutation({
    mutationFn: ({ workflowId, data }: any) => apiClient.approveWorkflow(workflowId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      closeModal();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ workflowId, data }: any) => apiClient.rejectWorkflow(workflowId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      closeModal();
    },
  });

  const handleAction = () => {
    if (!selectedWorkflow || !actionType) return;

    const payload = {
      tenant_id: user?.tenant_id,
      comment: comment || undefined,
      trace_id: `trace-${Date.now()}`,
    };

    if (actionType === 'approve') {
      approveMutation.mutate({ workflowId: selectedWorkflow.workflow_id, data: payload });
    } else {
      rejectMutation.mutate({ workflowId: selectedWorkflow.workflow_id, data: payload });
    }
  };

  const closeModal = () => {
    setSelectedWorkflow(null);
    setActionType(null);
    setComment('');
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Approval Inbox</h1>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Pending Approvals</h2>

        {isLoading ? (
          <p className="text-gray-600">Loading...</p>
        ) : workflows && workflows.length > 0 ? (
          <div className="space-y-4">
            {workflows.map((workflow: any) => (
              <div key={workflow.workflow_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">Workflow ID: {workflow.workflow_id.substring(0, 8)}...</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Decision: {workflow.decision_id.substring(0, 8)}...
                    </p>
                    <p className="text-sm text-gray-600">
                      Approver Role: <span className="font-medium">{workflow.approver_role}</span>
                    </p>
                    <p className="text-sm text-gray-600">
                      Status: <span className="font-medium">{workflow.status}</span>
                    </p>
                  </div>

                  <div className="space-x-2">
                    <button
                      onClick={() => {
                        setSelectedWorkflow(workflow);
                        setActionType('approve');
                      }}
                      className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => {
                        setSelectedWorkflow(workflow);
                        setActionType('reject');
                      }}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No pending approvals.</p>
        )}
      </div>

      {/* Action Modal */}
      {selectedWorkflow && actionType && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">
              {actionType === 'approve' ? 'Approve' : 'Reject'} Workflow
            </h3>

            <p className="text-sm text-gray-600 mb-4">
              Workflow ID: {selectedWorkflow.workflow_id.substring(0, 8)}...
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Comment (Optional)
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={3}
                placeholder="Add a comment..."
              />
            </div>

            {(approveMutation.error || rejectMutation.error) && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
                Action failed. Please try again.
              </div>
            )}

            <div className="flex space-x-2">
              <button
                onClick={handleAction}
                disabled={approveMutation.isPending || rejectMutation.isPending}
                className={`flex-1 py-2 px-4 rounded text-white ${
                  actionType === 'approve'
                    ? 'bg-green-600 hover:bg-green-700'
                    : 'bg-red-600 hover:bg-red-700'
                } disabled:opacity-50`}
              >
                {approveMutation.isPending || rejectMutation.isPending
                  ? 'Processing...'
                  : `Confirm ${actionType === 'approve' ? 'Approval' : 'Rejection'}`}
              </button>
              <button
                onClick={closeModal}
                className="flex-1 py-2 px-4 rounded border border-gray-300 hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Checklist:**
- [ ] Create `pages/WorkflowsPage.tsx`
- [ ] Show pending approvals list
- [ ] Add approve/reject buttons
- [ ] Create action modal with comment field
- [ ] Integrate with API (approveWorkflow, rejectWorkflow)
- [ ] Show success/error messages
- [ ] Refresh list after action
- [ ] Test: Can approve workflow
- [ ] Test: Can reject workflow
- [ ] Test: Comment is sent to API
- [ ] Git commit: "feat: workflow approval inbox (Phase A)"

---

### 📊 PHASE A COMPLETION CHECKLIST

#### Security Foundation ✅
- [ ] All hardcoded credentials removed
- [ ] Centralized configuration with Pydantic Settings
- [ ] .env.example created
- [ ] JWT authentication implemented
- [ ] Login endpoint working
- [ ] Protected endpoints (all require auth)
- [ ] Tenant whitelist enforced
- [ ] Health endpoints added (/health, /ready)

#### Backend API ✅
- [ ] Decision creation endpoint protected
- [ ] Workflow approval endpoint protected
- [ ] User adapter (minimal) implemented
- [ ] Role→Approver resolution working
- [ ] Tenant isolation enforced in endpoints

#### Docker Infrastructure ✅
- [ ] Dockerfile created and tested
- [ ] docker-compose.yml created
- [ ] PostgreSQL service configured
- [ ] Backend service configured
- [ ] Health checks configured
- [ ] Can start with `docker-compose up -d`
- [ ] All services healthy

#### Frontend (Minimal) ✅
- [ ] React + Vite + TypeScript setup
- [ ] API client with auth interceptor
- [ ] Login page functional
- [ ] Dashboard page showing user info
- [ ] Create decision form working
- [ ] Decision list displaying
- [ ] Workflow approval inbox functional
- [ ] Phase A warning banner on all pages

#### End-to-End Flow ✅
- [ ] Can login with hardcoded credentials
- [ ] Can create decision (receives APPROVE/REJECT/MANUAL_REVIEW)
- [ ] MANUAL_REVIEW creates workflow
- [ ] Can see workflow in approval inbox
- [ ] Can approve workflow
- [ ] Can reject workflow
- [ ] Can see audit trail (decision list)
- [ ] No tenant leaks (cross-tenant requests blocked)

#### Documentation ✅
- [ ] Phase A implementation guide created
- [ ] Environment variables documented
- [ ] Test credentials documented
- [ ] Warning banners visible everywhere

---

## 🟡 PHASE B — DEPLOYED BUT NOT TRUSTED (VPS)

**Goal:** System online tapi dipagari keras dengan Cloudflare protection

**Timeline:** 1 week
**Environment:** Single VPS with Cloudflare

---

### 📋 TASK BREAKDOWN - PHASE B

#### B1. VPS SETUP (Priority 🔴 CRITICAL)

##### B1.1: VPS Provisioning
**Effort:** 2 hours
**Provider:** DigitalOcean / Hetzner / Linode

**Specs (Minimal):**
- **CPU:** 2 vCPU
- **RAM:** 4 GB
- **Storage:** 80 GB SSD
- **OS:** Ubuntu 22.04 LTS

**Initial Setup:**
```bash
# SSH as root
ssh root@YOUR_VPS_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Install other tools
apt install -y git curl nginx certbot python3-certbot-nginx

# Create non-root user
adduser atlas
usermod -aG sudo,docker atlas

# Setup SSH key authentication
mkdir -p /home/atlas/.ssh
cp /root/.ssh/authorized_keys /home/atlas/.ssh/
chown -R atlas:atlas /home/atlas/.ssh
chmod 700 /home/atlas/.ssh
chmod 600 /home/atlas/.ssh/authorized_keys

# Disable password authentication (security)
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Setup firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

**Checklist:**
- [ ] VPS provisioned
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Non-root user created
- [ ] SSH key authentication configured
- [ ] Firewall configured
- [ ] Can SSH as non-root user

---

##### B1.2: Deploy Application
**Effort:** 3 hours

**Steps:**
```bash
# SSH as atlas user
ssh atlas@YOUR_VPS_IP

# Clone repository
git clone https://github.com/YOUR_ORG/ARSAKA_PUGUH.git
cd ARSAKA_PUGUH

# Create .env from example
cd docker
cp .env.example .env

# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env (set secrets!)
nano .env

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Verify health
curl http://localhost:8001/health
```

**Checklist:**
- [ ] Repository cloned
- [ ] .env configured with production secrets
- [ ] JWT_SECRET_KEY generated (32+ chars)
- [ ] DB_PASSWORD set (strong password)
- [ ] Services started
- [ ] Health check returns 200
- [ ] Database migrations applied

---

##### B1.3: Domain & Cloudflare Setup
**Effort:** 2 hours

**DNS Configuration:**
```
# Add A record in Cloudflare
Type: A
Name: atlas-phase-a (or your subdomain)
Content: YOUR_VPS_IP
Proxy: Enabled (orange cloud) ✅
TTL: Auto
```

**Cloudflare Settings:**

**1. SSL/TLS:**
- Mode: **Full (strict)**
- Always Use HTTPS: **On**
- Minimum TLS Version: **TLS 1.2**

**2. Firewall Rules:**
```
Rule 1: Block all except allowed IPs
  - Field: IP Address
  - Operator: is not in
  - Value: YOUR_OFFICE_IP, YOUR_HOME_IP (whitelist)
  - Action: Block

Rule 2: Rate limiting
  - Field: Request Rate
  - Operator: greater than
  - Value: 100 requests per minute
  - Action: Challenge (CAPTCHA)

Rule 3: Block non-API paths
  - Field: URI Path
  - Operator: does not start with
  - Value: /api/, /health, /ready, /login
  - Action: Block
```

**3. Access (Zero Trust):**
```
Application:
  - Name: ARSAKA_PUGUH Phase A
  - Domain: atlas-phase-a.yourdomain.com
  - Policy:
    - Action: Allow
    - Include: Emails ending in @yourcompany.com
    - Require: One-time PIN (OTP) via email
```

**4. WAF (Web Application Firewall):**
- Enable Managed Ruleset: **OWASP ModSecurity Core Rule Set**
- Enable DDoS Protection
- Enable Bot Fight Mode

**Checklist:**
- [ ] Domain DNS configured in Cloudflare
- [ ] SSL/TLS Full (strict) enabled
- [ ] IP whitelist firewall rule created
- [ ] Rate limiting configured
- [ ] Cloudflare Access configured (optional but recommended)
- [ ] WAF rules enabled
- [ ] Can access https://atlas-phase-a.yourdomain.com/health from allowed IP

---

##### B1.4: Nginx Reverse Proxy
**Effort:** 2 hours

**File: `/etc/nginx/sites-available/atlas-phase-a`**
```nginx
# ARSAKA_PUGUH Phase A — Nginx Configuration

server {
    listen 80;
    server_name atlas-phase-a.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name atlas-phase-a.yourdomain.com;

    # SSL certificates (Cloudflare Origin Certificate)
    ssl_certificate /etc/ssl/cloudflare/cert.pem;
    ssl_certificate_key /etc/ssl/cloudflare/key.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    # Phase A warning header
    add_header X-Environment "NON-PRODUCTION" always;
    add_header X-Warning "DATA-MAY-BE-DELETED" always;

    # Rate limiting zone
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health endpoints
    location ~ ^/(health|ready)$ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        access_log off;
    }

    # Frontend (optional, if built)
    location / {
        root /var/www/atlas-frontend;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Block access to sensitive paths
    location ~ /\. {
        deny all;
    }

    # Access logs
    access_log /var/log/nginx/atlas-phase-a.access.log;
    error_log /var/log/nginx/atlas-phase-a.error.log warn;
}
```

**Setup:**
```bash
# Create Cloudflare Origin Certificate (in Cloudflare dashboard)
# SSL/TLS → Origin Server → Create Certificate
# Download cert.pem and key.pem

# Upload to VPS
mkdir -p /etc/ssl/cloudflare
nano /etc/ssl/cloudflare/cert.pem  # Paste certificate
nano /etc/ssl/cloudflare/key.pem   # Paste private key
chmod 600 /etc/ssl/cloudflare/*.pem

# Create nginx config
sudo nano /etc/nginx/sites-available/atlas-phase-a
# Paste config above

# Enable site
sudo ln -s /etc/nginx/sites-available/atlas-phase-a /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

**Checklist:**
- [ ] Cloudflare Origin Certificate generated
- [ ] Certificate files uploaded to VPS
- [ ] Nginx config created
- [ ] Site enabled
- [ ] Nginx reloaded
- [ ] HTTPS works at https://atlas-phase-a.yourdomain.com
- [ ] HTTP redirects to HTTPS
- [ ] Security headers present (check with curl -I)
- [ ] Rate limiting works

---

#### B2. SECURITY HARDENING (Priority 🔴 CRITICAL)

##### B2.1: Disable Public Registration
**Effort:** 1 hour

Already implemented in Phase A (no registration endpoint exists).

**Verification:**
```bash
# Try to find registration endpoint (should not exist)
curl https://atlas-phase-a.yourdomain.com/api/v1/register
# Should return 404

# Verify only login endpoint exists
curl -X POST https://atlas-phase-a.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
# Should return 401 (invalid credentials)
```

**Checklist:**
- [ ] No registration endpoint exists
- [ ] Only hardcoded users can login
- [ ] Documented: "User creation is manual only in Phase B"

---

##### B2.2: Strict Rate Limiting
**Effort:** 1 hour

Already configured in:
1. Backend config (30 req/min per tenant)
2. Nginx (10 req/s with burst 20)
3. Cloudflare (100 req/min global)

**Test:**
```bash
# Test rate limiting
for i in {1..50}; do
  curl https://atlas-phase-a.yourdomain.com/api/v1/auth/login
  sleep 0.1
done

# Should see 429 Too Many Requests after ~20 requests
```

**Checklist:**
- [ ] Backend rate limiting enabled (30 req/min)
- [ ] Nginx rate limiting enabled (10 req/s)
- [ ] Cloudflare rate limiting enabled (100 req/min)
- [ ] Rate limit headers returned (X-RateLimit-*)
- [ ] 429 response includes Retry-After header

---

##### B2.3: Monitoring & Alerts
**Effort:** 3 hours

**Simple Monitoring (Phase B):**

**File: `scripts/health_check.sh`**
```bash
#!/bin/bash
# Simple health check script
# Run via cron: */5 * * * * /home/atlas/ARSAKA_PUGUH/scripts/health_check.sh

API_URL="https://atlas-phase-a.yourdomain.com"
SLACK_WEBHOOK="YOUR_SLACK_WEBHOOK_URL"  # Optional

# Check health endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")

if [ "$response" != "200" ]; then
    echo "❌ ALERT: Health check failed (HTTP $response)"

    # Send to Slack (optional)
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"🚨 ARSAKA_PUGUH health check failed: HTTP $response\"}"
    fi

    # Send email (requires mailutils)
    echo "Health check failed at $(date)" | mail -s "ARSAKA_PUGUH Alert" admin@yourcompany.com
else
    echo "✅ Health check passed at $(date)"
fi

# Check disk space
disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 80 ]; then
    echo "⚠️  WARN: Disk usage is ${disk_usage}%"
fi

# Check memory
mem_usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$mem_usage" -gt 80 ]; then
    echo "⚠️  WARN: Memory usage is ${mem_usage}%"
fi
```

**Setup:**
```bash
# Make executable
chmod +x scripts/health_check.sh

# Add to crontab (every 5 minutes)
crontab -e
# Add line:
# */5 * * * * /home/atlas/ARSAKA_PUGUH/scripts/health_check.sh >> /home/atlas/health_check.log 2>&1
```

**Checklist:**
- [ ] Health check script created
- [ ] Cron job configured (every 5 minutes)
- [ ] Slack/email notifications configured (optional)
- [ ] Disk space monitoring enabled
- [ ] Memory monitoring enabled
- [ ] Log file exists and rotates

---

### 📊 PHASE B COMPLETION CHECKLIST

#### Infrastructure ✅
- [ ] VPS provisioned and configured
- [ ] Docker and Docker Compose installed
- [ ] Application deployed and running
- [ ] Domain configured in Cloudflare
- [ ] SSL/TLS Full (strict) enabled
- [ ] Nginx reverse proxy configured
- [ ] HTTPS working with valid certificate

#### Security Hardening ✅
- [ ] IP whitelist configured (Cloudflare firewall)
- [ ] Rate limiting at 3 layers (Backend, Nginx, Cloudflare)
- [ ] WAF rules enabled (OWASP ModSecurity)
- [ ] Cloudflare Access configured (optional)
- [ ] Security headers present (X-Frame-Options, CSP, etc.)
- [ ] Public registration disabled (no endpoint)
- [ ] Manual user creation only

#### Operational ✅
- [ ] Health check monitoring enabled
- [ ] Cron job running
- [ ] Alerts configured (Slack/email)
- [ ] Disk space monitoring
- [ ] Memory monitoring
- [ ] Logs accessible and rotating

#### Testing ✅
- [ ] Can access via HTTPS from allowed IP
- [ ] Cannot access from non-whitelisted IP (blocked by Cloudflare)
- [ ] Login works with hardcoded credentials
- [ ] Can create decision
- [ ] Can approve workflow
- [ ] Rate limiting triggers at 30 req/min
- [ ] Health endpoint returns 200
- [ ] Security headers present

---

## ⏳ PHASE C & D — FUTURE

**Phase C** (Controlled Multi-Tenant) dan **Phase D** (Hardening) akan dijabarkan setelah Phase A & B berhasil dan stabil.

**Focus now:** Execute Phase A completely, then deploy to Phase B environment.

---

## 🎯 SUCCESS CRITERIA (FINAL CHECKLIST)

### Phase A Success ✅
- [ ] **Login works** - Can authenticate with hardcoded users
- [ ] **Create decision works** - Receives APPROVE/REJECT/MANUAL_REVIEW outcome
- [ ] **Approve workflow works** - Can approve pending workflows
- [ ] **Audit trail visible** - Can see decision history
- [ ] **No tenant leak** - Cross-tenant requests blocked
- [ ] **No hardcoded secrets** - All secrets in .env
- [ ] **Can reset without trauma** - Docker down/up works

### Phase B Success ✅
- [ ] **Online and accessible** - HTTPS working from allowed IPs
- [ ] **Protected** - Non-whitelisted IPs blocked
- [ ] **Rate limited** - 30 req/min enforced
- [ ] **Monitored** - Health checks running every 5 minutes
- [ ] **Documented** - All IPs, credentials, and access procedures documented

---

## 📖 NEXT STEPS

1. **Execute Phase A locally** - Get visible system working
2. **Test end-to-end flow** - Login → Create → Approve → Audit
3. **Deploy to Phase B VPS** - Single server deployment
4. **Test security** - Verify IP whitelist, rate limiting, WAF
5. **Monitor for 1 week** - Ensure stability before Phase C

**Timeline Estimate:**
- **Phase A:** 2-3 weeks (development + testing)
- **Phase B:** 1 week (deployment + security hardening)
- **Total:** 3-4 weeks to visible, deployed, protected system

---

**END OF IMPLEMENTATION PLAN**

**Remember:** This is NOT production-ready. This is a visible, functional prototype with minimal security for internal testing.

**⚠️ ALWAYS DISPLAY:** NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED WITHOUT NOTICE
