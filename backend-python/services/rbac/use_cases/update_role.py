"""
Update Role Use Case
Update existing custom role
"""

from typing import Dict, Any, Optional, List
from ..repositories.role_repo import RoleRepository
from ..repositories.models import Role
from shared.errors import ValidationError, NotFoundError, ConflictError, AuthorizationError


class UpdateRoleUseCase:
    """Update existing role"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    def execute(
        self,
        role_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[Dict[str, List[str]]] = None
    ) -> Role:
        """
        Update role

        Args:
            role_id: Role ID
            name: New role name
            description: New description
            permissions: New permissions (replaces existing)

        Returns:
            Updated Role model

        Raises:
            NotFoundError: If role not found
            AuthorizationError: If trying to modify system role
            ConflictError: If new name already exists
            ValidationError: If validation fails
        """
        # Find role
        role = self.role_repository.find_by_id(role_id)
        if not role:
            raise NotFoundError(message=f"Role with ID {role_id} not found")

        # Can't update system roles
        if role.is_system_role:
            raise AuthorizationError(
                message="System roles cannot be modified"
            )

        # Update name if provided
        if name is not None:
            name = name.strip().lower().replace(" ", "_")
            if not name:
                raise ValidationError(message="Role name cannot be empty")

            # Check for name conflict (excluding current role)
            if self.role_repository.exists_by_name(
                name,
                role.organization_id,
                exclude_id=role_id
            ):
                raise ConflictError(
                    message=f"Role '{name}' already exists in this scope"
                )

            role.name = name

        # Update description if provided
        if description is not None:
            role.description = description

        # Update permissions if provided
        if permissions is not None:
            role.permissions = permissions

        # Save changes
        return self.role_repository.update(role)
