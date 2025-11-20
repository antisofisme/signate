# User Management API Test Report

**Test Date**: 2025-11-14
**API Base URL**: http://192.168.5.12:8001
**API Version**: v1
**Tested By**: Claude Code

---

## Executive Summary

**Status**: CRITICAL FAILURES DETECTED
**Endpoints Tested**: 2/6 (Unable to test more due to blocking issue)
**Success Rate**: 0%

### Critical Blocking Issue Found

**P0 BUG**: User repository role mapping failure
- **Severity**: CRITICAL - Blocks ALL user management endpoints
- **Location**: `/backend-python/services/user/repositories/user_repo.py`, line 206
- **Issue**: `model.role` returns a Role object, but User entity expects a string
- **Error**: `ValueError: Role must be one of: super_admin, admin, manager, viewer`
- **Impact**: All endpoints that return user data fail with 500 error

---

## Endpoints Tested

### Authentication
- Login: PASSED
  - Endpoint: POST /api/v1/auth/login
  - Username: admin
  - Role: ADMIN
  - Organization ID: 4
  - Token received successfully

### User Management Endpoints

#### 1. GET /api/v1/users (List Users)
**Status**: FAILED
**HTTP Code**: 500 Internal Server Error
**Expected**: 200 OK

**Error Details**:
```
File "/app/services/user/repositories/user_repo.py", line 206, in _to_entity
    role=model.role,
File "/app/services/user/domain/user.py", line 40, in __post_init__
    raise ValueError(f"Role must be one of: {', '.join(self.VALID_ROLES)}")
ValueError: Role must be one of: super_admin, admin, manager, viewer
```

**Root Cause**:
- Database schema uses `role_id` (FK to roles table)
- UserModel has `role` relationship that returns Role object
- Repository `_to_entity` method passes Role object instead of role name string
- User domain entity validates role must be a string from VALID_ROLES list

**Database Investigation**:
```sql
-- Current database state
SELECT u.id, u.username, u.role_id, r.name as role_name
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
WHERE u.username = 'admin';

-- Result:
id | username | role_id | role_name
----+----------+---------+-----------
  9 | admin    |       2 | ADMIN
```

**Roles Table**:
```sql
SELECT id, name, is_system_role FROM roles WHERE is_system_role = true;

-- Result:
id |      name       | is_system_role
----+-----------------+----------------
  1 | SUPER_ADMIN     | t
  2 | ADMIN           | t
  3 | CONTENT_MANAGER | t
  4 | VIEWER          | t
```

**Mismatch Identified**:
- Database has: `ADMIN`, `SUPER_ADMIN`, `CONTENT_MANAGER`, `VIEWER` (uppercase)
- User entity expects: `admin`, `super_admin`, `manager`, `viewer` (lowercase)
- Also, `CONTENT_MANAGER` in DB vs `manager` in code

#### 2. POST /api/v1/users (Create User)
**Status**: FAILED
**HTTP Code**: 500 Internal Server Error
**Expected**: 201 Created

**Same root cause as endpoint #1** - Cannot convert user model to entity.

#### 3. GET /api/v1/users/{id} (Get Single User)
**Status**: NOT TESTED
**Reason**: Blocked by same issue as #1

#### 4. PUT /api/v1/users/{id} (Update User)
**Status**: NOT TESTED
**Reason**: Blocked by same issue as #1

#### 5. PUT /api/v1/users/{id}/change-password (Change Password - P0-16)
**Status**: NOT TESTED
**Reason**: Blocked by same issue as #1

#### 6. DELETE /api/v1/users/{id} (Delete User)
**Status**: NOT TESTED
**Reason**: Blocked by same issue as #1

---

## Permission Tests

### NOT COMPLETED
**Reason**: Cannot test permissions when all endpoints return 500 errors

**Planned Tests**:
- Admin can see all users: NOT TESTED
- Manager can see org users only: NOT TESTED
- Regular user can see self only: NOT TESTED

---

## Integration Verification

### Multi-Tenancy
**Status**: NOT TESTED
**Reason**: List users endpoint fails

### Cache Invalidation (P0-7)
**Status**: NOT TESTED
**Reason**: Update operations fail

### Session Revocation on Password Change (P0-16)
**Status**: NOT TESTED
**Reason**: Change password endpoint fails

### Role-Based Access Control
**Status**: NOT TESTED
**Reason**: All endpoints fail

---

## Issues Found

### Issue #1: Role Mapping in User Repository (CRITICAL - P0)
**File**: `backend-python/services/user/repositories/user_repo.py`
**Line**: 206
**Severity**: CRITICAL - Blocks all user operations

**Problem**:
```python
# Current (BROKEN):
def _to_entity(self, model: UserModel) -> User:
    return User(
        ...
        role=model.role,  # This is a Role OBJECT, not a string!
        ...
    )
```

**Fix Required**:
```python
# Should be:
def _to_entity(self, model: UserModel) -> User:
    # Convert role object to lowercase string
    role_name = model.role.name.lower() if model.role else 'viewer'

    # Map database role names to domain entity role names
    role_map = {
        'super_admin': 'super_admin',
        'admin': 'admin',
        'content_manager': 'manager',  # Map CONTENT_MANAGER to manager
        'viewer': 'viewer'
    }

    return User(
        ...
        role=role_map.get(role_name, 'viewer'),
        ...
    )
```

**Additional Fixes Needed**:
1. Add `joinedload` for role relationship in all queries to avoid N+1
2. Handle null role gracefully
3. Fix create/update methods that assign `user.role` string to `user_model.role` (should be role_id)

### Issue #2: Missing Role Eager Loading
**File**: `backend-python/services/user/repositories/user_repo.py`
**Lines**: 28, 45, 62, 78
**Severity**: HIGH - Performance issue (N+1 queries)

**Problem**: Queries don't eager load the role relationship

**Fix Required**:
```python
from sqlalchemy.orm import joinedload

# Add to all queries:
query = self.db.query(UserModel).options(joinedload(UserModel.role))
```

### Issue #3: Create/Update Role Assignment
**File**: `backend-python/services/user/repositories/user_repo.py`
**Lines**: 99, 126
**Severity**: CRITICAL - Create/update will fail

**Problem**:
```python
# Current (BROKEN):
user_model.role = user.role  # Assigning string to relationship
```

**Fix Required**:
```python
# Need to map role name to role_id
from services.rbac.repositories.models import Role

# In create:
role_obj = self.db.query(Role).filter(Role.name == user.role.upper()).first()
if not role_obj:
    raise ValueError(f"Invalid role: {user.role}")
user_model.role_id = role_obj.id

# In update:
if user.role:
    role_obj = self.db.query(Role).filter(Role.name == user.role.upper()).first()
    if not role_obj:
        raise ValueError(f"Invalid role: {user.role}")
    user_model.role_id = role_obj.id
```

### Issue #4: Role Filter in get_all
**File**: `backend-python/services/user/repositories/user_repo.py`
**Line**: 84
**Severity**: HIGH - Filter won't work

**Problem**:
```python
# Current (BROKEN):
if role:
    query = query.filter(UserModel.role == role)  # role is a relationship, not a column
```

**Fix Required**:
```python
if role:
    # Need to join and filter by role name
    from services.rbac.repositories.models import Role
    query = query.join(Role, UserModel.role_id == Role.id).filter(Role.name == role.upper())
```

---

## Recommendations

### Immediate Actions Required

1. **FIX P0**: Update `user_repo.py` `_to_entity` method to properly map Role object to string
   - Add role name mapping (CONTENT_MANAGER → manager)
   - Convert to lowercase
   - Handle null roles

2. **FIX P0**: Update `create` and `update` methods to use `role_id` instead of `role`
   - Add role name to role_id lookup
   - Validate role exists
   - Handle case sensitivity

3. **FIX HIGH**: Add eager loading for role relationship
   - Prevent N+1 query problems
   - Improve performance

4. **FIX HIGH**: Fix role filter in `get_all` method
   - Join roles table properly
   - Filter by role name

5. **TEST**: Re-run all user management endpoint tests after fixes

6. **VERIFY**: Integration tests for:
   - Multi-tenancy filtering
   - Cache invalidation
   - Session revocation
   - RBAC permissions

### Long-term Improvements

1. **Consistency**: Decide on single role naming convention
   - Either: Database uses lowercase (admin, manager, viewer)
   - Or: Code maps uppercase DB names to lowercase domain names
   - Current mismatch (CONTENT_MANAGER vs manager) is confusing

2. **Migration**: Consider adding CHECK constraint on roles.name
   - Ensure only valid role names in database
   - Prevent data inconsistencies

3. **Domain Model**: Consider whether User entity should use role_id instead of role string
   - Would match database schema better
   - Could lazy-load role details when needed

4. **Repository Tests**: Add unit tests for repository methods
   - Test role mapping
   - Test eager loading
   - Test organization filtering

---

## Test Summary

| Metric | Count |
|--------|-------|
| Total Endpoints | 6 |
| Endpoints Tested | 2 |
| Passed | 0 |
| Failed | 2 |
| Not Tested | 4 |
| **Success Rate** | **0%** |
| Critical Issues | 3 |
| High Priority Issues | 2 |

---

## Next Steps

1. Fix critical bugs in user repository
2. Deploy fixes to server
3. Re-run comprehensive test suite
4. Verify all 6 endpoints working
5. Test permission matrix (admin/manager/user)
6. Test multi-tenancy isolation
7. Test P0-7 (cache invalidation)
8. Test P0-16 (session revocation)
9. Generate final test report

---

## Files Requiring Changes

### Critical Priority
1. `backend-python/services/user/repositories/user_repo.py` - Fix role mapping
2. `backend-python/services/user/domain/user.py` - Consider role validation update

### For Reference
- Database schema: `roles` table uses uppercase names (ADMIN, CONTENT_MANAGER)
- User entity: Expects lowercase names (admin, manager)
- Migration needed to standardize naming or mapping layer needed

---

**Report Generated**: 2025-11-14
**Status**: TESTING BLOCKED - Critical bugs must be fixed before proceeding
