"""
Authentication & Authorization Utilities
JWT validation and permission checking middleware
"""

from .jwt import (
    CurrentUser,
    get_current_user,
    get_optional_user,
    decode_token
)

from .permissions import (
    Role,
    PermissionChecker,
    require_role,
    require_super_admin,
    require_admin,
    require_manager,
    require_same_organization,
    has_role,
    is_super_admin,
    is_admin,
    is_manager,
    is_same_organization,
    can_access_organization
)

__all__ = [
    # JWT
    "CurrentUser",
    "get_current_user",
    "get_optional_user",
    "decode_token",

    # Permissions
    "Role",
    "PermissionChecker",
    "require_role",
    "require_super_admin",
    "require_admin",
    "require_manager",
    "require_same_organization",
    "has_role",
    "is_super_admin",
    "is_admin",
    "is_manager",
    "is_same_organization",
    "can_access_organization",
]
