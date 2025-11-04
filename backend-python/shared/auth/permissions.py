"""
Permission Checking
Role-based access control (RBAC) for API endpoints
"""

from enum import Enum
from typing import List, Optional, Callable
from fastapi import Depends
from shared.errors import AuthorizationError, ErrorCodes
from .jwt import CurrentUser, get_current_user


class Role(str, Enum):
    """User roles in hierarchical order"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"


# Role hierarchy: higher roles have all permissions of lower roles
ROLE_HIERARCHY = {
    Role.SUPER_ADMIN: 4,
    Role.ADMIN: 3,
    Role.MANAGER: 2,
    Role.VIEWER: 1
}


def get_role_level(role: str) -> int:
    """Get numeric level for role (higher = more permissions)"""
    return ROLE_HIERARCHY.get(Role(role), 0)


def has_role(user: CurrentUser, required_role: str) -> bool:
    """
    Check if user has required role or higher

    Args:
        user: Current user
        required_role: Minimum required role

    Returns:
        True if user has required role or higher
    """
    user_level = get_role_level(user.role)
    required_level = get_role_level(required_role)
    return user_level >= required_level


def is_super_admin(user: CurrentUser) -> bool:
    """Check if user is super admin"""
    return user.role == Role.SUPER_ADMIN


def is_admin(user: CurrentUser) -> bool:
    """Check if user is admin or higher"""
    return has_role(user, Role.ADMIN)


def is_manager(user: CurrentUser) -> bool:
    """Check if user is manager or higher"""
    return has_role(user, Role.MANAGER)


def is_same_organization(user: CurrentUser, organization_id: int) -> bool:
    """Check if user belongs to the specified organization"""
    return user.organization_id == organization_id


def can_access_organization(user: CurrentUser, organization_id: int) -> bool:
    """
    Check if user can access resources from specified organization

    Rules:
    - super_admin: can access all organizations
    - admin: can access all organizations
    - manager/viewer: can only access own organization
    """
    if is_admin(user):
        return True
    return is_same_organization(user, organization_id)


def require_role(required_role: str) -> Callable:
    """
    FastAPI dependency to require minimum role

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(Role.ADMIN))])
        def admin_endpoint():
            return {"message": "Admin access"}

    Args:
        required_role: Minimum required role

    Returns:
        FastAPI dependency function
    """
    def check_role(current_user: CurrentUser = Depends(get_current_user)):
        if not has_role(current_user, required_role):
            raise AuthorizationError(
                message=f"Akses ditolak. Role minimal: {required_role}",
                code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
                details={
                    "user_role": current_user.role,
                    "required_role": required_role
                }
            )
        return current_user
    return check_role


def require_super_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    FastAPI dependency to require super admin role

    Usage:
        @router.post("/system-config")
        def update_system_config(current_user: CurrentUser = Depends(require_super_admin)):
            return {"message": "Config updated"}
    """
    if not is_super_admin(current_user):
        raise AuthorizationError(
            message="Akses ditolak. Hanya super admin yang diizinkan",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={"user_role": current_user.role}
        )
    return current_user


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    FastAPI dependency to require admin role or higher

    Usage:
        @router.post("/organizations")
        def create_organization(current_user: CurrentUser = Depends(require_admin)):
            return {"message": "Org created"}
    """
    if not is_admin(current_user):
        raise AuthorizationError(
            message="Akses ditolak. Role minimal: admin",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={"user_role": current_user.role}
        )
    return current_user


def require_manager(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    FastAPI dependency to require manager role or higher

    Usage:
        @router.get("/users")
        def list_users(current_user: CurrentUser = Depends(require_manager)):
            return {"users": []}
    """
    if not is_manager(current_user):
        raise AuthorizationError(
            message="Akses ditolak. Role minimal: manager",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={"user_role": current_user.role}
        )
    return current_user


def require_same_organization(
    organization_id: int,
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Check if user can access resources from specified organization

    Admins can access all organizations, others only their own

    Usage:
        @router.get("/organizations/{org_id}/users")
        def get_org_users(
            org_id: int,
            current_user: CurrentUser = Depends(lambda: require_same_organization(org_id))
        ):
            return {"users": []}
    """
    if not can_access_organization(current_user, organization_id):
        raise AuthorizationError(
            message="Akses ditolak. Anda tidak memiliki akses ke organization ini",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={
                "user_organization": current_user.organization_id,
                "requested_organization": organization_id
            }
        )
    return current_user


class PermissionChecker:
    """
    Permission checker class for complex permission logic

    Usage:
        checker = PermissionChecker(current_user)
        if checker.can_edit_user(target_user_id):
            # Allow edit
        else:
            # Deny
    """

    def __init__(self, current_user: CurrentUser):
        self.current_user = current_user

    def can_edit_user(self, target_user_id: int, target_organization_id: int) -> bool:
        """Check if current user can edit target user"""
        # Super admin can edit anyone
        if is_super_admin(self.current_user):
            return True

        # Admin can edit users in any organization
        if is_admin(self.current_user):
            return True

        # Manager can edit users in same organization (but not admins)
        if is_manager(self.current_user):
            return is_same_organization(self.current_user, target_organization_id)

        # Viewer can't edit anyone
        return False

    def can_delete_user(self, target_user_id: int, target_organization_id: int, target_role: str) -> bool:
        """Check if current user can delete target user"""
        # Can't delete yourself
        if target_user_id == self.current_user.id:
            return False

        # Super admin can delete anyone (except self)
        if is_super_admin(self.current_user):
            return True

        # Admin can delete users in any organization (but not other admins)
        if is_admin(self.current_user):
            return not is_admin(CurrentUser(
                id=target_user_id,
                username="",
                role=target_role,
                organization_id=target_organization_id
            ))

        # Manager can delete users in same organization (but not admins/managers)
        if is_manager(self.current_user):
            is_same_org = is_same_organization(self.current_user, target_organization_id)
            is_lower_role = get_role_level(target_role) < get_role_level(Role.MANAGER)
            return is_same_org and is_lower_role

        # Viewer can't delete anyone
        return False

    def can_create_user_with_role(self, role: str, organization_id: int) -> bool:
        """Check if current user can create user with specified role"""
        # Super admin can create any role
        if is_super_admin(self.current_user):
            return True

        # Admin can create any role except super_admin
        if is_admin(self.current_user):
            return role != Role.SUPER_ADMIN

        # Manager can create manager/viewer in same organization
        if is_manager(self.current_user):
            is_same_org = is_same_organization(self.current_user, organization_id)
            is_allowed_role = role in [Role.MANAGER, Role.VIEWER]
            return is_same_org and is_allowed_role

        # Viewer can't create users
        return False

    def can_manage_organization(self, organization_id: Optional[int] = None) -> bool:
        """Check if current user can manage organizations"""
        # Only admins and above can manage organizations
        return is_admin(self.current_user)
