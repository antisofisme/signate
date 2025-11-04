# Authentication & Authorization Middleware

Permission middleware untuk role-based access control (RBAC) di FastAPI.

## Role Hierarchy

```
super_admin (Level 4) - Akses semua
    ↓
admin (Level 3) - Akses semua organizations
    ↓
manager (Level 2) - Akses own organization only
    ↓
viewer (Level 1) - Read only access
```

## Usage Examples

### 1. Require Authentication (Any Role)

```python
from fastapi import APIRouter, Depends
from shared.auth import CurrentUser, get_current_user

router = APIRouter()

@router.get("/profile")
def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }
```

### 2. Require Specific Role

```python
from shared.auth import CurrentUser, require_admin, require_manager

# Only admin and above
@router.post("/organizations")
def create_organization(current_user: CurrentUser = Depends(require_admin)):
    return {"message": "Org created"}

# Only manager and above (manager, admin, super_admin)
@router.get("/users")
def list_users(current_user: CurrentUser = Depends(require_manager)):
    return {"users": []}
```

### 3. Require Super Admin

```python
from shared.auth import require_super_admin

@router.post("/system/config")
def update_system_config(current_user: CurrentUser = Depends(require_super_admin)):
    return {"message": "System config updated"}
```

### 4. Check Organization Access

```python
from shared.auth import CurrentUser, get_current_user, can_access_organization
from shared.errors import AuthorizationError, ErrorCodes

@router.get("/organizations/{org_id}/users")
def get_org_users(
    org_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    # Admin can access all organizations
    # Others can only access their own
    if not can_access_organization(current_user, org_id):
        raise AuthorizationError(
            message="Anda tidak memiliki akses ke organization ini",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS
        )

    # Get users...
    return {"users": []}
```

### 5. Complex Permission Checking

```python
from shared.auth import CurrentUser, get_current_user, PermissionChecker
from shared.errors import AuthorizationError, ErrorCodes

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get target user
    target_user = db.query(UserModel).get(user_id)

    # Check if current user can delete target user
    checker = PermissionChecker(current_user)
    if not checker.can_delete_user(
        target_user_id=target_user.id,
        target_organization_id=target_user.organization_id,
        target_role=target_user.role
    ):
        raise AuthorizationError(
            message="Anda tidak memiliki izin untuk menghapus user ini",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS
        )

    # Delete user...
    return {"message": "User deleted"}
```

### 6. Optional Authentication

```python
from shared.auth import get_optional_user

@router.get("/public-content")
def get_public_content(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_optional_user)
):
    # Works both authenticated and unauthenticated
    if current_user:
        # Personalized content
        return {"message": f"Welcome back, {current_user.username}"}
    else:
        # Public content
        return {"message": "Welcome, guest"}
```

## Permission Rules

### Organization Management
- **super_admin**: Dapat manage semua organizations
- **admin**: Dapat manage semua organizations
- **manager/viewer**: Tidak dapat manage organizations

### User Management
- **super_admin**: Dapat CRUD semua users, termasuk admin
- **admin**: Dapat CRUD users di semua organizations (kecuali admin lain)
- **manager**: Dapat CRUD users di own organization (kecuali admin/manager)
- **viewer**: Tidak dapat CRUD users

### Creating Users
- **super_admin**: Dapat create user dengan role apapun
- **admin**: Dapat create user (kecuali super_admin)
- **manager**: Dapat create manager/viewer di own organization
- **viewer**: Tidak dapat create users

### Device Management
- **admin and above**: Dapat manage semua devices
- **manager**: Dapat manage devices di own organization
- **viewer**: Read only

## JWT Token Payload

Token JWT berisi informasi:
```json
{
  "sub": "user_id",
  "username": "username",
  "role": "admin",
  "organization_id": 1,
  "exp": "expiry_timestamp"
}
```

## Error Handling

Permission middleware akan throw:
- `AuthenticationError` (401) - Token invalid/missing
- `AuthorizationError` (403) - Insufficient permissions

```python
from shared.errors import AuthenticationError, AuthorizationError, ErrorCodes

# In middleware
raise AuthenticationError(
    message="Token tidak valid",
    code=ErrorCodes.INVALID_TOKEN
)

raise AuthorizationError(
    message="Akses ditolak",
    code=ErrorCodes.INSUFFICIENT_PERMISSIONS
)
```

## Testing with Postman/curl

```bash
# Login to get token
curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token in protected endpoint
curl -X GET http://192.168.5.12:8001/api/v1/users \
  -H "Authorization: Bearer <your_token_here>"
```
