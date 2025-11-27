# Multi-Tenant Implementation Guide - Part 3

## Testing Strategy

### Unit Tests

#### File: `/mnt/g/khoirul/signate/backend/tests/test_auth.py`

```python
"""
Unit tests for authentication endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User
from app.models.organization import Organization
from app.models.role import Role
from app.models.user_organization import UserOrganization

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_organization(test_db):
    """Create test organization"""
    db = TestingSessionLocal()

    org = Organization(
        name="Test Organization",
        slug="test-org",
        is_active=True
    )
    db.add(org)

    # Create system roles
    admin_role = Role(
        name="admin",
        display_name="Admin",
        is_system_role=True,
        permissions={"*": ["*"]}
    )
    viewer_role = Role(
        name="viewer",
        display_name="Viewer",
        is_system_role=True,
        permissions={"devices": ["read"], "content": ["read"]}
    )
    db.add_all([admin_role, viewer_role])
    db.commit()

    yield org, admin_role, viewer_role

    db.close()


@pytest.fixture
def test_user(test_db, test_organization):
    """Create test user"""
    db = TestingSessionLocal()
    org, admin_role, _ = test_organization

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("TestPassword123"),
        full_name="Test User",
        is_active=True,
        role="admin"
    )
    db.add(user)
    db.flush()

    # Link user to organization
    user_org = UserOrganization(
        user_id=user.id,
        organization_id=org.id,
        role_id=admin_role.id,
        is_primary=True,
        is_active=True
    )
    db.add(user_org)
    db.commit()

    yield user

    db.close()


def test_login_success(test_user, test_organization):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser"


def test_login_wrong_password(test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "WrongPassword"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user():
    """Test login with non-existent user"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "Password123"
        }
    )

    assert response.status_code == 401


def test_register_success(test_organization):
    """Test successful registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123",
            "full_name": "New User",
            "organization_name": "New Organization"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "newuser"
    assert data["organization"] is not None


def test_register_duplicate_username(test_user):
    """Test registration with duplicate username"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "Password123",
            "organization_name": "New Org"
        }
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_get_current_user(test_user):
    """Test getting current user info"""
    # Login first
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123"
        }
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "organizations" in data


def test_refresh_token(test_user):
    """Test token refresh"""
    # Login first
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout(test_user):
    """Test logout"""
    # Login first
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123"
        }
    )
    token = login_response.json()["access_token"]

    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert "logged out" in response.json()["message"]
```

#### File: `/mnt/g/khoirul/signate/backend/tests/test_organizations.py`

```python
"""
Unit tests for organization endpoints
"""

import pytest
from fastapi.testclient import TestClient

from tests.test_auth import client, test_db, test_user, test_organization


def get_auth_headers(test_user):
    """Helper to get authentication headers"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_organizations(test_user, test_organization):
    """Test listing organizations"""
    headers = get_auth_headers(test_user)

    response = client.get(
        "/api/v1/organizations/",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == "Test Organization"


def test_create_organization(test_user):
    """Test creating organization"""
    headers = get_auth_headers(test_user)

    response = client.post(
        "/api/v1/organizations/",
        headers=headers,
        json={
            "name": "New Organization",
            "slug": "new-org",
            "description": "Test organization",
            "max_devices": 20,
            "max_users": 10
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Organization"
    assert data["slug"] == "new-org"


def test_get_organization(test_user, test_organization):
    """Test getting organization details"""
    headers = get_auth_headers(test_user)
    org, _, _ = test_organization

    response = client.get(
        f"/api/v1/organizations/{org.id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Organization"
    assert "device_count" in data
    assert "user_count" in data


def test_update_organization(test_user, test_organization):
    """Test updating organization"""
    headers = get_auth_headers(test_user)
    org, _, _ = test_organization

    response = client.put(
        f"/api/v1/organizations/{org.id}",
        headers=headers,
        json={
            "name": "Updated Organization",
            "max_devices": 50
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Organization"
    assert data["max_devices"] == 50


def test_invite_user(test_user, test_organization):
    """Test inviting user to organization"""
    headers = get_auth_headers(test_user)
    org, _, _ = test_organization

    response = client.post(
        f"/api/v1/organizations/{org.id}/invite",
        headers=headers,
        json={
            "email": "invited@example.com",
            "role_name": "viewer"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "invited@example.com"
    assert "invitation_token" in data
```

### Integration Tests

#### File: `/mnt/g/khoirul/signate/backend/tests/test_integration.py`

```python
"""
Integration tests for multi-tenant flows
"""

import pytest
from fastapi.testclient import TestClient

from tests.test_auth import client, test_db, test_organization


def test_full_user_flow(test_organization):
    """Test complete user flow: register -> login -> create device -> logout"""

    # 1. Register new user with new organization
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "IntegrationTest123",
            "full_name": "Integration User",
            "organization_name": "Integration Org"
        }
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get current user info
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert len(user_data["organizations"]) == 1

    # 3. Create a device
    device_response = client.post(
        "/api/devices",
        headers=headers,
        json={
            "device_name": "Test Device",
            "device_type": "monitor"
        }
    )
    assert device_response.status_code == 201
    device_id = device_response.json()["id"]

    # 4. List devices (should see only org's devices)
    devices_response = client.get("/api/devices", headers=headers)
    assert devices_response.status_code == 200
    devices = devices_response.json()
    assert len(devices) == 1
    assert devices[0]["id"] == device_id

    # 5. Logout
    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    # 6. Verify token no longer works
    verify_response = client.get("/api/v1/auth/me", headers=headers)
    assert verify_response.status_code == 401


def test_multi_org_user_flow(test_organization):
    """Test user in multiple organizations"""

    # 1. Create first organization and user
    register1 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "multiorguser",
            "email": "multiorg@example.com",
            "password": "MultiOrg123",
            "organization_name": "Org One"
        }
    )
    token1 = register1.json()["access_token"]
    org1_id = register1.json()["organization"]["id"]

    # 2. Create second organization
    org2_response = client.post(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "name": "Org Two",
            "slug": "org-two",
            "max_devices": 10,
            "max_users": 5
        }
    )
    org2_id = org2_response.json()["id"]

    # 3. Switch to second organization
    switch_response = client.post(
        "/api/v1/auth/change-organization",
        headers={"Authorization": f"Bearer {token1}"},
        json={"organization_id": org2_id}
    )
    assert switch_response.status_code == 200
    token2 = switch_response.json()["access_token"]

    # 4. Create device in org2
    device_response = client.post(
        "/api/devices",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "device_name": "Org2 Device",
            "device_type": "tv"
        }
    )
    assert device_response.status_code == 201

    # 5. Switch back to org1
    switch_back = client.post(
        "/api/v1/auth/change-organization",
        headers={"Authorization": f"Bearer {token2}"},
        json={"organization_id": org1_id}
    )
    token3 = switch_back.json()["access_token"]

    # 6. Verify org2 device is not visible in org1
    devices = client.get(
        "/api/devices",
        headers={"Authorization": f"Bearer {token3}"}
    )
    assert len(devices.json()) == 0  # Should see no devices in org1
```

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov faker

# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=app --cov-report=html

# Run specific test file
pytest backend/tests/test_auth.py -v

# Run specific test
pytest backend/tests/test_auth.py::test_login_success -v
```

---

## Deployment Guide

### Step 1: Update Dependencies on Server

```bash
# SSH to server
ssh gzjbbk@192.168.5.12

# Navigate to project
cd /home/gzjbbk/signate/backend

# Update requirements.txt (copy from local)
# Then install
pip install -r requirements.txt

# Or install individual new packages
pip install python-slugify aiosmtplib jinja2
```

### Step 2: Run Database Migration

```bash
# On server, navigate to backend directory
cd /home/gzjbbk/signage/backend

# Run migration script
python scripts/run_migration.py

# Or run migration manually
psql -h localhost -p 5433 -U signage_user -d signage_db -f migrations/006_add_multi_tenancy.sql
```

### Step 3: Create Default Admin User

#### File: `/mnt/g/khoirul/signate/backend/scripts/create_admin.py`

```python
"""
Create default admin user
Run this once after migration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.user_organization import UserOrganization
from app.models.role import Role
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_default_admin():
    """Create default admin user if not exists"""
    db = SessionLocal()

    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(
            User.username == settings.DEFAULT_ADMIN_USERNAME
        ).first()

        if admin_user:
            logger.info("Admin user already exists")
            return

        # Get default organization
        default_org = db.query(Organization).filter(
            Organization.slug == 'default'
        ).first()

        if not default_org:
            logger.error("Default organization not found. Run migration first.")
            return

        # Get admin role
        admin_role = db.query(Role).filter(
            Role.name == 'admin',
            Role.is_system_role == True
        ).first()

        if not admin_role:
            logger.error("Admin role not found. Run migration first.")
            return

        # Create admin user
        admin_user = User(
            username=settings.DEFAULT_ADMIN_USERNAME,
            email=settings.DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            full_name="System Administrator",
            role='admin',
            is_active=True,
            is_super_admin=True,
            email_verified=True
        )
        db.add(admin_user)
        db.flush()

        # Link to default organization
        user_org = UserOrganization(
            user_id=admin_user.id,
            organization_id=default_org.id,
            role_id=admin_role.id,
            is_primary=True,
            is_active=True
        )
        db.add(user_org)
        db.commit()

        logger.info(f"Admin user created successfully!")
        logger.info(f"Username: {settings.DEFAULT_ADMIN_USERNAME}")
        logger.info(f"Email: {settings.DEFAULT_ADMIN_EMAIL}")
        logger.info(f"Password: {settings.DEFAULT_ADMIN_PASSWORD}")
        logger.info("IMPORTANT: Change the password after first login!")

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_default_admin()
```

Run on server:

```bash
python scripts/create_admin.py
```

### Step 4: Update Environment Variables on Server

Edit `/home/gzjbbk/signage/backend/.env`:

```bash
# Add new multi-tenancy settings
JWT_SECRET=your_production_secret_min_32_chars_change_this
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@signage.com
FRONTEND_URL=http://192.168.5.12:3000

DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@signage.com
DEFAULT_ADMIN_PASSWORD=ChangeMe@2024
```

### Step 5: Rebuild and Restart Docker Container

```bash
# On server
cd /home/gzjbbk/signage

# Rebuild backend container
docker-compose build backend-api

# Restart services
docker-compose up -d

# Check logs
docker-compose logs -f backend-api
```

### Step 6: Verify Deployment

```bash
# Check API is running
curl http://192.168.5.12:8001/health

# Check database tables
psql -h localhost -p 5433 -U signage_user -d signage_db -c "\dt"

# Should see new tables:
# - organizations
# - roles
# - user_organizations
# - user_sessions
# - audit_logs

# Test admin login
curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ChangeMe@2024"}'
```

---

## Security Best Practices

### 1. Password Requirements

Enforce strong passwords in your schemas:

```python
@field_validator('password')
@classmethod
def validate_password_strength(cls, v: str) -> str:
    """Validate password strength"""
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters')
    if not any(c.isupper() for c in v):
        raise ValueError('Password must contain uppercase letter')
    if not any(c.islower() for c in v):
        raise ValueError('Password must contain lowercase letter')
    if not any(c.isdigit() for c in v):
        raise ValueError('Password must contain digit')
    if not any(c in '!@#$%^&*()_+-=' for c in v):
        raise ValueError('Password must contain special character')
    return v
```

### 2. Rate Limiting

#### File: `/mnt/g/khoirul/signate/backend/app/middleware/rate_limit.py`

```python
"""
Rate limiting middleware
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from typing import Dict, Tuple
from collections import defaultdict
import asyncio


class RateLimiter:
    """
    Rate limiter using token bucket algorithm
    """

    def __init__(self, max_requests: int = 60, window: int = 60):
        """
        Args:
            max_requests: Maximum requests allowed
            window: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed

        Returns:
            (is_allowed, retry_after)
        """
        now = time.time()

        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.window
        ]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            oldest = min(self.requests[key])
            retry_after = int(self.window - (now - oldest))
            return False, retry_after

        # Allow request
        self.requests[key].append(now)
        return True, 0


# Global rate limiters
auth_limiter = RateLimiter(max_requests=5, window=60)  # 5 login attempts per minute
api_limiter = RateLimiter(max_requests=100, window=60)  # 100 API calls per minute


async def rate_limit_auth(request: Request):
    """Rate limit authentication endpoints"""
    client_ip = request.client.host if request.client else "unknown"

    is_allowed, retry_after = auth_limiter.is_allowed(client_ip)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


async def rate_limit_api(request: Request):
    """Rate limit API endpoints"""
    # Get user ID from token if authenticated, otherwise use IP
    client_id = request.client.host if request.client else "unknown"

    is_allowed, retry_after = api_limiter.is_allowed(client_id)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
```

Use in endpoints:

```python
@router.post("/login")
async def login(
    request: Request,
    login_data: LoginRequest,
    rate_limit: None = Depends(rate_limit_auth),  # Add rate limiting
    db: Session = Depends(get_db)
):
    # ... login logic
```

### 3. SQL Injection Prevention

SQLAlchemy ORM prevents SQL injection by default. However, if using raw SQL:

```python
# BAD - Vulnerable to SQL injection
query = f"SELECT * FROM users WHERE username = '{username}'"
db.execute(query)

# GOOD - Use parameterized queries
from sqlalchemy import text
query = text("SELECT * FROM users WHERE username = :username")
db.execute(query, {"username": username})
```

### 4. XSS Prevention

Sanitize user input in schemas:

```python
from pydantic import field_validator
import bleach

@field_validator('description')
@classmethod
def sanitize_html(cls, v: str) -> str:
    """Sanitize HTML to prevent XSS"""
    if v:
        return bleach.clean(v, tags=['b', 'i', 'u', 'p'], strip=True)
    return v
```

### 5. CORS Configuration

In production, restrict CORS to specific domains:

```python
# .env
CORS_ORIGINS=http://192.168.5.12:3000,http://192.168.5.12:8080

# In config.py - parse as list
CORS_ORIGINS: List[str] = [
    "http://192.168.5.12:3000",  # Web Admin
    "http://192.168.5.12:8080",  # Viewer
]
```

### 6. Session Management

Clean up expired sessions periodically:

#### File: `/mnt/g/khoirul/signate/backend/app/utils/session_cleanup.py`

```python
"""
Session cleanup utility
"""

from sqlalchemy.orm import Session
from datetime import datetime
from app.models.user_session import UserSession
import logging

logger = logging.getLogger(__name__)


def cleanup_expired_sessions(db: Session) -> int:
    """
    Remove expired sessions from database

    Returns:
        Number of sessions deleted
    """
    try:
        deleted = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()

        db.commit()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired sessions")

        return deleted

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        db.rollback()
        return 0
```

Add to main.py startup:

```python
import asyncio
from app.utils.session_cleanup import cleanup_expired_sessions

async def periodic_session_cleanup():
    """Background task to cleanup expired sessions"""
    while True:
        await asyncio.sleep(3600)  # Every hour

        db = SessionLocal()
        try:
            cleanup_expired_sessions(db)
        finally:
            db.close()

@app.on_event("startup")
async def startup_event():
    # ... existing startup code

    # Start session cleanup task
    asyncio.create_task(periodic_session_cleanup())
```

---

## Performance Optimization

### 1. Database Indexing

Ensure all foreign keys and frequently queried fields are indexed (already in migration):

```sql
CREATE INDEX idx_devices_org ON devices(organization_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_user_orgs_user ON user_organizations(user_id);
CREATE INDEX idx_user_orgs_org ON user_organizations(organization_id);
```

### 2. Query Optimization

Use `joinedload` to prevent N+1 queries:

```python
from sqlalchemy.orm import joinedload

# Instead of this (causes N+1 queries)
users = db.query(User).all()
for user in users:
    print(user.organizations)  # Each triggers a query

# Do this (single query with join)
users = db.query(User).options(
    joinedload(User.organizations).joinedload(UserOrganization.role)
).all()
```

### 3. Caching

Use Redis for frequently accessed data:

```python
import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL)


def get_organization_cached(org_id: int, db: Session):
    """Get organization with caching"""
    cache_key = f"org:{org_id}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return Organization(**json.loads(cached))

    # Query database
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org:
        # Cache for 5 minutes
        redis_client.setex(
            cache_key,
            300,
            json.dumps(org.to_dict())
        )

    return org
```

### 4. Pagination

Always use pagination for list endpoints:

```python
@router.get("/devices")
def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),  # Max 100 per page
    db: Session = Depends(get_db)
):
    total = db.query(Device).count()
    devices = db.query(Device).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": devices
    }
```

---

## Frontend Integration Example

### React Hook for Authentication

```typescript
// hooks/useAuth.ts
import { useState, useEffect } from 'react';
import axios from 'axios';

interface User {
  id: number;
  username: string;
  email: string;
  organizations: Organization[];
}

interface Organization {
  organization_id: number;
  organization_name: string;
  organization_slug: string;
  role_name: string;
  is_primary: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('access_token')
  );

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get('http://192.168.5.12:8001/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string, organizationSlug?: string) => {
    const response = await axios.post('http://192.168.5.12:8001/api/v1/auth/login', {
      username,
      password,
      organization_slug: organizationSlug
    });

    const { access_token, refresh_token, user } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    setToken(access_token);
    setUser(user);

    return user;
  };

  const register = async (data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    organization_name?: string;
    invitation_token?: string;
  }) => {
    const response = await axios.post('http://192.168.5.12:8001/api/v1/auth/register', data);

    const { access_token, refresh_token, user } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    setToken(access_token);
    setUser(user);

    return user;
  };

  const logout = async () => {
    try {
      await axios.post('http://192.168.5.12:8001/api/v1/auth/logout', null, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
      setUser(null);
    }
  };

  const changeOrganization = async (organizationId: number) => {
    const response = await axios.post(
      'http://192.168.5.12:8001/api/v1/auth/change-organization',
      { organization_id: organizationId },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    const { access_token, refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    setToken(access_token);

    await fetchCurrentUser();
  };

  return {
    user,
    loading,
    login,
    register,
    logout,
    changeOrganization,
    isAuthenticated: !!user
  };
}
```

---

## Monitoring and Observability

### Health Check Endpoint

Update `/health` to check all services:

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Enhanced health check"""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health["services"]["database"] = "healthy"
    except Exception as e:
        health["status"] = "unhealthy"
        health["services"]["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        redis_client.ping()
        health["services"]["redis"] = "healthy"
    except Exception as e:
        health["services"]["redis"] = f"unhealthy: {str(e)}"

    return health
```

---

## Summary Checklist

### Before Deployment

- [ ] Run migration: `006_add_multi_tenancy.sql`
- [ ] Create default admin user
- [ ] Update `.env` with all new variables
- [ ] Install new dependencies
- [ ] Run tests
- [ ] Update CORS configuration for production
- [ ] Change default JWT secret
- [ ] Set up SMTP for email notifications

### After Deployment

- [ ] Verify API health check
- [ ] Test admin login
- [ ] Create test organization
- [ ] Test device creation with organization context
- [ ] Verify data isolation between organizations
- [ ] Monitor logs for errors
- [ ] Set up monitoring/alerting

### Security

- [ ] Strong JWT secret (32+ chars)
- [ ] HTTPS in production
- [ ] Rate limiting enabled
- [ ] CORS restricted to specific domains
- [ ] Password requirements enforced
- [ ] Session expiry configured
- [ ] Regular security audits

---

## Troubleshooting

### Issue: Migration Fails

```bash
# Check current database structure
psql -h localhost -p 5433 -U signage_user -d signage_db -c "\d users"

# Rollback if needed
psql -h localhost -p 5433 -U signage_user -d signage_db -f migrations/006_rollback_multi_tenancy.sql
```

### Issue: Token Validation Fails

Check:
1. JWT_SECRET matches in .env
2. Token not expired
3. Session exists in database
4. User is active

### Issue: Permission Denied

Check:
1. User has correct role in organization
2. Role has required permissions in `permissions` JSON
3. Organization context is correct

---

## Next Steps

1. **Email Service**: Implement actual email sending for invitations and password reset
2. **Audit Dashboard**: Create UI to view audit logs
3. **Organization Settings**: Add custom branding, logos, etc.
4. **Billing Integration**: Add subscription management
5. **API Versioning**: Add v2 endpoints as needed
6. **WebSocket Auth**: Add organization context to WebSocket connections
7. **Analytics**: Add organization-level analytics and reporting

---

**Implementation Complete!**

This multi-tenant system provides:
- Secure authentication with JWT
- Organization isolation
- Role-based permissions
- Session management
- Audit logging
- Production-ready security
- Comprehensive testing

For questions or issues, refer to:
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Your existing codebase at `/mnt/g/khoirul/signate/backend/`
