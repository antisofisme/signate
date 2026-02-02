"""
IAM Repository Interface (Port)

Abstract interface for IAM data operations.
This follows Clean Architecture - business logic depends on this interface,
not on concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain import Role, Permission, ServiceAccount


class IIAMRepository(ABC):
    """IAM repository interface."""

    # =========================================================================
    # User Operations (read from existing users table)
    # =========================================================================

    @abstractmethod
    async def list_users(
        self,
        tenant_id: UUID,
        role_id: Optional[UUID] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[dict], int]:
        """
        List users in a tenant.

        Args:
            tenant_id: Tenant UUID
            role_id: Optional filter by role
            search: Optional search query
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (users list, total count)
        """
        pass

    @abstractmethod
    async def get_user(self, tenant_id: UUID, user_id: UUID) -> Optional[dict]:
        """
        Get user by ID.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID

        Returns:
            User dict or None if not found
        """
        pass

    @abstractmethod
    async def get_user_roles(self, tenant_id: UUID, user_id: UUID) -> List[Role]:
        """
        Get roles assigned to a user in a tenant.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID

        Returns:
            List of Role entities
        """
        pass

    # =========================================================================
    # Role Operations
    # =========================================================================

    @abstractmethod
    async def list_roles(self, tenant_id: UUID) -> List[Role]:
        """
        List all roles in a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of Role entities
        """
        pass

    @abstractmethod
    async def get_role(self, tenant_id: UUID, role_id: UUID) -> Optional[Role]:
        """
        Get role by ID.

        Args:
            tenant_id: Tenant UUID
            role_id: Role UUID

        Returns:
            Role entity or None if not found
        """
        pass

    @abstractmethod
    async def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """
        Get permissions assigned to a role.

        Args:
            role_id: Role UUID

        Returns:
            List of Permission entities
        """
        pass

    # =========================================================================
    # Permission Operations
    # =========================================================================

    @abstractmethod
    async def list_permissions(self) -> List[Permission]:
        """
        List all available permissions.

        Returns:
            List of Permission entities
        """
        pass

    @abstractmethod
    async def get_permission_matrix(self, tenant_id: UUID) -> dict:
        """
        Get permission matrix showing all roles and their permissions.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Dict mapping role_id -> list of permission keys
        """
        pass

    # =========================================================================
    # Service Account Operations
    # =========================================================================

    @abstractmethod
    async def list_service_accounts(
        self,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[ServiceAccount], int]:
        """
        List service accounts in a tenant.

        Args:
            tenant_id: Tenant UUID
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (service accounts list, total count)
        """
        pass

    @abstractmethod
    async def get_service_account(
        self, tenant_id: UUID, account_id: UUID
    ) -> Optional[ServiceAccount]:
        """
        Get service account by ID.

        Args:
            tenant_id: Tenant UUID
            account_id: Service account UUID

        Returns:
            ServiceAccount entity or None if not found
        """
        pass

    @abstractmethod
    async def get_user_stats(self, tenant_id: UUID) -> dict:
        """
        Get user statistics for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Dict with user counts (total, active, inactive)
        """
        pass

    # =========================================================================
    # Role Write Operations
    # =========================================================================

    @abstractmethod
    async def create_role(
        self,
        tenant_id: UUID,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
    ) -> Role:
        """
        Create a new role in a tenant.

        Args:
            tenant_id: Tenant UUID
            name: Role name (unique within tenant)
            display_name: Display name for UI
            description: Optional description
            permission_ids: Optional list of permission UUIDs to assign

        Returns:
            Created Role entity

        Raises:
            RoleNameExistsError: If role name already exists in tenant
        """
        pass

    @abstractmethod
    async def update_role(
        self,
        tenant_id: UUID,
        role_id: UUID,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
    ) -> Role:
        """
        Update an existing role.

        Args:
            tenant_id: Tenant UUID
            role_id: Role UUID
            name: Optional new name
            display_name: Optional new display name
            description: Optional new description
            permission_ids: Optional new list of permission UUIDs (replaces existing)

        Returns:
            Updated Role entity

        Raises:
            RoleNotFoundError: If role not found
            SystemRoleError: If attempting to modify a system role
            RoleNameExistsError: If new name already exists
        """
        pass

    @abstractmethod
    async def delete_role(self, tenant_id: UUID, role_id: UUID) -> bool:
        """
        Delete a role (soft delete).

        Args:
            tenant_id: Tenant UUID
            role_id: Role UUID

        Returns:
            True if deleted successfully

        Raises:
            RoleNotFoundError: If role not found
            SystemRoleError: If attempting to delete a system role
            RoleInUseError: If role is assigned to users
        """
        pass

    @abstractmethod
    async def role_name_exists(
        self, tenant_id: UUID, name: str, exclude_role_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if role name exists in tenant.

        Args:
            tenant_id: Tenant UUID
            name: Role name to check
            exclude_role_id: Optional role ID to exclude (for updates)

        Returns:
            True if name exists
        """
        pass

    @abstractmethod
    async def get_role_user_count(self, tenant_id: UUID, role_id: UUID) -> int:
        """
        Get count of users assigned to a role.

        Args:
            tenant_id: Tenant UUID
            role_id: Role UUID

        Returns:
            Number of users with this role
        """
        pass

    # =========================================================================
    # User-Role Assignment Operations
    # =========================================================================

    @abstractmethod
    async def assign_role_to_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
        assigned_by: UUID,
    ) -> bool:
        """
        Assign a role to a user.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            role_id: Role UUID
            assigned_by: User UUID who is assigning the role

        Returns:
            True if assigned successfully

        Raises:
            UserNotFoundError: If user not found in tenant
            RoleNotFoundError: If role not found
            RoleAlreadyAssignedError: If role already assigned
        """
        pass

    @abstractmethod
    async def revoke_role_from_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
    ) -> bool:
        """
        Revoke a role from a user.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            role_id: Role UUID

        Returns:
            True if revoked successfully

        Raises:
            UserNotFoundError: If user not found in tenant
            RoleNotFoundError: If role not found
            RoleNotAssignedError: If role not assigned to user
        """
        pass

    @abstractmethod
    async def user_has_role(
        self, tenant_id: UUID, user_id: UUID, role_id: UUID
    ) -> bool:
        """
        Check if user has a specific role.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            role_id: Role UUID

        Returns:
            True if user has the role
        """
        pass

    @abstractmethod
    async def user_exists_in_tenant(self, tenant_id: UUID, user_id: UUID) -> bool:
        """
        Check if user exists in tenant.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID

        Returns:
            True if user is a member of the tenant
        """
        pass
