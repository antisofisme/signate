---
name: core-services-integration
description: Standardize integration of 5 core services (Auth, User, Organization, RBAC, Audit) and shared components when implementing new features. Use when creating new backend endpoints, frontend pages, or any feature that needs authentication, authorization, user management, organization context, or audit logging.
---

# Core Services Integration Guide

## Overview

This skill ensures consistent integration of the 5 foundational services and shared components across all features in the Smart TV Digital Signage system. Use this guide whenever implementing new features to avoid gaps and inconsistencies.

## When to Use This Skill

- Creating new backend API endpoints
- Creating new frontend pages/components
- Adding authentication to features
- Implementing role-based access control
- Adding audit logging to operations
- Working with organization-scoped data
- Using shared validators, cache, or error handling

## Architecture Quick Reference

```
Backend (FastAPI)                    Frontend (React + Vite)
─────────────────                    ─────────────────────
services/                            src/features/
├── auth/          ←──────────────→  ├── auth/
├── user/          ←──────────────→  ├── users/
├── organization/  ←──────────────→  ├── organizations/
├── rbac/          ←──────────────→  ├── rbac/
├── audit/         ←──────────────→  ├── audit/
└── [your-feature]/                  └── [your-feature]/

shared/                              src/shared/
├── auth.py        (JWT, permissions)├── hooks/ (useAuth)
├── validators.py  (input validation)├── utils/ (validators)
├── errors.py      (error responses) ├── api/ (axios client)
├── cache.py       (Redis caching)   └── components/
└── middleware.py  (rate limiting)
```

## Integration Checklist

### Backend Endpoint Checklist

```python
# 1. Import required dependencies
from shared.auth import get_current_user, require_permission
from shared.validators import sanitize_input, validate_email
from shared.errors import create_error_response, not_found_error, validation_error
from shared.cache import cache
from services.audit.use_cases.log_action import LogActionUseCase

# 2. Apply authentication
@router.get("/items")
async def get_items(
    current_user: dict = Depends(get_current_user)  # REQUIRED
):
    pass

# 3. Apply permission check
@router.post("/items")
async def create_item(
    current_user: dict = Depends(require_permission("items.create"))  # RBAC
):
    pass

# 4. Filter by organization (multi-tenancy)
items = repo.get_by_organization(current_user["organization_id"])

# 5. Sanitize user input
name = sanitize_input(data.name)

# 6. Log audit trail
audit_use_case.execute(
    user_id=current_user["sub"],
    action="CREATE",
    resource_type="item",
    resource_id=item.id,
    details={"name": item.name}
)

# 7. Use standardized errors
if not item:
    raise not_found_error("Item", item_id)
```

### Frontend Page Checklist

```typescript
// 1. Use auth hook for protected routes
import { useAuth } from '@/shared/hooks/useAuth';

// 2. Check permissions before rendering
const { user, hasPermission } = useAuth();
if (!hasPermission('items.read')) return <AccessDenied />;

// 3. Use organization context
const orgId = user?.organization_id;

// 4. Use TanStack Query for data fetching
const { data, isLoading, error } = useQuery({
  queryKey: ['items', orgId],
  queryFn: () => itemsApi.getAll(orgId),
  enabled: !!orgId
});

// 5. Handle errors consistently
if (error) return <ErrorDisplay error={error} />;

// 6. Use React Hook Form + Zod for validation
const schema = z.object({
  name: z.string().min(1).max(200),
  email: z.string().email()
});
```

## Service Integration Patterns

### 1. Auth Service Integration

**Backend:**
```python
# In your routes.py
from shared.auth import get_current_user, require_permission, verify_session

@router.get("/protected")
async def protected_endpoint(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["sub"]
    org_id = current_user["organization_id"]
    role = current_user["role"]
    # ...
```

**Frontend:**
```typescript
// In your component
import { useAuth } from '@/shared/hooks/useAuth';

function MyComponent() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  // ...
}
```

### 2. RBAC Service Integration

**Backend:**
```python
# Permission-based access
@router.delete("/items/{id}")
async def delete_item(
    id: int,
    current_user: dict = Depends(require_permission("items.delete"))
):
    # User has items.delete permission
    pass

# Role hierarchy check
from shared.auth import PermissionChecker
checker = PermissionChecker(current_user["role"], current_user.get("permissions", []))
if not checker.can_manage_users():
    raise forbidden_error("Cannot manage users")
```

**Frontend:**
```typescript
// Permission-based UI
import { usePermissions } from '@/features/rbac/hooks/usePermissions';

function ItemActions({ item }) {
  const { hasPermission } = usePermissions();

  return (
    <div>
      {hasPermission('items.edit') && <EditButton />}
      {hasPermission('items.delete') && <DeleteButton />}
    </div>
  );
}
```

### 3. Organization Service Integration

**Backend:**
```python
# Always filter by organization
@router.get("/items")
async def get_items(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org_id = current_user["organization_id"]
    items = item_repo.get_by_organization(org_id)  # REQUIRED
    return items
```

**Frontend:**
```typescript
// Organization context in API calls
const orgId = user?.organization_id;

// Include in query keys for proper caching
const { data } = useQuery({
  queryKey: ['items', orgId],  // Include orgId
  queryFn: () => api.get(`/items?organization_id=${orgId}`)
});
```

### 4. Audit Service Integration

**Backend:**
```python
from services.audit.use_cases.log_action import LogActionUseCase
from services.audit.repositories.audit_log_repo import AuditLogRepository

# In your use case or route
async def create_item(data, current_user, db):
    # Create item
    item = item_repo.create(data)

    # Log audit trail
    audit_repo = AuditLogRepository(db)
    audit_use_case = LogActionUseCase(audit_repo)
    audit_use_case.execute(
        user_id=int(current_user["sub"]),
        action="CREATE",
        resource_type="item",
        resource_id=item.id,
        details={"name": item.name},
        ip_address=request.client.host
    )

    return item
```

**Audit Actions Standard:**
- CREATE, READ, UPDATE, DELETE (CRUD)
- LOGIN, LOGOUT, PASSWORD_CHANGE (Auth)
- ASSIGN, UNASSIGN (Relationships)
- ACTIVATE, DEACTIVATE (Status changes)
- EXPORT, IMPORT (Bulk operations)

### 5. User Service Integration

**Backend:**
```python
# Get user details
from services.user.repositories.user_repo import UserRepository

user_repo = UserRepository(db)
user = user_repo.get_by_id(user_id)

# Bulk operations
users = user_repo.bulk_get_by_ids([1, 2, 3])
```

**Frontend:**
```typescript
import { useUsers } from '@/features/users/hooks/useUsers';

function UserSelector() {
  const { users, isLoading } = useUsers();
  // ...
}
```

## Shared Components Usage

### Validators (Backend)

```python
from shared.validators import (
    sanitize_input,      # XSS prevention
    validate_email,      # Email format
    validate_password,   # Password strength
    validate_username,   # Username format
    is_safe_path,        # Path traversal prevention
    validate_file_extension,  # File upload safety
    validate_url         # URL format
)

# Always sanitize user input
name = sanitize_input(request.name)
if not validate_email(request.email):
    raise validation_error("Invalid email format", field="email")
```

### Error Handling (Backend)

```python
from shared.errors import (
    create_error_response,  # Generic error
    not_found_error,        # 404
    validation_error,       # 400
    forbidden_error,        # 403
    ErrorCodes              # Standard error codes
)

# Use helpers instead of raw HTTPException
raise not_found_error("Device", device_id)
raise validation_error("Name is required", field="name")
raise forbidden_error("Cannot delete system role")
```

### Caching (Backend)

```python
from shared.cache import cache, list_cache_key

# Cache entity
cache.set(f"item:{item_id}", item_data, ttl=300)

# Get from cache
cached = cache.get(f"item:{item_id}")

# Invalidate on update
cache.delete(f"item:{item_id}")
cache.clear_pattern(f"org:{org_id}:items:*")
```

### Middleware (Backend)

```python
# Rate limiting is automatic via middleware
# Configure in shared/middleware.py

# Add to specific routes if needed
from shared.middleware import rate_limit_decorator

@router.post("/expensive-operation")
@rate_limit_decorator(max_requests=10, window_seconds=60)
async def expensive_operation():
    pass
```

## Common Mistakes to Avoid

### Backend

1. **Missing organization filter**
   ```python
   # WRONG - returns ALL items
   items = db.query(Item).all()

   # CORRECT - scoped to organization
   items = db.query(Item).filter(Item.organization_id == org_id).all()
   ```

2. **Missing permission check**
   ```python
   # WRONG - anyone can delete
   @router.delete("/items/{id}")
   async def delete_item(id: int):
       pass

   # CORRECT - requires permission
   @router.delete("/items/{id}")
   async def delete_item(
       id: int,
       current_user: dict = Depends(require_permission("items.delete"))
   ):
       pass
   ```

3. **Inconsistent error format**
   ```python
   # WRONG - plain string
   raise HTTPException(status_code=404, detail="Not found")

   # CORRECT - structured format
   raise not_found_error("Item", item_id)
   ```

4. **Missing audit logging**
   ```python
   # WRONG - no audit trail
   item_repo.delete(item_id)

   # CORRECT - with audit
   item_repo.delete(item_id)
   audit_use_case.execute(user_id, "DELETE", "item", item_id)
   ```

### Frontend

1. **Missing permission check**
   ```typescript
   // WRONG - shows to everyone
   <DeleteButton onClick={handleDelete} />

   // CORRECT - permission-gated
   {hasPermission('items.delete') && <DeleteButton onClick={handleDelete} />}
   ```

2. **Missing organization context**
   ```typescript
   // WRONG - missing org context
   const { data } = useQuery(['items'], getItems);

   // CORRECT - includes org for proper caching
   const { data } = useQuery(['items', orgId], () => getItems(orgId));
   ```

3. **Not handling loading/error states**
   ```typescript
   // WRONG - no states
   return <ItemList items={data} />;

   // CORRECT - handle all states
   if (isLoading) return <Skeleton />;
   if (error) return <ErrorDisplay error={error} />;
   return <ItemList items={data} />;
   ```

## File Templates

See supporting documentation:
- [backend-patterns.md](backend-patterns.md) - Complete backend templates
- [frontend-patterns.md](frontend-patterns.md) - Complete frontend templates
- [shared-components.md](shared-components.md) - Shared utilities reference

## Quick Commands

```bash
# Create new backend service
mkdir -p backend-python/services/[name]/{repositories,use_cases}
touch backend-python/services/[name]/{__init__,models,dtos,routes}.py

# Create new frontend feature
mkdir -p cms-vite/src/features/[name]/{api,components,hooks,types}
touch cms-vite/src/features/[name]/index.ts
```
