"""
RBAC Permission Constants
Centralized definitions for Role-Based Access Control
"""

from typing import Dict, List

# =============================================================================
# Resource Definitions
# =============================================================================

PERMISSION_RESOURCES: List[str] = [
    'dashboard',
    'devices',
    'contents',
    'playlists',
    'schedules',
    'tags',
    'menus',
    'analytics',
    'audit_logs',
    'users',
    'organizations',
    'roles',
    'sessions',
    'settings',
    'system',
]

# =============================================================================
# Action Definitions
# =============================================================================

PERMISSION_ACTIONS: List[str] = [
    'view',    # Read access
    'create',  # Create new items
    'edit',    # Update existing items
    'delete',  # Remove items
    'manage',  # Full control (implies all above)
]

# =============================================================================
# Resource Labels (for API responses)
# =============================================================================

RESOURCE_LABELS: Dict[str, str] = {
    'dashboard': 'Dashboard',
    'devices': 'Devices',
    'contents': 'Content',
    'playlists': 'Playlists',
    'schedules': 'Schedules',
    'tags': 'Tags',
    'menus': 'Digital Menus',
    'analytics': 'Analytics',
    'audit_logs': 'Audit Logs',
    'users': 'Users',
    'organizations': 'Organizations',
    'roles': 'Roles & Permissions',
    'sessions': 'Active Sessions',
    'settings': 'Settings',
    'system': 'System Administration',
}

# =============================================================================
# Action Labels (for API responses)
# =============================================================================

ACTION_LABELS: Dict[str, str] = {
    'view': 'View',
    'create': 'Create',
    'edit': 'Edit',
    'delete': 'Delete',
    'manage': 'Manage',
}

# =============================================================================
# Default System Role Permissions
# =============================================================================

SYSTEM_ROLE_PERMISSIONS: Dict[str, Dict[str, List[str]]] = {
    'SUPER_ADMIN': {
        'dashboard': ['view', 'manage'],
        'devices': ['view', 'create', 'edit', 'delete', 'manage'],
        'contents': ['view', 'create', 'edit', 'delete', 'manage'],
        'playlists': ['view', 'create', 'edit', 'delete', 'manage'],
        'schedules': ['view', 'create', 'edit', 'delete', 'manage'],
        'tags': ['view', 'create', 'edit', 'delete', 'manage'],
        'menus': ['view', 'create', 'edit', 'delete', 'manage'],
        'analytics': ['view', 'manage'],
        'audit_logs': ['view', 'manage'],
        'users': ['view', 'create', 'edit', 'delete', 'manage'],
        'organizations': ['view', 'create', 'edit', 'delete', 'manage'],
        'roles': ['view', 'create', 'edit', 'delete', 'manage'],
        'sessions': ['view', 'manage'],
        'settings': ['view', 'edit', 'manage'],
        'system': ['view', 'manage'],
    },
    'ADMIN': {
        'dashboard': ['view'],
        'devices': ['view', 'create', 'edit', 'delete'],
        'contents': ['view', 'create', 'edit', 'delete'],
        'playlists': ['view', 'create', 'edit', 'delete'],
        'schedules': ['view', 'create', 'edit', 'delete'],
        'tags': ['view', 'create', 'edit', 'delete'],
        'menus': ['view', 'create', 'edit', 'delete'],
        'analytics': ['view'],
        'audit_logs': ['view'],
        'users': ['view', 'create', 'edit', 'delete'],
        'organizations': ['view', 'edit'],
        'roles': ['view', 'create', 'edit', 'delete'],
        'sessions': ['view'],
        'settings': ['view', 'edit'],
    },
    'CONTENT_MANAGER': {
        'dashboard': ['view'],
        'devices': ['view'],
        'contents': ['view', 'create', 'edit', 'delete'],
        'playlists': ['view', 'create', 'edit', 'delete'],
        'schedules': ['view', 'create', 'edit'],
        'tags': ['view', 'create', 'edit'],
        'menus': ['view', 'create', 'edit'],
    },
    'VIEWER': {
        'dashboard': ['view'],
        'devices': ['view'],
        'contents': ['view'],
        'playlists': ['view'],
        'schedules': ['view'],
        'analytics': ['view'],
    },
}

# =============================================================================
# Helper Functions
# =============================================================================

def validate_resource(resource: str) -> bool:
    """Check if resource is valid"""
    return resource in PERMISSION_RESOURCES


def validate_action(action: str) -> bool:
    """Check if action is valid"""
    return action in PERMISSION_ACTIONS


def validate_permissions(permissions: Dict[str, List[str]]) -> tuple[bool, str]:
    """
    Validate permissions dictionary
    Returns (is_valid, error_message)
    """
    if not isinstance(permissions, dict):
        return False, "Permissions must be a dictionary"

    for resource, actions in permissions.items():
        if not validate_resource(resource):
            return False, f"Invalid resource: {resource}"

        if not isinstance(actions, list):
            return False, f"Actions for '{resource}' must be a list"

        for action in actions:
            if not validate_action(action):
                return False, f"Invalid action: {action} for resource: {resource}"

    return True, ""


def count_permissions(permissions: Dict[str, List[str]]) -> int:
    """Count total permissions in a permission object"""
    return sum(len(actions) for actions in permissions.values())


def get_total_possible_permissions() -> int:
    """Get total possible permissions"""
    return len(PERMISSION_RESOURCES) * len(PERMISSION_ACTIONS)


def has_permission(
    permissions: Dict[str, List[str]],
    resource: str,
    action: str
) -> bool:
    """Check if a permission object has a specific permission"""
    return action in permissions.get(resource, [])


def has_manage_permission(
    permissions: Dict[str, List[str]],
    resource: str
) -> bool:
    """Check if resource has 'manage' action (implies all permissions)"""
    return has_permission(permissions, resource, 'manage')
