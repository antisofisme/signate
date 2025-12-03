"""
RBAC Permission Checker
Resource-based permission checking for menu/content management

This module provides FastAPI dependencies for checking user permissions
against the RBAC system defined in services/rbac/constants.py
"""

from typing import Callable, Optional
from functools import wraps

from fastapi import Depends, HTTPException, status

from shared.auth import CurrentUser, get_current_user, is_super_admin
from shared.errors import AuthorizationError, ErrorCodes
from services.rbac.constants import SYSTEM_ROLE_PERMISSIONS, has_permission, has_manage_permission


def check_permission(
    user: CurrentUser,
    resource: str,
    action: str
) -> bool:
    """
    Check if user has permission for a specific resource and action.

    Uses the RBAC system with role-based defaults.
    SUPER_ADMIN always has full access.

    Args:
        user: Current authenticated user
        resource: Resource name (e.g., 'menus', 'contents')
        action: Action name (e.g., 'view', 'create', 'edit', 'delete')

    Returns:
        True if user has permission, False otherwise
    """
    # Normalize role to uppercase for matching SYSTEM_ROLE_PERMISSIONS
    role_upper = user.role.upper() if isinstance(user.role, str) else str(user.role).upper()

    # SUPER_ADMIN always has full access
    if role_upper == "SUPER_ADMIN":
        return True

    # Get role permissions from system defaults
    role_permissions = SYSTEM_ROLE_PERMISSIONS.get(role_upper, {})

    # Check if role has 'manage' permission (implies all actions)
    if has_manage_permission(role_permissions, resource):
        return True

    # Check specific action permission
    return has_permission(role_permissions, resource, action)


def require_permission(resource: str, action: str) -> Callable:
    """
    FastAPI dependency factory that requires specific permission.

    Usage:
        @router.post("", dependencies=[Depends(require_permission("menus", "create"))])
        async def create_menu(...):
            pass

        # Or get the user back:
        @router.post("")
        async def create_menu(
            current_user: CurrentUser = Depends(require_permission("menus", "create"))
        ):
            pass

    Args:
        resource: Resource name (e.g., 'menus', 'contents')
        action: Action name (e.g., 'view', 'create', 'edit', 'delete')

    Returns:
        FastAPI dependency function that checks permission

    Raises:
        HTTPException 403: If user doesn't have required permission
    """
    def permission_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if not check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Permission denied",
                    "message": f"You don't have permission to {action} {resource}",
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "required_permission": f"{resource}:{action}",
                    "user_role": current_user.role
                }
            )
        return current_user

    return permission_checker


def require_any_permission(resource: str, actions: list[str]) -> Callable:
    """
    FastAPI dependency that requires ANY of the specified permissions.

    Usage:
        @router.get("", dependencies=[Depends(require_any_permission("menus", ["view", "manage"]))])
        async def list_menus(...):
            pass

    Args:
        resource: Resource name
        actions: List of action names (any one of these is sufficient)

    Returns:
        FastAPI dependency function
    """
    def permission_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        for action in actions:
            if check_permission(current_user, resource, action):
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Permission denied",
                "message": f"You don't have permission to access {resource}",
                "code": "INSUFFICIENT_PERMISSIONS",
                "required_any_permission": [f"{resource}:{a}" for a in actions],
                "user_role": current_user.role
            }
        )

    return permission_checker


def require_all_permissions(permissions: list[tuple[str, str]]) -> Callable:
    """
    FastAPI dependency that requires ALL specified permissions.

    Usage:
        @router.post("/complex", dependencies=[
            Depends(require_all_permissions([("menus", "create"), ("contents", "create")]))
        ])
        async def complex_operation(...):
            pass

    Args:
        permissions: List of (resource, action) tuples

    Returns:
        FastAPI dependency function
    """
    def permission_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        missing = []
        for resource, action in permissions:
            if not check_permission(current_user, resource, action):
                missing.append(f"{resource}:{action}")

        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Permission denied",
                    "message": "You don't have all required permissions",
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "missing_permissions": missing,
                    "user_role": current_user.role
                }
            )
        return current_user

    return permission_checker


# =============================================================================
# Convenience functions for common resources
# =============================================================================

def require_menu_view() -> Callable:
    """Require permission to view menus"""
    return require_permission("menus", "view")

def require_menu_create() -> Callable:
    """Require permission to create menus"""
    return require_permission("menus", "create")

def require_menu_edit() -> Callable:
    """Require permission to edit menus"""
    return require_permission("menus", "edit")

def require_menu_delete() -> Callable:
    """Require permission to delete menus"""
    return require_permission("menus", "delete")

def require_menu_manage() -> Callable:
    """Require full menu management permission"""
    return require_permission("menus", "manage")

def require_content_view() -> Callable:
    """Require permission to view content"""
    return require_permission("contents", "view")

def require_content_create() -> Callable:
    """Require permission to create content"""
    return require_permission("contents", "create")

def require_content_edit() -> Callable:
    """Require permission to edit content"""
    return require_permission("contents", "edit")

def require_content_delete() -> Callable:
    """Require permission to delete content"""
    return require_permission("contents", "delete")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Core functions
    "check_permission",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",

    # Menu shortcuts
    "require_menu_view",
    "require_menu_create",
    "require_menu_edit",
    "require_menu_delete",
    "require_menu_manage",

    # Content shortcuts
    "require_content_view",
    "require_content_create",
    "require_content_edit",
    "require_content_delete",
]
