"""
Check Permission Use Case
Check if role has specific permission
"""

from typing import Dict, Any
from ..repositories.role_repo import RoleRepository
from shared.errors import NotFoundError


class CheckPermissionUseCase:
    """Check if role has permission"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    def execute(self, role_id: int, resource: str, action: str) -> Dict[str, Any]:
        """
        Check if role has permission

        Args:
            role_id: Role ID
            resource: Resource name
            action: Action name

        Returns:
            Dict with permission check result

        Raises:
            NotFoundError: If role not found
        """
        # Find role
        role = self.role_repository.find_by_id(role_id)
        if not role:
            raise NotFoundError(
                message=f"Role with ID {role_id} not found"
            )

        # Check permission
        has_permission = role.has_permission(resource, action)

        return {
            "has_permission": has_permission,
            "role_id": role.id,
            "role_name": role.name,
            "resource": resource,
            "action": action
        }
