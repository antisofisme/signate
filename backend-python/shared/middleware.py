"""
Authentication Middleware
FastAPI dependencies for JWT authentication and authorization
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import extract_user_from_token
from functools import wraps


# =============================================================================
# AUTHENTICATION DEPENDENCY
# =============================================================================

async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Extract and validate current user from Authorization header

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        User information dictionary

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Validate token and extract user info
    user_info = extract_user_from_token(token)

    # Add raw token for session validation (P0-16)
    user_info["token"] = token

    return user_info


async def get_current_active_user(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Verify that current user is active in database AND session is not revoked (P0-16)

    Multi-tenancy support:
    - SUPER_ADMIN: organization_id can be overridden via X-Organization-Id header
    - Regular users: organization_id is always from JWT (header ignored for security)

    Args:
        request: FastAPI request object (for reading X-Organization-Id header)
        current_user: User info from token (includes 'token' field)
        db: Database session

    Returns:
        User information dictionary with effective organization_id

    Raises:
        HTTPException: If user is not active, not found, or session revoked
    """
    from services.user.repositories.user_repo import UserRepository
    from services.session.repositories.session_repo import SessionRepository
    import hashlib

    user_repo = UserRepository(db)
    user = user_repo.find_by_id(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # CRITICAL FIX P0-16: Check if session is revoked
    if "token" in current_user:
        token = current_user["token"]

        session_repo = SessionRepository(db)
        session = session_repo.find_by_token(token)  # find_by_token will hash internally

        if session and session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "Session has been revoked. Please login again.",
                    "code": "SESSION_REVOKED",
                    "details": {}
                }
            )

        # SECURITY: Update session last activity timestamp for idle detection
        if session:
            try:
                session_repo.update_last_activity(session.id)
            except Exception:
                # Don't fail the request if activity update fails
                pass

    # =============================================================================
    # MULTI-TENANCY: Calculate effective organization_id
    # =============================================================================
    # Store original JWT organization for reference
    jwt_org_id = current_user.get("organization_id")
    current_user["jwt_organization_id"] = jwt_org_id

    user_role = current_user.get("role", "").lower()
    header_org_id = request.headers.get("X-Organization-Id")

    # For SUPER_ADMIN: Allow switching organizations via header
    if user_role == "super_admin" and header_org_id:
        try:
            effective_org_id = int(header_org_id)
            current_user["organization_id"] = effective_org_id
            current_user["organization_switched"] = True
        except (ValueError, TypeError):
            # Invalid header value, keep JWT org_id
            current_user["organization_switched"] = False
    else:
        # Regular users: Always use their JWT organization (ignore header)
        current_user["organization_switched"] = False

    return current_user


# =============================================================================
# ROLE-BASED AUTHORIZATION
# =============================================================================

class RoleChecker:
    """
    Dependency class to check user roles
    Performs case-insensitive role comparison to handle both
    UPPERCASE (JWT token) and lowercase (domain) role names
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [role.lower() for role in allowed_roles]

    def __call__(self, current_user: dict = Depends(get_current_active_user)):
        user_role = current_user["role"].lower() if current_user.get("role") else ""
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )
        return current_user


# Predefined role checkers
require_admin = RoleChecker(["super_admin", "admin"])
require_admin_or_manager = RoleChecker(["super_admin", "admin", "manager"])
require_any_role = RoleChecker(["super_admin", "admin", "manager", "user"])


# =============================================================================
# ORGANIZATION ACCESS CONTROL
# =============================================================================

class OrganizationAccessChecker:
    """
    Dependency class to check organization access

    Rules:
    - Admin: Can access all organizations
    - Manager/User: Can only access their own organization
    """

    def __call__(
        self,
        org_id: int,
        current_user: dict = Depends(get_current_active_user)
    ):
        # Admin can access any organization
        if current_user["role"] == "admin":
            return current_user

        # Manager/User can only access their own organization
        if current_user["organization_id"] != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own organization."
            )

        return current_user


require_org_access = OrganizationAccessChecker()


# =============================================================================
# RESOURCE OWNERSHIP CHECKER
# =============================================================================

class ResourceOwnershipChecker:
    """
    Dependency class to check resource ownership

    Rules:
    - Admin: Can access any resource
    - Manager: Can access resources in their organization
    - User: Can only access their own resources
    """

    def __call__(
        self,
        resource_user_id: int,
        resource_org_id: Optional[int],
        current_user: dict = Depends(get_current_active_user)
    ):
        # Admin can access anything
        if current_user["role"] == "admin":
            return current_user

        # Manager can access resources in their org
        if current_user["role"] == "manager":
            if resource_org_id != current_user["organization_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Resource belongs to different organization."
                )
            return current_user

        # User can only access their own resources
        if current_user["role"] == "user":
            if resource_user_id != current_user["user_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You can only access your own resources."
                )
            return current_user

        # Fallback: deny access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )


require_resource_access = ResourceOwnershipChecker()


# =============================================================================
# OPTIONAL AUTHENTICATION
# =============================================================================

async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Optional authentication - returns user if token present, None otherwise
    Useful for endpoints that work for both authenticated and anonymous users

    Args:
        authorization: Optional Bearer token

    Returns:
        User information dictionary or None
    """
    if not authorization:
        return None

    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        user_info = extract_user_from_token(token)
        return user_info
    except:
        return None


# =============================================================================
# PERMISSION HELPERS
# =============================================================================

def can_manage_user(current_user: dict, target_user_org_id: Optional[int]) -> bool:
    """
    Check if current user can manage target user

    Args:
        current_user: Current authenticated user
        target_user_org_id: Organization ID of target user

    Returns:
        True if user can manage, False otherwise
    """
    # Admin can manage any user
    if current_user["role"] == "admin":
        return True

    # Manager can manage users in their organization
    if current_user["role"] == "manager":
        return target_user_org_id == current_user["organization_id"]

    # Regular users cannot manage other users
    return False


def can_manage_organization(current_user: dict, target_org_id: int) -> bool:
    """
    Check if current user can manage target organization

    Args:
        current_user: Current authenticated user
        target_org_id: Target organization ID

    Returns:
        True if user can manage, False otherwise
    """
    # Only admins can manage organizations
    return current_user["role"] == "admin"


def can_view_audit_logs(current_user: dict, log_org_id: Optional[int]) -> bool:
    """
    Check if current user can view audit log

    Args:
        current_user: Current authenticated user
        log_org_id: Organization ID of audit log

    Returns:
        True if user can view, False otherwise
    """
    # Admin can view all logs
    if current_user["role"] == "admin":
        return True

    # Manager can view logs from their organization
    if current_user["role"] == "manager":
        return log_org_id == current_user["organization_id"]

    # Regular users cannot view audit logs
    return False


# =============================================================================
# PERMISSION-BASED ACCESS CONTROL (P0-2 RBAC)
# =============================================================================

class PermissionChecker:
    """
    Dependency class to check specific permissions from role's permission matrix

    Permission format: {resource: [actions]}
    Example: {"contents": ["view", "create", "edit"], "devices": ["view"]}

    Usage:
        @router.post("/contents")
        def create_content(
            current_user: dict = Depends(require_permission("contents", "create"))
        ):
            # current_user["organization_id"] is already the effective organization
            ...

    Multi-tenancy:
    - organization_id is already resolved by get_current_active_user
    - SUPER_ADMIN: organization_id from X-Organization-Id header (if provided)
    - Regular users: organization_id from JWT (header ignored for security)
    """

    def __init__(self, resource: str, action: str):
        """
        Args:
            resource: Resource name (e.g., "contents", "devices", "playlists")
            action: Action name (e.g., "view", "create", "edit", "delete", "manage")
        """
        self.resource = resource.lower()
        self.action = action.lower()

    async def __call__(
        self,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> dict:
        """
        Check if user has the required permission

        Permission lookup priority:
        1. Check permissions in JWT token (if present) - fast path
        2. Fetch permissions from database (fallback)

        Special roles:
        - SUPER_ADMIN: Has all permissions by default
        - System roles have predefined permissions

        Note:
        - current_user["organization_id"] is already the effective organization
          (resolved by get_current_active_user based on role and X-Organization-Id header)
        """
        user_role = current_user.get("role", "").lower()

        # SUPER_ADMIN bypass - has all permissions
        if user_role == "super_admin":
            return current_user

        # Check permissions from JWT token first (fast path)
        if "permissions" in current_user and current_user["permissions"]:
            if self._has_permission(current_user["permissions"]):
                return current_user

        # Fallback: Fetch permissions from database
        permissions = await self._get_user_permissions(current_user["user_id"], db)

        if self._has_permission(permissions):
            return current_user

        # Permission denied
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": f"Permission denied. Required: {self.resource}:{self.action}",
                "code": "PERMISSION_DENIED",
                "required_permission": f"{self.resource}:{self.action}",
                "user_role": user_role
            }
        )

    def _has_permission(self, permissions: dict) -> bool:
        """
        Check if permission exists in permission dict

        Args:
            permissions: Dict of {resource: [actions]}

        Returns:
            True if permission found
        """
        if not permissions:
            return False

        resource_permissions = permissions.get(self.resource, [])

        # Check for exact action or "manage" (which implies all actions)
        if self.action in resource_permissions:
            return True
        if "manage" in resource_permissions:
            return True

        return False

    async def _get_user_permissions(self, user_id: int, db: Session) -> dict:
        """
        Fetch user's role permissions from database

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Permission dict {resource: [actions]}
        """
        from services.user.repositories.user_repo import UserRepository

        user_repo = UserRepository(db)
        role_details = user_repo.get_user_role(user_id)

        if role_details and role_details.get("permissions"):
            return role_details["permissions"]

        return {}


def require_permission(resource: str, action: str) -> PermissionChecker:
    """
    Factory function to create permission checker

    Usage:
        @router.post("/contents")
        def create_content(
            current_user: dict = Depends(require_permission("contents", "create"))
        ):
            ...

    Args:
        resource: Resource name (e.g., "contents", "devices")
        action: Action name (e.g., "view", "create", "edit", "delete")

    Returns:
        PermissionChecker dependency
    """
    return PermissionChecker(resource, action)


class MultiPermissionChecker:
    """
    Check if user has ANY of the required permissions (OR logic)

    Usage:
        @router.get("/reports")
        def get_reports(
            current_user: dict = Depends(require_any_permission([
                ("analytics", "view"),
                ("reports", "view")
            ]))
        ):
            ...
    """

    def __init__(self, permissions: List[tuple]):
        """
        Args:
            permissions: List of (resource, action) tuples
        """
        self.permissions = [(r.lower(), a.lower()) for r, a in permissions]

    async def __call__(
        self,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> dict:
        user_role = current_user.get("role", "").lower()

        # SUPER_ADMIN bypass
        if user_role == "super_admin":
            return current_user

        # Get user's permissions
        user_permissions = current_user.get("permissions", {})
        if not user_permissions:
            from services.user.repositories.user_repo import UserRepository
            user_repo = UserRepository(db)
            role_details = user_repo.get_user_role(current_user["user_id"])
            if role_details:
                user_permissions = role_details.get("permissions", {})

        # Check if ANY permission matches
        for resource, action in self.permissions:
            resource_perms = user_permissions.get(resource, [])
            if action in resource_perms or "manage" in resource_perms:
                return current_user

        # None matched
        permission_strs = [f"{r}:{a}" for r, a in self.permissions]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": f"Permission denied. Required one of: {', '.join(permission_strs)}",
                "code": "PERMISSION_DENIED",
                "required_permissions": permission_strs
            }
        )


def require_any_permission(permissions: List[tuple]) -> MultiPermissionChecker:
    """
    Factory function for OR-based permission checking

    Args:
        permissions: List of (resource, action) tuples

    Returns:
        MultiPermissionChecker dependency
    """
    return MultiPermissionChecker(permissions)


class AllPermissionsChecker:
    """
    Check if user has ALL of the required permissions (AND logic)

    Usage:
        @router.delete("/organization/{org_id}")
        def delete_organization(
            current_user: dict = Depends(require_all_permissions([
                ("organizations", "delete"),
                ("users", "manage")
            ]))
        ):
            ...
    """

    def __init__(self, permissions: List[tuple]):
        self.permissions = [(r.lower(), a.lower()) for r, a in permissions]

    async def __call__(
        self,
        current_user: dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> dict:
        user_role = current_user.get("role", "").lower()

        # SUPER_ADMIN bypass
        if user_role == "super_admin":
            return current_user

        # Get user's permissions
        user_permissions = current_user.get("permissions", {})
        if not user_permissions:
            from services.user.repositories.user_repo import UserRepository
            user_repo = UserRepository(db)
            role_details = user_repo.get_user_role(current_user["user_id"])
            if role_details:
                user_permissions = role_details.get("permissions", {})

        # Check that ALL permissions match
        missing = []
        for resource, action in self.permissions:
            resource_perms = user_permissions.get(resource, [])
            if action not in resource_perms and "manage" not in resource_perms:
                missing.append(f"{resource}:{action}")

        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"Permission denied. Missing: {', '.join(missing)}",
                    "code": "PERMISSION_DENIED",
                    "missing_permissions": missing
                }
            )

        return current_user


def require_all_permissions(permissions: List[tuple]) -> AllPermissionsChecker:
    """
    Factory function for AND-based permission checking

    Args:
        permissions: List of (resource, action) tuples

    Returns:
        AllPermissionsChecker dependency
    """
    return AllPermissionsChecker(permissions)
