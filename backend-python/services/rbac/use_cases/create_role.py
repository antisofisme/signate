"""
Create Role Use Case
Create new custom role
"""

from typing import Dict, Any, Optional, List
from ..repositories.role_repo import RoleRepository
from ..repositories.models import Role
from shared.errors import ValidationError, ConflictError


class CreateRoleUseCase:
    """Create new role"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    def execute(
        self,
        name: str,
        description: Optional[str],
        organization_id: Optional[int],
        permissions: Dict[str, List[str]],
        created_by_id: Optional[int] = None
    ) -> Role:
        """
        Create new role

        Args:
            name: Role name
            description: Role description
            organization_id: Organization ID (None for system roles - admin only)
            permissions: Permissions dictionary
            created_by_id: User ID who creates this role (for audit trail)

        Returns:
            Created Role model

        Raises:
            ValidationError: If validation fails
            ConflictError: If role name already exists
        """
        # Validate name
        if not name or not name.strip():
            raise ValidationError(message="Role name is required")

        # Check if role name already exists
        if self.role_repository.exists_by_name(name, organization_id):
            raise ConflictError(
                message=f"Role '{name}' already exists in this scope"
            )

        # System roles can only be created by super_admin (handled in route)
        is_system_role = organization_id is None

        # Create role
        role = Role(
            name=name.strip().lower().replace(" ", "_"),
            description=description,
            organization_id=organization_id,
            is_system_role=is_system_role,
            permissions=permissions or {},
            created_by_id=created_by_id  # Audit trail (Migration 046)
        )

        return self.role_repository.create(role)
