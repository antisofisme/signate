"""
Assign Role to User Use Case
"""

from uuid import UUID

from ..interfaces import IIAMRepository


class AssignRoleToUserUseCase:
    """Use case for assigning a role to a user."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
        assigned_by: UUID,
    ) -> dict:
        """
        Assign a role to a user.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            role_id: Role UUID
            assigned_by: User UUID who is assigning the role

        Returns:
            Dict with assignment result

        Raises:
            UserNotFoundError: If user not found in tenant
            RoleNotFoundError: If role not found
            RoleAlreadyAssignedError: If role already assigned
        """
        await self._repository.assign_role_to_user(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
        )

        # Get updated user roles
        roles = await self._repository.get_user_roles(tenant_id, user_id)

        return {
            "user_id": str(user_id),
            "role_id": str(role_id),
            "assigned": True,
            "roles": [
                {
                    "id": str(role.id),
                    "name": role.name,
                    "display_name": role.display_name,
                    "is_system": role.is_system,
                }
                for role in roles
            ],
        }
