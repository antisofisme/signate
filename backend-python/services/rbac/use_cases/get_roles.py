"""
Get Roles Use Case
Retrieve roles with filtering
"""

from typing import List, Optional, Dict, Any
from ..repositories.role_repo import RoleRepository
from ..repositories.models import Role


class GetRolesUseCase:
    """Get roles with filtering"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    def execute(
        self,
        organization_id: Optional[int] = None,
        include_system: bool = True,
        name_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get roles with optional filtering

        Args:
            organization_id: Filter by organization (None = only system roles)
            include_system: Include system roles in results
            name_filter: Filter by name (partial match)

        Returns:
            Dict with roles list and total count
        """
        # Get roles
        roles = self.role_repository.get_all(
            organization_id=organization_id,
            include_system=include_system
        )

        # Apply name filter if provided
        if name_filter:
            name_lower = name_filter.lower()
            roles = [r for r in roles if name_lower in r.name.lower()]

        return {
            "roles": roles,
            "total": len(roles)
        }

    def get_by_id(self, role_id: int) -> Role:
        """
        Get role by ID

        Args:
            role_id: Role ID

        Returns:
            Role model

        Raises:
            NotFoundError: If role not found
        """
        from shared.errors import NotFoundError

        role = self.role_repository.find_by_id(role_id)
        if not role:
            raise NotFoundError(message=f"Role with ID {role_id} not found")

        return role

    def get_system_roles(self) -> List[Role]:
        """
        Get all system roles

        Returns:
            List of system roles
        """
        return self.role_repository.get_system_roles()

    def get_organization_roles(self, organization_id: int) -> List[Role]:
        """
        Get roles for organization

        Args:
            organization_id: Organization ID

        Returns:
            List of organization roles
        """
        return self.role_repository.get_organization_roles(organization_id)
