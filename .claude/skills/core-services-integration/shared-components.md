# Shared Components Reference

Complete reference for all shared utilities in the backend and frontend.

## Backend Shared Components

### Location: `backend-python/shared/`

```
shared/
├── __init__.py
├── auth.py           # Authentication & Authorization
├── cache.py          # Redis caching
├── config.py         # Configuration settings
├── database.py       # Database connection
├── errors.py         # Error handling
├── middleware.py     # Request middleware
└── validators.py     # Input validation
```

---

## shared/auth.py - Authentication & Authorization

### Functions

#### `get_current_user`
```python
from shared.auth import get_current_user

@router.get("/items")
async def get_items(current_user: dict = Depends(get_current_user)):
    """
    Returns dict with:
    - sub: str (user ID)
    - username: str
    - role: str (SUPER_ADMIN, ADMIN, MANAGER, VIEWER)
    - organization_id: int
    - permissions: List[str] (optional)
    """
    user_id = int(current_user["sub"])
    org_id = current_user["organization_id"]
```

#### `require_permission`
```python
from shared.auth import require_permission

@router.delete("/items/{id}")
async def delete_item(
    id: int,
    current_user: dict = Depends(require_permission("items.delete"))
):
    """Requires user to have specific permission"""
    pass
```

#### `verify_password` / `hash_password`
```python
from shared.auth import verify_password, hash_password

# Hash password
hashed = hash_password("plain_password")

# Verify password
is_valid = verify_password("plain_password", hashed)
```

#### `create_access_token`
```python
from shared.auth import create_access_token

token = create_access_token(data={
    "sub": str(user.id),
    "username": user.username,
    "role": user.role,
    "organization_id": user.organization_id
})
```

### Classes

#### `PermissionChecker`
```python
from shared.auth import PermissionChecker

checker = PermissionChecker(
    role=current_user["role"],
    permissions=current_user.get("permissions", [])
)

# Check capabilities
if checker.is_super_admin():
    # Full access
    pass

if checker.can_manage_users():
    # Can create/edit users
    pass

if checker.has_permission("devices.delete"):
    # Has specific permission
    pass

# Role hierarchy
# SUPER_ADMIN > ADMIN > MANAGER > VIEWER
if checker.is_at_least("MANAGER"):
    # MANAGER, ADMIN, or SUPER_ADMIN
    pass
```

---

## shared/validators.py - Input Validation

### Security Validators

#### `sanitize_input` - XSS Prevention
```python
from shared.validators import sanitize_input

# Always sanitize user input before storing
name = sanitize_input(request.name)  # Strips HTML/script tags
description = sanitize_input(request.description)
```

#### `is_safe_sql` - SQL Injection Prevention
```python
from shared.validators import is_safe_sql

# Check for SQL injection patterns
if not is_safe_sql(user_input):
    raise ValidationError("Invalid input")
```

#### `is_safe_path` - Path Traversal Prevention
```python
from shared.validators import is_safe_path

# Prevent directory traversal
if not is_safe_path(filename):
    raise ValidationError("Invalid filename")
```

### Format Validators

#### Email Validation
```python
from shared.validators import validate_email

if not validate_email(request.email):
    raise validation_error("Invalid email format", field="email")
```

#### Password Validation
```python
from shared.validators import validate_password

# Checks: length >= 8, uppercase, lowercase, digit
is_valid, message = validate_password(request.password)
if not is_valid:
    raise validation_error(message, field="password")
```

#### Username Validation
```python
from shared.validators import validate_username

# Checks: alphanumeric, underscore, 3-50 chars
if not validate_username(request.username):
    raise validation_error("Invalid username", field="username")
```

#### URL Validation
```python
from shared.validators import validate_url

if not validate_url(request.url):
    raise validation_error("Invalid URL", field="url")
```

### File Validators

#### File Extension
```python
from shared.validators import validate_file_extension

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "mp4", "webm"]

if not validate_file_extension(filename, ALLOWED_EXTENSIONS):
    raise validation_error(f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}")
```

#### File Size
```python
from shared.validators import validate_file_size

MAX_SIZE_MB = 50

if not validate_file_size(file_size_bytes, MAX_SIZE_MB):
    raise validation_error(f"File too large. Max: {MAX_SIZE_MB}MB")
```

### Complete Example
```python
from shared.validators import (
    sanitize_input,
    validate_email,
    validate_password,
    validate_file_extension,
    is_safe_path
)

def validate_user_input(data: CreateUserRequest):
    # Sanitize all text inputs
    data.name = sanitize_input(data.name)
    data.bio = sanitize_input(data.bio) if data.bio else None

    # Validate email
    if not validate_email(data.email):
        raise validation_error("Invalid email", field="email")

    # Validate password strength
    is_valid, msg = validate_password(data.password)
    if not is_valid:
        raise validation_error(msg, field="password")

    return data
```

---

## shared/errors.py - Error Handling

### Helper Functions

#### `create_error_response`
```python
from shared.errors import create_error_response

# Generic error response
raise create_error_response(
    message="Something went wrong",
    code="CUSTOM_ERROR",
    details={"field": "value"},
    status_code=400
)
```

#### `not_found_error`
```python
from shared.errors import not_found_error

# 404 Not Found
raise not_found_error("Device", device_id)
# Returns: {"message": "Device with ID 123 not found", "code": "NOT_FOUND", "details": {...}}
```

#### `validation_error`
```python
from shared.errors import validation_error

# 400 Bad Request
raise validation_error("Name is required", field="name")
raise validation_error("Invalid input", details={"errors": [...]})
```

#### `forbidden_error`
```python
from shared.errors import forbidden_error

# 403 Forbidden
raise forbidden_error("You cannot delete system roles")
```

### Error Codes
```python
from shared.errors import ErrorCodes

# Authentication
ErrorCodes.INVALID_CREDENTIALS
ErrorCodes.TOKEN_EXPIRED
ErrorCodes.TOKEN_INVALID
ErrorCodes.ACCESS_DENIED

# Validation
ErrorCodes.VALIDATION_ERROR
ErrorCodes.INVALID_INPUT
ErrorCodes.MISSING_FIELD

# Resources
ErrorCodes.NOT_FOUND
ErrorCodes.ALREADY_EXISTS
ErrorCodes.DUPLICATE_RESOURCE

# System
ErrorCodes.INTERNAL_ERROR
ErrorCodes.DATABASE_ERROR
```

### Exception Classes
```python
from shared.errors import (
    AppException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError
)

# In use cases / repositories
raise NotFoundError("User not found")
raise ConflictError("Username already exists")
raise ValidationError("Invalid date format")
```

---

## shared/cache.py - Redis Caching

### Basic Operations

```python
from shared.cache import cache

# Set with TTL (default 300 seconds)
cache.set("key", {"data": "value"}, ttl=60)

# Get
data = cache.get("key")  # Returns None if not found

# Delete
cache.delete("key")

# Check existence
if cache.exists("key"):
    pass

# Increment counter
count = cache.increment("counter_key")
```

### Pattern Operations

```python
from shared.cache import cache

# Clear by pattern (uses Redis KEYS + DELETE)
cache.clear_pattern("org:1:devices:*")
cache.clear_pattern("playlist:*")
```

### Invalidation Helpers

```python
from shared.cache import cache

# Content
cache.invalidate_content(content_id=123, org_id=1)

# Playlist
cache.invalidate_playlist(playlist_id=456, org_id=1)

# Device
cache.invalidate_device(device_id=789, org_id=1)

# Organization (all caches)
cache.invalidate_organization(org_id=1)

# Session
cache.invalidate_session(token="jwt_token_here")
```

### Cache Key Generators

```python
from shared.cache import (
    content_cache_key,
    playlist_cache_key,
    device_cache_key,
    list_cache_key
)

# Entity keys
key = content_cache_key(123)      # "content:123"
key = playlist_cache_key(456)     # "playlist:456"
key = device_cache_key(789)       # "device:789"

# List keys with filters
key = list_cache_key(
    entity="devices",
    org_id=1,
    page=1,
    limit=20,
    status="online"
)
# "org:1:devices:list:page:1:limit:20:status:online"
```

### Health Check

```python
from shared.cache import cache

status = cache.health_check()
# {"status": "healthy", "connected_clients": 5, "used_memory_human": "1.5M", ...}
```

---

## shared/middleware.py - Request Middleware

### Rate Limiting

```python
# Automatic via middleware - configured in main.py
# Default: 100 requests per minute per IP

# For specific endpoints
from shared.middleware import rate_limit_decorator

@router.post("/expensive-operation")
@rate_limit_decorator(max_requests=10, window_seconds=60)
async def expensive_operation():
    pass
```

### Request Logging

```python
# Automatic via middleware
# Logs: method, path, status_code, duration_ms, user_id (if authenticated)

# Log format:
# INFO: POST /api/devices 201 45ms user=123 org=1
```

### Security Headers

```python
# Automatic via middleware
# Adds:
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - X-XSS-Protection: 1; mode=block
# - Strict-Transport-Security (if HTTPS)
```

---

## Frontend Shared Components

### Location: `cms-vite/src/shared/`

```
shared/
├── api/
│   └── client.ts          # Axios client with interceptors
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── Modal.tsx
│   ├── ConfirmDialog.tsx
│   ├── Pagination.tsx
│   ├── AccessDenied.tsx
│   └── PageHeader.tsx
├── hooks/
│   ├── useAuth.ts         # Authentication hook
│   └── useDebounce.ts     # Debounce hook
└── utils/
    ├── cn.ts              # Class name utility
    └── validators.ts      # Frontend validators
```

---

## shared/api/client.ts - Axios Client

```typescript
import { apiClient } from '@/shared/api/client';

// GET request
const response = await apiClient.get<ResponseType>('/endpoint');

// POST request
const response = await apiClient.post<ResponseType>('/endpoint', data);

// PUT request
const response = await apiClient.put<ResponseType>('/endpoint/123', data);

// DELETE request
await apiClient.delete('/endpoint/123');

// With query params
const response = await apiClient.get('/endpoint', {
  params: { page: 1, limit: 20, search: 'query' }
});
```

### Interceptors (Automatic)
- **Request**: Adds Authorization header from stored token
- **Response**: Handles 401 (redirect to login), token refresh

---

## shared/hooks/useAuth.ts - Authentication Hook

```typescript
import { useAuth } from '@/shared/hooks/useAuth';

function MyComponent() {
  const {
    user,              // Current user object
    isAuthenticated,   // boolean
    isLoading,         // boolean
    login,             // (credentials) => Promise
    logout,            // () => void
    hasPermission,     // (permission: string) => boolean
    hasRole,           // (role: string) => boolean
  } = useAuth();

  // Check authentication
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  // Check permission
  if (!hasPermission('devices.delete')) {
    return <AccessDenied />;
  }

  // Access user data
  const orgId = user?.organization_id;
  const role = user?.role;
}
```

---

## shared/components/Modal.tsx

```typescript
import { Modal } from '@/shared/components/Modal';

<Modal
  open={isOpen}
  onOpenChange={setIsOpen}
  title="Modal Title"
  description="Optional description"
  size="md" // sm, md, lg, xl
>
  <ModalContent />
</Modal>
```

---

## shared/components/ConfirmDialog.tsx

```typescript
import { ConfirmDialog } from '@/shared/components/ConfirmDialog';

<ConfirmDialog
  open={showConfirm}
  onOpenChange={setShowConfirm}
  title="Delete Item?"
  description="This action cannot be undone."
  confirmText="Delete"
  cancelText="Cancel"
  onConfirm={handleDelete}
  isLoading={isDeleting}
  variant="destructive" // default, destructive
/>
```

---

## shared/components/Pagination.tsx

```typescript
import { Pagination } from '@/shared/components/Pagination';

<Pagination
  currentPage={page}
  totalPages={data.pages}
  onPageChange={setPage}
  showFirstLast={true}
/>
```

---

## shared/components/PageHeader.tsx

```typescript
import { PageHeader } from '@/shared/components/PageHeader';

<PageHeader
  title="Devices"
  description="Manage your digital signage devices"
  actions={
    <Button onClick={onCreate}>
      <Plus className="mr-2 h-4 w-4" />
      Add Device
    </Button>
  }
/>
```

---

## shared/utils/cn.ts - Class Name Utility

```typescript
import { cn } from '@/shared/utils/cn';

// Merge class names with conditional logic
<div className={cn(
  "base-class",
  isActive && "active-class",
  variant === "primary" ? "primary-class" : "secondary-class"
)} />
```

---

## Service Integration Quick Reference

| Service | Backend Import | Frontend Hook |
|---------|---------------|---------------|
| Auth | `from shared.auth import get_current_user` | `useAuth()` |
| RBAC | `from shared.auth import require_permission` | `usePermissions()` |
| Audit | `from services.audit.use_cases.log_action import LogActionUseCase` | N/A (backend only) |
| Cache | `from shared.cache import cache` | N/A (backend only) |
| Errors | `from shared.errors import not_found_error` | Error boundary |
| Validators | `from shared.validators import sanitize_input` | Zod schemas |

---

## Common Integration Checklist

### New Backend Endpoint
- [ ] Import `get_current_user` or `require_permission`
- [ ] Filter by `organization_id`
- [ ] Sanitize input with `sanitize_input()`
- [ ] Use standardized errors (`not_found_error`, `validation_error`)
- [ ] Add audit logging
- [ ] Invalidate cache on mutations
- [ ] Add to `shared/api_routes.py`

### New Frontend Page
- [ ] Check permission with `usePermissions()`
- [ ] Include `orgId` in query keys
- [ ] Handle loading/error states
- [ ] Use React Hook Form + Zod for forms
- [ ] Add translations to i18n files
- [ ] Add route to router config
- [ ] Add to sidebar navigation
