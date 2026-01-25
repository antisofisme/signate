"""
RBAC (Role-Based Access Control) interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List


class Permission(str, Enum):
    """Chat service permissions."""

    # Chat permissions
    CHAT_READ = "chat.read"
    CHAT_WRITE = "chat.write"

    # Session permissions
    SESSION_READ = "session.read"
    SESSION_WRITE = "session.write"
    SESSION_DELETE = "session.delete"

    # Knowledge permissions
    KNOWLEDGE_READ = "knowledge.read"
    KNOWLEDGE_WRITE = "knowledge.write"

    # Memory permissions
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    MEMORY_DELETE = "memory.delete"

    # Admin permissions
    ADMIN = "admin"
    ADMIN_EMBED = "admin.embed"
    ADMIN_TENANT = "admin.tenant"
    ADMIN_USER = "admin.user"


@dataclass
class RolePermissions:
    """Default permissions for each role."""

    ADMIN = [
        Permission.ADMIN,
        Permission.CHAT_READ, Permission.CHAT_WRITE,
        Permission.SESSION_READ, Permission.SESSION_WRITE, Permission.SESSION_DELETE,
        Permission.KNOWLEDGE_READ, Permission.KNOWLEDGE_WRITE,
        Permission.MEMORY_READ, Permission.MEMORY_WRITE, Permission.MEMORY_DELETE,
        Permission.ADMIN_EMBED, Permission.ADMIN_TENANT, Permission.ADMIN_USER,
    ]

    USER = [
        Permission.CHAT_READ, Permission.CHAT_WRITE,
        Permission.SESSION_READ, Permission.SESSION_WRITE, Permission.SESSION_DELETE,
        Permission.KNOWLEDGE_READ,
        Permission.MEMORY_READ, Permission.MEMORY_WRITE,
    ]

    READONLY = [
        Permission.CHAT_READ,
        Permission.SESSION_READ,
        Permission.KNOWLEDGE_READ,
        Permission.MEMORY_READ,
    ]


class IRBACService(ABC):
    """
    Interface for RBAC service.

    Implementations: SimpleRBACService
    """

    @abstractmethod
    def get_role_permissions(self, role: str) -> List[Permission]:
        """
        Get default permissions for role.

        Args:
            role: Role name (admin, user, readonly)

        Returns:
            List of Permission
        """
        pass

    @abstractmethod
    def has_permission(
        self,
        user_permissions: List[str],
        required_permission: Permission
    ) -> bool:
        """
        Check if user has required permission.

        Args:
            user_permissions: User's permission list
            required_permission: Permission to check

        Returns:
            True if has permission
        """
        pass

    @abstractmethod
    def has_any_permission(
        self,
        user_permissions: List[str],
        required_permissions: List[Permission]
    ) -> bool:
        """
        Check if user has any of the required permissions.

        Args:
            user_permissions: User's permission list
            required_permissions: Permissions to check

        Returns:
            True if has any permission
        """
        pass

    @abstractmethod
    def has_all_permissions(
        self,
        user_permissions: List[str],
        required_permissions: List[Permission]
    ) -> bool:
        """
        Check if user has all required permissions.

        Args:
            user_permissions: User's permission list
            required_permissions: Permissions to check

        Returns:
            True if has all permissions
        """
        pass
