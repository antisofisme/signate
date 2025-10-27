# Multi-Tenant Quick Start Guide

## Overview

This is a comprehensive multi-tenant user management system for your FastAPI Smart TV Digital Signage backend.

## Documentation Structure

1. **Part 1**: Database Models & Schemas (`MULTI_TENANT_IMPLEMENTATION_GUIDE.md`)
2. **Part 2**: API Endpoints & Integration (`MULTI_TENANT_IMPLEMENTATION_GUIDE_PART2.md`)
3. **Part 3**: Testing, Deployment & Security (`MULTI_TENANT_IMPLEMENTATION_GUIDE_PART3.md`)

---

## Quick Installation (30 minutes)

### Step 1: Install Dependencies (5 min)

```bash
cd /mnt/g/khoirul/signate/backend

# Add to requirements.txt
echo "python-slugify==8.0.1" >> requirements.txt
echo "aiosmtplib==3.0.1" >> requirements.txt
echo "jinja2==3.1.2" >> requirements.txt

# Install
pip install -r requirements.txt
```

### Step 2: Create New Model Files (10 min)

Create these files with code from Part 1:

```bash
# Models
backend/app/models/organization.py
backend/app/models/role.py
backend/app/models/user_organization.py
backend/app/models/user_session.py
backend/app/models/audit_log.py

# Schemas
backend/app/schemas/organization.py
backend/app/schemas/role.py

# API Endpoints
backend/app/api/organizations.py
backend/app/api/users.py

# Utilities
backend/app/utils/audit.py
backend/app/utils/session_cleanup.py
backend/app/middleware/rate_limit.py

# Scripts
backend/scripts/run_migration.py
backend/scripts/create_admin.py
```

### Step 3: Update Existing Files (5 min)

Update these files with changes from the guide:

- `backend/app/models/__init__.py` - Add new model imports
- `backend/app/models/user.py` - Add new fields
- `backend/app/models/device.py` - Add organization_id
- `backend/app/core/deps.py` - Replace with new version
- `backend/app/core/security/jwt.py` - Replace with enhanced version
- `backend/app/main.py` - Add new router imports
- `backend/app/core/config.py` - Add new settings

### Step 4: Update .env File (2 min)

```bash
# Add these to .env
JWT_SECRET=your_super_secret_min_32_chars_change_in_production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FRONTEND_URL=http://localhost:3000
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@signage.com
DEFAULT_ADMIN_PASSWORD=Admin@123456
```

### Step 5: Run Migration (3 min)

```bash
# The migration file already exists at:
# backend/migrations/006_add_multi_tenancy.sql

# Run it:
cd /mnt/g/khoirul/signate/backend
python scripts/run_migration.py

# Or manually:
psql -h localhost -p 5433 -U signage_user -d signage_db -f migrations/006_add_multi_tenancy.sql
```

### Step 6: Create Admin User (2 min)

```bash
python scripts/create_admin.py
```

### Step 7: Test Locally (3 min)

```bash
# Start backend
uvicorn app.main:app --reload --port 8001

# Test endpoints
curl http://localhost:8001/health

# Test login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123456"}'
```

---

## Deployment to Server (15 minutes)

### Step 1: Sync Files to Server (5 min)

```bash
# From local machine
cd /mnt/g/khoirul/signate

# Sync all changes
sshpass -p 'Password@2021' rsync -avz --exclude 'venv' --exclude '__pycache__' \
  backend/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/backend/
```

### Step 2: Install Dependencies on Server (3 min)

```bash
# SSH to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

cd /home/gzjbbk/signage/backend

# Install in Docker container
docker-compose exec backend-api pip install python-slugify aiosmtplib jinja2

# Or rebuild container
cd /home/gzjbbk/signage
docker-compose build backend-api
```

### Step 3: Run Migration on Server (3 min)

```bash
# On server
cd /home/gzjbbk/signage/backend

# Inside container
docker-compose exec backend-api python scripts/run_migration.py

# Or directly with psql
docker-compose exec postgres psql -U signage_user -d signage_db \
  -f /app/migrations/006_add_multi_tenancy.sql
```

### Step 4: Create Admin on Server (2 min)

```bash
docker-compose exec backend-api python scripts/create_admin.py
```

### Step 5: Restart Services (2 min)

```bash
cd /home/gzjbbk/signage
docker-compose restart backend-api

# Check logs
docker-compose logs -f backend-api
```

---

## API Endpoints Reference

### Authentication

```bash
POST /api/v1/auth/login              # Login
POST /api/v1/auth/register           # Register
POST /api/v1/auth/refresh            # Refresh token
POST /api/v1/auth/logout             # Logout
GET  /api/v1/auth/me                 # Get current user
POST /api/v1/auth/change-organization # Switch org
POST /api/v1/auth/forgot-password    # Request password reset
POST /api/v1/auth/reset-password     # Reset password
POST /api/v1/auth/verify-email       # Verify email
```

### Organizations

```bash
GET    /api/v1/organizations/             # List user's orgs
POST   /api/v1/organizations/             # Create org
GET    /api/v1/organizations/{id}         # Get org details
PUT    /api/v1/organizations/{id}         # Update org
DELETE /api/v1/organizations/{id}         # Delete org
GET    /api/v1/organizations/{id}/users   # List org users
POST   /api/v1/organizations/{id}/invite  # Invite user
```

### Users

```bash
GET    /api/v1/users/              # List users in org
POST   /api/v1/users/              # Create user
GET    /api/v1/users/{id}          # Get user details
PUT    /api/v1/users/{id}          # Update user
DELETE /api/v1/users/{id}          # Delete user
PUT    /api/v1/users/{id}/role     # Update user role
```

### Existing Endpoints (Now Organization-Scoped)

All these now filter by organization automatically:

```bash
GET/POST    /api/devices           # Devices
GET/POST    /api/content           # Content
GET/POST    /api/playlists         # Playlists
GET/POST    /api/tags              # Tags
```

---

## Database Schema

### New Tables

```
organizations          - Multi-tenant organizations
roles                  - RBAC roles
user_organizations     - User membership in orgs
user_sessions          - Session tracking
audit_logs            - Audit trail
```

### Updated Tables

All existing tables now have:
- `organization_id` (FK to organizations)
- `created_by` (FK to users)

### System Roles

Created automatically by migration:

- **super_admin** - Full system access
- **admin** - Organization admin
- **editor** - Content editor
- **viewer** - Read-only access

---

## Permission System

### Checking Permissions in Endpoints

```python
from app.core.deps import require_permission

@router.get("/devices")
def list_devices(
    current_user: User = Depends(require_permission("devices", "read")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    # User must have "devices.read" permission
    # Automatically filters by organization
    devices = db.query(Device).filter(
        Device.organization_id == organization.id
    ).all()
    return devices
```

### Permission Matrix

Stored in `roles.permissions` as JSON:

```json
{
  "devices": ["read", "create", "update", "delete"],
  "content": ["read", "create", "update", "delete"],
  "playlists": ["read", "create"],
  "users": ["read"]
}
```

---

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov faker

# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=app --cov-report=html
```

### Manual Testing Workflow

```bash
# 1. Register new user with new organization
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test@123456",
    "full_name": "Test User",
    "organization_name": "Test Org"
  }'

# 2. Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test@123456"}'

# 3. Get current user (use token from login)
curl -X GET http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Create device (scoped to organization)
curl -X POST http://localhost:8001/api/devices \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_name":"Test Device","device_type":"monitor"}'

# 5. List devices (only sees organization's devices)
curl -X GET http://localhost:8001/api/devices \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Common Issues & Solutions

### Issue: "Organization not found"

**Solution**: Ensure JWT token includes organization context. Switch organization:

```bash
curl -X POST http://localhost:8001/api/v1/auth/change-organization \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"organization_id": 1}'
```

### Issue: "Permission denied"

**Solution**: Check user's role and permissions:

```sql
SELECT u.username, r.name, r.permissions
FROM users u
JOIN user_organizations uo ON u.id = uo.user_id
JOIN roles r ON uo.role_id = r.id
WHERE u.id = YOUR_USER_ID;
```

### Issue: Migration fails

**Solution**: Check if tables already exist:

```sql
\dt  -- List all tables

-- If exists, drop and re-run (CAUTION: deletes data)
DROP TABLE IF EXISTS organizations CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
-- etc.
```

### Issue: "Token expired"

**Solution**: Use refresh token:

```bash
curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

---

## Security Checklist

- [ ] Change default JWT_SECRET in production
- [ ] Use HTTPS in production
- [ ] Restrict CORS to specific domains
- [ ] Enable rate limiting
- [ ] Change default admin password
- [ ] Set up email service for password reset
- [ ] Regular session cleanup
- [ ] Monitor audit logs
- [ ] Keep dependencies updated

---

## Performance Tips

1. **Use Indexes**: Already added in migration
2. **Enable Caching**: Use Redis for organizations, roles
3. **Pagination**: Always use skip/limit parameters
4. **Query Optimization**: Use joinedload for relationships
5. **Connection Pooling**: Already configured in SQLAlchemy

---

## Monitoring

### Health Check

```bash
curl http://192.168.5.12:8001/health
```

### Check Database Tables

```bash
docker-compose exec postgres psql -U signage_user -d signage_db -c "\dt"
```

### View Audit Logs

```sql
SELECT
  u.username,
  al.action,
  al.resource_type,
  al.resource_id,
  al.created_at
FROM audit_logs al
JOIN users u ON al.user_id = u.id
ORDER BY al.created_at DESC
LIMIT 20;
```

### Active Sessions

```sql
SELECT
  u.username,
  us.ip_address,
  us.created_at,
  us.last_activity
FROM user_sessions us
JOIN users u ON us.user_id = u.id
WHERE us.is_active = true
ORDER BY us.last_activity DESC;
```

---

## Frontend Integration

### Example Login Component (React)

```typescript
import { useState } from 'react';
import axios from 'axios';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const response = await axios.post('http://192.168.5.12:8001/api/v1/auth/login', {
        username,
        password
      });

      const { access_token, refresh_token, user, organization } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // Store user info
      console.log('Logged in as:', user.username);
      console.log('Organization:', organization.name);

      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      alert('Login failed');
    }
  };

  return (
    <div>
      <input value={username} onChange={(e) => setUsername(e.target.value)} />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}
```

### Axios Interceptor for Auto-Authentication

```typescript
import axios from 'axios';

// Add token to all requests
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken
          });
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token);

          // Retry original request
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
          return axios.request(error.config);
        } catch (refreshError) {
          // Refresh failed, logout
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
```

---

## Next Steps

### Phase 1: Core Implementation (Done)
- [x] Database models
- [x] Authentication endpoints
- [x] Organization management
- [x] Permission system

### Phase 2: Enhancement (Optional)
- [ ] Email service integration
- [ ] Custom roles per organization
- [ ] Organization branding/settings
- [ ] User profile management
- [ ] Activity dashboard

### Phase 3: Advanced Features (Future)
- [ ] SSO integration (OAuth2, SAML)
- [ ] Two-factor authentication
- [ ] API rate limiting per organization
- [ ] Usage analytics
- [ ] Billing/subscription management

---

## Support

For issues or questions:

1. Check the detailed guides (Part 1, 2, 3)
2. Review FastAPI docs: https://fastapi.tiangolo.com/
3. Check SQLAlchemy docs: https://docs.sqlalchemy.org/
4. Review your existing codebase

---

## File Locations

```
/mnt/g/khoirul/signate/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py (UPDATED)
│   │   │   ├── organizations.py (NEW)
│   │   │   ├── users.py (NEW)
│   │   │   └── devices.py (UPDATE organization filtering)
│   │   ├── core/
│   │   │   ├── deps.py (UPDATED)
│   │   │   ├── config.py (UPDATED)
│   │   │   └── security/
│   │   │       └── jwt.py (UPDATED)
│   │   ├── models/
│   │   │   ├── organization.py (NEW)
│   │   │   ├── role.py (NEW)
│   │   │   ├── user_organization.py (NEW)
│   │   │   ├── user_session.py (NEW)
│   │   │   ├── audit_log.py (NEW)
│   │   │   └── user.py (UPDATED)
│   │   ├── schemas/
│   │   │   ├── organization.py (NEW)
│   │   │   ├── role.py (NEW)
│   │   │   └── user.py (UPDATED)
│   │   └── utils/
│   │       ├── audit.py (NEW)
│   │       └── session_cleanup.py (NEW)
│   ├── migrations/
│   │   └── 006_add_multi_tenancy.sql (EXISTS)
│   ├── scripts/
│   │   ├── run_migration.py (NEW)
│   │   └── create_admin.py (NEW)
│   └── tests/
│       ├── test_auth.py (NEW)
│       └── test_organizations.py (NEW)
└── docs/
    ├── MULTI_TENANT_IMPLEMENTATION_GUIDE.md
    ├── MULTI_TENANT_IMPLEMENTATION_GUIDE_PART2.md
    ├── MULTI_TENANT_IMPLEMENTATION_GUIDE_PART3.md
    └── MULTI_TENANT_QUICK_START.md (THIS FILE)
```

---

**Happy Coding!** 🚀
