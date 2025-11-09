"""
Manage Permissions Use Case
Add/remove permissions from role
"""

from typing import Dict, List
from ..repositories.role_repo import RoleRepository
from shared.errors import NotFoundError, AuthorizationError, ValidationError


class ManagePermissionsUseCase:
    """Manage role permissions"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    def add_permission(self, role_id: int, resource: str, action: str) -> bool:
        """
        Add permission to role

        Args:
            role_id: Role ID
            resource: Resource name
            action: Action name

        Returns:
            True if added

        Raises:
            NotFoundError: If role not found
            AuthorizationError: If system role
        """
        # Validate
        role = self.role_repository.find_by_id(role_id)
        if not role:
            raise NotFoundError(message=f"Role with ID {role_id} not found")

        if role.is_system_role:
            raise AuthorizationError(
                message="Cannot modify system role permissions"
            )

        # Add permission
        return self.role_repository.add_permission(role_id, resource, action)

    def remove_permission(self, role_id: int, resource: str, action: str) -> bool:
        """
        Remove permission from role

        Args:
            role_id: Role ID
            resource: Resource name
            action: Action name

        Returns:
            True if removed

        Raises:
            NotFoundError: If role not found
            AuthorizationError: If system role
        """
        # Validate
        role = self.role_repository.find_by_id(role_id)
        if not role:
            raise NotFoundError(message=f"Role with ID {role_id} not found")

        if role.is_system_role:
            raise AuthorizationError(
                message="Cannot modify system role permissions"
            )

        # Remove permission
        return self.role_repository.remove_permission(role_id, resource, action)

    def get_permissions(self, role_id: int) -> Dict[str, List[str]]:
        """
        Get all permissions for role

        Args:
            role_id: Role ID

        Returns:
            Permissions dictionary

        Raises:
            NotFoundError: If role not found
        """
        role = self.role_repository.find_by_id(role_id)
        if not role:
            raise NotFoundError(message=f"Role with ID {role_id} not found")

        return role.permissions if isinstance(role.permissions, dict) else {}
