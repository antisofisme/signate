# User Management API Test Report

**Testing Date**: 2025-11-14
**API Server**: http://192.168.5.12:8001
**Tester**: Claude Code
**Status**: CRITICAL FAILURE

---

## Endpoints Tested: 2/6

### GET /api/v1/users
**Status**: ❌ FAILED
**HTTP Code**: 500 Internal Server Error
**Expected**: 200 OK

**Filters Attempted**:
- `organization_id`: NOT TESTED (blocked by error)
- `role`: NOT TESTED (blocked by error)
- `active_only`: NOT TESTED (blocked by error)

**Issues**:
```
ValueError: Role must be one of: super_admin, admin, manager, viewer
Location: /app/services/user/repositories/user_repo.py:206
Root Cause: Repository passes Role object instead of role name string
Impact: ALL user list operations fail
```

**Error Trace**:
```python
File "/app/services/user/repositories/user_repo.py", line 206, in _to_entity
    role=model.role,  # <-- Returns Role OBJECT, not string
File "/app/services/user/domain/user.py", line 40, in __post_init__
    raise ValueError(f"Role must be one of: {', '.join(self.VALID_ROLES)}")
ValueError: Role must be one of: super_admin, admin, manager, viewer
```

---

### POST /api/v1/users
**Status**: ❌ FAILED
**HTTP Code**: 500 Internal Server Error
**Expected**: 201 Created

**Issues**: Same as GET /api/v1/users (role mapping bug)

---

### GET /api/v1/users/{id}
**Status**: ❌ NOT TESTED
**Reason**: Blocked by same role mapping bug

---

### PUT /api/v1/users/{id}
**Status**: ❌ NOT TESTED
**Reason**: Blocked by same role mapping bug

---

### DELETE /api/v1/users/{id}
**Status**: ❌ NOT TESTED
**Reason**: Blocked by same role mapping bug

---

### PUT /api/v1/users/{id}/change-password
**Status**: ❌ NOT TESTED (P0-16 fix)
**Reason**: Blocked by same role mapping bug

**Note**: Cannot verify P0-16 fix (session revocation on password change) until role mapping is fixed.

---

## Permission Tests

### Admin access
**Status**: ❌ FAILED
**Reason**: Cannot test - endpoints returning 500 errors

**Expected Behavior**:
- Admin should see all users across all organizations
- Admin should be able to filter by organization_id
- Admin should be able to perform all CRUD operations

**Actual**: Unable to test due to blocking bug

---

### Manager access
**Status**: ❌ NOT TESTED
**Reason**: Cannot test - endpoints returning 500 errors

**Expected Behavior**:
- Manager should see only users in their organization
- Manager should NOT see organization_id filter (auto-filtered)
- Manager can create users in their org only
- Manager cannot change user roles

**Actual**: Unable to test due to blocking bug

---

### User access
**Status**: ❌ NOT TESTED
**Reason**: Cannot test - endpoints returning 500 errors

**Expected Behavior**:
- Regular user should see only their own profile
- User should get 403 when trying to access other users
- User can update limited fields (full_name, email) on self only
- User cannot change role or is_active status

**Actual**: Unable to test due to blocking bug

---

## Integration Verification

### Multi-tenancy
**Status**: ❌ NOT TESTED

**Expected**:
- Users filtered by organization_id
- Managers auto-filtered to own organization
- Cross-org data isolation enforced

**Actual**: Cannot verify - all endpoints failing

---

### Cache invalidation (P0-7)
**Status**: ❌ NOT TESTED

**Expected**:
- User updates invalidate cache
- Deleted users removed from cache
- Role changes reflected immediately

**Actual**: Cannot verify - update/delete endpoints failing

---

### Session revocation (P0-16)
**Status**: ❌ NOT TESTED

**Expected**:
- Password change revokes all user sessions
- User must re-login after password change
- Session count decremented

**Actual**: Cannot verify - change-password endpoint failing

---

## Issues Found: 4 CRITICAL BUGS

### Issue #1: Role Object vs String Type Mismatch (P0 - BLOCKING)

**Severity**: CRITICAL - Blocks ALL user operations
**File**: `backend-python/services/user/repositories/user_repo.py`
**Line**: 206
**Component**: UserRepository._to_entity()

**Problem**:
```python
# Current code (BROKEN):
def _to_entity(self, model: UserModel) -> User:
    return User(
        id=model.id,
        username=model.username,
        email=model.email,
        password_hash=model.password_hash,
        full_name=model.full_name,
        role=model.role,  # <-- BUG: Returns Role OBJECT, not string!
        organization_id=model.organization_id,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at
    )
```

**Root Cause Analysis**:

1. **Database Schema**:
   - `users.role_id` (INTEGER FK to roles.id)
   - Roles table has: SUPER_ADMIN, ADMIN, CONTENT_MANAGER, VIEWER

2. **UserModel (SQLAlchemy)**:
   - `role_id = Column(Integer, ForeignKey("roles.id"))`
   - `role = relationship("Role", foreign_keys=[role_id])`
   - Accessing `model.role` returns a **Role object**, not a string

3. **User Entity (Domain)**:
   - `role: str` - Expects string type
   - `VALID_ROLES = ['super_admin', 'admin', 'manager', 'viewer']`
   - Validation in `__post_init__` checks if role is in VALID_ROLES

4. **The Mismatch**:
   - Repository passes Role object → User entity expects string
   - Database has `CONTENT_MANAGER` → Domain expects `manager`
   - Database uses UPPERCASE → Domain validates lowercase

**Impact**:
- **ALL** endpoints that return user data fail with 500 error
- Cannot list users
- Cannot get single user
- Cannot create user
- Cannot update user
- Cannot delete user
- Cannot change password
- User Management feature is **completely non-functional**

**Fix Required**:
```python
def _to_entity(self, model: UserModel) -> User:
    """Convert SQLAlchemy model to domain entity"""

    # Convert Role object to lowercase string
    role_name = model.role.name.lower() if model.role else 'viewer'

    # Map database role names to domain role names
    role_mapping = {
        'super_admin': 'super_admin',
        'admin': 'admin',
        'content_manager': 'manager',  # Database uses CONTENT_MANAGER
        'viewer': 'viewer'
    }

    domain_role = role_mapping.get(role_name, 'viewer')

    return User(
        id=model.id,
        username=model.username,
        email=model.email,
        password_hash=model.password_hash,
        full_name=model.full_name,
        role=domain_role,  # Now properly mapped to string
        organization_id=model.organization_id,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at
    )
```

---

### Issue #2: Create/Update Assign String to Relationship Field (P0 - CRITICAL)

**Severity**: CRITICAL - Create/update will fail
**File**: `backend-python/services/user/repositories/user_repo.py`
**Lines**: 99 (create), 126 (update)
**Component**: UserRepository.create(), UserRepository.update()

**Problem**:
```python
# In create() method - Line 99 (BROKEN):
user_model = UserModel(
    username=user.username,
    email=user.email,
    password_hash=user.password_hash,
    full_name=user.full_name,
    role=user.role,  # <-- BUG: Assigning string to relationship field!
    organization_id=user.organization_id,
    is_active=user.is_active
)

# In update() method - Line 126 (BROKEN):
user_model.role = user.role  # <-- BUG: Same issue
```

**Root Cause**:
- `UserModel.role` is a **relationship**, not a column
- The actual column is `UserModel.role_id` (integer FK)
- Assigning a string to a relationship will cause SQLAlchemy error

**Impact**:
- Create user will fail
- Update user role will fail
- Role changes won't be persisted

**Fix Required**:
```python
def create(self, user: User) -> User:
    """Create new user"""
    from services.rbac.repositories.models import Role

    # Look up role_id from role name
    role_name_upper = self._map_domain_role_to_db(user.role)
    role_obj = self.db.query(Role).filter(Role.name == role_name_upper).first()

    if not role_obj:
        raise ValueError(f"Invalid role: {user.role}")

    user_model = UserModel(
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        full_name=user.full_name,
        role_id=role_obj.id,  # Use role_id, not role
        organization_id=user.organization_id,
        is_active=user.is_active
    )
    self.db.add(user_model)
    self.db.commit()
    self.db.refresh(user_model)
    return self._to_entity(user_model)

def update(self, user: User, organization_id: Optional[int] = None) -> User:
    """Update existing user"""
    from services.rbac.repositories.models import Role

    # ... existing query code ...

    user_model.email = user.email
    user_model.full_name = user.full_name

    # Update role if changed
    if user.role:
        role_name_upper = self._map_domain_role_to_db(user.role)
        role_obj = self.db.query(Role).filter(Role.name == role_name_upper).first()
        if not role_obj:
            raise ValueError(f"Invalid role: {user.role}")
        user_model.role_id = role_obj.id  # Use role_id, not role

    user_model.is_active = user.is_active

    self.db.commit()
    self.db.refresh(user_model)
    return self._to_entity(user_model)

def _map_domain_role_to_db(self, domain_role: str) -> str:
    """Map domain role name to database role name"""
    mapping = {
        'super_admin': 'SUPER_ADMIN',
        'admin': 'ADMIN',
        'manager': 'CONTENT_MANAGER',  # Domain uses 'manager', DB uses 'CONTENT_MANAGER'
        'viewer': 'VIEWER'
    }
    return mapping.get(domain_role, 'VIEWER')
```

---

### Issue #3: Missing Role Eager Loading (P1 - HIGH)

**Severity**: HIGH - N+1 query problem
**File**: `backend-python/services/user/repositories/user_repo.py`
**Lines**: All query methods (28, 45, 62, 78, 110, 137, 155)
**Component**: All UserRepository query methods

**Problem**:
- Queries don't eager load the `role` relationship
- When `_to_entity` accesses `model.role`, it triggers a separate SQL query
- Listing 100 users = 1 query for users + 100 queries for roles (N+1 problem)

**Impact**:
- Poor performance
- Unnecessary database load
- Potential lazy load errors if session closed

**Fix Required**:
```python
from sqlalchemy.orm import joinedload

# In find_by_id():
query = self.db.query(UserModel)\
    .options(joinedload(UserModel.role))\
    .filter(UserModel.id == user_id)

# In find_by_username():
query = self.db.query(UserModel)\
    .options(joinedload(UserModel.role))\
    .filter(UserModel.username == username)

# In find_by_email():
query = self.db.query(UserModel)\
    .options(joinedload(UserModel.role))\
    .filter(UserModel.email == email)

# In get_all():
query = self.db.query(UserModel)\
    .options(joinedload(UserModel.role))

# Apply to ALL methods that query UserModel
```

---

### Issue #4: Role Filter Broken in get_all() (P1 - HIGH)

**Severity**: HIGH - Feature doesn't work
**File**: `backend-python/services/user/repositories/user_repo.py`
**Line**: 84
**Component**: UserRepository.get_all()

**Problem**:
```python
# Current code (BROKEN):
if role:
    query = query.filter(UserModel.role == role)  # role is a relationship, not a column!
```

**Root Cause**:
- `UserModel.role` is a relationship to Role model, not a string column
- Cannot directly compare relationship to string
- Need to join roles table and filter by role name

**Impact**:
- Filtering users by role doesn't work
- API parameter `?role=admin` will fail or return no results

**Fix Required**:
```python
def get_all(
    self,
    organization_id: Optional[int] = None,
    role: Optional[str] = None,
    active_only: bool = False
) -> List[User]:
    """Get all users with filters"""
    from services.rbac.repositories.models import Role

    query = self.db.query(UserModel).options(joinedload(UserModel.role))

    if organization_id:
        query = query.filter(UserModel.organization_id == organization_id)

    if role:
        # Map domain role to database role name
        role_db_name = self._map_domain_role_to_db(role)
        # Join roles table and filter by name
        query = query.join(Role, UserModel.role_id == Role.id)\
                     .filter(Role.name == role_db_name)

    if active_only:
        query = query.filter(UserModel.is_active == True)

    user_models = query.order_by(UserModel.created_at.desc()).all()
    return [self._to_entity(user) for user in user_models]
```

---

## Database Investigation Results

### Current Database State

**Roles Table**:
```sql
SELECT id, name, is_system_role FROM roles WHERE is_system_role = true;
```

Result:
```
id |      name       | is_system_role
----+-----------------+----------------
 1 | SUPER_ADMIN     | t
 2 | ADMIN           | t
 3 | CONTENT_MANAGER | t
 4 | VIEWER          | t
```

**Admin User**:
```sql
SELECT u.id, u.username, u.role_id, r.name as role_name
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
WHERE u.username = 'admin';
```

Result:
```
id | username | role_id | role_name
----+----------+---------+-----------
  9 | admin    |       2 | ADMIN
```

**Users Table Schema**:
```
Column          | Type
----------------+---------------------------
id              | integer (PK)
username        | varchar(50) UNIQUE
email           | varchar(100) UNIQUE
password_hash   | varchar(255)
full_name       | varchar(100)
organization_id | integer (FK organizations)
is_active       | boolean
created_at      | timestamp with time zone
updated_at      | timestamp with time zone
role_id         | integer (FK roles)        <-- NOTE: role_id, not role
```

**Key Finding**: Database uses `role_id` (FK), NOT `role` column

---

## Role Naming Discrepancies

### Database (roles.name):
- `SUPER_ADMIN` (uppercase, underscore)
- `ADMIN` (uppercase)
- `CONTENT_MANAGER` (uppercase, underscore)
- `VIEWER` (uppercase)

### User Domain Entity (VALID_ROLES):
- `super_admin` (lowercase, underscore)
- `admin` (lowercase)
- `manager` (lowercase) ← Different name!
- `viewer` (lowercase)

### Mapping Required:
| Database | Domain | Note |
|----------|--------|------|
| SUPER_ADMIN | super_admin | Case conversion |
| ADMIN | admin | Case conversion |
| CONTENT_MANAGER | manager | Name change + case |
| VIEWER | viewer | Case conversion |

---

## Recommendations

### Immediate Actions (P0)

1. **Fix _to_entity() method**
   - Add role object to string conversion
   - Add role name mapping (CONTENT_MANAGER → manager)
   - Add lowercase conversion
   - Handle null roles gracefully

2. **Fix create() method**
   - Look up role_id from role name
   - Assign to user_model.role_id, not user_model.role
   - Add role validation

3. **Fix update() method**
   - Look up role_id from role name
   - Assign to user_model.role_id, not user_model.role
   - Add role validation

4. **Deploy fixes to server**
   - Sync updated user_repo.py
   - Restart backend container
   - Verify no syntax errors in logs

5. **Re-run test suite**
   - Execute comprehensive tests
   - Verify all endpoints return 200/201/204
   - Generate new test report

### High Priority Actions (P1)

1. **Fix get_all() role filter**
   - Join roles table
   - Filter by role name
   - Test filter functionality

2. **Add eager loading**
   - Add joinedload to all queries
   - Measure performance improvement
   - Verify no N+1 queries

3. **Add repository unit tests**
   - Test role mapping
   - Test create/update with roles
   - Test filtering by role
   - Test organization isolation

### Future Improvements

1. **Standardize role naming**
   - Decision: Use lowercase in DB or mapping layer?
   - Update database or keep mapping?
   - Document chosen approach

2. **Add database constraints**
   - CHECK constraint on roles.name
   - Ensure only valid values
   - Prevent data inconsistencies

3. **Consider domain model changes**
   - Should User entity use role_id instead of role string?
   - Would match database better
   - Trade-off: convenience vs. accuracy

4. **Add integration tests**
   - Test multi-tenancy isolation
   - Test cache invalidation
   - Test session revocation
   - Test RBAC enforcement

---

## Files Requiring Changes

### Critical (Must Fix)
1. `backend-python/services/user/repositories/user_repo.py`
   - Line 206: Fix _to_entity()
   - Line 99: Fix create()
   - Line 126: Fix update()
   - Line 84: Fix get_all() filter
   - All queries: Add joinedload

### Optional (Consider)
1. `backend-python/services/user/domain/user.py`
   - Update VALID_ROLES documentation
   - Add role normalization helper

2. Database migration
   - Rename CONTENT_MANAGER to MANAGER?
   - Add CHECK constraint?
   - Standardize to lowercase?

---

## Test Summary

| Metric | Value |
|--------|-------|
| **Endpoints Tested** | 2/6 |
| **Passed** | 0 |
| **Failed** | 2 |
| **Not Tested** | 4 |
| **Success Rate** | **0%** |
| **Critical Issues** | 4 |
| **Blocking Issue** | Yes (role mapping) |

---

## Conclusion

**All user management endpoints are non-functional** due to a critical bug in the user repository's role mapping logic. The repository attempts to pass a Role object to the User domain entity which expects a role name string. This causes a ValueError on every operation that returns user data.

**Next Steps**:
1. Fix the 4 critical bugs in user_repo.py
2. Deploy fixes to server
3. Re-run comprehensive test suite
4. Verify all endpoints functional
5. Test permission matrix
6. Test integrations (multi-tenancy, cache, sessions)
7. Generate final passing test report

**Estimated Fix Time**: 30 minutes
**Testing Time**: 15 minutes
**Total Resolution Time**: ~45 minutes

---

**Report Generated**: 2025-11-14 03:18 UTC
**Reporter**: Claude Code
**Status**: AWAITING FIXES
