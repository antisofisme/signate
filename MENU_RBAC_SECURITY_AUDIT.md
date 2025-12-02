# Menu System RBAC Security Audit Report

**Date**: 2025-12-02
**Auditor**: Backend Security Coding Expert
**Scope**: Menu management system (Admin & Media routes)
**Systems Reviewed**:
- `/backend-python/services/menu/routes.py` (Admin routes)
- `/backend-python/services/menu/menu_media_routes.py` (Media routes)
- `/backend-python/services/menu/public_routes.py` (Public routes)
- `/backend-python/shared/auth.py` (RBAC implementation)
- `/backend-python/services/rbac/constants.py` (Permission definitions)

---

## Executive Summary

The menu system has **NO role-based permission checks** on administrative endpoints. All authenticated users can perform CRUD operations regardless of their role (SUPER_ADMIN, ADMIN, CONTENT_MANAGER, or VIEWER). This is a **CRITICAL security vulnerability** that allows privilege escalation and unauthorized data modification.

**Risk Level**: 🔴 **CRITICAL**

**Impact**:
- VIEWER role can create, edit, and delete menus
- CONTENT_MANAGER can delete menus (should be admin-only)
- Users can modify data across organizations (if SUPER_ADMIN header is forged)
- No audit trail differentiation between authorized and unauthorized actions

---

## Critical Issues (Privilege Escalation & Missing Auth)

### CRIT-01: No Role Checks on Menu CRUD Operations
**File**: `/backend-python/services/menu/routes.py`
**Lines**: 113-324 (All CRUD endpoints)

**Issue**: ALL menu endpoints only verify authentication (`get_current_user`) but do NOT check role permissions.

**Affected Endpoints**:
```python
# Lines 113-161: Create Menu
@router.post("", status_code=201)
async def create_menu(
    current_user: CurrentUser = Depends(get_current_user),  # ❌ No role check
    ...
)

# Lines 250-297: Update Menu
@router.patch("/{menu_id}")
def update_menu(
    current_user: CurrentUser = Depends(get_current_user),  # ❌ No role check
    ...
)

# Lines 300-324: Delete Menu
@router.delete("/{menu_id}", status_code=204)
def delete_menu(
    current_user: CurrentUser = Depends(get_current_user),  # ❌ No role check
    ...
)
```

**Expected Permissions** (from `/services/rbac/constants.py` line 82-135):
```python
SYSTEM_ROLE_PERMISSIONS = {
    'SUPER_ADMIN': {
        'menus': ['view', 'create', 'edit', 'delete', 'manage'],  # ✅ All
    },
    'ADMIN': {
        'menus': ['view', 'create', 'edit', 'delete'],  # ✅ All
    },
    'CONTENT_MANAGER': {
        'menus': ['view', 'create', 'edit'],  # ⚠️ NO DELETE
    },
    'VIEWER': {
        # ❌ NO menu permissions defined - should be VIEW ONLY
    },
}
```

**Actual Behavior**: VIEWER can delete menus because there's no permission check.

**Attack Scenario**:
1. Attacker registers as VIEWER role
2. Attacker calls `DELETE /api/v1/menus/1` with valid JWT
3. Menu is deleted successfully (audit log shows "menu.delete" but doesn't flag unauthorized action)
4. Business impact: Critical menu data lost

**Recommendation**:
```python
# Add permission checks to all menu endpoints
from shared.rbac_checker import require_permission

@router.delete("/{menu_id}", status_code=204)
def delete_menu(
    menu_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("menus", "delete")),  # ✅ Add this
    ...
)
```

---

### CRIT-02: No Role Checks on Menu Item CRUD
**File**: `/backend-python/services/menu/routes.py`
**Lines**: 406-510 (Menu items endpoints)

**Issue**: Same as CRIT-01 - menu items can be created/edited/deleted by any authenticated user.

**Affected Endpoints**:
```python
# Lines 406-436: Add Menu Item
@router.post("/{menu_id}/items", status_code=201)
def add_menu_item(...)  # ❌ No role check

# Lines 439-474: Update Menu Item
@router.patch("/{menu_id}/items/{item_id}")
def update_menu_item(...)  # ❌ No role check

# Lines 477-510: Delete Menu Item
@router.delete("/{menu_id}/items/{item_id}", status_code=204)
def delete_menu_item(...)  # ❌ No role check
```

**Expected**: CONTENT_MANAGER should be able to edit but NOT delete items.

**Actual**: VIEWER can delete items.

---

### CRIT-03: No Role Checks on Menu Categories
**File**: `/backend-python/services/menu/routes.py`
**Lines**: 673-843 (Categories endpoints)

**Issue**: Categories can be created/edited/deleted by any authenticated user.

**Affected Endpoints**:
```python
# Lines 695-737: Create Category
@router.post("/{menu_id}/categories", status_code=201)
def create_menu_category(...)  # ❌ No role check

# Lines 740-781: Update Category
@router.patch("/{menu_id}/categories/{category_id}")
def update_menu_category(...)  # ❌ No role check

# Lines 784-817: Delete Category
@router.delete("/{menu_id}/categories/{category_id}", status_code=204)
def delete_menu_category(...)  # ❌ No role check
```

---

### CRIT-04: No Role Checks on Media Management
**File**: `/backend-python/services/menu/menu_media_routes.py`
**Lines**: 276-555 (All media endpoints)

**Issue**: Media upload, update, delete have NO role checks.

**Affected Endpoints**:
```python
# Lines 276-420: Upload Media
@router.post("", status_code=201)
async def upload_menu_media(
    current_user: CurrentUser = Depends(get_current_user),  # ❌ No role check
    ...
)

# Lines 440-458: Update Media
@router.patch("/{media_id}")
def update_menu_media(...)  # ❌ No role check

# Lines 461-477: Delete Media (Soft Delete)
@router.delete("/{media_id}", status_code=204)
def delete_menu_media(...)  # ❌ No role check

# Lines 508-528: Permanent Delete
@router.delete("/{media_id}/permanent", status_code=204)
def permanent_delete_menu_media(...)  # ❌ No role check
```

**Expected**: Only ADMIN+ should be able to permanently delete media.

**Actual**: VIEWER can permanently delete media.

---

### CRIT-05: No Role Checks on Excel Import/Export
**File**: `/backend-python/services/menu/routes.py`
**Lines**: 515-594 (Import/Export endpoints)

**Issue**: Bulk import can replace all menu items without permission check.

**Affected Endpoints**:
```python
# Lines 515-544: Bulk Import (DANGEROUS)
@router.post("/{menu_id}/import")
async def import_items_from_excel(
    replace_existing: bool = Query(False),  # ⚠️ Can delete all items
    current_user: CurrentUser = Depends(get_current_user),  # ❌ No role check
    ...
)
```

**Attack Scenario**:
1. VIEWER uploads malicious Excel file with `replace_existing=True`
2. All menu items are deleted and replaced with attacker's data
3. Business impact: Data loss, menu corruption

---

### CRIT-06: Weak Organization Isolation Check
**File**: `/backend-python/services/menu/routes.py`
**Lines**: Multiple locations

**Issue**: Organization ID is checked in repositories, but NOT validated against user's actual permissions.

**Current Implementation** (Line 148):
```python
# routes.py line 148
menu = menu_repo.find_by_id(menu_data["id"], current_user.organization_id)
```

**Problem**: `current_user.organization_id` can be overridden via `X-Organization-Id` header for SUPER_ADMIN (see `/shared/auth.py` lines 516-540).

**Repository Check** (menu_repo.py lines 48-63):
```python
def find_by_id(
    self,
    menu_id: int,
    organization_id: int,  # ❌ Trusts input blindly
    include_deleted: bool = False
) -> Optional[MenuModel]:
    query = self.db.query(MenuModel).filter(
        MenuModel.id == menu_id,
        MenuModel.organization_id == organization_id  # No role check
    )
```

**Missing Validation**:
- No check if SUPER_ADMIN is switching to a valid organization
- No check if regular user is forging `X-Organization-Id` header

**Recommendation**: Add organization validation:
```python
from shared.auth import can_access_organization, is_super_admin

def find_by_id(self, menu_id: int, organization_id: int, current_user: CurrentUser):
    # Validate organization access
    if not is_super_admin(current_user):
        if current_user.organization_id != organization_id:
            raise AuthorizationError("Cannot access other organizations")

    # Existing query...
```

---

## Warning Issues (Incomplete Permission Checks)

### WARN-01: No Service-Level Permission Validation
**File**: `/backend-python/services/menu/use_cases/*.py`

**Issue**: Use cases assume route-level permission checks (which don't exist).

**Example** (`create_menu.py` lines 20-60):
```python
class CreateMenuUseCase:
    async def execute(
        self,
        organization_id: int,
        created_by_id: int,
        ...
    ):
        # ❌ No permission check - assumes route validated it
        # Business logic executes blindly
```

**Recommendation**: Implement defense-in-depth with service-level checks:
```python
class CreateMenuUseCase:
    async def execute(
        self,
        organization_id: int,
        created_by_id: int,
        current_user: CurrentUser,  # Add user context
        ...
    ):
        # ✅ Validate permission at service layer
        from shared.rbac_checker import check_permission
        check_permission(current_user, "menus", "create")

        # Business logic...
```

---

### WARN-02: Missing CONTENT_MANAGER vs ADMIN Differentiation
**File**: `/backend-python/services/rbac/constants.py` lines 118-126

**Issue**: CONTENT_MANAGER has 'edit' permission on menus, but the code doesn't distinguish between:
- Editing menu content (items, media) - CONTENT_MANAGER ✅
- Editing menu settings (colors, QR code, public URL) - ADMIN only ⚠️

**Current Permissions**:
```python
'CONTENT_MANAGER': {
    'menus': ['view', 'create', 'edit'],  # Too broad
},
```

**Recommendation**: Split into granular permissions:
```python
'CONTENT_MANAGER': {
    'menus': ['view'],  # Can view menu settings
    'menu_items': ['view', 'create', 'edit'],  # Can manage items
    'menu_media': ['view', 'create', 'edit'],  # Can manage media
    'menu_categories': ['view', 'create', 'edit'],  # Can manage categories
},
'ADMIN': {
    'menus': ['view', 'create', 'edit', 'delete'],  # Can change menu settings
    'menu_items': ['view', 'create', 'edit', 'delete'],
    'menu_media': ['view', 'create', 'edit', 'delete'],
},
```

---

### WARN-03: No Audit Log Differentiation for Unauthorized Access
**File**: `/backend-python/services/menu/routes.py` (Multiple audit_logger calls)

**Issue**: Audit logs don't flag unauthorized actions because permissions aren't checked.

**Current Logging** (Line 276-283):
```python
audit_logger.log_action(
    user_id=current_user.id,
    action="menu.update",
    resource_type="menu",
    resource_id=menu.id,
    details=update_data,
    organization_id=current_user.organization_id
)
```

**Problem**: If a VIEWER updates a menu, the log shows "menu.update" without indicating it's unauthorized.

**Recommendation**: Add authorization context:
```python
audit_logger.log_action(
    user_id=current_user.id,
    action="menu.update",
    resource_type="menu",
    resource_id=menu.id,
    details={
        **update_data,
        "user_role": current_user.role,
        "authorized": has_permission(current_user, "menus", "edit"),  # ✅ Flag
    },
    organization_id=current_user.organization_id
)
```

---

### WARN-04: Public Routes Have No Rate Limiting
**File**: `/backend-python/services/menu/public_routes.py`

**Issue**: Public menu viewer has NO rate limiting, allowing DDoS attacks.

**Vulnerable Endpoints**:
```python
# Lines 71-109: Public Menu Access
@router.get("/{public_url_code}")
async def get_public_menu(...)  # ❌ No rate limit

# Lines 112-144: Track Contact Click
@router.post("/{public_url_code}/track-contact")
async def track_contact_click(...)  # ❌ No rate limit
```

**Recommendation**: Add rate limiting:
```python
from shared.rate_limiter import rate_limit

@router.get("/{public_url_code}")
@rate_limit(max_requests=60, window_seconds=60)  # 60 req/min per IP
async def get_public_menu(...)
```

---

## Info - Recommendations

### INFO-01: Implement Permission Checker Middleware
**Create**: `/backend-python/shared/rbac_checker.py`

```python
"""RBAC Permission Checker for FastAPI Routes"""

from fastapi import Depends, HTTPException
from shared.auth import get_current_user, CurrentUser
from services.rbac.constants import has_permission, SYSTEM_ROLE_PERMISSIONS

def require_permission(resource: str, action: str):
    """
    FastAPI dependency to require specific permission.

    Usage:
        @router.post("/menus")
        def create_menu(
            _: None = Depends(require_permission("menus", "create")),
            current_user: CurrentUser = Depends(get_current_user)
        ):
            ...
    """
    def check_permission(current_user: CurrentUser = Depends(get_current_user)):
        # Get user's role permissions
        role_permissions = SYSTEM_ROLE_PERMISSIONS.get(current_user.role.upper(), {})

        # Check if user has permission
        if not has_permission(role_permissions, resource, action):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Insufficient permissions",
                    "required": f"{resource}:{action}",
                    "user_role": current_user.role,
                    "allowed_actions": role_permissions.get(resource, [])
                }
            )

        return current_user

    return check_permission


def check_permission_silent(current_user: CurrentUser, resource: str, action: str) -> bool:
    """
    Silent permission check (returns boolean, doesn't raise exception).

    Use in service layer for conditional logic.
    """
    role_permissions = SYSTEM_ROLE_PERMISSIONS.get(current_user.role.upper(), {})
    return has_permission(role_permissions, resource, action)
```

---

### INFO-02: Add Permission Checks to All Menu Endpoints

**Implementation Template**:
```python
from shared.rbac_checker import require_permission

# Example: Create Menu
@router.post("", status_code=201)
async def create_menu(
    payload: MenuCreateDTO,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("menus", "create")),  # ✅ Add this
    menu_repo: MenuRepository = Depends(get_menu_repository),
    ...
):
    """Create new digital menu"""
    # Existing implementation...


# Example: Delete Menu
@router.delete("/{menu_id}", status_code=204)
def delete_menu(
    menu_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("menus", "delete")),  # ✅ Add this
    menu_repo: MenuRepository = Depends(get_menu_repository),
    ...
):
    """Soft delete menu"""
    # Existing implementation...
```

**Apply to All Endpoints**:
- Menu CRUD: `create_menu`, `update_menu`, `delete_menu`
- Menu Items: `add_menu_item`, `update_menu_item`, `delete_menu_item`
- Categories: `create_menu_category`, `update_menu_category`, `delete_menu_category`
- Media: `upload_menu_media`, `update_menu_media`, `delete_menu_media`, `permanent_delete_menu_media`
- Import/Export: `import_items_from_excel`, `export_menu_to_excel`

---

### INFO-03: Implement Granular Permissions for Menu Subsystems

**Update**: `/backend-python/services/rbac/constants.py`

```python
# Add new resource types
PERMISSION_RESOURCES: List[str] = [
    # ... existing ...
    'menus',           # Menu settings (name, colors, QR code)
    'menu_items',      # Menu items (food/drink items)
    'menu_media',      # Media library
    'menu_categories', # Category management
]

# Update role permissions
SYSTEM_ROLE_PERMISSIONS: Dict[str, Dict[str, List[str]]] = {
    'SUPER_ADMIN': {
        'menus': ['view', 'create', 'edit', 'delete', 'manage'],
        'menu_items': ['view', 'create', 'edit', 'delete', 'manage'],
        'menu_media': ['view', 'create', 'edit', 'delete', 'manage'],
        'menu_categories': ['view', 'create', 'edit', 'delete', 'manage'],
    },
    'ADMIN': {
        'menus': ['view', 'create', 'edit', 'delete'],
        'menu_items': ['view', 'create', 'edit', 'delete'],
        'menu_media': ['view', 'create', 'edit', 'delete'],
        'menu_categories': ['view', 'create', 'edit', 'delete'],
    },
    'CONTENT_MANAGER': {
        'menus': ['view'],  # Read-only menu settings
        'menu_items': ['view', 'create', 'edit'],  # ⚠️ No delete
        'menu_media': ['view', 'create', 'edit'],  # ⚠️ No delete
        'menu_categories': ['view', 'create', 'edit'],  # ⚠️ No delete
    },
    'VIEWER': {
        'menus': ['view'],
        'menu_items': ['view'],
        'menu_media': ['view'],
        'menu_categories': ['view'],
    },
}
```

**Then update route decorators**:
```python
# Menu settings - ADMIN only
@router.patch("/{menu_id}")
def update_menu(
    _: None = Depends(require_permission("menus", "edit")),  # Admin+
    ...
)

# Menu items - CONTENT_MANAGER can edit
@router.patch("/{menu_id}/items/{item_id}")
def update_menu_item(
    _: None = Depends(require_permission("menu_items", "edit")),  # Content Manager+
    ...
)

# Menu items delete - ADMIN only
@router.delete("/{menu_id}/items/{item_id}")
def delete_menu_item(
    _: None = Depends(require_permission("menu_items", "delete")),  # Admin+
    ...
)
```

---

### INFO-04: Add Organization Validation Middleware

**Create**: `/backend-python/shared/organization_validator.py`

```python
"""Organization Access Validation for Multi-Tenancy"""

from fastapi import Depends, HTTPException
from shared.auth import get_current_user, CurrentUser, is_super_admin

def validate_organization_access(organization_id: int):
    """
    Validate that current user can access specified organization.

    Usage:
        @router.get("/menus/{menu_id}")
        def get_menu(
            menu_id: int,
            current_user: CurrentUser = Depends(get_current_user),
            menu_repo: MenuRepository = Depends(get_menu_repository)
        ):
            # Get menu first
            menu = menu_repo.find_by_id(menu_id, current_user.organization_id)

            # Validate organization access
            validate_organization_access(menu.organization_id)(current_user)

            # Continue...
    """
    def check_access(current_user: CurrentUser = Depends(get_current_user)):
        # SUPER_ADMIN can access any organization
        if is_super_admin(current_user):
            return current_user

        # Regular users can only access their own organization
        if current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Organization access denied",
                    "user_organization": current_user.organization_id,
                    "requested_organization": organization_id
                }
            )

        return current_user

    return check_access
```

---

### INFO-05: Security Testing Checklist

**Test Cases to Implement**:

```python
# tests/security/test_menu_rbac.py

def test_viewer_cannot_create_menu():
    """VIEWER role should not be able to create menus"""
    viewer_token = login_as_viewer()
    response = client.post(
        "/api/v1/menus",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"name": "Test Menu", "menu_type": "food"}
    )
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]["error"]


def test_viewer_cannot_delete_menu():
    """VIEWER role should not be able to delete menus"""
    admin_token = login_as_admin()
    menu = create_menu(admin_token)

    viewer_token = login_as_viewer()
    response = client.delete(
        f"/api/v1/menus/{menu['id']}",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert response.status_code == 403


def test_content_manager_cannot_delete_menu():
    """CONTENT_MANAGER can edit but not delete menus"""
    admin_token = login_as_admin()
    menu = create_menu(admin_token)

    manager_token = login_as_content_manager()

    # Can edit items
    response = client.post(
        f"/api/v1/menus/{menu['id']}/items",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"name": "Burger", "price": 10.00}
    )
    assert response.status_code == 201

    # Cannot delete menu
    response = client.delete(
        f"/api/v1/menus/{menu['id']}",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 403


def test_cannot_access_other_organization_menu():
    """Users cannot access menus from other organizations"""
    org1_admin_token = login_as_admin(org_id=1)
    org1_menu = create_menu(org1_admin_token)

    org2_admin_token = login_as_admin(org_id=2)
    response = client.get(
        f"/api/v1/menus/{org1_menu['id']}",
        headers={"Authorization": f"Bearer {org2_admin_token}"}
    )
    assert response.status_code == 404  # Menu not found (org isolation)


def test_super_admin_can_access_all_organizations():
    """SUPER_ADMIN can switch organizations via header"""
    org1_admin_token = login_as_admin(org_id=1)
    org1_menu = create_menu(org1_admin_token)

    super_admin_token = login_as_super_admin()
    response = client.get(
        f"/api/v1/menus/{org1_menu['id']}",
        headers={
            "Authorization": f"Bearer {super_admin_token}",
            "X-Organization-Id": "1"  # Switch to org 1
        }
    )
    assert response.status_code == 200
    assert response.json()["data"]["id"] == org1_menu["id"]
```

---

## Summary of Vulnerabilities

| ID | Severity | Issue | Affected Endpoints | Recommendation |
|----|----------|-------|-------------------|----------------|
| CRIT-01 | 🔴 Critical | No role checks on menu CRUD | 8 endpoints | Add `require_permission` to all routes |
| CRIT-02 | 🔴 Critical | No role checks on menu items | 6 endpoints | Add `require_permission("menu_items", action)` |
| CRIT-03 | 🔴 Critical | No role checks on categories | 5 endpoints | Add `require_permission("menu_categories", action)` |
| CRIT-04 | 🔴 Critical | No role checks on media | 8 endpoints | Add `require_permission("menu_media", action)` |
| CRIT-05 | 🔴 Critical | No role check on bulk import | 1 endpoint | Require ADMIN+ for bulk operations |
| CRIT-06 | 🔴 Critical | Weak org isolation | All endpoints | Validate org access in repositories |
| WARN-01 | ⚠️ Warning | No service-level checks | All use cases | Add defense-in-depth checks |
| WARN-02 | ⚠️ Warning | Broad CONTENT_MANAGER perms | Permission constants | Split into granular permissions |
| WARN-03 | ⚠️ Warning | No audit log flags | All audit logs | Add authorization status to logs |
| WARN-04 | ⚠️ Warning | No rate limiting on public | 2 public endpoints | Add rate limiting |

---

## Remediation Priority

### Phase 1: Critical Fixes (Immediate - Week 1)
1. ✅ Create `shared/rbac_checker.py` with `require_permission` dependency
2. ✅ Add permission checks to all menu CRUD endpoints (routes.py)
3. ✅ Add permission checks to all media endpoints (menu_media_routes.py)
4. ✅ Add organization validation to repositories
5. ✅ Write security tests for VIEWER privilege escalation

### Phase 2: Warning Fixes (Week 2)
1. ✅ Implement service-level permission checks in use cases
2. ✅ Split permissions into granular resources (menu_items, menu_media, menu_categories)
3. ✅ Add audit log authorization flags
4. ✅ Add rate limiting to public endpoints

### Phase 3: Hardening (Week 3-4)
1. ✅ Implement organization validation middleware
2. ✅ Add comprehensive security test suite
3. ✅ Conduct penetration testing with different roles
4. ✅ Document permission model in API docs

---

## Compliance & Regulatory Impact

**OWASP Top 10 Violations**:
- **A01:2021 – Broken Access Control**: ✅ VIOLATED (all CRIT issues)
- **A03:2021 – Injection**: ⚠️ Partial (no input validation on permissions)

**GDPR/Privacy Concerns**:
- Menu data may contain personal information (phone numbers, WhatsApp numbers)
- Unauthorized access by VIEWER could lead to data breach notification requirements

**Industry Standards**:
- **PCI DSS**: If menus include payment information, this is a critical compliance failure
- **SOC 2**: Lack of access controls fails "Logical Access" control objectives

---

## Conclusion

The menu system requires **IMMEDIATE remediation** of all CRITICAL issues before production deployment. The current implementation allows any authenticated user to perform administrative actions, creating significant security and business risks.

**Estimated Remediation Time**: 2-3 weeks for full implementation and testing.

**Risk of NOT Fixing**:
- Data loss (unauthorized deletion)
- Data corruption (unauthorized modification)
- Compliance violations (unauthorized access to PII)
- Reputational damage (security breach disclosure)

---

**Report End**
